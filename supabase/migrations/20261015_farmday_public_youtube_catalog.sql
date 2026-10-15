-- Public catalog only contains YouTube videos confirmed public by an admin-only server-side check.
create table if not exists public.farmday_public_youtube_catalog (
 upload_id uuid primary key references public.farmday_uploads(id) on delete cascade,
 youtube_video_id text not null unique,
 title text not null,
 description text not null default '',
 thumbnail_url text,
 published_at timestamptz,
 checked_at timestamptz not null default now(),
 constraint youtube_id_format check(youtube_video_id ~ '^[A-Za-z0-9_-]{11}$')
);
alter table public.farmday_public_youtube_catalog enable row level security;
create policy "Anyone can read verified public YouTube videos" on public.farmday_public_youtube_catalog for select to anon, authenticated using (true);
-- No browser write policies. Only service-role Edge Function can insert/update/delete.
grant select on public.farmday_public_youtube_catalog to anon, authenticated;
