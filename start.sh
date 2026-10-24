#!/usr/bin/env bash
# start.sh - 1-Click Launch Script for Agent Video Studio

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

echo "=================================================="
echo "🎬 Starting Agent Video Studio..."
echo "=================================================="

# 1. Install python dependencies if not already present
if ! python3 -c "import edge_tts, faster_whisper" 2>/dev/null; then
    echo "📦 Installing Python dependencies (edge-tts, faster-whisper, yt-dlp)..."
    pip3 install -r requirements.txt
fi

# 2. Check Remotion dependencies
if [ ! -d "remotion-composer/node_modules" ]; then
    echo "🎨 Installing Remotion motion graphics dependencies..."
    cd remotion-composer && npm install && cd ..
fi

# 3. Launch Studio UI
echo "✨ Launching Studio UI on http://localhost:5500..."
python3 studio.py
