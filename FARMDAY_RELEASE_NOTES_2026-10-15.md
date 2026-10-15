# FarmDay – YouTube Admin workflow (15 October 2026)

## Implemented in this ZIP
- Admin workflow tabs: YouTube Processing → YouTube Checks → Ready for Review → Published; separate Rejected / Needs Evidence, Monetization Review and YouTube Issues.
- Video appears in Ready for Review only when processing is marked `processed` and the manual YouTube Studio check is `clear`.
- `Approve & Publish` for one or several selected videos calls `farmday-youtube-admin-actions` server function; successful publications are removed from Review and shown under Published after refresh.
- Admin Team UI: owner can add/remove other administrators; owner account cannot be modified in UI.
- Discover reads the public YouTube catalog.

## Supabase changes already applied to project kgntwauwilqrixcwwprj
- Edge function `farmday-youtube-admin-actions` ACTIVE v3, JWT verification on. Admin-only publish with YouTube API status update and verification; catalog upsert after confirmed Public. Owner-only list_admins/set_admin.
- `farmday_owner_config` table created, owner UUID configured; row-level security enabled and access revoked from regular roles.
- `farmday_protect_admin_flag` trigger prevents removing owner admin status and blocks client-side changes to is_admin.
- Existing processing sync and public catalog sync left in place.

## Important limitations / remaining verification
- The production YouTube OAuth publishing path has not been exercised on a real video in this session. Test with a disposable upload before relying on it.
- YouTube API does not expose all Studio copyright / monetization signals. Manual Studio check remains required before publication.
- `Delete Selected` does not remove YouTube-hosted videos; those must currently be removed through YouTube Studio. No misleading delete button is enabled for those.
- The frontend build could not be verified here because dependencies were not installed; `npm install` failed in the execution environment. Run `npm install` then `npm run build` locally.
- Uploads can remain in YouTube Processing until the scheduled processing sync updates the database (typically up to 5 minutes).

## Local install
Extract the ZIP over a backed-up FarmDay project directory, then `npm install` and `npm run dev`.
