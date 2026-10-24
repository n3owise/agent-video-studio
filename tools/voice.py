#!/usr/bin/env python3
"""
tools/voice.py - Generate natural neural narration using edge-tts.
Zero API keys required. Free, unlimited, expressive studio quality.
"""

import argparse
import os
import subprocess
import sys

DEFAULT_VOICE = "en-US-AndrewMultilingualNeural"

POPULAR_VOICES = {
    "andrew": "en-US-AndrewMultilingualNeural",      # Warm, expressive male narrator
    "brian": "en-US-BrianNeural",                    # Professional documentary male
    "aria": "en-US-AriaNeural",                      # Crisp, engaging female narrator
    "emma": "en-US-EmmaMultilingualNeural",          # Warm, friendly female
    "christopher": "en-US-ChristopherNeural",        # Authoritative storytelling
    "guy": "en-US-GuyNeural",                        # Conversational everyday male
    "jenny": "en-US-JennyNeural"                     # Friendly conversational female
}

def generate_voice(script_path: str, output_path: str, voice: str = DEFAULT_VOICE, vtt_path: str = None, rate: str = "-2%"):
    os.makedirs(os.path.dirname(os.path.abspath(output_path)), exist_ok=True)
    
    # Resolve shortcut voice names
    resolved_voice = POPULAR_VOICES.get(voice.lower(), voice)
    
    cmd = [
        sys.executable, "-m", "edge_tts",
        "--voice", resolved_voice,
        "--rate", rate,
        "-f", script_path,
        "--write-media", output_path
    ]
    if vtt_path:
        os.makedirs(os.path.dirname(os.path.abspath(vtt_path)), exist_ok=True)
        cmd.extend(["--write-subtitles", vtt_path])
        
    print(f"[Voice] Generating neural voiceover with {resolved_voice}...")
    res = subprocess.run(cmd, capture_output=True, text=True)
    if res.returncode != 0:
        print(f"Error generating voice: {res.stderr}", file=sys.stderr)
        sys.exit(1)
        
    print(f"[Voice] Audio saved to: {output_path}")
    if vtt_path:
        print(f"[Voice] Subtitles saved to: {vtt_path}")

def main():
    parser = argparse.ArgumentParser(description="Generate natural neural voiceover.")
    parser.add_argument("--script", "-s", required=True, help="Path to text script file")
    parser.add_argument("--out", "-o", required=True, help="Path to output .mp3 file")
    parser.add_argument("--voice", "-v", default=DEFAULT_VOICE, help="Voice name or shortcut (andrew, brian, aria, emma)")
    parser.add_argument("--vtt", help="Optional path to output .vtt subtitle file")
    parser.add_argument("--rate", default="-2%", help="Speech rate adjustment (e.g. -2%, +0%)")
    args = parser.parse_args()

    generate_voice(args.script, args.out, args.voice, args.vtt, args.rate)

if __name__ == "__main__":
    main()
