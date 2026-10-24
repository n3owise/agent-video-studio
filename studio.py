#!/usr/bin/env python3
"""
studio.py - The Localhost Video Studio UI
A modern, zero-dependency dark-mode web control panel for configuring explainer videos.
Runs on http://localhost:5500
"""

import http.server
import json
import os
import socketserver
import urllib.parse
import webbrowser
import glob

PORT = 5500
REPO_ROOT = os.path.dirname(os.path.abspath(__file__))
PROJECTS_DIR = os.path.join(REPO_ROOT, "projects")
RENDERS_DIR = os.path.join(REPO_ROOT, "renders")

HTML_TEMPLATE = """<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Agent Video Studio</title>
  <style>
    :root {
      --bg: #0b0f19;
      --card-bg: rgba(23, 32, 54, 0.7);
      --border: rgba(255, 255, 255, 0.1);
      --accent: #f59e0b;
      --accent-glow: rgba(245, 158, 11, 0.3);
      --text: #f8fafc;
      --muted: #94a3b8;
      --input-bg: rgba(15, 23, 42, 0.8);
    }
    * { box-sizing: border-box; margin: 0; padding: 0; }
    body {
      font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
      background: radial-gradient(circle at top, #1e293b 0%, #0b0f19 100%);
      color: var(--text);
      min-height: 100vh;
      padding: 30px 20px;
      display: flex;
      justify-content: center;
    }
    .container {
      width: 100%;
      max-width: 860px;
    }
    header {
      text-align: center;
      margin-bottom: 30px;
    }
    h1 {
      font-size: 2.2rem;
      font-weight: 800;
      background: linear-gradient(135deg, #f59e0b, #fbbf24, #38bdf8);
      -webkit-background-clip: text;
      -webkit-text-fill-color: transparent;
      margin-bottom: 8px;
    }
    p.subtitle {
      color: var(--muted);
      font-size: 1rem;
    }
    .card {
      background: var(--card-bg);
      backdrop-filter: blur(12px);
      border: 1px solid var(--border);
      border-radius: 16px;
      padding: 24px;
      margin-bottom: 24px;
      box-shadow: 0 8px 32px rgba(0,0,0,0.3);
    }
    .section-title {
      font-size: 1.1rem;
      font-weight: 700;
      margin-bottom: 14px;
      display: flex;
      align-items: center;
      gap: 8px;
      color: #e2e8f0;
    }
    label {
      display: block;
      font-size: 0.85rem;
      font-weight: 600;
      color: var(--muted);
      margin-bottom: 6px;
      text-transform: uppercase;
      letter-spacing: 0.5px;
    }
    input[type="text"], textarea, select {
      width: 100%;
      padding: 12px 14px;
      background: var(--input-bg);
      border: 1px solid var(--border);
      border-radius: 8px;
      color: var(--text);
      font-size: 1rem;
      outline: none;
      transition: all 0.2s;
    }
    input[type="text"]:focus, textarea:focus, select:focus {
      border-color: var(--accent);
      box-shadow: 0 0 0 3px var(--accent-glow);
    }
    .grid-2 {
      display: grid;
      grid-template-columns: 1fr 1fr;
      gap: 16px;
    }
    .pills {
      display: flex;
      flex-wrap: wrap;
      gap: 8px;
      margin-top: 10px;
    }
    .pill {
      font-size: 0.8rem;
      padding: 5px 12px;
      background: rgba(255,255,255,0.06);
      border: 1px solid var(--border);
      border-radius: 20px;
      cursor: pointer;
      color: #cbd5e1;
      transition: all 0.2s;
    }
    .pill:hover {
      background: var(--accent);
      color: #0b0f19;
      font-weight: 600;
    }
    .btn {
      background: linear-gradient(135deg, #f59e0b, #d97706);
      color: #0b0f19;
      font-size: 1.1rem;
      font-weight: 700;
      padding: 14px 28px;
      border: none;
      border-radius: 10px;
      cursor: pointer;
      width: 100%;
      transition: all 0.2s;
      box-shadow: 0 4px 16px var(--accent-glow);
    }
    .btn:hover {
      transform: translateY(-2px);
      box-shadow: 0 6px 24px var(--accent-glow);
    }
    .prompt-box {
      margin-top: 20px;
      padding: 16px;
      background: rgba(15, 23, 42, 0.9);
      border: 1px dashed var(--accent);
      border-radius: 10px;
      display: none;
    }
    .prompt-box pre {
      white-space: pre-wrap;
      font-family: monospace;
      font-size: 0.95rem;
      color: #38bdf8;
      margin-top: 8px;
    }
    .gallery {
      margin-top: 30px;
    }
    .video-item {
      background: rgba(15, 23, 42, 0.6);
      border: 1px solid var(--border);
      border-radius: 12px;
      padding: 16px;
      margin-bottom: 16px;
    }
    video {
      width: 100%;
      border-radius: 8px;
      margin-top: 10px;
      background: #000;
    }
    .status-badge {
      display: inline-block;
      padding: 4px 10px;
      border-radius: 20px;
      font-size: 0.75rem;
      font-weight: 700;
      background: rgba(34, 197, 94, 0.2);
      color: #4ade80;
      border: 1px solid rgba(34, 197, 94, 0.3);
    }
  </style>
</head>
<body>
  <div class="container">
    <header>
      <h1>🎬 Agent Video Studio</h1>
      <p class="subtitle">Design your explainer in seconds — let your AI agent handle production</p>
    </header>

    <div class="card">
      <form id="studio-form">
        <div style="margin-bottom: 20px;">
          <label>Topic & Core Narrative</label>
          <input type="text" id="topic" placeholder="e.g. Why Coffee Only Grows in the Bean Belt" required />
          <div class="pills">
            <span class="pill" onclick="setTopic('Why Coffee Only Grows in the Bean Belt')">☕ Coffee Belt</span>
            <span class="pill" onclick="setTopic('How Quantum Computers Work')">⚛️ Quantum Computing</span>
            <span class="pill" onclick="setTopic('Why Airplanes Can Fly')">✈️ Flight Physics</span>
            <span class="pill" onclick="setTopic('The 1969 Apollo Moon Landing')">🚀 Apollo Moon Landing</span>
            <span class="pill" onclick="setTopic('How mRNA Vaccines Train Immunity')">🧬 mRNA Vaccines</span>
          </div>
        </div>

        <div class="grid-2" style="margin-bottom: 20px;">
          <div>
            <label>Aspect Ratio</label>
            <select id="format">
              <option value="16:9">16:9 Landscape (YouTube, TV, Presentations)</option>
              <option value="9:16">9:16 Vertical (TikTok, Instagram Reels, Shorts)</option>
            </select>
          </div>
          <div>
            <label>Target Duration</label>
            <select id="duration">
              <option value="60">60 Seconds (Full Deep-Dive Explainer)</option>
              <option value="30">30 Seconds (Fast Punchy Hook)</option>
            </select>
          </div>
        </div>

        <div class="grid-2" style="margin-bottom: 20px;">
          <div>
            <label>Neural Voice (100% Free)</label>
            <select id="voice">
              <option value="en-US-AndrewMultilingualNeural">Andrew (Warm, Expressive Male Narrator)</option>
              <option value="en-US-AriaNeural">Aria (Engaging, Crisp Female Narrator)</option>
              <option value="en-US-BrianNeural">Brian (Deep, Authoritative Documentary)</option>
              <option value="en-US-EmmaMultilingualNeural">Emma (Warm & Friendly Female)</option>
              <option value="en-US-GuyNeural">Guy (Conversational Everyday Male)</option>
            </select>
          </div>
          <div>
            <label>Caption Style</label>
            <select id="captionStyle">
              <option value="kinetic-gold">✨ TikTok Word-by-Word Active Gold</option>
              <option value="cyber-cyan">💎 Cyber Neon Cyan Highlight</option>
              <option value="clean-white">⚪ Clean Minimalist Monochrome</option>
            </select>
          </div>
        </div>

        <div style="margin-bottom: 24px;">
          <label>Visual Theme & Motion Preset</label>
          <select id="theme">
            <option value="flat-motion-graphics">☕ Coffee Warm Roast (#F59E0B Amber / #120E0B Dark Roast)</option>
            <option value="clean-professional">🌐 Clean Corporate (#2563EB Blue / #FFFFFF Crisp)</option>
            <option value="minimalist-diagram">📐 Modern Tech Blueprint (#1A1A2E Navy / #E94560 Coral)</option>
            <option value="anime-ghibli">🍃 Nature & Organic (#2D5016 Forest / #FFB347 Gold)</option>
          </select>
        </div>

        <button type="submit" class="btn">🚀 Prepare Production Task</button>
      </form>

      <div id="prompt-box" class="prompt-box">
        <div style="display:flex; justify-content:space-between; align-items:center;">
          <strong style="color:#f59e0b;">✨ Task Saved! Copy this prompt to your AI Agent:</strong>
          <span class="status-badge">READY IN projects/current_task.json</span>
        </div>
        <pre id="agent-prompt">Produce the video specified in projects/current_task.json following AGENTS.md</pre>
      </div>
    </div>

    <div class="gallery">
      <div class="section-title">🎞️ Recent Renders & Gallery</div>
      <div id="gallery-container">
        <!-- Videos will be listed here -->
      </div>
    </div>
  </div>

  <script>
    function setTopic(text) {
      document.getElementById('topic').value = text;
    }

    document.getElementById('studio-form').addEventListener('submit', async (e) => {
      e.preventDefault();
      const spec = {
        topic: document.getElementById('topic').value,
        format: document.getElementById('format').value,
        duration: parseInt(document.getElementById('duration').value),
        voice: document.getElementById('voice').value,
        captionStyle: document.getElementById('captionStyle').value,
        theme: document.getElementById('theme').value,
        createdAt: new Date().toISOString()
      };

      const res = await fetch('/api/save-task', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(spec)
      });

      if (res.ok) {
        document.getElementById('prompt-box').style.display = 'block';
        document.getElementById('agent-prompt').innerText = 
          `Please produce the explainer video according to projects/current_task.json. Follow all guidelines in AGENTS.md.`;
      }
    });

    async function loadGallery() {
      const res = await fetch('/api/renders');
      if (res.ok) {
        const videos = await res.json();
        const container = document.getElementById('gallery-container');
        if (videos.length === 0) {
          container.innerHTML = '<p style="color:var(--muted); font-size:0.9rem;">No rendered videos yet. Produce your first one with your AI agent!</p>';
          return;
        }
        container.innerHTML = videos.map(v => `
          <div class="video-item">
            <div style="display:flex; justify-content:space-between; align-items:center;">
              <strong>${v.name}</strong>
              <a href="${v.url}" download style="color:#38bdf8; text-decoration:none; font-size:0.85rem; font-weight:600;">⬇️ Download MP4</a>
            </div>
            <video controls src="${v.url}"></video>
          </div>
        `).join('');
      }
    }

    loadGallery();
  </script>
</body>
</html>
"""

