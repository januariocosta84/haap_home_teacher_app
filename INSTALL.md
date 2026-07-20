# HAAP Platform — Installation Guide

**Stack:** Ubuntu 24.04 LTS · Python 3.12 · Django 4.2 · MySQL 8.0 · Apache 2.4 + mod_wsgi

---

## Quick Install (Automated)

If you just want to run the script:

```bash
# 1. Transfer files to new server (run on OLD server)
tar -czf haap_media.tar.gz -C /var/www/new_app/haap_app media
mysqldump -u root -pPaddington2025yoyo haap > haap_backup.sql
scp -r /var/www/new_app/haap_app/ root@NEW_SERVER_IP:/var/www/new_app/haap_app/
scp haap_backup.sql haap_media.tar.gz root@NEW_SERVER_IP:/var/www/new_app/haap_app/

# 2. On the NEW server
chmod +x /var/www/new_app/haap_app/install.sh
sudo bash /var/www/new_app/haap_app/install.sh
```

---

## Manual Installation (Step by Step)

### Prerequisites

- Fresh Ubuntu 24.04 LTS server
- Root or sudo access
- The project files transferred to `/var/www/new_app/haap_app/`

---

### Step 1 — System Packages

```bash
apt-get update
apt-get install -y \
    python3.12 python3.12-venv python3.12-dev \
    apache2 libapache2-mod-wsgi-py3 \
    mysql-server libmysqlclient-dev \
    pkg-config build-essential git curl wget
```

Enable the WSGI Apache module:
```bash
a2enmod wsgi
```

---

### Step 2 — MySQL Database

```bash
# Start MySQL
systemctl start mysql
systemctl enable mysql

# Secure and configure
mysql -u root
```

Inside the MySQL prompt:
```sql
ALTER USER 'root'@'localhost' IDENTIFIED WITH mysql_native_password BY 'YourStrongPassword';
CREATE DATABASE haap CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci;
FLUSH PRIVILEGES;
EXIT;
```

**Restore database from backup** (if you have a dump from the old server):
```bash
mysql -u root -p haap < haap_backup.sql
```

---

### Step 3 — Application Directory

```bash
mkdir -p /var/www/new_app/haap_app/media/apk
mkdir -p /var/www/new_app/haap_app/media/users
```

Place your project files in `/var/www/new_app/haap_app/`.

---

### Step 4 — Python Virtual Environment

```bash
cd /var/www/new_app/haap_app

# Create virtual environment
python3.12 -m venv .venv

# Activate and install packages
.venv/bin/pip install --upgrade pip
.venv/bin/pip install -r requirements.txt
```

---

### Step 5 — Environment File (.env)

Create `/var/www/new_app/haap_app/.env`:

```env
SECRET_KEY=your-long-random-secret-key-here

# Django
DEBUG=False
ALLOWED_HOSTS=127.0.0.1,localhost,YOUR_SERVER_IP

# MySQL
DB_NAME=haap
DB_USER=root
DB_PASSWORD=YourStrongPassword
DB_HOST=localhost
DB_PORT=3306

# Email (optional — Gmail example)
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_HOST_USER=your_email@gmail.com
EMAIL_HOST_PASSWORD=your_app_password
EMAIL_USE_TLS=True
```

Generate a secure SECRET_KEY:
```bash
python3.12 -c "import secrets, string; print(''.join(secrets.choice(string.ascii_letters+string.digits+'!@#\$%^&*') for _ in range(50)))"
```

---

### Step 6 — Django Setup

**Option A — Fresh install (no database dump):**
```bash
cd /var/www/new_app/haap_app

# Run migrations
.venv/bin/python manage.py migrate

# Seed location data (municipality, admin posts, sucos, aldeias)
.venv/bin/python read_excel.py

# Create first admin user
.venv/bin/python manage.py shell
```
In the shell:
```python
from core.models import User
User.objects.create_superuser(
    whatsapp_number='00000000000',
    email='admin@haap.tl',
    password='Admin@1234',
    first_name='System',
    last_name='Admin',
    role='moe_admin',
)
exit()
```

**Option B — Restore from backup:**
```bash
mysql -u root -p haap < haap_backup.sql
```

---

### Step 7 — Media Files

If you have a media archive from the old server:
```bash
cd /var/www/new_app/haap_app
tar -xzf haap_media.tar.gz
```

---

### Step 8 — File Permissions

```bash
# Apache (www-data) needs write access to media
chown -R www-data:www-data /var/www/new_app/haap_app/media

# App files — root owns, www-data can read
chown -R root:www-data /var/www/new_app/haap_app
chmod -R 755 /var/www/new_app/haap_app
chmod 640 /var/www/new_app/haap_app/.env
chmod -R 775 /var/www/new_app/haap_app/media
```

