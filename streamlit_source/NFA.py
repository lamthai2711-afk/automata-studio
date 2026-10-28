import streamlit as st
import graphviz
import pandas as pd
from collections import deque
import time
import json

# ==========================================
# 1. PAGE CONFIGURATION & CUSTOM THEME
# ==========================================
st.set_page_config(
    page_title="Automata Studio: Cognitive Learning Lab",
    page_icon="🧠",
    layout="wide",
    initial_sidebar_state="expanded"
)

DEFAULT_PRESET_NAME = "Contains Empty Transition (ε)"

# Initialize persistent session states for Telemetry & Controls
if "user_actions_log" not in st.session_state:
    st.session_state.user_actions_log = []
if "session_start_time" not in st.session_state:
    st.session_state.session_start_time = time.time()
if "sim_step_index" not in st.session_state:
    st.session_state.sim_step_index = 0
if "scenario_choice_key" not in st.session_state:
    st.session_state.scenario_choice_key = DEFAULT_PRESET_NAME
if "reset_counter" not in st.session_state:
    st.session_state.reset_counter = 0

def log_action(action_type, details=""):
    """Tracks learner behavior for educational research telemetry."""
    elapsed = round(time.time() - st.session_state.session_start_time, 1)
    st.session_state.user_actions_log.append({
        "timestamp_sec": elapsed,
        "action": action_type,
        "details": details
    })

def reset_to_default():
    """Resets all automaton parameters, transitions, and stepper state back to default."""
    st.session_state.scenario_choice_key = DEFAULT_PRESET_NAME
    st.session_state.sim_step_index = 0
    st.session_state.reset_counter += 1
    for key in list(st.session_state.keys()):
        if key.startswith("trans_") or key in ("states_input_key", "alpha_input_key", "stepper_str_input"):
            del st.session_state[key]
    log_action("reset_to_default", DEFAULT_PRESET_NAME)

# ==========================================
# 2. SCENARIOS LIBRARY
# ==========================================
PREBUILT_SCENARIOS = {
    "Contains Empty Transition (ε)": {
        "states": "A, B, C",
        "alphabet": "0, 1, e",
        "start": "A",
        "accept": ["C"],
        "transitions": {
            "A": {"0": "A", "e": "B"},
            "B": {"1": "B, C"},
            "C": {}
        },
        "description": "Standard NFA featuring epsilon reachability and branch expansion."
    },
    "Ends with '01'": {
        "states": "q0, q1, q2",
        "alphabet": "0, 1",
        "start": "q0",
        "accept": ["q2"],
        "transitions": {
            "q0": {"0": "q0, q1", "1": "q0"},
            "q1": {"1": "q2"},
            "q2": {}
        },
        "description": "Pattern matching automaton demonstrating non-deterministic path forks."
    },
    "Even number of 1s": {
        "states": "Even, Odd",
        "alphabet": "0, 1",
        "start": "Even",
        "accept": ["Even"],
        "transitions": {
            "Even": {"0": "Even", "1": "Odd"},
            "Odd": {"0": "Odd", "1": "Even"}
        },
        "description": "Parity checker automaton exhibiting symmetric cyclic equivalence."
    },
    "Post-Survey Context 1 (A, B, C)": {
        "states": "A, B, C",
        "alphabet": "0, 1, e",
        "start": "A",
        "accept": ["C"],
        "transitions": {
            "A": {"0": "A", "e": "B"},
            "B": {"1": "C"},
            "C": {"0": "C"}
        },
        "description": "Post-Survey Part B (Q5–Q8): Start A, Accept C, δ(A,0)={A}, δ(A,ε)={B}, δ(B,1)={C}, δ(C,0)={C}."
    },
    "Post-Survey Context 2 (1, 2, 3)": {
        "states": "1, 2, 3",
        "alphabet": "a, b, e",
        "start": "1",
        "accept": ["3"],
        "transitions": {
            "1": {"a": "1", "e": "2"},
            "2": {"b": "2, 3"},
            "3": {"a": "3"}
        },
        "description": "Post-Survey Part D (Q11–Q13): Start 1, Accept 3, δ(1,a)={1}, δ(1,ε)={2}, δ(2,b)={2,3}, δ(3,a)={3}."
    }
}

