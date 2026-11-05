import re
import time
import json
from collections import deque
import streamlit as st
import graphviz
import pandas as pd

# ==========================================
# 1. PAGE CONFIGURATION & SESSION STATE
# ==========================================
st.set_page_config(
    page_title="Automata Studio: Cognitive Learning Lab",
    page_icon="🧠",
    layout="wide",
    initial_sidebar_state="expanded"
)

DEFAULT_PRESET_NAME = "Custom Automaton"

# ==========================================
# 2. LECTURE 5 SCENARIOS LIBRARY (SLIDES 99-132)
# ==========================================
PREBUILT_SCENARIOS = {
    "NFA → DFA: Example 1": {
        "states": "q1, q2, q3, q4",
        "alphabet": "a, b, e",
        "start": "q1",
        "accept": ["q3"],
        "transitions": {
            "q1": {"b": ["q2"]},
            "q2": {"a": ["q3"]},
            "q3": {"e": ["q2", "q4"]},
            "q4": {"a": ["q2"]}
        },
        "string_transitions": [
            {"from": "q4", "label": "ab", "to": "q1"}
        ],
        "sample_str": "baabba",
        "description": "NFA → DFA: Example 1 (Slides 101–106)"
    },
    "NFA → DFA: Example 2": {
        "states": "q1, q2, q3",
        "alphabet": "a, b, e",
        "start": "q1",
        "accept": ["q3"],
        "transitions": {
            "q1": {"b": ["q2"]},
            "q2": {"b": ["q3"]},
            "q3": {"e": ["q1"]}
        },
        "string_transitions": [
            {"from": "q1", "label": "aa", "to": "q2"},
            {"from": "q1", "label": "ba", "to": "q2"}
        ],
        "sample_str": "bab",
        "description": "NFA → DFA: Example 2 (Slides 107–112)"
    },
    "NFA → DFA: Example 3": {
        "states": "q1, q2, q3, q4, q5, q6, q7, q8",
        "alphabet": "a, b, e",
        "start": "q1",
        "accept": ["q8"],
        "transitions": {
            "q1": {"a": ["q2"]},
            "q2": {"e": ["q3", "q4"]},
            "q3": {"a": ["q5"]},
            "q4": {"b": ["q6"]},
            "q5": {"e": ["q7"]},
            "q6": {"e": ["q7"]},
            "q7": {"b": ["q8"]},
            "q8": {}
        },
        "string_transitions": [],
        "sample_str": "aab",
        "description": "NFA → DFA: Example 3 (Slides 113–117)"
    },
    "NFA → DFA: Example 4": {
        "states": "q1, q2, q3, q4, q5, q6",
        "alphabet": "a, b, e",
        "start": "q1",
        "accept": ["q6"],
        "transitions": {
            "q1": {"b": ["q2"]},
            "q2": {"b": ["q3"]},
            "q3": {"b": ["q6"]},
            "q4": {"e": ["q3"]},
            "q5": {"a": ["q1", "q4"]},
            "q6": {"e": ["q4", "q5"]}
        },
        "string_transitions": [
            {"from": "q1", "label": "ab", "to": "q4"}
        ],
        "sample_str": "abb",
        "description": "NFA → DFA: Example 4 (Slides 118–124)"
    },
    "NFA → DFA: Example 5": {
        "states": "q1, q2, q3, q4, q5, q6, q7",
        "alphabet": "a, b, e",
        "start": "q1",
        "accept": ["q7"],
        "transitions": {
            "q1": {"a": ["q2"], "e": ["q4"]},
            "q2": {"b": ["q3"]},
            "q3": {"a": ["q4"]},
            "q4": {"e": ["q5", "q7"]},
            "q5": {"a": ["q3"], "e": ["q6"]},
            "q6": {"b": ["q3"], "a": ["q7"]},
            "q7": {}
        },
        "string_transitions": [
            {"from": "q7", "label": "bb", "to": "q1"}
        ],
        "sample_str": "bba",
        "description": "NFA → DFA: Example 5 (Slides 125–132)"
    }
}

# Initialize persistent session states for Telemetry & Controls
if "user_actions_log" not in st.session_state:
    st.session_state.user_actions_log = []
if "session_start_time" not in st.session_state:
    st.session_state.session_start_time = time.time()
if "sim_step_index" not in st.session_state:
    st.session_state.sim_step_index = 0
if "conv_stage_index" not in st.session_state:
    st.session_state.conv_stage_index = 0
if "scenario_choice_key" not in st.session_state:
    st.session_state.scenario_choice_key = DEFAULT_PRESET_NAME
if "last_loaded_scenario" not in st.session_state:
    st.session_state.last_loaded_scenario = DEFAULT_PRESET_NAME
if "stepper_str_input" not in st.session_state:
    st.session_state.stepper_str_input = ""
if "string_transitions_list" not in st.session_state:
    st.session_state.string_transitions_list = []
if "show_optional_min_dfa" not in st.session_state:
    st.session_state.show_optional_min_dfa = False
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


def clear_automaton_widget_keys():
    """Clears dynamic transition and specification widget keys on reset."""
    for key in list(st.session_state.keys()):
        if key.startswith(("trans_", "states_in_", "alpha_in_", "start_sel_", "acc_sel_", "str_from_", "str_lbl_", "str_to_")):
            del st.session_state[key]


def reset_to_default():
    """Resets all automaton parameters, transitions, and steppers back to Custom Automaton (blank canvas)."""
    st.session_state.scenario_choice_key = DEFAULT_PRESET_NAME
    st.session_state.last_loaded_scenario = DEFAULT_PRESET_NAME
    st.session_state.sim_step_index = 0
    st.session_state.conv_stage_index = 0
    st.session_state.stepper_str_input = ""
    st.session_state.string_transitions_list = []
    st.session_state.stepper_target_radio = "Converted DFA"
    st.session_state.reset_counter += 1
    clear_automaton_widget_keys()
    log_action("reset_to_default", DEFAULT_PRESET_NAME)


