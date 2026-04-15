// msb_rename_utility — minimal vanilla JS client.
//
// Client-side shape mirrors the server contract exactly:
//   pipeline = [{ op: "<name>", params: {...} }, ...]
// We never construct filenames on the client — preview is always
// computed server-side so the docs and UI describe the same semantics.
// All DOM built via createElement/textContent — no innerHTML, no XSS surface.

const $ = (sel) => document.querySelector(sel);
const el = (tag, attrs = {}, ...children) => {
  const node = document.createElement(tag);
  for (const [k, v] of Object.entries(attrs)) {
    if (k === "class") node.className = v;
    else if (k === "text") node.textContent = v;
    else if (k.startsWith("on")) node.addEventListener(k.slice(2), v);
    else node.setAttribute(k, v);
  }
  for (const c of children) if (c != null) node.append(c);
  return node;
};

const OP_SPECS = {
  case: [
    { k: "mode", label: "mode", type: "select", options: ["lower", "upper", "title", "sentence"], default: "lower" },
    { k: "scope", label: "scope", type: "select", options: ["stem", "ext", "both"], default: "stem" },
  ],
  replace: [
    { k: "find", label: "find", type: "text", default: "" },
    { k: "with", label: "with", type: "text", default: "" },
    { k: "case_sensitive", label: "case-sens", type: "checkbox", default: true },
  ],
  regex: [
    { k: "pattern", label: "pattern", type: "text", default: "" },
    { k: "repl", label: "repl", type: "text", default: "" },
    { k: "flags", label: "flags (i,m,s)", type: "text", default: "" },
  ],
  insert: [
    { k: "text", label: "text", type: "text", default: "" },
    { k: "at", label: "at", type: "text", default: "0" },
  ],
  numbering: [
    { k: "start", label: "start", type: "number", default: 1 },
    { k: "step", label: "step", type: "number", default: 1 },
    { k: "pad", label: "pad", type: "number", default: 3 },
    { k: "position", label: "pos", type: "select", options: ["suffix", "prefix"], default: "suffix" },
    { k: "sep", label: "sep", type: "text", default: "_" },
  ],
  pad: [
    { k: "width", label: "width", type: "number", default: 4 },
    { k: "scope", label: "scope", type: "select", options: ["stem", "name"], default: "stem" },
  ],
  trim: [
    { k: "chars", label: "chars (blank=ws)", type: "text", default: "" },
    { k: "side", label: "side", type: "select", options: ["both", "left", "right"], default: "both" },
  ],
  remove_at: [
    { k: "start", label: "start", type: "number", default: 0 },
    { k: "count", label: "count", type: "number", default: 1 },
  ],
  change_ext: [
    { k: "to", label: "to", type: "text", default: "" },
    { k: "only_if", label: "only_if (blank=any)", type: "text", default: "" },
  ],
  date_from_mtime: [
    { k: "format", label: "format", type: "text", default: "%Y-%m-%d" },
    { k: "position", label: "pos", type: "select", options: ["prefix", "suffix"], default: "prefix" },
    { k: "sep", label: "sep", type: "text", default: "_" },
  ],
};

let pipeline = []; // [{op, params}]

function renderParam(step, spec) {
  let input;
  if (spec.type === "select") {
    input = el("select");
    for (const opt of spec.options) input.append(el("option", { value: opt, text: opt }));
  } else if (spec.type === "checkbox") {
    input = el("input", { type: "checkbox" });
  } else {
    input = el("input", { type: spec.type });
  }
  const cur = step.params[spec.k] ?? spec.default;
  if (spec.type === "checkbox") input.checked = !!cur;
  else input.value = cur;
  input.addEventListener("input", () => {
    if (spec.type === "checkbox") step.params[spec.k] = input.checked;
    else if (spec.type === "number") step.params[spec.k] = Number(input.value);
    else step.params[spec.k] = input.value;
  });
  return el("span", { class: "param" }, el("label", { text: spec.label }), input);
}

function render() {
  const host = $("#pipeline");
  host.replaceChildren();
  pipeline.forEach((step, i) => {
    const row = el("div", { class: "op-row" },
      el("span", { class: "op-name", text: step.op }),
    );
    for (const spec of OP_SPECS[step.op]) row.append(renderParam(step, spec));
    row.append(el("button", {
      class: "remove", text: "×", title: "remove op",
      onclick: () => { pipeline.splice(i, 1); render(); },
    }));
    host.append(row);
  });
  updateStatus();
}

function addOp(kind) {
  const params = {};
  for (const spec of OP_SPECS[kind]) params[spec.k] = spec.default;
  pipeline.push({ op: kind, params });
  render();
}

function getFiles() {
  return $("#filesInput").value.split("\n").map(s => s.trim()).filter(Boolean);
}

function updateStatus() {
  const n = getFiles().length;
  $("#statusLine").textContent =
    `${n} file${n === 1 ? "" : "s"} · ${pipeline.length} op${pipeline.length === 1 ? "" : "s"}`;
}

function normalizePipelineForServer() {
  return pipeline.map(step => {
    if (step.op !== "regex") return step;
    const raw = (step.params.flags || "").toString();
    const flags = raw.split(/[\s,]+/).filter(Boolean);
    return { ...step, params: { ...step.params, flags } };
  });
}

function showError(msg) {
  $("#preview").replaceChildren(el("div", { class: "error", text: msg }));
}