---

### Step 9 — Apache Virtual Host

Create `/etc/apache2/sites-available/haap.conf`:

```apache
<VirtualHost *:80>
    ServerName YOUR_SERVER_IP

    ErrorLog ${APACHE_LOG_DIR}/error.log
    CustomLog ${APACHE_LOG_DIR}/access.log combined

    WSGIDaemonProcess haap_new \
        python-home=/var/www/new_app/haap_app/.venv \
        python-path=/var/www/new_app/haap_app

    WSGIProcessGroup haap_new
    WSGIScriptAlias / /var/www/new_app/haap_app/haap_platform/wsgi.py

    <Directory /var/www/new_app/haap_app/haap_platform>
        <Files wsgi.py>
            Require all granted
        </Files>
    </Directory>

    Alias /static/ /var/www/new_app/haap_app/static/
    Alias /media/  /var/www/new_app/haap_app/media/

    <Directory /var/www/new_app/haap_app/static>
        Require all granted
    </Directory>

    <Directory /var/www/new_app/haap_app/media>
        Require all granted
    </Directory>

</VirtualHost>
```

Enable and restart:
```bash
a2dissite 000-default.conf
a2ensite haap.conf
apache2ctl configtest        # must say "Syntax OK"
systemctl restart apache2
```

---

### Step 10 — Verify

```bash
# Check Apache is running
systemctl status apache2

# Check for errors
tail -50 /var/log/apache2/error.log

# Test the site
curl -s -o /dev/null -w "%{http_code}" http://localhost/login/
# Should return 200
```

---

## Files to Transfer Between Servers

| What | Command (on OLD server) |
|---|---|
| App code | `scp -r /var/www/new_app/haap_app/ root@NEW_IP:/var/www/new_app/` |
| Database | `mysqldump -u root -p haap > haap_backup.sql` then `scp` |
| Media files | `tar -czf haap_media.tar.gz -C /var/www/new_app/haap_app media` then `scp` |

Place `haap_backup.sql` and `haap_media.tar.gz` inside `/var/www/new_app/haap_app/` — the install script will detect and use them automatically.

---

## Common Commands

| Task | Command |
|---|---|
| Restart server | `service apache2 restart` |
| View errors | `tail -f /var/log/apache2/error.log` |
| Django shell | `cd /var/www/new_app/haap_app && .venv/bin/python manage.py shell` |
| Run migrations | `.venv/bin/python manage.py migrate` |
| Seed locations | `.venv/bin/python read_excel.py` |
| DB backup | `mysqldump -u root -p haap > haap_backup.sql` |
| DB restore | `mysql -u root -p haap < haap_backup.sql` |

---

## Project Structure

```
/var/www/new_app/haap_app/
├── .env                        ← secret config (never commit to git)
├── .venv/                      ← Python virtual environment
├── install.sh                  ← this install script
├── manage.py
├── requirements.txt
├── munic.xlsx                  ← location seed data (municipality/suco/aldeia)
├── read_excel.py               ← location data seeder script
├── haap_platform/
│   ├── settings.py
│   ├── urls.py
│   └── wsgi.py
├── core/                       ← users, children, APK, auth
├── preschools/                 ← preschool management
├── klase/                      ← classroom management
├── equipment/                  ← equipment tracking
├── ticket/                     ← support tickets
├── templates/                  ← all HTML templates
├── static/                     ← CSS, JS, images
└── media/                      ← user uploads (profile pics, APK files)
    ├── apk/                    ← uploaded APK files
    └── users/                  ← user profile images
```

---

## Key Settings

| Setting | Value | Where |
|---|---|---|
| `DEBUG` | `False` in production | `.env` |
| `ALLOWED_HOSTS` | Server IP / domain | `.env` |
| `X_FRAME_OPTIONS` | `SAMEORIGIN` | `settings.py` |
| `LOGIN_URL` | `/login/` | `settings.py` |
| `MEDIA_ROOT` | `haap_app/media/` | `settings.py` |
| Default profile image | `media/apk/user.jpg` | `settings.py` |

---

## After Installation

1. Open `http://YOUR_SERVER_IP/` in a browser
2. Log in with your admin credentials
3. Go to **Users** and create your real `moe_admin` account
4. If fresh install: delete the default `admin@haap.tl` superuser
5. Change `ALLOWED_HOSTS` in `.env` to your actual server IP/domain
6. Run `service apache2 restart` after any `.env` or code change
