#!/usr/bin/env python3
"""
tools/render.py - Render Remotion Explainer composition using JSON props.
"""

import argparse
import json
import os
import subprocess
import sys

def render_video(props_path: str, output_path: str, concurrency: int = 4):
    if not os.path.exists(props_path):
        print(f"Error: Props file not found at {props_path}", file=sys.stderr)
        sys.exit(1)

    os.makedirs(os.path.dirname(os.path.abspath(output_path)), exist_ok=True)
    
    # Path to remotion-composer
    script_dir = os.path.dirname(os.path.abspath(__file__))
    repo_root = os.path.dirname(script_dir)
    composer_dir = os.path.join(repo_root, "remotion-composer")

    if not os.path.exists(composer_dir):
        print(f"Error: remotion-composer directory not found at {composer_dir}", file=sys.stderr)
        sys.exit(1)

    abs_props = os.path.abspath(props_path)
    abs_out = os.path.abspath(output_path)

    cmd = [
        "npx", "remotion", "render",
        "src/index.tsx", "Explainer",
        abs_out,
        "--props", abs_props,
        "--codec", "h264",
        "--concurrency", str(concurrency)
    ]

    print(f"[Render] Starting Remotion render...")
    print(f"[Render] Props: {abs_props}")
    print(f"[Render] Output: {abs_out}")

    res = subprocess.run(cmd, cwd=composer_dir)
    if res.returncode != 0:
        print("[Render] Remotion render failed.", file=sys.stderr)
        sys.exit(res.returncode)

    print(f"\n[Render] ✨ Render Complete! Video saved to: {abs_out}")

def main():
    parser = argparse.ArgumentParser(description="Render Remotion explainer video.")
    parser.add_argument("--props", "-p", required=True, help="Path to remotion_props.json")
    parser.add_argument("--out", "-o", required=True, help="Path to final .mp4 output")
    parser.add_argument("--concurrency", "-c", type=int, default=4, help="Render concurrency (default 4)")
    args = parser.parse_args()

    render_video(args.props, args.out, args.concurrency)

if __name__ == "__main__":
    main()
