#!/usr/bin/env bash
# One-command start for macOS / Linux.
set -e
cd "$(dirname "$0")/backend"
[ -d venv ] || python3 -m venv venv
source venv/bin/activate
pip install -q -r requirements.txt
echo "Open http://localhost:5000"
python app.py
