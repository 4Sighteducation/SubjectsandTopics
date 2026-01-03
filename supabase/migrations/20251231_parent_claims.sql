-- Parent-first purchase claims:
-- A parent purchases on the marketing site, enters the child's email, and the child later claims Pro in-app.
-- This avoids "Hide My Email" issues from Sign in with Apple by making the claim based on a code delivered to the email.

create table if not exists public.parent_claims (
  id uuid primary key default gen_random_uuid(),
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now(),

  -- The email the parent entered (used only to deliver the claim code)
  child_email text not null,
  child_email_lower text not null,

  -- Secret claim code (delivered via email).
  -- We store it in plaintext for simplicity; it is long/high-entropy and one-time use once claimed.
  claim_code text not null unique,

  -- created -> paid -> claimed (or cancelled)
  status text not null default 'created'
    check (status in ('created','paid','claimed','cancelled')),

  -- Stripe identifiers for support/debug
  stripe_subscription_id text null,
  stripe_invoice_id text null,
  stripe_customer_id text null,
  livemode boolean not null default false,

  -- The paid period end (ms since epoch) from the invoice line period.end.
  paid_expires_at_ms bigint null,
  paid_at timestamptz null,

  -- Who claimed it (Supabase auth.users id)
  claimed_by uuid null references auth.users(id) on delete set null,
  claimed_at timestamptz null
);

create index if not exists parent_claims_child_email_lower_idx on public.parent_claims (child_email_lower);
create index if not exists parent_claims_status_idx on public.parent_claims (status);
create index if not exists parent_claims_stripe_subscription_id_idx on public.parent_claims (stripe_subscription_id);

-- Keep updated_at current (reuses shared helper created in 20251220_push_notifications.sql)
drop trigger if exists trg_parent_claims_updated_at on public.parent_claims;
create trigger trg_parent_claims_updated_at
before update on public.parent_claims
for each row execute function public.set_updated_at();

-- RLS: only service-role / edge functions should read or write these rows directly.
-- (The claim flow will be implemented via Edge Functions, not direct client access.)
alter table public.parent_claims enable row level security;

drop policy if exists "parent_claims_no_access" on public.parent_claims;
create policy "parent_claims_no_access"
on public.parent_claims
for all
to public
using (false)
with check (false);


