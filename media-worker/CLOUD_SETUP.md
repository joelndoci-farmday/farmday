# FarmDay cloud media engine — setup and limitations

This workflow runs FFmpeg + Chromaprint on GitHub Actions every 30 minutes, or manually using workflow_dispatch. It reads the **private original video** in Supabase Storage bucket `farmday-admin-review`, never a YouTube title or a YouTube stream.

## Required GitHub Actions repository secrets

Under Settings → Secrets and variables → Actions, add:

- `FARMDAY_SUPABASE_URL`: `https://kgntwauwilqrixcwwprj.supabase.co`
- `FARMDAY_SUPABASE_SERVICE_ROLE_KEY`: Supabase **service_role** key from the FarmDay project (never commit or share this key in chat).

The worker runs only after the workflow is merged into `main` and these secrets are configured. **Do not run it on untrusted pull requests.** Repo is public; workflows must not print secrets or store downloaded videos as artifacts.

## Video availability prerequisite

The existing `farmday-youtube-upload` Edge Function streams videos straight to YouTube and records a virtual `youtube-private/<id>` storage path. It does **not** preserve the original. The separate `savePrivateReviewCopy()` frontend helper saves the original to private bucket `farmday-admin-review` and inserts `farmday_review_previews` keyed by the YouTube upload session. That helper must be called during a real upload to make the original available. **Existing YouTube-only uploads cannot be retroactively analyzed without the original file being supplied again.**

Supabase Storage quotas and bandwidth apply. Uploading 1 GiB per video is not guaranteed to fit free-tier capacity; enforce a practical limit before enabling all users, and implement deletion/retention before scaling. Do not delete originals automatically until retention and review requirements are settled.

## What the engine does

- Downloads the original with a short-lived signed URL, keeps it on the runner temporary filesystem.
- Calculates full SHA-256 and frame difference hashes every five seconds (up to 360 frames).
- Calculates an audio Chromaprint fingerprint when available.
- Compares exact files and possible visual matches **within previously analyzed FarmDay uploads**.
- Writes findings and technical statuses to `farmday_media_analysis`; leaves copyright and monetization unverified and decision on hold.

It **cannot** query YouTube Content ID globally, prove ownership/licensing, or determine YouTube Partner Program monetization eligibility. Human rights evidence and YouTube Studio review remain necessary.

## Test

Upload a small test MP4 after the private original copy integration is enabled. Confirm a matching row in `farmday_review_previews`, then run Actions → FarmDay private media analysis → Run workflow. Check `farmday_media_analysis` for `provider=github-actions-ffmpeg-v1`. Repeat with the same original to test exact-file duplicate detection.

Do not merge before reviewing the frontend private-copy integration and ensuring storage capacity. The workflow is isolated from the existing YouTube upload and publishing functions.
