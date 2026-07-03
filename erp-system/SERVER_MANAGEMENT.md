# Server Management Guide

**Server IP:** 72.61.174.119
**SSH:** `ssh root@72.61.174.119`

This server runs **two independent Django apps**. They share nothing — separate code,
virtualenvs, SQLite databases, systemd services, and subdomains. Work on one never
affects the other.

| | **Main ERP** | **Purchase ERP** |
|---|---|---|
| **Domain** | https://senovkaplastics.cloud | https://purchase.senovkaplastics.cloud |
| **Project path** | `/var/www/erp-system/erp-system` | `/var/www/purchase/erp-system` |
| **Virtualenv** | `/var/www/erp-system/.venv` (beside project) | `/var/www/purchase/erp-system/.venv` (inside project) |
| **systemd service** | `erp` | `purchase` |
| **Gunicorn bind** | (existing) | `127.0.0.1:8001` |
| **Database** | `.../erp-system/erp-system/db.sqlite3` | `/var/www/purchase/erp-system/db.sqlite3` |
| **Static files** | `.../staticfiles` | `/var/www/purchase/erp-system/staticfiles` |
| **Nginx config** | `/etc/nginx/sites-available/senovkaplastics.cloud` | `/etc/nginx/sites-available/purchase.senovkaplastics.cloud` |
| **Runs as user** | root | **`www-data`** |

> ⚠️ **The single most important rule for the Purchase app:** its service runs as
> **`www-data`**, but you log in and run commands as **root**. Every time you touch its
> files as root (git pull, edit, reset DB), ownership flips to root and the app can no
> longer write its SQLite database → **500 errors**. So **every root operation on the
> Purchase app must end with:**
>
> ```bash
> chown -R www-data:www-data /var/www/purchase
> systemctl restart purchase
> ```

---

## 0. Two things that WILL bite you (read first)

### A. `fatal: detected dubious ownership in repository`
Git refuses to run because the repo is owned by `www-data` while you're root. Fix once
(persists for future sessions):

```bash
git config --global --add safe.directory /var/www/purchase
```

