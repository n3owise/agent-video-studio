# CLAUDE.md — Agent Video Studio Instructions

## ⚡ 1-Step Launch Trigger
When the user says **"Install and run https://github.com/n3owise/agent-video-studio"** or asks to launch the studio:
1. Ensure dependencies: `pip install -r requirements.txt` and `cd remotion-composer && npm install && cd ..`
2. Start `python3 studio.py` as a background process (it auto-opens `http://localhost:5500` in their default browser).
3. If needed, run `open http://localhost:5500` (macOS) or `xdg-open http://localhost:5500` (Linux) or `start http://localhost:5500` (Windows).
4. Inform the user: *"Agent Video Studio is open at http://localhost:5500 with the 1-click video generator ready."*

---

## Direct Production Workflow
When asked to produce or edit an explainer video via chat:
1. Always consult `AGENTS.md` for the component list, tools, and execution steps.
2. Check `projects/current_task.json` if the user configured a video via the localhost Studio UI.
3. Use the built-in helper tools in `tools/`:
   - `python tools/voice.py` for speech synthesis (edge-tts)
   - `python tools/captions.py` for millisecond Whisper alignment
   - `python tools/broll.py` for 1080p stock footage normalization
   - `python tools/render.py` for Remotion Full HD export
4. Keep `backgroundOverlay` at ~0.48 so text & charts are crisp over video footage.
