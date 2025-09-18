#!/usr/bin/env bash
set -e
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python src/main.py --pdf "$1" --outdir "./runs/$(date +%Y%m%d-%H%M%S)"
