# Deploy on Render (about 20 minutes)

1. Push this repository to GitHub (private is fine).
2. On render.com sign in with GitHub, then **New + → Blueprint**, pick the repository. Render reads `render.yaml` and
   creates a database, `ripple-api` and `ripple-web`.
3. When asked for variables, fill what you can now: `ADMIN_EMAILS` (your login email). Leave Razorpay/GitHub blank for now.
4. Click **Apply** and wait for both services to show **Live**.
5. Copy the two addresses Render gave you, then set:
   - on **ripple-api → Environment**: `FRONTEND_URL` = the ripple-web address (no trailing slash)
   - on **ripple-web → Environment**: `BACKEND_URL` = the ripple-api address (no trailing slash)
   Saving restarts each service. No rebuild is needed because the website reads `BACKEND_URL` at runtime.
6. Check `https://<ripple-api>/health` → `{"status":"ok"}`. Open the ripple-web address, sign up with the email in `ADMIN_EMAILS`;
   **Command center** appears in the sidebar.
7. Continue with `docs/BILLING.md` (payments) and `docs/GITHUB_APP.md` (real repositories).

## Good to know
- Free web services sleep when idle (first request can take about a minute). Use a paid instance before real customers.
- Free Render Postgres has expiry/size limits that change. Check Render's current pricing page and use a paid database before storing customer data.
- `QUEUE_BACKEND=inline` runs analyses inside the API process: fine to start. Add Redis + a worker (`app/worker.py`) when volume grows.
- Tables are created automatically on start. Add Alembic migrations before changing existing tables in production.
