# Parent subscriptions handover (Parent pays → Child unlocks Pro)

### Date / scope
- **Date**: 2025-12-31
- **Goal**: Support a “parent pays, child unlocks” annual subscription (£39.99/yr) via **Stripe**, with entitlement management in **RevenueCat**, and backend logic in **Supabase Edge Functions**.
- **Apple compliance**: No in-app links to external payment. Parent purchases happen on the website.

---

## Current status (what’s implemented)

### ✅ Implemented: “Parent-first” flow (marketing website → child claims in app)
This flow is fully wired end-to-end:
- Parent enters child email on the website → Stripe Checkout (subscription)
- Stripe webhook marks claim as paid and emails the child a **claim code + link**
- Child signs into app and redeems claim code → app calls `claim-pro` → **RevenueCat Pro granted** and Stripe subscription metadata is updated for future renewals

### ✅ Also supported (backend): “Direct grant/extend” on renewals
The Stripe webhook supports granting/renewing Pro when a Stripe subscription has `metadata.student_user_id`.
- This is what makes renewals “automatic” once the Stripe subscription is bound to a Supabase user id.

### ⚠️ Not implemented yet (UI/product): “Student initiates invite to parent”
The “Ask a parent to pay” button/flow (student triggers email to parent) is **not fully productised** in this repo right now.
However, the webhook path for “grant/extend for student_user_id” already exists, so implementing the student→parent email + checkout is straightforward (see “Student-initiated flow (recommended next)” below).

---

## Architecture (systems + responsibilities)

### Stripe (payments)
- **Product/Price**: “Parent Revision Pass” annual `price_...`
- **Checkout**: created server-side in Supabase Edge Function `parent-checkout`
- **Webhook**: delivered to Supabase Edge Function `stripe-webhook`
- **Key metadata conventions**:
  - Parent-first: `metadata.parent_claim_id`, `metadata.child_email`
  - Bound-to-student renewals: `metadata.student_user_id`

### Supabase (backend)
- **Database**: `public.parent_claims` stores claim state and Stripe identifiers
- **Edge Functions**:
  - `parent-checkout` (public, JWT OFF): creates Stripe Checkout session + `parent_claims` row
  - `stripe-webhook` (public, JWT OFF): processes `invoice.paid` to either (a) email claim code, or (b) grant/extend Pro
  - `claim-pro` (private, JWT ON): verifies code, grants Pro in RevenueCat, binds Stripe subscription to user id

### RevenueCat (entitlements)
- Source of truth for **in-app “Pro” access**.
- Server-side grants are done via RevenueCat API (v2) from Edge Functions.

### Marketing website (parent-facing)
In this repo there is a Next.js marketing app under `marketing/`:
- `/parents` → child email capture + “continue to secure checkout”
- `/parents/thanks` → post-checkout success page
- `/claim?code=...` → shows claim code + deep link / install options
- `/api/parent-checkout` → proxies to Supabase `parent-checkout` edge function

> Note: If your live website is deployed from a separate repo (e.g. `FLASH_marketing`), these same routes/files must exist there too.

### Mobile app (child-facing)
- Redeem UI: `src/screens/paywall/RedeemCodeScreen.tsx`
- Navigation includes `RedeemCodeScreen` (see `src/navigation/MainNavigator.tsx`)

---

## Data model

### `public.parent_claims`
Migration: `supabase/migrations/20251231_parent_claims.sql`

Fields you’ll care about most:
- `claim_code`: long code delivered by email
- `status`: `created` → `paid` → `claimed` (or `cancelled`)
- `paid_expires_at_ms`: extracted from Stripe invoice line item period end
- `stripe_subscription_id`, `stripe_invoice_id`, `stripe_customer_id`
- `livemode`: whether this claim came from live Stripe mode
- `claimed_by`, `claimed_at`: which Supabase `auth.users.id` redeemed

RLS is **deny-all**: only service role (Edge Functions) should touch rows.

---

## Parent-first flow (implemented)

### 1) Parent enters child email → creates Stripe Checkout
- **UI**: `marketing/app/parents/page.tsx`
- **API route** (marketing): `marketing/app/api/parent-checkout/route.ts`
- **Edge Function**: `supabase/functions/parent-checkout/index.ts`

