# FarmDay: YouTube -> Discover (15 October 2026)

## What changed
- `src/components/VideoGrid.jsx`: displays verified public YouTube videos in Home/Discover, including for logged-out visitors. A click opens the YouTube watch page. Title, description and thumbnail are shown in a card.
- `src/components/VideoWorkflow.jsx`: Admin button to manually check/sync YouTube privacy status, and uses verified-public status for its preview player.
- `supabase/migrations/20261015_farmday_public_youtube_catalog.sql`: public read-only catalog. Writes are server-only.

## Supabase already applied to FarmDay project kgntwauwilqrixcwwprj
- Created `public.farmday_public_youtube_catalog` with anonymous read-only RLS.
- Deployed admin-only `farmday-youtube-public-catalog-sync` Edge Function.
- Updated existing `farmday-youtube-processing-sync` Edge Function (v4) to refresh the public catalog automatically on its existing 5-minute cron schedule. Only confirmed public YouTube videos are shown. Private/unlisted videos are not added.
- Did NOT make any YouTube videos public. Existing `Testi` remains private; no public videos currently appear.

## To run
1. Extract ZIP, configure the existing `.env` (keep your existing credentials).
2. `npm ci` and `npm run dev`.
3. Log into Admin; click `Sync public YouTube videos to Discover` to refresh immediately, or wait up to ~5 minutes for the automatic sync.
4. Open Discover in an incognito browser window (without logging in). Public videos appear as cards and link directly to YouTube.
5. Private video Testi remains hidden until explicitly made public in YouTube Studio.

## Important limits
- YouTube private videos cannot be played through the public YouTube iframe. For Admin private playback, use a saved private review copy.
- The new sync does NOT change YouTube privacy settings, enable monetization, or approve uploads.
- Video thumbnails may take time to propagate on YouTube.
- npm install/build could not complete in the authoring environment due to unavailable npm packages; JSX syntax was checked using the TypeScript parser. Run the build locally.