class StudioHandler(http.server.SimpleHTTPRequestHandler):
    def do_GET(self):
        parsed = urllib.parse.urlparse(self.path)
        if parsed.path == "/" or parsed.path == "/index.html":
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.end_headers()
            self.wfile.write(HTML_TEMPLATE.encode("utf-8"))
            return

        if parsed.path == "/api/renders":
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            
            video_files = []
            for pattern in [os.path.join(RENDERS_DIR, "*.mp4"), os.path.join(PROJECTS_DIR, "**", "*.mp4")]:
                for f in glob.glob(pattern, recursive=True):
                    rel = os.path.relpath(f, REPO_ROOT)
                    video_files.append({
                        "name": os.path.basename(f),
                        "url": f"/files/{rel}"
                    })
            self.wfile.write(json.dumps(video_files).encode("utf-8"))
            return

        if parsed.path.startswith("/files/"):
            rel_path = parsed.path[len("/files/"):]
            full_path = os.path.join(REPO_ROOT, rel_path)
            if os.path.exists(full_path) and os.path.isfile(full_path):
                self.send_response(200)
                if full_path.endswith(".mp4"):
                    self.send_header("Content-Type", "video/mp4")
                self.send_header("Content-Length", str(os.path.getsize(full_path)))
                self.end_headers()
                with open(full_path, "rb") as f:
                    self.wfile.write(f.read())
                return

        super().do_GET()

    def do_POST(self):
        if self.path == "/api/save-task":
            length = int(self.headers.get("Content-Length", 0))
            body = self.rfile.read(length).decode("utf-8")
            data = json.loads(body)
            
            os.makedirs(PROJECTS_DIR, exist_ok=True)
            task_path = os.path.join(PROJECTS_DIR, "current_task.json")
            with open(task_path, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2)
                
            print(f"[Studio] New task saved to: {task_path}")
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(json.dumps({"status": "ok", "task_path": task_path}).encode("utf-8"))
            return

        self.send_response(404)
        self.end_headers()

def run_server():
    os.makedirs(PROJECTS_DIR, exist_ok=True)
    os.makedirs(RENDERS_DIR, exist_ok=True)
    
    server_address = ("", PORT)
    with socketserver.TCPServer(server_address, StudioHandler) as httpd:
        print(f"✨ Agent Video Studio UI running at: http://localhost:{PORT}")
        print("Press Ctrl+C to stop.")
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            print("\nStudio server stopped.")

if __name__ == "__main__":
    run_server()