What `parent-checkout` does:
- Validates `childEmail`
- Inserts a `parent_claims` row with `status='created'` and a random `claim_code`
- Creates Stripe Checkout Session in `mode=subscription`
- Adds **subscription metadata**:
  - `parent_claim_id` = inserted row id
  - `child_email` = normalized child email

### 2) Stripe invoices the subscription → webhook emails claim code
- **Edge Function**: `supabase/functions/stripe-webhook/index.ts`
- **Trigger event**: `invoice.paid`

What `stripe-webhook` does for parent-first:
- Fetches Stripe subscription + metadata
- If it sees `metadata.parent_claim_id`:
  - Updates `parent_claims`:
    - `status='paid'`, stores Stripe IDs, stores `paid_expires_at_ms`, sets `paid_at`
  - Sends the child an email containing:
    - claim code
    - claim link `.../claim?code=...`
    - app deep link fallback

### 3) Child redeems code in app → Pro granted in RevenueCat
- **App UI**: `src/screens/paywall/RedeemCodeScreen.tsx`
- **Edge Function**: `supabase/functions/claim-pro/index.ts` (JWT ON)

What `claim-pro` does:
- Validates caller session (JWT)
- Looks up `parent_claims.claim_code`
- Requires `status='paid'` (or already claimed by same user)
- Grants RevenueCat Pro entitlement until `paid_expires_at_ms`
- Updates Stripe subscription metadata with `metadata.student_user_id = <supabase user id>`
- Marks claim as `claimed`

### 4) Renewal automation
On next `invoice.paid`, `stripe-webhook` can grant/extend Pro based on `metadata.student_user_id`.

---

## Student-initiated flow (recommended next)

Goal: child taps “Ask a parent to unlock” in-app, enters parent email, parent pays, child unlocks automatically.

Recommended implementation (minimal):
- Add a new Edge Function (JWT ON) e.g. `create-parent-checkout-for-student`
  - Input: parent email
  - Creates Stripe Checkout session with subscription metadata:
    - `student_user_id = <current user>`
    - optionally `student_email` / `student_name`
  - Sends the parent an email (SendGrid) with the Stripe Checkout URL
- Webhook path already exists:
  - When `invoice.paid` arrives and `student_user_id` is present, it grants/extends Pro.

This keeps the iOS app Apple-compliant because the app never links to payment; it only sends an email request.

---

## Secrets / env vars (where they live)

### Supabase Edge Functions (Dashboard → Edge Functions → Secrets)
Stripe:
- `STRIPE_SECRET_KEY_TEST`
- `STRIPE_SECRET_KEY`
- `STRIPE_WEBHOOK_SECRET_TEST`
- `STRIPE_WEBHOOK_SECRET`
- `STRIPE_PARENT_PRICE_ID_TEST`
- `STRIPE_PARENT_PRICE_ID`
- `STRIPE_MODE` = `test` or `live`

RevenueCat:
- `REVENUECAT_SECRET_API_KEY` (v2 key, requires Customer info read/write)
- `REVENUECAT_PROJECT_ID`
- `REVENUECAT_PRO_ENTITLEMENT_ID`

SendGrid:
- `SENDGRID_API_KEY`
- `SENDGRID_PARENTS_FROM_EMAIL` (e.g. `tony@fl4shcards.com`)

Optional URLs:
- `PARENTS_SUCCESS_URL` (defaults to `https://www.fl4shcards.com/parents/thanks?session_id=...`)
- `PARENTS_CANCEL_URL` (defaults to `https://www.fl4shcards.com/parents?cancelled=1`)

### Marketing site env (Vercel)
Marketing API route calls Supabase functions and needs:
- `NEXT_PUBLIC_SUPABASE_URL`
- `EXPO_PUBLIC_SUPABASE_ANON_KEY` (used as anon “apikey” header for function calls)

---

## Verify JWT settings (critical)

In Supabase:
- `parent-checkout`: **verify_jwt = false**
- `stripe-webhook`: **verify_jwt = false**
- `claim-pro`: **verify_jwt = true**

Symptoms:
- Stripe webhooks failing with 401 “Missing authorization header” → `stripe-webhook` JWT accidentally ON.

---

## Moving from TEST → LIVE (step-by-step)