def reset_current_preset():
    """Restores the currently selected scenario preset without losing scenario selection."""
    current = st.session_state.get("scenario_choice_key", DEFAULT_PRESET_NAME)
    if current == "Custom Automaton":
        reset_to_default()
        return
    preset = PREBUILT_SCENARIOS[current]
    st.session_state.sim_step_index = 0
    st.session_state.conv_stage_index = 0
    st.session_state.stepper_str_input = preset["sample_str"]
    st.session_state.string_transitions_list = [dict(item) for item in preset["string_transitions"]]
    st.session_state.reset_counter += 1
    clear_automaton_widget_keys()
    log_action("reset_current_preset", current)


# ==========================================
# 3. FORMAL ALGORITHM ENGINES (SLIDE 100 ALIGNED)
# ==========================================
def state_sort_key(state_name, state_order_map=None):
    """Orders states naturally by declared/introduced index or numeric suffix (q1, q2, ..., q10)."""
    if state_order_map and state_name in state_order_map:
        return (0, state_order_map[state_name], "")
    m = re.match(r"^([A-Za-z_]+)(\d+)$", state_name)
    if m:
        return (1, int(m.group(2)), m.group(1))
    return (2, 0, state_name)


def sort_states(state_iterable, state_order_map=None):
    """Returns a deterministically ordered list of NFA states."""
    return sorted(list(state_iterable), key=lambda s: state_sort_key(s, state_order_map))


def format_state_name(state_set, state_order_map=None):
    """Renders exact Lecture 5 subset notation ({q1, q2} and Ø for empty/sink state)."""
    if not state_set or state_set == frozenset({"Ø"}):
        return "Ø"
    ordered = sort_states(state_set, state_order_map)
    return "{" + ", ".join(ordered) + "}"


def validate_alphabet_and_strings(alphabet_list, states_list, string_transitions):
    """Validates single-character alphabet Σ and multi-symbol string transition rules."""
    errors = []
    atomic_symbols = [s for s in alphabet_list if s != "e"]

    invalid_alpha = [s for s in atomic_symbols if len(s) != 1]
    if invalid_alpha:
        errors.append(
            f"Formal Alphabet Error: Symbols {invalid_alpha} in Alphabet must be single characters "
            f"(use 'Multi-Symbol / String Transitions' below for strings like 'ab')."
        )

    valid_sigma = {s for s in atomic_symbols if len(s) == 1}
    valid_states = set(states_list)

    for idx, rule in enumerate(string_transitions, start=1):
        src = rule.get("from", "").strip()
        lbl = rule.get("label", "").strip()
        dst = rule.get("to", "").strip()
        if src not in valid_states or dst not in valid_states:
            errors.append(f"String Rule #{idx}: State '{src}' or '{dst}' is not in declared States K.")
            continue
        if len(lbl) < 2:
            errors.append(
                f"String Rule #{idx} ('{src} ──{lbl}──▶ {dst}'): Multi-symbol string label must have length ≥ 2."
            )
            continue
        if "e" in lbl and "e" not in valid_sigma:
            errors.append(
                f"String Rule #{idx} ('{src} ──{lbl}──▶ {dst}'): Epsilon ('e') cannot be mixed inside a multi-symbol string."
            )
            continue
        unknown_chars = [ch for ch in lbl if ch not in valid_sigma]
        if unknown_chars:
            sigma_disp = "{" + ", ".join(sorted(valid_sigma)) + "}"
            errors.append(
                f"String Rule #{idx} ('{src} ──{lbl}──▶ {dst}'): Character(s) {sorted(set(unknown_chars))} "
                f"do not belong to declared Alphabet Σ = {sigma_disp}."
            )
    return errors


def build_combined_original_nfa(states_list, alphabet_list, start_state, accept_states, single_trans, string_transitions):
    """Builds the Original NFA M including both single-symbol and unsplit string edges for visualization."""
    combined = {s: {} for s in states_list}
    for s, row in single_trans.items():
        if s not in combined:
            continue
        for sym, targets in row.items():
            if targets:
                combined[s][sym] = list(targets)
    for rule in string_transitions:
        src, lbl, dst = rule["from"], rule["label"], rule["to"]
        if src in combined and dst in states_list and lbl:
            combined[src].setdefault(lbl, [])
            if dst not in combined[src][lbl]:
                combined[src][lbl].append(dst)
    return {
        "states": list(states_list),
        "alphabet": list(alphabet_list),
        "start_state": start_state,
        "accept_states": list(accept_states),
        "transitions": combined
    }


def expand_string_transitions(states_list, alphabet_list, start_state, accept_states, single_trans, string_transitions):
    """
    Slide 100 Phase 1: Eliminates multi-symbol string transitions (e.g., q4 --ab--> q1)
    by introducing sequential intermediate states q_{max+1}, q_{max+2}, ...
    """
    existing = set(states_list)
    q_nums = []
    for s in states_list:
        m = re.match(r"^q(\d+)$", s)
        if m:
            q_nums.append(int(m.group(1)))
    next_q_num = (max(q_nums) + 1) if q_nums else 1

    def allocate_new_state():
        nonlocal next_q_num
        while f"q{next_q_num}" in existing:
            next_q_num += 1
        name = f"q{next_q_num}"
        existing.add(name)
        next_q_num += 1
        return name

    expanded_states = list(states_list)
    expanded_trans = {s: {} for s in states_list}
    for s, row in single_trans.items():
        if s in expanded_trans:
            for sym, targets in row.items():
                for t in targets:
                    if t not in expanded_trans[s].setdefault(sym, []):
                        expanded_trans[s][sym].append(t)

    # Group string rules by source state in declared state order to match Heckl's slide numbering
    split_log = []
    introduced_states = []
    for src_state in states_list:
        matching_rules = [r for r in string_transitions if r["from"] == src_state]
        for rule in matching_rules:
            src, lbl, dst = rule["from"], rule["label"], rule["to"]
            if len(lbl) < 2:
                continue
            curr = src
            chain_parts = [src]
            rule_new_states = []
            for idx, ch in enumerate(lbl):
                if idx < len(lbl) - 1:
                    mid = allocate_new_state()
                    expanded_states.append(mid)
                    expanded_trans[mid] = {}
                    introduced_states.append(mid)
                    rule_new_states.append(mid)
                    expanded_trans[curr].setdefault(ch, []).append(mid)
                    chain_parts.append(f"──{ch}──▶ {mid}")
                    curr = mid
                else:
                    if dst not in expanded_trans[curr].setdefault(ch, []):
                        expanded_trans[curr][ch].append(dst)
                    chain_parts.append(f"──{ch}──▶ {dst}")
            split_log.append({
                "Original Transition": f"{src} ──{lbl}──▶ {dst}",
                "Introduced State(s)": ", ".join(rule_new_states),
                "Expanded Single-Symbol Chain": " ".join(chain_parts)
            })

    expanded_nfa = {
        "states": expanded_states,
        "alphabet": list(alphabet_list),
        "start_state": start_state,
        "accept_states": list(accept_states),
        "transitions": expanded_trans
    }
    return expanded_nfa, split_log, introduced_states


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
    """Evaluates direct single-symbol reachable states before epsilon closure."""
    reachable = set()
    for s in states:
        if s in transitions and symbol in transitions[s]:
            for nxt in transitions[s][symbol]:
                reachable.add(nxt)
    return frozenset(reachable)


