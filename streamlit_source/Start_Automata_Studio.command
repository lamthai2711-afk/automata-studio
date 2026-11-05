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
  echo "[SETUP REQUIRED] Python 3.9+ was not found on this computer."
  echo "Install Python 3 from https://www.python.org/downloads/ or open"
  echo "index.html to run the zero-install offline Web version immediately."
  echo "========================================================================"
  read -r -p "Press Enter to exit..."
  exit 1
fi

echo "========================================================================"
echo "  AUTOMATA STUDIO: INTERACTIVE LEARNING LABORATORY (STREAMLIT EDITION)"
echo "========================================================================"

USE_USER_PIP=0
if [ ! -x ".venv/bin/python" ] || [ ! -x ".venv/bin/pip" ]; then
  rm -rf .venv
  echo "[1/2] Creating local virtual environment (.venv)..."
  if ! python3 -m venv .venv >/dev/null 2>&1; then
    rm -rf .venv
    echo "[INFO] python3-venv is not installed; falling back to user Python environment..."
    USE_USER_PIP=1
  fi
fi

if [ "$USE_USER_PIP" -eq 0 ]; then
  if [ ! -f ".venv/.deps_installed_v3" ]; then
    echo "[2/2] Installing Streamlit, Graphviz, and Pandas (first-time setup)..."
    .venv/bin/python -m pip install --disable-pip-version-check -r requirements.txt
    touch .venv/.deps_installed_v3
  fi
  PY_EXEC=".venv/bin/python"
else
  if ! python3 -c "import streamlit, graphviz, pandas" >/dev/null 2>&1; then
    echo "[2/2] Installing Streamlit, Graphviz, and Pandas into user site-packages..."
    python3 -m pip install --user --disable-pip-version-check -r requirements.txt || \
    python3 -m pip install --user --break-system-packages --disable-pip-version-check -r requirements.txt
  fi
  PY_EXEC="python3"
fi

echo "Launching Automata Studio at http://localhost:8501 ..."
echo "(Close this window or press Ctrl+C to stop the server.)"
exec "$PY_EXEC" -m streamlit run NFA.py --browser.gatherUsageStats false --server.headless false
