#!/usr/bin/env bash
set -euo pipefail
echo "🐍  Creating venv …"
python3 -m venv venv
source venv/bin/activate
echo "📦  Installing packages …"
pip install -U pip wheel
pip install -r requirements.txt
echo "✅  Done.  Run: source venv/bin/activate"