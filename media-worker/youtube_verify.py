"""Bounded audiovisual verification of publicly accessible YouTube candidates.
No authentication, DRM circumvention or inference of copyright ownership.
"""
import os
import shutil
import subprocess
import tempfile
from pathlib import Path

from analyze import visual_hashes, audio_fp, media_metadata


def frame_alignment(source, candidate):
    """Order-preserving, tolerant frame alignment; 5-second dHash samples."""
    if not source or not candidate:
        return 0.0
    def distance(a, b):
        return (int(a, 16) ^ int(b, 16)).bit_count()
    # Allow small time shifts; never match solely on one common static frame.
    best = 0.0
    for shift in range(-3, 4):
        compared = [(x, candidate[i + shift]) for i, x in enumerate(source)
                    if 0 <= i + shift < len(candidate)]
        if len(compared) < min(6, len(source)):
            continue
        rate = sum(distance(a, b) <= 8 for a, b in compared) / len(compared)
        best = max(best, rate)
    return round(best, 3)


def verify(source_path, source_frames, source_duration, candidates, max_candidates=3):
    """Download only short, public candidate media and compare frame sequences.
    A verified match means audiovisual similarity, never proof of ownership.
    """
    results = []
    if not shutil.which("yt-dlp"):
        return [{"status": "unavailable", "reason": "yt_dlp_not_installed"}]
    for item in candidates[:max_candidates]:
        vid = item.get("video_id")
        if not isinstance(vid, str) or len(vid) != 11 or not all(ch.isalnum() or ch in "-_" for ch in vid):
            continue
        with tempfile.TemporaryDirectory() as directory:
            output = str(Path(directory) / "candidate.%(ext)s")
            command = ["yt-dlp", "--no-playlist", "--no-progress", "--no-warnings",
                       "--socket-timeout", "12", "--retries", "1",
                       "--max-filesize", "80M", "--match-filter", "duration <= 900",
                       "-f", "best[height<=480][ext=mp4]/best[height<=480]/best",
                       "-o", output, "https://www.youtube.com/watch?v=" + vid]
            try:
                run = subprocess.run(command, capture_output=True, text=True, timeout=95)
                files = [f for f in Path(directory).iterdir() if f.is_file()]
                if run.returncode or not files:
                    results.append({"video_id": vid, "url": item.get("url"),
                                    "status": "unavailable", "reason": "public_media_not_accessible"})
                    continue
                path = files[0]
                if path.stat().st_size > 80 * 1024 * 1024:
                    results.append({"video_id": vid, "status": "unavailable", "reason": "size_limit"})
                    continue
                duration = media_metadata(path).get("duration_seconds")
                if not duration or not source_duration or abs(duration - source_duration) > max(8, source_duration * .04):
                    results.append({"video_id": vid, "url": item.get("url"),
                                    "status": "not_matched", "reason": "duration_mismatch"})
                    continue
                candidate_frames = visual_hashes(path)
                visual = frame_alignment(source_frames, candidate_frames)
                # Strong ordered visual agreement across at least six distinct samples.
                matched = visual >= .88 and len(source_frames) >= 6
                results.append({"video_id": vid, "url": item.get("url"),
                                "status": "verified_visual_duplicate" if matched else "not_matched",
                                "visual_alignment": visual,
                                "sample_count": len(source_frames),
                                "note": "Visual similarity does not establish copyright ownership."})
            except (OSError, ValueError, subprocess.TimeoutExpired):
                results.append({"video_id": vid, "url": item.get("url"),
                                "status": "unavailable", "reason": "verification_error"})
    return results