def nfa_to_dfa_slide100_pipeline(original_nfa, expanded_nfa, split_log, introduced_states):
    """
    Executes Lecture 5 (Slide 100) NFA -> DFA conversion with dynamic step count detection:
      - 5 steps when multi-symbol string transitions exist
      - 4 steps when no multi-symbol string transitions exist (matching Example 3, Slides 113-117)
    Enqueues Ø immediately upon first discovery so Q1..Qn match Slides 104-130 verbatim.
    """
    alphabet = [s for s in expanded_nfa["alphabet"] if s != "e" and len(s) == 1]
    nfa_trans = expanded_nfa["transitions"]
    start_state = expanded_nfa["start_state"]
    nfa_accept = set(expanded_nfa["accept_states"])
    state_order_map = {s: idx for idx, s in enumerate(expanded_nfa["states"])}

    has_string_splits = len(split_log) > 0
    total_steps = 5 if has_string_splits else 4

    pipeline_data = {
        "has_string_splits": has_string_splits,
        "total_steps": total_steps,
        "split_log": split_log,
        "introduced_states": introduced_states,
        "e_sets": {},
        "e_sets_rows": [],
        "initial_state_label": None,
        "initial_state_formula": "",
        "q_aliases": {},
        "transitions_log": [],
        "final_states": [],
        "final_states_formula": "",
        "steps": []
    }

    if not start_state:
        return None, pipeline_data

    # Phase: Definition of E-sets
    for state in expanded_nfa["states"]:
        eset_str = format_state_name(get_empty_closure([state], nfa_trans), state_order_map)
        pipeline_data["e_sets"][state] = eset_str
        pipeline_data["e_sets_rows"].append({
            "State q": state,
            "Definition of E-set": f"E({state}) = {eset_str}"
        })

    # Phase: Definition of new initial state
    initial_closure = get_empty_closure([start_state], nfa_trans)
    initial_label = format_state_name(initial_closure, state_order_map)
    pipeline_data["initial_state_label"] = initial_label
    pipeline_data["q_aliases"][initial_label] = "Q1"
    pipeline_data["initial_state_formula"] = f"s' = E({start_state}) = {initial_label} = Q1"

    # Phase: Definition of transition function (BFS enqueuing Ø on first encounter)
    dfa_transitions = {}
    dfa_states_closures = [initial_closure]
    seen_labels = {initial_label: initial_closure}
    queue = deque([initial_closure])

    while queue:
        curr = queue.popleft()
        curr_label = format_state_name(curr, state_order_map)
        curr_alias = pipeline_data["q_aliases"][curr_label]
        dfa_transitions[curr_label] = {}

        for sym in alphabet:
            if curr:
                m_set = move(curr, sym, nfa_trans)
                m_sorted = sort_states(m_set, state_order_map)
            else:
                m_sorted = []

            if m_sorted:
                target_closure = get_empty_closure(m_sorted, nfa_trans)
                target_label = format_state_name(target_closure, state_order_map)
                union_expr = " ∪ ".join(f"E({p})" for p in m_sorted)
            else:
                target_closure = frozenset()
                target_label = "Ø"
                union_expr = "Ø"

            if target_label not in seen_labels:
                seen_labels[target_label] = target_closure
                dfa_states_closures.append(target_closure)
                pipeline_data["q_aliases"][target_label] = f"Q{len(dfa_states_closures)}"
                queue.append(target_closure)

            target_alias = pipeline_data["q_aliases"][target_label]
            dfa_transitions[curr_label][sym] = target_label

            if m_sorted:
                full_formula = f"δ({curr_label}, {sym}) = {union_expr} = {target_label} = {target_alias}"
            else:
                full_formula = f"δ({curr_label}, {sym}) = Ø = {target_alias}"

            pipeline_data["transitions_log"].append({
                "State S": f"{curr_label} ({curr_alias})",
                "Symbol σ": sym,
                "E-set Union": union_expr,
                "Target = Qi": f"{target_label} = {target_alias}",
                "Slide Formula": full_formula
            })

    # Phase: Definition of final states
    dfa_state_labels = [format_state_name(c, state_order_map) for c in dfa_states_closures]
    dfa_accept_list = []
    for c in dfa_states_closures:
        if any(s in nfa_accept for s in c):
            lbl = format_state_name(c, state_order_map)
            dfa_accept_list.append(lbl)

    pipeline_data["final_states"] = dfa_accept_list
    if dfa_accept_list:
        pipeline_data["final_states_formula"] = "F' = {" + ", ".join(dfa_accept_list) + "}"
    else:
        pipeline_data["final_states_formula"] = "F' = Ø"

    # Build Dynamic Step Descriptor Array (4 or 5 steps)
    steps = []
    if has_string_splits:
        steps.append({
            "key": "string_elim",
            "title": "Eliminating string transitions by introducing new states",
            "summary": f"Introduced {len(introduced_states)} intermediate state(s) ({', '.join(introduced_states)}) to split multi-symbol edges into single-character transitions."
        })
    steps.append({
        "key": "e_sets",
        "title": "Definition of E-sets",
        "summary": f"Computed ε-closure E(q) for all {len(expanded_nfa['states'])} single-symbol NFA states."
    })
    steps.append({
        "key": "initial_state",
        "title": "Definition of new initial state",
        "summary": pipeline_data["initial_state_formula"]
    })
    steps.append({
        "key": "transition_fn",
        "title": "Definition of transition function",
        "summary": f"Evaluated δ(S, σ) across {len(dfa_state_labels)} reachable subset state(s) (Q1..Q{len(dfa_state_labels)})."
    })
    steps.append({
        "key": "final_states",
        "title": "Definition of final states",
        "summary": pipeline_data["final_states_formula"]
    })
    for idx, st_obj in enumerate(steps, start=1):
        st_obj["step_num"] = idx
    pipeline_data["steps"] = steps

    final_dfa = {
        "states": dfa_state_labels,
        "alphabet": alphabet,
        "start_state": initial_label,
        "accept_states": dfa_accept_list,
        "transitions": dfa_transitions
    }
    return final_dfa, pipeline_data


