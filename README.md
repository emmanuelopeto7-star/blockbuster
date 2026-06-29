# Blockbuster

A desktop rental management system built with Python and CustomTkinter, styled after a video
rental store. It tracks members, inventory (VHS, DVD, CD, equipment), and rentals through their
full lifecycle: request, approval, and return.

Three roles share the same login screen and get routed to their own dashboard:

- **Customer** — browse available inventory, request rentals, and view personal rental history.
- **Clerk** — register new customers, approve or deny rental requests, and process returns.
- **Admin** — everything Clerk can do, plus managing inventory and registering members of any role.

Rentals require a minimum $100 cash balance and are due back within 7 days; overdue items are
automatically marked `Late`.

## Setup

### Prerequisites
- Python 3.10+ (developed and tested on Python 3.14.5)

### 1. Create and activate a virtual environment

```
python -m venv venv
```

### 2. Install dependencies

```
pip install -r requirements.txt
```

`requirements.txt` installs:

- `customtkinter` — the GUI framework every screen is built with.
- `darkdetect` — OS dark/light mode detection (`customtkinter` dependency).
- `pandas`, `numpy`, `python-dateutil`, `tzdata`, `requests`, `certifi`, `charset-normalizer`,
  `idna`, `urllib3`, `packaging`, `six` — present in the environment but not currently imported
  by `main.py`, `gui_pages.py`, `actions.py`, or `database.py`.

### 3. Run the app

```
python main.py
```

The SQLite database (`blockbuster.db`) is created and seeded automatically on first run.

## Project Structure

- `main.py` — app entry point, initializes the database and launches the GUI.
- `gui_pages.py` — CustomTkinter screens: `LoginScreen`, `CustomerDashboard`, `ClerkDashboard`,
  `AdminDashboard`.
- `actions.py` — business logic: authentication, rentals, inventory, members.
- `database.py` — SQLite schema setup, migrations, and seed data.
- `blockbuster.db` — the SQLite database file, created automatically on first run.

## Demo Login Credentials

For demo purposes only.

| Role | Email | Password |
| --- | --- | --- |
| Admin | admin@blockbuster.com | admin6767 |
| Clerk | clerk@blockbuster.com | Clerk6969 |
| Customer | john@customer.com | customer123 |
| Customer | jane.smith@customer.com | Jane6969 |
| Customer | carlos.rivera@customer.com | Carlos6969 |
| Customer | aisha.bello@customer.com | Aisha6969 |
| Customer | oscar@customer.com | Oscar6969 |

Admin and Clerk always log in with the fixed passwords above. Customer passwords are set
per-account at registration (or via "Reset Customer Password" in the Clerk/Admin dashboard).
