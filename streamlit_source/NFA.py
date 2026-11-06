import re
import time
import json
from collections import deque
import streamlit as st
class _DotBuilder:
    """Pure-Python Graphviz DOT string builder (zero external package/binary dependency)."""

    def __init__(self, name="Automaton", graph_attr=None):
        self._name = re.sub(r"[^A-Za-z0-9_]", "_", str(name))
        self._lines = [f"digraph {self._name} {{"]
        for k, v in (graph_attr or {}).items():
            self._lines.append(f"  {k}={self._q(v)};")

    @staticmethod
    def _q(val):
        s = str(val).replace("\\", "\\\\").replace('"', '\\"').replace("\n", "\\n")
        return f'"{s}"'

    def node(self, name, label=None, **attrs):
        kv = []
        if label is not None:
            kv.append(f"label={self._q(label)}")
        for k, v in attrs.items():
            kv.append(f"{k}={self._q(v)}")
        attr_str = f" [{', '.join(kv)}]" if kv else ""
        self._lines.append(f"  {self._q(name)}{attr_str};")

    def edge(self, src, dst, label=None, **attrs):
        kv = []
        if label is not None:
            kv.append(f"label={self._q(label)}")
        for k, v in attrs.items():
            kv.append(f"{k}={self._q(v)}")
        attr_str = f" [{', '.join(kv)}]" if kv else ""
        self._lines.append(f"  {self._q(src)} -> {self._q(dst)}{attr_str};")

    @property
    def source(self):
        return "\n".join(self._lines + ["}"])
import pandas as pd

# ==========================================
# 1. PAGE CONFIGURATION & SESSION STATE
# ==========================================
st.set_page_config(
    page_title="Automata Studio",
    page_icon="🧠",
    layout="wide",
    initial_sidebar_state="expanded"
)

DEFAULT_PRESET_NAME = "Custom Automaton"

GROUP_PALETTE = [
    {"fill": "#e0f2fe", "stroke": "#0284c7", "sw": "2.4"},
    {"fill": "#dcfce7", "stroke": "#15803d", "sw": "2.4"},
    {"fill": "#fef9c3", "stroke": "#ca8a04", "sw": "2.4"},
    {"fill": "#f3e8ff", "stroke": "#7e22ce", "sw": "2.4"},
    {"fill": "#ffedd5", "stroke": "#c2410c", "sw": "2.4"},
    {"fill": "#fce7f3", "stroke": "#be185d", "sw": "2.4"},
    {"fill": "#e0e7ff", "stroke": "#4338ca", "sw": "2.4"},
    {"fill": "#ccfbf1", "stroke": "#0f766e", "sw": "2.4"},
]

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
            "q4": {"a": ["q2"]},
        },
        "string_transitions": [
            {"from": "q4", "label": "ab", "to": "q1"}
        ],
        "sample_str": "baabba",
        "description": "NFA → DFA: Example 1 (Slides 101–106)",
    },
    "NFA → DFA: Example 2": {
        "states": "q1, q2, q3",
        "alphabet": "a, b, e",
        "start": "q1",
        "accept": ["q3"],
        "transitions": {
            "q1": {"b": ["q2"]},
            "q2": {"b": ["q3"]},
            "q3": {"e": ["q1"]},
        },
        "string_transitions": [
            {"from": "q1", "label": "aa", "to": "q2"},
            {"from": "q1", "label": "ba", "to": "q2"},
        ],
        "sample_str": "bab",
        "description": "NFA → DFA: Example 2 (Slides 107–112)",
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
            "q8": {},
        },
        "string_transitions": [],
        "sample_str": "aab",
        "description": "NFA → DFA: Example 3 (Slides 113–117)",
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
            "q6": {"e": ["q4", "q5"]},
        },
        "string_transitions": [
            {"from": "q1", "label": "ab", "to": "q4"}
        ],
        "sample_str": "abb",
        "description": "NFA → DFA: Example 4 (Slides 118–124)",
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
            "q7": {},
        },
        "string_transitions": [
            {"from": "q7", "label": "bb", "to": "q1"}
        ],
        "sample_str": "bba",
        "description": "NFA → DFA: Example 5 (Slides 125–132)",
    },
}

def init_session_state():
    defaults = {
        "user_actions_log": [],
        "session_start_time": time.time(),
        "sim_step_index": 0,
        "conv_stage_index": 0,
        "eset_sub_index": 0,
        "trans_sub_index": 0,
        "min_sub_index": 0,
        "scenario_choice_key": DEFAULT_PRESET_NAME,
        "last_loaded_scenario": DEFAULT_PRESET_NAME,
        "stepper_str_input": "",
        "string_transitions_list": [],
        "show_optional_min_dfa": False,
        "reset_counter": 0,
    }
    for k, v in defaults.items():
        if k not in st.session_state:
            st.session_state[k] = v

init_session_state()

def log_action(action_type, details=""):
    """Tracks learner behavior for educational research telemetry."""
    elapsed = round(time.time() - st.session_state.session_start_time, 1)
    st.session_state.user_actions_log.append({
        "timestamp_sec": elapsed,
        "action": action_type,
        "details": details,
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
    st.session_state.eset_sub_index = 0
    st.session_state.trans_sub_index = 0
    st.session_state.min_sub_index = 0
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
    st.session_state.eset_sub_index = 0
    st.session_state.trans_sub_index = 0
    st.session_state.min_sub_index = 0
    st.session_state.stepper_str_input = preset["sample_str"]
    st.session_state.string_transitions_list = [dict(item) for item in preset["string_transitions"]]
    st.session_state.reset_counter += 1
    clear_automaton_widget_keys()
    log_action("reset_current_preset", current)

# ==========================================
# 3. FORMAL ALGORITHM ENGINES (SLIDE 100 + SUB-STEP + M2)
# ==========================================
def state_sort_key(state_name, state_order_map=None):
    if state_order_map and state_name in state_order_map:
        return (0, state_order_map[state_name], "")
    m = re.match(r"^([A-Za-z_]+)(\d+)$", state_name)
    if m:
        return (1, int(m.group(2)), m.group(1))
    return (2, 0, state_name)

def sort_states(state_iterable, state_order_map=None):
    return sorted(list(state_iterable), key=lambda s: state_sort_key(s, state_order_map))

def format_state_name(state_set, state_order_map=None):
    if not state_set or state_set == frozenset({"Ø"}):
        return "Ø"
    ordered = sort_states(state_set, state_order_map)
    return "{" + ", ".join(ordered) + "}"

def validate_alphabet_and_strings(alphabet_list, states_list, string_transitions):
    errors = []
    atomic_symbols = [s for s in alphabet_list if s != "e"]

    invalid_alpha = [s for s in atomic_symbols if len(s) != 1]
    if invalid_alpha:
        errors.append(
            f"Formal Alphabet Error: Symbols {invalid_alpha} in Alphabet must be single characters "
            f"(use 'String Transitions' below for multi-symbol strings like 'ab')."
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
        "transitions": combined,
    }

def expand_string_transitions(states_list, alphabet_list, start_state, accept_states, single_trans, string_transitions):
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
                "String Arc": f"{src} ──{lbl}──▶ {dst}",
                "New State(s)": ", ".join(rule_new_states),
                "Single-Symbol Chain": " ".join(chain_parts),
            })

    expanded_nfa = {
        "states": expanded_states,
        "alphabet": list(alphabet_list),
        "start_state": start_state,
        "accept_states": list(accept_states),
        "transitions": expanded_trans,
    }
    return expanded_nfa, split_log, introduced_states

