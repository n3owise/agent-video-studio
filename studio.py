#!/usr/bin/env python3
"""
studio.py - Agent Video Studio Control Center
A minimalist, high-end, Awwwards-inspired control panel with live visual caption & theme simulator.
Runs locally at http://localhost:5500
"""

import http.server
import json
import os
import socketserver
import urllib.parse
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
  <title>Agent Video Studio — The Film Director for Coding Agents</title>
  <link rel="preconnect" href="https://fonts.googleapis.com">
  <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
  <link href="https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@300;400;500;600;700;800&family=JetBrains+Mono:wght@400;500;600&family=Space+Grotesk:wght@500;700&display=swap" rel="stylesheet">
  <style>
    :root {
      --bg: #07080c;
      --card-bg: rgba(13, 16, 26, 0.75);
      --card-border: rgba(255, 255, 255, 0.08);
      --card-hover: rgba(255, 255, 255, 0.16);
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
      width: 1000px;
      height: 550px;
      background: radial-gradient(ellipse at center, rgba(245, 158, 11, 0.12) 0%, rgba(56, 189, 248, 0.05) 45%, transparent 70%);
      pointer-events: none;
      z-index: 0;
    }

    .container {
      width: 100%;
      max-width: 960px;
      position: relative;
      z-index: 1;
    }

    /* Header */
    header {
      display: flex;
      flex-direction: column;
      align-items: center;
      text-align: center;
      margin-bottom: 36px;
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
      max-width: 620px;
      line-height: 1.6;
    }

    /* ==========================================================================
       LIVE VISUAL CANVAS SIMULATOR (Real-Time WYSIWYG)
       ========================================================================== */
    .simulator-card {
      background: var(--card-bg);
      border: 1px solid var(--card-border);
      border-radius: 20px;
      padding: 24px;
      margin-bottom: 28px;
      box-shadow: 0 20px 40px -15px rgba(0, 0, 0, 0.5), inset 0 1px 0 rgba(255, 255, 255, 0.06);
      position: relative;
      overflow: hidden;
    }

    .simulator-header {
      display: flex;
      justify-content: space-between;
      align-items: center;
      margin-bottom: 16px;
    }

    .sim-tag {
      font-family: 'JetBrains Mono', monospace;
      font-size: 0.75rem;
      font-weight: 600;
      color: var(--accent-light);
      display: flex;
      align-items: center;
      gap: 6px;
    }

    .sim-screen {
      width: 100%;
      height: 240px;
      border-radius: 14px;
      background: #120e0b;
      border: 1px solid rgba(255, 255, 255, 0.1);
      position: relative;
      overflow: hidden;
      display: flex;
      flex-direction: column;
      justify-content: space-between;
      padding: 24px;
      transition: background 0.4s ease;
      box-shadow: inset 0 0 40px rgba(0,0,0,0.8);
    }

    /* Ambient animated video placeholder in the simulator */
    .sim-screen::before {
      content: "";
      position: absolute;
      inset: 0;
      background: radial-gradient(circle at 70% 30%, rgba(255,255,255,0.06) 0%, transparent 60%);
      pointer-events: none;
    }

    .sim-top-badge {
      align-self: flex-start;
      padding: 4px 10px;
      border-radius: 6px;
      background: rgba(0,0,0,0.6);
      border: 1px solid rgba(255,255,255,0.1);
      font-size: 0.75rem;
      font-weight: 600;
      color: #cbd5e1;
      backdrop-filter: blur(4px);
    }

    .sim-center-content {
      align-self: center;
      text-align: center;
      z-index: 2;
    }

    .sim-metric-val {
      font-family: 'Space Grotesk', sans-serif;
      font-size: 2.2rem;
      font-weight: 800;
      color: var(--accent);
      letter-spacing: -0.02em;
      transition: color 0.3s ease;
    }

    .sim-metric-sub {
      font-size: 0.85rem;
      color: #94a3b8;
      font-weight: 500;
    }

    .sim-caption-bar {
      align-self: center;
      z-index: 2;
      display: flex;
      gap: 6px;
      font-size: 1.05rem;
      font-weight: 700;
      font-family: 'Space Grotesk', sans-serif;
      letter-spacing: -0.01em;
    }

    .sim-word {
      padding: 3px 6px;
      border-radius: 4px;
      color: #ffffff;
      transition: all 0.3s ease;
    }

    /* Caption Style Variations on Live Simulator */
    .sim-caption-bar.style-kinetic-gold .active-word {
      background: #fbbf24;
      color: #0b0f19;
      transform: scale(1.12);
      box-shadow: 0 4px 12px rgba(251, 191, 36, 0.4);
    }

    .sim-caption-bar.style-cyber-cyan .active-word {
      background: #22d3ee;
      color: #041824;
      transform: scale(1.12);
      box-shadow: 0 0 16px rgba(34, 211, 238, 0.8);
    }

    .sim-caption-bar.style-clean-white .active-word {
      background: #ffffff;
      color: #0b0f19;
      transform: scale(1.08);
      box-shadow: 0 2px 10px rgba(255, 255, 255, 0.3);
    }

    /* ==========================================================================
       MAIN FORM & INTERACTIVE VISUAL CARDS
       ========================================================================== */
    .glass-card {
      background: var(--card-bg);
      backdrop-filter: blur(20px);
      -webkit-backdrop-filter: blur(20px);
      border: 1px solid var(--card-border);
      border-radius: 20px;
      padding: 32px;
      margin-bottom: 24px;
      box-shadow: 0 20px 40px -15px rgba(0, 0, 0, 0.5), inset 0 1px 0 rgba(255, 255, 255, 0.06);
    }

    .field-group {
      margin-bottom: 28px;
    }

    .field-group:last-child {
      margin-bottom: 0;
    }

    .label-row {
      display: flex;
      justify-content: space-between;
      align-items: center;
      margin-bottom: 12px;
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
    }

    input[type="text"]:focus, textarea:focus {
      border-color: rgba(245, 158, 11, 0.6);
      box-shadow: 0 0 0 4px var(--accent-glow);
    }

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
    }

    .pill:hover {
      background: rgba(245, 158, 11, 0.15);
      border-color: rgba(245, 158, 11, 0.4);
      color: var(--accent-light);
      transform: translateY(-1px);
    }

    /* Aspect Grid */
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
      transition: all 0.25s;
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
    }

    .aspect-card.active .aspect-icon-box {
      background: rgba(245, 158, 11, 0.15);
      border-color: rgba(245, 158, 11, 0.3);
      color: var(--accent-light);
    }

    /* ==========================================================================
       VISUAL CAPTION STYLE PREVIEW CARDS
       ========================================================================== */
    .caption-style-grid {
      display: grid;
      grid-template-columns: repeat(3, 1fr);
      gap: 14px;
    }

    .style-card {
      background: var(--surface-inner);
      border: 1px solid var(--card-border);
      border-radius: 14px;
      padding: 16px;
      cursor: pointer;
      transition: all 0.25s;
      display: flex;
      flex-direction: column;
      justify-content: space-between;
    }

    .style-card:hover {
      border-color: var(--card-hover);
    }

    .style-card.active {
      border-color: var(--accent);
      background: rgba(245, 158, 11, 0.05);
      box-shadow: 0 0 0 1px var(--accent), 0 8px 20px -8px var(--accent-glow);
    }

    .style-preview-box {
      background: #030408;
      border: 1px solid rgba(255, 255, 255, 0.06);
      border-radius: 10px;
      padding: 14px 10px;
      margin-bottom: 12px;
      display: flex;
      justify-content: center;
      align-items: center;
      font-size: 0.82rem;
      font-weight: 700;
      gap: 4px;
    }

    .style-card-title {
      font-weight: 700;
      font-size: 0.9rem;
      color: var(--text);
      margin-bottom: 2px;
    }

    .style-card-desc {
      font-size: 0.74rem;
      color: var(--text-dim);
      line-height: 1.4;
    }

    /* ==========================================================================
       VISUAL COLOR THEME PREVIEW CARDS
       ========================================================================== */
    .theme-grid {
      display: grid;
      grid-template-columns: repeat(2, 1fr);
      gap: 14px;
    }

    .theme-card {
      background: var(--surface-inner);
      border: 1px solid var(--card-border);
      border-radius: 14px;
      padding: 18px;
      cursor: pointer;
      transition: all 0.25s;
    }

    .theme-card:hover {
      border-color: var(--card-hover);
    }

    .theme-card.active {
      border-color: var(--accent);
      background: rgba(245, 158, 11, 0.05);
      box-shadow: 0 0 0 1px var(--accent), 0 8px 20px -8px var(--accent-glow);
    }

    .theme-card-top {
      display: flex;
      justify-content: space-between;
      align-items: center;
      margin-bottom: 10px;
    }

    .theme-name {
      font-size: 0.92rem;
      font-weight: 700;
      color: #ffffff;
    }

    .swatches {
      display: flex;
      gap: 5px;
    }

    .swatch {
      width: 14px;
      height: 14px;
      border-radius: 50%;
      border: 1px solid rgba(255,255,255,0.2);
    }

    .theme-chart-preview {
      display: flex;
      align-items: flex-end;
      gap: 6px;
      height: 32px;
      padding: 4px 8px;
      background: rgba(0,0,0,0.4);
      border-radius: 6px;
      margin-bottom: 8px;
    }

    .theme-bar {
      border-radius: 3px;
      flex: 1;
    }

    .theme-desc {
      font-size: 0.76rem;
      color: var(--text-dim);
    }

    /* Duration segmented */
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
    }

    .segment-btn.active {
      background: rgba(255, 255, 255, 0.08);
      color: #ffffff;
      box-shadow: 0 2px 8px rgba(0,0,0,0.3);
    }

    /* Dropdown wrapper */
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

    /* Button */
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
      transition: all 0.25s;
      margin-top: 10px;
    }

    .submit-btn:hover {
      transform: translateY(-2px);
      box-shadow: 0 16px 40px -5px rgba(245, 158, 11, 0.45);
      background: linear-gradient(135deg, #fbbf24 0%, #f59e0b 100%);
    }

    /* Prompt output */
    .prompt-card {
      display: none;
      margin-top: 24px;
      background: rgba(10, 14, 23, 0.95);
      border: 1px solid rgba(245, 158, 11, 0.4);
      border-radius: 16px;
      padding: 24px;
      box-shadow: 0 12px 36px -10px rgba(0, 0, 0, 0.8);
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
      white-space: pre-wrap;
    }

    /* Gallery */
    .gallery-section {
      margin-top: 36px;
    }

    .gallery-title {
      font-size: 1.25rem;
      font-weight: 800;
      letter-spacing: -0.02em;
      margin-bottom: 16px;
      display: flex;
      align-items: center;
      gap: 10px;
    }

    .video-card {
      background: var(--card-bg);
      border: 1px solid var(--card-border);
      border-radius: 16px;
      padding: 20px;
      margin-bottom: 20px;
    }

    video {
      width: 100%;
      border-radius: 12px;
      background: #000;
      aspect-ratio: 16 / 9;
    }

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
      .grid-2, .aspect-grid, .caption-style-grid, .theme-grid { grid-template-columns: 1fr; }
      h1 { font-size: 2.1rem; }
      .glass-card { padding: 20px; }
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
      <p class="subtitle">Visually preview caption kinetic motion and color palettes in real-time below. Copy the generated spec to your agent to render.</p>
    </header>

    <!-- =====================================================================
         LIVE VISUAL SIMULATOR (WYSIWYG)
         ===================================================================== -->
    <div class="simulator-card">
      <div class="simulator-header">
        <div class="sim-tag">
          <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="10"></circle><polygon points="10 8 16 12 10 16 10 8"></polygon></svg>
          <span>LIVE COMPOSITION SIMULATOR</span>
        </div>
        <span id="sim-theme-badge" style="font-family:'JetBrains Mono',monospace; font-size:0.75rem; color:#94a3b8;">☕ Coffee Warm Roast</span>
      </div>

      <div class="sim-screen" id="sim-screen">
        <div class="sim-top-badge" id="sim-aspect-badge">16:9 • 1080P Widescreen</div>

        <div class="sim-center-content">
          <div class="sim-metric-val" id="sim-metric">0°C / 32°F</div>
          <div class="sim-metric-sub" id="sim-metric-sub">Biological Kryptonite: Frost kills coffee trees in hours</div>
        </div>

        <div class="sim-caption-bar style-kinetic-gold" id="sim-caption-bar">
          <span class="sim-word">Why</span>
          <span class="sim-word">your</span>
          <span class="sim-word">garden</span>
          <span class="sim-word active-word" id="sim-active-word">CAN'T</span>
          <span class="sim-word">grow</span>
          <span class="sim-word">coffee</span>
        </div>
      </div>
    </div>

    <!-- MAIN CONTROL PANEL -->
    <div class="glass-card">
      <form id="studio-form">
        <!-- 1. Topic -->
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

        <!-- 2. Aspect Ratio -->
        <div class="field-group">
          <div class="label-row">
            <label>2. Format & Canvas Aspect Ratio</label>
          </div>
          <div class="aspect-grid">
            <div class="aspect-card active" id="card-16-9" onclick="setAspect('16:9')">
              <div class="aspect-icon-box">
                <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><rect x="2" y="5" width="20" height="14" rx="3"></rect><path d="M10 10l5 2-5 2v-4z"></path></svg>
              </div>
              <div>
                <h4 style="font-weight:700; margin-bottom:2px;">16:9 Landscape</h4>
                <p style="font-size:0.78rem; color:var(--text-dim);">YouTube, Desktop, Keynotes</p>
              </div>
            </div>
            <div class="aspect-card" id="card-9-16" onclick="setAspect('9:16')">
              <div class="aspect-icon-box">
                <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><rect x="5" y="2" width="14" height="20" rx="3"></rect><circle cx="12" cy="18" r="1"></circle></svg>
              </div>
              <div>
                <h4 style="font-weight:700; margin-bottom:2px;">9:16 Vertical</h4>
                <p style="font-size:0.78rem; color:var(--text-dim);">TikTok, Reels, YouTube Shorts</p>
              </div>
            </div>
          </div>
          <input type="hidden" id="format" value="16:9" />
        </div>

        <!-- 3. VISUAL CAPTION STYLES (SEE HOW IT LOOKS) -->
        <div class="field-group">
          <div class="label-row">
            <label>3. Kinetic Caption Style (Visual Preview)</label>
            <span class="label-hint">Click to see live animation in simulator above</span>
          </div>
          <div class="caption-style-grid">
            <!-- Style 1 -->
            <div class="style-card active" id="style-gold" onclick="setCaptionStyle('kinetic-gold')">
              <div class="style-preview-box">
                <span style="color:#94a3b8;">WHY</span>
                <span style="background:#fbbf24; color:#0b0f19; padding:2px 6px; border-radius:4px; box-shadow:0 0 8px rgba(251,191,36,0.5);">GARDEN</span>
                <span style="color:#94a3b8;">CAN'T</span>
              </div>
              <div class="style-card-title">✨ TikTok Active Gold</div>
              <div class="style-card-desc">High-energy viral TikTok/Reels font with spring bounce box.</div>
            </div>

            <!-- Style 2 -->
            <div class="style-card" id="style-cyan" onclick="setCaptionStyle('cyber-cyan')">
              <div class="style-preview-box">
                <span style="color:#94a3b8;">WHY</span>
                <span style="background:#22d3ee; color:#041824; padding:2px 6px; border-radius:4px; box-shadow:0 0 10px rgba(34,211,238,0.8);">GARDEN</span>
                <span style="color:#94a3b8;">CAN'T</span>
              </div>
              <div class="style-card-title">💎 Cyber Neon Cyan</div>
              <div class="style-card-desc">Luminous sci-fi neon glow for engineering, physics & tech.</div>
            </div>

            <!-- Style 3 -->
            <div class="style-card" id="style-white" onclick="setCaptionStyle('clean-white')">
              <div class="style-preview-box">
                <span style="color:#94a3b8;">WHY</span>
                <span style="background:#ffffff; color:#0b0f19; padding:2px 6px; border-radius:4px;">GARDEN</span>
                <span style="color:#94a3b8;">CAN'T</span>
              </div>
              <div class="style-card-title">⚪ Minimalist Clean</div>
              <div class="style-card-desc">Crisp monochrome contrast for classic documentaries.</div>
            </div>
          </div>
          <input type="hidden" id="captionStyle" value="kinetic-gold" />
        </div>

        <!-- 4. VISUAL MOTION & COLOR PALETTES (SEE HOW IT LOOKS) -->
        <div class="field-group">
          <div class="label-row">
            <label>4. Color & Motion Palette (Visual Preview)</label>
            <span class="label-hint">Click to see canvas colors shift in real time</span>
          </div>
          <div class="theme-grid">
            <!-- Theme 1 -->
            <div class="theme-card active" id="theme-coffee" onclick="setTheme('flat-motion-graphics')">
              <div class="theme-card-top">
                <span class="theme-name">☕ Coffee Warm Roast</span>
                <div class="swatches">
                  <span class="swatch" style="background:#f59e0b;"></span>
                  <span class="swatch" style="background:#d97706;"></span>
                  <span class="swatch" style="background:#38bdf8;"></span>
                  <span class="swatch" style="background:#120e0b;"></span>
                </div>
              </div>
              <div class="theme-chart-preview">
                <div class="theme-bar" style="background:#38bdf8; height:25%;"></div>
                <div class="theme-bar" style="background:#34d399; height:65%;"></div>
                <div class="theme-bar" style="background:#f87171; height:100%;"></div>
              </div>
              <div class="theme-desc">Amber gold accents, dark roast background & vivid temperature bars.</div>
            </div>

            <!-- Theme 2 -->
            <div class="theme-card" id="theme-fintech" onclick="setTheme('clean-professional')">
              <div class="theme-card-top">
                <span class="theme-name">🌐 Modern Tech & SaaS</span>
                <div class="swatches">
                  <span class="swatch" style="background:#2563eb;"></span>
                  <span class="swatch" style="background:#38bdf8;"></span>
                  <span class="swatch" style="background:#10b981;"></span>
                  <span class="swatch" style="background:#ffffff;"></span>
                </div>
              </div>
              <div class="theme-chart-preview">
                <div class="theme-bar" style="background:#2563eb; height:45%;"></div>
                <div class="theme-bar" style="background:#38bdf8; height:80%;"></div>
                <div class="theme-bar" style="background:#10b981; height:60%;"></div>
              </div>
              <div class="theme-desc">Electric blue, sky cyan & clean high-trust corporate metrics.</div>
            </div>

            <!-- Theme 3 -->
            <div class="theme-card" id="theme-blueprint" onclick="setTheme('minimalist-diagram')">
              <div class="theme-card-top">
                <span class="theme-name">📐 Technical Blueprint</span>
                <div class="swatches">
                  <span class="swatch" style="background:#e94560;"></span>
                  <span class="swatch" style="background:#0f3460;"></span>
                  <span class="swatch" style="background:#1a1a2e;"></span>
                  <span class="swatch" style="background:#9ca3af;"></span>
                </div>
              </div>
              <div class="theme-chart-preview">
                <div class="theme-bar" style="background:#e94560; height:70%;"></div>
                <div class="theme-bar" style="background:#0f3460; height:40%;"></div>
                <div class="theme-bar" style="background:#9ca3af; height:90%;"></div>
              </div>
              <div class="theme-desc">Deep space navy with high-contrast scientific coral accents.</div>
            </div>

            <!-- Theme 4 -->
            <div class="theme-card" id="theme-nature" onclick="setTheme('anime-ghibli')">
              <div class="theme-card-top">
                <span class="theme-name">🍃 Nature & Biology</span>
                <div class="swatches">
                  <span class="swatch" style="background:#2d5016;"></span>
                  <span class="swatch" style="background:#ffb347;"></span>
                  <span class="swatch" style="background:#a8e6cf;"></span>
                  <span class="swatch" style="background:#0a0a1a;"></span>
                </div>
              </div>
              <div class="theme-chart-preview">
                <div class="theme-bar" style="background:#ffb347; height:50%;"></div>
                <div class="theme-bar" style="background:#2d5016; height:85%;"></div>
                <div class="theme-bar" style="background:#a8e6cf; height:65%;"></div>
              </div>
              <div class="theme-desc">Forest greens, sunburst gold & organic natural science palettes.</div>
            </div>
          </div>
          <input type="hidden" id="theme" value="flat-motion-graphics" />
        </div>

        <!-- 5. Duration & Voice -->
        <div class="field-group grid-2">
          <div>
            <div class="label-row"><label>5. Target Duration</label></div>
            <div class="segmented-control">
              <button type="button" class="segment-btn active" id="dur-60" onclick="setDuration(60)">60s Explainer</button>
              <button type="button" class="segment-btn" id="dur-30" onclick="setDuration(30)">30s Fast Hook</button>
            </div>
            <input type="hidden" id="duration" value="60" />
          </div>

          <div>
            <div class="label-row"><label>6. Neural Voice</label></div>
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
      
      const badge = document.getElementById('sim-aspect-badge');
      badge.innerText = ratio === '16:9' ? '16:9 • 1080P Widescreen' : '9:16 • 1080P Vertical Reel';
    }

    function setDuration(dur) {
      document.getElementById('duration').value = dur;
      document.getElementById('dur-60').classList.toggle('active', dur === 60);
      document.getElementById('dur-30').classList.toggle('active', dur === 30);
    }

    // Interactive Caption Style Switcher
    function setCaptionStyle(style) {
      document.getElementById('captionStyle').value = style;
      document.getElementById('style-gold').classList.toggle('active', style === 'kinetic-gold');
      document.getElementById('style-cyan').classList.toggle('active', style === 'cyber-cyan');
      document.getElementById('style-white').classList.toggle('active', style === 'clean-white');

      const simBar = document.getElementById('sim-caption-bar');
      simBar.className = 'sim-caption-bar style-' + style;
    }

    // Interactive Theme Switcher
    const THEME_DATA = {
      'flat-motion-graphics': {
        name: '☕ Coffee Warm Roast',
        bg: '#120e0b',
        metricColor: '#f59e0b',
        val: '0°C / 32°F',
        sub: 'Biological Kryptonite: Frost kills coffee trees in hours'
      },
      'clean-professional': {
        name: '🌐 Modern Tech & SaaS',
        bg: '#0a101f',
        metricColor: '#38bdf8',
        val: '$4.2B ARR',
        sub: 'Zero friction cloud distribution at scale'
      },
      'minimalist-diagram': {
        name: '📐 Technical Blueprint',
        bg: '#0c0f1a',
        metricColor: '#e94560',
        val: '2.4 × 10⁸ ops/s',
        sub: 'Quantum coherence limit observed in nanoseconds'
      },
      'anime-ghibli': {
        name: '🍃 Nature & Biology',
        bg: '#08140c',
        metricColor: '#ffb347',
        val: '1,800 Meters',
        sub: 'Highland mountain mist concentrates dense sugars'
      }
    };

    function setTheme(theme) {
      document.getElementById('theme').value = theme;
      document.getElementById('theme-coffee').classList.toggle('active', theme === 'flat-motion-graphics');
      document.getElementById('theme-fintech').classList.toggle('active', theme === 'clean-professional');
      document.getElementById('theme-blueprint').classList.toggle('active', theme === 'minimalist-diagram');
      document.getElementById('theme-nature').classList.toggle('active', theme === 'anime-ghibli');

      const t = THEME_DATA[theme] || THEME_DATA['flat-motion-graphics'];
      document.getElementById('sim-theme-badge').innerText = t.name;
      document.getElementById('sim-screen').style.background = t.bg;
      document.getElementById('sim-metric').style.color = t.metricColor;
      document.getElementById('sim-metric').innerText = t.val;
      document.getElementById('sim-metric-sub').innerText = t.sub;
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
            <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:12px;">
              <span style="font-weight:700; color:#ffffff;">${v.name}</span>
              <span style="font-family:'JetBrains Mono',monospace; font-size:0.72rem; padding:4px 10px; border-radius:999px; background:rgba(56,189,248,0.1); border:1px solid rgba(56,189,248,0.2); color:#38bdf8;">1080P FULL HD • 30 FPS</span>
            </div>
            <video controls src="${v.url}"></video>
            <div style="display:flex; justify-content:flex-end; margin-top:14px;">
              <a href="${v.url}" download style="color:#fbbf24; text-decoration:none; font-size:0.85rem; font-weight:700;">⬇️ Download Master MP4</a>
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
