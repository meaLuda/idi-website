# Deploy plan — `integrate/09michel-2026-06-09` to idi.africa

Server state checked 8 September 2026. Production is serving an image built two
months ago; this branch is 7 commits ahead of origin.

---

## Pre-flight — already done on the server

These were blockers. All fixed and verified:

| Item | State |
|---|---|
| `SCAN_IP_SALT` in `/opt/idi/.env` | **set** — without it the new image refuses to start with `DEBUG=0` |
| `CACHE_URL` in `/opt/idi/.env` | **set** — `redis:6379/4`, password percent-encoded, verified with redis-py |
| Healthcheck | now `curl -fsS http://localhost:8000/health/` (was `/`, which `SECURE_SSL_REDIRECT` answers with a 301 that `curl -f` treats as success — it never exercised the app) |
| `idi_private_media` volume | declared, so archived certificate PDFs survive a redeploy |
| `deploy-backup` target | added and **test-run successfully** (13K, 20 tables) |
| Makefile deploy key | was `~/.ssh/github-actions-deploy`, which does not exist on this machine; now uses the `sintal-mainserver` SSH config alias |

`.env` and `docker-compose.production.yml` were backed up before editing
(`.bak.20260908-063839`, `.bak.20260908-064103`).

## Server readiness

```
live site      https://idi.africa/  HTTP 200 in 0.34s
container      idi:latest  Up 2 months (healthy)
disk           373G free (15% used)
rollback       3 tagged images available
migrations     prod at home/0007 — exactly this branch's baseline
```

---

## What deploying actually changes

**Six migrations run automatically** — the entrypoint calls `migrate --noinput`
on every start:

- `home/0008` ContactMessage
- `home/0009` renames `TeamMember.create_at` → `updated_at`, adds `created_at`,
  adds ordering. **Touches 5 live rows.** `RenameField` preserves data.
- `home/0010` sets the `django.contrib.sites` row to `idi.africa`
- `home/0011` NewsletterSubscriber
- `credentials/0001`, `credentials/0002` — new tables only

**A live bug gets fixed immediately.** Production's `/sitemap.xml` currently
publishes `https://example.com/...` for every URL, because the Site row is still
Django's default. Migration `0010` corrects it — verify this first after deploy.

**New public routes:** `/verify/`, `/verify/<code>/`, `/v/<code>`,
`/privacy-policy/`, `/terms/`, `/accessibility/`, `/newsletter/subscribe/`.

**Behaviour changes worth knowing before pressing go:**

- The contact form now stores and emails enquiries. Prod has **no `EMAIL_*`
  settings**, so notification will fail — but the database row is the durable
  record and the failure is logged, so no enquiry is lost. Configure
  `EMAIL_HOST` etc. when convenient.
- `/fellowship/did-academy` now 301s to `/fellowship/did-academy/`.
- Fabricated case-study statistics and the placeholder articles disappear.
  **Roughly nine case-study pages will look noticeably sparser.** That is the
  intended outcome, but it is a visible content change — make sure whoever owns
  the site expects it.
- ~600KB less JavaScript per page; Alpine now loads on only two templates.

---

## Build architecture — read this first

**The production host is x86_64/amd64. This machine is Apple Silicon (arm64).**

`docker build` without `--platform` produces an arm64 image that `docker load`
accepts and then cannot run. Because `deploy-cutover` replaces the running
container before it checks health, the site goes down until someone notices.

That happened on the first attempt on 2026-09-08: idi.africa returned 404 for
roughly four minutes. Migrations had not yet run, so the database was untouched
and re-tagging the previous image was enough to restore service.

`deploy-image` now builds `--platform linux/amd64` and asserts the resulting
image's architecture, so a mismatch fails locally before anything is shipped.

> **The Makefile is gitignored**, so that fix is not version-controlled. If the
> Makefile is ever recreated or copied to another machine, re-add both the
> `--platform` flag and the architecture assertion. This is the strongest reason
> to bring the deploy pipeline into the repository.

---

## Steps