def trace_epsilon_closure_bfs(seed_states, transitions, state_order_map=None):
    """Traces exact BFS epsilon-closure hops and traversed ε-edges."""
    closure_set = set(seed_states)
    bfs_queue = deque(seed_states)
    hops = []
    eps_edges = []
    while bfs_queue:
        u = bfs_queue.popleft()
        for v in transitions.get(u, {}).get("e", []):
            is_new = v not in closure_set
            hops.append({"from": u, "to": v, "is_new": is_new})
            eps_edges.append({"src": u, "dest": v, "symbol": "e", "role": "eps"})
            if is_new:
                closure_set.add(v)
                bfs_queue.append(v)
    members = sort_states(closure_set, state_order_map)
    return members, hops, eps_edges

def get_empty_closure(states, transitions):
    members, _, _ = trace_epsilon_closure_bfs(states, transitions)
    return frozenset(members)

def move(states, symbol, transitions):
    reachable = set()
    for s in states:
        for nxt in transitions.get(s, {}).get(symbol, []):
            reachable.add(nxt)
    return frozenset(reachable)

def nfa_to_dfa_slide100_pipeline(original_nfa, expanded_nfa, split_log, introduced_states):
    """Executes Lecture 5 (Slide 100) NFA -> DFA conversion with sub-step path traces."""
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
        "initial_state_members": [],
        "initial_state_eps_edges": [],
        "q_aliases": {},
        "transitions_log": [],
        "final_states": [],
        "final_states_formula": "",
        "steps": [],
    }

    if not start_state:
        return None, pipeline_data

    # Phase: Definition of E-sets (with BFS path traces)
    e_trace_by_state = {}
    for state in expanded_nfa["states"]:
        members, hops, eps_edges = trace_epsilon_closure_bfs([state], nfa_trans, state_order_map)
        e_trace_by_state[state] = {"members": members, "hops": hops, "eps_edges": eps_edges}
        eset_str = format_state_name(frozenset(members), state_order_map)
        pipeline_data["e_sets"][state] = eset_str
        pipeline_data["e_sets_rows"].append({
            "state": state,
            "eset_str": eset_str,
            "formula": f"E({state}) = {eset_str}",
            "members": members,
            "eps_reached_states": [x for x in members if x != state],
            "hops": hops,
            "eps_edges": eps_edges,
        })

    # Phase: Definition of new initial state
    init_trace = e_trace_by_state[start_state]
    initial_closure = frozenset(init_trace["members"])
    initial_label = format_state_name(initial_closure, state_order_map)
    pipeline_data["initial_state_label"] = initial_label
    pipeline_data["initial_state_members"] = list(init_trace["members"])
    pipeline_data["initial_state_eps_edges"] = list(init_trace["eps_edges"])
    pipeline_data["q_aliases"][initial_label] = "Q1"
    pipeline_data["initial_state_formula"] = f"s' = E({start_state}) = {initial_label} = Q1"

    # Phase: Definition of transition function (BFS enqueuing Ø on first encounter)
    dfa_transitions = {}
    dfa_states_closures = [initial_closure]
    seen_labels = {initial_label: initial_closure}
    queue = deque([initial_closure])

    while queue:
        curr = queue.popleft()
        curr_members = sort_states(curr, state_order_map) if curr else []
        curr_label = format_state_name(curr, state_order_map)
        curr_alias = pipeline_data["q_aliases"][curr_label]
        dfa_transitions[curr_label] = {}

        for sym in alphabet:
            move_hops = []
            move_edges = []
            move_set = set()
            for s in curr_members:
                for dst in nfa_trans.get(s, {}).get(sym, []):
                    move_hops.append({"from": s, "symbol": sym, "to": dst})
                    move_edges.append({"src": s, "dest": dst, "symbol": sym, "role": "move"})
                    move_set.add(dst)
            m_sorted = sort_states(move_set, state_order_map)

            if m_sorted:
                t_members, _, eps_edges = trace_epsilon_closure_bfs(m_sorted, nfa_trans, state_order_map)
                target_closure = frozenset(t_members)
                target_label = format_state_name(target_closure, state_order_map)
                union_expr = " ∪ ".join(f"E({p})" for p in m_sorted)
                eset_components = [{"state": p, "eset_str": pipeline_data["e_sets"][p]} for p in m_sorted]
                eps_only_states = [x for x in t_members if x not in move_set]
            else:
                t_members = []
                eps_edges = []
                target_closure = frozenset()
                target_label = "Ø"
                union_expr = "Ø"
                eset_components = []
                eps_only_states = []

            is_newly_discovered = target_label not in seen_labels
            if is_newly_discovered:
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
                "curr_label": curr_label,
                "curr_alias": curr_alias,
                "curr_members": curr_members,
                "symbol": sym,
                "move_states": m_sorted,
                "move_hops": move_hops,
                "move_edges": move_edges,
                "eps_edges": eps_edges,
                "eps_only_states": eps_only_states,
                "eset_components": eset_components,
                "union_expr": union_expr,
                "target_label": target_label,
                "target_alias": target_alias,
                "is_newly_discovered": is_newly_discovered,
                "Slide Formula": full_formula,
            })

    dfa_state_labels = [format_state_name(c, state_order_map) for c in dfa_states_closures]
    dfa_accept_list = [
        format_state_name(c, state_order_map)
        for c in dfa_states_closures
        if any(s in nfa_accept for s in c)
    ]

    pipeline_data["final_states"] = dfa_accept_list
    pipeline_data["final_states_formula"] = (
        "F' = {" + ", ".join(dfa_accept_list) + "}" if dfa_accept_list else "F' = Ø"
    )

    steps = []
    if has_string_splits:
        steps.append({
            "key": "string_elim",
            "title": "Eliminating string transitions by introducing new states",
        })
    steps.append({"key": "e_sets", "title": "Definition of E-sets"})
    steps.append({"key": "initial_state", "title": "Definition of new initial state"})
    steps.append({"key": "transition_fn", "title": "Definition of transition function"})
    steps.append({"key": "final_states", "title": "Definition of final states"})
    for idx, st_obj in enumerate(steps, start=1):
        st_obj["step_num"] = idx
    pipeline_data["steps"] = steps

    final_dfa = {
        "states": dfa_state_labels,
        "alphabet": alphabet,
        "start_state": initial_label,
        "accept_states": dfa_accept_list,
        "transitions": dfa_transitions,
        "nodeBadges": {lbl: f"Q{idx + 1}" for idx, lbl in enumerate(dfa_state_labels)},
    }
    return final_dfa, pipeline_data

