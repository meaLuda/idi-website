# Server-side infra (Traefik + Garage) — reproducibility notes

These configs are applied **live on the server**; they are committed here so a rebuild
(or an Ansible run) can reproduce them. They are *not* loaded by the Django app.

## Traefik dynamic configs

Copy both files to the server's Traefik dynamic config directory and Traefik will hot-reload
them (file provider, `watch: true`):

```
scp deploy/traefik/idi-s3-proxy.yml  server:/opt/traefik/config/dynamic/
scp deploy/traefik/idi-wpcontent.yml server:/opt/traefik/config/dynamic/
```

- `idi-s3-proxy.yml` — proxies `idi.africa/media/*` to the Garage S3 website endpoint and
  stamps `Cache-Control: public, max-age=31536000, immutable` on the response.
- `idi-wpcontent.yml` — rewrites legacy `/wp-content/*.{png,jpg,jpeg}` links to the
  self-hosted WebP assets under `/static/images/wp-content/*.webp` (keeps old SEO/backlinks alive).

Router `priority` values matter: wp-content (110) > media (100) > the catch-all Django
router, so the specific rules win.

## Garage bucket (media)

The media bucket is exposed over Garage's S3 *website* endpoint. One-time setup:

```bash
# Alias the bucket to the public website hostname
garage bucket alias <bucket-id> idi-media.s3-web.sintal.africa

# Enable website (public read) serving for the bucket
garage bucket website --allow <bucket-id>
```

The Django side writes media to this bucket via `django-storages` + `boto3` (S3 backend);
Traefik serves reads from the website endpoint (see `idi-s3-proxy.yml`).

## Volume ownership (one-time)

On a fresh deploy the named volumes are root-owned, but the container runs gunicorn as the
non-root `django` user (uid/gid 1000). If you see permission errors on first boot:

```bash
docker run --rm -v idi_static:/v busybox chown -R 1000:1000 /v
docker run --rm -v idi_media:/v  busybox chown -R 1000:1000 /v
```

The image also avoids this class of failure by:
- setting `ENV HOME=/tmp` for the django user (writable cache/config dir), and
- running `collectstatic` **without** `--clear` in `docker-entrypoint.sh` (clearing the
  target first is what crash-loops on a fresh/wrong-owned volume).
