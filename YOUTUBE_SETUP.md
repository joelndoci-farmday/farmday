# Farmday 11 — YouTube Safety Engine: connection roadmap

## What this ZIP actually implements
- New admin panel for ORIGINAL private Supabase video uploads.
- Admin-only SQL review RPC, evidence fields, fail-closed candidate gate, immutable-ish append-only audit records (no client writes).
- Preview of private uploaded files via short-lived signed URLs.
- External discovered YouTube videos are never copied into the Farmday YouTube channel.
- **No Google OAuth, API upload, copyright certification, monetization switch or public auto-publishing is active yet.**

## Install
1. Extract this ZIP and copy existing Farmday `.env` settings (never share secret keys).
2. Apply `supabase/migrations/20261013_farmday_youtube_safety.sql` in the SQL Editor of the Farmday project `kgntwauwilqrixcwwprj` only. Do not apply to OnStood.
3. `npm install` then `npm run build`, then `npm run dev`.
4. Log in with the Farmday admin account and open `/admin`.

## Next connection prerequisites
1. In Google Cloud Console create/select a project for Farmday and enable YouTube Data API v3.
2. Configure OAuth consent screen and OAuth web client. Google needs the authorized redirect URL of a server-side callback (to be implemented, NOT localhost frontend callback). Never put the client secret in Vite variables.
3. Connect the exact YouTube channel by OAuth; validate its `channels.list?mine=true` ID and store encrypted refresh tokens server-side.
4. Implement resumable upload of only original, rights-screened videos, with `privacyStatus=private` **explicitly** set. Default must never be public.
5. Poll `videos.list(part=status,processingDetails)` and record only processing/technical results. Content ID and ad suitability are NOT comprehensively exposed by this API.
6. Require a separate verified rights + YouTube Studio check before public publishing. No public autopublish until operational testing, channel/API audits and policy checks are complete.
7. Independently implement Discovery using YouTube search and embedding (no video reuploads), with quota/rate limits, deduplication and respect for embedding restrictions.
8. Later: Reels/Shorts distribution only for licensed original material and subject to platform API permissions.

## Important
- YouTube API `processingStatus=succeeded` is not proof of copyright clearance or monetization eligibility.
- Candidate is not monetization approval. Avoid claiming guaranteed protection from copyright claims, strikes, or reused-content reviews.
- The previous 50 MB upload limit is unchanged; larger videos need resumable upload infrastructure.

## October 13 update — OAuth connection UI
- Farmday Admin now includes **Connect Farmday YouTube** and connection status, using the deployed `youtube-oauth-start` Edge Function and the admin-only `farmday_youtube_connection_status` SQL RPC.
- The Supabase project currently reports `youtube-oauth-start` and `youtube-oauth-callback` as ACTIVE. Verify OAuth end-to-end manually with the admin account; no successful connection has been confirmed.
- Do not attempt to upload arbitrary user videos through the admin refresh token from the browser. Direct large-file uploads require an authenticated, rate-limited streaming/resumable gateway that never exposes channel tokens or grants an unrestricted channel upload URL to users.
- **The 50 MB existing upload limit remains in force until the gateway is implemented and tested.** This package does not claim YouTube upload works yet.
