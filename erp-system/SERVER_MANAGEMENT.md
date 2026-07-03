# Server Management Guide

**Server IP:** 72.61.174.119
**Domain:** https://senovkaplastics.cloud
**Project Path:** `/var/www/erp-system/erp-system`
**Venv Path:** `/var/www/erp-system/.venv`

---

## SSH into Server

```bash
ssh root@72.61.174.119
```

---

## Activate Virtual Environment

Always run this first before any Python/Django commands:

```bash
source /var/www/erp-system/.venv/bin/activate
cd /var/www/erp-system/erp-system
```

---

## Deploy Updates from GitHub

> **Important:** Push your local changes to GitHub first, THEN pull on the server.

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

If the status shows errors: `journalctl -u erp -n 50 --no-pager`

---

## Database — Clean & Migrate (Option 1)

> **Warning:** This deletes ALL data permanently. Take a backup first.

### Step 1 — Backup existing database (safety first)
```bash
cp /var/www/erp-system/erp-system/db.sqlite3 /root/db_backup_$(date +%F_%H%M).sqlite3
```

### Step 2 — SSH in and activate environment
```bash
ssh root@72.61.174.119
source /var/www/erp-system/.venv/bin/activate
cd /var/www/erp-system/erp-system
```

### Step 3 — Delete the database
```bash
rm db.sqlite3
```

### Step 4 — Run migrations (creates fresh database)
```bash
python manage.py migrate
```

### Step 5 — Create users (SuperAdmin + Admin)
```bash
python seed_users.py
```

This creates:
| Username | Password | Role |
|---|---|---|
| `superadmin` | `superadmin123` | Super Admin |
| `admin` | `admin123` | Admin |

> Change passwords at `/profile/` after first login.

### Step 6 — Restart the app
```bash
systemctl restart erp
```

---

## Seed Data (Option 2)

Use this to add sample categories, products, and customers to an existing database — does NOT delete any data.

### Step 1 — SSH in and activate environment
```bash
ssh root@72.61.174.119
source /var/www/erp-system/.venv/bin/activate
cd /var/www/erp-system/erp-system
```

### Step 2 — Seed users (SuperAdmin + Admin)
```bash
python seed_users.py
```

### Step 3 — Seed sample data (optional)
```bash
python seed_data.py
```

This adds:
- 5 product categories (Fiber, Foam, Roof Tiles, Pipes, Hardware)
- 20 products across categories
- 15 sample customers with balances
- Customer-specific pricing for select customers

> Safe to run multiple times — uses `get_or_create` so nothing is duplicated.

---

## Full Fresh Setup (clean install on server)

Run these steps in order after a fresh git clone or full reset:

```bash
ssh root@72.61.174.119
source /var/www/erp-system/.venv/bin/activate
cd /var/www/erp-system/erp-system

# 1. Remove old database
rm -f db.sqlite3

# 2. Apply all migrations
python manage.py migrate

# 3. Collect static files
python manage.py collectstatic --no-input

# 4. Create users
python seed_users.py

# 5. (Optional) Load sample data
python seed_data.py

# 6. Restart app
systemctl restart erp
```

---

## Restart / Stop / Start the App

```bash
systemctl restart erp     # restart
systemctl stop erp        # stop
systemctl start erp       # start
systemctl status erp      # check if running
```

## Restart Nginx

```bash
systemctl reload nginx    # reload config
systemctl restart nginx   # full restart
```

---

## View App Logs (for debugging errors)

```bash
journalctl -u erp -n 50 --no-pager
journalctl -u erp -f          # live tail
```

---

## Backup the Database

```bash
cp /var/www/erp-system/erp-system/db.sqlite3 /root/db_backup_$(date +%F_%H%M).sqlite3
```

List all backups:
```bash
ls -lh /root/db_backup_*.sqlite3
```

Restore a backup:
```bash
cp /root/db_backup_YYYY-MM-DD_HHMM.sqlite3 /var/www/erp-system/erp-system/db.sqlite3
systemctl restart erp
```

---

## User Role Reference

| Role | Can Do |
|---|---|
| **Super Admin** | Everything + manage users at `/users/` + filter activity logs by user |
| **Admin** | Everything — billing, production, customers, bookings, petty cash, purchasing |

Seed script creates both. Only difference: Super Admin manages who has access.

---

## Full Deploy Workflow (code changes)

1. Make changes locally and push to GitHub:
   ```powershell
   git add .
   git commit -m "your message"
   git push
   ```

2. Pull and deploy on server:
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

   > If the status shows errors, check logs: `journalctl -u erp -n 50 --no-pager`
