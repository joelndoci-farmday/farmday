# Farmday 2030 — UI workflow patch (2026-10-13)

## Included
- Admin Video Management overview with five queues: Processing, Ready for Review, Ready for Monetization, Ready for Rejection, YouTube Issues & Removal Requests.
- Original-upload uploader usernames and profile links in admin review.
- Admin manual logging of YouTube removal/copyright/restriction notices. The matching `farmday_youtube_issues` table and admin-only RLS policies were deployed to the Farmday Supabase project. SQL migration is also included in `supabase/migrations/20261013_farmday_youtube_issues.sql` for reproducibility.
- Messenger: online user roster while chat is open, persistent minimized chat state, auto-focus message input on conversation selection, auto-scroll to latest messages.
- Existing review and upload features preserved; no public YouTube publishing has been added.

## Important limitations
- The queue overview is a *read-only categorization*. The checkboxes select items but do not publish or monetize. Existing admin approval functionality remains separate. Bulk actions require a server-side audited RPC and are intentionally not enabled.
- YouTube OAuth is connected on the server, but **resumable direct-to-YouTube upload, private-to-public publication and automatic Studio monetization controls are NOT implemented** in this ZIP. The existing 50 MB Supabase Storage upload still applies.
- YouTube copyright/Content ID notifications are not comprehensively exposed by YouTube Data API. Issues can be recorded manually.
- Online presence is based on a live Realtime presence channel when Messenger is open. For fully global online presence even with chat closed, move presence tracking to an app-wide provider in a future update.
- JavaScript/JSX files passed TypeScript JSX parser syntax checks. Full Vite build could not be executed in this environment because the uploaded ZIP contains Windows node_modules and Linux Rollup native dependency is missing. Run `npm install` then `npm run build` on Windows.

## Windows installation
1. Back up your existing Farmday folder and `.env` file.
2. Unzip into your Farmday project (preserve your own `.env`).
3. In CMD run `npm install`, `npm run build`, then `npm run dev`.
4. Verify Admin / Video Management and Messenger. Do not paste secrets into frontend code.

## Admin decisions update
- Video Management now offers Return to Review, Mark for Rejection, Approve Monetization Candidate, and Delete Selected for selected original uploads.
- Each decision requires confirmation; candidate approval uses the existing server-side fail-closed safety RPC and will fail without documented rights and checks.
- Deletion requires typing DELETE and calls the admin-only `farmday-admin-delete-upload` Edge Function, which removes the private Storage object before removing the database upload record. It does not delete any YouTube video.
- None of these actions publishes to YouTube or activates ads.
