# Automata Studio: Interactive NFA → DFA Learning Laboratory

Interactive educational laboratory for **Formal Languages and Automata Theory** at **Széchenyi István University (SZE)**, aligned with **Lecture 5 (Slides 99–132)**:
- **Core Workflow (`NFA → DFA` Conversion, Slide 100)**: Dynamic **4-step / 5-step** detection, multi-symbol string transition splitting, interactive **E-set** & **Transition δ** sub-step explorers with live graph path highlighting, compact math-first UI with `(?)` hover/tap explanations, character-by-character **String Stepper**, and **Research Interaction Telemetry**.
- **Single-Checkbox Optional Extension (`🧩 Extension: DFA Minimization`)**: Unchecked by default so the core `NFA → DFA` workflow stays 100% pure; checking the single box unlocks group-by-group **Moore Partition Refinement (`P0 → Pr → Minimized DFA`)** with live splitting/equivalence arc highlighting and `Minimized DFA` string tracing.
- **Complete Lecture 5 Worked Example Presets (`Slides 101–132`) + Active Practice Default (`Custom Automaton`)**:
  - `Custom Automaton` (Default blank canvas for active student practice)
  - `NFA → DFA: Example 1` (`Slides 101–106`)
  - `NFA → DFA: Example 2` (`Slides 107–112`)
  - `NFA → DFA: Example 3` (`Slides 113–117` — 4 steps, skips string splitting; minimizes `6 → 5` states)
  - `NFA → DFA: Example 4` (`Slides 118–124` — 5 steps; minimizes `9 → 6` states)
  - `NFA → DFA: Example 5` (`Slides 125–132` — 5 steps)

---

## Offline & Online Quick Start Options

### Option 1 — Instant Zero-Install Offline Web App (`index.html`, No Python Needed)
- **100% Offline Local File**: Download the repository ZIP (green **`<> Code`** button → **`Download ZIP`**) or `Automata_Studio_Streamlit_App.zip`, extract it, and double-click **`index.html`** in any modern browser (Chrome, Edge, Firefox, Safari). Zero internet connection, zero external CDNs, and zero installation required (`stable.html` is also included as a classic reference build).
- **Live on GitHub Pages**: [https://lamthai2711-afk.github.io/automata-studio/](https://lamthai2711-afk.github.io/automata-studio/)

---

### Option 2 — Unzip & Double-Click Python Streamlit Desktop App
Run the synchronized Python Streamlit edition (`NFA.py`) just by unzipping and double-clicking:

1. **Download & Extract**: Extract the downloaded `.zip` archive completely to any folder on your computer.
2. **Double-Click to Launch**:
   - **Windows**: Double-click **`Start_Automata_Studio.bat`**.
   - **macOS**: Double-click **`Start_Automata_Studio.command`** (right-click → **Open** on first run).
   - **Linux**: Run `./start_automata_studio.sh` (or `./streamlit_source/start_automata_studio.sh`).
3. **Automatic Local Setup & Offline Execution**:
   - On the **first launch only**, the script creates a local `.venv` folder inside the extracted directory and installs `streamlit`, `graphviz`, and `pandas` (requires Python 3.9+ installed).
   - On **every subsequent launch** (even completely **offline without internet**), setup is skipped and **Automata Studio** opens directly at `http://localhost:8501`.

---

### Option 3 — Manual Developer CLI / Streamlit Community Cloud
```bash
cd streamlit_source
pip install -r requirements.txt
streamlit run NFA.py
```

---

## Repository Structure

```text
automata-studio/
├── index.html                        # Standalone 100% offline-capable Web application (v4.2)
├── stable.html                       # Preserved classic Web build (v4.1)
├── Automata_Studio_Streamlit_App.zip # Complete ready-to-extract offline student bundle
├── Start_Automata_Studio.bat         # Windows double-click Streamlit launcher
├── Start_Automata_Studio.command     # macOS double-click Streamlit launcher
├── HOW_TO_RUN.txt                    # Plain-text quick start instructions
├── README.md                         # Project documentation & setup guide
└── streamlit_source/
    ├── NFA.py                        # Canonical Python Streamlit application source (v4.2)
    ├── Start_Automata_Studio.bat     # Windows double-click launcher
    ├── Start_Automata_Studio.command # macOS double-click launcher
    ├── start_automata_studio.sh      # Linux shell launcher
    ├── requirements.txt              # Python dependencies (streamlit, graphviz, pandas)
    ├── packages.txt                  # Streamlit Cloud system package spec
    ├── HOW_TO_RUN.txt                # Quick start guide copy
    └── .streamlit/
        └── config.toml               # Disables first-run prompt for instant local launch
```
