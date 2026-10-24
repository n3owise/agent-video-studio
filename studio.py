#!/usr/bin/env python3
"""
studio.py - Agent Video Studio Control Center
A minimalist, high-end, Awwwards-inspired control panel for directing explainer videos.
Runs locally at http://localhost:5500
"""

import http.server
import json
import os
import socketserver
import urllib.parse
import glob
import subprocess
import sys

PORT = 5500
REPO_ROOT = os.path.dirname(os.path.abspath(__file__))
PROJECTS_DIR = os.path.join(REPO_ROOT, "projects")
RENDERS_DIR = os.path.join(REPO_ROOT, "renders")

HTML_TEMPLATE = """<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Agent Video Studio — The Film Director for Coding Agents</title>
  <link rel="preconnect" href="https://fonts.googleapis.com">
  <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
  <link href="https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@300;400;500;600;700;800&family=JetBrains+Mono:wght@400;500;600&display=swap" rel="stylesheet">
  <style>
    :root {
      --bg: #07080c;
      --card-bg: rgba(13, 16, 26, 0.75);
      --card-border: rgba(255, 255, 255, 0.08);
      --card-hover: rgba(255, 255, 255, 0.14);
      --accent: #f59e0b;
      --accent-light: #fbbf24;
      --accent-glow: rgba(245, 158, 11, 0.25);
      --cyan: #38bdf8;
      --text: #f1f5f9;
      --text-muted: #94a3b8;
      --text-dim: #64748b;
      --surface-inner: rgba(8, 11, 18, 0.65);
    }

    * { box-sizing: border-box; margin: 0; padding: 0; }

    body {
      font-family: 'Plus Jakarta Sans', -apple-system, BlinkMacSystemFont, sans-serif;
      background-color: var(--bg);
      color: var(--text);
      min-height: 100vh;
      overflow-x: hidden;
      position: relative;
      display: flex;
      flex-direction: column;
      align-items: center;
      padding: 40px 20px 80px;
    }

    /* Ambient lighting */
    body::before {
      content: "";
      position: fixed;
      top: -200px;
      left: 50%;
      transform: translateX(-50%);
      width: 900px;
      height: 500px;
      background: radial-gradient(ellipse at center, rgba(245, 158, 11, 0.12) 0%, rgba(56, 189, 248, 0.05) 45%, transparent 70%);
      pointer-events: none;
      z-index: 0;
    }

    .container {
      width: 100%;
      max-width: 900px;
      position: relative;
      z-index: 1;
    }

    /* Header */
    header {
      display: flex;
      flex-direction: column;
      align-items: center;
      text-align: center;
      margin-bottom: 40px;
    }

    .top-badge {
      display: inline-flex;
      align-items: center;
      gap: 8px;
      padding: 6px 14px;
      border-radius: 999px;
      background: rgba(255, 255, 255, 0.04);
      border: 1px solid rgba(255, 255, 255, 0.08);
      font-family: 'JetBrains Mono', monospace;
      font-size: 0.75rem;
      letter-spacing: 0.05em;
      color: var(--text-muted);
      margin-bottom: 18px;
      backdrop-filter: blur(8px);
    }

    .status-pulse {
      width: 7px;
      height: 7px;
      border-radius: 50%;
      background: #10b981;
      box-shadow: 0 0 10px #10b981;
      animation: pulse 2s infinite ease-in-out;
    }

    @keyframes pulse {
      0%, 100% { opacity: 1; transform: scale(1); }
      50% { opacity: 0.4; transform: scale(0.85); }
    }

    h1 {
      font-size: 2.75rem;
      font-weight: 800;
      letter-spacing: -0.03em;
      line-height: 1.15;
      margin-bottom: 12px;
      background: linear-gradient(180deg, #ffffff 30%, #cbd5e1 100%);
      -webkit-background-clip: text;
      -webkit-text-fill-color: transparent;
    }

    h1 span.gradient {
      background: linear-gradient(135deg, #f59e0b 0%, #fbbf24 50%, #38bdf8 100%);
      -webkit-background-clip: text;
      -webkit-text-fill-color: transparent;
    }

    p.subtitle {
      color: var(--text-muted);
      font-size: 1.05rem;
      font-weight: 400;
      max-width: 580px;
      line-height: 1.6;
    }

    /* Luxury Glass Cards */
    .glass-card {
      background: var(--card-bg);
      backdrop-filter: blur(20px);
      -webkit-backdrop-filter: blur(20px);
      border: 1px solid var(--card-border);
      border-radius: 20px;
      padding: 32px;
      margin-bottom: 24px;
      box-shadow: 0 20px 40px -15px rgba(0, 0, 0, 0.5), inset 0 1px 0 rgba(255, 255, 255, 0.06);
      transition: border-color 0.3s;
    }

    .field-group {
      margin-bottom: 26px;
    }

    .field-group:last-child {
      margin-bottom: 0;
    }

    .label-row {
      display: flex;
      justify-content: space-between;
      align-items: center;
      margin-bottom: 10px;
    }

    label {
      font-size: 0.8rem;
      font-weight: 700;
      text-transform: uppercase;
      letter-spacing: 0.08em;
      color: var(--text-muted);
    }

    .label-hint {
      font-size: 0.75rem;
      color: var(--text-dim);
    }

    /* Clean Input */
    input[type="text"], textarea {
      width: 100%;
      padding: 16px 18px;
      background: var(--surface-inner);
      border: 1px solid var(--card-border);
      border-radius: 12px;
      color: var(--text);
      font-family: inherit;
      font-size: 1.05rem;
      font-weight: 500;
      outline: none;
      transition: all 0.25s cubic-bezier(0.16, 1, 0.3, 1);
      box-shadow: inset 0 2px 4px rgba(0,0,0,0.2);
    }

    input[type="text"]:focus, textarea:focus {
      border-color: rgba(245, 158, 11, 0.6);
      box-shadow: 0 0 0 4px var(--accent-glow), inset 0 2px 4px rgba(0,0,0,0.2);
    }

    /* Minimal Pills */
    .pills {
      display: flex;
      flex-wrap: wrap;
      gap: 8px;
      margin-top: 12px;
    }

    .pill {
      font-size: 0.8rem;
      font-weight: 500;
      padding: 6px 14px;
      background: rgba(255, 255, 255, 0.03);
      border: 1px solid rgba(255, 255, 255, 0.06);
      border-radius: 999px;
      color: var(--text-muted);
      cursor: pointer;
      transition: all 0.2s ease;
      user-select: none;
    }

    .pill:hover {
      background: rgba(245, 158, 11, 0.15);
      border-color: rgba(245, 158, 11, 0.4);
      color: var(--accent-light);
      transform: translateY(-1px);
    }

    /* Interactive Visual Cards for Aspect Ratio */
    .aspect-grid {
      display: grid;
      grid-template-columns: 1fr 1fr;
      gap: 14px;
    }

    .aspect-card {
      display: flex;
      align-items: center;
      gap: 16px;
      padding: 16px 20px;
      background: var(--surface-inner);
      border: 1px solid var(--card-border);
      border-radius: 14px;
      cursor: pointer;
      transition: all 0.25s cubic-bezier(0.16, 1, 0.3, 1);
      position: relative;
      user-select: none;
    }

    .aspect-card:hover {
      border-color: var(--card-hover);
      background: rgba(255, 255, 255, 0.03);
    }

    .aspect-card.active {
      border-color: var(--accent);
      background: rgba(245, 158, 11, 0.06);
      box-shadow: 0 0 0 1px var(--accent), 0 8px 20px -8px var(--accent-glow);
    }

    .aspect-icon-box {
      width: 44px;
      height: 44px;
      border-radius: 10px;
      background: rgba(255, 255, 255, 0.04);
      border: 1px solid rgba(255, 255, 255, 0.08);
      display: flex;
      align-items: center;
      justify-content: center;
      color: var(--text-muted);
      transition: all 0.2s;
    }

    .aspect-card.active .aspect-icon-box {
      background: rgba(245, 158, 11, 0.15);
      border-color: rgba(245, 158, 11, 0.3);
      color: var(--accent-light);
    }

    .aspect-info h4 {
      font-size: 0.95rem;
      font-weight: 700;
      color: var(--text);
      margin-bottom: 2px;
    }

    .aspect-info p {
      font-size: 0.78rem;
      color: var(--text-dim);
    }

    /* Segmented Toggle for Duration */
    .segmented-control {
      display: flex;
      padding: 4px;
      background: var(--surface-inner);
      border: 1px solid var(--card-border);
      border-radius: 12px;
    }

    .segment-btn {
      flex: 1;
      padding: 12px 16px;
      font-size: 0.88rem;
      font-weight: 600;
      border: none;
      background: transparent;
      color: var(--text-muted);
      border-radius: 8px;
      cursor: pointer;
      transition: all 0.2s;
      text-align: center;
      user-select: none;
    }

    .segment-btn.active {
      background: rgba(255, 255, 255, 0.08);
      color: #ffffff;
      box-shadow: 0 2px 8px rgba(0,0,0,0.3);
    }

    /* Dropdowns */
    .custom-select-wrapper {
      position: relative;
    }

    select {
      width: 100%;
      padding: 15px 40px 15px 16px;
      background: var(--surface-inner);
      border: 1px solid var(--card-border);
      border-radius: 12px;
      color: var(--text);
      font-family: inherit;
      font-size: 0.95rem;
      font-weight: 500;
      outline: none;
      cursor: pointer;
      appearance: none;
      transition: all 0.2s;
    }

    select:focus {
      border-color: rgba(245, 158, 11, 0.6);
      box-shadow: 0 0 0 3px var(--accent-glow);
    }

    .select-chevron {
      position: absolute;
      right: 16px;
      top: 50%;
      transform: translateY(-50%);
      pointer-events: none;
      color: var(--text-dim);
    }

    .grid-2 {
      display: grid;
      grid-template-columns: 1fr 1fr;
      gap: 16px;
    }

    /* Awwwards Button */
    .submit-btn {
      width: 100%;
      padding: 18px 32px;
      background: linear-gradient(135deg, #f59e0b 0%, #d97706 100%);
      border: none;
      border-radius: 14px;
      color: #050811;
      font-family: inherit;
      font-size: 1.05rem;
      font-weight: 800;
      letter-spacing: -0.01em;
      cursor: pointer;
      box-shadow: 0 10px 30px -5px var(--accent-glow), inset 0 1px 0 rgba(255, 255, 255, 0.3);
      transition: all 0.25s cubic-bezier(0.16, 1, 0.3, 1);
      display: flex;
      align-items: center;
      justify-content: center;
      gap: 10px;
      margin-top: 10px;
    }

    .submit-btn:hover {
      transform: translateY(-2px);
      box-shadow: 0 16px 40px -5px rgba(245, 158, 11, 0.45);
      background: linear-gradient(135deg, #fbbf24 0%, #f59e0b 100%);
    }

    .submit-btn:active {
      transform: translateY(0);
    }

    /* Result Agent Terminal Card */
    .prompt-card {
      display: none;
      margin-top: 24px;
      background: rgba(10, 14, 23, 0.95);
      border: 1px solid rgba(245, 158, 11, 0.4);
      border-radius: 16px;
      padding: 24px;
      box-shadow: 0 12px 36px -10px rgba(0, 0, 0, 0.8), 0 0 20px -5px rgba(245, 158, 11, 0.15);
      animation: fadeIn 0.4s ease forwards;
    }

    @keyframes fadeIn {
      from { opacity: 0; transform: translateY(8px); }
      to { opacity: 1; transform: translateY(0); }
    }

    .terminal-header {
      display: flex;
      justify-content: space-between;
      align-items: center;
      margin-bottom: 14px;
    }

    .terminal-title {
      font-family: 'JetBrains Mono', monospace;
      font-size: 0.8rem;
      font-weight: 600;
      color: var(--accent-light);
      display: flex;
      align-items: center;
      gap: 8px;
    }

    .copy-btn {
      background: rgba(255, 255, 255, 0.08);
      border: 1px solid rgba(255, 255, 255, 0.12);
      border-radius: 8px;
      color: #ffffff;
      padding: 6px 14px;
      font-size: 0.78rem;
      font-weight: 600;
      cursor: pointer;
      display: flex;
      align-items: center;
      gap: 6px;
      transition: all 0.2s;
    }

    .copy-btn:hover {
      background: rgba(255, 255, 255, 0.15);
    }

    .terminal-code {
      background: #030407;
      border: 1px solid rgba(255, 255, 255, 0.06);
      border-radius: 10px;
      padding: 16px;
      font-family: 'JetBrains Mono', monospace;
      font-size: 0.9rem;
      line-height: 1.6;
      color: #38bdf8;
      overflow-x: auto;
      white-space: pre-wrap;
    }

    /* Video Showcase Gallery */
    .gallery-section {
      margin-top: 36px;
    }

    .gallery-title {
      font-size: 1.25rem;
      font-weight: 800;
      letter-spacing: -0.02em;
      margin-bottom: 16px;
      color: var(--text);
      display: flex;
      align-items: center;
      gap: 10px;
    }

    .gallery-grid {
      display: grid;
      grid-template-columns: 1fr;
      gap: 20px;
    }

    .video-card {
      background: var(--card-bg);
      border: 1px solid var(--card-border);
      border-radius: 16px;
      padding: 20px;
      box-shadow: 0 10px 30px rgba(0,0,0,0.3);
      transition: border-color 0.2s;
    }

    .video-card:hover {
      border-color: var(--card-hover);
    }

    .video-header {
      display: flex;
      justify-content: space-between;
      align-items: center;
      margin-bottom: 12px;
    }

    .video-name {
      font-weight: 700;
      font-size: 1rem;
      color: #ffffff;
    }

    .badge-pill {
      font-family: 'JetBrains Mono', monospace;
      font-size: 0.72rem;
      padding: 4px 10px;
      border-radius: 999px;
      background: rgba(56, 189, 248, 0.1);
      border: 1px solid rgba(56, 189, 248, 0.2);
      color: var(--cyan);
    }

    video {
      width: 100%;
      border-radius: 12px;
      background: #000;
      aspect-ratio: 16 / 9;
      box-shadow: 0 4px 20px rgba(0,0,0,0.5);
    }

    .video-footer {
      display: flex;
      justify-content: flex-end;
      margin-top: 14px;
    }

    .download-link {
      display: inline-flex;
      align-items: center;
      gap: 6px;
      color: var(--accent-light);
      text-decoration: none;
      font-size: 0.85rem;
      font-weight: 700;
      transition: opacity 0.2s;
    }

    .download-link:hover {
      opacity: 0.85;
    }

    /* Toast notification */
    #toast {
      position: fixed;
      bottom: 30px;
      left: 50%;
      transform: translateX(-50%) translateY(100px);
      background: #10b981;
      color: #041f14;
      padding: 10px 22px;
      border-radius: 999px;
      font-weight: 700;
      font-size: 0.85rem;
      box-shadow: 0 10px 25px rgba(16, 185, 129, 0.3);
      transition: transform 0.3s cubic-bezier(0.16, 1, 0.3, 1);
      z-index: 1000;
    }

    #toast.show {
      transform: translateX(-50%) translateY(0);
    }

    @media (max-width: 640px) {
      .grid-2, .aspect-grid { grid-template-columns: 1fr; }
      h1 { font-size: 2.1rem; }
      .glass-card { padding: 22px; }
    }
  </style>
</head>
<body>

  <div class="container">
    <header>
      <div class="top-badge">
        <span class="status-pulse"></span>
        <span>STUDIO ENGINE READY • LOCAL HOST 5500</span>
      </div>
      <h1>Direct Videos with <span class="gradient">Your Coding Agent</span></h1>
      <p class="subtitle">Set your visual rules, voice, and topic below. Copy the prompt to Cursor, Claude Code, or Antigravity to render.</p>
    </header>

    <div class="glass-card">
      <form id="studio-form">
        <!-- Topic -->
        <div class="field-group">
          <div class="label-row">
            <label>1. Narrative Topic & Hook</label>
            <span class="label-hint">What story should your video explain?</span>
          </div>
          <input type="text" id="topic" placeholder="e.g. Why Coffee Only Grows in the Bean Belt" required />
          <div class="pills">
            <span class="pill" onclick="setTopic('Why Coffee Only Grows in the Bean Belt')">☕ Coffee Belt</span>
            <span class="pill" onclick="setTopic('How Quantum Computers Factor Numbers')">⚛️ Quantum Computing</span>
            <span class="pill" onclick="setTopic('The Bernoulli Myth: How Wings Actually Fly')">✈️ Flight Physics</span>
            <span class="pill" onclick="setTopic('Why the 1969 Apollo Guidance Computer Survived')">🚀 Apollo Guidance</span>
            <span class="pill" onclick="setTopic('How mRNA Vaccines Train Human Ribosomes')">🧬 mRNA Technology</span>
          </div>
        </div>

        <!-- Aspect Ratio Visual Cards -->
        <div class="field-group">
          <div class="label-row">
            <label>2. Format & Canvas Aspect Ratio</label>
            <span class="label-hint">Target distribution platform</span>
          </div>
          <div class="aspect-grid">
            <div class="aspect-card active" id="card-16-9" onclick="setAspect('16:9')">
              <div class="aspect-icon-box">
                <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><rect x="2" y="5" width="20" height="14" rx="3"></rect><path d="M10 10l5 2-5 2v-4z"></path></svg>
              </div>
              <div class="aspect-info">
                <h4>16:9 Landscape</h4>
                <p>YouTube, Desktop, Keynotes</p>
              </div>
            </div>
            <div class="aspect-card" id="card-9-16" onclick="setAspect('9:16')">
              <div class="aspect-icon-box">
                <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><rect x="5" y="2" width="14" height="20" rx="3"></rect><circle cx="12" cy="18" r="1"></circle></svg>
              </div>
              <div class="aspect-info">
                <h4>9:16 Vertical</h4>
                <p>TikTok, Reels, YouTube Shorts</p>
              </div>
            </div>
          </div>
          <input type="hidden" id="format" value="16:9" />
        </div>

        <!-- Duration & Voice -->
        <div class="field-group grid-2">
          <div>
            <div class="label-row">
              <label>3. Target Duration</label>
            </div>
            <div class="segmented-control">
              <button type="button" class="segment-btn active" id="dur-60" onclick="setDuration(60)">60s Explainer</button>
              <button type="button" class="segment-btn" id="dur-30" onclick="setDuration(30)">30s Fast Hook</button>
            </div>
            <input type="hidden" id="duration" value="60" />
          </div>

          <div>
            <div class="label-row">
              <label>4. Neural Narration Voice</label>
            </div>
            <div class="custom-select-wrapper">
              <select id="voice">
                <option value="en-US-AndrewMultilingualNeural">Andrew (Warm & Expressive Male)</option>
                <option value="en-US-AriaNeural">Aria (Crisp & Engaging Female)</option>
                <option value="en-US-BrianNeural">Brian (Authoritative Documentary)</option>
                <option value="en-US-EmmaMultilingualNeural">Emma (Warm & Friendly Female)</option>
                <option value="en-US-GuyNeural">Guy (Conversational Everyday Male)</option>
              </select>
              <div class="select-chevron">
                <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polyline points="6 9 12 15 18 9"></polyline></svg>
              </div>
            </div>
          </div>
        </div>

        <!-- Caption Style & Visual Theme -->
        <div class="field-group grid-2">
          <div>
            <div class="label-row">
              <label>5. Kinetic Caption Style</label>
            </div>
            <div class="custom-select-wrapper">
              <select id="captionStyle">
                <option value="kinetic-gold">✨ TikTok Active Gold Highlighter</option>
                <option value="cyber-cyan">💎 Cyber Neon Cyan Highlight</option>
                <option value="clean-white">⚪ Clean Minimalist Monochrome</option>
              </select>
              <div class="select-chevron">
                <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polyline points="6 9 12 15 18 9"></polyline></svg>
              </div>
            </div>
          </div>

          <div>
            <div class="label-row">
              <label>6. Color & Motion Palette</label>
            </div>
            <div class="custom-select-wrapper">
              <select id="theme">
                <option value="flat-motion-graphics">☕ Coffee Warm Roast (Amber #F59E0B / Dark Slate)</option>
                <option value="clean-professional">🌐 Clean Modern Fintech (Royal Blue #2563EB / White)</option>
                <option value="minimalist-diagram">📐 Technical Architecture (Navy #1A1A2E / Coral Accent)</option>
                <option value="anime-ghibli">🍃 Nature & Organic (Forest Green / Warm Gold)</option>
              </select>
              <div class="select-chevron">
                <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polyline points="6 9 12 15 18 9"></polyline></svg>
              </div>
            </div>
          </div>
        </div>

        <!-- Action Button -->
        <button type="submit" class="submit-btn">
          <span>🚀 Save Spec & Prepare Production</span>
        </button>
      </form>

      <!-- Terminal Output Prompt -->
      <div id="prompt-card" class="prompt-card">
        <div class="terminal-header">
          <div class="terminal-title">
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polyline points="4 17 10 11 4 5"></polyline><line x1="12" y1="19" x2="20" y2="19"></line></svg>
            <span>TASK PREPARED IN projects/current_task.json</span>
          </div>
          <button type="button" class="copy-btn" onclick="copyPrompt()">
            <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><rect x="9" y="9" width="13" height="13" rx="2" ry="2"></rect><path d="M5 15H4a2 2 0 0 1-2-2V4a2 2 0 0 1 2-2h9a2 2 0 0 1 2 2v1"></path></svg>
            <span id="copy-btn-text">Copy Prompt</span>
          </button>
        </div>
        <div class="terminal-code" id="prompt-code">Please produce the explainer video according to projects/current_task.json. Follow all guidelines in AGENTS.md.</div>
      </div>
    </div>

    <!-- Gallery -->
    <div class="gallery-section">
      <div class="gallery-title">
        <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polygon points="23 7 16 12 23 17 23 7"></polygon><rect x="1" y="5" width="15" height="14" rx="2" ry="2"></rect></svg>
        <span>Production Vault & Renders</span>
      </div>
      <div class="gallery-grid" id="gallery-container">
        <!-- Rendered videos dynamically injected here -->
      </div>
    </div>
  </div>

  <div id="toast">Copied prompt to clipboard!</div>

  <script>
    function setTopic(text) {
      document.getElementById('topic').value = text;
    }

    function setAspect(ratio) {
      document.getElementById('format').value = ratio;
      document.getElementById('card-16-9').classList.toggle('active', ratio === '16:9');
      document.getElementById('card-9-16').classList.toggle('active', ratio === '9:16');
    }

    function setDuration(dur) {
      document.getElementById('duration').value = dur;
      document.getElementById('dur-60').classList.toggle('active', dur === 60);
      document.getElementById('dur-30').classList.toggle('active', dur === 30);
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
        updatedAt: new Date().toISOString()
      };

      const res = await fetch('/api/save-task', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(spec)
      });

      if (res.ok) {
        document.getElementById('prompt-card').style.display = 'block';
        document.getElementById('prompt-code').innerText = 
          `Please read AGENTS.md and produce the explainer video configured in projects/current_task.json:\n` +
          `• Topic: "${spec.topic}"\n` +
          `• Format: ${spec.format} | Duration: ${spec.duration}s\n` +
          `• Voice: ${spec.voice} | Style: ${spec.captionStyle}\n\n` +
          `Execute tools/voice.py, tools/captions.py, tools/broll.py and tools/render.py.`;
        
        document.getElementById('prompt-card').scrollIntoView({ behavior: 'smooth', block: 'nearest' });
      }
    });

    function copyPrompt() {
      const text = document.getElementById('prompt-code').innerText;
      navigator.clipboard.writeText(text);
      
      const toast = document.getElementById('toast');
      toast.classList.add('show');
      setTimeout(() => toast.classList.remove('show'), 2500);

      const btnText = document.getElementById('copy-btn-text');
      btnText.innerText = "Copied!";
      setTimeout(() => btnText.innerText = "Copy Prompt", 2000);
    }

    async function loadGallery() {
      const res = await fetch('/api/renders');
      if (res.ok) {
        const videos = await res.json();
        const container = document.getElementById('gallery-container');
        if (videos.length === 0) {
          container.innerHTML = '<p style="color:var(--text-dim); font-size:0.9rem;">No videos rendered yet. Direct your first one above!</p>';
          return;
        }
        container.innerHTML = videos.map(v => `
          <div class="video-card">
            <div class="video-header">
              <span class="video-name">${v.name}</span>
              <span class="badge-pill">1080P FULL HD • 30 FPS</span>
            </div>
            <video controls src="${v.url}"></video>
            <div class="video-footer">
              <a href="${v.url}" download class="download-link">
                <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"></path><polyline points="7 10 12 15 17 10"></polyline><line x1="12" y1="15" x2="12" y2="3"></line></svg>
                <span>Download Master MP4</span>
              </a>
            </div>
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
                
            print(f"[Studio] New task saved: {task_path}")
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
    
    # Allow port reuse
    socketserver.TCPServer.allow_reuse_address = True
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