# ==========================================
# 3. FORMAL ALGORITHM ENGINES
# ==========================================
def get_empty_closure(states, transitions):
    """Computes formal E-set (epsilon-closure) via iterative depth reachability."""
    closure = set(states)
    stack = list(states)
    while stack:
        curr = stack.pop()
        if curr in transitions and "e" in transitions[curr]:
            for nxt in transitions[curr]["e"]:
                if nxt not in closure:
                    closure.add(nxt)
                    stack.append(nxt)
    return frozenset(closure)

def move(states, symbol, transitions):
    """Evaluates transition destination set across given alphabet symbol."""
    reachable = set()
    for s in states:
        if s in transitions and symbol in transitions[s]:
            for nxt in transitions[s][symbol]:
                reachable.add(nxt)
    return frozenset(reachable)

def format_state_name(state_set):
    """Renders consistent notation for sets of states and trap sinks."""
    if not state_set or state_set == frozenset({"Trap"}):
        return "Trap"
    return "{" + ", ".join(sorted(list(state_set))) + "}"

def nfa_to_dfa_with_steps(nfa_def):
    """Executes Subset Construction with complete pedagogical tracing logs."""
    alphabet = [s for s in nfa_def["alphabet"] if s != "e"]
    nfa_trans = nfa_def["transitions"]
    start_state = nfa_def["start_state"]
    nfa_accept = set(nfa_def["accept_states"])
    
    step_data = {
        "e_sets": {},
        "initial_state": None,
        "transitions_log": [],
        "final_states": []
    }
    if not start_state:
        return None, step_data

    for state in nfa_def["states"]:
        step_data["e_sets"][state] = format_state_name(get_empty_closure([state], nfa_trans))

    initial_closure = get_empty_closure([start_state], nfa_trans)
    step_data["initial_state"] = format_state_name(initial_closure)
    
    dfa_transitions = {}
    dfa_accept = set()
    dfa_states = []
    
    unmarked = deque([initial_closure])
    dfa_states.append(initial_closure)
    
    while unmarked:
        curr = unmarked.popleft()
        state_label = format_state_name(curr)
        dfa_transitions[state_label] = {}
        
        if any(s in nfa_accept for s in curr):
            dfa_accept.add(state_label)
            if state_label not in step_data["final_states"]:
                step_data["final_states"].append(state_label)
                
        for sym in alphabet:
            m = move(curr, sym, nfa_trans)
            c = get_empty_closure(m, nfa_trans)
            
            if not c:
                c = frozenset({"Trap"})
            target_label = format_state_name(c)
            dfa_transitions[state_label][sym] = target_label
            
            step_data["transitions_log"].append({
                "Current State S": state_label,
                "Symbol σ": sym,
                "Move(S, σ)": format_state_name(m) if m else "∅",
                "E-set(Move) -> Target": target_label
            })
            
            if c not in dfa_states and c != frozenset({"Trap"}):
                dfa_states.append(c)
                unmarked.append(c)
                
    needs_trap = any("Trap" in dfa_transitions[st].values() for st in dfa_transitions)
    if needs_trap and "Trap" not in dfa_transitions:
        dfa_transitions["Trap"] = {sym: "Trap" for sym in alphabet}
        for sym in alphabet:
            step_data["transitions_log"].append({
                "Current State S": "Trap",
                "Symbol σ": sym,
                "Move(S, σ)": "∅",
                "E-set(Move) -> Target": "Trap"
            })
            
    final_dfa = {
        "states": [format_state_name(s) for s in dfa_states] + (["Trap"] if needs_trap else []),
        "alphabet": alphabet,
        "start_state": format_state_name(initial_closure),
        "accept_states": list(dfa_accept),
        "transitions": dfa_transitions
    }
    return final_dfa, step_data