async function runPreview() {
  const files = getFiles();
  const host = $("#preview");
  host.replaceChildren();
  if (files.length === 0) { showError("add at least one filename above"); return; }
  let res, data;
  try {
    res = await fetch("/api/preview", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        files,
        pipeline: normalizePipelineForServer(),
        dir: $("#dirInput").value.trim() || undefined,
      }),
    });
    data = await res.json();
  } catch (e) {
    showError(`network error: ${e.message}`); return;
  }
  if (!res.ok) { showError(data.error || "server error"); return; }
  for (const row of data) {
    const newClasses = ["new"];
    if (row.unchanged) newClasses.push("unchanged");
    if (row.collision) newClasses.push("collision");
    host.append(
      el("div", { class: "old", text: row.old }),
      el("div", { class: "arrow", text: "→" }),
      el("div", { class: newClasses.join(" "), text: row.new + (row.collision ? "  ⚠ collision" : "") }),
    );
  }
}

document.querySelectorAll("[data-add]").forEach(b => {
  b.addEventListener("click", () => addOp(b.dataset.add));
});
let lastUndoLog = null; // server-returned path from last successful apply

// ── URL deep links ───────────────────────────────────────────────
// Hash format: #p=<urlsafe-b64 of JSON {pipeline, files?}>
// The hash stays client-side (never sent to server), so sharing doesn't leak
// to server logs. `dir` is deliberately excluded — it's a local path.
function encodeShareHash(payload) {
  const json = JSON.stringify(payload);
  const b64 = btoa(unescape(encodeURIComponent(json)))
    .replaceAll("+", "-").replaceAll("/", "_").replaceAll("=", "");
  return `#p=${b64}`;
}
function decodeShareHash(hash) {
  const m = (hash || "").match(/^#p=(.+)$/);
  if (!m) return null;
  let b64 = m[1].replaceAll("-", "+").replaceAll("_", "/");
  while (b64.length % 4) b64 += "=";
  try {
    return JSON.parse(decodeURIComponent(escape(atob(b64))));
  } catch { return null; }
}

function loadFromHash() {
  const payload = decodeShareHash(location.hash);
  if (!payload) return;
  if (Array.isArray(payload.pipeline)) {
    pipeline = payload.pipeline.map(s => ({ op: s.op, params: { ...s.params } }));
    render();
  }
  if (typeof payload.files === "string" && payload.files) {
    $("#filesInput").value = payload.files;
    updateStatus();
  }
}

function shareLink() {
  const hash = encodeShareHash({
    pipeline,
    files: $("#filesInput").value || undefined,
  });
  const url = `${location.origin}${location.pathname}${hash}`;
  navigator.clipboard.writeText(url).then(
    () => { $("#statusLine").textContent = "link copied to clipboard"; },
    () => { prompt("Copy this link:", url); }
  );
}

async function runApply() {
  const dir = $("#dirInput").value.trim();
  const files = getFiles();
  if (!dir) { showError("`dir` is required for apply — type the absolute directory path above"); return; }
  if (files.length === 0) { showError("add at least one filename"); return; }
  if (!confirm(`About to rename ${files.length} file(s) in:\n${dir}\n\nContinue?`)) return;

  let res, data;
  try {
    res = await fetch("/api/apply", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ dir, files, pipeline: normalizePipelineForServer() }),
    });
    data = await res.json();
  } catch (e) { showError(`network error: ${e.message}`); return; }

  if (!res.ok) { showError(data.error || "apply failed"); return; }
  lastUndoLog = data.undo_log;
  $("#statusLine").textContent = `applied ${data.applied} · undo: ${data.undo_log.split("/").pop()}`;
  runPreview();  // refresh so the grid shows the now-current state
}

async function runUndo() {
  if (!lastUndoLog) { showError("no undo log from this session — paste one manually via /api/undo"); return; }
  if (!confirm("Undo the last apply?")) return;
  const res = await fetch("/api/undo", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ undo_log: lastUndoLog }),
  });
  const data = await res.json();
  if (!res.ok) { showError(data.error || "undo failed"); return; }
  $("#statusLine").textContent = `undone ${data.undone}`;
  lastUndoLog = null;
}

$("#clearBtn").addEventListener("click", () => { pipeline = []; render(); });
$("#runBtn").addEventListener("click", runPreview);
$("#applyBtn").addEventListener("click", runApply);
$("#undoBtn").addEventListener("click", runUndo);
$("#shareBtn").addEventListener("click", shareLink);
$("#filesInput").addEventListener("input", updateStatus);

// ── file pickers ─────────────────────────────────────────────────
// Browser security forbids reading absolute filesystem paths, so pickers
// can only populate the filenames textarea. The user still fills `dir`
// manually (or we work in preview-only mode without it).
function _fillFilesFromList(list) {
  const names = [...list]
    .map(f => (f.webkitRelativePath || f.name).split("/").pop())
    .filter(Boolean);
  if (!names.length) return;
  $("#filesInput").value = names.join("\n");
  updateStatus();
  $("#statusLine").textContent += " · dir not auto-filled (browser restriction) — type it manually for apply";
}

$("#pickFilesBtn").addEventListener("click", () => $("#pickFiles").click());
$("#pickDirBtn").addEventListener("click", () => $("#pickDir").click());
$("#pickFiles").addEventListener("change", e => _fillFilesFromList(e.target.files));
$("#pickDir").addEventListener("change", e => _fillFilesFromList(e.target.files));

loadFromHash();
render();
