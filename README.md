# 🏢 Building Bill Manager — Web App

A web application for managing monthly utility bills across two buildings (House 220 & 226).

## Quick Start

### 1. Install wkhtmltopdf (for PDF generation)

| OS | Command |
|---|---|
| **Linux / WSL** | `bash install_wkhtmltopdf_linux.sh` |
| **macOS** | `bash install_wkhtmltopdf_mac.sh` |
| **Windows** | Run `install_wkhtmltopdf_windows.bat` |

### 2. Configure the app

```bash
cp .env.example .env
# Edit .env to change your password, electricity rate, etc.
```

Key settings in `.env`:

| Setting | Default | Description |
|---|---|---|
| `APP_PASSWORD` | `billingapp2025` | Password to log in |
| `DATABASE_URL` | `sqlite:///./bills.db` | Change to `postgresql://...` for Postgres |
| `ELECTRICITY_RATE` | `9.0` | BDT per unit (base rate) |
| `ELECTRICITY_RATE_HIGH` | `10.0` | BDT per unit above threshold |
| `ELECTRICITY_RATE_THRESHOLD` | `0` | Units threshold for high rate (0 = flat) |

### 3. Install dependencies

```bash
# Python backend
pip install -r backend/requirements.txt

# Node.js frontend
cd frontend && npm install && cd ..
```

### 4. Run the app

Open **two terminals**:

```bash
# Terminal 1 — Backend API (port 8000)
uvicorn backend.main:app --reload --port 8000

# Terminal 2 — Frontend (port 5173)
cd frontend && npm run dev
```

Open **http://localhost:5173** in your browser.  
Family members on the same WiFi can use **http://YOUR_IP:5173**.

---

## How It Works

### Monthly workflow
1. Click **New Month** on the Dashboard
2. Previous month's `present units` are **automatically carried forward** as this month's `previous units`
3. Update the **Present Units ✏️** column for each room
4. Totals update **instantly** as you type
5. Click **Save Changes**, then **Generate PDF**

### Electricity rate rules
- **Flat rate:** Set `rate_threshold_units = 0` (default)
- **Tiered billing:** Set threshold > 0. Units up to threshold use the base rate; units above use the high rate.
- You can change rates per-month in the Rate Settings bar on the editor page.

### Database migration (SQLite → PostgreSQL)
Just change one line in `.env`:
```
DATABASE_URL=postgresql://user:password@localhost:5432/billing
```
Then run:
```bash
# Export SQLite data
sqlite3 bills.db .dump > backup.sql
# Import to Postgres (or use pgloader)
```

---

## Project Structure

```
CSVtoPDF/
├── backend/
│   ├── main.py          # FastAPI app + all routes
│   ├── models.py        # SQLAlchemy ORM models
│   ├── database.py      # DB connection (swap engine here)
│   ├── config.py        # Building/room config + password
│   ├── pdf_gen.py       # Cross-platform PDF generation
│   └── requirements.txt
├── frontend/
│   └── src/
│       ├── App.jsx             # Auth + routing
│       ├── api.js              # All backend calls
│       ├── pages/
│       │   ├── LoginPage.jsx
│       │   ├── Dashboard.jsx
│       │   └── MonthEditor.jsx # Main data-entry page
│       └── index.css
├── template.html        # Bill HTML template (Jinja2)
├── .env.example         # Config template
└── install_wkhtmltopdf_*.sh / .bat
```