def minimize_dfa(dfa_def, alias_map=None):
    """Minimizes DFA using Moore's Equivalence Partitioning with full M2 group-by-group trace."""
    if not dfa_def or not dfa_def.get("states"):
        return None, None, {"sub_steps": [], "is_already_minimal": True}

    states = list(dfa_def["states"])
    accept_set = set(dfa_def["accept_states"])
    non_accept = [s for s in states if s not in accept_set]
    accept = [s for s in states if s in accept_set]
    alphabet = list(dfa_def["alphabet"])
    transitions = dfa_def["transitions"]

    def get_alias(st):
        if alias_map and st in alias_map:
            return alias_map[st]
        return f"Q{states.index(st) + 1}" if st in states else st

    def fmt_compact(st):
        al = get_alias(st)
        return f"{al} {st}" if al != st else st

    sub_steps = []
    partitions = []
    if non_accept:
        partitions.append(non_accept)
    if accept:
        partitions.append(accept)

    p0_palette = {}
    for b_idx, blk in enumerate(partitions):
        pal = GROUP_PALETTE[b_idx % len(GROUP_PALETTE)]
        for st_name in blk:
            p0_palette[st_name] = pal

    sub_steps.append({
        "kind": "init_p0",
        "pill": "1. P0",
        "headline": f"P0 = {{ {', '.join(f'G{i}' for i in range(len(partitions)))} }}",
        "badge": f"{len(partitions)} initial block{'s' if len(partitions) > 1 else ''}",
        "help_tip": (
            "Moore's algorithm starts at P0 by separating non-accepting DFA subsets (K' \\ F') "
            "from accepting subsets (F'). Singleton blocks (1 state) can never split further."
        ),
        "highlight_cfg": {"node_palette_map": p0_palette, "dim_inactive": False},
        "rows": [
            {
                "Block": f"G{b_idx} ({'Final' if all(s in accept_set for s in blk) else 'Non-Final'})",
                "States Qi": ", ".join(get_alias(s) for s in blk),
                "Subsets": ", ".join(blk),
                "Status": f"{len(blk)} states → test" if len(blk) >= 2 else "Singleton (fixed)",
            }
            for b_idx, blk in enumerate(partitions)
        ],
    })

    round_num = 1
    while True:
        if not any(len(p) >= 2 for p in partitions):
            break

        new_partitions = []
        any_split_in_round = False

        for b_idx, part in enumerate(partitions):
            if len(part) < 2:
                new_partitions.append(part)
                continue

            sig_map = {}
            state_details = []
            for st_name in part:
                per_sym = []
                vec = []
                for sym in alphabet:
                    target = transitions.get(st_name, {}).get(sym, "Ø")
                    g_idx = next((i for i, p in enumerate(partitions) if target in p), -1)
                    per_sym.append({"sym": sym, "target": target, "target_alias": get_alias(target), "g_idx": g_idx})
                    vec.append(g_idx)
                vec_t = tuple(vec)
                if vec_t not in sig_map:
                    sig_map[vec_t] = {"vec": vec_t, "members": []}
                sig_map[vec_t]["members"].append(st_name)
                state_details.append({"st": st_name, "alias": get_alias(st_name), "per_sym": per_sym, "vec": vec_t})

            entries = [sig_map[k] for k in sorted(sig_map.keys())]
            did_split = len(entries) > 1
            if did_split:
                any_split_in_round = True
            for entry in entries:
                new_partitions.append(entry["members"])

            splitting_syms = [
                sym for s_idx, sym in enumerate(alphabet)
                if len({e["vec"][s_idx] for e in entries}) > 1
            ]

            step_palette = {}
            for o_idx, other_blk in enumerate(partitions):
                if o_idx == b_idx:
                    continue
                for s in other_blk:
                    step_palette[s] = {"fill": "#f8fafc", "stroke": "#94a3b8", "sw": "1.5"}
            for sub_i, entry in enumerate(entries):
                pal = GROUP_PALETTE[(sub_i + 1) % len(GROUP_PALETTE)] if did_split else GROUP_PALETTE[1]
                for s in entry["members"]:
                    step_palette[s] = pal

            highlight_edges = []
            for d in state_details:
                for ps in d["per_sym"]:
                    if did_split and ps["sym"] in splitting_syms:
                        highlight_edges.append({"src": d["st"], "dest": ps["target"], "symbol": ps["sym"], "role": "move"})
                    elif not did_split:
                        highlight_edges.append({"src": d["st"], "dest": ps["target"], "symbol": ps["sym"], "role": "eps"})

            step_no = len(sub_steps) + 1
            sub_steps.append({
                "kind": "test_block",
                "pill": f"{step_no}. R{round_num}·G{b_idx}",
                "did_split": did_split,
                "headline": f"Round {round_num} · Test G{b_idx} = {{{', '.join(get_alias(s) for s in part)}}}",
                "badge": f"✂️ Split → {len(entries)} groups" if did_split else "✓ Keep together",
                "help_tip": (
                    f"Testing G{b_idx} against Round {round_num - 1} blocks: symbol(s) {', '.join(splitting_syms)} "
                    f"send members into different target blocks, splitting G{b_idx} into {len(entries)} sub-blocks."
                    if did_split
                    else f"Every state in G{b_idx} maps to the exact same Round {round_num - 1} target block on all symbols ({', '.join(alphabet)}), remaining equivalent."
                ),
                "highlight_cfg": {
                    "source_halo_states": list(part),
                    "node_palette_map": step_palette,
                    "edges": highlight_edges,
                    "dim_inactive": True,
                },
                "rows": [
                    {
                        f"Subset(s) in G{b_idx}": ", ".join(fmt_compact(s) for s in entry["members"]),
                        f"Sig ({', '.join(alphabet)})": "(" + ", ".join(f"G{g}" for g in entry["vec"]) + ")",
                        "Outcome": f"Split #{sub_i + 1}" if did_split else "Equivalent",
                    }
                    for sub_i, entry in enumerate(entries)
                ],
            })

        partitions = new_partitions
        if not any_split_in_round:
            break
        round_num += 1

    start_state = dfa_def["start_state"]

    def partition_key(p):
        if start_state in p:
            return (0, 0)
        if len(p) == 1 and p[0] == "Ø":
            return (2, 999999)
        return (1, min((states.index(s) if s in states else 99999) for s in p))

    partitions.sort(key=partition_key)

    def build_min_class_label(sorted_members):
        if len(sorted_members) == 1:
            return sorted_members[0]
        joined_subsets = " ≡ ".join(sorted_members)
        if len(sorted_members) == 2 and len(joined_subsets) <= 22:
            return joined_subsets
        return " ≡ ".join(get_alias(s) for s in sorted_members)

    state_map = {}
    orig_merge_palette = {}
    min_merge_palette = {}
    min_badge_map = {}
    mapping_rows = []
    min_states = []

    for idx, p in enumerate(partitions):
        sorted_members = sorted(list(p), key=lambda s: states.index(s) if s in states else 99999)
        label = build_min_class_label(sorted_members)
        min_states.append(label)
        min_badge_map[label] = "≡".join(get_alias(s) for s in sorted_members)
        for s in sorted_members:
            state_map[s] = label
        if len(sorted_members) >= 2:
            pal = GROUP_PALETTE[idx % len(GROUP_PALETTE)]
            for s in sorted_members:
                orig_merge_palette[s] = pal
            min_merge_palette[label] = pal

        is_start = start_state in sorted_members
        is_acc = any(s in accept_set for s in sorted_members)
        role_tag = (
            "Start, Final" if (is_start and is_acc)
            else ("Start" if is_start else ("Final" if is_acc else ("Trap Ø" if sorted_members == ["Ø"] else ("Merged" if len(sorted_members) >= 2 else "State"))))
        )
        mapping_rows.append({
            "Equivalence Class": f"{label} ({role_tag})",
            "group": label,
            "aliases_equiv": "≡".join(get_alias(s) for s in sorted_members),
            "is_merged": len(sorted_members) >= 2,
            "DFA Subsets": f"{', '.join(get_alias(s) for s in sorted_members)} ({', '.join(sorted_members)})",
        })

    min_start = state_map.get(start_state)
    min_accept = [lbl for lbl in min_states if any(state_map.get(s) == lbl for s in accept)]
    min_trans = {}
    for s in states:
        mapped_src = state_map[s]
        min_trans.setdefault(mapped_src, {})
        for sym in alphabet:
            target = transitions.get(s, {}).get(sym)
            if target and target in state_map:
                min_trans[mapped_src][sym] = state_map[target]

    for r in mapping_rows:
        grp = r["group"]
        r["δ_min"] = ", ".join(f"{sym}→{min_trans.get(grp, {}).get(sym, 'Ø')}" for sym in alphabet)

    min_dfa = {
        "states": min_states,
        "alphabet": alphabet,
        "start_state": min_start,
        "accept_states": min_accept,
        "transitions": min_trans,
        "nodeBadges": min_badge_map,
    }

    is_already_minimal = len(min_states) == len(states)
    merged_aliases = [r["aliases_equiv"] for r in mapping_rows if r["is_merged"]]
    merged_groups = [r["group"] for r in mapping_rows if r["is_merged"]]
    final_step_no = len(sub_steps) + 1

    sub_steps.append({
        "kind": "final_min",
        "pill": f"{final_step_no}. Min DFA",
        "is_already_minimal": is_already_minimal,
        "headline": (
            f"Fixed Point — Already Minimal ({len(min_states)} states)"
            if is_already_minimal
            else f"Fixed Point — Merged {len(states)} ➔ {len(min_states)} states"
        ),
        "badge": "✓ Already Minimal" if is_already_minimal else f"Merged {', '.join(merged_aliases)}",
        "help_tip": (
            f"Every equivalence class is a singleton, so the Converted DFA ({len(states)} states) is already minimal."
            if is_already_minimal
            else f"Equivalent states collapse into merged class(es) {', '.join(merged_groups)} to form the minimal DFA."
        ),
        "orig_highlight_cfg": {
            "source_halo_states": [s for p in partitions if len(p) >= 2 for s in p],
            "node_palette_map": orig_merge_palette,
            "dim_inactive": False,
        },
        "min_highlight_cfg": {
            "node_palette_map": min_merge_palette,
            "dim_inactive": False,
        },
        "rows": [{k: v for k, v in r.items() if k in ("Equivalence Class", "DFA Subsets", "δ_min")} for r in mapping_rows],
    })

    mapping_df = pd.DataFrame([
        {k: v for k, v in r.items() if k in ("Equivalence Class", "DFA Subsets", "δ_min")}
        for r in mapping_rows
    ])
    m2_data = {
        "sub_steps": sub_steps,
        "is_already_minimal": is_already_minimal,
        "orig_count": len(states),
        "min_count": len(min_states),
    }
    return min_dfa, mapping_df, m2_data