def minimize_dfa(dfa_def):
    """Minimizes DFA using Moore's Equivalence Partitioning algorithm (with Ø sink handling)."""
    if not dfa_def or not dfa_def.get("states"):
        return None, None

    states = dfa_def["states"]
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
                    target = transitions.get(state, {}).get(sym, "Ø")
                    target_idx = -1
                    for idx, p in enumerate(partitions):
                        if target in p:
                            target_idx = idx
                            break
                    sig.append(target_idx)
                sig_tuple = tuple(sig)
                signatures.setdefault(sig_tuple, set()).add(state)

            for sig_key in sorted(signatures.keys()):
                new_partitions.append(signatures[sig_key])

        if len(new_partitions) == len(partitions):
            break
        partitions = new_partitions

    start_state = dfa_def["start_state"]

    def partition_key(p):
        if start_state in p:
            return (0, "")
        if p == {"Ø"}:
            return (2, "Ø")
        return (1, min(sorted(list(p))))

    partitions.sort(key=partition_key)

    state_map = {}
    for idx, p in enumerate(partitions):
        label = f"M{idx}"
        for s in p:
            state_map[s] = label

    min_states = [f"M{i}" for i in range(len(partitions))]
    min_start = state_map.get(start_state)
    min_accept = sorted(
        list({state_map[s] for s in accept_states if s in state_map}),
        key=lambda x: int(x[1:])
    )

    min_trans = {}
    for s in states:
        mapped_src = state_map[s]
        min_trans.setdefault(mapped_src, {})
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
        {"Minimized Group": f"M{i}", "Original DFA Subsets": ", ".join(sorted(list(p)))}
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
            return False, path, f"Invalid symbol '{char}' not in alphabet {{{', '.join(dfa_def['alphabet'])}}}."
        next_st = dfa_def["transitions"].get(curr, {}).get(char, "Ø")
        path.append((next_st, char))
        curr = next_st

    is_accepted = curr in dfa_def["accept_states"]
    return is_accepted, path, "Success"


# ==========================================
# 4. VISUALIZATION ENGINE (GRAPHVIZ DOT)
# ==========================================
def wrap_subset_label_for_dot(state_name):
    """Wraps long subset state names across two balanced lines so Graphviz circles stay compact."""
    if len(state_name) <= 12 or "," not in state_name:
        return state_name
    inner = state_name[1:-1] if state_name.startswith("{") and state_name.endswith("}") else state_name
    parts = [p.strip() for p in inner.split(",")]
    if len(parts) <= 3:
        return state_name
    mid = (len(parts) + 1) // 2
    return "{" + ", ".join(parts[:mid]) + ",\n" + ", ".join(parts[mid:]) + "}"


def draw_automaton(automaton_def, name="Automaton", highlighted_states=None, active_edge=None):
    """Generates styled topological DOT source with Mayer signaling cues and Ø sink notation."""
    dot = graphviz.Digraph(name, graph_attr={
        "rankdir": "LR",
        "bgcolor": "transparent",
        "margin": "0.12"
    })
    if not automaton_def or not automaton_def.get("start_state"):
        return dot.source

    dot.node("hidden_start", label="", shape="none", width="0", height="0")
    dot.edge("hidden_start", automaton_def["start_state"], color="#2563eb", penwidth="2.2")

    highlighted_states = set(highlighted_states or [])

    for state in automaton_def["states"]:
        shape = "doublecircle" if state in automaton_def["accept_states"] else "circle"
        fontcolor = "#0f172a"

        if state in highlighted_states:
            fillcolor = "#86efac"
            penwidth = "3.2"
            color = "#15803d"
        elif state == automaton_def["start_state"]:
            fillcolor = "#dbeafe"
            penwidth = "2.0"
            color = "#1d4ed8"
        elif state == "Ø":
            fillcolor = "#fee2e2"
            penwidth = "1.6"
            color = "#b91c1c"
        else:
            fillcolor = "#ffffff"
            penwidth = "1.3"
            color = "#64748b"

        disp_label = wrap_subset_label_for_dot(state)
        fontsize = "11" if len(state) > 12 else "13"
        dot.node(
            state, disp_label, shape=shape, style="filled", fillcolor=fillcolor,
            color=color, penwidth=penwidth, fontcolor=fontcolor, fontname="Arial", fontsize=fontsize
        )

    edge_groups = {}
    for src, transitions in automaton_def["transitions"].items():
        for symbol, dests in transitions.items():
            target_list = dests if isinstance(dests, list) else [dests]
            for dest in target_list:
                edge_groups.setdefault((src, dest), []).append(symbol)

    for (src, dest), symbols in edge_groups.items():
        is_hit = active_edge and (src == active_edge[0] and dest == active_edge[1] and active_edge[2] in symbols)
        edge_color = "#dc2626" if is_hit else "#475569"
        edge_width = "3.0" if is_hit else "1.4"
        label_str = ", ".join("ε" if s == "e" else s for s in symbols)
        dot.edge(
            src, dest, label=f" {label_str} ", fontcolor="#0f172a",
            color=edge_color, penwidth=edge_width, fontname="Arial", fontsize="12"
        )
    return dot.source


