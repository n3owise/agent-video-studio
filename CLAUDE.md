# CLAUDE.md — Agent Video Studio Instructions

When asked to produce or edit an explainer video:
1. Always consult `AGENTS.md` for the component list, tools, and execution steps.
2. Check `projects/current_task.json` if the user configured a video via the localhost Studio UI (`python studio.py`).
3. Use the built-in helper tools in `tools/`:
   - `python tools/voice.py` for speech synthesis (edge-tts)
   - `python tools/captions.py` for millisecond Whisper alignment
   - `python tools/broll.py` for 1080p stock footage normalization
   - `python tools/render.py` for Remotion Full HD export
4. Keep `backgroundOverlay` at ~0.48 so text & charts are crisp over video footage.
