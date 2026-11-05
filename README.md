# Automata Studio: Interactive NFA → DFA Learning Laboratory

Interactive educational laboratory for **Formal Languages and Automata Theory** (`NFA → DFA Subset Construction`, `Dynamic Slide 100 Step Detection`, `Multi-Symbol String Transition Splitting`, `E-Set Union Derivations`, `Optional Moore Minimization`, `Step-by-Step String Stepper`, and `Research Interaction Telemetry`) at **Széchenyi István University (SZE)**.

Both the **Web Edition (`index.html`)** and the **Python Streamlit Edition (`streamlit_source/NFA.py`)** are 100% synchronized:
- **Active Self-Practice Default (`Custom Automaton`)**: Opens on a clean custom canvas so students construct their own NFAs (including single-symbol, `ε` via `'e'`, and multi-symbol string edges like `ab`, `aa`, `ba`, `bb` with strict formal alphabet validation).
- **Dynamic Conversion Step Detection (Lecture 5, Slide 100)**: Automatically detects **5 conversion steps** when multi-symbol string transitions exist (introducing `q_{max+1}` intermediate states in Step 1) or **4 conversion steps** when only single-symbol/`ε` edges exist (skipping Step 1 automatically).
- **Complete Lecture 5 Worked Example Presets (Slides 101–132)**:
  - `NFA → DFA: Example 1` (`Slides 101–106`)
  - `NFA → DFA: Example 2` (`Slides 107–112`)
  - `NFA → DFA: Example 3` (`Slides 113–117`)
  - `NFA → DFA: Example 4` (`Slides 118–124`)
  - `NFA → DFA: Example 5` (`Slides 125–132`)

---

## Quick Start Options

### Option 1 — Unzip & Double-Click Streamlit Desktop App (No Terminal Needed)
You can run the full Python Streamlit application as a self-bootstrapping desktop package just by unzipping and double-clicking:

1. **Download & Extract**:
   - On GitHub, click the green **`<> Code`** button above and select **`Download ZIP`** (or download the standalone `Automata_Studio_Streamlit_App.zip` bundle), then **extract (unzip)** the archive to any folder on your computer.
2. **Double-Click to Launch**:
   - **Windows**: Double-click **`Start_Automata_Studio.bat`** (located in the extracted root folder or inside `streamlit_source/`).
   - **macOS**: Double-click **`Start_Automata_Studio.command`** (if macOS Gatekeeper prompts on first launch, right-click the file and choose **Open**).
   - **Linux**: Run `./streamlit_source/start_automata_studio.sh` (or double-click and choose *Run in Terminal*).
3. **What Happens Automatically**:
   - On the **first launch only**, the launcher creates an isolated `.venv` folder inside the extracted directory and installs `streamlit`, `graphviz`, and `pandas` automatically (requires Python 3.9+ installed on the machine; no system-wide Graphviz binary installation is needed because Streamlit renders the generated Graphviz DOT graphs directly in the browser).
   - On **every subsequent double-click**, setup is skipped and **Automata Studio** opens immediately in your default browser at `http://localhost:8501`.

---

### Option 2 — Instant Zero-Install Web Version (Online or 100% Offline)
No Python or package installation required:
- **Live on GitHub Pages**: [https://lamthai2711-afk.github.io/automata-studio/](https://lamthai2711-afk.github.io/automata-studio/)
- **100% Offline Local File**: Double-click **`index.html`** in any modern browser (Chrome, Edge, Firefox, Safari). All styles, layout algorithms, and SVG graph renderers are self-contained inline with zero external CDN dependencies.

---

### Option 3 — Manual Developer CLI / Streamlit Community Cloud
If you prefer running Streamlit manually from a terminal:
```bash
cd streamlit_source
pip install -r requirements.txt
streamlit run NFA.py
```
To deploy online on [Streamlit Community Cloud](https://share.streamlit.io/), point the app to repository `lamthai2711-afk/automata-studio`, branch `main`, and main file path `streamlit_source/NFA.py`.

---

## Repository Structure

```text
automata-studio/
├── index.html                        # Standalone 100% offline-capable Web application (GitHub Pages)
├── Start_Automata_Studio.bat         # Windows double-click Streamlit launcher
├── Start_Automata_Studio.command     # macOS double-click Streamlit launcher
├── HOW_TO_RUN.txt                    # Plain-text quick start instructions
├── README.md                         # Project documentation & setup guide
└── streamlit_source/
    ├── NFA.py                        # Canonical Python Streamlit application source
    ├── Start_Automata_Studio.bat     # Windows double-click launcher (inside folder)
    ├── Start_Automata_Studio.command # macOS double-click launcher (inside folder)
    ├── start_automata_studio.sh      # Linux shell launcher
    ├── requirements.txt              # Python dependencies (streamlit, graphviz, pandas)
    ├── packages.txt                  # Streamlit Cloud system package spec
    ├── HOW_TO_RUN.txt                # Quick start guide copy
    └── .streamlit/
        └── config.toml               # Disables first-run onboarding prompt for one-click launch
```