def simulate_string(dfa_def, input_string):
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
# 4. VISUALIZATION ENGINE (GRAPHVIZ DOT WITH MULTI-ROLE CUES)
# ==========================================
def wrap_subset_label_for_dot(state_name):
    if len(state_name) <= 12 or "," not in state_name:
        return state_name
    inner = state_name[1:-1] if state_name.startswith("{") and state_name.endswith("}") else state_name
    parts = [p.strip() for p in inner.split(",")]
    if len(parts) <= 3:
        return state_name
    mid = (len(parts) + 1) // 2
    return "{" + ", ".join(parts[:mid]) + ",\n" + ", ".join(parts[mid:]) + "}"

def draw_automaton(automaton_def, name="Automaton", highlighted_states=None, active_edge=None, highlight_cfg=None):
    """Generates styled topological DOT source with multi-role path & partition cues."""
    dot = _DotBuilder(name, graph_attr={
        "rankdir": "LR",
        "bgcolor": "transparent",
        "margin": "0.18",
        "nodesep": "0.82",
        "ranksep": "1.15",
    })
    if not automaton_def or not automaton_def.get("start_state"):
        return dot.source

    cfg = highlight_cfg or {}
    green_states = set(cfg.get("green_states", highlighted_states or []))
    origin_states = set(cfg.get("origin_states", []))
    move_states = set(cfg.get("move_states", []))
    source_halo_states = set(cfg.get("source_halo_states", []))
    node_palette_map = cfg.get("node_palette_map", {})
    cfg_edges = list(cfg.get("edges", []))
    if active_edge:
        cfg_edges.append({"src": active_edge[0], "dest": active_edge[1], "symbol": active_edge[2], "role": "move"})
    dim_inactive = bool(cfg.get("dim_inactive", False))

    dot.node("hidden_start", label="", shape="none", width="0", height="0")
    dot.edge("hidden_start", automaton_def["start_state"], color="#93c5fd" if dim_inactive else "#2563eb", penwidth="2.2")

    for state in automaton_def["states"]:
        is_accept = state in automaton_def["accept_states"]
        shape = "doublecircle" if is_accept else "circle"
        style_parts = ["filled"]
        fontcolor = "#0f172a"

        if state in node_palette_map:
            fillcolor = node_palette_map[state]["fill"]
            color = node_palette_map[state]["stroke"]
            penwidth = node_palette_map[state].get("sw", "2.4")
        elif state in origin_states or state in move_states:
            fillcolor = "#fef08a"
            color = "#ca8a04"
            penwidth = "3.2"
        elif state in green_states:
            fillcolor = "#86efac"
            color = "#15803d"
            penwidth = "3.2"
        elif state in source_halo_states:
            fillcolor = "#dbeafe"
            color = "#2563eb"
            penwidth = "2.6"
            style_parts.append("dashed")
        elif not dim_inactive and state == automaton_def["start_state"]:
            fillcolor = "#dbeafe"
            color = "#1d4ed8"
            penwidth = "2.2"
        elif state == "Ø":
            fillcolor = "#fee2e2"
            color = "#b91c1c"
            penwidth = "1.8"
        else:
            fillcolor = "#ffffff"
            color = "#94a3b8" if dim_inactive else "#64748b"
            penwidth = "1.4"
            if dim_inactive:
                fontcolor = "#64748b"

        if state in source_halo_states and "dashed" not in style_parts:
            color = "#2563eb"

        disp_label = wrap_subset_label_for_dot(state)
        fontsize = "11" if len(state) > 12 else "13"
        dot.node(
            state,
            disp_label,
            shape=shape,
            style=",".join(style_parts),
            fillcolor=fillcolor,
            color=color,
            penwidth=penwidth,
            fontcolor=fontcolor,
            fontname="Arial",
            fontsize=fontsize,
        )

    edge_groups = {}
    for src, transitions in automaton_def["transitions"].items():
        for symbol, dests in transitions.items():
            target_list = dests if isinstance(dests, list) else [dests]
            for dest in target_list:
                edge_groups.setdefault((src, dest), []).append(symbol)

    for (src, dest), symbols in edge_groups.items():
        move_hits = {e["symbol"] for e in cfg_edges if e["src"] == src and e["dest"] == dest and e["role"] == "move"}
        eps_hits = {e["symbol"] for e in cfg_edges if e["src"] == src and e["dest"] == dest and e["role"] == "eps"}

        if any(s in move_hits for s in symbols):
            edge_color = "#dc2626"
            edge_width = "3.1"
            fcolor = "#dc2626"
        elif any(s in eps_hits for s in symbols):
            edge_color = "#16a34a"
            edge_width = "3.0"
            fcolor = "#15803d"
        elif dim_inactive:
            edge_color = "#cbd5e1"
            edge_width = "1.2"
            fcolor = "#94a3b8"
        else:
            edge_color = "#475569"
            edge_width = "1.5"
            fcolor = "#0f172a"

        label_str = ", ".join("ε" if s == "e" else s for s in symbols)
        dot.edge(
            src,
            dest,
            label=f" {label_str} ",
            fontcolor=fcolor,
            color=edge_color,
            penwidth=edge_width,
            fontname="Arial",
            fontsize="12",
        )
    return dot.source

