# Server Management Guide

**Server IP:** 72.61.174.119
**SSH:** `ssh root@72.61.174.119`

This server now runs **two independent Django apps**. They share nothing — separate code, separate virtualenvs, separate SQLite databases, separate services, separate subdomains. Work on one never affects the other.

---

## Quick Reference — Two Apps

| | **Main ERP** | **Purchase ERP** |
|---|---|---|
| **Domain** | https://senovkaplastics.cloud | https://purchase.senovkaplastics.cloud |
| **Project path** | `/var/www/erp-system/erp-system` | `/var/www/purchase/erp-system` |
| **Venv path** | `/var/www/erp-system/.venv` | `/var/www/purchase/erp-system/.venv` |
| **Service name** | `erp` | `purchase` |
| **Gunicorn port** | (existing) | `127.0.0.1:8001` |
| **Database** | `.../erp-system/erp-system/db.sqlite3` | `/var/www/purchase/erp-system/db.sqlite3` |
| **Static files** | `.../staticfiles` | `/var/www/purchase/erp-system/staticfiles` |
| **Nginx config** | `/etc/nginx/sites-available/senovkaplastics.cloud` | `/etc/nginx/sites-available/purchase.senovkaplastics.cloud` |
| **systemd file** | `/etc/systemd/system/erp.service` | `/etc/systemd/system/purchase.service` |
| **File owner** | root | `www-data` |

> **Watch the venv difference.** The main ERP's venv sits *beside* the project (`/var/www/erp-system/.venv`). The purchase app's venv is *inside* it (`/var/www/purchase/erp-system/.venv`). Easy to mix up.

---

## Activate Virtual Environment

Always run this first before any Python/Django commands.

**Main ERP:**
```bash
source /var/www/erp-system/.venv/bin/activate
cd /var/www/erp-system/erp-system
```

**Purchase ERP:**
```bash
source /var/www/purchase/erp-system/.venv/bin/activate
cd /var/www/purchase/erp-system
```

---

## Restart / Stop / Start / Status

**Main ERP:**
```bash
systemctl restart erp
systemctl stop erp
systemctl start erp
systemctl status erp
```

**Purchase ERP:**
```bash
systemctl restart purchase
systemctl stop purchase
systemctl start purchase
systemctl status purchase
```

**Nginx (shared by both):**
```bash
systemctl reload nginx    # reload config (use after editing a site)
systemctl restart nginx   # full restart
nginx -t                  # test config BEFORE reloading
```

---

## Deploy Updates from GitHub

> **Important:** Push your local changes to GitHub first, THEN pull on the server.

### Main ERP
```bash
ssh root@72.61.174.119
cd /var/www/erp-system/erp-system
git pull
source /var/www/erp-system/.venv/bin/activate
pip install -r requirements.txt
python manage.py migrate
python manage.py collectstatic --no-input
systemctl restart erp
systemctl status erp
```

### Purchase ERP
> This repo has the Django project nested one level down, and its files are owned by `www-data`. After pulling as root, re-fix ownership so the app can still write to its SQLite database.

```bash
ssh root@72.61.174.119
cd /var/www/purchase/erp-system
git pull
source /var/www/purchase/erp-system/.venv/bin/activate
pip install -r requirements.txt
python manage.py migrate
python manage.py collectstatic --no-input
chown -R www-data:www-data /var/www/purchase     # restore write access to db.sqlite3
systemctl restart purchase
systemctl status purchase
```

If either status shows errors, check logs (see below).

---

## View App Logs (for debugging)

**Main ERP:**
```bash
journalctl -u erp -n 50 --no-pager
journalctl -u erp -f          # live tail
```

**Purchase ERP:**
```bash
journalctl -u purchase -n 50 --no-pager
journalctl -u purchase -f     # live tail
```

---

## Backup the Database

**Main ERP:**
```bash
cp /var/www/erp-system/erp-system/db.sqlite3 /root/erp_backup_$(date +%F_%H%M).sqlite3
```

**Purchase ERP:**
```bash
cp /var/www/purchase/erp-system/db.sqlite3 /root/purchase_backup_$(date +%F_%H%M).sqlite3
```

**List all backups:**
```bash
ls -lh /root/*_backup_*.sqlite3
```

**Restore a backup (example — Purchase):**
```bash
cp /root/purchase_backup_YYYY-MM-DD_HHMM.sqlite3 /var/www/purchase/erp-system/db.sqlite3
chown www-data:www-data /var/www/purchase/erp-system/db.sqlite3
systemctl restart purchase
```

---

## Database — Clean & Migrate

> **Warning:** This deletes ALL data permanently. Take a backup first.

### Main ERP
```bash
# 1. Backup
cp /var/www/erp-system/erp-system/db.sqlite3 /root/erp_backup_$(date +%F_%H%M).sqlite3
# 2. Activate + cd
source /var/www/erp-system/.venv/bin/activate
cd /var/www/erp-system/erp-system
# 3. Delete + rebuild
rm db.sqlite3
python manage.py migrate
python seed_users.py
systemctl restart erp
```

