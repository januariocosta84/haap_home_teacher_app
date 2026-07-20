#!/usr/bin/env bash
# =============================================================================
#  HAAP Platform — Automated Server Installation Script
#  Ubuntu 24.04 LTS | Apache + mod_wsgi | MySQL 8 | Python 3.12 | Django 4.2
# =============================================================================
#
#  BEFORE RUNNING THIS SCRIPT on a new server you must transfer:
#    1.  The project code  →  /var/www/new_app/haap_app/
#    2.  A MySQL dump      →  /var/www/new_app/haap_app/haap_backup.sql   (optional)
#    3.  The media folder  →  /var/www/new_app/haap_app/media/             (optional)
#
#  Quick transfer from old server (run on OLD server):
#    tar -czf haap_media.tar.gz -C /var/www/new_app/haap_app media
#    mysqldump -u root -p haap > haap_backup.sql
#    scp -r /var/www/new_app/haap_app/ root@NEW_IP:/var/www/new_app/haap_app/
#    scp haap_backup.sql root@NEW_IP:/var/www/new_app/haap_app/
#    scp haap_media.tar.gz root@NEW_IP:/var/www/new_app/haap_app/
#
#  Then on the NEW server:
#    chmod +x /var/www/new_app/haap_app/install.sh
#    sudo bash /var/www/new_app/haap_app/install.sh
# =============================================================================

set -euo pipefail

# ── Colors ────────────────────────────────────────────────────────────────────
RED='\033[0;31m'; GREEN='\033[0;32m'; YELLOW='\033[1;33m'
CYAN='\033[0;36m'; BOLD='\033[1m'; NC='\033[0m'

info()    { echo -e "${CYAN}[INFO]${NC}  $*"; }
success() { echo -e "${GREEN}[OK]${NC}    $*"; }
warn()    { echo -e "${YELLOW}[WARN]${NC}  $*"; }
error()   { echo -e "${RED}[ERROR]${NC} $*"; exit 1; }
step()    { echo -e "\n${BOLD}${CYAN}══ $* ══${NC}"; }

# ── Must run as root ──────────────────────────────────────────────────────────
[[ $EUID -ne 0 ]] && error "Run as root:  sudo bash install.sh"

# =============================================================================
#  CONFIGURATION  — edit these before running if you want non-interactive mode
# =============================================================================
APP_DIR="/var/www/new_app/haap_app"
VENV_DIR="$APP_DIR/.venv"
APACHE_CONF="/etc/apache2/sites-available/haap.conf"

# Prompt for server-specific values
echo -e "\n${BOLD}HAAP Platform — Installation Setup${NC}"
echo "────────────────────────────────────────"

read -rp "Server IP or domain  [e.g. 154.26.155.43]: " SERVER_IP
SERVER_IP="${SERVER_IP:-localhost}"

read -rp "MySQL root password  [Paddington2025yoyo]: " DB_ROOT_PASS
DB_ROOT_PASS="${DB_ROOT_PASS:-Paddington2025yoyo}"

read -rp "Database name        [haap]: " DB_NAME
DB_NAME="${DB_NAME:-haap}"

read -rp "Database user        [root]: " DB_USER
DB_USER="${DB_USER:-root}"

read -rp "Database password    [same as root]: " DB_PASS
DB_PASS="${DB_PASS:-$DB_ROOT_PASS}"

read -rp "Django SECRET_KEY    [auto-generate]: " DJANGO_SECRET
if [[ -z "$DJANGO_SECRET" ]]; then
    DJANGO_SECRET=$(python3 -c "import secrets, string; print(''.join(secrets.choice(string.ascii_letters+string.digits+'!@#\$%^&*') for _ in range(50)))")
    info "Generated SECRET_KEY: $DJANGO_SECRET"
fi

read -rp "Email (Gmail) user   [leave blank to skip]: " EMAIL_USER
EMAIL_PASS=""
if [[ -n "$EMAIL_USER" ]]; then
    read -rp "Email app password   : " EMAIL_PASS
fi

echo ""

# =============================================================================
#  STEP 1 — System packages
# =============================================================================
step "Installing system packages"