```bash
# 0. OrbStack must be running — `make deploy` builds the image locally.
docker ps >/dev/null || open -a OrbStack

# 1. Confirm the branch is green before building anything.
python manage.py test          # expect: 175 tests, OK

# 2. Deploy. deploy-backup runs first, before the image is even built.
make deploy
```

`make deploy` = `deploy-backup` → `deploy-image` → `deploy-push` →
`deploy-cutover` → `deploy-verify`.

Expect roughly 5–10 minutes, dominated by `docker save | gzip | scp` of a ~750MB
image over the link.

---

## Verification

```bash
# The sitemap bug — the clearest signal the deploy landed.
curl -s https://idi.africa/sitemap.xml | grep -c example.com          # expect 0
curl -s https://idi.africa/sitemap.xml | grep -c "<loc>"              # expect ~25

# Core pages
for p in / /contact/ /team/ /case-studies/ /privacy-policy/ /verify/; do
  curl -s -o /dev/null -w "$p %{http_code}\n" "https://idi.africa$p"
done

# Verification pages must never be indexable
curl -sI https://idi.africa/verify/ | grep -i x-robots-tag            # noindex
curl -s https://idi.africa/robots.txt | grep -c "Disallow: /verify/"  # every UA block

# Container came up clean
ssh sintal-mainserver 'docker inspect idi --format "{{.State.Health.Status}}"'
ssh sintal-mainserver 'docker logs idi --tail 40 | grep -iE "error|traceback"'
```

Then, in the admin: issue one real certificate, download its QR, **print it at
20 mm and scan it with an actual phone**. No automated check substitutes for that.

---

## Rollback

The cutover tags the outgoing image before loading the new one.

```bash
ssh sintal-mainserver
docker images idi --format "{{.Tag}}" | head -5      # pick the rollback-<ts> tag
docker tag idi:rollback-<timestamp> idi:latest
cd /opt/idi && docker compose -f docker-compose.production.yml up -d
```

**Migrations do not roll back with the image.** If the schema must be reverted:

```bash
sudo ls -1t /opt/idi/backups/ididb-*.sql.gz | head -1
# restore with psql from a client container on database_network
# (same pattern as deploy/backup-db.sh)
```

Because `0009` renames a column, the old image would fail against the new schema.
In practice: roll back the image *and* restore the dump, or roll forward.

---

## Risks

**High — one-way for the schema.** `0009` renames a column on a table with live
data. The backup is the safety net; confirm `deploy-backup` printed a non-zero
table count before continuing.

**Medium — content becomes visibly sparser.** Nine case studies lose their
invented statistics. Expected, but visible to anyone watching the site.

**Medium — no email on prod.** Contact enquiries save but notify nobody until
`EMAIL_*` is configured. Watch `/admin/home/contactmessage/` in the meantime.

**Low — first deploy in two months.** The gap is the risk, not any single change:
more moves at once, so verify deliberately rather than assuming.

**Known false alarm:** `deploy-verify` can report a 404 even on a successful
deploy. It runs the instant the container reports healthy, which is a moment
before Traefik re-registers the recreated container. Re-check the URL by hand
before concluding anything is wrong — this happened on the successful
2026-09-08 deploy.

**Not blocking, worth knowing:** `docker-compose.production.yml` mounts
`idi_static` over the image's collected static. A stale volume can shadow a
correct build — this caught me twice locally. If styling looks wrong after
deploy, look there first.

---

## Not done, deliberately

- `scripts_cleanup_dead_assets.sh` has **not** been run. It deletes ~16MB of
  unreferenced assets including a 15.5MB SVG. Review and run separately.
- The homepage hero still shows "98.4% placement rate", hardcoded at
  `templates/home/partials/_hero.html:33`. The same claim was removed from
  `llms.txt` as unsourced, so leaving it on the homepage is inconsistent.
  Decide: delete it, make it `HomeStat`-driven, or source it.
- Nothing is pushed. `git push origin integrate/09michel-2026-06-09` when ready.
