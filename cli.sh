#!/usr/bin/env bash
# cli.sh - 1-Line CLI Video Production for Agent Video Studio

set -e
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# Resolve python interpreter with modern dependencies
if [ -f "$SCRIPT_DIR/.venv/bin/python3" ]; then
    PYTHON_CMD="$SCRIPT_DIR/.venv/bin/python3"
elif [ -f "$SCRIPT_DIR/../OpenMontage/.venv/bin/python3" ]; then
    PYTHON_CMD="$SCRIPT_DIR/../OpenMontage/.venv/bin/python3"
else
    PYTHON_CMD="python3"
fi

"$PYTHON_CMD" studio.py --render "$@"