apt-get update -qq
apt-get install -y -qq \
    python3.12 python3.12-venv python3.12-dev \
    apache2 libapache2-mod-wsgi-py3 \
    mysql-server libmysqlclient-dev \
    pkg-config \
    git curl wget unzip \
    build-essential

a2enmod wsgi
success "System packages installed"

# =============================================================================
#  STEP 2 — MySQL setup
# =============================================================================
step "Setting up MySQL"

systemctl start mysql
systemctl enable mysql

# Set root password and create database
mysql -u root <<EOF
ALTER USER 'root'@'localhost' IDENTIFIED WITH mysql_native_password BY '${DB_ROOT_PASS}';
FLUSH PRIVILEGES;
CREATE DATABASE IF NOT EXISTS \`${DB_NAME}\` CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci;
EOF

if [[ "$DB_USER" != "root" ]]; then
    mysql -u root -p"${DB_ROOT_PASS}" <<EOF
CREATE USER IF NOT EXISTS '${DB_USER}'@'localhost' IDENTIFIED BY '${DB_PASS}';
GRANT ALL PRIVILEGES ON \`${DB_NAME}\`.* TO '${DB_USER}'@'localhost';
FLUSH PRIVILEGES;
EOF
    success "DB user '${DB_USER}' created"
fi

success "MySQL database '${DB_NAME}' ready"

# =============================================================================
#  STEP 3 — App directory
# =============================================================================
step "Preparing application directory"

mkdir -p "$APP_DIR"
mkdir -p "$APP_DIR/media/apk"
mkdir -p "$APP_DIR/media/users"

# Set initial ownership so we can write files
chown -R root:root "$APP_DIR"

success "Directories ready"

# =============================================================================
#  STEP 4 — Python virtual environment & packages
# =============================================================================
step "Creating Python virtual environment"

if [[ ! -d "$VENV_DIR" ]]; then
    python3.12 -m venv "$VENV_DIR"
    success "Virtual environment created"
else
    warn "Virtual environment already exists — skipping creation"
fi

"$VENV_DIR/bin/pip" install --upgrade pip -q
"$VENV_DIR/bin/pip" install -r "$APP_DIR/requirements.txt" -q
success "Python packages installed"

# =============================================================================
#  STEP 5 — .env file
# =============================================================================
step "Writing .env file"

cat > "$APP_DIR/.env" <<ENV
SECRET_KEY=${DJANGO_SECRET}

# Django
DEBUG=False
ALLOWED_HOSTS=127.0.0.1,localhost,${SERVER_IP}

# MySQL
DB_NAME=${DB_NAME}
DB_USER=${DB_USER}
DB_PASSWORD=${DB_PASS}
DB_HOST=localhost
DB_PORT=3306

# Email
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_HOST_USER=${EMAIL_USER}
EMAIL_HOST_PASSWORD=${EMAIL_PASS}
EMAIL_USE_TLS=True
ENV

success ".env written at $APP_DIR/.env"

# =============================================================================
#  STEP 6 — Database: restore dump OR run fresh migrations
# =============================================================================
step "Setting up database"

DUMP_FILE="$APP_DIR/haap_backup.sql"

if [[ -f "$DUMP_FILE" ]]; then
    info "Found haap_backup.sql — restoring database..."
    mysql -u root -p"${DB_ROOT_PASS}" "${DB_NAME}" < "$DUMP_FILE"
    success "Database restored from dump"
else
    warn "No haap_backup.sql found — running fresh migrations + seeding location data"
    cd "$APP_DIR"
    "$VENV_DIR/bin/python" manage.py migrate --run-syncdb
    success "Migrations applied"

    if [[ -f "$APP_DIR/munic.xlsx" ]]; then
        info "Seeding location data from munic.xlsx..."
        cd "$APP_DIR"
        "$VENV_DIR/bin/python" read_excel.py
        success "Location data seeded"
    else
        warn "munic.xlsx not found — location data not seeded"
    fi

    info "Creating default superuser (admin@haap.tl / Admin@1234)"
    cd "$APP_DIR"
    "$VENV_DIR/bin/python" manage.py shell <<PYEOF
from core.models import User
if not User.objects.filter(email='admin@haap.tl').exists():
    u = User.objects.create_superuser(
        whatsapp_number='00000000000',
        email='admin@haap.tl',
        password='Admin@1234',
        first_name='System',
        last_name='Admin',
        role='moe_admin',
    )
    print('Superuser created: admin@haap.tl / Admin@1234')
else:
    print('Superuser already exists')
PYEOF
fi

# =============================================================================
#  STEP 7 — Media files
# =============================================================================
step "Setting up media files"

MEDIA_TAR="$APP_DIR/haap_media.tar.gz"
if [[ -f "$MEDIA_TAR" ]]; then
    info "Found haap_media.tar.gz — extracting..."
    tar -xzf "$MEDIA_TAR" -C "$APP_DIR"
    success "Media files restored"
else
    warn "No haap_media.tar.gz found — media/apk and media/users will be empty"
fi

# Ensure default profile image placeholder exists
touch "$APP_DIR/media/apk/.keep"

# =============================================================================
#  STEP 8 — Permissions
# =============================================================================
step "Setting file permissions"

# Apache (www-data) needs write access to media only
chown -R www-data:www-data "$APP_DIR/media"
# Everything else owned by root, readable by www-data
chown -R root:www-data "$APP_DIR"
chmod -R 755 "$APP_DIR"
chmod 640 "$APP_DIR/.env"
chmod -R 775 "$APP_DIR/media"

success "Permissions set"

# =============================================================================
#  STEP 9 — Static files
# =============================================================================
step "Collecting static files"

cd "$APP_DIR"
"$VENV_DIR/bin/python" manage.py collectstatic --noinput -v 0 2>/dev/null || \
    warn "collectstatic skipped (STATIC_ROOT not configured — static served directly)"

# =============================================================================
#  STEP 10 — Apache virtual host
# =============================================================================
step "Configuring Apache"

cat > "$APACHE_CONF" <<APACHECONF
<VirtualHost *:80>
    ServerName ${SERVER_IP}

    ErrorLog \${APACHE_LOG_DIR}/error.log
    CustomLog \${APACHE_LOG_DIR}/access.log combined

    WSGIDaemonProcess haap_new \\
        python-home=${VENV_DIR} \\
        python-path=${APP_DIR}

    WSGIProcessGroup haap_new
    WSGIScriptAlias / ${APP_DIR}/haap_platform/wsgi.py

    <Directory ${APP_DIR}/haap_platform>
        <Files wsgi.py>
            Require all granted
        </Files>
    </Directory>

    Alias /static/ ${APP_DIR}/static/
    Alias /media/  ${APP_DIR}/media/

    <Directory ${APP_DIR}/static>
        Require all granted
    </Directory>

    <Directory ${APP_DIR}/media>
        Require all granted
    </Directory>

</VirtualHost>
APACHECONF

# Disable default site, enable haap
a2dissite 000-default.conf 2>/dev/null || true
a2ensite haap.conf

# Test config before restarting
apache2ctl configtest && systemctl restart apache2
success "Apache configured and restarted"

# =============================================================================
#  DONE
# =============================================================================
echo ""
echo -e "${GREEN}${BOLD}╔══════════════════════════════════════════════════════╗${NC}"
echo -e "${GREEN}${BOLD}║   HAAP Platform installed successfully!              ║${NC}"
echo -e "${GREEN}${BOLD}╚══════════════════════════════════════════════════════╝${NC}"
echo ""
echo -e "  URL:       ${CYAN}http://${SERVER_IP}/${NC}"
echo -e "  App:       ${APP_DIR}"
echo -e "  Logs:      /var/log/apache2/error.log"
echo -e "  DB:        ${DB_NAME} @ localhost:3306"
echo ""
if [[ ! -f "$DUMP_FILE" ]]; then
    echo -e "  ${YELLOW}Default admin login:${NC}"
    echo -e "    Email:    admin@haap.tl"
    echo -e "    Password: Admin@1234"
    echo -e "  ${RED}Change this password immediately after first login!${NC}"
fi
echo ""
echo -e "  To restart Apache:  ${CYAN}service apache2 restart${NC}"
echo -e "  To view errors:     ${CYAN}tail -f /var/log/apache2/error.log${NC}"
echo ""