# ==========================================
# 5. USER INTERFACE ARCHITECTURE
# ==========================================
def main():
    st.title("🧠 Automata Studio: Interactive Learning Laboratory")
    st.markdown(
        """
        Master **NFA → DFA Conversion** through **Auto-Detected Lecture 5 Steps (Slide 100)**, 
        **Multi-Symbol String Transition Splitting**, **E-Set Union Derivations**, and **Step-by-Step String Tracing**.
        """
    )

    # --- SIDEBAR CONFIGURATION ---
    with st.sidebar:
        st.header("⚙️ Experiment Controls")
        participant_tag = st.text_input("Participant ID (Optional)", placeholder="e.g., SZE-XXXXXX")

        rcol1, rcol2 = st.columns(2)
        with rcol1:
            st.button("🔄 Reset Default", use_container_width=True, type="secondary", on_click=reset_to_default)
        with rcol2:
            st.button("↺ Reset Preset", use_container_width=True, type="secondary", on_click=reset_current_preset)

        st.divider()
        st.header("📚 Scenarios & Presets")
        scenario_options = ["Custom Automaton"] + list(PREBUILT_SCENARIOS.keys())
        scenario_choice = st.selectbox(
            "Select Scenario Preset:",
            scenario_options,
            key="scenario_choice_key"
        )

        # Synchronize state when switching presets
        if scenario_choice != st.session_state.last_loaded_scenario:
            st.session_state.last_loaded_scenario = scenario_choice
            st.session_state.sim_step_index = 0
            st.session_state.conv_stage_index = 0
            clear_automaton_widget_keys()
            if scenario_choice in PREBUILT_SCENARIOS:
                p_load = PREBUILT_SCENARIOS[scenario_choice]
                st.session_state.stepper_str_input = p_load["sample_str"]
                st.session_state.string_transitions_list = [dict(x) for x in p_load["string_transitions"]]
            else:
                st.session_state.stepper_str_input = ""
                st.session_state.string_transitions_list = []
            log_action("select_preset", scenario_choice)

        if scenario_choice != "Custom Automaton":
            preset = PREBUILT_SCENARIOS[scenario_choice]
            def_states = preset["states"]
            def_alpha = preset["alphabet"]
            def_start = preset["start"]
            def_acc = preset["accept"]
            st.info(f"ℹ️ **Scenario Note:** {preset['description']}")
        else:
            preset = None
            def_states = "q1, q2, q3"
            def_alpha = "a, b, e"
            def_start = "q1"
            def_acc = ["q3"]
            st.info(
                "ℹ️ **Custom Mode:** Define states, single-symbol alphabet, and transitions below "
                "(including multi-symbol strings like `ab`) to practice active conversion."
            )

        rc = st.session_state.reset_counter
        st.subheader("NFA Formal Specification")
        raw_states = st.text_input(
            "States K (comma-separated)",
            value=def_states,
            key=f"states_in_{scenario_choice}_{rc}"
        )
        states_list = list(dict.fromkeys(s.strip() for s in raw_states.split(",") if s.strip()))

        raw_alphabet = st.text_input(
            "Alphabet Σ (single symbols, 'e' for ε)",
            value=def_alpha,
            key=f"alpha_in_{scenario_choice}_{rc}"
        )
        alphabet_list = list(dict.fromkeys(a.strip() for a in raw_alphabet.split(",") if a.strip()))

        start_state = st.selectbox(
            "Initial State (s)",
            options=states_list,
            index=states_list.index(def_start) if def_start in states_list else 0,
            key=f"start_sel_{scenario_choice}_{rc}"
        ) if states_list else None

        accept_states = st.multiselect(
            "Final States (F)",
            options=states_list,
            default=[a for a in def_acc if a in states_list],
            key=f"acc_sel_{scenario_choice}_{rc}"
        )

        st.divider()
        st.markdown("#### Single-Symbol & ε Transitions")
        single_transitions = {s: {} for s in states_list}

        for state in states_list:
            with st.expander(f"Transitions from '{state}'", expanded=(scenario_choice != "Custom Automaton")):
                for sym in alphabet_list:
                    default_targets = []
                    if preset and state in preset["transitions"] and sym in preset["transitions"][state]:
                        default_targets = [t for t in preset["transitions"][state][sym] if t in states_list]

                    disp_sym = "ε (e)" if sym == "e" else sym
                    selected = st.multiselect(
                        f"Read '{disp_sym}' ➔ Go to:",
                        options=states_list,
                        default=default_targets,
                        key=f"trans_{scenario_choice}_{rc}_{state}_{sym}"
                    )
                    if selected:
                        single_transitions[state][sym] = selected

        st.divider()
        st.markdown("#### Multi-Symbol / String Transitions")
        st.caption("Add string edges (length ≥ 2, e.g., `ab`, `aa`, `ba`, `bb`) to trigger Step 1 string splitting.")

        # Prune any string rules referencing deleted states
        st.session_state.string_transitions_list = [
            r for r in st.session_state.string_transitions_list
            if r.get("from") in states_list and r.get("to") in states_list
        ]

        if st.session_state.string_transitions_list:
            for idx, rule in enumerate(list(st.session_state.string_transitions_list)):
                sc1, sc2 = st.columns([4, 1])
                sc1.markdown(f"`{rule['from']} ──{rule['label']}──▶ {rule['to']}`")
                if sc2.button("✕", key=f"del_str_{scenario_choice}_{rc}_{idx}", help="Remove string transition"):
                    removed = st.session_state.string_transitions_list.pop(idx)
                    st.session_state.conv_stage_index = 0
                    log_action("remove_string_transition", f"{removed['from']}--{removed['label']}-->{removed['to']}")
                    st.rerun()
        else:
            st.caption("*No multi-symbol string transitions active.*")

        if states_list:
            add_c1, add_c2, add_c3 = st.columns([1.1, 1.2, 1.1])
            new_from = add_c1.selectbox("From", options=states_list, key=f"str_from_{scenario_choice}_{rc}")
            new_lbl = add_c2.text_input("String", placeholder="ab", key=f"str_lbl_{scenario_choice}_{rc}").strip()
            new_to = add_c3.selectbox("To", options=states_list, key=f"str_to_{scenario_choice}_{rc}")
            if st.button("➕ Add String Transition", use_container_width=True):
                candidate_err = validate_alphabet_and_strings(
                    alphabet_list, states_list, [{"from": new_from, "label": new_lbl, "to": new_to}]
                )
                if candidate_err:
                    st.error(candidate_err[0])
                else:
                    new_rule = {"from": new_from, "label": new_lbl, "to": new_to}
                    if new_rule not in st.session_state.string_transitions_list:
                        st.session_state.string_transitions_list.append(new_rule)
                        st.session_state.conv_stage_index = 0
                        log_action("add_string_transition", f"{new_from}--{new_lbl}-->{new_to}")
                        st.rerun()

    if not states_list or not start_state:
        st.warning("⚠️ Please provide at least one state and an initial state in the sidebar to begin.")
        return

    validation_errors = validate_alphabet_and_strings(
        alphabet_list, states_list, st.session_state.string_transitions_list
    )
    if validation_errors:
        for err in validation_errors:
            st.error(f"⚠️ {err}")
        return

    has_any_single = any(bool(row) for row in single_transitions.values())
    has_any_string = len(st.session_state.string_transitions_list) > 0
    is_blank_custom = (scenario_choice == "Custom Automaton") and (not has_any_single) and (not has_any_string)

    original_nfa = build_combined_original_nfa(
        states_list, alphabet_list, start_state, accept_states,
        single_transitions, st.session_state.string_transitions_list
    )
    expanded_nfa, split_log, introduced_states = expand_string_transitions(
        states_list, alphabet_list, start_state, accept_states,
        single_transitions, st.session_state.string_transitions_list
    )
    dfa_def, pipeline_data = nfa_to_dfa_slide100_pipeline(
        original_nfa, expanded_nfa, split_log, introduced_states
    )
    min_dfa_def, min_mapping = minimize_dfa(dfa_def)

    # ==========================================
    # 6. MAIN APPLICATION TABS (STRICTLY 3 TABS)
    # ==========================================
    tab_pipeline, tab_stepper, tab_telemetry = st.tabs([
        "📊 1. NFA ➔ DFA Step-by-Step Conversion",
        "⏯️ 2. Step-by-Step String Stepper",
        "📋 3. Research Telemetry & Activity Log"
    ])

    # --- TAB 1: LECTURE 5 STEP-BY-STEP CONVERSION & PIPELINE ---
    with tab_pipeline:
        if is_blank_custom:
            st.info(
                "📝 **Blank Custom Automaton Ready for Practice:** Add single-symbol transitions or multi-symbol string "
                "transitions (e.g., `ab`, `ba`) in the left sidebar — or select a **Lecture 5 Example (Slides 101–132)** "
                "preset — to build your NFA and step through the conversion."
            )

        if pipeline_data["has_string_splits"]:
            st.success(
                f"🔍 **Auto-Detected {pipeline_data['total_steps']} Conversion Steps (Slide 100):** "
                f"Detected **{len(split_log)}** multi-symbol string transition(s) — **Step 1** splits string transitions "
                f"by introducing intermediate state(s) `{', '.join(introduced_states)}`."
            )
        else:
            st.info(
                f"🔍 **Auto-Detected {pipeline_data['total_steps']} Conversion Steps (Slide 100):** "
                f"No multi-symbol string transitions detected — string-transition elimination is skipped automatically "
                f"(starts directly at **Step 1: Definition of E-sets**, matching Example 3)."
            )

        tbar1, tbar2 = st.columns([1.6, 1.4])
        with tbar1:
            view_mode = st.radio(
                "Presentation Mode:",
                ["Interactive Step-by-Step Walkthrough", "Full Pipeline Overview"],
                horizontal=True,
                key="pipeline_view_mode_radio"
            )
        with tbar2:
            st.write("")
            show_min_dfa = st.checkbox(
                "Show Optional Bonus Stage: Minimized DFA",
                key="show_optional_min_dfa"
            )

        st.caption(
            "Legend: 🔵 Initial State (#dbeafe) | 🟢 Newly Introduced / Highlighted State (#86efac) "
            "| ◎ Final State (Double Circle) | 🔴 Ø Empty / Trap State (#fee2e2)."
        )

        steps_list = pipeline_data["steps"]
        max_stage = len(steps_list) + (1 if show_min_dfa else 0)
        st.session_state.conv_stage_index = min(st.session_state.conv_stage_index, max_stage)

        if view_mode == "Interactive Step-by-Step Walkthrough":
            nav1, nav2, nav3, nav4 = st.columns([1.1, 1.1, 1.2, 2.6])
            with nav1:
                if st.button("⏮️ Given NFA", use_container_width=True):
                    st.session_state.conv_stage_index = 0
                    log_action("conv_step_reset")
            with nav2:
                if st.button("◀️ Prev Step", use_container_width=True, disabled=(st.session_state.conv_stage_index == 0)):
                    st.session_state.conv_stage_index = max(0, st.session_state.conv_stage_index - 1)
                    log_action("conv_step_prev", f"Stage_{st.session_state.conv_stage_index}")
            with nav3:
                if st.button("Next Step ▶️", use_container_width=True, type="primary", disabled=(st.session_state.conv_stage_index >= max_stage)):
                    st.session_state.conv_stage_index = min(max_stage, st.session_state.conv_stage_index + 1)
                    log_action("conv_step_next", f"Stage_{st.session_state.conv_stage_index}")

            stage_idx = min(st.session_state.conv_stage_index, max_stage)
            stage_labels = ["Given NFA M"] + [f"Step {s['step_num']}: {s['title']}" for s in steps_list]
            if show_min_dfa:
                stage_labels.append("Bonus: Minimized DFA")
            nav4.markdown(f"**Current View:** `{stage_labels[stage_idx]}`")

            if stage_idx == 0:
                st.markdown(f"#### Given NFA M (`{len(original_nfa['states'])} states`)")
                st.graphviz_chart(draw_automaton(original_nfa, "Given_NFA"), use_container_width=True)
                st.markdown("**Detected Conversion Plan (Slide 100):**")
                for s_obj in steps_list:
                    st.markdown(f"- **Step {s_obj['step_num']}** — *{s_obj['title']}*")
            elif stage_idx <= len(steps_list):
                active_step = steps_list[stage_idx - 1]
                st.markdown(f"#### Step {active_step['step_num']} of {len(steps_list)} — {active_step['title']}")

                if active_step["key"] == "string_elim":
                    sc_left, sc_right = st.columns(2)
                    with sc_left:
                        st.markdown(f"**Original NFA M (`{len(original_nfa['states'])} states`)**")
                        st.graphviz_chart(draw_automaton(original_nfa, "Orig_NFA_Step1"), use_container_width=True)
                    with sc_right:
                        st.markdown(f"**Expanded Single-Symbol NFA (`{len(expanded_nfa['states'])} states`)**")
                        st.graphviz_chart(
                            draw_automaton(expanded_nfa, "Exp_NFA_Step1", highlighted_states=introduced_states),
                            use_container_width=True
                        )
                    st.dataframe(pd.DataFrame(split_log), hide_index=True, use_container_width=True)

                elif active_step["key"] == "e_sets":
                    sc_left, sc_right = st.columns([1.2, 1])
                    with sc_left:
                        st.markdown("**Single-Symbol NFA Reference**")
                        st.graphviz_chart(draw_automaton(expanded_nfa, "Ref_NFA_Esets"), use_container_width=True)
                    with sc_right:
                        st.markdown("**Definition of E-sets:**")
                        st.dataframe(pd.DataFrame(pipeline_data["e_sets_rows"]), hide_index=True, use_container_width=True)

                elif active_step["key"] == "initial_state":
                    init_members = list(get_empty_closure([start_state], expanded_nfa["transitions"]))
                    sc_left, sc_right = st.columns([1.2, 1])
                    with sc_left:
                        st.markdown("**Initial E-Closure Highlighted on NFA**")
                        st.graphviz_chart(
                            draw_automaton(expanded_nfa, "Ref_NFA_Init", highlighted_states=init_members),
                            use_container_width=True
                        )
                    with sc_right:
                        st.markdown("**Definition of new initial state:**")
                        st.success(f"`{pipeline_data['initial_state_formula']}`")

                elif active_step["key"] == "transition_fn":
                    sc_left, sc_right = st.columns([1.05, 1.35])
                    with sc_left:
                        st.markdown("**Single-Symbol NFA Reference**")
                        st.graphviz_chart(draw_automaton(expanded_nfa, "Ref_NFA_Trans"), use_container_width=True)
                    with sc_right:
                        st.markdown("**Definition of transition function (BFS Order Q1..Qn):**")
                        st.dataframe(
                            pd.DataFrame(pipeline_data["transitions_log"])[["Slide Formula"]],
                            hide_index=True,
                            use_container_width=True
                        )

                elif active_step["key"] == "final_states":
                    st.success(f"**Definition of final states:** `{pipeline_data['final_states_formula']}`")
                    st.markdown(f"#### Resulting Converted DFA M' (`{len(dfa_def['states'])} states`)")
                    st.graphviz_chart(
                        draw_automaton(dfa_def, "Result_DFA", highlighted_states=[s for s in dfa_def["accept_states"] if s != dfa_def["start_state"]]),
                        use_container_width=True
                    )
            else:
                st.markdown(f"#### Bonus Stage — Minimized DFA (`{len(min_dfa_def['states'])} states`)")
                mc1, mc2 = st.columns([1.3, 1])
                with mc1:
                    st.graphviz_chart(draw_automaton(min_dfa_def, "Bonus_Min_DFA"), use_container_width=True)
                with mc2:
                    st.dataframe(min_mapping, hide_index=True, use_container_width=True)

        else:
            # Full Pipeline Overview Mode
            num_graph_cols = 2 + (1 if pipeline_data["has_string_splits"] else 0) + (1 if show_min_dfa else 0)
            gcols = st.columns(num_graph_cols)
            col_ptr = 0

            with gcols[col_ptr]:
                st.markdown(f"#### Given NFA (`{len(original_nfa['states'])} states`)")
                st.graphviz_chart(draw_automaton(original_nfa, "Overview_Orig_NFA"), use_container_width=True)
            col_ptr += 1

            if pipeline_data["has_string_splits"]:
                with gcols[col_ptr]:
                    st.markdown(f"#### Step 1 NFA (`{len(expanded_nfa['states'])} states`)")
                    st.graphviz_chart(
                        draw_automaton(expanded_nfa, "Overview_Exp_NFA", highlighted_states=introduced_states),
                        use_container_width=True
                    )
                col_ptr += 1

            with gcols[col_ptr]:
                st.markdown(f"#### Converted DFA (`{len(dfa_def['states'])} states`)")
                st.graphviz_chart(draw_automaton(dfa_def, "Overview_DFA"), use_container_width=True)
            col_ptr += 1

            if show_min_dfa and min_dfa_def:
                with gcols[col_ptr]:
                    st.markdown(f"#### Minimized DFA (`{len(min_dfa_def['states'])} states`)")
                    st.graphviz_chart(draw_automaton(min_dfa_def, "Overview_Min_DFA"), use_container_width=True)

            st.markdown("#### Complete Step-by-Step Mathematical Derivations (Slide 100)")
            for s_obj in steps_list:
                with st.expander(f"Step {s_obj['step_num']} of {len(steps_list)} — {s_obj['title']}", expanded=True):
                    if s_obj["key"] == "string_elim":
                        st.dataframe(pd.DataFrame(split_log), hide_index=True, use_container_width=True)
                    elif s_obj["key"] == "e_sets":
                        st.dataframe(pd.DataFrame(pipeline_data["e_sets_rows"]), hide_index=True, use_container_width=True)
                    elif s_obj["key"] == "initial_state":
                        st.markdown(f"`{pipeline_data['initial_state_formula']}`")
                    elif s_obj["key"] == "transition_fn":
                        st.dataframe(
                            pd.DataFrame(pipeline_data["transitions_log"])[["State S", "Symbol σ", "E-set Union", "Target = Qi", "Slide Formula"]],
                            hide_index=True,
                            use_container_width=True
                        )
                    elif s_obj["key"] == "final_states":
                        st.markdown(f"`{pipeline_data['final_states_formula']}`")

            if show_min_dfa and min_mapping is not None:
                with st.expander("Optional Bonus — Minimized DFA Equivalence Partition Map", expanded=True):
                    st.dataframe(min_mapping, hide_index=True, use_container_width=True)

    # --- TAB 2: STEP-BY-STEP STRING STEPPER ---
    with tab_stepper:
        st.markdown("### Interactive Step-by-Step String Stepper")
        st.caption("Trace character-by-character transitions on the Converted DFA one click at a time.")

        sim_cols = st.columns([2, 1])
        with sim_cols[0]:
            target_str = st.text_input(
                "Input String to Trace:",
                placeholder="Enter a string over Σ (e.g., abba)...",
                key="stepper_str_input"
            ).strip()
        with sim_cols[1]:
            if st.session_state.show_optional_min_dfa:
                machine_target = st.radio(
                    "Select Target Automaton:",
                    ["Converted DFA", "Minimized DFA"],
                    horizontal=True,
                    key="stepper_target_radio"
                )
            else:
                machine_target = "Converted DFA"
                st.markdown("**Target Automaton:** `Converted DFA (M')`")
            chosen_machine = min_dfa_def if (machine_target == "Minimized DFA" and min_dfa_def) else dfa_def

        if is_blank_custom and not target_str:
            st.info(
                "ℹ️ Add transitions to your Custom Automaton in the sidebar and enter a test string above to trace execution."
            )
        else:
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
                    if st.button("Next Step ▶️", use_container_width=True, type="primary"):
                        st.session_state.sim_step_index = min(max_steps, st.session_state.sim_step_index + 1)
                        log_action("stepper_next", f"Step_{st.session_state.sim_step_index}")

                current_idx = min(st.session_state.sim_step_index, max_steps)
                current_state = path[current_idx][0]
                consumed_symbol = path[current_idx][1]
                visited_trace = " ➔ ".join(p[0] for p in path[:current_idx + 1])

                st.markdown(f"**Step {current_idx} of {max_steps}** | Active State: `{current_state}` | Path: `{visited_trace}`")

                if not target_str:
                    st.markdown("String Progress: *ε (empty string)*")
                else:
                    str_vis = []
                    for i, ch in enumerate(target_str):
                        if i < current_idx:
                            str_vis.append(f"<span style='background-color: #dcfce7; color: #166534; padding: 2px 7px; border-radius: 5px; font-weight: bold;'>{ch}</span>")
                        elif i == current_idx:
                            str_vis.append(f"<span style='background-color: #fde047; color: #0f172a; padding: 2px 7px; border-radius: 5px; font-weight: bold;'>{ch}</span>")
                        else:
                            str_vis.append(f"<span style='color: #94a3b8; padding: 2px 7px;'>{ch}</span>")
                    st.markdown(f"String Progress: {' '.join(str_vis)}", unsafe_allow_html=True)

                active_edge_tuple = None
                if current_idx > 0:
                    prev_state = path[current_idx - 1][0]
                    active_edge_tuple = (prev_state, current_state, consumed_symbol)

                st.graphviz_chart(
                    draw_automaton(
                        chosen_machine,
                        "Stepper_Graph",
                        highlighted_states=[current_state],
                        active_edge=active_edge_tuple
                    ),
                    use_container_width=True
                )

                if current_idx == max_steps:
                    disp_str = target_str if target_str else "ε"
                    if is_acc:
                        st.success(f"🎉 Simulation Complete: The string '{disp_str}' is **ACCEPTED** (Ended in final state `{current_state}`).")
                    else:
                        st.error(f"🛑 Simulation Complete: The string '{disp_str}' is **REJECTED** (Ended in non-final state `{current_state}`).")

    # --- TAB 3: RESEARCH TELEMETRY & AUDIT ---
    with tab_telemetry:
        st.markdown("### 📋 Educational Interaction Telemetry")
        st.caption("Verifiable interaction log recorded during this learning session. Useful for research validation.")

        total_actions = len(st.session_state.user_actions_log)
        elapsed_sec = round(time.time() - st.session_state.session_start_time, 1)
        elapsed_min = round(elapsed_sec / 60, 1)

        m1, m2 = st.columns(2)
        m1.metric("Active Session Time", f"{elapsed_min} mins")
        m2.metric("Total User Actions", f"{total_actions} events")

        telemetry_payload = {
            "participant_id": participant_tag.strip() or "ANONYMOUS",
            "elapsed_seconds": elapsed_sec,
            "actions_summary_count": total_actions,
            "recent_actions": st.session_state.user_actions_log[-10:]
        }

        st.markdown("#### Session Verification Code")
        st.caption("You can copy this JSON string as proof of active participation if requested by your instructor:")
        st.code(json.dumps(telemetry_payload, indent=2), language="json")

        if st.checkbox("Show Detailed Action Event Log"):
            if st.session_state.user_actions_log:
                st.dataframe(pd.DataFrame(st.session_state.user_actions_log), hide_index=True, use_container_width=True)
            else:
                st.info("No interaction events recorded yet in this session.")


if __name__ == "__main__":
    main()
