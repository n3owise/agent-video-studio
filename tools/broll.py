#!/usr/bin/env python3
"""
tools/broll.py - Download and normalize free B-roll stock footage to 1080p 30fps H.264.
Zero audio, exact 1920x1080 resolution, optimized for Remotion playback.
"""

import argparse
import os
import subprocess
import sys
import shutil

def normalize_video(input_path: str, output_path: str, duration: float = 15.0, loop_count: int = 1):
    os.makedirs(os.path.dirname(os.path.abspath(output_path)), exist_ok=True)
    temp_out = output_path + ".tmp.mp4"
    
    # Scale to 1920x1080, 30fps, remove audio, h264
    cmd = [
        "ffmpeg", "-y",
        "-stream_loop", str(loop_count),
        "-i", input_path,
        "-t", str(duration),
        "-vf", "scale=1920:1080:force_original_aspect_ratio=increase,crop=1920:1080,fps=30",
        "-c:v", "libx264", "-pix_fmt", "yuv420p", "-preset", "fast", "-crf", "22",
        "-an",
        temp_out
    ]
    res = subprocess.run(cmd, capture_output=True, text=True)
    if res.returncode != 0:
        print(f"FFmpeg error: {res.stderr}", file=sys.stderr)
        if os.path.exists(temp_out):
            os.remove(temp_out)
        return False
        
    shutil.move(temp_out, output_path)
    print(f"[B-Roll] Normalized clip saved to: {output_path}")
    return True

def fetch_broll(query_or_url: str, output_path: str, duration: float = 15.0):
    os.makedirs(os.path.dirname(os.path.abspath(output_path)), exist_ok=True)
    
    # If it's a local file, just normalize it
    if os.path.exists(query_or_url):
        return normalize_video(query_or_url, output_path, duration, loop_count=2)
        
    # If it's a URL or search query
    target_url = query_or_url
    if not (query_or_url.startswith("http://") or query_or_url.startswith("https://")):
        target_url = f"ytsearch1:{query_or_url} 4k free stock footage no copyright"

    raw_temp = output_path + ".raw.mp4"
    print(f"[B-Roll] Downloading footage for '{query_or_url}'...")
    
    dl_cmd = [
        "yt-dlp",
        "--no-playlist",
        "-f", "bestvideo[height<=1080][ext=mp4]/best[height<=1080]/best",
        "-o", raw_temp,
        target_url
    ]
    res = subprocess.run(dl_cmd, capture_output=True, text=True)
    if res.returncode != 0 or not os.path.exists(raw_temp):
        print(f"Download failed: {res.stderr}", file=sys.stderr)
        return False

    success = normalize_video(raw_temp, output_path, duration, loop_count=2)
    if os.path.exists(raw_temp):
        os.remove(raw_temp)
    return success

def main():
    parser = argparse.ArgumentParser(description="Download and normalize B-roll stock footage.")
    parser.add_argument("--query", "-q", required=True, help="Search term (e.g. 'coffee plantation drone') or video URL or local file")
    parser.add_argument("--out", "-o", required=True, help="Path to output .mp4 file")
    parser.add_argument("--duration", "-d", type=float, default=15.0, help="Clip duration in seconds")
    args = parser.parse_args()

    fetch_broll(args.query, args.out, args.duration)

if __name__ == "__main__":
    main()
