#!/usr/bin/env bash
set -euo pipefail

# Säkerställ att vi befinner oss i rätt mapp
DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )"
cd "$DIR"

# Aktivera virtuell miljö om den finns, annars varna
if [ -f ".venv/bin/activate" ]; then
    source .venv/bin/activate
else
    echo "Varning: Ingen .venv hittades. Kör 'python3 -m venv .venv && .venv/bin/pip install -r requirements.txt' först."
fi

# Kör Streamlit
echo "Startar webbappen..."
streamlit run app.py
