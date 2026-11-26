# Connect real repositories: create the Ripple GitHub App

1. GitHub → **Settings → Developer settings → GitHub Apps → New GitHub App**.
2. Fill in:
   - **Homepage URL:** your ripple-web address
   - **Setup URL:** `https://<ripple-web>/api/v1/integrations/github/callback`  and tick **Redirect on update**
   - **Webhook URL:** `https://<ripple-api>/api/v1/webhooks/github`, **Webhook secret:** a long random string
   - **Permissions (Repository):** Contents: Read-only · Pull requests: Read and write (for the report comment) · Metadata: Read-only
   - **Subscribe to events:** Pull request
   - **Where can this app be installed:** Any account (or only your account while testing)
3. Create the app, then **Generate a private key** (a `.pem` file downloads).
4. On `ripple-api → Environment` set:
   `GITHUB_APP_SLUG` (the app's URL name), `GITHUB_APP_ID`, `GITHUB_WEBHOOK_SECRET`, and `GITHUB_APP_PRIVATE_KEY`
   (paste the whole key; line breaks may be written as `\n`).
5. In Ripple: **Dashboard → Connect GitHub**, pick repositories, return, then **Import connected repositories → Add**.
6. Open a pull request in that repository. Within about a minute a Ripple comment appears on it and the analysis shows in the dashboard.

Not yet exercised against live GitHub in this build: run steps 5–6 on a throwaway repository first and send me any error.
