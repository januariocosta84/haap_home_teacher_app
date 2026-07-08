#!/usr/bin/env bash
# ============================================================
#  sync_to_prod.sh
#  Push new data from worldmosaic (dev) → haap (production)
#  Uses INSERT IGNORE so production records are never overwritten.
#
#  Usage:
#    bash sync_to_prod.sh           # interactive
#    bash sync_to_prod.sh --yes     # non-interactive (for cron)
# ============================================================

set -euo pipefail

# ── Config ──────────────────────────────────────────────────
DB_USER="root"
DB_PASS="Paddington2025yoyo"
DB_HOST="localhost"
DEV_DB="worldmosaic"
PROD_DB="haap"
DUMP_FILE="/tmp/wm_sync_$(date +%Y%m%d_%H%M%S).sql"
LOG_FILE="/var/www/new_app/haap_app/sync.log"

# Tables to sync (application data only — system/log tables excluded)
SYNC_TABLES=(
  users
  children
  preschools
  preschool_teachers
  classrooms
  klase_classroomchild
  support_tickets
  ticket_supportticketdetail
  ticket_supportticketmessage
  ticket_notifications
  teacher_activity_logs
  activity_result
  app_notifications
  municipalities
  administrative_posts
  sucos
  aldeias
  equipments
  apk_versions
)

# ── Helpers ─────────────────────────────────────────────────
TS()  { date '+%Y-%m-%d %H:%M:%S'; }
log() { echo "[$(TS)] $*" | tee -a "$LOG_FILE"; }
count() { mysql -u"$DB_USER" -p"$DB_PASS" -h"$DB_HOST" "$1" -sNe "SELECT COUNT(*) FROM $2;" 2>/dev/null || echo "?"; }

# ── Prompt unless --yes ──────────────────────────────────────
if [[ "${1:-}" != "--yes" ]]; then
  echo ""
  echo "  This will push NEW records from  [$DEV_DB]  →  [$PROD_DB]"
  echo "  Existing production records are never overwritten (INSERT IGNORE)."
  echo ""
  read -r -p "  Continue? [y/N] " ans
  [[ "$ans" =~ ^[Yy]$ ]] || { echo "Aborted."; exit 0; }
fi

log "====== SYNC START: $DEV_DB → $PROD_DB ======"

# ── Pre-sync counts ──────────────────────────────────────────
log "--- Pre-sync counts ---"
for tbl in "${SYNC_TABLES[@]}"; do
  d=$(count "$DEV_DB" "$tbl")
  p=$(count "$PROD_DB" "$tbl")
  [[ "$d" != "$p" ]] && log "  $tbl : dev=$d  prod=$p  ← diff"
done

# ── Dump dev database (data only, INSERT IGNORE) ─────────────
log "Dumping $DEV_DB ..."
mysqldump \
  -u"$DB_USER" -p"$DB_PASS" -h"$DB_HOST" \
  --no-create-info \
  --no-create-db \
  --skip-triggers \
  --complete-insert \
  --insert-ignore \
  "$DEV_DB" \
  "${SYNC_TABLES[@]}" \
  > "$DUMP_FILE" 2>/dev/null

LINES=$(wc -l < "$DUMP_FILE")
log "Dump complete: $LINES lines → $DUMP_FILE"

# ── Apply to production ──────────────────────────────────────
log "Importing into $PROD_DB ..."
mysql -u"$DB_USER" -p"$DB_PASS" -h"$DB_HOST" "$PROD_DB" < "$DUMP_FILE" 2>/dev/null
log "Import complete."

# ── Post-sync counts ─────────────────────────────────────────
log "--- Post-sync counts ---"
for tbl in "${SYNC_TABLES[@]}"; do
  d=$(count "$DEV_DB" "$tbl")
  p=$(count "$PROD_DB" "$tbl")
  log "  $tbl : dev=$d  prod=$p"
done

# ── Cleanup ──────────────────────────────────────────────────
rm -f "$DUMP_FILE"
log "====== SYNC DONE ======"
echo ""
echo "  Done. Log: $LOG_FILE"
