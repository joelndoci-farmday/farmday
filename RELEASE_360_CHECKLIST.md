# FarmDay – Moderation workflow release (2026-10-15)

## Implemented
- YouTube upload processing completes -> Ready for Review; removed the blocking YouTube Checks tab.
- Review includes an explicit administrator **Confirm Studio Check** action, then **Approve & Publish**. Publication remains Unlisted until YouTube API confirms Public.
- Rejected / Needs Evidence and YouTube Issues: **Delete from YouTube + Notify User**, with reason, details, explicit DELETE confirmation, server authorization, YouTube API deletion, permanent moderation history, and an automatic in-app FarmDay message to the uploader.
- Admin appointment/removal is owner-only and owner admin role is protected at the database level.
- Existing monetization review remains separate from publication.

## Supabase applied
- `farmday-youtube-admin-actions` active v4 (publish, list_admins, set_admin, delete_youtube).
- `farmday_owner_config`, owner role protection trigger, `farmday_moderation_history`.
- Existing upload, processing sync, and public catalog sync remain in place.

## Safety and operational limits
- YouTube API does not expose all Studio copyright/monetization notices. Studio confirmation is manual and cannot certify future absence of claims.
- In-app notification is a private FarmDay message, not carrier SMS.
- If YouTube deletion succeeds but database cleanup or notification fails, the server returns an explicit error; moderation history records the YouTube deletion. Investigate before retrying.
- The React production build was not run: npm offline install lacks cached `ws@8.22.0` package. ZIP integrity and code presence were verified, not browser end-to-end behavior.
- No test video was deleted or published during this release.

## Acceptance tests to run together
1. Upload Unlisted and confirm YouTube processing moves it into Ready for Review.
2. Select video, inspect in YouTube Studio, click Confirm Studio Check, then Approve & Publish.
3. Verify actual Public status on YouTube, Published tab, and Discover as anonymous guest.
4. Upload a separate disposable test video; register a manual YouTube issue; choose a reason, type DELETE; confirm deletion in YouTube and FarmDay and receipt of a FarmDay private message.
5. Confirm non-admin cannot call server actions, admin cannot manage admins, owner cannot lose admin status.
6. Simulate errors (YouTube API failure, network interruption) before declaring production-ready.
