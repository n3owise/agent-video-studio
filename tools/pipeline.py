#!/usr/bin/env python3
"""
tools/pipeline.py - Full End-to-End Automated Video Production Pipeline.
Converts any topic into a Full HD motion graphics explainer video with:
1. LLM script & scene generation (OpenRouter / Fallback)
2. Microsoft Edge Neural Voice (edge-tts)
3. Whisper millisecond word timestamps (faster-whisper)
4. 1080p B-Roll footage normalization (yt-dlp + ffmpeg)
5. Remotion 1080p rendering
"""

import argparse
import concurrent.futures
import glob
import json
import os
import re
import shutil
import subprocess
import sys
import threading
import time
import urllib.request

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TOOLS_DIR = os.path.join(REPO_ROOT, "tools")
PROJECTS_DIR = os.path.join(REPO_ROOT, "projects")
RENDERS_DIR = os.path.join(REPO_ROOT, "renders")

# Resolve python executable with dependencies
PYTHON_EXEC = sys.executable
local_venv = os.path.join(REPO_ROOT, ".venv", "bin", "python3")
candidate_venv = os.path.join(os.path.dirname(REPO_ROOT), "OpenMontage", ".venv", "bin", "python3")
if os.path.exists(local_venv):
    PYTHON_EXEC = local_venv
elif os.path.exists(candidate_venv):
    PYTHON_EXEC = candidate_venv

def slugify(text: str) -> str:
    slug = re.sub(r'[^a-zA-Z0-9]+', '-', text.strip().lower())
    return slug[:40].strip('-') or "explainer"

def call_llm(prompt: str, system_prompt: str = "") -> str:
    api_key = os.environ.get("OPENROUTER_API_KEY")
    if not api_key:
        return ""
        
    url = "https://openrouter.ai/api/v1/chat/completions"
    messages = []
    if system_prompt:
        messages.append({"role": "system", "content": system_prompt})
    messages.append({"role": "user", "content": prompt})

    req = urllib.request.Request(
        url,
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
            "HTTP-Referer": "https://github.com/n3owise/agent-video-studio",
            "X-Title": "Agent Video Studio"
        },
        data=json.dumps({
            "model": "meta-llama/llama-3.3-70b-instruct",
            "messages": messages,
            "temperature": 0.7
        }).encode("utf-8")
    )
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            return data["choices"][0]["message"]["content"]
    except Exception as e:
        print(f"[Pipeline] LLM call error: {e}", file=sys.stderr)
        return ""

