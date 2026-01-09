-- Fix + backfill: ensure waitlist auto-Pro is readable by the app and applied to existing signups.
-- Run in Supabase SQL Editor (service role). Safe to re-run.
--
-- What this does:
-- 1) Ensures `beta_access` RLS is enabled and the "Users can view their own beta access" policy exists.
-- 2) Updates `public.grant_pro_to_user(...)` to also best-effort upsert into `public.user_subscriptions`
--    (for older app builds that read user_subscriptions).
-- 3) Backfills Pro for all eligible waitlist users who already have an auth account.
--
-- IMPORTANT:
-- - This cannot grant Pro to users who have NOT created an account yet (no auth.users row).
-- - Your trigger already grants Pro at signup when installed; this just makes it reliable + backfills.

-- 1) Ensure beta_access is readable by signed-in users (required for app to see Pro)
alter table public.beta_access enable row level security;

do $$
begin
  if not exists (
    select 1
    from pg_policies
    where schemaname = 'public'
      and tablename = 'beta_access'
      and policyname = 'Users can view their own beta access'
  ) then
    create policy "Users can view their own beta access"
      on public.beta_access
      for select
      using (auth.uid() = user_id);
  end if;
end $$;

-- 2) Make grant_pro_to_user write BOTH beta_access (source-of-truth) and best-effort user_subscriptions
create or replace function public.grant_pro_to_user(
  p_user_id uuid,
  p_expires_at timestamptz,
  p_source text,
  p_note text
)
returns void
language plpgsql
security definer
set search_path = public
as $$
begin
  -- Best-effort upsert into public.user_subscriptions.
  -- Never block auth signups (schema can drift across environments).
  begin
    insert into public.user_subscriptions (user_id, tier, source, platform, expires_at, created_at, updated_at)
    values (p_user_id, 'pro', p_source, 'web', p_expires_at, now(), now())
    on conflict (user_id)
    do update set tier = excluded.tier,
                  source = excluded.source,
                  platform = excluded.platform,
                  expires_at = excluded.expires_at,
                  updated_at = now();
  exception when others then
    null;
  end;

  -- Source of truth for free access is public.beta_access (read by the app as an override).
  insert into public.beta_access (user_id, email, tier, expires_at, note, created_at, updated_at)
  values (
    p_user_id,
    (select email from auth.users where id = p_user_id),
    'pro',
    p_expires_at,
    p_note,
    now(),
    now()
  )
  on conflict (user_id)
  do update set email = excluded.email,
                tier = excluded.tier,
                expires_at = excluded.expires_at,
                note = excluded.note,
                updated_at = now();
end;
$$;

revoke all on function public.grant_pro_to_user(uuid, timestamptz, text, text) from public, anon, authenticated;
grant execute on function public.grant_pro_to_user(uuid, timestamptz, text, text) to service_role;

-- 3) Backfill: grant Pro to ALL eligible waitlist users who already created an account.
-- Eligible = (is_top_twenty=true OR auto_pro_enabled=true)
with eligible as (
  select
    u.id as user_id,
    w.id as waitlist_id,
    greatest(coalesce(w.auto_pro_days, 365), 1) as days_to_grant
  from auth.users u
  join public.waitlist w
    on lower(w.email) = lower(u.email)
  where (w.is_top_twenty = true or w.auto_pro_enabled = true)
)
select public.grant_pro_to_user(
  e.user_id,
  now() + make_interval(days => e.days_to_grant),
  'waitlist_backfill',
  'waitlist_backfill'
)
from eligible e;

-- 4) Optional: mark waitlist rows as granted (so admin UI reflects it)
with eligible as (
  select
    u.id as user_id,
    w.id as waitlist_id
  from auth.users u
  join public.waitlist w
    on lower(w.email) = lower(u.email)
  where (w.is_top_twenty = true or w.auto_pro_enabled = true)
)
update public.waitlist w
set auto_pro_granted_at = coalesce(w.auto_pro_granted_at, now()),
    auto_pro_granted_user_id = coalesce(w.auto_pro_granted_user_id, e.user_id)
from eligible e
where w.id = e.waitlist_id;

