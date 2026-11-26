# Payments with Razorpay (INR subscriptions)

Ripple never touches card data: the customer pays on Razorpay's hosted page. Access changes only when Razorpay's
signed webhook confirms payment, so a customer can't upgrade by merely clicking.

## Set up (use Test Mode first)
1. Create a Razorpay account and stay in **Test Mode** until everything works.
2. **Settings → API Keys → Generate**: copy the Key Id and Key Secret → `RAZORPAY_KEY_ID`, `RAZORPAY_KEY_SECRET`.
3. **Subscriptions → Plans → Create Plan** twice (billing period: monthly, interval 1):
   Developer Pro ₹799 and Team ₹4,999. Copy each plan id (`plan_...`) → `RAZORPAY_PLAN_PRO`, `RAZORPAY_PLAN_TEAM`.
   (Subscriptions may need to be enabled on your account; check Razorpay's current requirements.)
4. **Settings → Webhooks → Add**: URL `https://<ripple-api>/api/v1/webhooks/razorpay`, choose a secret → `RAZORPAY_WEBHOOK_SECRET`.
   Tick: `subscription.activated`, `subscription.charged`, `subscription.pending`, `subscription.halted`,
   `subscription.cancelled`, `subscription.completed`, `subscription.resumed`.
5. Restart the API, sign in, open **Billing → Choose Developer Pro**, pay with a Razorpay test card/UPI, and watch the
   plan change to **pro** a few seconds after payment.

## What to verify in Test Mode before going live
- A cancel-at-period-end: confirm which event Razorpay sends and when, so paid time isn't cut short.
- A failed payment: status becomes "past due"; after Razorpay's retries it becomes "halted" and the team drops to Free.
- The Command center shows the payment under **Billed MRR**.

## Going live
Complete Razorpay KYC, switch to live keys/plans/webhook, and publish your Terms and Privacy pages (starter templates in `/terms`, `/privacy`;
have a lawyer review them). GST invoicing and tax handling: confirm with your chartered accountant.
