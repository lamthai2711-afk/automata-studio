#!/usr/bin/env bash
set -e
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"

if [ -f "$SCRIPT_DIR/NFA.py" ]; then
  APP_DIR="$SCRIPT_DIR"
elif [ -f "$SCRIPT_DIR/streamlit_source/NFA.py" ]; then
  APP_DIR="$SCRIPT_DIR/streamlit_source"
else
  echo "[ERROR] Could not locate NFA.py."
  read -r -p "Press Enter to exit..."
  exit 1
fi

cd "$APP_DIR"

if ! command -v python3 >/dev/null 2>&1; then
  echo "========================================================================"
  echo "[SETUP REQUIRED] Python 3.9+ was not found on this machine."
  echo "Install Python 3 from https://www.python.org/downloads/ or open"
  echo "index.html to run the zero-install offline Web version immediately."
  echo "========================================================================"
  read -r -p "Press Enter to exit..."
  exit 1
fi

echo "========================================================================"
echo "  AUTOMATA STUDIO: INTERACTIVE LEARNING LABORATORY (STREAMLIT EDITION)"
echo "========================================================================"

if [ ! -x ".venv/bin/python" ]; then
  echo "[1/2] Creating local virtual environment (.venv)..."
  python3 -m venv .venv
fi

if [ ! -f ".venv/.deps_installed_v2" ]; then
  echo "[2/2] Installing Streamlit, Graphviz, and Pandas (first-time setup)..."
  .venv/bin/python -m pip install --disable-pip-version-check -r requirements.txt
  touch .venv/.deps_installed_v2
fi

echo "Launching Automata Studio at http://localhost:8501 ..."
echo "(Close this window or press Ctrl+C to stop the server.)"
exec .venv/bin/python -m streamlit run NFA.py --browser.gatherUsageStats false --server.headless false