def minimize_dfa(dfa_def):
    """Minimizes DFA using Moore's Equivalence Partitioning algorithm."""
    states = dfa_def["states"]
    if not states:
        return None, None
        
    accept_states = set(dfa_def["accept_states"])
    non_accept_states = set(states) - accept_states
    alphabet = dfa_def["alphabet"]
    transitions = dfa_def["transitions"]
    
    partitions = []
    if non_accept_states:
        partitions.append(non_accept_states)
    if accept_states:
        partitions.append(accept_states)
        
    while True:
        new_partitions = []
        for part in partitions:
            signatures = {}
            for state in part:
                sig = []
                for sym in alphabet:
                    target = transitions.get(state, {}).get(sym, "Trap")
                    target_idx = -1
                    for idx, p in enumerate(partitions):
                        if target in p:
                            target_idx = idx
                            break
                    sig.append(target_idx)
                sig_tuple = tuple(sig)
                if sig_tuple not in signatures:
                    signatures[sig_tuple] = set()
                signatures[sig_tuple].add(state)
            
            for sig_key in sorted(signatures.keys(), key=lambda x: str(x)):
                new_partitions.append(signatures[sig_key])
                
        if len(new_partitions) == len(partitions):
            break
        partitions = new_partitions

    start_state = dfa_def["start_state"]
    def partition_key(p):
        return "" if start_state in p else min(list(p))
    partitions.sort(key=partition_key)

    state_map = {}
    for idx, p in enumerate(partitions):
        label = f"M{idx}"
        for s in p:
            state_map[s] = label
            
    min_states = sorted(list(set(state_map.values())), key=lambda x: int(x[1:]))
    min_start = state_map.get(dfa_def["start_state"])
    min_accept = sorted(list(set(state_map[s] for s in accept_states if s in state_map)), key=lambda x: int(x[1:]))
    
    min_trans = {}
    for s in states:
        mapped_src = state_map[s]
        if mapped_src not in min_trans:
            min_trans[mapped_src] = {}
        for sym in alphabet:
            target = transitions.get(s, {}).get(sym)
            if target and target in state_map:
                min_trans[mapped_src][sym] = state_map[target]
                
    min_dfa = {
        "states": min_states,
        "alphabet": alphabet,
        "start_state": min_start,
        "accept_states": min_accept,
        "transitions": min_trans
    }
    
    mapping_df = pd.DataFrame([
        {"Minimized Group": f"M{i}", "Original Component States": ", ".join(sorted(list(p)))}
        for i, p in enumerate(partitions)
    ])
    return min_dfa, mapping_df

def simulate_string(dfa_def, input_string):
    """Simulates character-by-character trace through a deterministic automaton."""
    curr = dfa_def["start_state"]
    path = [(curr, "Start")]
    if not curr:
        return False, path, "No initial start state defined."
        
    for char in input_string:
        if char not in dfa_def["alphabet"]:
            return False, path, f"Invalid symbol '{char}' not in alphabet."
        next_st = dfa_def["transitions"].get(curr, {}).get(char, "Trap")
        path.append((next_st, char))
        curr = next_st
        
    is_accepted = curr in dfa_def["accept_states"]
    return is_accepted, path, "Success"

