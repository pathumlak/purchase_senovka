# Local Development Guide

## Run the server locally

Open a terminal in the project folder (`erp-system/`) and run:

```bash
python manage.py runserver --settings=erp.settings_local
```

Then open your browser at: **http://127.0.0.1:8000**

---

## Login credentials

| Username | Password | Role |
|---|---|---|
| `superadmin` | `superadmin123` | Super Admin — full access |
| `admin` | `admin123` | Admin — no billing / no user management |

> Change passwords after first login at `/profile/`

---

## What the local settings change

| Setting | Production | Local |
|---|---|---|
| `DEBUG` | `False` | `True` (shows full error pages) |
| `ALLOWED_HOSTS` | server IP / domain | `localhost`, `127.0.0.1` |

Everything else (database, apps, models) is identical to production.

---

## First-time setup (if running fresh)

```bash
# 1. Apply migrations
python manage.py migrate --settings=erp.settings_local

# 2. Create superadmin + admin users
python seed_users.py

# 3. (Optional) Load sample data
python seed_data.py

# 4. Start server
python manage.py runserver --settings=erp.settings_local
```

---

## Shortcut — set default settings for the session

Instead of typing `--settings=erp.settings_local` every time, set the environment variable once:

**Windows (PowerShell):**
```powershell
$env:DJANGO_SETTINGS_MODULE = "erp.settings_local"
python manage.py runserver
```

**Windows (Command Prompt):**
```cmd
set DJANGO_SETTINGS_MODULE=erp.settings_local
python manage.py runserver
```

---

## Role differences (quick reference)

| Feature | superadmin | admin |
|---|---|---|
| Dashboard, logs | Yes | Yes |
| Production / Categories / Products | Yes | Yes |
| Customers | Yes | Yes |
| Bookings | Yes | Yes |
| Petty Cash / Purchasing | Yes | Yes |
| **Billing (create/cancel/settle)** | Yes | No |
| **Manage Users** | Yes | No |
| **Filter logs by user** | Yes | No |
