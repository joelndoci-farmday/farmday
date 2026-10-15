# FarmDay media analysis — implementation status

Implemented in this package:
- Original-file SHA-256 computed in browser before upload (only files <=150 MiB to avoid browser memory exhaustion).
- Four sampled visual difference hashes from the original file when the browser can decode it.
- Authenticated owner-only RPC storing preliminary client signals; checks exact SHA-256 matches against FarmDay's existing fingerprints.
- Admin-only RPC exposing analysis results and explicit `unverified` labels in Admin.
- Standalone FFmpeg/Chromaprint analysis prototype in media-worker/analyze.py (not deployed).
- Existing technical YouTube and title-based search engines remain unchanged.

Not implemented or not guaranteed:
- Server-side trusted video/audio analysis pipeline, automatic ingestion/storage of original files, or online FFmpeg worker.
- Global YouTube audiovisual comparisons or Content ID access.
- Proof of ownership, music licenses, copyright clearance, monetization eligibility or YPP approval.
- For videos >150 MiB no client fingerprint is calculated. This is a safety limit, not a claim of verification.
- Browser-origin signals are user-supplied and cannot establish authenticity. Hash match scope is only FarmDay uploads that supplied hashes.

Supabase migrations already applied to project kgntwauwilqrixcwwprj:
- farmday_browser_fingerprint_capture (farmday_submit_client_fingerprints)
- farmday_admin_media_reports_rpc (farmday_admin_media_reports)

To run: extract ZIP to a clean folder, use npm ci on Windows and npm run dev. Keep your .env separately; it is intentionally not included. The frontend has not passed a full Vite build in this environment because the ZIP's Windows node_modules lacks Linux Rollup native dependencies. Preserve a backup of your existing folder before replacing it.