# ==========================================
# 5. USER INTERFACE ARCHITECTURE (COMPACT + (?) TOOLTIPS)
# ==========================================
def main():
    hdr_col1, hdr_col2 = st.columns([4, 1])
    with hdr_col1:
        st.title(
            "🧠 Automata Studio",
            help=(
                "Interactive NFA → DFA conversion laboratory aligned with Lecture 5 (Slide 100): "
                "automatic 4/5-step detection, E-set & δ path highlighting, character-by-character string tracing, "
                "and an optional DFA Minimization extension."
            ),
        )
    with hdr_col2:
        st.write("")
        st.caption(f"Actions: `{len(st.session_state.user_actions_log)}`")

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
        st.header("📚 Presets")
        scenario_options = ["Custom Automaton"] + list(PREBUILT_SCENARIOS.keys())
        scenario_choice = st.selectbox(
            "Preset",
            scenario_options,
            key="scenario_choice_key",
            label_visibility="collapsed",
        )

        if scenario_choice != st.session_state.last_loaded_scenario:
            st.session_state.last_loaded_scenario = scenario_choice
            st.session_state.sim_step_index = 0
            st.session_state.conv_stage_index = 0
            st.session_state.eset_sub_index = 0
            st.session_state.trans_sub_index = 0
            st.session_state.min_sub_index = 0
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
            st.info(f"ℹ️ **{preset['description']}**")
        else:
            preset = None
            def_states = "q1, q2, q3"
            def_alpha = "a, b, e"
            def_start = "q1"
            def_acc = ["q3"]
            st.caption(
                "ℹ️ **Custom Automaton**",
                help="Build your own NFA below using single-symbol, ε ('e'), or multi-symbol string edges (e.g. 'ab').",
            )

        rc = st.session_state.reset_counter
        st.subheader(
            "NFA Tuple (K, Σ, Δ, s, F)",
            help="Define finite states K (comma-separated) and single-character alphabet Σ (use 'e' for empty transition ε).",
        )
        raw_states = st.text_input("States K", value=def_states, key=f"states_in_{scenario_choice}_{rc}")
        states_list = list(dict.fromkeys(s.strip() for s in raw_states.split(",") if s.strip()))

        raw_alphabet = st.text_input("Alphabet Σ ('e' = ε)", value=def_alpha, key=f"alpha_in_{scenario_choice}_{rc}")
        alphabet_list = list(dict.fromkeys(a.strip() for a in raw_alphabet.split(",") if a.strip()))

        start_state = st.selectbox(
            "Initial State (s)",
            options=states_list,
            index=states_list.index(def_start) if def_start in states_list else 0,
            key=f"start_sel_{scenario_choice}_{rc}",
        ) if states_list else None

        accept_states = st.multiselect(
            "Final States (F)",
            options=states_list,
            default=[a for a in def_acc if a in states_list],
            key=f"acc_sel_{scenario_choice}_{rc}",
        )

        st.divider()
        st.markdown(
            "#### Single-Symbol & ε Edges",
            help="Expand any state qi below to toggle outgoing transitions for individual symbols in Σ or ε ('e').",
        )
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
                        key=f"trans_{scenario_choice}_{rc}_{state}_{sym}",
                    )
                    if selected:
                        single_transitions[state][sym] = selected

        st.divider()
        st.markdown(
            "#### String Transitions (|w| ≥ 2)",
            help="Add multi-symbol string arcs (e.g. ab, aa, ba, bb). When ≥ 1 string arc exists, Slide 100 Step 1 splits it automatically.",
        )

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
        single_transitions, st.session_state.string_transitions_list,
    )
    expanded_nfa, split_log, introduced_states = expand_string_transitions(
        states_list, alphabet_list, start_state, accept_states,
        single_transitions, st.session_state.string_transitions_list,
    )
    dfa_def, pipeline_data = nfa_to_dfa_slide100_pipeline(
        original_nfa, expanded_nfa, split_log, introduced_states,
    )
    min_dfa_def, min_mapping, min_m2_data = minimize_dfa(dfa_def, pipeline_data["q_aliases"])

    # ==========================================
    # 6. MAIN APPLICATION TABS (STRICTLY 3 TABS)
    # ==========================================
    tab_pipeline, tab_stepper, tab_telemetry = st.tabs([
        "📊 1. NFA ➔ DFA Conversion",
        "⏯️ 2. String Stepper",
        "📋 3. Research Telemetry",
    ])

    # --- TAB 1: CONVERSION PIPELINE + SINGLE-CHECKBOX EXTENSION ---
    with tab_pipeline:
        tbar1, tbar2 = st.columns([1.5, 1.5])
        with tbar1:
            view_mode = st.radio(
                "Mode",
                ["Step-by-Step", "Overview"],
                horizontal=True,
                key="pipeline_view_mode_radio",
                label_visibility="collapsed",
            )
        with tbar2:
            show_min_dfa = st.checkbox(
                "🧩 Extension: DFA Minimization",
                key="show_optional_min_dfa",
                help=(
                    "Single-click extension toggle: when unchecked, runs the pure 4–5 step Lecture 5 NFA → DFA workflow; "
                    "when checked, appends group-by-group Moore DFA Minimization (P0 → Pr → Minimized DFA)."
                ),
            )

        steps_list = pipeline_data["steps"]
        max_stage = len(steps_list) + (1 if show_min_dfa else 0)
        st.session_state.conv_stage_index = min(st.session_state.conv_stage_index, max_stage)
        stage_idx = st.session_state.conv_stage_index

        if view_mode == "Step-by-Step":
            short_map = {
                "string_elim": "Eliminate Strings",
                "e_sets": "E-sets",
                "initial_state": "Initial State",
                "transition_fn": "Transition δ",
                "final_states": "Final States & DFA",
            }
            stage_pills = ["Given NFA M"] + [f"Step {s['step_num']}: {short_map.get(s['key'], s['title'])}" for s in steps_list]
            if show_min_dfa:
                stage_pills.append("🧩 Ext: Minimize DFA")

            nav1, nav2, nav3, nav4 = st.columns([1, 1, 1, 2.5])
            with nav1:
                if st.button("⏮️ Given NFA", use_container_width=True):
                    st.session_state.conv_stage_index = 0
                    st.session_state.eset_sub_index = 0
                    st.session_state.trans_sub_index = 0
                    st.session_state.min_sub_index = 0
                    log_action("conv_step_reset")
                    st.rerun()
            with nav2:
                if st.button("◀️ Prev", use_container_width=True, disabled=(stage_idx == 0)):
                    active_s = steps_list[stage_idx - 1] if 1 <= stage_idx <= len(steps_list) else None
                    if active_s and active_s["key"] == "e_sets" and isinstance(st.session_state.eset_sub_index, int) and st.session_state.eset_sub_index > 0:
                        st.session_state.eset_sub_index -= 1
                    elif active_s and active_s["key"] == "transition_fn" and isinstance(st.session_state.trans_sub_index, int) and st.session_state.trans_sub_index > 0:
                        st.session_state.trans_sub_index -= 1
                    elif show_min_dfa and stage_idx == len(steps_list) + 1 and isinstance(st.session_state.min_sub_index, int) and st.session_state.min_sub_index > 0:
                        st.session_state.min_sub_index -= 1
                    else:
                        st.session_state.conv_stage_index = max(0, stage_idx - 1)
                    log_action("conv_step_prev", f"Stage_{st.session_state.conv_stage_index}")
                    st.rerun()
            with nav3:
                active_s = steps_list[stage_idx - 1] if 1 <= stage_idx <= len(steps_list) else None
                min_total = len(min_m2_data["sub_steps"]) if min_m2_data else 0
                on_last_sub = True
                if active_s and active_s["key"] == "e_sets":
                    on_last_sub = (st.session_state.eset_sub_index == "all") or (st.session_state.eset_sub_index >= len(pipeline_data["e_sets_rows"]) - 1)
                elif active_s and active_s["key"] == "transition_fn":
                    on_last_sub = (st.session_state.trans_sub_index == "all") or (st.session_state.trans_sub_index >= len(pipeline_data["transitions_log"]) - 1)
                elif show_min_dfa and stage_idx == len(steps_list) + 1:
                    on_last_sub = (st.session_state.min_sub_index == "all") or (st.session_state.min_sub_index >= min_total - 1)
                at_end = (stage_idx >= max_stage) and on_last_sub

                if st.button("Next ▶️", use_container_width=True, type="primary", disabled=at_end):
                    if active_s and active_s["key"] == "e_sets" and st.session_state.eset_sub_index != "all" and st.session_state.eset_sub_index < len(pipeline_data["e_sets_rows"]) - 1:
                        st.session_state.eset_sub_index += 1
                    elif active_s and active_s["key"] == "transition_fn" and st.session_state.trans_sub_index != "all" and st.session_state.trans_sub_index < len(pipeline_data["transitions_log"]) - 1:
                        st.session_state.trans_sub_index += 1
                    elif show_min_dfa and stage_idx == len(steps_list) + 1 and st.session_state.min_sub_index != "all" and st.session_state.min_sub_index < min_total - 1:
                        st.session_state.min_sub_index += 1
                    else:
                        st.session_state.conv_stage_index = min(max_stage, stage_idx + 1)
                        st.session_state.eset_sub_index = 0
                        st.session_state.trans_sub_index = 0
                        st.session_state.min_sub_index = 0
                    log_action("conv_step_next", f"Stage_{st.session_state.conv_stage_index}")
                    st.rerun()
            with nav4:
                picked_stage = st.selectbox(
                    "Jump to Stage",
                    options=list(range(len(stage_pills))),
                    index=stage_idx,
                    format_func=lambda i: stage_pills[i],
                    label_visibility="collapsed",
                )
                if picked_stage != stage_idx:
                    st.session_state.conv_stage_index = picked_stage
                    st.session_state.eset_sub_index = 0
                    st.session_state.trans_sub_index = 0
                    st.session_state.min_sub_index = 0
                    log_action("conv_stage_goto", stage_pills[picked_stage])
                    st.rerun()

            if stage_idx == 0:
                c_left, c_right = st.columns([1.15, 1])
                with c_left:
                    st.markdown(f"**Given NFA M** (`{len(original_nfa['states'])} states`)")
                    st.graphviz_chart(draw_automaton(original_nfa, "Given_NFA"), use_container_width=True)
                with c_right:
                    detect_help = (
                        "Auto-detected multi-symbol string transition(s) → executing all 5 Slide 100 steps."
                        if pipeline_data["has_string_splits"]
                        else "No multi-symbol string transitions → string splitting skipped automatically (4 steps, matching Example 3)."
                    )
                    st.markdown(f"**Slide 100 Steps ({len(steps_list)})**", help=detect_help)
                    for s_obj in steps_list:
                        st.markdown(f"{s_obj['step_num']}. {s_obj['title']}")

            elif stage_idx <= len(steps_list):
                active_step = steps_list[stage_idx - 1]

                if active_step["key"] == "string_elim":
                    sc_left, sc_right = st.columns(2)
                    with sc_left:
                        st.markdown(f"**Given NFA M** (`{len(original_nfa['states'])} states`)")
                        st.graphviz_chart(draw_automaton(original_nfa, "Orig_NFA_Step1"), use_container_width=True)
                    with sc_right:
                        st.markdown(
                            f"**Single-Symbol NFA** (`{len(expanded_nfa['states'])} states`)",
                            help="Multi-symbol edges (k ≥ 2) are decomposed into single-symbol chains by introducing k − 1 fresh states.",
                        )
                        st.graphviz_chart(
                            draw_automaton(expanded_nfa, "Exp_NFA_Step1", highlighted_states=introduced_states),
                            use_container_width=True,
                        )
                    st.dataframe(pd.DataFrame(split_log), hide_index=True, use_container_width=True)

                elif active_step["key"] == "e_sets":
                    rows = pipeline_data["e_sets_rows"]
                    sub_options = [f"E({r['state']})" for r in rows] + ["📋 All"]
                    cur_sub = len(rows) if st.session_state.eset_sub_index == "all" else min(len(rows) - 1, int(st.session_state.eset_sub_index))
                    picked_eset = st.radio(
                        "E-set Sub-step",
                        options=list(range(len(sub_options))),
                        index=cur_sub,
                        format_func=lambda i: sub_options[i],
                        horizontal=True,
                        label_visibility="collapsed",
                    )
                    new_eset_val = "all" if picked_eset == len(rows) else picked_eset
                    if new_eset_val != st.session_state.eset_sub_index:
                        st.session_state.eset_sub_index = new_eset_val
                        log_action("select_eset_substep", str(new_eset_val))
                        st.rerun()

                    sc_left, sc_right = st.columns([1.1, 1.15])
                    if st.session_state.eset_sub_index == "all":
                        h_cfg = {}
                    else:
                        arow = rows[st.session_state.eset_sub_index]
                        h_cfg = {
                            "origin_states": [arow["state"]],
                            "green_states": arow["eps_reached_states"],
                            "edges": arow["eps_edges"],
                            "dim_inactive": True,
                        }
                    with sc_left:
                        st.graphviz_chart(draw_automaton(expanded_nfa, "Ref_NFA_Esets", highlight_cfg=h_cfg), use_container_width=True)
                        st.caption("🟡 Origin `qi`  |  🟢 `ε`-Closure")
                    with sc_right:
                        if st.session_state.eset_sub_index != "all":
                            arow = rows[st.session_state.eset_sub_index]
                            hops_str = "∅ ε-out" if not arow["hops"] else ", ".join(f"{h['from']}→{h['to']}" for h in arow["hops"])
                            st.markdown(
                                f"**[{st.session_state.eset_sub_index + 1}/{len(rows)}] `{arow['formula']}`**  \n"
                                f"`{arow['state']} ──ε*──▶ {hops_str}`",
                                help="E(qi) is the reflexive-transitive ε-closure: all states reachable from qi via 0 or more ε-transitions.",
                            )
                        df_esets = pd.DataFrame([{"State": r["state"], "E-set": r["formula"]} for r in rows])
                        st.dataframe(df_esets, hide_index=True, use_container_width=True)

                elif active_step["key"] == "initial_state":
                    sc_left, sc_right = st.columns([1.15, 1])
                    init_cfg = {
                        "origin_states": [start_state],
                        "green_states": [x for x in pipeline_data["initial_state_members"] if x != start_state],
                        "edges": pipeline_data["initial_state_eps_edges"],
                        "dim_inactive": True,
                    }
                    with sc_left:
                        st.graphviz_chart(draw_automaton(expanded_nfa, "Ref_NFA_Init", highlight_cfg=init_cfg), use_container_width=True)
                    with sc_right:
                        st.markdown(
                            f"**`{pipeline_data['initial_state_formula']}`**",
                            help=f"The DFA start state s' is the E-set of NFA start state {start_state}, labeled Q1.",
                        )

                elif active_step["key"] == "transition_fn":
                    t_rows = pipeline_data["transitions_log"]
                    t_opts = [f"{i + 1}.{r['curr_alias']}·{r['symbol']}" for i, r in enumerate(t_rows)] + ["📋 All"]
                    cur_t = len(t_rows) if st.session_state.trans_sub_index == "all" else min(len(t_rows) - 1, int(st.session_state.trans_sub_index))
                    picked_t = st.selectbox(
                        "Transition δ Sub-step",
                        options=list(range(len(t_opts))),
                        index=cur_t,
                        format_func=lambda i: t_opts[i],
                        label_visibility="collapsed",
                    )
                    new_t_val = "all" if picked_t == len(t_rows) else picked_t
                    if new_t_val != st.session_state.trans_sub_index:
                        st.session_state.trans_sub_index = new_t_val
                        log_action("select_trans_substep", str(new_t_val))
                        st.rerun()

                    sc_left, sc_right = st.columns([1.05, 1.3])
                    if st.session_state.trans_sub_index == "all":
                        h_cfg = {}
                    else:
                        tr = t_rows[st.session_state.trans_sub_index]
                        h_cfg = {
                            "source_halo_states": tr["curr_members"],
                            "move_states": tr["move_states"],
                            "green_states": tr["eps_only_states"],
                            "edges": tr["move_edges"] + tr["eps_edges"],
                            "dim_inactive": True,
                        }
                    with sc_left:
                        st.graphviz_chart(draw_automaton(expanded_nfa, "Ref_NFA_Trans", highlight_cfg=h_cfg), use_container_width=True)
                        st.caption("🔵 Source `S`  |  🔴 `Move(σ)`  |  🟢 `ε`-Closure")
                    with sc_right:
                        if st.session_state.trans_sub_index != "all":
                            tr = t_rows[st.session_state.trans_sub_index]
                            badge = f"🆕 {tr['target_alias']}" if tr["is_newly_discovered"] else f"↪ {tr['target_alias']}"
                            move_txt = (
                                "∅ ⇒ Ø" if not tr["move_hops"]
                                else f"{', '.join(h['from'] + '→' + h['to'] for h in tr['move_hops'])} ⇒ {{{', '.join(tr['move_states'])}}}"
                            )
                            st.markdown(
                                f"**[{st.session_state.trans_sub_index + 1}/{len(t_rows)}] `δ({tr['curr_alias']}, {tr['symbol']})`** — `{badge}`  \n"
                                f"- `S = {tr['curr_alias']}` : `{tr['curr_label']}`  \n"
                                f"- `Move({tr['symbol']})` : `{move_txt}`  \n"
                                f"- `∪ E-set` : `{tr['Slide Formula']}`",
                                help="Follow direct symbol edges from S (red arrows to yellow nodes), then take the union of their E-sets (green ε-closure).",
                            )
                        st.dataframe(pd.DataFrame(t_rows)[["Slide Formula"]], hide_index=True, use_container_width=True)

                elif active_step["key"] == "final_states":
                    fc_left, fc_right = st.columns([1.5, 1])
                    with fc_left:
                        st.markdown(f"**Converted DFA** (`{len(dfa_def['states'])} states`)")
                        st.graphviz_chart(
                            draw_automaton(dfa_def, "Result_DFA", highlighted_states=[s for s in dfa_def["accept_states"] if s != dfa_def["start_state"]]),
                            use_container_width=True,
                        )
                    with fc_right:
                        st.markdown(
                            f"**`{pipeline_data['final_states_formula']}`**",
                            help="Every DFA subset Qi containing at least one original NFA final state (Qi ∩ F ≠ Ø) is marked accepting.",
                        )
                        summary_rows = []
                        for idx_s, st_lbl in enumerate(dfa_def["states"]):
                            row_d = {"Qi": f"Q{idx_s + 1}", "Subset": st_lbl}
                            for sym in dfa_def["alphabet"]:
                                dst = dfa_def["transitions"].get(st_lbl, {}).get(sym, "Ø")
                                row_d[f"δ(Qi,{sym})"] = f"{pipeline_data['q_aliases'].get(dst, '')} ({dst})".strip()
                            summary_rows.append(row_d)
                        st.dataframe(pd.DataFrame(summary_rows), hide_index=True, use_container_width=True)

            elif show_min_dfa and min_dfa_def and min_m2_data:
                m_steps = min_m2_data["sub_steps"]
                m_opts = [s["pill"] for s in m_steps] + ["📋 All"]
                cur_m = len(m_steps) if st.session_state.min_sub_index == "all" else min(len(m_steps) - 1, int(st.session_state.min_sub_index))
                picked_m = st.radio(
                    "M2 Minimization Sub-step",
                    options=list(range(len(m_opts))),
                    index=cur_m,
                    format_func=lambda i: m_opts[i],
                    horizontal=True,
                    label_visibility="collapsed",
                )
                new_m_val = "all" if picked_m == len(m_steps) else picked_m
                if new_m_val != st.session_state.min_sub_index:
                    st.session_state.min_sub_index = new_m_val
                    log_action("ext_min_dfa_substep", str(new_m_val))
                    st.rerun()

                active_m = m_steps[-1] if st.session_state.min_sub_index == "all" else m_steps[st.session_state.min_sub_index]
                st.markdown(
                    f"**`{active_m['headline']}`** — `{active_m['badge']}`",
                    help=active_m["help_tip"],
                )
                if st.session_state.min_sub_index == "all" or active_m["kind"] == "final_min":
                    fin = m_steps[-1]
                    mc1, mc2 = st.columns(2)
                    with mc1:
                        st.markdown(f"**Converted DFA M'** (`{len(dfa_def['states'])} states`)")
                        st.graphviz_chart(draw_automaton(dfa_def, "Orig_DFA_Min", highlight_cfg=fin["orig_highlight_cfg"]), use_container_width=True)
                    with mc2:
                        st.markdown(f"**Minimized DFA** (`{len(min_dfa_def['states'])} states`)")
                        st.graphviz_chart(draw_automaton(min_dfa_def, "Final_Min_DFA", highlight_cfg=fin["min_highlight_cfg"]), use_container_width=True)
                    st.dataframe(pd.DataFrame(fin["rows"]), hide_index=True, use_container_width=True)
                else:
                    mc1, mc2 = st.columns([1.1, 1.15])
                    with mc1:
                        st.graphviz_chart(draw_automaton(dfa_def, "Step_M2_DFA", highlight_cfg=active_m["highlight_cfg"]), use_container_width=True)
                    with mc2:
                        st.dataframe(pd.DataFrame(active_m["rows"]), hide_index=True, use_container_width=True)

        else:
            # Overview Mode
            num_graph_cols = 2 + (1 if pipeline_data["has_string_splits"] else 0) + (1 if show_min_dfa else 0)
            gcols = st.columns(num_graph_cols)
            col_ptr = 0

            with gcols[col_ptr]:
                st.markdown(f"**Given NFA M** (`{len(original_nfa['states'])} states`)")
                st.graphviz_chart(draw_automaton(original_nfa, "Overview_Orig_NFA"), use_container_width=True)
            col_ptr += 1

            if pipeline_data["has_string_splits"]:
                with gcols[col_ptr]:
                    st.markdown(f"**Single-Symbol NFA** (`{len(expanded_nfa['states'])} states`)")
                    st.graphviz_chart(draw_automaton(expanded_nfa, "Overview_Exp_NFA", highlighted_states=introduced_states), use_container_width=True)
                col_ptr += 1

            with gcols[col_ptr]:
                st.markdown(f"**Converted DFA M'** (`{len(dfa_def['states'])} states`)")
                st.graphviz_chart(draw_automaton(dfa_def, "Overview_DFA"), use_container_width=True)
            col_ptr += 1

            if show_min_dfa and min_dfa_def:
                with gcols[col_ptr]:
                    st.markdown(f"**🧩 Minimized DFA** (`{len(min_dfa_def['states'])} states`)")
                    st.graphviz_chart(draw_automaton(min_dfa_def, "Overview_Min_DFA"), use_container_width=True)

            st.markdown("#### Derivations (Slide 100)")
            for s_obj in steps_list:
                with st.expander(f"Step {s_obj['step_num']}: {s_obj['title']}", expanded=True):
                    if s_obj["key"] == "string_elim":
                        st.dataframe(pd.DataFrame(split_log), hide_index=True, use_container_width=True)
                    elif s_obj["key"] == "e_sets":
                        st.dataframe(pd.DataFrame([{"State": r["state"], "E-set": r["formula"]} for r in pipeline_data["e_sets_rows"]]), hide_index=True, use_container_width=True)
                    elif s_obj["key"] == "initial_state":
                        st.markdown(f"`{pipeline_data['initial_state_formula']}`")
                    elif s_obj["key"] == "transition_fn":
                        st.dataframe(pd.DataFrame(pipeline_data["transitions_log"])[["Slide Formula"]], hide_index=True, use_container_width=True)
                    elif s_obj["key"] == "final_states":
                        st.markdown(f"`{pipeline_data['final_states_formula']}`")

            if show_min_dfa and min_mapping is not None:
                with st.expander(f"🧩 Extension: DFA Minimization ({len(dfa_def['states'])} ➔ {len(min_dfa_def['states'])} states)", expanded=True):
                    st.dataframe(min_mapping, hide_index=True, use_container_width=True)

    # --- TAB 2: STEP-BY-STEP STRING STEPPER ---
    with tab_stepper:
        st.markdown(
            "### String Stepper",
            help="Trace how the Converted DFA (or Minimized DFA when the Extension is enabled) processes an input string character-by-character.",
        )

        sim_cols = st.columns([2, 1])
        with sim_cols[0]:
            target_str = st.text_input(
                "Input String to Trace:",
                placeholder="Enter a string over Σ (e.g., abba)...",
                key="stepper_str_input",
            ).strip()
        with sim_cols[1]:
            if st.session_state.show_optional_min_dfa:
                machine_target = st.radio(
                    "Target Automaton:",
                    ["Converted DFA", "Minimized DFA"],
                    horizontal=True,
                    key="stepper_target_radio",
                )
            else:
                machine_target = "Converted DFA"
                st.markdown("**Target Automaton:** `Converted DFA`")
            chosen_machine = min_dfa_def if (machine_target == "Minimized DFA" and min_dfa_def) else dfa_def

        if is_blank_custom and not target_str:
            st.info("ℹ️ Add transitions in the sidebar and enter a test string above to trace execution.")
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

                st_gcol, st_tcol = st.columns([1.5, 1])
                with st_gcol:
                    st.graphviz_chart(
                        draw_automaton(chosen_machine, "Stepper_Graph", highlighted_states=[current_state], active_edge=active_edge_tuple),
                        use_container_width=True,
                    )
                with st_tcol:
                    cfg_rows = []
                    for idx_p, (p_st, p_sym) in enumerate(path):
                        unread = target_str[idx_p:] if idx_p < len(target_str) else "ε"
                        cfg_rows.append({
                            "Step": idx_p,
                            "Configuration (q, w)": f"({p_st}, {unread or 'ε'})",
                            "Transition δ": "Initial" if idx_p == 0 else f"δ({path[idx_p - 1][0]}, {p_sym}) → {p_st}",
                        })
                    st.dataframe(pd.DataFrame(cfg_rows), hide_index=True, use_container_width=True)

                if current_idx == max_steps:
                    disp_str = target_str if target_str else "ε"
                    if is_acc:
                        st.success(f"🎉 Simulation Complete: The string '{disp_str}' is **ACCEPTED** (Ended in final state `{current_state}`).")
                    else:
                        st.error(f"🛑 Simulation Complete: The string '{disp_str}' is **REJECTED** (Ended in non-final state `{current_state}`).")

    # --- TAB 3: RESEARCH TELEMETRY & AUDIT ---
    with tab_telemetry:
        st.markdown("### 📋 Educational Interaction Telemetry")
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
            "recent_actions": st.session_state.user_actions_log[-10:],
        }

        st.markdown("#### Session Verification Code")
        st.code(json.dumps(telemetry_payload, indent=2), language="json")

        if st.checkbox("Show Detailed Action Event Log"):
            if st.session_state.user_actions_log:
                st.dataframe(pd.DataFrame(st.session_state.user_actions_log), hide_index=True, use_container_width=True)
            else:
                st.info("No interaction events recorded yet in this session.")

if __name__ == "__main__":
    main()
