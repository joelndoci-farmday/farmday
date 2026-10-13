-- Farmday 11: fail-closed safety review for ORIGINAL uploaded files only.
-- Apply to Farmday Supabase project, not OnStood. No external YouTube uploads here.
create table if not exists public.farmday_upload_safety (
 upload_id uuid primary key references public.farmday_uploads(id) on delete cascade,
 screening_state text not null default 'hold' check (screening_state in ('hold','needs_evidence','rejected','candidate')),
 rights_evidence text,
 music_rights_evidence text,
 originality_notes text,
 duplicate_check text not null default 'not_checked' check (duplicate_check in ('not_checked','clear','suspected')),
 content_check text not null default 'not_checked' check (content_check in ('not_checked','clear','flagged')),
 youtube_video_id text,
 youtube_processing text not null default 'not_uploaded' check (youtube_processing in ('not_uploaded','processing','succeeded','failed','rejected')),
 youtube_studio_check text not null default 'not_checked' check (youtube_studio_check in ('not_checked','clear','claim','uncertain')),
 monetization_state text not null default 'not_verified' check (monetization_state in ('not_verified','manual_review','candidate','ineligible')),
 last_checked_at timestamptz,
 updated_at timestamptz not null default now(),
 updated_by uuid references auth.users(id),
 constraint farmday_safety_youtube_id_format check (youtube_video_id is null or youtube_video_id ~ '^[A-Za-z0-9_-]{11}$')
);
create table if not exists public.farmday_safety_events (
 id bigint generated always as identity primary key,
 upload_id uuid not null references public.farmday_uploads(id) on delete cascade,
 actor_id uuid references auth.users(id),
 action text not null,
 detail text,
 created_at timestamptz not null default now()
);
create index if not exists farmday_safety_events_upload_idx on public.farmday_safety_events(upload_id,created_at desc);
create or replace function public.farmday_is_admin() returns boolean language sql stable security definer set search_path=public as $$
 select exists(select 1 from public.profiles where id=auth.uid() and is_admin=true);
$$;
revoke all on function public.farmday_is_admin() from public;
grant execute on function public.farmday_is_admin() to authenticated;
alter table public.farmday_upload_safety enable row level security;
alter table public.farmday_safety_events enable row level security;
revoke all on public.farmday_upload_safety from anon;
revoke all on public.farmday_safety_events from anon;
grant select on public.farmday_upload_safety to authenticated;
grant select on public.farmday_safety_events to authenticated;
create policy "admin read safety" on public.farmday_upload_safety for select to authenticated using (public.farmday_is_admin());
create policy "admin read safety events" on public.farmday_safety_events for select to authenticated using (public.farmday_is_admin());
-- Mutations through a server-checked RPC, not arbitrary browser updates.
create or replace function public.farmday_review_upload_safety(
 p_upload_id uuid,p_state text,p_rights text,p_music text,p_originality text,
 p_duplicate text,p_content text,p_studio text,p_note text default null
) returns void language plpgsql security definer set search_path=public as $$
begin
 if not public.farmday_is_admin() then raise exception 'Admin only'; end if;
 if not exists(select 1 from public.farmday_uploads where id=p_upload_id) then raise exception 'Upload not found'; end if;
 if p_state not in ('hold','needs_evidence','rejected','candidate') or
    p_duplicate not in ('not_checked','clear','suspected') or
    p_content not in ('not_checked','clear','flagged') or
    p_studio not in ('not_checked','clear','claim','uncertain') then raise exception 'Invalid review state'; end if;
 if p_state='candidate' and (
    nullif(trim(coalesce(p_rights,'')),'') is null or
    nullif(trim(coalesce(p_music,'')),'') is null or
    nullif(trim(coalesce(p_originality,'')),'') is null or
    p_duplicate <> 'clear' or p_content <> 'clear' or p_studio <> 'clear'
 ) then raise exception 'Fail-closed: all evidence and checks required for candidate status'; end if;
 insert into public.farmday_upload_safety
 (upload_id,screening_state,rights_evidence,music_rights_evidence,originality_notes,duplicate_check,content_check,youtube_studio_check,monetization_state,updated_by,updated_at,last_checked_at)
 values(p_upload_id,p_state,p_rights,p_music,p_originality,p_duplicate,p_content,p_studio,
 case when p_state='candidate' then 'candidate' else 'not_verified' end,auth.uid(),now(),now())
 on conflict(upload_id) do update set screening_state=excluded.screening_state,rights_evidence=excluded.rights_evidence,
 music_rights_evidence=excluded.music_rights_evidence,originality_notes=excluded.originality_notes,
 duplicate_check=excluded.duplicate_check,content_check=excluded.content_check,
 youtube_studio_check=excluded.youtube_studio_check,monetization_state=excluded.monetization_state,
 updated_by=auth.uid(),updated_at=now(),last_checked_at=now();
 insert into public.farmday_safety_events(upload_id,actor_id,action,detail) values(p_upload_id,auth.uid(),'review:'||p_state,left(coalesce(p_note,''),1000));
end;$$;
revoke all on function public.farmday_review_upload_safety(uuid,text,text,text,text,text,text,text,text) from public;
grant execute on function public.farmday_review_upload_safety(uuid,text,text,text,text,text,text,text,text) to authenticated;
-- No auto-publish RPC exists by design. YouTube access tokens MUST remain server-side.
