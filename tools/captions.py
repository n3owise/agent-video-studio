#!/usr/bin/env python3
"""
tools/captions.py - Extract millisecond word-by-word timestamps using Whisper.
Outputs the exact JSON array expected by Remotion's CaptionOverlay component.
"""

import argparse
import json
import os
import sys

def extract_word_timestamps(audio_path: str, output_path: str, model_size: str = "tiny.en"):
    try:
        from faster_whisper import WhisperModel
    except ImportError:
        print("Error: faster-whisper not installed. Run: pip install faster-whisper", file=sys.stderr)
        sys.exit(1)

    print(f"[Captions] Transcribing {audio_path} using Whisper ({model_size})...")
    model = WhisperModel(model_size, device="cpu", compute_type="int8")
    segments, info = model.transcribe(audio_path, word_timestamps=True)

    words_data = []
    for segment in segments:
        for w in segment.words:
            clean_word = w.word.strip()
            if not clean_word:
                continue
            is_break = any(clean_word.endswith(p) for p in [".", "?", "!", ":", ";"])
            words_data.append({
                "word": clean_word,
                "startMs": int(round(w.start * 1000)),
                "endMs": int(round(w.end * 1000)),
                "pageBreakAfter": is_break
            })

    os.makedirs(os.path.dirname(os.path.abspath(output_path)), exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(words_data, f, indent=2)

    print(f"[Captions] Extracted {len(words_data)} word timestamps -> {output_path}")

def main():
    parser = argparse.ArgumentParser(description="Extract word timestamps for Remotion captions.")
    parser.add_argument("--audio", "-a", required=True, help="Path to input audio file (.mp3 / .wav)")
    parser.add_argument("--out", "-o", required=True, help="Path to output JSON file")
    parser.add_argument("--model", "-m", default="tiny.en", help="Whisper model size (tiny.en, base.en, small.en)")
    args = parser.parse_args()

    extract_word_timestamps(args.audio, args.out, args.model)

if __name__ == "__main__":
    main()