Now `git pull` works. (This does not change file ownership — it just tells git it's OK.)

### B. Login gives "Server Error (500)" on the Purchase app
Almost always a **read-only database**: a fresh or root-owned `db.sqlite3` can't be
written by the `www-data` service, and logging in needs to write a session row.

```bash
chown -R www-data:www-data /var/www/purchase
systemctl restart purchase
```

Confirm the real cause anytime with:

```bash
journalctl -u purchase -n 40 --no-pager
```

Look for `OperationalError: attempt to write a readonly database` → that's this issue.

---

## 1. Deploy an update (pull latest code) — PURCHASE APP

Push your local changes to GitHub **first**, then run on the server:

```bash
ssh root@72.61.174.119
git config --global --add safe.directory /var/www/purchase   # once, if not set
cd /var/www/purchase/erp-system

git pull
source .venv/bin/activate
pip install -r requirements.txt        # only if dependencies changed
python manage.py migrate               # applies any new DB migrations
python manage.py collectstatic --no-input

# ALWAYS finish with these two (root pull flipped ownership):
chown -R www-data:www-data /var/www/purchase
systemctl restart purchase
systemctl status purchase --no-pager | head -6
```

Then hard-refresh the site in the browser (**Ctrl+Shift+R**) to bypass cached CSS.

- `git pull` should say it's updating (e.g. `ddcec57..bff7e74`). If it says
  **"Already up to date"** but you expected changes, you pushed to a different
  branch/remote than the server tracks — check `git log --oneline -3` and
  `git remote -v`.
- `systemctl status` must show **`active (running)`**.

### Main ERP (for reference)
```bash
ssh root@72.61.174.119
cd /var/www/erp-system/erp-system
git pull
source /var/www/erp-system/.venv/bin/activate
pip install -r requirements.txt
python manage.py migrate
python manage.py collectstatic --no-input
systemctl restart erp
systemctl status erp --no-pager | head -6
```
(The Main ERP runs as root, so it does **not** need the `chown` step.)

---

## 2. Start / stop / restart / status

```bash
systemctl restart purchase     # or: erp
systemctl stop purchase
systemctl start purchase
systemctl status purchase --no-pager
```

**Nginx (shared by both apps):**
```bash
nginx -t                # ALWAYS test config before reloading
systemctl reload nginx  # apply config changes
systemctl restart nginx # full restart
```

---

## 3. View logs (debugging)

```bash
journalctl -u purchase -n 50 --no-pager   # last 50 lines
journalctl -u purchase -f                 # live tail (Ctrl+C to stop)
```
Swap `purchase` for `erp` for the Main app.

---

## 4. Back up the database

```bash
# Purchase
cp /var/www/purchase/erp-system/db.sqlite3 /root/purchase_backup_$(date +%F_%H%M).sqlite3

# Main
cp /var/www/erp-system/erp-system/db.sqlite3 /root/erp_backup_$(date +%F_%H%M).sqlite3

ls -lh /root/*_backup_*.sqlite3           # list backups
```

**Restore a Purchase backup:**
```bash
cp /root/purchase_backup_YYYY-MM-DD_HHMM.sqlite3 /var/www/purchase/erp-system/db.sqlite3
chown -R www-data:www-data /var/www/purchase
systemctl restart purchase
```

---

## 5. Reset the database (wipe + rebuild) — PURCHASE APP

> 🔴 **DELETES ALL PURCHASE DATA PERMANENTLY.** Back up first (step 4).

```bash
# 1. Backup
cp /var/www/purchase/erp-system/db.sqlite3 /root/purchase_backup_$(date +%F_%H%M).sqlite3

# 2. Activate + cd
source /var/www/purchase/erp-system/.venv/bin/activate
cd /var/www/purchase/erp-system

# 3. Delete + rebuild schema
rm db.sqlite3
python manage.py migrate

# 4. Seed logins + sample data
python seed_users.py     # creates superadmin / admin
python seed_data.py      # sample categories, products, customers, pricing (optional)

# 5. Restore ownership (a root-created db.sqlite3 is NOT writable by www-data) + restart
chown -R www-data:www-data /var/www/purchase
systemctl restart purchase
systemctl status purchase --no-pager | head -6
```

**Default logins after reset:**

| Username | Password | Role |
|---|---|---|
| `superadmin` | `superadmin123` | Super Admin |
| `admin` | `admin123` | Admin |

> Change these at `/profile/` immediately after first login.

`seed_data.py` adds: 5 categories (Fiber, Foam, Roof Tiles, Pipes, Hardware),
20 products, 15 customers with balances, and customer-specific pricing.
It uses `get_or_create`, so it's safe to run on an existing DB without duplicating.

---

## 6. SSL / HTTPS

Both certs auto-renew via certbot's timer.

```bash
certbot certificates          # list certs + expiry
certbot renew --dry-run       # test renewal
certbot renew                 # force renewal check
systemctl reload nginx        # apply after a renewal

# issue a cert for a brand-new subdomain:
certbot --nginx -d NEWSUB.senovkaplastics.cloud
```

---

## 7. Troubleshooting cheat sheet

| Symptom | Cause | Fix |
|---|---|---|
| `fatal: detected dubious ownership` on git | repo owned by www-data, you're root | `git config --global --add safe.directory /var/www/purchase` |
| **500 right after clicking Sign In** | read-only SQLite (ownership reset) | `chown -R www-data:www-data /var/www/purchase && systemctl restart purchase` |
| Site works but **can't save data** | same ownership issue | same as above |
| **400 Bad Request** in browser | domain missing from `ALLOWED_HOSTS` in `erp/settings.py` | add the domain, restart. (A `400` from `curl http://127.0.0.1:8001` is normal.) |
| Site loads **with no styling** | static not collected / wrong nginx alias | `collectstatic --no-input`, then re-chown; check nginx `/static/` alias path |
| **Wrong app restarted** | `erp` vs `purchase` mixed up | they're independent — double-check the service name |
| **Port conflict** | both apps on same port | Purchase must stay on `127.0.0.1:8001`; never share a port |
| CSS changes not showing | browser cache | hard refresh (Ctrl+Shift+R); confirm `collectstatic` ran |

---

## 8. Reference — Purchase service & nginx

**`/etc/systemd/system/purchase.service`:**
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

**`/etc/nginx/sites-available/purchase.senovkaplastics.cloud`** (HTTP block; certbot adds the 443/SSL block automatically):
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

    location /static/ { alias /var/www/purchase/erp-system/staticfiles/; }
    location /media/  { alias /var/www/purchase/erp-system/media/; }
}
```

---

## 9. First-time setup (clone from scratch) — PURCHASE APP

```bash
cd /var/www
git clone https://github.com/pathumlak/purchase_senovka.git purchase
cd /var/www/purchase/erp-system

python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt gunicorn

python manage.py migrate
python manage.py collectstatic --no-input
python seed_users.py

chown -R www-data:www-data /var/www/purchase
systemctl daemon-reload
systemctl enable --now purchase
systemctl status purchase --no-pager
```

---

## Golden rules

1. **Push to GitHub first, then pull on the server.** Never edit code directly on the server.
2. **Every root action on `/var/www/purchase` ends with `chown -R www-data:www-data /var/www/purchase` + `systemctl restart purchase`.**
3. **Back up the database before any reset or risky change.**
4. **`nginx -t` before every `systemctl reload nginx`.**
5. **Never edit `settings_local.py` for production** — it has `DEBUG=True`. The live
   services use `erp/settings.py` (`DEBUG=False`).