# ==========================================
# 4. VISUALIZATION ENGINE (GRAPHVIZ)
# ==========================================
def draw_automaton(automaton_def, name="Automaton", highlighted_states=None, active_edge=None):
    """Generates styled topological diagrams with state signaling and cues."""
    dot = graphviz.Digraph(name, graph_attr={
        'rankdir': 'LR',
        'bgcolor': 'transparent',
        'margin': '0.1'
    })
    if not automaton_def.get('start_state'):
        return dot

    dot.node('hidden_start', label='', shape='none', width='0', height='0')
    dot.edge('hidden_start', automaton_def['start_state'], color='#2563eb', penwidth='2')
    
    highlighted_states = highlighted_states or []
    
    for state in automaton_def['states']:
        shape = 'doublecircle' if state in automaton_def['accept_states'] else 'circle'
        fontcolor = '#0f172a'
        
        if state in highlighted_states:
            fillcolor = '#86efac'
            penwidth = '3.5'
            color = '#15803d'
        elif state == automaton_def['start_state']:
            fillcolor = '#dbeafe'
            penwidth = '2.0'
            color = '#1d4ed8'
        elif state == "Trap":
            fillcolor = '#fee2e2'
            penwidth = '1.5'
            color = '#b91c1c'
        else:
            fillcolor = '#ffffff'
            penwidth = '1.2'
            color = '#64748b'
            
        dot.node(state, state, shape=shape, style='filled', fillcolor=fillcolor,
                 color=color, penwidth=penwidth, fontcolor=fontcolor, fontname='Arial')
        
    edge_groups = {}
    for src, transitions in automaton_def['transitions'].items():
        for symbol, dests in transitions.items():
            target_list = dests if isinstance(dests, list) else [dests]
            for dest in target_list:
                edge_groups.setdefault((src, dest), []).append(symbol)

    for (src, dest), symbols in edge_groups.items():
        is_hit = active_edge and (src == active_edge[0] and dest == active_edge[1] and active_edge[2] in symbols)
        edge_color = '#dc2626' if is_hit else '#64748b'
        edge_width = '3.0' if is_hit else '1.0'
        label_str = ", ".join("ε" if s == "e" else s for s in symbols)
        dot.edge(src, dest, label=f" {label_str} ", fontcolor='#1e293b',
                 color=edge_color, penwidth=edge_width)
    return dot

