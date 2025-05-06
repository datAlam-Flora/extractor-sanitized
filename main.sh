#!/bin/bash

# Set UTF-8 encoding for Python output
export PYTHONIOENCODING=utf-8
export PYTHONLEGACYWINDOWSSTDIO=utf-8

# For Windows terminals running Bash
if [[ "$OSTYPE" == "msys" ]] || [[ "$OSTYPE" == "win32" ]]; then
  # Change Windows console code page to UTF-8
  chcp.com 65001 > /dev/null 2>&1 || true
fi

# Activate the virtual environment (path for Windows)
source ./.venv/Scripts/activate

# Run the Python script with explicit encoding
python -X utf8 main.py