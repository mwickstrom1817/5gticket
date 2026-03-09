# 🔒 5G Security — Customer Portal

A Streamlit-based customer portal for 5G Security. Customers can view system health, browse installed equipment, and submit support tickets. You manage everything from a dedicated admin panel.

---

## Tech Stack
- **Frontend:** Streamlit
- **Database:** Neon (PostgreSQL)
- **File Storage:** Cloudflare R2
- **Email:** SMTP (Gmail / Outlook / any provider)
- **Auth:** Session-based with bcrypt password hashing

---

## Project Structure
```
app.py                        ← Main entry point & navigation
pages/
  admin_dashboard.py          ← Admin: overview, open tickets, system health
  admin_customers.py          ← Admin: add/edit customers, assign portal logins, set system health
  admin_equipment.py          ← Admin: add/edit equipment per customer
  admin_tickets.py            ← Admin: manage & respond to tickets
  customer_dashboard.py       ← Customer: system health cards + recent tickets
  customer_equipment.py       ← Customer: view installed equipment
  customer_tickets.py         ← Customer: ticket history
  submit_ticket.py            ← Customer: submit a new ticket
utils/
  db.py                       ← Neon DB connection + schema init + helpers
  auth.py                     ← Login, logout, password hashing, role enforcement
  storage.py                  ← Cloudflare R2 upload/delete
  email_notify.py             ← SMTP email notifications
.streamlit/
  secrets.toml.template       ← Copy → secrets.toml and fill in your values
requirements.txt
```

---

## Setup

### 1. Clone and install
```bash
git clone https://github.com/your-org/5g-customer-portal.git
cd 5g-customer-portal
pip install -r requirements.txt
```

### 2. Configure secrets
```bash
cp .streamlit/secrets.toml.template .streamlit/secrets.toml
# Fill in your Neon, R2, SMTP values
```

### 3. Run locally
```bash
streamlit run app.py
```

### 4. Create your admin account
On first run, the DB tables are auto-created. Then run this once in a Python shell to create your admin login:

```python
import streamlit as st
# Set secrets first, then:
from utils.auth import create_user
create_user("Your Name", "you@5gsecurity.com", "yourpassword", "admin")
```

Or add a one-time admin seed script (see below).

### 5. Deploy to Streamlit Cloud
- Push to GitHub
- Connect repo at share.streamlit.io
- Add your secrets in the Streamlit Cloud dashboard under **Settings → Secrets**

---

## One-Time Admin Seed Script
Save as `seed_admin.py` and run once locally:

```python
import sys
sys.path.insert(0, ".")
import streamlit as st
# Patch secrets for local run if needed
from utils.db import init_db
from utils.auth import create_user

init_db()
create_user("Your Name", "you@5gsecurity.com", "changeme123", "admin")
print("Admin created.")
```

---

## Adding a Customer (workflow)
1. Log in as admin
2. Go to **Manage Customers** → **Add New Customer**
3. Fill in company info, optionally create portal login in same step
4. Go to **Manage Equipment** → add their devices
5. System health defaults to 🟢 Green — update as needed
6. Share the portal URL and their login credentials with the customer

---

## Email Setup (Gmail)
1. Enable 2FA on your Gmail account
2. Generate an App Password: Google Account → Security → App Passwords
3. Use that 16-char password as `SMTP_PASSWORD` in secrets.toml
