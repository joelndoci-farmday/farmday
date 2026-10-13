-- Manual YouTube issue tracking. Do not treat this as automatic copyright detection.
create table if not exists public.farmday_youtube_issues (
 id uuid primary key default gen_random_uuid(),
 upload_id uuid references public.farmday_uploads(id) on delete set null,
 youtube_video_id text,
 issue_type text not null check (issue_type in ('removal_request','copyright_claim','copyright_strike','community_guidelines','youtube_restriction','other')),
 status text not null default 'open' check (status in ('open','investigating','resolved','removed')),
 details text not null default '',
 source text not null default 'manual' check (source in ('manual','youtube_api','youtube_studio','email')),
 created_by uuid references auth.users(id),
 created_at timestamptz not null default now(),
 updated_at timestamptz not null default now()
);
create index if not exists farmday_youtube_issues_status_idx on public.farmday_youtube_issues(status,created_at desc);
alter table public.farmday_youtube_issues enable row level security;
revoke all on public.farmday_youtube_issues from anon;
grant select,insert,update on public.farmday_youtube_issues to authenticated;
drop policy if exists farmday_youtube_issues_admin_select on public.farmday_youtube_issues;
create policy farmday_youtube_issues_admin_select on public.farmday_youtube_issues for select to authenticated using (public.farmday_is_admin());
drop policy if exists farmday_youtube_issues_admin_insert on public.farmday_youtube_issues;
create policy farmday_youtube_issues_admin_insert on public.farmday_youtube_issues for insert to authenticated with check (public.farmday_is_admin() and created_by=auth.uid());
drop policy if exists farmday_youtube_issues_admin_update on public.farmday_youtube_issues;
create policy farmday_youtube_issues_admin_update on public.farmday_youtube_issues for update to authenticated using (public.farmday_is_admin()) with check (public.farmday_is_admin());