def generate_script_and_scenes(topic: str, duration: int = 60):
    system_prompt = (
        "You are an elite YouTube documentarian & video director. "
        "Write a 60-second word-for-word spoken voiceover script (~135 words) that will be read aloud by the narrator. "
        "Do NOT include stage directions like 'Scene 1:'; only the actual spoken words. "
        "Also plan exactly 6 scenes for Remotion motion graphics explainer. "
        "Output ONLY a raw JSON object with keys: "
        "'script': (string of the full 135-word voiceover), "
        "'scenes': (array of 6 objects with keys:\n"
        "  1. {'id': 'cut-1', 'type': 'hero_title', 'title': '...', 'subtitle': '...', 'broll_search': '...'}\n"
        "  2. {'id': 'cut-2', 'type': 'stat_card', 'stat': '...', 'subtitle': '...', 'broll_search': '...'}\n"
        "  3. {'id': 'cut-3', 'type': 'bar_chart', 'title': '...', 'chartData': [{'label': '...', 'value': 20}, {'label': '...', 'value': 65}, {'label': '...', 'value': 95}], 'broll_search': '...'}\n"
        "  4. {'id': 'cut-4', 'type': 'stat_card', 'stat': '...', 'subtitle': '...', 'broll_search': '...'}\n"
        "  5. {'id': 'cut-5', 'type': 'bar_chart', 'title': '...', 'chartData': [{'label': '...', 'value': 15}, {'label': '...', 'value': 50}, {'label': '...', 'value': 88}], 'broll_search': '...'}\n"
        "  6. {'id': 'cut-6', 'type': 'text_card', 'title': '...', 'broll_search': '...'}\n"
        "Each 'broll_search' MUST be an exact search phrase for 4K free stock video footage depicting the specific scene concept.)"
    )
    user_prompt = f"Topic: {topic}\nTarget duration: {duration} seconds."
    
    raw = call_llm(user_prompt, system_prompt)
    if raw:
        try:
            clean = raw.strip()
            if clean.startswith("```"):
                clean = re.sub(r"^```[a-zA-Z]*\n", "", clean)
                clean = re.sub(r"\n```$", "", clean)
            parsed = json.loads(clean.strip())
            if "script" in parsed and "scenes" in parsed and len(parsed["script"].split()) > 40:
                return parsed["script"], parsed["scenes"]
        except Exception as e:
            print(f"[Pipeline] JSON parse fallback: {e}")

    # Solid Fallback if no LLM key or parse issue
    fallback_script = (
        f"Why is {topic} fundamentally transforming the modern world? "
        "Behind the headlines lies an intricate web of technology and critical thresholds. "
        "A single failure or vulnerability can destabilize entire systems in minutes. "
        "Engineers and researchers are now racing against time to maintain equilibrium. "
        "From raw computational intelligence to real-time precision monitoring, the stakes have never been higher. "
        f"Next time you consider {topic}, remember: it survives on humanity's sharpest technological tightrope."
    )
    fallback_scenes = [
        {"id": "cut-1", "type": "hero_title", "title": topic, "subtitle": "The High-Stakes Frontier", "broll_search": f"{topic} technology cinematic 4k"},
        {"id": "cut-2", "type": "stat_card", "stat": "99.9% Precision", "subtitle": "Critical Autonomous Threshold", "broll_search": f"{topic} supercomputer radar"},
        {"id": "cut-3", "type": "bar_chart", "title": "System Reaction Latency (ms)", "chartData": [{"label": "Baseline", "value": 25}, {"label": "Target", "value": 75}, {"label": "Peak", "value": 98}], "broll_search": f"{topic} server datacenter technology"},
        {"id": "cut-4", "type": "stat_card", "stat": "Global Reach", "subtitle": "Strategic Planetary Equilibrium", "broll_search": "planet earth space global satellite"},
        {"id": "cut-5", "type": "bar_chart", "title": "Computational Scale Growth", "chartData": [{"label": "Phase 1", "value": 20}, {"label": "Phase 2", "value": 55}, {"label": "Phase 3", "value": 90}], "broll_search": f"{topic} futuristic command center"},
        {"id": "cut-6", "type": "text_card", "title": f"The future of {topic} is unfolding now.", "broll_search": f"{topic} modern science laboratory"}
    ]
    return fallback_script, fallback_scenes