# ==========================================
# 5. USER INTERFACE ARCHITECTURE
# ==========================================
def main():
    st.title("🧠 Automata Studio: Interactive Learning Laboratory")
    st.markdown(
        """
        Explore state transformation algorithms through **Dynamic Visual Pipelines**, **Step-by-Step Mathematical Decomposition**, 
        and **Interactive String Execution Tracing**.
        """
    )

    with st.sidebar:
        st.header("⚙️ Experiment Controls")
        participant_tag = st.text_input("Participant ID (Optional)", placeholder="e.g., SZE-XXXXXX")
        
        if st.button("🔄 Reset to Default", use_container_width=True, type="secondary"):
            reset_to_default()
            st.rerun()

        st.divider()
        st.header("📚 Scenarios & Presets")
        scenario_options = list(PREBUILT_SCENARIOS.keys()) + ["Custom Automaton"]
        scenario_choice = st.selectbox(
            "Select Scenario Preset:",
            scenario_options,
            key="scenario_choice_key"
        )
        
        if scenario_choice != "Custom Automaton":
            preset = PREBUILT_SCENARIOS[scenario_choice]
            def_states = preset["states"]
            def_alpha = preset["alphabet"]
            def_start = preset["start"]
            def_acc = preset["accept"]
            st.info(f"ℹ️ **Scenario Note:** {preset['description']}")
        else:
            preset = None
            def_states = "q0, q1, q2"
            def_alpha = "0, 1, e"
            def_start = "q0"
            def_acc = ["q2"]

        rc = st.session_state.reset_counter
        st.subheader("NFA Formal Specification")
        raw_states = st.text_input("States (comma-separated)", value=def_states, key=f"states_in_{scenario_choice}_{rc}")
        states_list = [s.strip() for s in raw_states.split(",") if s.strip()]
        
        raw_alphabet = st.text_input("Alphabet (comma-separated)", value=def_alpha, key=f"alpha_in_{scenario_choice}_{rc}")
        alphabet_list = [a.strip() for a in raw_alphabet.split(",") if a.strip()]
        
        start_state = st.selectbox(
            "Start State (q0)",
            options=states_list,
            index=states_list.index(def_start) if def_start in states_list else 0,
            key=f"start_sel_{scenario_choice}_{rc}"
        ) if states_list else None
        
        accept_states = st.multiselect(
            "Accept States (F)",
            options=states_list,
            default=[a for a in def_acc if a in states_list],
            key=f"acc_sel_{scenario_choice}_{rc}"
        )
        
        st.markdown("#### Transition Table Builder")
        nfa_transitions = {s: {} for s in states_list}
        
        for state in states_list:
            with st.expander(f"Transitions from state: '{state}'", expanded=(scenario_choice != "Custom Automaton")):
                for sym in alphabet_list:
                    default_targets = []
                    if preset and state in preset["transitions"]:
                        if sym in preset["transitions"][state]:
                            raw_t = preset["transitions"][state][sym]
                            if isinstance(raw_t, str):
                                default_targets = [t.strip() for t in raw_t.split(",") if t.strip() in states_list]
                            elif isinstance(raw_t, list):
                                default_targets = [t for t in raw_t if t in states_list]
                                
                    selected = st.multiselect(
                        f"Read '{sym}' ➔ Go to:",
                        options=states_list,
                        default=default_targets,
                        key=f"trans_{scenario_choice}_{rc}_{state}_{sym}"
                    )
                    if selected:
                        nfa_transitions[state][sym] = selected

    if not states_list or not start_state:
        st.warning("⚠️ Please provide a valid automaton configuration in the sidebar to begin.")
        return

    nfa_def = {
        "states": states_list,
        "alphabet": alphabet_list,
        "start_state": start_state,
        "accept_states": accept_states,
        "transitions": nfa_transitions
    }

    dfa_def, step_data = nfa_to_dfa_with_steps(nfa_def)
    min_dfa_def, min_mapping = minimize_dfa(dfa_def)

    tab_pipeline, tab_stepper, tab_telemetry = st.tabs([
        "📊 1. Visual Pipeline",
        "⏯️ 2. Step-by-Step String Stepper",
        "📋 3. Research Telemetry & Activity Log"
    ])

    with tab_pipeline:
        st.markdown("### Comparative Automata Transformation Pipeline")
        st.caption("Visualizing the topological progression from NFA to Deterministic Machine to Minimal Canonical Form.")
        
        c1, c2, c3 = st.columns(3)
        with c1:
            st.markdown("#### 1. Original NFA")
            st.graphviz_chart(draw_automaton(nfa_def, "Original_NFA"))
            with st.expander("Show E-Closure (E-sets)", expanded=True):
                st.dataframe(pd.DataFrame(list(step_data["e_sets"].items()), columns=["NFA State", "E-set (Epsilon Closure)"]),
                             hide_index=True, use_container_width=True)
                             
        with c2:
            st.markdown("#### 2. Converted DFA (Subset Construction)")
            st.graphviz_chart(draw_automaton(dfa_def, "Converted_DFA"))
            with st.expander("Subset Construction Transition Table", expanded=True):
                st.dataframe(pd.DataFrame(step_data["transitions_log"]), hide_index=True, use_container_width=True)
                
        with c3:
            st.markdown("#### 3. Minimized DFA (Equivalence Partitions)")
            if min_dfa_def:
                st.graphviz_chart(draw_automaton(min_dfa_def, "Minimized_DFA"))
                with st.expander("State Collapsing Equivalence Map", expanded=True):
                    st.dataframe(min_mapping, hide_index=True, use_container_width=True)

    with tab_stepper:
        st.markdown("### Interactive Step-by-Step String Stepper")
        st.caption("Avoid information overload by navigating character transitions one click at a time.")
        
        sim_cols = st.columns([2, 1, 1])
        with sim_cols[0]:
            target_str = st.text_input("Input String to Trace:", value="0101", key="stepper_str_input")
        with sim_cols[1]:
            machine_target = st.radio("Select Target Automaton:", ["Minimized DFA", "Standard DFA"], horizontal=True)
            chosen_machine = min_dfa_def if machine_target == "Minimized DFA" and min_dfa_def else dfa_def

        is_acc, path, msg = simulate_string(chosen_machine, target_str)
        
        if msg != "Success":
            st.error(f"⚠️ Simulation Alert: {msg}")
        else:
            max_steps = len(path) - 1
            st.session_state.sim_step_index = min(st.session_state.sim_step_index, max_steps)
            
            ctrl_cols = st.columns([1, 1, 1, 3])
            with ctrl_cols[0]:
                if st.button("⏮️ Reset Stepper", use_container_width=True):
                    st.session_state.sim_step_index = 0
                    log_action("stepper_reset")
            with ctrl_cols[1]:
                if st.button("◀️ Prev Step", use_container_width=True):
                    st.session_state.sim_step_index = max(0, st.session_state.sim_step_index - 1)
                    log_action("stepper_prev", f"Step_{st.session_state.sim_step_index}")
            with ctrl_cols[2]:
                if st.button("Next Step ▶️", use_container_width=True):
                    st.session_state.sim_step_index = min(max_steps, st.session_state.sim_step_index + 1)
                    log_action("stepper_next", f"Step_{st.session_state.sim_step_index}")

            current_idx = min(st.session_state.sim_step_index, max_steps)
            current_state = path[current_idx][0]
            consumed_symbol = path[current_idx][1]

            st.markdown(f"**Step {current_idx} of {max_steps}** | Active State: `{current_state}`")
            
            str_vis = []
            for i, ch in enumerate(target_str):
                if i < current_idx:
                    str_vis.append(f"<span style='color: #16a34a; font-weight: bold;'>{ch}</span>")
                elif i == current_idx:
                    str_vis.append(f"<span style='background-color: #fde047; padding: 2px 6px; border-radius: 4px; font-weight: bold;'>{ch}</span>")
                else:
                    str_vis.append(f"<span style='color: #94a3b8;'>{ch}</span>")
            st.markdown(f"String Progress: `{' '.join(str_vis)}`", unsafe_allow_html=True)
            
            active_edge_tuple = None
            if current_idx > 0:
                prev_state = path[current_idx - 1][0]
                active_edge_tuple = (prev_state, current_state, consumed_symbol)

            st.graphviz_chart(draw_automaton(chosen_machine, "Stepper_Graph",
                                             highlighted_states=[current_state],
                                             active_edge=active_edge_tuple))

            if current_idx == max_steps:
                if is_acc:
                    st.success(f"🎉 Simulation Complete: The string '{target_str}' is **ACCEPTED** by the automaton.")
                else:
                    st.error(f"🛑 Simulation Complete: The string '{target_str}' is **REJECTED** (Ended in non-accept state '{current_state}').")

    with tab_telemetry:
        st.markdown("### 📋 Educational Interaction Telemetry")
        total_actions = len(st.session_state.user_actions_log)
        elapsed_min = round((time.time() - st.session_state.session_start_time) / 60, 1)

        m1, m2 = st.columns(2)
        m1.metric("Active Session Time", f"{elapsed_min} mins")
        m2.metric("Total User Actions", f"{total_actions} events")

        telemetry_payload = {
            "participant_id": participant_tag or "ANONYMOUS",
            "elapsed_seconds": round(time.time() - st.session_state.session_start_time, 1),
            "actions_summary_count": total_actions,
            "recent_actions": st.session_state.user_actions_log[-10:]
        }
        st.code(json.dumps(telemetry_payload, indent=2), language="json")

if __name__ == "__main__":
    main()
