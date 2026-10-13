# Farmday 4 — consent + moderation foundation

English-language React/Vite/Supabase application, continuing the Farmday 3 modular structure.

## Start

Extract the ZIP. From `farmday-v4`, run `npm install` and `npm run dev`. Configure the Supabase project URL and publishable key in `.env` (see `.env.example`). Do not put YouTube client secrets, OAuth refresh tokens or Supabase service-role keys in frontend code.

## Implemented

- One unchecked `I agree to the Terms & Conditions.` checkbox, `Continue` button immediately below, full scrollable agreement beneath that. The agreement includes a YouTube hosting/streaming explanation in the middle.
- Submission via an authenticated Supabase RPC that atomically saves a YouTube-link video, agreement version/acceptance record and review-queue metadata.
- Separate admin lists: unassigned, monetization intent, non-monetization intent. Moving queues requires confirmation. Admin approval affects Farmday visibility only, not YouTube publishing.
- Existing public videos, profiles, messages and other app pages preserved from Farmday 3.

## YouTube integration: NOT YET ACTIVE

This version accepts an existing YouTube video URL. It does **not** upload video files, perform Content ID checks, monetize videos, or automatically publish on YouTube. Implementing that safely requires server-side video upload processing, Google OAuth authorization for the channel, secure token storage, a background job worker, API quota management, YouTube policy/audit checks and independent verification of copyright and advertising suitability. The YouTube Data API cannot directly toggle per-video ad monetization. An admin queue named `monetization` is not an ad-setting control.

The text is a comprehensive *draft*, not a substitute for review by a qualified legal professional. Privacy and applicable jurisdiction terms need finalized public policies and contact details before production launch.

## Supabase migration

The linked Farmday project `kgntwauwilqrixcwwprj` was updated with `farmday_video_consent_and_review_queues`. It creates `farmday_video_reviews`, its RLS policies, and `farmday_submit_video` RPC. Existing OnStood project is untouched.

## Farmday v5 mobile file upload
- `Upload Video` opens a modal with one agreement checkbox, Continue and the full terms below.
- After acceptance, select a video from phone gallery/files or desktop folders; tap Done — Submit for review.
- Uploaded files go to the **private** `farmday-pending-videos` Supabase Storage bucket and the `farmday_uploads` review table. They are not publicly visible.
- On success, users see a pending-review notice saying review **may take up to 24 hours** (an estimate, not a guaranteed SLA).
- Current size cap: **50 MB**. Large phone videos require resumable TUS uploads, an appropriate storage plan and a server-side background worker before production.
- Admin can preview privately and assign a review queue. YouTube channel upload, copyright scans, publishing and monetization are **not connected**.
- Supabase migration was applied to the Farmday project; the user still needs to run/test the client app.

## Farmday 6 social features
- Profile photo upload (JPEG, PNG, WebP, 5 MB), public avatar display, editable profile, password update.
- Follow requests and accept/unfollow management on profile; public profile Follow and Message links.
- Notification bell for video likes, comments, messages, follow requests and accepted follows; 30-second fallback polling.
- Responsive conversation UI with contacts, online presence indicator and mobile conversation navigation.
- Supabase migration was applied to Farmday project. Realtime Presence only reports members currently connected to the same presence channel; this is not a global reliable online census.
- Google login and automatic YouTube publishing remain unconnected.
- Build could not be completed in this environment because dependency installation timed out; validate locally using `npm install` and `npm run build`.

## Version 7: Messages badge
- Messages navigation shows a red unread count, separate from the bell. Bell excludes message notifications.
- The receiver marks a conversation as read when it is opened. Supabase migration adds messages.read_at and grants only receiver update of read_at.
- About us removed from primary navigation (footer link retained).
- Test with two accounts: send a message, see red badge, open chat, badge clears.

## Farmday 9 — feed-first navigation
- Clicking the Farmday logo opens `/`, a public feed of approved videos (3 cards per row on desktop, 1 on mobile).
- Videos load 12 at a time using Supabase pagination and IntersectionObserver, with a fallback Load more button.
- One Discover navigation item points to `/videos` and searches video title/description plus farmer name/farm/location.
- Removed duplicate Discover/Explore navigation and the landing hero; upload, messaging, notifications and profile remain.
- YouTube video links still open YouTube; this does not change hosting or moderation.

## Farmday 11 safety foundation
See `YOUTUBE_SETUP.md`. Admin safety review and SQL migration included. OAuth and YouTube API connection NOT ACTIVE; no auto-publishing.