def run_pipeline(spec: dict, status_callback=None):
    def update(pct: int, msg: str):
        print(f"[{pct}%] {msg}")
        if status_callback:
            status_callback(pct, msg)

    topic = spec.get("topic", "Why Coffee Only Grows in the Bean Belt")
    voice = spec.get("voice", "en-US-AndrewMultilingualNeural")
    theme = spec.get("theme", "flat-motion-graphics")
    caption_style = spec.get("captionStyle", "kinetic-gold")
    duration = spec.get("duration", 60)
    aspect_ratio = spec.get("format", "16:9")
    
    slug = slugify(topic)
    project_dir = os.path.join(PROJECTS_DIR, slug)
    os.makedirs(project_dir, exist_ok=True)
    os.makedirs(RENDERS_DIR, exist_ok=True)

    public_project_dir = os.path.join(REPO_ROOT, "remotion-composer", "public", "projects", slug)
    os.makedirs(public_project_dir, exist_ok=True)
    video_assets_dir = os.path.join(public_project_dir, "assets", "video")
    os.makedirs(video_assets_dir, exist_ok=True)

    # 1. Script & Scenes
    custom_script = spec.get("custom_script")
    custom_scenes = spec.get("custom_scenes")

    if custom_script and custom_scenes:
        update(15, f"Using director-approved custom script & scene plan for '{topic}'...")
        script_text = custom_script
        scenes = custom_scenes
    elif custom_script:
        update(15, f"Using director-approved custom script for '{topic}'...")
        script_text = custom_script
        _, scenes = generate_script_and_scenes(topic, duration)
    elif custom_scenes:
        update(15, f"Using director-approved custom scene plan for '{topic}'...")
        scenes = custom_scenes
        script_text, _ = generate_script_and_scenes(topic, duration)
    else:
        update(15, f"Generating narrative script & scene plan for '{topic}'...")
        script_text, scenes = generate_script_and_scenes(topic, duration)

    script_path = os.path.join(project_dir, "script.txt")
    with open(script_path, "w", encoding="utf-8") as f:
        f.write(script_text)

    # 2. Neural Voiceover (edge-tts)
    update(35, f"Synthesizing natural voiceover ({voice.split('-')[2] if '-' in voice else voice})...")
    audio_out = os.path.join(public_project_dir, "narration.mp3")
    vtt_out = os.path.join(project_dir, "subtitles.vtt")
    voice_py = os.path.join(TOOLS_DIR, "voice.py")
    subprocess.run([PYTHON_EXEC, voice_py, "--script", script_path, "--out", audio_out, "--voice", voice, "--vtt", vtt_out], check=True)

    # 3. Whisper Millisecond Timestamps
    update(55, "Aligning word-level captions with Whisper (millisecond accuracy)...")
    captions_out = os.path.join(project_dir, "captions.json")
    captions_py = os.path.join(TOOLS_DIR, "captions.py")
    subprocess.run([PYTHON_EXEC, captions_py, "--audio", audio_out, "--out", captions_out], check=True)

    with open(captions_out, "r", encoding="utf-8") as f:
        captions_data = json.load(f)

    # 4. Stock Video B-Roll
    update(64, f"Curating and fetching topic-accurate 1080p B-roll footage for '{topic}'...")
    from tools import broll
    sample_videos = sorted(glob.glob(os.path.join(REPO_ROOT, "remotion-composer", "public", "projects", "coffee-belt-explainer", "assets", "video", "*.mp4")))
    sample_sizes = set(os.path.getsize(sv) for sv in sample_videos if os.path.exists(sv))
    is_coffee_topic = any(k in topic.lower() for k in ["coffee", "bean belt", "roast"])

    scenes_to_process = scenes[:6]
    total_clips = len(scenes_to_process)
    completed_lock = threading.Lock()
    completed_count = 0

    def download_worker(item):
        nonlocal completed_count
        i, sc = item
        clip_name = f"scene_{i+1:02d}.mp4"
        dest_clip = os.path.join(video_assets_dir, clip_name)

        # Purge stale placeholder coffee clips if this is a new or non-coffee topic
        if os.path.exists(dest_clip) and not is_coffee_topic:
            try:
                if os.path.getsize(dest_clip) in sample_sizes:
                    print(f"[Pipeline] Replacing placeholder coffee clip: {clip_name}")
                    os.remove(dest_clip)
            except Exception:
                pass

        search_query = sc.get("broll_search") or f"{topic} {sc.get('title', '')}".strip()

        if not os.path.exists(dest_clip):
            fetch_ok = False
            try:
                fetch_ok = broll.fetch_broll(search_query, dest_clip, duration=15.0, aspect_ratio=aspect_ratio)
            except Exception as e:
                print(f"[Pipeline] B-roll fetch error: {e}")

            # If download fails, try a broader query based directly on the topic
            if not fetch_ok or not os.path.exists(dest_clip) or os.path.getsize(dest_clip) == 0:
                broad_query = f"{topic} technology footage"
                print(f"[Pipeline] Retrying B-roll with broad query: '{broad_query}'")
                try:
                    fetch_ok = broll.fetch_broll(broad_query, dest_clip, duration=15.0, aspect_ratio=aspect_ratio)
                except Exception as e:
                    print(f"[Pipeline] Broad B-roll retry error: {e}")

            # Only fallback to sample clips if network completely failed
            if not os.path.exists(dest_clip) and sample_videos:
                sample_src = sample_videos[i % len(sample_videos)]
                print(f"[Pipeline] Network fallback to sample video for {clip_name}")
                try:
                    broll.normalize_video(sample_src, dest_clip, duration=15.0, aspect_ratio=aspect_ratio)
                except Exception:
                    shutil.copyfile(sample_src, dest_clip)

        with completed_lock:
            completed_count += 1
            pct = 64 + int((completed_count / total_clips) * 14) if total_clips > 0 else 78
            update(pct, f"Parallel B-roll [{completed_count}/{total_clips}] fetched: '{search_query[:28]}'...")

    if total_clips > 0:
        with concurrent.futures.ThreadPoolExecutor(max_workers=4) as executor:
            list(executor.map(download_worker, enumerate(scenes_to_process)))

    broll_paths = [f"projects/{slug}/assets/video/scene_{i+1:02d}.mp4" for i in range(total_clips)]
    if not broll_paths:
        broll_paths = [""]

    # Copy background music if available
    sample_bgm = os.path.join(REPO_ROOT, "remotion-composer", "public", "projects", "coffee-belt-explainer", "bgm.mp3")
    dest_bgm = os.path.join(public_project_dir, "bgm.mp3")
    if os.path.exists(sample_bgm) and not os.path.exists(dest_bgm):
        shutil.copyfile(sample_bgm, dest_bgm)

    # 5. Assemble Remotion Props
    update(78, "Assembling Remotion motion graphics props...")
    
    # Safe scene references
    c1 = scenes[0] if len(scenes) > 0 else {}
    c2 = scenes[1] if len(scenes) > 1 else {}
    c3 = scenes[2] if len(scenes) > 2 else {}
    c4 = scenes[3] if len(scenes) > 3 else {}
    c5 = scenes[4] if len(scenes) > 4 else {}
    c6 = scenes[5] if len(scenes) > 5 else {}

    default_c3_chart = [
        {"label": "Baseline", "value": 25},
        {"label": "Target", "value": 70},
        {"label": "Optimized", "value": 98}
    ]
    default_c5_chart = [
        {"label": "Phase 1", "value": 20},
        {"label": "Phase 2", "value": 55},
        {"label": "Phase 3", "value": 92}
    ]

    dur_factor = float(duration) / 60.0

    cuts = [
        {
            "id": "cut-1-hero",
            "type": "hero_title",
            "in_seconds": round(0.0 * dur_factor, 2),
            "out_seconds": round(8.2 * dur_factor, 2),
            "text": c1.get("title") or c1.get("text") or topic,
            "subtitle": c1.get("subtitle", "The Hidden Science"),
            "backgroundVideo": broll_paths[0],
            "backgroundOverlay": 0.48
        },
        {
            "id": "cut-2-stat",
            "type": "stat_card",
            "in_seconds": round(8.2 * dur_factor, 2),
            "out_seconds": round(17.5 * dur_factor, 2),
            "stat": c2.get("stat", "99.9%"),
            "subtitle": c2.get("subtitle", "Critical Threshold"),
            "accentColor": "#38BDF8",
            "backgroundVideo": broll_paths[1] if len(broll_paths) > 1 else broll_paths[0],
            "backgroundOverlay": 0.48
        },
        {
            "id": "cut-3-chart",
            "type": "bar_chart",
            "in_seconds": round(17.5 * dur_factor, 2),
            "out_seconds": round(28.0 * dur_factor, 2),
            "title": c3.get("title", "Comparative Analysis"),
            "chartData": c3.get("chartData") or default_c3_chart,
            "chartColors": ["#38BDF8", "#34D399", "#F87171"],
            "showGrid": True,
            "showValues": True,
            "backgroundVideo": broll_paths[2] if len(broll_paths) > 2 else broll_paths[0],
            "backgroundOverlay": 0.52
        },
        {
            "id": "cut-4-belt",
            "type": "stat_card",
            "in_seconds": round(28.0 * dur_factor, 2),
            "out_seconds": round(38.0 * dur_factor, 2),
            "stat": c4.get("stat", "Global Scale"),
            "subtitle": c4.get("subtitle", "Strategic Scope"),
            "accentColor": "#FBBF24",
            "backgroundVideo": broll_paths[3] if len(broll_paths) > 3 else broll_paths[0],
            "backgroundOverlay": 0.48
        },
        {
            "id": "cut-5-altitude",
            "type": "bar_chart",
            "in_seconds": round(38.0 * dur_factor, 2),
            "out_seconds": round(53.5 * dur_factor, 2),
            "title": c5.get("title", "Growth & Impact Metrics"),
            "chartData": c5.get("chartData") or default_c5_chart,
            "chartColors": ["#94A3B8", "#A78BFA", "#34D399"],
            "showGrid": True,
            "showValues": True,
            "backgroundVideo": broll_paths[4] if len(broll_paths) > 4 else broll_paths[0],
            "backgroundOverlay": 0.50
        },
        {
            "id": "cut-6-outro",
            "type": "text_card",
            "in_seconds": round(53.5 * dur_factor, 2),
            "out_seconds": round(float(duration), 2),
            "text": c6.get("title") or c6.get("text") or f"The future of {topic} is unfolding now.",
            "color": "#F8FAFC",
            "backgroundVideo": broll_paths[5] if len(broll_paths) > 5 else broll_paths[0],
            "backgroundOverlay": 0.48
        }
    ]

    highlight_color = "#FBBF24"
    if caption_style == "cyber-cyan":
        highlight_color = "#22D3EE"
    elif caption_style == "clean-white":
        highlight_color = "#FFFFFF"

    remotion_props = {
        "format": aspect_ratio,
        "theme": theme,
        "themeConfig": {
            "captionHighlightColor": highlight_color,
            "springConfig": {"damping": 18, "stiffness": 100, "mass": 1}
        },
        "cuts": cuts,
        "captions": captions_data,
        "audio": {
            "narration": {
                "src": f"projects/{slug}/narration.mp3",
                "volume": 1.0
            },
            "music": {
                "src": f"projects/{slug}/bgm.mp3",
                "volume": 0.18,
                "fadeInSeconds": 1.5,
                "fadeOutSeconds": 3.0
            }
        }
    }

    props_path = os.path.join(project_dir, "remotion_props.json")
    with open(props_path, "w", encoding="utf-8") as f:
        json.dump(remotion_props, f, indent=2)

    # 6. Render Full HD MP4
    output_mp4 = os.path.join(RENDERS_DIR, f"{slug}.mp4")
    update(88, f"Rendering Full HD MP4 in Remotion ({output_mp4})...")
    render_py = os.path.join(TOOLS_DIR, "render.py")
    composition_name = "ExplainerShorts" if aspect_ratio == "9:16" else "Explainer"
    subprocess.run([PYTHON_EXEC, render_py, "--props", props_path, "--out", output_mp4, "--composition", composition_name, "--concurrency", "4"], check=True)

    update(100, f"✨ Production Complete! Video ready at: {output_mp4}")
    return output_mp4

def main():
    parser = argparse.ArgumentParser(description="Run end-to-end explainer video production.")
    parser.add_argument("--spec", help="Path to spec JSON file")
    parser.add_argument("--topic", help="Topic string")
    parser.add_argument("--format", default="16:9", choices=["16:9", "9:16"], help="Aspect ratio (16:9 or 9:16)")
    parser.add_argument("--voice", default="en-US-AndrewMultilingualNeural", help="Voice name")
    parser.add_argument("--theme", default="flat-motion-graphics", help="Theme palette")
    parser.add_argument("--caption", default="kinetic-gold", help="Caption style")
    parser.add_argument("--duration", type=int, default=60, help="Duration in seconds")
    args = parser.parse_args()

    spec = {}
    if args.spec and os.path.exists(args.spec):
        with open(args.spec, "r", encoding="utf-8") as f:
            spec = json.load(f)
    if args.topic:
        spec["topic"] = args.topic
    if args.format:
        spec["format"] = args.format
    if args.voice:
        spec["voice"] = args.voice
    if args.theme:
        spec["theme"] = args.theme
    if args.caption:
        spec["captionStyle"] = args.caption
    if args.duration:
        spec["duration"] = args.duration

    run_pipeline(spec)

if __name__ == "__main__":
    main()