### 1) Stripe: create live product/price
- In Stripe **Live mode**, create “Parent Revision Pass” annual price £39.99
- Copy the **live** `price_...`
- Set Supabase secret `STRIPE_PARENT_PRICE_ID` to that live price id

### 2) Stripe: create live webhook endpoint
- Create a **Live** webhook endpoint pointing at:
  - `https://<your-project-ref>.supabase.co/functions/v1/stripe-webhook`
- Subscribe to at least:
  - `invoice.paid`
  - (optional but recommended later: `invoice.payment_failed`, `customer.subscription.deleted`, `customer.subscription.updated`)
- Copy signing secret into Supabase:
  - `STRIPE_WEBHOOK_SECRET`

### 3) Supabase: flip mode to live
- Set `STRIPE_MODE=live` in Supabase secrets
- Confirm `STRIPE_SECRET_KEY` is set (live secret key)

### 4) SendGrid: confirm from address
- Ensure `SENDGRID_PARENTS_FROM_EMAIL` is a verified sender and matches what you want (e.g. `tony@fl4shcards.com`)

### 5) RevenueCat: confirm entitlement id
- Confirm `REVENUECAT_PRO_ENTITLEMENT_ID` matches the entitlement you want unlocked (Pro)
- Confirm the v2 API key has the required permissions (customer info read/write)

### 6) Stripe Tax (VAT)
If you want Stripe to calculate/collect VAT internationally:
- Enable Stripe Tax in Stripe dashboard (registrations/settings)
- Update checkout creation to enable automatic tax if needed.
  - **Note**: current `parent-checkout` sets `billing_address_collection=auto` but does not explicitly set `automatic_tax[enabled]=true`.
  - If tax collection is required, add:
    - `automatic_tax[enabled]=true`
    - and ensure your Stripe Tax settings/registrations are configured.

### 7) Live smoke test
- Make a real live purchase (small controlled test) and then refund/cancel
- Confirm:
  - Webhook fires in Supabase logs
  - `parent_claims.livemode=true`
  - Claim email arrives
  - Child redeems → Pro granted in RevenueCat

---

## Testing checklist (recommended)

### Parent-first test
- Visit `/parents` and create checkout
- Complete checkout
- Confirm `parent_claims` row updated to `paid` with:
  - `stripe_subscription_id` set
  - `paid_expires_at_ms` set
- Confirm child email received
- In app: redeem code → success
- In RevenueCat dashboard: entitlement granted until expected date

### Renewal test (later)
- Use Stripe test clocks or manually create a renewal invoice in test mode
- Confirm `stripe-webhook` sees `student_user_id` and extends Pro

---

## Common failure modes (quick debug)

- **No Supabase edge logs when clicking checkout**:
  - Marketing `/api/parent-checkout` not forwarding `apikey` + `Authorization` headers
- **Stripe webhook 401**:
  - `stripe-webhook` JWT verification accidentally ON
- **Webhook says “missing metadata.student_user_id”**:
  - Subscription not bound to a child yet (expected for parent-first until claim happens)
- **Child doesn’t receive email**:
  - Metadata missing `parent_claim_id` or SendGrid sender misconfigured

---

## PowerShell commands: iOS build + TestFlight submit

### Production/TestFlight (recommended)
From `C:\Users\tonyd\OneDrive - 4Sight Education Ltd\Apps\FLASH`:

```powershell
cd "C:\Users\tonyd\OneDrive - 4Sight Education Ltd\Apps\FLASH"

# (Optional safety) stop EAS trying to sync capabilities in Apple Developer portal
$env:EXPO_NO_CAPABILITY_SYNC="1"

# Install deps (pick one)
npm ci
# or: npm install

# Login (if needed)
npx eas login

# Build an App Store/TestFlight compatible ipa
npx eas build --platform ios --profile production

# Submit the latest build to TestFlight
npx eas submit --platform ios --profile production --latest
```

### Preview build (simulator/internal)
```powershell
cd "C:\Users\tonyd\OneDrive - 4Sight Education Ltd\Apps\FLASH"
$env:EXPO_NO_CAPABILITY_SYNC="1"
npm ci
npx eas build --platform ios --profile preview
```

---

## Notes on versioning
- `app.config.js` controls:
  - `expo.version` (human version)
  - `ios.buildNumber` (must increase every upload to App Store Connect)
  - `android.versionCode` (must increase for Play Store)


