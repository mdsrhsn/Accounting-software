# BizHisaab

Pakistani e-commerce business accounting — courier COD, purchases, expenses, ad spend, P&L, and cash flow in one Flask app.

**GitHub:** https://github.com/mdsrhsn/Accounting-software

## Features

- Dashboard with period filters and net worth
- Purchases, partial payments, vendor ledger
- Expenses and category summaries
- Courier settlements (DigiDokaan, Daewoo, PostEx tracking)
- Returns (Shopify integration)
- Ad spend (Facebook/TikTok, USD/PKR + tax)
- Cash & Bank, loans, investment
- P&L and cash flow reports
- CSV import/export
- Admin vs employee roles

## Deploy (Railway + PostgreSQL)

BizHisaab uses **Railway PostgreSQL** only — `DATABASE_URL` is read from Railway env vars. Supabase is not required.

1. Connect this repo on Railway and set **Start Command**:
   ```txt
   gunicorn app:app --bind 0.0.0.0:$PORT --workers 1 --timeout 120
   ```
2. In Railway project: **Add Plugin → PostgreSQL**. Railway auto-creates `DATABASE_URL` on the web service (reference the Postgres service variable if needed).
3. Set `SECRET_KEY` to a long random string in Railway **Variables**.
4. Optionally set courier/Shopify vars from `.env.example`.

On first boot, tables are created automatically in your Railway Postgres database. Existing data is never dropped — migrations only **add** missing columns.

## Local run

```bash
pip install -r requirements.txt
export DATABASE_URL=postgresql://...
export SECRET_KEY=dev-secret
python3 app.py
```

## Data safety

- All schema changes use `CREATE TABLE IF NOT EXISTS` and `ADD COLUMN IF NOT EXISTS`.
- No automatic deletes, truncates, or data rewrites on startup.
- Export full backup anytime from **Export All** in admin.

## Default admin

If no `admin` user exists, one is created on first run. Change the password immediately from **Change Password** in the sidebar.
