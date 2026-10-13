# Farmday private YouTube upload gateway (pilot)

- Edge Function: `farmday-youtube-upload`, version 1, deployed to Farmday Supabase.
- Upload begins with an authenticated POST, then transfers 2 MiB chunks via PUT to Supabase Edge Functions. The server holds the Google refresh token and YouTube resumable session URI. No OAuth credentials are exposed to browsers.
- Uploads are PRIVATE on YouTube. The local `farmday_uploads` row is inserted only after YouTube confirms the upload; `storage_path` starts `youtube-private/` to distinguish it from legacy Supabase Storage objects.
- Initial file cap: 1 GiB. This is an application cap, not a YouTube account limit. Edge Function request limits, execution limits, YouTube API quota and YouTube verification may restrict uploads.
- Admin public-publishing and YouTube removal workflows are NOT yet implemented. `Approve Monetization Candidate` is not YouTube ad activation.
- Private YouTube uploads should be checked in YouTube Studio for copyright and policy notices. YouTube Data API does not expose every such signal.
- IMPORTANT: Existing `Delete Selected` endpoint only handles Supabase Storage objects; do not use it on `youtube-private/` uploads until YouTube deletion workflow is implemented.
- Upload retries recover offsets for a running session. A browser restart currently requires a new upload.
- Verify API quota and CORS, Google token refresh and browser transfer with a small original test video before production.
