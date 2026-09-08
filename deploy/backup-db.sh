#!/usr/bin/env bash
# Dump the production IDI database before a deploy.
#
# Run remotely by `make deploy-backup`:
#     ssh sintal-mainserver 'bash -s' < deploy/backup-db.sh
#
# Kept as a file rather than inlined in the Makefile because quoting a script
# through make -> ssh -> sh mangles escapes; an inline version silently produced
# a zero-byte "backup", which is worse than no backup at all.
#
# Uses the application's own credentials from /opt/idi/.env, so no database
# superuser password is needed, and runs a throwaway client container on
# database_network rather than requiring psql on the host.
set -euo pipefail

ENV_FILE=/opt/idi/.env
BACKUP_DIR=/opt/idi/backups
KEEP=10

read_env() {
    # Values are single-quoted in .env; strip quotes and any trailing comment.
    sudo grep -E "^$1=" "$ENV_FILE" \
        | head -1 | cut -d= -f2- \
        | sed -E "s/[[:space:]]+#.*$//" \
        | tr -d "'\""
}

DB_NAME=$(read_env DB_NAME)
DB_USER=$(read_env DB_USER)
DB_PASSWORD=$(read_env DB_PASSWORD)
DB_HOST=$(read_env DB_HOST)
DB_PORT=$(read_env DB_PORT)
DB_PORT=${DB_PORT:-5432}

for var in DB_NAME DB_USER DB_PASSWORD DB_HOST; do
    if [ -z "${!var}" ]; then
        echo "ERROR: $var missing from $ENV_FILE" >&2
        exit 1
    fi
done

sudo mkdir -p "$BACKUP_DIR"
TS=$(date +%Y%m%d-%H%M%S)
OUT="$BACKUP_DIR/ididb-$TS.sql.gz"
TMP=$(mktemp /tmp/ididb-XXXXXX.sql.gz)

# Dump to a temp file first: piping straight to the destination leaves a
# truncated file behind if pg_dump fails partway through.
if ! docker run --rm --network database_network -e PGPASSWORD="$DB_PASSWORD" postgres:16-alpine \
        pg_dump -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -d "$DB_NAME" --no-owner --no-acl \
        | gzip > "$TMP"; then
    rm -f "$TMP"
    echo "ERROR: pg_dump failed; no backup written" >&2
    exit 1
fi

# A valid dump always contains schema. Refuse to record an empty one as a backup.
TABLES=$(zcat "$TMP" | grep -c 'CREATE TABLE' || true)
if [ "$TABLES" -lt 1 ]; then
    rm -f "$TMP"
    echo "ERROR: dump contained no tables; refusing to record it as a backup" >&2
    exit 1
fi

sudo mv "$TMP" "$OUT"
sudo chmod 600 "$OUT"
echo "backup: $OUT ($(sudo du -h "$OUT" | cut -f1), $TABLES tables)"

# Keep only the most recent $KEEP dumps.
sudo ls -1t "$BACKUP_DIR"/ididb-*.sql.gz 2>/dev/null | tail -n +$((KEEP + 1)) \
    | sudo xargs -r rm -f
echo "retained: $(sudo ls -1 "$BACKUP_DIR"/ididb-*.sql.gz 2>/dev/null | wc -l) dump(s)"
