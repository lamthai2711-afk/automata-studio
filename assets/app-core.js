const DEFAULT_PRESET_NAME = "Custom Automaton";
const PREBUILT_SCENARIOS = {
"NFA → DFA: Example 1": {
states: "q1, q2, q3, q4",
alphabet: "a, b, e",
start: "q1",
accept: ["q3"],
transitions: {
"q1": { "b": ["q2"] },
"q2": { "a": ["q3"] },
"q3": { "e": ["q2", "q4"] },
"q4": { "a": ["q2"] }
},
stringTransitions: [
{ from: "q4", label: "ab", to: "q1" }
],
sampleStr: "baabba",
description: "NFA → DFA: Example 1 (Slides 101–106)"
},
"NFA → DFA: Example 2": {
states: "q1, q2, q3",
alphabet: "a, b, e",
start: "q1",
accept: ["q3"],
transitions: {
"q1": { "b": ["q2"] },
"q2": { "b": ["q3"] },
"q3": { "e": ["q1"] }
},
stringTransitions: [
{ from: "q1", label: "aa", to: "q2" },
{ from: "q1", label: "ba", to: "q2" }
],
sampleStr: "bab",
description: "NFA → DFA: Example 2 (Slides 107–112)"
},
"NFA → DFA: Example 3": {
states: "q1, q2, q3, q4, q5, q6, q7, q8",
alphabet: "a, b, e",
start: "q1",
accept: ["q8"],
transitions: {
"q1": { "a": ["q2"] },
"q2": { "e": ["q3", "q4"] },
"q3": { "a": ["q5"] },
"q4": { "b": ["q6"] },
"q5": { "e": ["q7"] },
"q6": { "e": ["q7"] },
"q7": { "b": ["q8"] },
"q8": {}
},
stringTransitions: [],
sampleStr: "aab",
description: "NFA → DFA: Example 3 (Slides 113–117)"
},
"NFA → DFA: Example 4": {
states: "q1, q2, q3, q4, q5, q6",
alphabet: "a, b, e",
start: "q1",
accept: ["q6"],
transitions: {
"q1": { "b": ["q2"] },
"q2": { "b": ["q3"] },
"q3": { "b": ["q6"] },
"q4": { "e": ["q3"] },
"q5": { "a": ["q1", "q4"] },
"q6": { "e": ["q4", "q5"] }
},
stringTransitions: [
{ from: "q1", label: "ab", to: "q4" }
],
sampleStr: "abb",
description: "NFA → DFA: Example 4 (Slides 118–124)"
},
"NFA → DFA: Example 5": {
states: "q1, q2, q3, q4, q5, q6, q7",
alphabet: "a, b, e",
start: "q1",
accept: ["q7"],
transitions: {
"q1": { "a": ["q2"], "e": ["q4"] },
"q2": { "b": ["q3"] },
"q3": { "a": ["q4"] },
"q4": { "e": ["q5", "q7"] },
"q5": { "a": ["q3"], "e": ["q6"] },
"q6": { "b": ["q3"], "a": ["q7"] },
"q7": {}
},
stringTransitions: [
{ from: "q7", label: "bb", to: "q1" }
],
sampleStr: "bba",
description: "NFA → DFA: Example 5 (Slides 125–132)"
}
};
const appState = {
sessionStartTime: Date.now(),
userActionsLog: [],
simStepIndex: 0,
convStageIndex: 0,
eSetSubIndex: 0,
transSubIndex: 0,
minSubIndex: 0,
lastHelpLogByTopic: {},
pipelineViewMode: "interactive",
showOptionalMinDfa: false,
presetName: DEFAULT_PRESET_NAME,
states: ["q1", "q2", "q3"],
alphabet: ["a", "b", "e"],
startState: "q1",
acceptStates: ["q3"],
transitions: { "q1": {}, "q2": {}, "q3": {} },
stringTransitions: [],
openBuilderStates: new Set(),
originalNfa: null,
expandedNfa: null,
dfaDef: null,
pipelineData: null,
minDfaDef: null,
minMapping: [],
minM2Data: null,
fullWidthGraph: false,
step1GraphTab: 'expanded',
m2FinalGraphTab: 'min',
customNodePositions: {},
graphCameras: {},
graphRegistry: {}
};
function asciiCompare(a, b) {
return a < b ? -1 : (a > b ? 1 : 0);
}
function escapeHtml(str) {
return String(str)
.replace(/&/g, "&amp;")
.replace(/</g, "&lt;")
.replace(/>/g, "&gt;")
.replace(/"/g, "&quot;");
}
function toggleSidebar(collapse) {
document.body.classList.toggle("sidebar-collapsed", collapse);
}
function setDiagramScale(scale, btnEl) {
document.documentElement.style.setProperty("--diagram-scale", String(scale));
document.querySelectorAll(".zoom-btn").forEach(b => b.classList.remove("active"));
if (btnEl) btnEl.classList.add("active");
logAction("zoom_diagram", `${Math.round(scale * 100)}%`);
}
function logAction(actionType, details = "") {
const elapsed = Number(((Date.now() - appState.sessionStartTime) / 1000).toFixed(1));
appState.userActionsLog.push({ timestamp_sec: elapsed, action: actionType, details });
document.getElementById("headerSessionBadge").textContent = `Actions: ${appState.userActionsLog.length}`;
updateTelemetryView();
}
function positionHelpPop(wrap) {
if (!wrap) return;
const btn = wrap.querySelector(".q-help-btn");
const pop = wrap.querySelector(".q-help-pop");
if (!btn || !pop) return;
const rect = btn.getBoundingClientRect();
const popW = 276;
const vw = window.innerWidth || 1280;
const vh = window.innerHeight || 800;
let left = pop.classList.contains("pop-left") ? rect.left : (rect.right - popW);
if (left + popW > vw - 12) left = vw - popW - 12;
if (left < 12) left = 12;
let top = rect.bottom + 7;
if (top + 110 > vh - 12 && rect.top > 120) {
top = Math.max(12, rect.top - 96);
}
pop.style.left = `${Math.round(left)}px`;
pop.style.top = `${Math.round(top)}px`;
}
function logHelpHover(topicKey, el = null) {
if (el) positionHelpPop(el);
const now = Date.now();
const prev = appState.lastHelpLogByTopic[topicKey] || 0;
if (now - prev < 4000) return;
appState.lastHelpLogByTopic[topicKey] = now;
logAction("help_tooltip_view", topicKey);
}
function toggleHelpPin(ev, topicKey) {
if (ev) ev.stopPropagation();
const btn = ev && ev.currentTarget ? ev.currentTarget : null;
const wrap = btn ? btn.closest(".q-help") : null;
if (!wrap) return;
const wasPinned = wrap.classList.contains("is-pinned");
document.querySelectorAll(".q-help.is-pinned").forEach(el => el.classList.remove("is-pinned"));
if (!wasPinned) {
positionHelpPop(wrap);
wrap.classList.add("is-pinned");
appState.lastHelpLogByTopic[topicKey] = Date.now();
logAction("help_tooltip_pin", topicKey);
}
}
function renderHelpBadge(tipHtml, topicKey, alignLeft = false) {
const safeTopic = escapeHtml(topicKey);
const posCls = alignLeft ? "q-help-pop pop-left" : "q-help-pop";
return `<span class="q-help" onmouseenter="logHelpHover('${safeTopic}', this)"><button type="button" class="q-help-btn" onclick="toggleHelpPin(event, '${safeTopic}')" aria-label="Explanation">?</button><span class="${posCls}">${tipHtml}</span></span>`;
}
function openMinimizationExtension() {
const chk = document.getElementById("chkOptionalMinDfa");
if (!appState.showOptionalMinDfa) {
appState.showOptionalMinDfa = true;
if (chk) chk.checked = true;
const minOpt = document.getElementById("lblStepperMinDfaOption");
if (minOpt) minOpt.classList.remove("hidden");
}
if (appState.pipelineData) {
appState.convStageIndex = appState.pipelineData.steps.length + 1;
appState.minSubIndex = 0;
}
logAction("open_min_dfa_extension", "M2_GroupByGroup");
recomputeAndRenderAll();
}
function flashResetToast(msg = "✓ Reset") {
const toast = document.getElementById("resetStatusToast");
if (!toast) return;
toast.textContent = msg;
toast.classList.remove("hidden");
setTimeout(() => toast.classList.add("hidden"), 2000);
}
function setPipelineViewMode(mode) {
appState.pipelineViewMode = mode;
document.getElementById("interactiveWalkthroughWrap").classList.toggle("hidden", mode !== "interactive");
document.getElementById("fullOverviewWrap").classList.toggle("hidden", mode !== "overview");
logAction("pipeline_view_mode", mode);
recomputeAndRenderAll();
}
function toggleOptionalMinDfa(checked) {
appState.showOptionalMinDfa = Boolean(checked);
const minOpt = document.getElementById("lblStepperMinDfaOption");
if (minOpt) minOpt.classList.toggle("hidden", !appState.showOptionalMinDfa);
if (!appState.showOptionalMinDfa) {
const convRadio = document.querySelector("input[name='stepperTargetMachine'][value='Converted DFA']");
if (convRadio) convRadio.checked = true;
appState.simStepIndex = 0;
}
logAction("toggle_optional_min_dfa", String(appState.showOptionalMinDfa));
recomputeAndRenderAll();
}
function toggleFullWidthGraph() {
appState.fullWidthGraph = !appState.fullWidthGraph;
logAction("toggle_full_width_graph", String(appState.fullWidthGraph));
renderPipelineTab();
const stepWrap = document.getElementById("stepperSplitWrap");
if (stepWrap) stepWrap.classList.toggle("is-full-graph", appState.fullWidthGraph);
renderStepperView();
}
function setStep1GraphTab(tabKey) {
appState.step1GraphTab = tabKey;
renderPipelineTab();
}
function setM2FinalGraphTab(tabKey) {
appState.m2FinalGraphTab = tabKey;
renderPipelineTab();
}
function resetGraphLayout(graphKey) {
delete appState.customNodePositions[graphKey];
delete appState.graphCameras[graphKey];
logAction("reset_graph_layout", graphKey);
rerenderSingleGraph(graphKey);
}
function zoomGraphCamera(graphKey, factor) {
const cam = appState.graphCameras[graphKey] || { zoom: 1, panX: 0, panY: 0 };
cam.zoom = Math.max(0.55, Math.min(2.6, Number((cam.zoom * factor).toFixed(3))));
appState.graphCameras[graphKey] = cam;
rerenderSingleGraph(graphKey);
}
function resetToDefault() {
document.getElementById("presetSelect").value = DEFAULT_PRESET_NAME;
appState.showOptionalMinDfa = false;
const chk = document.getElementById("chkOptionalMinDfa");
if (chk) chk.checked = false;
const minOpt = document.getElementById("lblStepperMinDfaOption");
if (minOpt) minOpt.classList.add("hidden");
const convRadio = document.querySelector("input[name='stepperTargetMachine'][value='Converted DFA']");
if (convRadio) convRadio.checked = true;
appState.customNodePositions = {};
appState.graphCameras = {};
logAction("reset_to_default", DEFAULT_PRESET_NAME);
loadPreset(DEFAULT_PRESET_NAME);
flashResetToast("✓ Default");
}
function resetCurrentPreset() {
const current = document.getElementById("presetSelect").value;
if (current === "Custom Automaton") {
resetToDefault();
return;
}
logAction("reset_current_preset", current);
loadPreset(current);
flashResetToast("✓ Restored");
}
function stateSortKey(stateName, stateOrderMap = null) {
if (stateOrderMap && Object.prototype.hasOwnProperty.call(stateOrderMap, stateName)) {
return { tier: 0, num: stateOrderMap[stateName], prefix: "" };
}
const m = /^([A-Za-z_]+)(\d+)$/.exec(stateName);
if (m) return { tier: 1, num: parseInt(m[2], 10), prefix: m[1] };
return { tier: 2, num: 0, prefix: stateName };
}
function sortStates(stateIterable, stateOrderMap = null) {
return Array.from(stateIterable).sort((a, b) => {
const ka = stateSortKey(a, stateOrderMap);
const kb = stateSortKey(b, stateOrderMap);
if (ka.tier !== kb.tier) return ka.tier - kb.tier;
if (ka.num !== kb.num) return ka.num - kb.num;
return asciiCompare(ka.prefix, kb.prefix);
});
}
function formatStateName(stateArray, stateOrderMap = null) {
if (!stateArray || stateArray.length === 0) return "Ø";
if (stateArray.length === 1 && stateArray[0] === "Ø") return "Ø";
return "{" + sortStates(stateArray, stateOrderMap).join(", ") + "}";
}
function validateAlphabetAndStrings(alphabetList, statesList, stringTransitions) {
const errors = [];
const atomicSymbols = alphabetList.filter(s => s !== "e");
const invalidAlpha = atomicSymbols.filter(s => s.length !== 1);
if (invalidAlpha.length > 0) {
errors.push(
`Formal Alphabet Error: Symbols [${invalidAlpha.join(", ")}] in Alphabet must be single characters (use 'Multi-Symbol / String Transitions' below for strings like 'ab').`
);
}
const validSigma = new Set(atomicSymbols.filter(s => s.length === 1));
const validStates = new Set(statesList);
stringTransitions.forEach((rule, idx) => {
const src = (rule.from || "").trim();
const lbl = (rule.label || "").trim();
const dst = (rule.to || "").trim();
if (!validStates.has(src) || !validStates.has(dst)) {
errors.push(`String Rule #${idx + 1}: State '${src}' or '${dst}' is not in declared States K.`);
return;
}
if (lbl.length < 2) {
errors.push(`String Rule #${idx + 1} ('${src} ──${lbl}──▶ ${dst}'): Multi-symbol string label must have length ≥ 2.`);
return;
}
if (lbl.includes("e") && !validSigma.has("e")) {
errors.push(`String Rule #${idx + 1} ('${src} ──${lbl}──▶ ${dst}'): Epsilon ('e') cannot be mixed inside a multi-symbol string.`);
return;
}
const unknown = Array.from(new Set(lbl.split("").filter(ch => !validSigma.has(ch)))).sort();
if (unknown.length > 0) {
const sigmaDisp = "{" + Array.from(validSigma).sort().join(", ") + "}";
errors.push(`String Rule #${idx + 1} ('${src} ──${lbl}──▶ ${dst}'): Character(s) [${unknown.join(", ")}] do not belong to declared Alphabet Σ = ${sigmaDisp}.`);
}
});
return errors;
}
function buildCombinedOriginalNfa(statesList, alphabetList, startState, acceptStates, singleTrans, stringTransitions) {
const combined = {};
statesList.forEach(s => { combined[s] = {}; });
for (const [s, row] of Object.entries(singleTrans || {})) {
if (!combined[s]) continue;
for (const [sym, targets] of Object.entries(row || {})) {
if (targets && targets.length > 0) combined[s][sym] = [...targets];
}
}
for (const rule of stringTransitions) {
const { from: src, label: lbl, to: dst } = rule;
if (combined[src] && statesList.includes(dst) && lbl) {
if (!combined[src][lbl]) combined[src][lbl] = [];
if (!combined[src][lbl].includes(dst)) combined[src][lbl].push(dst);
}
}
return {
states: [...statesList],
alphabet: [...alphabetList],
start_state: startState,
accept_states: [...acceptStates],
transitions: combined
};
}
function expandStringTransitions(statesList, alphabetList, startState, acceptStates, singleTrans, stringTransitions) {
const existing = new Set(statesList);
let maxQ = 0;
statesList.forEach(s => {
const m = /^q(\d+)$/.exec(s);
if (m) maxQ = Math.max(maxQ, parseInt(m[1], 10));
});
let nextQ = maxQ + 1;
function allocateNewState() {
while (existing.has(`q${nextQ}`)) nextQ += 1;
const name = `q${nextQ}`;
existing.add(name);
nextQ += 1;
return name;
}
const expandedStates = [...statesList];
const expandedTrans = {};
statesList.forEach(s => { expandedTrans[s] = {}; });
for (const [s, row] of Object.entries(singleTrans || {})) {
if (!expandedTrans[s]) continue;
for (const [sym, targets] of Object.entries(row || {})) {
for (const t of (targets || [])) {
if (!expandedTrans[s][sym]) expandedTrans[s][sym] = [];
if (!expandedTrans[s][sym].includes(t)) expandedTrans[s][sym].push(t);
}
}
}
const splitLog = [];
const introducedStates = [];
for (const srcState of statesList) {
const rules = stringTransitions.filter(r => r.from === srcState);
for (const rule of rules) {
const { from: src, label: lbl, to: dst } = rule;
if (!lbl || lbl.length < 2) continue;
let curr = src;
const chainParts = [src];
const ruleNewStates = [];
for (let i = 0; i < lbl.length; i++) {
const ch = lbl[i];
if (i < lbl.length - 1) {
const mid = allocateNewState();
expandedStates.push(mid);
expandedTrans[mid] = {};
introducedStates.push(mid);
ruleNewStates.push(mid);
if (!expandedTrans[curr][ch]) expandedTrans[curr][ch] = [];
expandedTrans[curr][ch].push(mid);
chainParts.push(`──${ch}──▶ ${mid}`);
curr = mid;
} else {
if (!expandedTrans[curr][ch]) expandedTrans[curr][ch] = [];
if (!expandedTrans[curr][ch].includes(dst)) expandedTrans[curr][ch].push(dst);
chainParts.push(`──${ch}──▶ ${dst}`);
}
}
splitLog.push({
original: `${src} ──${lbl}──▶ ${dst}`,
introduced: ruleNewStates.join(", "),
chain: chainParts.join(" ")
});
}
}
return {
expandedNfa: {
states: expandedStates,
alphabet: [...alphabetList],
start_state: startState,
accept_states: [...acceptStates],
transitions: expandedTrans
},
splitLog,
introducedStates
};
}
function traceEpsilonClosureBfs(seedStates, transitions, stateOrderMap) {
const closureSet = new Set(seedStates);
const bfsQueue = [...seedStates];
const hops = [];
const epsEdges = [];
while (bfsQueue.length > 0) {
const u = bfsQueue.shift();
const epsTargets = (transitions[u] && transitions[u]["e"]) ? transitions[u]["e"] : [];
for (const v of epsTargets) {
const isNew = !closureSet.has(v);
hops.push({ from: u, to: v, isNew });
epsEdges.push({ src: u, dest: v, symbol: "e", role: "eps" });
if (isNew) {
closureSet.add(v);
bfsQueue.push(v);
}
}
}
const members = sortStates(closureSet, stateOrderMap);
return { members, hops, epsEdges };
}
function nfaToDfaSlide100Pipeline(expandedNfa, splitLog, introducedStates) {
const alphabet = expandedNfa.alphabet.filter(s => s !== "e" && s.length === 1);
const nfaTrans = expandedNfa.transitions;
const startState = expandedNfa.start_state;
const nfaAccept = new Set(expandedNfa.accept_states);
const stateOrderMap = {};
expandedNfa.states.forEach((s, idx) => { stateOrderMap[s] = idx; });
const hasStringSplits = splitLog.length > 0;
const totalSteps = hasStringSplits ? 5 : 4;
const pipelineData = {
hasStringSplits,
totalSteps,
splitLog,
introducedStates,
eSetsRows: [],
eSetMap: {},
initialStateLabel: null,
initialStateMembers: [],
initialStateEpsEdges: [],
initialStateFormula: "",
qAliases: {},
transitionsLog: [],
finalStates: [],
finalStatesFormula: "",
steps: []
};
if (!startState) return { dfaDef: null, pipelineData };
expandedNfa.states.forEach((st, idx) => {
const { members, hops, epsEdges } = traceEpsilonClosureBfs([st], nfaTrans, stateOrderMap);
const esetStr = formatStateName(members, stateOrderMap);
const epsReachedStates = members.filter(x => x !== st);
pipelineData.eSetMap[st] = esetStr;
pipelineData.eSetsRows.push({
subIndex: idx,
state: st,
members,
epsReachedStates,
hops,
epsEdges,
esetStr,
formula: `E(${st}) = ${esetStr}`
});
});
const initTrace = traceEpsilonClosureBfs([startState], nfaTrans, stateOrderMap);
const initialClosure = initTrace.members;
const initialLabel = formatStateName(initialClosure, stateOrderMap);
pipelineData.initialStateMembers = initialClosure;
pipelineData.initialStateEpsEdges = initTrace.epsEdges;
pipelineData.initialStateLabel = initialLabel;
pipelineData.qAliases[initialLabel] = "Q1";
pipelineData.initialStateFormula = `s' = E(${startState}) = ${initialLabel} = Q1`;
const dfaTransitions = {};
const dfaClosures = [initialClosure];
const seenLabels = new Set([initialLabel]);
const queue = [initialClosure];
let transSubCounter = 0;
while (queue.length > 0) {
const curr = queue.shift();
const currLabel = formatStateName(curr, stateOrderMap);
const currAlias = pipelineData.qAliases[currLabel];
dfaTransitions[currLabel] = {};
for (const sym of alphabet) {
const moveHops = [];
const moveEdges = [];
const directSet = new Set();
for (const u of curr) {
const targets = (nfaTrans[u] && nfaTrans[u][sym]) ? nfaTrans[u][sym] : [];
for (const v of targets) {
directSet.add(v);
moveHops.push({ from: u, symbol: sym, to: v });
moveEdges.push({ src: u, dest: v, symbol: sym, role: "move" });
}
}
const mSorted = sortStates(directSet, stateOrderMap);
let targetClosure = [];
let targetLabel = "Ø";
let unionExpr = "Ø";
let epsHops = [];
let epsEdges = [];
let epsOnlyStates = [];
let esetComponents = [];
if (mSorted.length > 0) {
const cTrace = traceEpsilonClosureBfs(mSorted, nfaTrans, stateOrderMap);
targetClosure = cTrace.members;
epsHops = cTrace.hops;
epsEdges = cTrace.epsEdges;
epsOnlyStates = targetClosure.filter(x => !directSet.has(x));
targetLabel = formatStateName(targetClosure, stateOrderMap);
unionExpr = mSorted.map(p => `E(${p})`).join(" ∪ ");
esetComponents = mSorted.map(p => ({ state: p, esetStr: pipelineData.eSetMap[p] }));
}
const isNewlyDiscovered = !seenLabels.has(targetLabel);
if (isNewlyDiscovered) {
seenLabels.add(targetLabel);
dfaClosures.push(targetClosure);
pipelineData.qAliases[targetLabel] = `Q${dfaClosures.length}`;
queue.push(targetClosure);
}
const targetAlias = pipelineData.qAliases[targetLabel];
dfaTransitions[currLabel][sym] = targetLabel;
const fullFormula = mSorted.length > 0
? `δ(${currLabel}, ${sym}) = ${unionExpr} = ${targetLabel} = ${targetAlias}`
: `δ(${currLabel}, ${sym}) = Ø = ${targetAlias}`;
pipelineData.transitionsLog.push({
subIndex: transSubCounter++,
currMembers: [...curr],
currLabel,
currAlias,
stateWithAlias: `${currLabel} (${currAlias})`,
symbol: sym,
moveHops,
moveStates: mSorted,
moveEdges,
epsHops,
epsOnlyStates,
epsEdges,
esetComponents,
unionExpr,
targetClosure,
targetLabel,
targetAlias,
targetWithAlias: `${targetLabel} = ${targetAlias}`,
isNewlyDiscovered,
fullFormula
});
}
}
const dfaStateLabels = dfaClosures.map(c => formatStateName(c, stateOrderMap));
const dfaAcceptList = [];
for (const c of dfaClosures) {
if (c.some(s => nfaAccept.has(s))) {
dfaAcceptList.push(formatStateName(c, stateOrderMap));
}
}
pipelineData.finalStates = dfaAcceptList;
pipelineData.finalStatesFormula = dfaAcceptList.length > 0
? `F' = {${dfaAcceptList.join(", ")}}`
: "F' = Ø";
const steps = [];
if (hasStringSplits) {
steps.push({
key: "string_elim",
title: "Eliminating string transitions by introducing new states"
});
}
steps.push({ key: "e_sets", title: "Definition of E-sets" });
steps.push({ key: "initial_state", title: "Definition of new initial state" });
steps.push({ key: "transition_fn", title: "Definition of transition function" });
steps.push({ key: "final_states", title: "Definition of final states" });
steps.forEach((s, idx) => { s.stepNum = idx + 1; });
pipelineData.steps = steps;
pipelineData.aliasMap = Object.fromEntries(dfaStateLabels.map((lbl, idx) => [lbl, `Q${idx + 1}`]));
return {
dfaDef: {
states: dfaStateLabels,
alphabet,
start_state: initialLabel,
accept_states: dfaAcceptList,
transitions: dfaTransitions,
nodeBadges: Object.fromEntries(dfaStateLabels.map((lbl, idx) => [lbl, `Q${idx + 1}`]))
},
pipelineData
};
}
const GROUP_PALETTE = [
{ fill: "#e0f2fe", stroke: "#0284c7", sw: "2.4" },
{ fill: "#dcfce7", stroke: "#15803d", sw: "2.4" },
{ fill: "#fef9c3", stroke: "#ca8a04", sw: "2.4" },
{ fill: "#f3e8ff", stroke: "#7e22ce", sw: "2.4" },
{ fill: "#ffedd5", stroke: "#c2410c", sw: "2.4" },
{ fill: "#fce7f3", stroke: "#be185d", sw: "2.4" },
{ fill: "#e0e7ff", stroke: "#4338ca", sw: "2.4" },
{ fill: "#ccfbf1", stroke: "#0f766e", sw: "2.4" }
];
function minimizeDfa(dfaDef, aliasObj = null) {
if (!dfaDef || !dfaDef.states || dfaDef.states.length === 0) {
return { minDfa: null, mapping: [], m2Data: { subSteps: [], isAlreadyMinimal: true } };
}
const states = dfaDef.states;
const acceptSet = new Set(dfaDef.accept_states);
const nonAccept = states.filter(s => !acceptSet.has(s));
const accept = states.filter(s => acceptSet.has(s));
const alphabet = dfaDef.alphabet;
const transitions = dfaDef.transitions;
const getAlias = (st) => {
if (aliasObj && aliasObj[st]) return aliasObj[st];
const idx = states.indexOf(st);
return idx >= 0 ? `Q${idx + 1}` : st;
};
const fmtCompact = (st) => {
const al = getAlias(st);
return al !== st ? `${al} ${st}` : st;
};
const subSteps = [];
let partitions = [];
if (nonAccept.length > 0) partitions.push(nonAccept);
if (accept.length > 0) partitions.push(accept);
const p0Palette = {};
partitions.forEach((blk, bIdx) => {
const pal = GROUP_PALETTE[bIdx % GROUP_PALETTE.length];
blk.forEach(st => { p0Palette[st] = pal; });
});
subSteps.push({
kind: "init_p0",
pill: "1. P0",
headline: `P0 = { ${partitions.map((_, i) => `G${i}`).join(", ")} }`,
badge: `${partitions.length} initial block${partitions.length > 1 ? "s" : ""}`,
badgeCls: "hop-chip-src",
helpTip: `Moore's algorithm starts at <code>P0</code> by separating non-accepting DFA subsets (<code>K' \\ F'</code>) from accepting subsets (<code>F'</code>). Singleton blocks (1 state) can never split further.`,
highlightCfg: {
nodePaletteMap: p0Palette,
dimInactive: false
},
blocksSummary: partitions.map((blk, bIdx) => {
const isFinalBlk = blk.every(s => acceptSet.has(s));
return {
groupName: `G${bIdx}`,
roleLabel: isFinalBlk ? "Final (F')" : "Non-Final (K' \\ F')",
aliasesStr: blk.map(getAlias).join(", "),
subsetsStr: blk.map(fmtCompact).join(", "),
status: blk.length >= 2 ? `${blk.length} states → test` : "Singleton (fixed)",
tip: isFinalBlk
? `Accepting DFA states (${blk.map(fmtCompact).join(", ")}) contain at least one NFA final state.`
: `Non-accepting DFA states (${blk.map(fmtCompact).join(", ")}) contain no NFA final state.`
};
})
});
let round = 1;
while (true) {
const multiBlocksExist = partitions.some(p => p.length >= 2);
if (!multiBlocksExist) break;
const newPartitions = [];
let anySplitInRound = false;
partitions.forEach((part, bIdx) => {
if (part.length < 2) {
newPartitions.push(part);
return;
}
const sigMap = new Map();
const stateDetails = [];
for (const st of part) {
const perSym = alphabet.map(sym => {
const target = (transitions[st] && transitions[st][sym]) ? transitions[st][sym] : "Ø";
const gIdx = partitions.findIndex(p => p.includes(target));
return { sym, target, targetAlias: getAlias(target), gIdx };
});
const vec = perSym.map(x => x.gIdx);
const sigKey = JSON.stringify(vec);
if (!sigMap.has(sigKey)) sigMap.set(sigKey, { vec, members: [], samplePerSym: perSym });
sigMap.get(sigKey).members.push(st);
stateDetails.push({ st, alias: getAlias(st), perSym, vec });
}
const entries = Array.from(sigMap.values()).sort((a, b) => {
for (let i = 0; i < Math.min(a.vec.length, b.vec.length); i++) {
if (a.vec[i] !== b.vec[i]) return a.vec[i] - b.vec[i];
}
return a.vec.length - b.vec.length;
});
const didSplit = entries.length > 1;
if (didSplit) anySplitInRound = true;
for (const entry of entries) newPartitions.push(entry.members);
const splittingSyms = alphabet.filter((_, sIdx) => {
const seen = new Set(entries.map(e => e.vec[sIdx]));
return seen.size > 1;
});
const stepPalette = {};
partitions.forEach((otherBlk, oIdx) => {
if (oIdx === bIdx) return;
otherBlk.forEach(s => { stepPalette[s] = { fill: "#f8fafc", stroke: "#94a3b8", sw: "1.6" }; });
});
entries.forEach((entry, subIdx) => {
const pal = didSplit
? GROUP_PALETTE[(subIdx + 1) % GROUP_PALETTE.length]
: GROUP_PALETTE[1];
entry.members.forEach(s => { stepPalette[s] = pal; });
});
const highlightEdges = [];
for (const d of stateDetails) {
for (const ps of d.perSym) {
if (didSplit && splittingSyms.includes(ps.sym)) {
highlightEdges.push({ src: d.st, dest: ps.target, symbol: ps.sym, role: "move" });
} else if (!didSplit) {
highlightEdges.push({ src: d.st, dest: ps.target, symbol: ps.sym, role: "eps" });
}
}
}
const stepNum = subSteps.length + 1;
const sigHeaderTuple = `(${alphabet.join(", ")})`;
subSteps.push({
kind: "test_block",
pill: `${stepNum}. R${round}·G${bIdx}`,
round,
blockName: `G${bIdx}`,
sigHeaderTuple,
didSplit,
headline: `Round ${round} · Test G${bIdx} = {${part.map(getAlias).join(", ")}}`,
badge: didSplit ? `✂️ Split → ${entries.length} groups` : "✓ Keep together",
badgeCls: didSplit ? "hop-chip-move" : "hop-chip-eps",
helpTip: didSplit
? `Testing block <code>G${bIdx}</code> against Round ${round - 1} groups: symbol(s) <code>${splittingSyms.join(", ")}</code> send members into different target blocks, forcing <code>G${bIdx}</code> to split into ${entries.length} sub-blocks.`
: `Every state in <code>G${bIdx}</code> transitions into the exact same Round ${round - 1} target block on all symbols <code>(${alphabet.join(", ")})</code>, so they remain equivalent in Round ${round}.`,
highlightCfg: {
sourceHaloStates: part,
nodePaletteMap: stepPalette,
edges: highlightEdges,
dimInactive: true
},
subGroupsRows: entries.map((entry, subIdx) => {
const tupleStr = "(" + entry.vec.map(g => `G${g}`).join(", ") + ")";
const detailMoves = stateDetails
.filter(sd => entry.members.includes(sd.st))
.map(sd => `${sd.alias}=${sd.st}: ` + sd.perSym.map(p => `${p.sym}→${p.targetAlias}(G${p.gIdx})`).join(", "))
.join(" | ");
return {
membersShort: entry.members.map(getAlias).join(", "),
membersFull: entry.members.map(fmtCompact).join(", "),
sigTuple: tupleStr,
outcome: didSplit ? `Split #${subIdx + 1}` : "Equivalent",
tip: detailMoves
};
})
});
});
partitions = newPartitions;
if (!anySplitInRound) break;
round += 1;
}
const startState = dfaDef.start_state;
function partitionRank(p) {
if (p.includes(startState)) return { tier: 0, idx: 0 };
if (p.length === 1 && p[0] === "Ø") return { tier: 2, idx: 999999 };
const minIdx = Math.min(...p.map(s => {
const i = states.indexOf(s);
return i >= 0 ? i : 99999;
}));
return { tier: 1, idx: minIdx };
}
partitions.sort((a, b) => {
const ra = partitionRank(a);
const rb = partitionRank(b);
if (ra.tier !== rb.tier) return ra.tier - rb.tier;
return ra.idx - rb.idx;
});
const stateMap = {};
const mapping = [];
const origMergePalette = {};
const minMergePalette = {};
const minBadgeMap = {};
function buildMinClassLabel(sortedMembers) {
if (sortedMembers.length === 1) {
return sortedMembers[0];
}
const joinedSubsets = sortedMembers.join(" ≡ ");
if (sortedMembers.length === 2 && joinedSubsets.length <= 22) {
return joinedSubsets;
}
return sortedMembers.map(getAlias).join(" ≡ ");
}
const minStates = [];
partitions.forEach((p, idx) => {
const sortedMembers = [...p].sort((a, b) => {
const ia = states.indexOf(a);
const ib = states.indexOf(b);
return (ia >= 0 && ib >= 0) ? (ia - ib) : asciiCompare(a, b);
});
const label = buildMinClassLabel(sortedMembers);
minStates.push(label);
minBadgeMap[label] = sortedMembers.map(getAlias).join("≡");
sortedMembers.forEach(s => { stateMap[s] = label; });
const pal = p.length >= 2
? GROUP_PALETTE[idx % GROUP_PALETTE.length]
: null;
if (pal) {
sortedMembers.forEach(s => { origMergePalette[s] = pal; });
minMergePalette[label] = pal;
}
mapping.push({
group: label,
rawMembers: sortedMembers,
isMerged: sortedMembers.length >= 2,
isStart: sortedMembers.includes(startState),
isAccept: sortedMembers.some(s => acceptSet.has(s)),
aliases: sortedMembers.map(getAlias).join(", "),
members: sortedMembers.join(", ")
});
});
const minStart = stateMap[startState];
const minAccept = minStates.filter(lbl => accept.some(s => stateMap[s] === lbl));
const minTrans = {};
for (const s of states) {
const srcGroup = stateMap[s];
if (!minTrans[srcGroup]) minTrans[srcGroup] = {};
for (const sym of alphabet) {
const t = transitions[s] ? transitions[s][sym] : null;
if (t && stateMap[t]) minTrans[srcGroup][sym] = stateMap[t];
}
}
const minDfaObj = {
states: minStates,
alphabet,
start_state: minStart,
accept_states: minAccept,
transitions: minTrans,
nodeBadges: minBadgeMap
};
const isAlreadyMinimal = (minStates.length === states.length);
const mergedGroups = mapping.filter(m => m.isMerged);
const finalStepNum = subSteps.length + 1;
subSteps.push({
kind: "final_min",
pill: `${finalStepNum}. Min DFA`,
isAlreadyMinimal,
headline: isAlreadyMinimal
? `Fixed Point — Already Minimal (${minStates.length} states)`
: `Fixed Point — Merged ${states.length} ➔ ${minStates.length} states`,
badge: isAlreadyMinimal ? "✓ Already Minimal" : `Merged ${mergedGroups.map(m => m.aliases.replace(/, /g, "≡")).join(", ")}`,
badgeCls: "hop-chip-eps",
helpTip: isAlreadyMinimal
? `No two states in the Converted DFA are equivalent; every equivalence class is a singleton, so it is already the unique minimal DFA.`
: `Partition stabilized with ${mergedGroups.length} merged equivalence class(es): ${mergedGroups.map(m => `<code>${escapeHtml(m.group)}</code>`).join(", ")}. Collapsing each class into one state yields the Minimized DFA.`,
origHighlightCfg: {
sourceHaloStates: mergedGroups.flatMap(m => m.rawMembers),
nodePaletteMap: origMergePalette,
dimInactive: false
},
minHighlightCfg: {
nodePaletteMap: minMergePalette,
dimInactive: false
},
classRows: mapping.map(m => {
const transSummary = alphabet.map(sym => `${sym}→${(minTrans[m.group] && minTrans[m.group][sym]) || "Ø"}`).join(", ");
const roleTag = m.isStart && m.isAccept ? "Start, Final" : (m.isStart ? "Start" : (m.isAccept ? "Final" : (m.members === "Ø" ? "Trap Ø" : (m.isMerged ? "Merged" : "State"))));
return {
group: m.group,
roleTag,
isMerged: m.isMerged,
aliases: m.aliases,
members: m.members,
transSummary,
tip: `Class <code>${m.group}</code> (${roleTag}) represents DFA subset(s): <code>${escapeHtml(m.members)}</code>. Transitions: <code>${escapeHtml(transSummary)}</code>.`
};
})
});
return {
minDfa: minDfaObj,
mapping,
m2Data: {
subSteps,
isAlreadyMinimal,
origCount: states.length,
minCount: minStates.length
}
};
}
function simulateString(dfaDef, inputStr) {
const currStart = dfaDef.start_state;
const path = [{ state: currStart, symbol: "Start" }];
if (!currStart) return { isAccepted: false, path, msg: "No initial state defined." };
let curr = currStart;
for (const ch of inputStr) {
if (!dfaDef.alphabet.includes(ch)) {
return { isAccepted: false, path, msg: `Invalid symbol '${ch}' not in alphabet {${dfaDef.alphabet.join(", ")}}.` };
}
const nextSt = (dfaDef.transitions[curr] && dfaDef.transitions[curr][ch]) ? dfaDef.transitions[curr][ch] : "Ø";
path.push({ state: nextSt, symbol: ch });
curr = nextSt;
}
return { isAccepted: dfaDef.accept_states.includes(curr), path, msg: "Success" };
}
function computeLayeredLayout(automatonDef) {
const states = automatonDef.states || [];
const start = automatonDef.start_state;
const nonSinkStates = states.filter(s => s !== "Ø");
const adj = new Map();
const pred = new Map();
nonSinkStates.forEach(s => {
adj.set(s, new Set());
pred.set(s, new Set());
});
for (const [src, row] of Object.entries(automatonDef.transitions || {})) {
if (!adj.has(src)) continue;
for (const dests of Object.values(row || {})) {
const list = Array.isArray(dests) ? dests : [dests];
for (const d of list) {
if (adj.has(d) && d !== src) {
adj.get(src).add(d);
pred.get(d).add(src);
}
}
}
}
const rankMap = new Map();
if (start && adj.has(start)) {
rankMap.set(start, 0);
const q = [start];
while (q.length > 0) {
const u = q.shift();
const r = rankMap.get(u);
for (const v of adj.get(u) || []) {
if (!rankMap.has(v)) {
rankMap.set(v, r + 1);
q.push(v);
}
}
}
}
let maxRank = 0;
for (const r of rankMap.values()) if (r > maxRank) maxRank = r;
for (const st of nonSinkStates) {
if (!rankMap.has(st)) {
maxRank += 1;
rankMap.set(st, maxRank);
}
}
const layers = new Map();
for (const st of nonSinkStates) {
const r = rankMap.get(st) || 0;
if (!layers.has(r)) layers.set(r, []);
layers.get(r).push(st);
}
const sortedRanks = Array.from(layers.keys()).sort((a, b) => a - b);
const tempOrderPos = {};
sortedRanks.forEach(rk => {
layers.get(rk).forEach((st, idx) => { tempOrderPos[st] = idx; });
});
for (let pass = 0; pass < 2; pass++) {
for (let c = 1; c < sortedRanks.length; c++) {
const rk = sortedRanks[c];
const arr = layers.get(rk);
arr.sort((a, b) => {
const pa = Array.from(pred.get(a) || []);
const pb = Array.from(pred.get(b) || []);
const ba = pa.length ? pa.reduce((acc, u) => acc + (tempOrderPos[u] ?? 0), 0) / pa.length : (tempOrderPos[a] ?? 0);
const bb = pb.length ? pb.reduce((acc, u) => acc + (tempOrderPos[u] ?? 0), 0) / pb.length : (tempOrderPos[b] ?? 0);
if (Math.abs(ba - bb) > 1e-4) return ba - bb;
return asciiCompare(a, b);
});
arr.forEach((st, idx) => { tempOrderPos[st] = idx; });
}
}
const hasLongSubsets = states.some(s => s.length > 9);
const colGap = hasLongSubsets ? 258 : 224;
const rowGap = hasLongSubsets ? 192 : 168;
const coords = {};
let minMainY = 0, maxMainY = 0;
sortedRanks.forEach((rk, colIdx) => {
const colStates = layers.get(rk);
const m = colStates.length;
const x = colIdx * colGap;
colStates.forEach((st, rowIdx) => {
const startY = -((m - 1) * rowGap) / 2;
const stagger = (m === 1 && sortedRanks.length >= 3 && colIdx > 0 && colIdx % 2 === 1) ? -28 : 0;
const y = startY + rowIdx * rowGap + stagger;
if (y < minMainY) minMainY = y;
if (y > maxMainY) maxMainY = y;
coords[st] = { x, y, col: colIdx, row: rowIdx, colSize: m, isSink: false };
});
});
if (states.includes("Ø")) {
if (nonSinkStates.length === 0) {
coords["Ø"] = { x: 0, y: 0, col: 0, row: 0, colSize: 1, isSink: true };
} else {
const totalWidth = Math.max(0, (sortedRanks.length - 1) * colGap);
const sinkX = sortedRanks.length >= 2 ? Math.round(totalWidth * 0.54) : Math.round(colGap * 0.85);
const sinkY = Math.round(maxMainY + rowGap * 1.04);
coords["Ø"] = { x: sinkX, y: sinkY, col: sortedRanks.length, row: 99, colSize: 1, isSink: true };
}
}
return coords;
}
function splitNodeLabelLines(st) {
if (st.length <= 11) return [st];
if (st.includes(" ≡ ")) {
const eqParts = st.split(" ≡ ");
if (eqParts.length === 2) return [eqParts[0] + " ≡", eqParts[1]];
}
if (!st.includes(",")) return [st];
const inner = (st.startsWith("{") && st.endsWith("}")) ? st.slice(1, -1) : st;
const parts = inner.split(",").map(x => x.trim());
if (parts.length <= 3) return [st];
const mid = Math.ceil(parts.length / 2);
return [
"{" + parts.slice(0, mid).join(", ") + ",",
parts.slice(mid).join(", ") + "}"
];
}
function normalizeHighlightConfig(highlightSpec, activeEdge) {
if (Array.isArray(highlightSpec) || !highlightSpec) {
return {
greenStates: new Set(highlightSpec || []),
originStates: new Set(),
moveStates: new Set(),
sourceHaloStates: new Set(),
nodePaletteMap: {},
edges: activeEdge ? [{ src: activeEdge.src, dest: activeEdge.dest, symbol: activeEdge.symbol, role: "move" }] : [],
dimInactive: false
};
}
return {
greenStates: new Set(highlightSpec.greenStates || []),
originStates: new Set(highlightSpec.originStates || []),
moveStates: new Set(highlightSpec.moveStates || []),
sourceHaloStates: new Set(highlightSpec.sourceHaloStates || []),
nodePaletteMap: highlightSpec.nodePaletteMap || {},
edges: highlightSpec.edges || [],
dimInactive: Boolean(highlightSpec.dimInactive)
};
}
function distPointToSegment(px, py, x1, y1, x2, y2) {
const dx = x2 - x1, dy = y2 - y1;
const lenSq = dx * dx + dy * dy;
if (lenSq < 1e-6) return Math.hypot(px - x1, py - y1);
const t = Math.max(0.08, Math.min(0.92, ((px - x1) * dx + (py - y1) * dy) / lenSq));
return Math.hypot(px - (x1 + t * dx), py - (y1 + t * dy));
}
function buildAutomatonSvgMarkup(automatonDef, highlightSpec = [], activeEdge = null, graphKey = "default") {
if (!automatonDef || !automatonDef.states || automatonDef.states.length === 0) {
return `<div style="font-size:0.95rem;color:#94a3b8;padding:16px;">No states to display</div>`;
}
const states = automatonDef.states;
const acceptSet = new Set(automatonDef.accept_states || []);
const badgeMap = automatonDef.nodeBadges || {};
const cfg = normalizeHighlightConfig(highlightSpec, activeEdge);
const baseCoords = computeLayeredLayout(automatonDef);
const customOverrides = appState.customNodePositions[graphKey] || {};
const coords = {};
for (const st of states) {
coords[st] = customOverrides[st]
? { ...baseCoords[st], x: customOverrides[st].x, y: customOverrides[st].y }
: { ...baseCoords[st] };
}
const nodeRadius = {};
for (const st of states) {
const lines = splitNodeLabelLines(st);
nodeRadius[st] = lines.length > 1 ? 43 : (st.length > 7 ? 38 : 33);
}
let graphMinY = Infinity, graphMaxY = -Infinity;
for (const st of states) {
if (coords[st].y < graphMinY) graphMinY = coords[st].y;
if (coords[st].y > graphMaxY) graphMaxY = coords[st].y;
}
const graphMidY = (graphMinY + graphMaxY) / 2;
const edgeGroups = new Map();
for (const [src, row] of Object.entries(automatonDef.transitions || {})) {
for (const [sym, dests] of Object.entries(row || {})) {
const list = Array.isArray(dests) ? dests : [dests];
for (const dest of list) {
if (!coords[src] || !coords[dest]) continue;
const key = `${src}|||${dest}`;
if (!edgeGroups.has(key)) edgeGroups.set(key, []);
if (!edgeGroups.get(key).includes(sym)) edgeGroups.get(key).push(sym);
}
}
}
let minX = Infinity, minY = Infinity, maxX = -Infinity, maxY = -Infinity;
function expandBounds(x, y, pad = 0) {
if (x - pad < minX) minX = x - pad;
if (x + pad > maxX) maxX = x + pad;
if (y - pad < minY) minY = y - pad;
if (y + pad > maxY) maxY = y + pad;
}
for (const st of states) {
const extraHalo = cfg.sourceHaloStates.has(st) ? 10 : 0;
const extraBadge = badgeMap[st] ? 16 : 0;
expandBounds(coords[st].x, coords[st].y, nodeRadius[st] + 10 + extraHalo + extraBadge);
}
const uid = "g" + graphKey.replace(/[^A-Za-z0-9]/g, "") + Math.random().toString(36).slice(2, 6);
let edgesSvg = "";
let labelsSvg = "";
let nodesSvg = "";
const startPos = coords[automatonDef.start_state];
if (startPos) {
const r0 = nodeRadius[automatonDef.start_state];
const sx1 = startPos.x - (r0 + 42);
const sx2 = startPos.x - (r0 + 4);
expandBounds(sx1, startPos.y, 8);
const startStroke = cfg.dimInactive ? "#93c5fd" : "#2563eb";
edgesSvg += `<line x1="${sx1}" y1="${startPos.y}" x2="${sx2}" y2="${startPos.y}" stroke="${startStroke}" stroke-width="2.6" marker-end="url(#arrow-start-${uid})" />`;
}
let upperLaneCount = 0;
let lowerLaneCount = 0;
const labelBoxes = [];
for (const [key, syms] of edgeGroups.entries()) {
const [src, dest] = key.split("|||");
const p1 = coords[src], p2 = coords[dest];
const r1 = nodeRadius[src], r2 = nodeRadius[dest];
const matchedMoveSyms = new Set(
cfg.edges.filter(e => e.src === src && e.dest === dest && e.role === "move").map(e => e.symbol)
);
const matchedEpsSyms = new Set(
cfg.edges.filter(e => e.src === src && e.dest === dest && e.role === "eps").map(e => e.symbol)
);
const isMoveHit = syms.some(s => matchedMoveSyms.has(s));
const isEpsHit = !isMoveHit && syms.some(s => matchedEpsSyms.has(s));
const isActiveFlow = isMoveHit || isEpsHit;
let strokeColor = "#475569";
let strokeWidth = "1.85";
let marker = `url(#arrow-${uid})`;
let pillBg = "#ffffff";
let pillStroke = "#cbd5e1";
if (isMoveHit) {
strokeColor = "#dc2626";
strokeWidth = "3.4";
marker = `url(#arrow-active-${uid})`;
pillBg = "#fff1f2";
pillStroke = "#fda4af";
} else if (isEpsHit) {
strokeColor = "#16a34a";
strokeWidth = "3.3";
marker = `url(#arrow-eps-${uid})`;
pillBg = "#f0fdf4";
pillStroke = "#86efac";
} else if (cfg.dimInactive) {
strokeColor = "#cbd5e1";
strokeWidth = "1.35";
marker = `url(#arrow-dim-${uid})`;
}
const plainLabel = syms.map(s => s === "e" ? "ε" : s).join(", ");
const pillW = Math.max(24, plainLabel.length * 8.5 + 14);
const pillH = 20;
const labelSpansHtml = syms.map((s, idx) => {
const disp = escapeHtml(s === "e" ? "ε" : s);
const sep = idx < syms.length - 1 ? ", " : "";
let fillCol = cfg.dimInactive ? "#94a3b8" : "#0f172a";
if (matchedMoveSyms.has(s)) fillCol = "#dc2626";
else if (matchedEpsSyms.has(s)) fillCol = "#15803d";
return `<tspan fill="${fillCol}">${disp}</tspan>${sep ? `<tspan fill="#94a3b8">${sep}</tspan>` : ""}`;
}).join("");
let pathD = "";
let anchorX = 0, anchorY = 0;
if (src === dest) {
const loopDown = p1.isSink || (states.length > 2 && p1.y > graphMidY + 25);
const dir = loopDown ? 1 : -1;
const ly = p1.y + dir * r1;
const ctrlY = ly + dir * 48;
pathD = `M ${p1.x - 13} ${ly - dir * 2} C ${p1.x - 32} ${ctrlY}, ${p1.x + 32} ${ctrlY}, ${p1.x + 13} ${ly - dir * 2}`;
anchorX = p1.x;
anchorY = ly + dir * 42;
expandBounds(anchorX, anchorY, pillW / 2 + 10);
} else {
const hasReverse = edgeGroups.has(`${dest}|||${src}`);
const dx = p2.x - p1.x, dy = p2.y - p1.y;
const dist = Math.hypot(dx, dy) || 1;
const ux = dx / dist, uy = dy / dist;
const nx = -uy, ny = ux;
let hitsObstacle = false;
for (const other of states) {
if (other === src || other === dest) continue;
const po = coords[other];
const dSeg = distPointToSegment(po.x, po.y, p1.x, p1.y, p2.x, p2.y);
if (dSeg < nodeRadius[other] + 30) {
hitsObstacle = true;
break;
}
}
const colSpan = Math.abs((p2.col || 0) - (p1.col || 0));
const isBackEdge = p2.x < p1.x - 20;
let offX = 0, offY = 0;
let labelT = 0.5;
if (hasReverse) {
const sign = asciiCompare(src, dest) < 0 ? 1 : -1;
offX = nx * 40;
offY = ny * 40;
labelT = sign > 0 ? 0.43 : 0.57;
} else if (p2.isSink && hitsObstacle) {
lowerLaneCount += 1;
offY = 46 + lowerLaneCount * 28;
offX = (p1.x < p2.x ? -18 : 18);
labelT = 0.42;
} else if (hitsObstacle || isBackEdge || colSpan > 1) {
const midY = (p1.y + p2.y) / 2;
const bowUp = (midY <= graphMidY) && !isBackEdge;
if (bowUp) {
upperLaneCount += 1;
const mag = 56 + upperLaneCount * 34 + Math.max(0, colSpan - 1) * 14;
offY = -mag;
} else {
lowerLaneCount += 1;
const mag = 56 + lowerLaneCount * 34 + Math.max(0, colSpan - 1) * 14;
offY = mag;
}
labelT = isBackEdge ? 0.48 : 0.45;
}
const cx = (p1.x + p2.x) / 2 + offX;
const cy = (p1.y + p2.y) / 2 + offY;
const startDirX = cx - p1.x, startDirY = cy - p1.y;
const startLen = Math.hypot(startDirX, startDirY) || 1;
const sx = p1.x + (startDirX / startLen) * r1;
const sy = p1.y + (startDirY / startLen) * r1;
const endDirX = p2.x - cx, endDirY = p2.y - cy;
const endLen = Math.hypot(endDirX, endDirY) || 1;
const ex = p2.x - (endDirX / endLen) * (r2 + 4);
const ey = p2.y - (endDirY / endLen) * (r2 + 4);
pathD = `M ${sx.toFixed(1)} ${sy.toFixed(1)} Q ${cx.toFixed(1)} ${cy.toFixed(1)} ${ex.toFixed(1)} ${ey.toFixed(1)}`;
const omt = 1 - labelT;
anchorX = omt * omt * sx + 2 * omt * labelT * cx + labelT * labelT * ex;
anchorY = omt * omt * sy + 2 * omt * labelT * cy + labelT * labelT * ey;
expandBounds(cx, cy, 18);
}
const safeSrc = escapeHtml(src);
const safeDst = escapeHtml(dest);
if (isActiveFlow) {
edgesSvg += `<g class="svg-edge-group" data-src="${safeSrc}" data-dest="${safeDst}">
<path d="${pathD}" fill="none" stroke="${strokeColor}" stroke-opacity="0.28" stroke-width="${Number(strokeWidth) + 1.8}" />
<path d="${pathD}" class="edge-flow-pulse" fill="none" stroke="${strokeColor}" stroke-width="${strokeWidth}" marker-end="${marker}" />
</g>`;
} else {
edgesSvg += `<g class="svg-edge-group" data-src="${safeSrc}" data-dest="${safeDst}">
<path d="${pathD}" fill="none" stroke="${strokeColor}" stroke-width="${strokeWidth}" marker-end="${marker}" />
</g>`;
}
labelBoxes.push({
src, dest,
ax: anchorX, ay: anchorY,
x: anchorX, y: anchorY,
w: pillW, h: pillH,
pillBg, pillStroke, labelSpansHtml
});
}
for (let iter = 0; iter < 14; iter++) {
for (const lb of labelBoxes) {
for (const st of states) {
const pc = coords[st];
const minClear = nodeRadius[st] + Math.max(lb.h / 2, 12) + 6;
const dx = lb.x - pc.x, dy = lb.y - pc.y;
const d = Math.hypot(dx, dy) || 0.1;
if (d < minClear) {
const push = (minClear - d) * 0.75;
lb.x += (dx / d) * push;
lb.y += (dy / d) * push;
}
}
}
for (let i = 0; i < labelBoxes.length; i++) {
for (let j = i + 1; j < labelBoxes.length; j++) {
const a = labelBoxes[i], b = labelBoxes[j];
const overlapX = (a.w / 2 + b.w / 2 + 7) - Math.abs(a.x - b.x);
const overlapY = (a.h / 2 + b.h / 2 + 6) - Math.abs(a.y - b.y);
if (overlapX > 0 && overlapY > 0) {
if (overlapX < overlapY) {
const dir = a.x <= b.x ? -1 : 1;
a.x += dir * (overlapX / 2);
b.x -= dir * (overlapX / 2);
} else {
const dir = a.y <= b.y ? -1 : 1;
a.y += dir * (overlapY / 2);
b.y -= dir * (overlapY / 2);
}
}
}
}
}
for (const lb of labelBoxes) {
expandBounds(lb.x, lb.y, lb.w / 2 + 8);
const shiftDist = Math.hypot(lb.x - lb.ax, lb.y - lb.ay);
const leader = shiftDist > 13
? `<line x1="${lb.ax.toFixed(1)}" y1="${lb.ay.toFixed(1)}" x2="${lb.x.toFixed(1)}" y2="${lb.y.toFixed(1)}" stroke="#94a3b8" stroke-width="1" stroke-dasharray="2,2" />`
: "";
labelsSvg += `<g class="svg-edge-group" data-src="${escapeHtml(lb.src)}" data-dest="${escapeHtml(lb.dest)}">
${leader}
<rect x="${(lb.x - lb.w / 2).toFixed(1)}" y="${(lb.y - lb.h / 2).toFixed(1)}" width="${lb.w}" height="${lb.h}" rx="5" fill="${lb.pillBg}" fill-opacity="0.97" stroke="${lb.pillStroke}" stroke-width="1" />
<text x="${lb.x.toFixed(1)}" y="${(lb.y + 4.5).toFixed(1)}" text-anchor="middle" font-size="13" font-family="Arial, sans-serif" font-weight="700">${lb.labelSpansHtml}</text>
</g>`;
}
for (const st of states) {
const { x, y } = coords[st];
const R = nodeRadius[st];
let fill = "#ffffff", stroke = cfg.dimInactive ? "#94a3b8" : "#64748b", sw = "1.9";
if (cfg.nodePaletteMap && cfg.nodePaletteMap[st]) {
fill = cfg.nodePaletteMap[st].fill;
stroke = cfg.nodePaletteMap[st].stroke;
sw = cfg.nodePaletteMap[st].sw || "2.5";
} else if (cfg.originStates.has(st) || cfg.moveStates.has(st)) {
fill = "#fef08a"; stroke = "#ca8a04"; sw = "3.3";
} else if (cfg.greenStates.has(st)) {
fill = "#86efac"; stroke = "#15803d"; sw = "3.3";
} else if (cfg.sourceHaloStates.has(st)) {
fill = "#dbeafe"; stroke = "#1d4ed8"; sw = "2.5";
} else if (!cfg.dimInactive && st === automatonDef.start_state) {
fill = "#dbeafe"; stroke = "#1d4ed8"; sw = "2.4";
} else if (st === "Ø") {
fill = "#fee2e2"; stroke = "#b91c1c"; sw = "2.1";
}
const haloSvg = cfg.sourceHaloStates.has(st)
? `<circle cx="${x}" cy="${y}" r="${R + 6}" fill="none" stroke="#2563eb" stroke-width="2.4" stroke-dasharray="5,3" />`
: "";
const innerAcceptSvg = acceptSet.has(st)
? `<circle cx="${x}" cy="${y}" r="${R - 5.5}" fill="none" stroke="${stroke}" stroke-width="1.8" />`
: "";
const textFill = (cfg.dimInactive && fill === "#ffffff") ? "#64748b" : "#0f172a";
const lines = splitNodeLabelLines(st);
let textSvg = "";
if (lines.length === 1) {
const fontSize = st.length > 9 ? 11.6 : (st.length > 5 ? 13 : 15);
textSvg = `<text x="${x}" y="${y + 4.8}" text-anchor="middle" font-size="${fontSize}" font-family="Arial, sans-serif" font-weight="700" fill="${textFill}">${escapeHtml(lines[0])}</text>`;
} else {
textSvg = `<text x="${x}" y="${y - 3}" text-anchor="middle" font-size="11" font-family="Arial, sans-serif" font-weight="700" fill="${textFill}">
<tspan x="${x}" dy="0">${escapeHtml(lines[0])}</tspan>
<tspan x="${x}" dy="13.5">${escapeHtml(lines[1])}</tspan>
</text>`;
}
let badgeSvg = "";
const bTxt = badgeMap[st];
if (bTxt) {
const bw = Math.max(24, bTxt.length * 7.2 + 10);
const bx = x + R * 0.68;
const by = y - R * 0.82;
expandBounds(bx, by, bw / 2 + 4);
badgeSvg = `
<rect x="${(bx - bw / 2).toFixed(1)}" y="${(by - 9.5).toFixed(1)}" width="${bw}" height="18" rx="9" fill="#eff6ff" stroke="#60a5fa" stroke-width="1.1" />
<text x="${bx.toFixed(1)}" y="${(by + 3.5).toFixed(1)}" text-anchor="middle" font-size="10.8" font-family="Arial, sans-serif" font-weight="700" fill="#1d4ed8">${escapeHtml(bTxt)}</text>
`;
}
nodesSvg += `<g class="svg-state-node" data-state="${escapeHtml(st)}" data-x="${x}" data-y="${y}">
${haloSvg}
<circle cx="${x}" cy="${y}" r="${R}" fill="${fill}" stroke="${stroke}" stroke-width="${sw}" />
${innerAcceptSvg}
${textSvg}
${badgeSvg}
</g>`;
}
const margin = 26;
const baseVbX = Math.floor(minX - margin);
const baseVbY = Math.floor(minY - margin);
const baseVbW = Math.max(240, Math.ceil((maxX - minX) + margin * 2));
const baseVbH = Math.max(180, Math.ceil((maxY - minY) + margin * 2));
const cam = appState.graphCameras[graphKey] || { zoom: 1, panX: 0, panY: 0 };
const effW = baseVbW / cam.zoom;
const effH = baseVbH / cam.zoom;
const effX = baseVbX + (baseVbW - effW) / 2 + cam.panX;
const effY = baseVbY + (baseVbH - effH) / 2 + cam.panY;
return `<svg class="interactive-automaton-svg" data-graph-key="${escapeHtml(graphKey)}" data-base-vbx="${baseVbX}" data-base-vby="${baseVbY}" data-base-vbw="${baseVbW}" data-base-vbh="${baseVbH}" xmlns="http://www.w3.org/2000/svg" viewBox="${effX.toFixed(1)} ${effY.toFixed(1)} ${effW.toFixed(1)} ${effH.toFixed(1)}">
<defs>
<marker id="arrow-${uid}" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="6.5" markerHeight="6.5" orient="auto-start-reverse">
<path d="M 0 1 L 10 5 L 0 9 z" fill="#475569"/>
</marker>
<marker id="arrow-dim-${uid}" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="6" markerHeight="6" orient="auto-start-reverse">
<path d="M 0 1 L 10 5 L 0 9 z" fill="#cbd5e1"/>
</marker>
<marker id="arrow-active-${uid}" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="7" markerHeight="7" orient="auto-start-reverse">
<path d="M 0 1 L 10 5 L 0 9 z" fill="#dc2626"/>
</marker>
<marker id="arrow-eps-${uid}" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="7" markerHeight="7" orient="auto-start-reverse">
<path d="M 0 1 L 10 5 L 0 9 z" fill="#16a34a"/>
</marker>
<marker id="arrow-start-${uid}" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="6.5" markerHeight="6.5" orient="auto">
<path d="M 0 1 L 10 5 L 0 9 z" fill="#2563eb"/>
</marker>
</defs>
${edgesSvg}
${labelsSvg}
${nodesSvg}
</svg>`;
}
function renderAutomatonSvg(automatonDef, highlightSpec = [], activeEdge = null, graphKey = null, allowExpandToggle = true) {
const key = graphKey || ("g_" + (automatonDef && automatonDef.states ? automatonDef.states.join("_").replace(/[^A-Za-z0-9_]/g, "") : "empty"));
appState.graphRegistry[key] = { automatonDef, highlightSpec, activeEdge, allowExpandToggle };
const cam = appState.graphCameras[key] || { zoom: 1, panX: 0, panY: 0 };
const zoomPct = Math.round(cam.zoom * 100);
const expandBtn = allowExpandToggle
? `<button type="button" class="graph-hud-btn" onclick="toggleFullWidthGraph()" title="Toggle 100% Full-Width vs 60/40 Side-by-Side">${appState.fullWidthGraph ? "🗗 60/40" : "⛶ Full"}</button>`
: "";
return `
<span class="graph-hud-hint">✥ Drag nodes · Scroll zoom</span>
<div class="graph-floating-hud">
<button type="button" class="graph-hud-btn" onclick="zoomGraphCamera('${escapeHtml(key)}', 0.85)" title="Zoom Out">−</button>
<span style="font-family:var(--mono);font-size:0.73rem;color:#475569;min-width:36px;text-align:center;">${zoomPct}%</span>
<button type="button" class="graph-hud-btn" onclick="zoomGraphCamera('${escapeHtml(key)}', 1.18)" title="Zoom In">+</button>
<button type="button" class="graph-hud-btn" onclick="resetGraphLayout('${escapeHtml(key)}')" title="Reset Auto-Layout &amp; Zoom">↺ Auto</button>
${expandBtn}
</div>
<div class="svg-stage-slot" data-slot-key="${escapeHtml(key)}" style="width:100%;display:flex;align-items:center;justify-content:center;">
${buildAutomatonSvgMarkup(automatonDef, highlightSpec, activeEdge, key)}
</div>
`;
}
function rerenderSingleGraph(graphKey) {
const reg = appState.graphRegistry[graphKey];
if (!reg) return;
document.querySelectorAll(`.svg-stage-slot[data-slot-key="${CSS.escape(graphKey)}"]`).forEach(slot => {
slot.innerHTML = buildAutomatonSvgMarkup(reg.automatonDef, reg.highlightSpec, reg.activeEdge, graphKey);
const frame = slot.closest(".st-graph-frame");
if (frame) {
const pctSpan = frame.querySelector(".graph-floating-hud span");
const cam = appState.graphCameras[graphKey] || { zoom: 1, panX: 0, panY: 0 };
if (pctSpan) pctSpan.textContent = `${Math.round(cam.zoom * 100)}%`;
}
});
}
(function setupInteractiveSvgDelegation() {
let dragCtx = null;
function clientToSvgDelta(svgEl, dxPx, dyPx) {
const vb = svgEl.viewBox.baseVal;
const rect = svgEl.getBoundingClientRect();
if (!vb || !rect.width || !rect.height) return { dx: dxPx, dy: dyPx };
return {
dx: dxPx * (vb.width / rect.width),
dy: dyPx * (vb.height / rect.height)
};
}
document.addEventListener("pointerdown", (ev) => {
if (ev.button !== 0) return;
const nodeEl = ev.target.closest ? ev.target.closest(".svg-state-node") : null;
const svgEl = ev.target.closest ? ev.target.closest("svg.interactive-automaton-svg") : null;
if (!svgEl) return;
const graphKey = svgEl.getAttribute("data-graph-key");
if (!graphKey) return;
if (nodeEl) {
const stName = nodeEl.getAttribute("data-state");
const startX = parseFloat(nodeEl.getAttribute("data-x") || "0");
const startY = parseFloat(nodeEl.getAttribute("data-y") || "0");
dragCtx = {
mode: "node",
graphKey,
stateName: stName,
clientX0: ev.clientX,
clientY0: ev.clientY,
origX: startX,
origY: startY,
svgEl,
rafPending: false
};
nodeEl.classList.add("is-dragging");
ev.preventDefault();
} else {
const cam = appState.graphCameras[graphKey] || { zoom: 1, panX: 0, panY: 0 };
dragCtx = {
mode: "pan",
graphKey,
clientX0: ev.clientX,
clientY0: ev.clientY,
origPanX: cam.panX,
origPanY: cam.panY,
zoom: cam.zoom,
svgEl,
rafPending: false
};
const frame = svgEl.closest(".st-graph-frame");
if (frame) frame.classList.add("is-panning");
ev.preventDefault();
}
});
document.addEventListener("pointermove", (ev) => {
if (!dragCtx) {
const hoverNode = ev.target.closest ? ev.target.closest(".svg-state-node") : null;
const hoverSvg = ev.target.closest ? ev.target.closest("svg.interactive-automaton-svg") : null;
document.querySelectorAll("svg.interactive-automaton-svg.has-hover-focus").forEach(s => {
if (s !== hoverSvg || !hoverNode) {
s.classList.remove("has-hover-focus");
s.querySelectorAll(".is-incident-edge, .is-incident-node").forEach(el => {
el.classList.remove("is-incident-edge", "is-incident-node");
});
}
});
if (hoverNode && hoverSvg) {
const st = hoverNode.getAttribute("data-state");
hoverSvg.classList.add("has-hover-focus");
const connected = new Set([st]);
hoverSvg.querySelectorAll(".svg-edge-group").forEach(eg => {
const s = eg.getAttribute("data-src"), d = eg.getAttribute("data-dest");
const inc = (s === st || d === st);
eg.classList.toggle("is-incident-edge", inc);
if (inc) { connected.add(s); connected.add(d); }
});
hoverSvg.querySelectorAll(".svg-state-node").forEach(nd => {
nd.classList.toggle("is-incident-node", connected.has(nd.getAttribute("data-state")));
});
}
return;
}
const liveSvg = document.querySelector(`svg.interactive-automaton-svg[data-graph-key="${CSS.escape(dragCtx.graphKey)}"]`) || dragCtx.svgEl;
const delta = clientToSvgDelta(liveSvg, ev.clientX - dragCtx.clientX0, ev.clientY - dragCtx.clientY0);
if (dragCtx.mode === "node") {
if (!appState.customNodePositions[dragCtx.graphKey]) {
appState.customNodePositions[dragCtx.graphKey] = {};
}
appState.customNodePositions[dragCtx.graphKey][dragCtx.stateName] = {
x: Math.round(dragCtx.origX + delta.dx),
y: Math.round(dragCtx.origY + delta.dy)
};
} else {
appState.graphCameras[dragCtx.graphKey] = {
zoom: dragCtx.zoom,
panX: Math.round(dragCtx.origPanX - delta.dx),
panY: Math.round(dragCtx.origPanY - delta.dy)
};
}
if (!dragCtx.rafPending) {
dragCtx.rafPending = true;
requestAnimationFrame(() => {
if (!dragCtx) return;
dragCtx.rafPending = false;
rerenderSingleGraph(dragCtx.graphKey);
});
}
});
document.addEventListener("pointerup", () => {
if (!dragCtx) return;
document.querySelectorAll(".st-graph-frame.is-panning").forEach(f => f.classList.remove("is-panning"));
dragCtx = null;
});
document.addEventListener("wheel", (ev) => {
const svgEl = ev.target.closest ? ev.target.closest("svg.interactive-automaton-svg") : null;
if (!svgEl) return;
ev.preventDefault();
const graphKey = svgEl.getAttribute("data-graph-key");
if (!graphKey) return;
const factor = ev.deltaY < 0 ? 1.12 : 0.89;
zoomGraphCamera(graphKey, factor);
}, { passive: false });
})();
