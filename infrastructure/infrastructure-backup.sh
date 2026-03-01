#!/bin/bash
set -euo pipefail

### ==============================
### Konfiguration
### ==============================

DATE=$(date +%F_%H-%M)
BASE_DIR="<path-to>backup_mantis"
PG_DIR="$BASE_DIR/postgres"
IMG_DIR="$BASE_DIR/images"
LOG_FILE="$BASE_DIR/backup.log"

POSTGRES_CONTAINER="infrastructure_db_1"
WEB_CONTAINER="infrastructure_web_1"

POSTGRES_DB="mantis_tracker"
POSTGRES_USER="mate_user"

# IMAGE_VOLUME="infrastructure_web_1"

RETENTION_DAYS=14

### ==============================
### Logging
### ==============================

log() {
  echo "[$(date '+%F %T')] $1" | tee -a "$LOG_FILE"
}

error_exit() {
  log "❌ FEHLER: $1"
  exit 1
}

### ==============================
### Start
### ==============================

log "===== Backup gestartet ====="

mkdir -p "$PG_DIR" "$IMG_DIR"

### ==============================
### 1️⃣ PostgreSQL Dump
### ==============================

log "Erstelle PostgreSQL Dump..."

podman exec "$POSTGRES_CONTAINER" \
  pg_dump -U "$POSTGRES_USER" "$POSTGRES_DB" \
  > "$PG_DIR/db_$DATE.sql" \
  || error_exit "Postgres Dump fehlgeschlagen"

log "Postgres Dump erfolgreich."

### ==============================
### 2️⃣ Bilder inkrementell sichern
### ==============================

log "Synchronisiere Bilder..."

podman exec "$WEB_CONTAINER" \
  tar -C /mantis/app/datastore -cf - . \
  | tar -C "$IMG_DIR" -xf - \
  || error_exit "Bilder-Backup fehlgeschlagen"
log "Bilder-Sync erfolgreich."

### ==============================
### 3️⃣ Alte Backups löschen
### ==============================

log "Bereinige alte Dumps (> $RETENTION_DAYS Tage)..."

find "$PG_DIR" -type f -mtime +$RETENTION_DAYS -delete

log "Rotation abgeschlossen."

log "===== Backup erfolgreich beendet ====="