### Purchase ERP
```bash
# 1. Backup
cp /var/www/purchase/erp-system/db.sqlite3 /root/purchase_backup_$(date +%F_%H%M).sqlite3
# 2. Activate + cd
source /var/www/purchase/erp-system/.venv/bin/activate
cd /var/www/purchase/erp-system
# 3. Delete + rebuild
rm db.sqlite3
python manage.py migrate
python seed_users.py
chown -R www-data:www-data /var/www/purchase     # IMPORTANT for purchase app
systemctl restart purchase
```

**Seed users creates:**

| Username | Password | Role |
|---|---|---|
| `superadmin` | `superadmin123` | Super Admin |
| `admin` | `admin123` | Admin |

> Change passwords at `/profile/` after first login.

---

## Seed Sample Data (does NOT delete anything)

Adds sample categories, products, and customers to an existing database. Safe to run multiple times (`get_or_create`).

**Main ERP:**
```bash
source /var/www/erp-system/.venv/bin/activate
cd /var/www/erp-system/erp-system
python seed_users.py
python seed_data.py
```

**Purchase ERP:**
```bash
source /var/www/purchase/erp-system/.venv/bin/activate
cd /var/www/purchase/erp-system
python seed_users.py
python seed_data.py
chown -R www-data:www-data /var/www/purchase
```

Adds: 5 categories (Fiber, Foam, Roof Tiles, Pipes, Hardware), 20 products, 15 customers with balances, and customer-specific pricing.

---

## Full Fresh Setup (clean install)

### Purchase ERP (from scratch, matching how it was deployed)
```bash
# Clone (folder forced to "purchase")
cd /var/www
git clone https://github.com/pathumlak/purchase_senovka.git purchase
cd /var/www/purchase/erp-system

# Virtualenv + deps
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt gunicorn

# Django setup
python manage.py migrate
python manage.py collectstatic --no-input

# Ownership (service runs as www-data; SQLite needs write access to the folder)
chown -R www-data:www-data /var/www/purchase

# Service
systemctl daemon-reload
systemctl enable --now purchase
systemctl status purchase
```

---

## SSL / HTTPS Renewal

Both certs auto-renew via certbot's timer. To check or force:

```bash
certbot certificates          # list all certs + expiry
certbot renew --dry-run       # test renewal without changing anything
certbot renew                 # force a renewal check
systemctl reload nginx        # apply after renewal
```

To issue a cert for a brand-new subdomain:
```bash
certbot --nginx -d NEWSUB.senovkaplastics.cloud
```

---

## The `purchase.service` File (reference)

Located at `/etc/systemd/system/purchase.service`:

```ini
[Unit]
Description=Purchase ERP (Django)
After=network.target

[Service]
User=www-data
Group=www-data
WorkingDirectory=/var/www/purchase/erp-system
ExecStart=/var/www/purchase/erp-system/.venv/bin/gunicorn --workers 3 --bind 127.0.0.1:8001 erp.wsgi:application

[Install]
WantedBy=multi-user.target
```

After editing it: `systemctl daemon-reload && systemctl restart purchase`

---

## The Purchase Nginx Block (reference)

Located at `/etc/nginx/sites-available/purchase.senovkaplastics.cloud` (certbot added the SSL/443 section automatically — the HTTP block below is the original):

```nginx
server {
    listen 80;
    server_name purchase.senovkaplastics.cloud;

    location / {
        proxy_pass http://127.0.0.1:8001;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    location /static/ {
        alias /var/www/purchase/erp-system/staticfiles/;
    }

    location /media/ {
        alias /var/www/purchase/erp-system/media/;
    }
}
```

---

## User Role Reference

| Role | Can Do |
|---|---|
| **Super Admin** | Everything + manage users at `/users/` + filter activity logs by user |
| **Admin** | Everything — billing, production, customers, bookings, petty cash, purchasing |

---

## Common Gotchas

- **Wrong app restarted?** Double-check the service name — `erp` vs `purchase`. They're independent.
- **Purchase site works but can't save data** → ownership got reset (usually after a `git pull` as root). Fix: `chown -R www-data:www-data /var/www/purchase && systemctl restart purchase`
- **Site loads with no styling** → run `collectstatic`, and confirm the Nginx `/static/` alias path is right.
- **400 Bad Request in browser** → the domain isn't in `ALLOWED_HOSTS` in `erp/settings.py`. (A `400` from `curl http://127.0.0.1:8001` is *normal* — that's the bare-IP being rejected.)
- **Port conflict** → the purchase app must stay on `8001`. Never point both apps at the same port.
- **Never edit `settings_local.py` for production** — it has `DEBUG=True`. The live services use `erp/settings.py` (`DEBUG=False`).