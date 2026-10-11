#!/usr/bin/env bash
cd "$(dirname "$0")"

# Use local venv or existing venv
if [ -d ".venv" ]; then
    source .venv/bin/activate
elif [ -d "../Open-LLM-VTuber/.venv" ]; then
    source ../Open-LLM-VTuber/.venv/bin/activate
fi

echo "=========================================="
echo " Starting Personal AI VTuber Assistant... "
echo " URL: http://localhost:8080"
echo "=========================================="
python3 app.py
