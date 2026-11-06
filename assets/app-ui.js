function clearStringRuleError() {
const box = document.getElementById("stringRuleErrorBox");
if (box) { box.textContent = ""; box.classList.add("hidden"); }
}
function addStringTransitionRule() {
clearStringRuleError();
const fromSt = document.getElementById("strFromSelect").value;
const lbl = document.getElementById("strLabelInput").value.trim();
const toSt = document.getElementById("strToSelect").value;
const candidate = [{ from: fromSt, label: lbl, to: toSt }];
const errs = validateAlphabetAndStrings(appState.alphabet, appState.states, candidate);
if (errs.length > 0) {
const box = document.getElementById("stringRuleErrorBox");
box.textContent = errs[0];
box.classList.remove("hidden");
return;
}
const exists = appState.stringTransitions.some(r => r.from === fromSt && r.label === lbl && r.to === toSt);
if (!exists) {
appState.stringTransitions.push({ from: fromSt, label: lbl, to: toSt });
document.getElementById("strLabelInput").value = "";
appState.convStageIndex = 0;
appState.eSetSubIndex = 0;
appState.transSubIndex = 0;
logAction("add_string_transition", `${fromSt}--${lbl}-->${toSt}`);
rebuildSidebarControls();
recomputeAndRenderAll();
}
}
function removeStringTransitionRule(idx) {
const removed = appState.stringTransitions.splice(idx, 1)[0];
appState.convStageIndex = 0;
appState.eSetSubIndex = 0;
appState.transSubIndex = 0;
if (removed) logAction("remove_string_transition", `${removed.from}--${removed.label}-->${removed.to}`);
rebuildSidebarControls();
recomputeAndRenderAll();
}
function loadPreset(presetName) {
appState.presetName = presetName;
clearStringRuleError();
const descBox = document.getElementById("scenarioDescriptionBox");
if (presetName !== "Custom Automaton" && PREBUILT_SCENARIOS[presetName]) {
const p = PREBUILT_SCENARIOS[presetName];
document.getElementById("statesInput").value = p.states;
document.getElementById("alphabetInput").value = p.alphabet;
appState.states = p.states.split(",").map(s => s.trim()).filter(Boolean);
appState.alphabet = p.alphabet.split(",").map(s => s.trim()).filter(Boolean);
appState.startState = p.start;
appState.acceptStates = [...p.accept];
appState.transitions = JSON.parse(JSON.stringify(p.transitions));
appState.stringTransitions = p.stringTransitions.map(r => ({ ...r }));
appState.openBuilderStates = new Set(appState.states);
document.getElementById("stepperStringInput").value = p.sampleStr || "";
descBox.innerHTML = `ℹ️ <strong>${escapeHtml(p.description)}</strong>`;
} else {
appState.states = ["q1", "q2", "q3"];
appState.alphabet = ["a", "b", "e"];
appState.startState = "q1";
appState.acceptStates = ["q3"];
appState.transitions = { "q1": {}, "q2": {}, "q3": {} };
appState.stringTransitions = [];
appState.openBuilderStates = new Set();
document.getElementById("statesInput").value = "q1, q2, q3";
document.getElementById("alphabetInput").value = "a, b, e";
document.getElementById("stepperStringInput").value = "";
descBox.innerHTML = `ℹ️ <strong>Custom Automaton</strong> ${renderHelpBadge("Build your own NFA below using single-symbol, <code>ε</code>, or multi-symbol string edges (e.g. <code>ab</code>), then step through its DFA conversion.", "custom_mode_note", true)}`;
}
appState.simStepIndex = 0;
appState.convStageIndex = 0;
appState.eSetSubIndex = 0;
appState.transSubIndex = 0;
appState.minSubIndex = 0;
appState.customNodePositions = {};
appState.graphCameras = {};
rebuildSidebarControls();
recomputeAndRenderAll();
}
function rebuildSidebarControls() {
const startSel = document.getElementById("startStateSelect");
const strFromSel = document.getElementById("strFromSelect");
const strToSel = document.getElementById("strToSelect");
const prevFrom = strFromSel.value;
const prevTo = strToSel.value;
startSel.innerHTML = "";
strFromSel.innerHTML = "";
strToSel.innerHTML = "";
appState.states.forEach((st, idx) => {
const opt = document.createElement("option");
opt.value = st; opt.textContent = st;
if (st === appState.startState) opt.selected = true;
startSel.appendChild(opt);
const of = document.createElement("option");
of.value = st; of.textContent = st;
if (st === prevFrom || (!prevFrom && idx === 0)) of.selected = true;
strFromSel.appendChild(of);
const ot = document.createElement("option");
ot.value = st; ot.textContent = st;
if (st === prevTo || (!prevTo && idx === appState.states.length - 1)) ot.selected = true;
strToSel.appendChild(ot);
});
const accContainer = document.getElementById("acceptStatesContainer");
accContainer.innerHTML = "";
appState.states.forEach(st => {
const isAcc = appState.acceptStates.includes(st);
const btn = document.createElement("button");
btn.type = "button";
btn.className = `st-tag ${isAcc ? "selected" : ""}`;
btn.textContent = isAcc ? `${st} ×` : `+ ${st}`;
btn.addEventListener("click", () => {
if (appState.acceptStates.includes(st)) {
appState.acceptStates = appState.acceptStates.filter(x => x !== st);
} else {
appState.acceptStates.push(st);
}
logAction("toggle_accept_state", st);
rebuildSidebarControls();
recomputeAndRenderAll();
});
accContainer.appendChild(btn);
});
const transBuilder = document.getElementById("transitionsBuilderContainer");
transBuilder.innerHTML = "";
appState.states.forEach(st => {
if (!appState.transitions[st]) appState.transitions[st] = {};
const det = document.createElement("details");
det.className = "st-expander";
if (appState.openBuilderStates.has(st)) det.open = true;
det.addEventListener("toggle", () => {
if (det.open) appState.openBuilderStates.add(st);
else appState.openBuilderStates.delete(st);
});
const sum = document.createElement("summary");
sum.textContent = `Transitions from '${st}'`;
det.appendChild(sum);
const body = document.createElement("div");
body.className = "st-expander-content";
appState.alphabet.forEach(sym => {
const blk = document.createElement("div");
blk.className = "trans-rule-block";
const lbl = document.createElement("div");
lbl.className = "trans-rule-lbl";
lbl.textContent = `Read '${sym === "e" ? "ε (e)" : sym}' ➔ Go to:`;
blk.appendChild(lbl);
const targetsWrap = document.createElement("div");
targetsWrap.className = "st-multiselect-box";
const currentTargets = appState.transitions[st][sym] || [];
appState.states.forEach(targetSt => {
const active = currentTargets.includes(targetSt);
const chip = document.createElement("button");
chip.type = "button";
chip.className = `st-tag ${active ? "selected" : ""}`;
chip.textContent = active ? `${targetSt} ×` : `+ ${targetSt}`;
chip.addEventListener("click", () => {
const arr = appState.transitions[st][sym] || [];
if (arr.includes(targetSt)) {
appState.transitions[st][sym] = arr.filter(x => x !== targetSt);
} else {
appState.transitions[st][sym] = [...arr, targetSt];
}
logAction("toggle_transition", `${st} --${sym}--> ${targetSt}`);
rebuildSidebarControls();
recomputeAndRenderAll();
});
targetsWrap.appendChild(chip);
});
blk.appendChild(targetsWrap);
body.appendChild(blk);
});
det.appendChild(body);
transBuilder.appendChild(det);
});
const strListEl = document.getElementById("stringRulesListContainer");
appState.stringTransitions = appState.stringTransitions.filter(
r => appState.states.includes(r.from) && appState.states.includes(r.to)
);
if (appState.stringTransitions.length === 0) {
strListEl.innerHTML = `<div style="font-size:0.82rem;color:var(--st-muted);font-style:italic;">No multi-symbol string transitions active.</div>`;
} else {
strListEl.innerHTML = appState.stringTransitions.map((r, idx) => `
<div class="str-rule-item">
<span>${escapeHtml(r.from)} ──${escapeHtml(r.label)}──▶ ${escapeHtml(r.to)}</span>
<button type="button" class="str-rule-del" onclick="removeStringTransitionRule(${idx})" title="Remove string transition">✕</button>
</div>
`).join("");
}
}
function setESetSubStep(val) {
appState.eSetSubIndex = val;
logAction("select_eset_substep", String(val));
renderPipelineTab();
}
function setTransSubStep(val) {
appState.transSubIndex = val;
logAction("select_trans_substep", String(val));
renderPipelineTab();
}
function setMinSubStep(val) {
appState.minSubIndex = val;
logAction("ext_min_dfa_substep", String(val));
renderPipelineTab();
}
function getActiveStepObject() {
const pd = appState.pipelineData;
if (!pd) return null;
const idx = appState.convStageIndex;
if (idx >= 1 && idx <= pd.steps.length) return pd.steps[idx - 1];
return null;
}
function isOnMinExtensionStage() {
const pd = appState.pipelineData;
if (!pd || !appState.showOptionalMinDfa) return false;
return appState.convStageIndex === pd.steps.length + 1;
}
function convStepAction(type, explicitIdx = null) {
const pd = appState.pipelineData;
if (!pd) return;
const steps = pd.steps;
const maxStage = steps.length + (appState.showOptionalMinDfa ? 1 : 0);
const activeStep = getActiveStepObject();
const onMinExt = isOnMinExtensionStage();
const minTotal = (appState.minM2Data && appState.minM2Data.subSteps) ? appState.minM2Data.subSteps.length : 0;
if (type === "goto" && explicitIdx !== null) {
appState.convStageIndex = Math.max(0, Math.min(maxStage, explicitIdx));
const targetStep = getActiveStepObject();
if (targetStep && targetStep.key === "e_sets") appState.eSetSubIndex = 0;
if (targetStep && targetStep.key === "transition_fn") appState.transSubIndex = 0;
if (isOnMinExtensionStage()) appState.minSubIndex = 0;
} else if (type === "reset") {
appState.convStageIndex = 0;
appState.eSetSubIndex = 0;
appState.transSubIndex = 0;
appState.minSubIndex = 0;
} else if (type === "next_major") {
appState.convStageIndex = Math.min(maxStage, appState.convStageIndex + 1);
const targetStep = getActiveStepObject();
if (targetStep && targetStep.key === "e_sets") appState.eSetSubIndex = 0;
if (targetStep && targetStep.key === "transition_fn") appState.transSubIndex = 0;
if (isOnMinExtensionStage()) appState.minSubIndex = 0;
} else if (type === "next") {
if (activeStep && activeStep.key === "e_sets" && appState.eSetSubIndex !== "all" && appState.eSetSubIndex < pd.eSetsRows.length - 1) {
appState.eSetSubIndex += 1;
} else if (activeStep && activeStep.key === "transition_fn" && appState.transSubIndex !== "all" && appState.transSubIndex < pd.transitionsLog.length - 1) {
appState.transSubIndex += 1;
} else if (onMinExt && appState.minSubIndex !== "all" && appState.minSubIndex < minTotal - 1) {
appState.minSubIndex += 1;
} else {
appState.convStageIndex = Math.min(maxStage, appState.convStageIndex + 1);
const nextStep = getActiveStepObject();
if (nextStep && nextStep.key === "e_sets") appState.eSetSubIndex = 0;
if (nextStep && nextStep.key === "transition_fn") appState.transSubIndex = 0;
if (isOnMinExtensionStage()) appState.minSubIndex = 0;
}
} else if (type === "prev") {
if (activeStep && activeStep.key === "e_sets" && typeof appState.eSetSubIndex === "number" && appState.eSetSubIndex > 0) {
appState.eSetSubIndex -= 1;
} else if (activeStep && activeStep.key === "transition_fn" && typeof appState.transSubIndex === "number" && appState.transSubIndex > 0) {
appState.transSubIndex -= 1;
} else if (onMinExt && typeof appState.minSubIndex === "number" && appState.minSubIndex > 0) {
appState.minSubIndex -= 1;
} else {
appState.convStageIndex = Math.max(0, appState.convStageIndex - 1);
const prevStep = getActiveStepObject();
if (prevStep && prevStep.key === "e_sets") appState.eSetSubIndex = Math.max(0, pd.eSetsRows.length - 1);
if (prevStep && prevStep.key === "transition_fn") appState.transSubIndex = Math.max(0, pd.transitionsLog.length - 1);
if (isOnMinExtensionStage()) appState.minSubIndex = Math.max(0, minTotal - 1);
}
}
logAction(`conv_stage_${type}`, `Stage_${appState.convStageIndex}_e_${appState.eSetSubIndex}_t_${appState.transSubIndex}_m_${appState.minSubIndex}`);
renderPipelineTab();
}
function renderStepBodyHtml(stepObj, pd, originalNfa, expandedNfa, dfaDef) {
if (stepObj.key === "string_elim") {
const rowsHtml = pd.splitLog.map(r => `
<tr>
<td style="font-weight:700;">${escapeHtml(r.original)}</td>
<td style="font-weight:700;color:#15803d;">${escapeHtml(r.introduced)}</td>
<td>${escapeHtml(r.chain)}</td>
</tr>
`).join("");
const splitTip = renderHelpBadge(
"Slide 100 Step 1: Any multi-symbol transition <code>p ──s1s2..sk──▶ r</code> (<code>k ≥ 2</code>) is decomposed into single-symbol arcs by inserting <code>k − 1</code> fresh states.",
"step_string_elim"
);
const showOrig = appState.step1GraphTab === "orig";
const splitCls = appState.fullWidthGraph ? "conv-split-grid is-full-graph" : "conv-split-grid";
return `
<div class="${splitCls}">
<div>
<div class="substep-bar" style="margin-bottom:0.5rem;">
<button type="button" class="substep-pill ${!showOrig ? 'active' : ''}" onclick="setStep1GraphTab('expanded')">Single-Symbol NFA (${expandedNfa.states.length} states)</button>
<button type="button" class="substep-pill ${showOrig ? 'active' : ''}" onclick="setStep1GraphTab('orig')">Given NFA M (${originalNfa.states.length} states)</button>
</div>
<div class="st-graph-frame">
${showOrig
? renderAutomatonSvg(originalNfa, [], null, "step1_orig")
: renderAutomatonSvg(expandedNfa, pd.introducedStates, null, "step1_exp")}
</div>
<div class="mini-graph-legend">
<span><span class="legend-dot" style="background:#86efac;border:2px solid #15803d;"></span>Introduced State(s): <code>${escapeHtml(pd.introducedStates.join(", "))}</code></span>
</div>
</div>
<div>
<div class="compact-math-card">
<div class="compact-math-head">
<span style="font-family:var(--mono);font-weight:700;">String Splitting (${pd.splitLog.length} rule${pd.splitLog.length > 1 ? 's' : ''}) ${splitTip}</span>
<span class="hop-chip-eps">+${pd.introducedStates.length} state${pd.introducedStates.length > 1 ? 's' : ''}</span>
</div>
</div>
<div class="st-table-wrap">
<table class="st-table">
<thead>
<tr>
<th>String Arc</th>
<th>New</th>
<th>Single-Symbol Chain</th>
</tr>
</thead>
<tbody>${rowsHtml}</tbody>
</table>
</div>
</div>
</div>
`;
}
if (stepObj.key === "e_sets") {
const totalSub = pd.eSetsRows.length;
const isAll = (appState.eSetSubIndex === "all");
const subIdx = isAll ? (totalSub - 1) : Math.max(0, Math.min(totalSub - 1, Number(appState.eSetSubIndex) || 0));
if (!isAll) appState.eSetSubIndex = subIdx;
const activeRow = pd.eSetsRows[subIdx];
const pillsHtml = pd.eSetsRows.map((r, i) => `
<button type="button" class="substep-pill ${(!isAll && i === subIdx) ? 'active' : ''}" onclick="setESetSubStep(${i})">
E(${escapeHtml(r.state)})
</button>
`).join("");
let highlightCfg = [];
let mathCardHtml = "";
if (isAll || !activeRow) {
highlightCfg = [];
mathCardHtml = `
<div class="compact-math-card">
<div class="compact-math-head">
<strong>All ${totalSub} E-sets</strong>
${renderHelpBadge("Click any <code>E(qi)</code> pill above or any table row below to highlight its exact <code>ε</code>-path on the NFA diagram.", "eset_all_summary")}
</div>
</div>
`;
} else {
highlightCfg = {
originStates: [activeRow.state],
greenStates: activeRow.epsReachedStates,
edges: activeRow.epsEdges,
dimInactive: true
};
const hopsChips = activeRow.hops.length === 0
? `<span style="color:var(--st-muted);">∅ ε-out</span>`
: activeRow.hops.map(h => `<span class="hop-chip-eps">${escapeHtml(h.from)}→${escapeHtml(h.to)}</span>`).join(" ");
const headTip = renderHelpBadge(
`<code>E(${escapeHtml(activeRow.state)})</code> is the reflexive-transitive <code>ε</code>-closure: all NFA states reachable from <code>${escapeHtml(activeRow.state)}</code> using 0 or more <code>ε</code>-transitions.`,
`eset_head_${activeRow.state}`
);
const hopTip = activeRow.hops.length === 0
? renderHelpBadge(`No outgoing <code>ε</code>-transitions leave <code>${escapeHtml(activeRow.state)}</code>; by reflexivity (0 steps), <code>E(${escapeHtml(activeRow.state)}) = {${escapeHtml(activeRow.state)}}</code>.`, `eset_hop_${activeRow.state}`)
: renderHelpBadge(`BFS follows outgoing green <code>ε</code>-edges from <code>${escapeHtml(activeRow.state)}</code> (${activeRow.hops.map(h => `${escapeHtml(h.from)}──ε──▶${escapeHtml(h.to)}`).join(", ")}) until no new states are reached.`, `eset_hop_${activeRow.state}`);
mathCardHtml = `
<div class="compact-math-card">
<div class="compact-math-head">
<span style="font-family:var(--mono);font-weight:700;">[${subIdx + 1}/${totalSub}] E(${escapeHtml(activeRow.state)}) ${headTip}</span>
<code style="font-weight:700;color:#0f5132;background:#e6f6ed;padding:2px 8px;border-radius:5px;">${escapeHtml(activeRow.formula)}</code>
</div>
<div class="compact-math-row">
<span class="compact-lhs">
<span class="hop-chip-origin">${escapeHtml(activeRow.state)}</span>
<span>──ε*──▶</span>
${hopsChips}
</span>
${hopTip}
</div>
</div>
`;
}
const rowsHtml = pd.eSetsRows.map((r, i) => {
const rowCls = isAll
? "clickable-row"
: (i === subIdx ? "clickable-row active-substep-row" : (i < subIdx ? "clickable-row" : "clickable-row pending-substep-row"));
const statusMark = (!isAll && i === subIdx) ? "▶ " : ((!isAll && i < subIdx) || isAll ? "✓ " : "· ");
return `
<tr class="${rowCls}" onclick="setESetSubStep(${i})">
<td style="font-weight:700;width:84px;">${statusMark}${escapeHtml(r.state)}</td>
<td style="font-weight:700;color:#0068c9;">${escapeHtml(r.formula)}</td>
</tr>
`;
}).join("");
return `
<div class="substep-bar">
<button type="button" class="substep-nav-mini" onclick="setESetSubStep(${Math.max(0, subIdx - 1)})" ${(!isAll && subIdx === 0) ? "disabled" : ""}>◀</button>
<button type="button" class="substep-nav-mini" onclick="setESetSubStep(${Math.min(totalSub - 1, subIdx + 1)})" ${(!isAll && subIdx >= totalSub - 1) ? "disabled" : ""}>▶</button>
<span style="color:var(--st-border);margin:0 2px;">|</span>
${pillsHtml}
<button type="button" class="substep-pill ${isAll ? 'active' : ''}" onclick="setESetSubStep('all')">📋 All</button>
</div>
<div class="${appState.fullWidthGraph ? 'conv-split-grid is-full-graph' : 'conv-split-grid'}">
<div>
<div class="st-graph-frame">${renderAutomatonSvg(expandedNfa, highlightCfg, null, "nfa_esets")}</div>
<div class="mini-graph-legend">
<span><span class="legend-dot" style="background:#fef08a;border:2px solid #ca8a04;"></span>Origin <code>qi</code></span>
<span><span class="legend-dot" style="background:#86efac;border:2px solid #15803d;"></span>ε-Closure</span>
</div>
</div>
<div>
${mathCardHtml}
<div class="st-table-wrap">
<table class="st-table">
<thead>
<tr>
<th>State</th>
<th>E-set ${renderHelpBadge("Click any row to highlight its ε-closure path on the NFA diagram.", "eset_table_help", true)}</th>
</tr>
</thead>
<tbody>${rowsHtml}</tbody>
</table>
</div>
</div>
</div>
`;
}
if (stepObj.key === "initial_state") {
const initHighlight = {
originStates: [expandedNfa.start_state],
greenStates: pd.initialStateMembers.filter(x => x !== expandedNfa.start_state),
edges: pd.initialStateEpsEdges,
dimInactive: true
};
const initTip = renderHelpBadge(
`The new DFA initial state <code>s'</code> is the E-set of the NFA initial state <code>${escapeHtml(expandedNfa.start_state)}</code>, labeled <code>Q1</code> to start BFS subset construction.`,
"step_initial_state"
);
return `
<div class="${appState.fullWidthGraph ? 'conv-split-grid is-full-graph' : 'conv-split-grid'}">
<div>
<div class="st-graph-frame">${renderAutomatonSvg(expandedNfa, initHighlight, null, "nfa_init")}</div>
<div class="mini-graph-legend">
<span><span class="legend-dot" style="background:#fef08a;border:2px solid #ca8a04;"></span>NFA Start <code>${escapeHtml(expandedNfa.start_state)}</code></span>
<span><span class="legend-dot" style="background:#86efac;border:2px solid #15803d;"></span>Initial E-Closure <code>Q1</code></span>
</div>
</div>
<div>
<div class="formula-card" style="display:flex;align-items:center;justify-content:space-between;gap:0.5rem;">
<span>${escapeHtml(pd.initialStateFormula)}</span>
${initTip}
</div>
</div>
</div>
`;
}
if (stepObj.key === "transition_fn") {
const totalSub = pd.transitionsLog.length;
const isAll = (appState.transSubIndex === "all");
const subIdx = isAll ? (totalSub - 1) : Math.max(0, Math.min(totalSub - 1, Number(appState.transSubIndex) || 0));
if (!isAll) appState.transSubIndex = subIdx;
const activeRow = pd.transitionsLog[subIdx];
const pillsHtml = pd.transitionsLog.map((r, i) => `
<button type="button" class="substep-pill ${(!isAll && i === subIdx) ? 'active' : ''}" onclick="setTransSubStep(${i})" title="${escapeHtml(r.fullFormula)}">
${i + 1}.${escapeHtml(r.currAlias)}·${escapeHtml(r.symbol)}
</button>
`).join("");
let highlightCfg = [];
let mathCardHtml = "";
if (isAll || !activeRow) {
highlightCfg = [];
mathCardHtml = `
<div class="compact-math-card">
<div class="compact-math-head">
<strong>All ${totalSub} Evaluations (Q1..Q${dfaDef.states.length})</strong>
${renderHelpBadge("Click any pill above or formula row below to highlight source subset S, direct symbol moves, and follow-up ε-closures.", "trans_all_summary")}
</div>
</div>
`;
} else {
highlightCfg = {
sourceHaloStates: activeRow.currMembers,
moveStates: activeRow.moveStates,
greenStates: activeRow.epsOnlyStates,
edges: [...activeRow.moveEdges, ...activeRow.epsEdges],
dimInactive: true
};
const discoveryBadge = activeRow.isNewlyDiscovered
? `<span style="background:#dcfce7;color:#166534;padding:1px 8px;border-radius:999px;font-size:0.78rem;font-weight:700;">🆕 ${escapeHtml(activeRow.targetAlias)}</span>`
: `<span style="background:#f1f5f9;color:#475569;padding:1px 8px;border-radius:999px;font-size:0.78rem;font-weight:600;">↪ ${escapeHtml(activeRow.targetAlias)}</span>`;
const srcText = activeRow.currMembers.length === 0 ? "Ø" : `{${activeRow.currMembers.join(", ")}}`;
const srcTip = renderHelpBadge(
activeRow.currMembers.length === 0
? "<code>Ø</code> is the empty subset (0 active NFA states). Reading any symbol from <code>Ø</code> stays in <code>Ø</code>."
: `Active NFA states inside subset <code>${escapeHtml(activeRow.currAlias)} = ${escapeHtml(srcText)}</code> (marked with blue dashed rings on the NFA diagram).`,
`trans_src_${subIdx}`
);
let moveShort = "";
let moveTipText = "";
if (activeRow.currMembers.length === 0) {
moveShort = "Ø ⇒ Ø";
moveTipText = `Since <code>${escapeHtml(activeRow.currAlias)} = Ø</code> has no NFA states, reading <code>'${escapeHtml(activeRow.symbol)}'</code> produces <code>Ø</code>.`;
} else if (activeRow.moveHops.length === 0) {
moveShort = "∅ ⇒ Ø";
moveTipText = `None of the states in <code>${escapeHtml(srcText)}</code> have an outgoing <code>'${escapeHtml(activeRow.symbol)}'</code> transition, so direct Move is empty (<code>Ø</code>).`;
} else {
moveShort = `${activeRow.moveHops.map(h => `${h.from}→${h.to}`).join(", ")} ⇒ {${activeRow.moveStates.join(", ")}}`;
moveTipText = `Direct <code>'${escapeHtml(activeRow.symbol)}'</code>-arcs from <code>${escapeHtml(srcText)}</code> (red arrows) land on yellow state(s) <code>{${escapeHtml(activeRow.moveStates.join(", "))}}</code>.`;
}
const moveTip = renderHelpBadge(moveTipText, `trans_move_${subIdx}`);
const unionShort = activeRow.esetComponents.length === 0
? `Ø = ${activeRow.targetAlias}`
: `${activeRow.esetComponents.map(c => `E(${c.state})`).join(" ∪ ")} = ${activeRow.targetLabel} = ${activeRow.targetAlias}`;
const unionTip = renderHelpBadge(
activeRow.esetComponents.length === 0
? (activeRow.isNewlyDiscovered
? `Empty result <code>Ø</code> is discovered for the first time and enqueued as sink state <code>${escapeHtml(activeRow.targetAlias)}</code>.`
: `Maps back to known empty sink state <code>${escapeHtml(activeRow.targetAlias)} = Ø</code>.`)
: `Union of E-sets (${activeRow.esetComponents.map(c => `<code>E(${escapeHtml(c.state)})=${escapeHtml(c.esetStr)}</code>`).join(" ∪ ")}) yields <code>${escapeHtml(activeRow.targetLabel)}</code> (${activeRow.isNewlyDiscovered ? `new DFA state <code>${escapeHtml(activeRow.targetAlias)}</code> added to queue` : `known state <code>${escapeHtml(activeRow.targetAlias)}</code>`}).`,
`trans_union_${subIdx}`
);
const headTip = renderHelpBadge(
`Evaluating <code>δ(${escapeHtml(activeRow.currLabel)}, ${escapeHtml(activeRow.symbol)})</code>: follow <code>'${escapeHtml(activeRow.symbol)}'</code>-edges from <code>${escapeHtml(activeRow.currAlias)}</code>, then take the union of E-sets.`,
`trans_head_${subIdx}`
);
mathCardHtml = `
<div class="compact-math-card">
<div class="compact-math-head">
<span style="font-family:var(--mono);font-weight:700;">[${subIdx + 1}/${totalSub}] δ(${escapeHtml(activeRow.currAlias)}, ${escapeHtml(activeRow.symbol)}) ${headTip}</span>
${discoveryBadge}
</div>
<div class="compact-math-row">
<span class="compact-lhs"><span class="hop-chip-src">S = ${escapeHtml(activeRow.currAlias)}</span> <span>${escapeHtml(srcText)}</span></span>
${srcTip}
</div>
<div class="compact-math-row">
<span class="compact-lhs"><span class="hop-chip-move">Move(${escapeHtml(activeRow.symbol)})</span> <span>${escapeHtml(moveShort)}</span></span>
${moveTip}
</div>
<div class="compact-math-row">
<span class="compact-lhs"><span class="hop-chip-eps">∪ E-set</span> <span>${escapeHtml(unionShort)}</span></span>
${unionTip}
</div>
</div>
`;
}
const rowsHtml = pd.transitionsLog.map((r, i) => {
const rowCls = isAll
? "clickable-row"
: (i === subIdx ? "clickable-row active-substep-row" : (i < subIdx ? "clickable-row" : "clickable-row pending-substep-row"));
const statusMark = (!isAll && i === subIdx) ? "▶ " : ((!isAll && i < subIdx) || isAll ? "✓ " : "· ");
return `
<tr class="${rowCls}" onclick="setTransSubStep(${i})">
<td>${statusMark}${escapeHtml(r.fullFormula)}</td>
</tr>
`;
}).join("");
return `
<div class="substep-bar">
<button type="button" class="substep-nav-mini" onclick="setTransSubStep(${Math.max(0, subIdx - 1)})" ${(!isAll && subIdx === 0) ? "disabled" : ""}>◀</button>
<button type="button" class="substep-nav-mini" onclick="setTransSubStep(${Math.min(totalSub - 1, subIdx + 1)})" ${(!isAll && subIdx >= totalSub - 1) ? "disabled" : ""}>▶</button>
<span style="color:var(--st-border);margin:0 2px;">|</span>
${pillsHtml}
<button type="button" class="substep-pill ${isAll ? 'active' : ''}" onclick="setTransSubStep('all')">📋 All</button>
</div>
<div class="${appState.fullWidthGraph ? 'conv-split-grid is-full-graph' : 'conv-split-grid'}">
<div>
<div class="st-graph-frame">${renderAutomatonSvg(expandedNfa, highlightCfg, null, "nfa_trans")}</div>
<div class="mini-graph-legend">
<span><span class="legend-dot" style="background:#dbeafe;border:2px dashed #2563eb;"></span>Source <code>S</code></span>
<span><span class="legend-dot" style="background:#fef08a;border:2px solid #dc2626;"></span>Move(<code>σ</code>)</span>
<span><span class="legend-dot" style="background:#86efac;border:2px solid #16a34a;"></span>ε-Closure</span>
</div>
</div>
<div>
${mathCardHtml}
<div class="st-table-wrap">
<table class="st-table">
<thead>
<tr>
<th>Slide Formula δ(S, σ) ${renderHelpBadge("Matches Lecture 5 slide derivations verbatim. Click any row to highlight its path on the NFA diagram.", "trans_table_help", true)}</th>
</tr>
</thead>
<tbody>${rowsHtml}</tbody>
</table>
</div>
</div>
</div>
`;
}
if (stepObj.key === "final_states") {
const finalTip = renderHelpBadge(
"Slide 100 Final Step: Every DFA subset <code>Qi</code> that contains at least one original NFA accepting state (<code>Qi ∩ F ≠ Ø</code>) is marked with a double-circle final ring.",
"step_final_states"
);
const symHeaders = dfaDef.alphabet.map(sym => `<th>δ(Qi, ${escapeHtml(sym)})</th>`).join("");
const summaryRows = dfaDef.states.map((st, idx) => {
const qi = `Q${idx + 1}`;
const isAcc = dfaDef.accept_states.includes(st);
const isStart = st === dfaDef.start_state;
const cells = dfaDef.alphabet.map(sym => {
const dst = (dfaDef.transitions[st] && dfaDef.transitions[st][sym]) || "Ø";
const dstAlias = pd.aliasMap[dst] || "";
return `<td>${escapeHtml(dstAlias ? `${dstAlias} (${dst})` : dst)}</td>`;
}).join("");
const mark = (isStart && isAcc) ? "→ ◎ " : (isStart ? "→ " : (isAcc ? "◎ " : ""));
return `<tr style="${isAcc ? 'background:#f0fdf4;' : ''}">
<td style="font-weight:700;color:#1d4ed8;">${mark}${qi}</td>
<td style="font-weight:700;">${escapeHtml(st)}</td>
${cells}
</tr>`;
}).join("");
return `
<div class="${appState.fullWidthGraph ? 'conv-split-grid is-full-graph' : 'conv-split-grid'}">
<div>
<h4 class="st-h4" style="margin-bottom:0.42rem;">
<span>Converted DFA</span>
<span class="state-count-code">${dfaDef.states.length} states</span>
</h4>
<div class="st-graph-frame">${renderAutomatonSvg(dfaDef, dfaDef.accept_states.filter(s => s !== dfaDef.start_state), null, "dfa_final")}</div>
<div class="mini-graph-legend">
<span><span class="legend-dot" style="background:#dbeafe;border:2px solid #1d4ed8;"></span>Initial <code>Q1 = ${escapeHtml(dfaDef.start_state)}</code></span>
<span><span class="legend-dot" style="background:#86efac;border:3px double #15803d;"></span>Final <code>F'</code></span>
<span><span class="legend-dot" style="background:#fee2e2;border:2px solid #b91c1c;"></span>Bottom Sink <code>Ø</code></span>
</div>
</div>
<div>
<div class="formula-card" style="margin-bottom:0.7rem;border-left-color:#15803d;display:flex;align-items:center;justify-content:space-between;gap:0.5rem;">
<span>${escapeHtml(pd.finalStatesFormula)}</span>
${finalTip}
</div>
<div class="st-table-wrap">
<table class="st-table">
<thead>
<tr>
<th>Qi</th>
<th>Subset</th>
${symHeaders}
</tr>
</thead>
<tbody>${summaryRows}</tbody>
</table>
</div>
</div>
</div>
`;
}
return "";
}
function renderMinExtensionHtml(dfaDef, minDfa, m2Data) {
const subSteps = (m2Data && m2Data.subSteps) ? m2Data.subSteps : [];
const totalSub = subSteps.length;
if (totalSub === 0 || !minDfa) return "";
const isAll = (appState.minSubIndex === "all");
const subIdx = isAll ? (totalSub - 1) : Math.max(0, Math.min(totalSub - 1, Number(appState.minSubIndex) || 0));
if (!isAll) appState.minSubIndex = subIdx;
const cur = subSteps[subIdx];
const pillsHtml = subSteps.map((st, i) => `
<button type="button" class="substep-pill ${(!isAll && i === subIdx) ? 'active' : ''}" onclick="setMinSubStep(${i})">
${escapeHtml(st.pill)}
</button>
`).join("");
const navBarHtml = `
<div class="substep-bar" style="border-color:#ddd6fe;background:#faf5ff;">
<button type="button" class="substep-nav-mini" onclick="setMinSubStep(${Math.max(0, subIdx - 1)})" ${(!isAll && subIdx === 0) ? "disabled" : ""}>◀</button>
<button type="button" class="substep-nav-mini" onclick="setMinSubStep(${Math.min(totalSub - 1, subIdx + 1)})" ${(!isAll && subIdx >= totalSub - 1) ? "disabled" : ""}>▶</button>
<span style="color:#ddd6fe;margin:0 2px;">|</span>
${pillsHtml}
<button type="button" class="substep-pill ${isAll ? 'active' : ''}" onclick="setMinSubStep('all')">📋 All</button>
</div>
`;
if (isAll || cur.kind === "final_min") {
const fin = subSteps[totalSub - 1];
const rowsHtml = fin.classRows.map(r => `
<tr style="${r.isMerged ? 'background:#eff6ff;font-weight:700;' : ''}">
<td style="font-weight:700;color:#5b21b6;">${escapeHtml(r.group)} <span style="font-weight:500;font-size:0.76rem;color:#64748b;">(${escapeHtml(r.roleTag)})</span></td>
<td>${escapeHtml(r.aliases)} <span style="color:#64748b;font-size:0.8rem;">${escapeHtml(r.members)}</span></td>
<td>
<span style="display:inline-flex;align-items:center;justify-content:space-between;width:100%;gap:0.35rem;">
<span>${escapeHtml(r.transSummary)}</span>
${renderHelpBadge(r.tip, `min_class_${r.group}`)}
</span>
</td>
</tr>
`).join("");
const logRowsHtml = subSteps.map((s, i) => `
<tr class="clickable-row ${(!isAll && i === subIdx) ? 'active-substep-row' : ''}" onclick="setMinSubStep(${i})">
<td style="font-weight:700;width:110px;">${escapeHtml(s.pill)}</td>
<td>${escapeHtml(s.headline)}</td>
<td><span class="${s.badgeCls}">${escapeHtml(s.badge)}</span></td>
</tr>
`).join("");
const showOrigDfa = appState.m2FinalGraphTab === "orig";
const splitCls = appState.fullWidthGraph ? "conv-split-grid is-full-graph" : "conv-split-grid";
return `
${navBarHtml}
<div class="${splitCls}">
<div>
<div class="substep-bar" style="margin-bottom:0.5rem;">
<button type="button" class="substep-pill ${!showOrigDfa ? 'active' : ''}" onclick="setM2FinalGraphTab('min')">Minimized DFA (${minDfa.states.length} states)</button>
<button type="button" class="substep-pill ${showOrigDfa ? 'active' : ''}" onclick="setM2FinalGraphTab('orig')">Converted DFA (${dfaDef.states.length} states)</button>
</div>
<div class="st-graph-frame">
${showOrigDfa
? renderAutomatonSvg(dfaDef, fin.origHighlightCfg, null, "m2_orig_dfa")
: renderAutomatonSvg(minDfa, fin.minHighlightCfg, null, "m2_min_dfa")}
</div>
<div class="mini-graph-legend">
<span><span class="legend-dot" style="background:#e0f2fe;border:2px solid #0284c7;"></span>Merged Equivalence Class</span>
<span><span class="legend-dot" style="background:#ffffff;border:3px double #334155;"></span>Final State</span>
<span><span class="legend-dot" style="background:#fee2e2;border:2px solid #b91c1c;"></span>Bottom Sink <code>Ø</code></span>
</div>
</div>
<div>
<div class="compact-math-card ext-card">
<div class="compact-math-head">
<span style="font-family:var(--mono);font-weight:700;">[${totalSub}/${totalSub}] ${escapeHtml(fin.headline)} ${renderHelpBadge(fin.helpTip, "min_final_head", true)}</span>
<span class="${fin.badgeCls}">${escapeHtml(fin.badge)}</span>
</div>
</div>
<div class="st-table-wrap" style="margin-bottom:0.75rem;">
<table class="st-table">
<thead>
<tr>
<th>Equivalence Class</th>
<th>DFA Subsets</th>
<th>δ_min ${renderHelpBadge("Induced transitions between minimized equivalence classes.", "min_final_table", true)}</th>
</tr>
</thead>
<tbody>${rowsHtml}</tbody>
</table>
</div>
${isAll ? `
<div class="st-table-wrap">
<table class="st-table">
<thead><tr><th>Step</th><th>M2 Partition Trace (Click row to inspect)</th><th>Status</th></tr></thead>
<tbody>${logRowsHtml}</tbody>
</table>
</div>
` : ""}
</div>
</div>
`;
}
if (cur.kind === "init_p0") {
const blkRows = cur.blocksSummary.map(b => `
<tr>
<td style="font-weight:700;color:#0068c9;">${escapeHtml(b.groupName)} <span style="font-weight:400;color:#64748b;font-size:0.78rem;">(${escapeHtml(b.roleLabel)})</span></td>
<td>${escapeHtml(b.aliasesStr)}</td>
<td>
<span style="display:inline-flex;align-items:center;justify-content:space-between;width:100%;gap:0.35rem;">
<span>${escapeHtml(b.status)}</span>
${renderHelpBadge(b.tip, `min_p0_${b.groupName}`)}
</span>
</td>
</tr>
`).join("");
return `
${navBarHtml}
<div class="${appState.fullWidthGraph ? 'conv-split-grid is-full-graph' : 'conv-split-grid'}">
<div>
<div class="st-graph-frame">${renderAutomatonSvg(dfaDef, cur.highlightCfg, null, "m2_p0_dfa")}</div>
<div class="mini-graph-legend">
<span><span class="legend-dot" style="background:#e0f2fe;border:2px solid #0284c7;"></span>G0 (Non-Final)</span>
<span><span class="legend-dot" style="background:#dcfce7;border:2px solid #15803d;"></span>G1 (Final)</span>
</div>
</div>
<div>
<div class="compact-math-card ext-card">
<div class="compact-math-head">
<span style="font-family:var(--mono);font-weight:700;">[${subIdx + 1}/${totalSub}] ${escapeHtml(cur.headline)} ${renderHelpBadge(cur.helpTip, "min_p0_head", true)}</span>
<span class="${cur.badgeCls}">${escapeHtml(cur.badge)}</span>
</div>
</div>
<div class="st-table-wrap">
<table class="st-table">
<thead>
<tr>
<th>Block</th>
<th>States Qi</th>
<th>Status ${renderHelpBadge("Multi-state blocks (≥ 2 states) are tested in Round 1; singleton blocks are already minimal.", "min_p0_status", true)}</th>
</tr>
</thead>
<tbody>${blkRows}</tbody>
</table>
</div>
</div>
</div>
`;
}
const sigRows = cur.subGroupsRows.map(r => `
<tr>
<td style="font-weight:700;">${escapeHtml(r.membersShort)}</td>
<td style="font-weight:700;color:#5b21b6;">${escapeHtml(r.sigTuple)}</td>
<td>
<span style="display:inline-flex;align-items:center;justify-content:space-between;width:100%;gap:0.35rem;">
<span class="${cur.didSplit ? 'hop-chip-move' : 'hop-chip-eps'}">${escapeHtml(r.outcome)}</span>
${renderHelpBadge(`Transitions into previous-round blocks: <code>${escapeHtml(r.tip)}</code>.`, `min_r${cur.round}_${cur.blockName}_${r.membersShort}`)}
</span>
</td>
</tr>
`).join("");
return `
${navBarHtml}
<div class="${appState.fullWidthGraph ? 'conv-split-grid is-full-graph' : 'conv-split-grid'}">
<div>
<div class="st-graph-frame">${renderAutomatonSvg(dfaDef, cur.highlightCfg, null, "m2_step_dfa")}</div>
<div class="mini-graph-legend">
<span><span class="legend-dot" style="background:#dbeafe;border:2px dashed #2563eb;"></span>Tested <code>${escapeHtml(cur.blockName)}</code></span>
${cur.didSplit
? `<span><span class="legend-dot" style="background:#fef9c3;border:2px solid #dc2626;"></span>Splitting Arcs</span>`
: `<span><span class="legend-dot" style="background:#dcfce7;border:2px solid #16a34a;"></span>Matching Arcs</span>`}
</div>
</div>
<div>
<div class="compact-math-card ext-card">
<div class="compact-math-head">
<span style="font-family:var(--mono);font-weight:700;">[${subIdx + 1}/${totalSub}] ${escapeHtml(cur.headline)} ${renderHelpBadge(cur.helpTip, `min_head_${subIdx}`, true)}</span>
<span class="${cur.badgeCls}">${escapeHtml(cur.badge)}</span>
</div>
</div>
<div class="st-table-wrap">
<table class="st-table">
<thead>
<tr>
<th>Subset(s) in ${escapeHtml(cur.blockName)}</th>
<th>Sig ${escapeHtml(cur.sigHeaderTuple)} ${renderHelpBadge("Target partition block index (Gi) reached on each symbol in Σ.", `min_sig_col_${subIdx}`, true)}</th>
<th>Result</th>
</tr>
</thead>
<tbody>${sigRows}</tbody>
</table>
</div>
</div>
</div>
`;
}
function renderPipelineTab() {
const pd = appState.pipelineData;
const originalNfa = appState.originalNfa;
const expandedNfa = appState.expandedNfa;
const dfaDef = appState.dfaDef;
const minDfa = appState.minDfaDef;
const m2Data = appState.minM2Data;
if (!pd || !dfaDef) return;
const steps = pd.steps;
const maxStage = steps.length + (appState.showOptionalMinDfa ? 1 : 0);
appState.convStageIndex = Math.min(appState.convStageIndex, maxStage);
const stageIdx = appState.convStageIndex;
const activeStep = getActiveStepObject();
const onMinExt = isOnMinExtensionStage();
const minTotal = (m2Data && m2Data.subSteps) ? m2Data.subSteps.length : 0;
const atVeryStart = (stageIdx === 0);
const onLastESetSub = activeStep && activeStep.key === "e_sets" && (appState.eSetSubIndex === "all" || appState.eSetSubIndex >= pd.eSetsRows.length - 1);
const onLastTransSub = activeStep && activeStep.key === "transition_fn" && (appState.transSubIndex === "all" || appState.transSubIndex >= pd.transitionsLog.length - 1);
const onLastMinSub = onMinExt && (appState.minSubIndex === "all" || appState.minSubIndex >= minTotal - 1);
const atVeryEnd = (stageIdx >= maxStage) && (
(!activeStep && !onMinExt) ||
(activeStep && activeStep.key !== "e_sets" && activeStep.key !== "transition_fn") ||
onLastESetSub ||
onLastTransSub ||
onLastMinSub
);
document.getElementById("btnConvPrev").disabled = atVeryStart;
document.getElementById("btnConvNext").disabled = atVeryEnd;
const skipBtn = document.getElementById("btnConvSkipMajor");
const showSkip = stageIdx < maxStage && (
(activeStep && activeStep.key === "e_sets" && !onLastESetSub) ||
(activeStep && activeStep.key === "transition_fn" && !onLastTransSub)
);
skipBtn.classList.toggle("hidden", !showSkip);
const shortMap = {
string_elim: "Eliminate Strings",
e_sets: "E-sets",
initial_state: "Initial State",
transition_fn: "Transition δ",
final_states: "Final States & DFA"
};
const pillItems = [
{ label: "Given NFA M", isExt: false },
...steps.map(s => ({ label: `Step ${s.stepNum}: ${shortMap[s.key] || s.title}`, isExt: false }))
];
if (appState.showOptionalMinDfa) {
pillItems.push({ label: "🧩 Ext: Minimize DFA", isExt: true });
}
document.getElementById("convStagePillsContainer").innerHTML = pillItems.map((item, i) => `
<button type="button" class="conv-pill ${item.isExt ? 'ext-pill' : ''} ${i === stageIdx ? 'active' : ''}" onclick="convStepAction('goto', ${i})">${escapeHtml(item.label)}</button>
`).join("");
const stageContainer = document.getElementById("convActiveStageContent");
if (stageIdx === 0) {
const planItems = steps.map(s => `<li style="margin-bottom:0.22rem;"><strong>Step ${s.stepNum}:</strong> ${escapeHtml(s.title)}</li>`).join("");
const detectTip = renderHelpBadge(
pd.hasStringSplits
? "Auto-detected multi-symbol string transition(s) → executing all 5 Slide 100 conversion steps."
: "No multi-symbol string transitions present → string splitting is skipped automatically (4 steps, matching Lecture 5 Example 3).",
"given_nfa_steps_detect",
true
);
stageContainer.innerHTML = `
<div class="${appState.fullWidthGraph ? 'conv-split-grid is-full-graph' : 'conv-split-grid'}">
<div>
<h4 class="st-h4" style="margin-bottom:0.45rem;">
<span>Given NFA M</span>
<span class="state-count-code">${originalNfa.states.length} states</span>
</h4>
<div class="st-graph-frame">${renderAutomatonSvg(originalNfa, [], null, "given_nfa")}</div>
<div class="mini-graph-legend">
<span><span class="legend-dot" style="background:#dbeafe;border:2px solid #1d4ed8;"></span>Initial <code>${escapeHtml(originalNfa.start_state)}</code></span>
<span><span class="legend-dot" style="background:#ffffff;border:3px double #334155;"></span>Final <code>F</code></span>
</div>
</div>
<div>
<h4 class="st-h4" style="margin-bottom:0.45rem;">
<span style="display:inline-flex;align-items:center;">Slide 100 Steps (${steps.length}) ${detectTip}</span>
</h4>
<div class="formula-card" style="font-family:var(--sans);padding:0.75rem 1rem;">
<ol style="padding-left:1.2rem;">${planItems}</ol>
</div>
</div>
</div>
`;
} else if (stageIdx <= steps.length) {
stageContainer.innerHTML = renderStepBodyHtml(activeStep, pd, originalNfa, expandedNfa, dfaDef);
const activeTr = stageContainer.querySelector("tr.active-substep-row");
if (activeTr && activeTr.scrollIntoView) {
activeTr.scrollIntoView({ block: "nearest" });
}
} else if (minDfa && m2Data) {
stageContainer.innerHTML = renderMinExtensionHtml(dfaDef, minDfa, m2Data);
}
const cards = [];
cards.push(`
<div>
<h4 class="st-h4" style="margin-bottom:0.45rem;"><span>Given NFA M</span><span class="state-count-code">${originalNfa.states.length} states</span></h4>
<div class="st-graph-frame">${renderAutomatonSvg(originalNfa, [], null, "ov_orig", false)}</div>
</div>
`);
if (pd.hasStringSplits) {
cards.push(`
<div>
<h4 class="st-h4" style="margin-bottom:0.45rem;"><span>Single-Symbol NFA</span><span class="state-count-code">${expandedNfa.states.length} states</span></h4>
<div class="st-graph-frame">${renderAutomatonSvg(expandedNfa, pd.introducedStates, null, "ov_exp", false)}</div>
</div>
`);
}
cards.push(`
<div>
<h4 class="st-h4" style="margin-bottom:0.45rem;"><span>Converted DFA M'</span><span class="state-count-code">${dfaDef.states.length} states</span></h4>
<div class="st-graph-frame">${renderAutomatonSvg(dfaDef, [], null, "ov_dfa", false)}</div>
</div>
`);
if (appState.showOptionalMinDfa && minDfa) {
cards.push(`
<div>
<h4 class="st-h4" style="margin-bottom:0.45rem;"><span>🧩 Minimized DFA</span><span class="state-count-code">${minDfa.states.length} states</span></h4>
<div class="st-graph-frame">${renderAutomatonSvg(minDfa, [], null, "ov_min", false)}</div>
</div>
`);
}
const gridEl = document.getElementById("overviewGraphsGrid");
gridEl.className = `overview-grid overview-cols-${Math.min(4, Math.max(2, cards.length))}`;
gridEl.innerHTML = cards.join("");
const stepExpanders = steps.map(s => {
let inner = "";
if (s.key === "string_elim") {
inner = `<div class="st-table-wrap"><table class="st-table"><thead><tr><th>Original</th><th>New State(s)</th><th>Chain</th></tr></thead><tbody>${pd.splitLog.map(r => `<tr><td>${escapeHtml(r.original)}</td><td>${escapeHtml(r.introduced)}</td><td>${escapeHtml(r.chain)}</td></tr>`).join("")}</tbody></table></div>`;
} else if (s.key === "e_sets") {
inner = `<div class="st-table-wrap"><table class="st-table"><thead><tr><th>State</th><th>E-set</th></tr></thead><tbody>${pd.eSetsRows.map(r => `<tr><td>${escapeHtml(r.state)}</td><td>${escapeHtml(r.formula)}</td></tr>`).join("")}</tbody></table></div>`;
} else if (s.key === "initial_state") {
inner = `<div class="formula-card">${escapeHtml(pd.initialStateFormula)}</div>`;
} else if (s.key === "transition_fn") {
inner = `<div class="st-table-wrap"><table class="st-table"><thead><tr><th>Slide Formula δ(S, σ)</th></tr></thead><tbody>${pd.transitionsLog.map(r => `<tr><td>${escapeHtml(r.fullFormula)}</td></tr>`).join("")}</tbody></table></div>`;
} else if (s.key === "final_states") {
inner = `<div class="formula-card">${escapeHtml(pd.finalStatesFormula)}</div>`;
}
return `<details class="st-expander" open><summary>Step ${s.stepNum}: ${escapeHtml(s.title)}</summary><div class="st-expander-content">${inner}</div></details>`;
});
if (appState.showOptionalMinDfa && minDfa && m2Data) {
const fin = m2Data.subSteps[m2Data.subSteps.length - 1];
const minRows = fin ? fin.classRows.map(r => `<tr><td style="font-weight:700;color:#5b21b6;">${escapeHtml(r.group)}</td><td>${escapeHtml(r.aliases)} (${escapeHtml(r.members)})</td><td>${escapeHtml(r.transSummary)}</td></tr>`).join("") : "";
stepExpanders.push(`<details class="st-expander" open><summary>🧩 Extension: DFA Minimization (${dfaDef.states.length} ➔ ${minDfa.states.length} states)</summary><div class="st-expander-content"><div class="st-table-wrap"><table class="st-table"><thead><tr><th>Class</th><th>Subsets</th><th>δ_min</th></tr></thead><tbody>${minRows}</tbody></table></div></div></details>`);
}
document.getElementById("overviewStepsStack").innerHTML = stepExpanders.join("");
}
function syncTupleFromInputControls() {
const rawStates = document.getElementById("statesInput")?.value || "";
const parsedStates = Array.from(new Set(rawStates.split(",").map(s => s.trim()).filter(Boolean)));
if (parsedStates.length > 0) appState.states = parsedStates;
const rawAlpha = document.getElementById("alphabetInput")?.value || "";
const parsedAlpha = Array.from(new Set(rawAlpha.split(",").map(s => s.trim()).filter(Boolean)));
if (parsedAlpha.length > 0) appState.alphabet = parsedAlpha;
const startSelVal = document.getElementById("startStateSelect")?.value;
if (startSelVal && appState.states.includes(startSelVal)) {
appState.startState = startSelVal;
} else if (appState.states.length > 0 && !appState.states.includes(appState.startState)) {
appState.startState = appState.states[0];
}
appState.acceptStates = appState.acceptStates.filter(s => appState.states.includes(s));
}
function recomputeAndRenderAll() {
syncTupleFromInputControls();
const valErrors = validateAlphabetAndStrings(appState.alphabet, appState.states, appState.stringTransitions);
const errBanner = document.getElementById("globalValidationErrorBanner");
if (valErrors.length > 0) {
errBanner.innerHTML = valErrors.map(e => `<div>⚠️ ${escapeHtml(e)}</div>`).join("");
errBanner.classList.remove("hidden");
return;
}
errBanner.classList.add("hidden");
const originalNfa = buildCombinedOriginalNfa(
appState.states, appState.alphabet, appState.startState, appState.acceptStates,
appState.transitions, appState.stringTransitions
);
const { expandedNfa, splitLog, introducedStates } = expandStringTransitions(
appState.states, appState.alphabet, appState.startState, appState.acceptStates,
appState.transitions, appState.stringTransitions
);
const { dfaDef, pipelineData } = nfaToDfaSlide100Pipeline(expandedNfa, splitLog, introducedStates);
const { minDfa, mapping, m2Data } = minimizeDfa(dfaDef, pipelineData.aliasMap);
appState.originalNfa = originalNfa;
appState.expandedNfa = expandedNfa;
appState.dfaDef = dfaDef;
appState.pipelineData = pipelineData;
appState.minDfaDef = minDfa;
appState.minMapping = mapping;
appState.minM2Data = m2Data;
renderPipelineTab();
renderStepperView();
updateTelemetryView();
}
function renderStepperView() {
const targetStr = document.getElementById("stepperStringInput").value.trim();
const machineChoice = document.querySelector("input[name='stepperTargetMachine']:checked")?.value || "Converted DFA";
const chosenMachine = (machineChoice === "Minimized DFA" && appState.showOptionalMinDfa && appState.minDfaDef)
? appState.minDfaDef
: appState.dfaDef;
if (!chosenMachine) return;
const hasAnySingle = Object.values(appState.transitions).some(row => Object.values(row).some(arr => arr && arr.length > 0));
const isBlankCustom = (appState.presetName === "Custom Automaton") && !hasAnySingle && appState.stringTransitions.length === 0;
const blankPrompt = document.getElementById("stepperBlankCustomPrompt");
const execArea = document.getElementById("stepperExecutionArea");
if (isBlankCustom && targetStr.length === 0) {
blankPrompt.classList.remove("hidden");
execArea.classList.add("hidden");
return;
}
blankPrompt.classList.add("hidden");
execArea.classList.remove("hidden");
const { isAccepted, path, msg } = simulateString(chosenMachine, targetStr);
const banner = document.getElementById("stepperResultBanner");
if (msg !== "Success") {
banner.className = "st-alert-warn";
banner.textContent = `⚠️ Simulation Alert: ${msg}`;
banner.classList.remove("hidden");
return;
}
const maxSteps = path.length - 1;
appState.simStepIndex = Math.min(appState.simStepIndex, maxSteps);
const currIdx = appState.simStepIndex;
const currState = path[currIdx].state;
const consumedSym = path[currIdx].symbol;
document.getElementById("stepperProgressLabel").textContent = `Step ${currIdx} of ${maxSteps}`;
document.getElementById("stepperActiveStateBadge").textContent = currState;
const tape = document.getElementById("stepperTapeContainer");
if (targetStr.length === 0) {
tape.innerHTML = `<span style="color:#64748b;font-style:italic;">ε (empty string)</span>`;
} else {
tape.innerHTML = targetStr.split("").map((ch, i) => {
const safeCh = escapeHtml(ch);
if (i < currIdx) return `<span class="tape-char-done">${safeCh}</span>`;
if (i === currIdx) return `<span class="tape-char-curr">${safeCh}</span>`;
return `<span class="tape-char-wait">${safeCh}</span>`;
}).join("");
}
const visitedTrace = path.slice(0, currIdx + 1).map(p => p.state).join(" ➔ ");
document.getElementById("stepperTraceSequence").textContent = visitedTrace;
let activeEdge = null;
if (currIdx > 0) {
activeEdge = { src: path[currIdx - 1].state, dest: currState, symbol: consumedSym };
}
const stepSplit = document.getElementById("stepperSplitWrap");
if (stepSplit) stepSplit.classList.toggle("is-full-graph", appState.fullWidthGraph);
const stepperKey = (chosenMachine === appState.minDfaDef) ? "stepper_min_dfa" : "stepper_conv_dfa";
document.getElementById("stepperGraphContainer").innerHTML = renderAutomatonSvg(chosenMachine, [currState], activeEdge, stepperKey, true);
const sideCard = document.getElementById("stepperSideTraceCard");
if (sideCard) {
const unreadNow = currIdx < targetStr.length ? targetStr.slice(currIdx) : "ε";
const stepTransitionFormula = currIdx === 0
? `Start at initial state ${currState}`
: `δ(${path[currIdx - 1].state}, ${consumedSym}) = ${currState}`;
sideCard.innerHTML = `
<div class="compact-math-head">
<span style="font-family:var(--mono);font-weight:700;">[${currIdx}/${maxSteps}] (${escapeHtml(currState)}, ${escapeHtml(unreadNow || "ε")})</span>
${renderHelpBadge("Configuration <code>(q, w)</code> pairs the active state <code>q</code> with the unread suffix <code>w</code> (Tutorial Lesson 4 yield <code>⊢</code> notation).", "stepper_config_help")}
</div>
<div class="compact-math-row">
<span class="compact-lhs">${escapeHtml(stepTransitionFormula)}</span>
</div>
`;
}
const traceTbody = document.getElementById("stepperTraceTableBody");
if (traceTbody) {
traceTbody.innerHTML = path.map((p, idx) => {
const unread = idx < targetStr.length ? targetStr.slice(idx) : "ε";
const rowCls = idx === currIdx ? "clickable-row active-substep-row" : (idx < currIdx ? "clickable-row" : "clickable-row pending-substep-row");
const transTxt = idx === 0
? "Initial"
: `δ(${path[idx - 1].state}, ${p.symbol}) → ${p.state}`;
return `<tr class="${rowCls}" onclick="appState.simStepIndex=${idx}; renderStepperView();">
<td style="font-weight:700;">${idx}</td>
<td>(${escapeHtml(p.state)}, ${escapeHtml(unread || "ε")})</td>
<td>${escapeHtml(transTxt)}</td>
</tr>`;
}).join("");
}
if (currIdx === maxSteps) {
const dispStr = targetStr.length > 0 ? targetStr : "ε";
banner.classList.remove("hidden");
if (isAccepted) {
banner.className = "st-alert-success";
banner.innerHTML = `🎉 Simulation Complete: The string <code>'${escapeHtml(dispStr)}'</code> is <strong>ACCEPTED</strong> (Ended in final state <code>${escapeHtml(currState)}</code>).`;
} else {
banner.className = "st-alert-error";
banner.innerHTML = `🛑 Simulation Complete: The string <code>'${escapeHtml(dispStr)}'</code> is <strong>REJECTED</strong> (Ended in non-final state <code>${escapeHtml(currState)}</code>).`;
}
} else {
banner.classList.add("hidden");
}
}
function stepperAction(type) {
const targetStr = document.getElementById("stepperStringInput").value.trim();
const maxSteps = targetStr.length;
if (type === "reset") {
appState.simStepIndex = 0;
logAction("stepper_reset");
} else if (type === "prev") {
appState.simStepIndex = maxSteps > 0 ? Math.max(0, appState.simStepIndex - 1) : 0;
logAction("stepper_prev", `Step_${appState.simStepIndex}`);
} else if (type === "next") {
appState.simStepIndex = Math.min(maxSteps, appState.simStepIndex + 1);
logAction("stepper_next", `Step_${appState.simStepIndex}`);
}
renderStepperView();
}
function switchTab(tabName) {
const tabs = ["pipeline", "stepper", "telemetry"];
tabs.forEach(t => {
const cap = t.charAt(0).toUpperCase() + t.slice(1);
const panel = document.getElementById(`tabPanel${cap}`);
const btn = document.getElementById(`tabBtn${cap}`);
if (t === tabName) {
panel.classList.remove("hidden");
btn.className = "st-tab active";
} else {
panel.classList.add("hidden");
btn.className = "st-tab";
}
});
logAction("switch_tab", tabName);
}
function updateTelemetryView() {
const elapsedSec = Number(((Date.now() - appState.sessionStartTime) / 1000).toFixed(1));
const elapsedMin = (elapsedSec / 60).toFixed(1);
document.getElementById("metricSessionTime").textContent = `${elapsedMin} mins`;
document.getElementById("metricTotalActions").textContent = `${appState.userActionsLog.length} events`;
const pid = document.getElementById("participantIdInput").value.trim() || "ANONYMOUS";
const payload = {
participant_id: pid,
elapsed_seconds: elapsedSec,
actions_summary_count: appState.userActionsLog.length,
recent_actions: appState.userActionsLog.slice(-10)
};
document.getElementById("telemetryJsonPre").textContent = JSON.stringify(payload, null, 2);
const showDetailed = document.getElementById("chkDetailedEventLog")?.checked;
const logContainer = document.getElementById("detailedEventLogContainer");
const logBody = document.getElementById("detailedEventLogBody");
if (showDetailed) {
logContainer.classList.remove("hidden");
if (appState.userActionsLog.length === 0) {
logBody.innerHTML = `<tr><td colspan="4" style="color:#64748b;text-align:center;">No interaction events recorded yet in this session.</td></tr>`;
} else {
logBody.innerHTML = appState.userActionsLog.map((ev, i) => `
<tr>
<td style="color:#64748b;">${i + 1}</td>
<td>${ev.timestamp_sec}</td>
<td style="font-weight:700;color:#0068c9;">${escapeHtml(ev.action)}</td>
<td>${escapeHtml(ev.details || "")}</td>
</tr>
`).join("");
}
} else {
logContainer.classList.add("hidden");
}
}
function copyTelemetryJson() {
const text = document.getElementById("telemetryJsonPre").textContent;
if (navigator.clipboard && navigator.clipboard.writeText) {
navigator.clipboard.writeText(text);
} else {
const ta = document.createElement("textarea");
ta.value = text;
document.body.appendChild(ta);
ta.select();
document.execCommand("copy");
document.body.removeChild(ta);
}
const btn = document.getElementById("btnCopyTelemetry");
btn.textContent = "✓ Copied!";
setTimeout(() => { btn.textContent = "📋 Copy JSON"; }, 2000);
}
document.addEventListener("DOMContentLoaded", () => {
document.getElementById("presetSelect").addEventListener("change", (e) => {
logAction("select_preset", e.target.value);
loadPreset(e.target.value);
});
document.getElementById("statesInput").addEventListener("change", (e) => {
const list = Array.from(new Set(e.target.value.split(",").map(s => s.trim()).filter(Boolean)));
if (list.length > 0) {
appState.states = list;
if (!appState.states.includes(appState.startState)) appState.startState = appState.states[0];
appState.acceptStates = appState.acceptStates.filter(s => appState.states.includes(s));
appState.eSetSubIndex = 0;
appState.transSubIndex = 0;
logAction("edit_states", appState.states.join(","));
rebuildSidebarControls();
recomputeAndRenderAll();
}
});
document.getElementById("alphabetInput").addEventListener("change", (e) => {
const list = Array.from(new Set(e.target.value.split(",").map(s => s.trim()).filter(Boolean)));
if (list.length > 0) {
appState.alphabet = list;
appState.eSetSubIndex = 0;
appState.transSubIndex = 0;
logAction("edit_alphabet", appState.alphabet.join(","));
rebuildSidebarControls();
recomputeAndRenderAll();
}
});
document.getElementById("startStateSelect").addEventListener("change", (e) => {
appState.startState = e.target.value;
appState.eSetSubIndex = 0;
appState.transSubIndex = 0;
logAction("select_start_state", appState.startState);
recomputeAndRenderAll();
});
document.getElementById("strLabelInput").addEventListener("keydown", (e) => {
if (e.key === "Enter") {
e.preventDefault();
addStringTransitionRule();
}
});
document.getElementById("stepperStringInput").addEventListener("input", () => {
appState.simStepIndex = 0;
renderStepperView();
});
document.querySelectorAll("input[name='stepperTargetMachine']").forEach(r => {
r.addEventListener("change", () => {
appState.simStepIndex = 0;
logAction("switch_stepper_target", r.value);
renderStepperView();
});
});
document.addEventListener("click", () => {
document.querySelectorAll(".q-help.is-pinned").forEach(el => el.classList.remove("is-pinned"));
});
const initChk = document.getElementById("chkOptionalMinDfa");
if (initChk) initChk.checked = false;
const initConvRadio = document.querySelector("input[name='stepperTargetMachine'][value='Converted DFA']");
if (initConvRadio) initConvRadio.checked = true;
document.getElementById("participantIdInput").addEventListener("input", updateTelemetryView);
loadPreset(DEFAULT_PRESET_NAME);
});
