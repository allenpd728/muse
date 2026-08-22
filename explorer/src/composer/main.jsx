// Composer shell (issue #80, docs/scope-composer.md task 2): route + node
// palette + reactflow canvas + property inspector for scalar fields.
// The graph is a projection of the schema (task 1's graph.mjs); every edit
// recompiles and revalidates in memory — invalid states surface in the
// inspector, never silently dropped. No audio; export is MVP 5.
import React from "react";
import { createRoot } from "react-dom/client";
import ReactFlow, { Background, Controls, addEdge } from "reactflow";
import "reactflow/dist/style.css";
import { docToGraph, compile } from "./graph.mjs";
import { validateDocument } from "../validate.js";
import { danglingRefs } from "@muse-tools/refs.mjs";
import "../styles.css";

// v0.2 section-role enum (schema/form.schema.json) — pinned in
// composer.test.mjs against the schema.
export const SECTION_ROLES = [
  "intro", "outro", "interlude", "coda", "solo", "custom",
  "verse", "pre_chorus", "chorus", "refrain", "bridge", "hook",
  "exposition", "development", "recapitulation", "episode", "theme",
  "variation", "trio", "minuet", "scherzo", "fugue", "cadenza", "finale",
  "cue", "underscore", "stinger", "main_title", "end_credits",
  "build", "drop", "breakdown", "vamp", "groove",
];

// Node palette: the schema construct types (scope doc). Adding creates a
// node with a fresh key; globals/constraints are singletons.
export const PALETTE = [
  ["motif", "Motif"],
  ["theme", "Theme"],
  ["rhythm", "Rhythm"],
  ["progression", "Progression"],
  ["section", "Section"],
  ["rendition", "Rendition"],
  ["globals", "Globals"],
  ["constraints", "Constraints"],
];

const KIND_LABEL = Object.fromEntries(PALETTE);

// Scalar fields editable in the inspector per kind (MVP 2 scope: scalar
// only; lists/references are MVP 3–4).
const INSPECTOR_FIELDS = {
  motif: [["id", "text"]],
  theme: [["id", "text"], ["cadence", "text"]],
  rhythm: [["id", "text"], ["grid", "text"]],
  progression: [["id", "text"], ["bars_per_chord", "number"]],
  section: [["id", "text"], ["role", "role"], ["bars", "number"], ["energy", "number"]],
  rendition: [["id", "text"], ["name", "text"]],
  globals: [["bpm", "number"], ["feel", "text"], ["duration_bars", "number"]],
  constraints: [],
};

let freshSeq = 0;
const freshKey = (kind) => `${kind}.new_${++freshSeq}`;

// Palette add-node operation (pure, exported for tests): a new node with a
// fresh key; globals/constraints are singletons; section nodes default
// role "custom" (schema-valid).
export const addPaletteNode = (graph, kind) => {
  if ((kind === "globals" || kind === "constraints") && graph.nodes.some((n) => n.kind === kind)) return graph;
  const key = freshKey(kind);
  const fields = kind === "section" ? { id: key, role: "custom" } : { id: key };
  return {
    nodes: [...graph.nodes, { id: `${kind}:${key}`, kind, key, fields, _source: null }],
    edges: graph.edges,
  };
};

// --- MVP 3: edge/reference editing ---

// §2.3 transform vocabulary for the suffix helper.
export const TRANSFORMS = ["seq(+n)", "seq(-n)", "inv", "retro", "aug(n)", "dim(n)"];

// The material id pool a uses ref may target (same pool the harness lints).
const materialNodeIds = (graph) =>
  graph.nodes.filter((n) => ["motif", "theme", "rhythm"].includes(n.kind)).map((n) => n.id);

// Which edge type a reactflow connection creates, by endpoint kinds.
export const edgeTypeFor = (graph, sourceId, targetId) => {
  const kind = (id) => graph.nodes.find((n) => n.id === id)?.kind;
  const [s, t] = [kind(sourceId), kind(targetId)];
  if (s === "section" && ["motif", "theme", "rhythm"].includes(t)) return "uses";
  if (s === "section" && t === "progression") return "harmony";
  if (s === "section" && t === "section") return "order";
  if (s === "theme" && ["motif", "theme", "rhythm"].includes(t)) return "phrase-motif";
  return null;
};

// A ref string decomposed for the helper: base id + suffix chain.
export const splitRef = (ref) => {
  const [base, ...ops] = String(ref ?? "").split("#");
  return { base, suffix: ops.length ? `#${ops.join("#")}` : "" };
};

// --- MVP 4: material editors ---
// Space-separated text lists, parsed per field kind. Parse failures keep the
// last good value (the edit → validate loop would flag a bad write anyway,
// but a half-typed token shouldn't corrupt the document).
export const parseList = (text, kind) => {
  const tokens = String(text).trim().split(/\s+/).filter(Boolean);
  if (kind === "pitches") {
    const bad = tokens.filter((t) => !/^[A-G](#|b)?-?\d+$/.test(t));
    return bad.length ? { error: `not pitches: ${bad.join(", ")}` } : { value: tokens };
  }
  if (kind === "numbers") {
    const bad = tokens.filter((t) => !/^\d+(\.\d+)?$/.test(t) || Number(t) <= 0);
    return bad.length ? { error: `not positive numbers: ${bad.join(", ")}` } : { value: tokens.map(Number) };
  }
  if (kind === "pattern") {
    const bad = tokens.filter((t) => !/^\d+(\.\d+)?$/.test(t));
    return bad.length ? { error: `not numbers: ${bad.join(", ")}` } : { value: tokens.map(Number) };
  }
  return { value: tokens }; // chords: free text (spec §6 open question)
};

const LIST_FIELDS = {
  motif: [["pitches", "pitches"], ["durations", "numbers"]],
  rhythm: [["pattern", "pattern"]],
  progression: [["chords", "chords"]],
};

// --- MVP 5: validation + export ---

// Export shape: provenance entry appended on save per the scope doc —
// event "edit", actor "composer-tool", ai: false. `at` injectable for tests.
export const withExportProvenance = (doc, { at = new Date().toISOString() } = {}) => ({
  ...doc,
  metadata: {
    ...doc.metadata,
    provenance: [
      ...(doc.metadata?.provenance ?? []),
      { event: "edit", actor: "composer-tool", at, ai: false },
    ],
  },
});

// Export filename: doc name with spaces collapsed and any existing JSON
// suffix normalized to .muse.json (exported for tests).
export const exportFilename = (docName) =>
  `${(docName ?? "untitled").replace(/\s+/g, "-").replace(/\.muse\.json$|\.json$/i, "")}.muse.json`;

// Download helper (browser only).
const download = (doc, name) => {
  const blob = new Blob([JSON.stringify(doc, null, 2) + "\n"], { type: "application/json" });
  const a = document.createElement("a");
  a.href = URL.createObjectURL(blob);
  a.download = name;
  a.click();
  URL.revokeObjectURL(a.href);
};

function ListEditor({ node, name, kind, onEdit }) {
  const raw = (node.fields[name] ?? []).join(" ");
  const [text, setText] = React.useState(raw);
  const [error, setError] = React.useState(null);
  React.useEffect(() => { setText(raw); setError(null); }, [raw, node.id]);
  return (
    <label className="field">
      <span>{name}</span>
      <input
        type="text"
        value={text}
        className={error ? "invalid" : ""}
        title={error ?? ""}
        onChange={(e) => {
          setText(e.target.value);
          const r = parseList(e.target.value, kind);
          if (r.error) setError(r.error);
          else { setError(null); onEdit(node.id, name, r.value); }
        }}
      />
    </label>
  );
}

const LAYOUT_X = { globals: 0, constraints: 0, motif: 0, theme: 320, rhythm: 0, progression: 320, section: 640, rendition: 960 };
const LAYOUT_Y = { globals: 0, constraints: 160, motif: 320, rhythm: 320, progression: 320, section: 320, rendition: 320 };

const flowNodes = (graph, selectedId) => {
  const counters = {};
  return graph.nodes.map((n) => {
    const row = counters[n.kind] = (counters[n.kind] ?? 0) + 1;
    return {
      id: n.id,
      position: { x: LAYOUT_X[n.kind] ?? 0, y: (LAYOUT_Y[n.kind] ?? 0) + (row - 1) * 110 },
      data: { label: `${KIND_LABEL[n.kind] ?? n.kind}\n${n.key ?? ""}` },
      style: {
        background: "#1c1f26",
        color: "#d7dce4",
        border: `1px solid ${n.id === selectedId ? "#e0af68" : "#7aa2f7"}`,
        borderRadius: 6,
        whiteSpace: "pre-line",
        fontSize: 12,
        width: 180,
      },
    };
  });
};

const flowEdges = (graph) =>
  graph.edges.map((e, i) => ({
    id: `e${i}`,
    source: e.from,
    target: e.to,
    label: e.type === "uses" && e.data?.ref?.includes("#") ? e.data.ref.split("#").slice(1).join("#") : e.type,
    animated: e.type === "order",
    style: { stroke: "#565f89" },
    labelStyle: { fill: "#9aa5ce", fontSize: 10 },
  }));

// Ref editor for one uses edge: base id (material pool dropdown) +
// transform-suffix helper. Edits write back through onEditEdge.
function UsesRefEditor({ edge, graph, onEditEdge }) {
  const { base, suffix } = splitRef(edge.data.ref);
  const poolKeys = materialNodeIds(graph).map((id) => id.split(":").slice(1).join(":"));
  return (
    <div className="field-row">
      <select
        value={base}
        onChange={(e) => onEditEdge(edge, { ...edge.data, ref: `${e.target.value}${suffix}` })}
      >
        {!poolKeys.includes(base) && <option value={base}>{base} (dangling)</option>}
        {poolKeys.map((key) => <option key={key} value={key}>{key}</option>)}
      </select>
      <select
        value=""
        title="append transform suffix"
        onChange={(e) => {
          if (!e.target.value) return;
          const op = e.target.value.replace("n", "2");
          onEditEdge(edge, { ...edge.data, ref: `${base}${suffix}#${op}` });
        }}
      >
        <option value="">+ transform…</option>
        {TRANSFORMS.map((t) => <option key={t} value={t}>{t}</option>)}
      </select>
      {suffix && (
        <button title="clear transforms" onClick={() => onEditEdge(edge, { ...edge.data, ref: base })}>✕{suffix}</button>
      )}
    </div>
  );
}

function Inspector({ node, graph, onEdit, onEditEdge, onRemoveEdge, onReorder }) {
  if (!node) return <p className="muted">select a node to edit its fields</p>;
  const fields = INSPECTOR_FIELDS[node.kind] ?? [];
  const usesEdges = graph.edges.filter((e) => e.type === "uses" && e.from === node.id);
  const harmonyEdge = graph.edges.find((e) => e.type === "harmony" && e.from === node.id);
  const orderOut = graph.edges.filter((e) => e.type === "order" && e.from === node.id);
  const orderIn = graph.edges.filter((e) => e.type === "order" && e.to === node.id);
  return (
    <div>
      <h3>{KIND_LABEL[node.kind] ?? node.kind} <span className="muted">{node.key ?? ""}</span></h3>
      {fields.map(([name, type]) => (
        <label className="field" key={name}>
          <span>{name}</span>
          {type === "role" ? (
            <select
              value={node.fields.role ?? "custom"}
              onChange={(e) => onEdit(node.id, name, e.target.value)}
            >
              {SECTION_ROLES.map((r) => <option key={r} value={r}>{r}</option>)}
            </select>
          ) : (
            <input
              type={type === "number" ? "number" : "text"}
              step={name === "energy" ? "0.05" : "1"}
              value={node.fields[name] ?? ""}
              onChange={(e) =>
                onEdit(node.id, name, type === "number" ? (e.target.value === "" ? undefined : Number(e.target.value)) : e.target.value)
              }
            />
          )}
        </label>
      ))}
      {(LIST_FIELDS[node.kind] ?? []).map(([name, kind]) => (
        <ListEditor key={name} node={node} name={name} kind={kind} onEdit={onEdit} />
      ))}
      {node.kind === "section" && (
        <>
          <h4>uses</h4>
          {usesEdges.length === 0 && <p className="muted">none — drag from this node to a motif/theme/rhythm</p>}
          {usesEdges.map((e, i) => (
            <div key={i} className="edge-row">
              <UsesRefEditor edge={e} graph={graph} onEditEdge={onEditEdge} />
              <button title="remove" onClick={() => onRemoveEdge(e)}>✕</button>
            </div>
          ))}
          <h4>harmony</h4>
          {harmonyEdge
            ? <div className="edge-row"><span>{harmonyEdge.data.ref}</span><button title="remove" onClick={() => onRemoveEdge(harmonyEdge)}>✕</button></div>
            : <p className="muted">none — drag from this node to a progression</p>}
          <h4>form order</h4>
          <div className="edge-row">
            <button disabled={orderIn.length === 0} onClick={() => onReorder(node.id, -1)}>↑ earlier</button>
            <button disabled={orderOut.length === 0} onClick={() => onReorder(node.id, +1)}>↓ later</button>
          </div>
        </>
      )}
    </div>
  );
}

function Composer() {
  const [doc, setDoc] = React.useState(null);
  const [graph, setGraph] = React.useState({ nodes: [], edges: [] });
  const [docName, setDocName] = React.useState(null);
  const [selectedId, setSelectedId] = React.useState(null);

  const loadText = (text, name) => {
    try {
      const parsed = JSON.parse(text);
      setDoc(parsed);
      setGraph(docToGraph(parsed));
      setDocName(name);
      setSelectedId(null);
    } catch (e) {
      alert(`${name}: ${e.message}`);
    }
  };

  const issues = React.useMemo(() => (doc ? validateDocument(doc) : []), [doc]);

  // Every edit: mutate graph → recompile → revalidate. The recompiled doc
  // is state, so the panel and any future export see the same truth.
  const applyGraph = (next) => {
    setGraph(next);
    setDoc(compile(next, doc));
  };

  const editField = (nodeId, name, value) => {
    applyGraph({
      nodes: graph.nodes.map((n) => (n.id === nodeId ? { ...n, fields: { ...n.fields, [name]: value } } : n)),
      edges: graph.edges,
    });
  };

  const addNode = (kind) => applyGraph(addPaletteNode(graph, kind));

  // --- MVP 3 operations ---

  const keyOf = (nodeId) => nodeId.split(":").slice(1).join(":");

  // reactflow drag-connect: typed by endpoint kinds; anything else rejected.
  const onConnect = React.useCallback((conn) => {
    const type = edgeTypeFor(graph, conn.source, conn.target);
    if (!type) return;
    const data =
      type === "uses" ? { ref: keyOf(conn.target) }
      : type === "harmony" ? { ref: keyOf(conn.target) }
      : type === "order" ? { index: graph.edges.filter((e) => e.type === "order").length }
      : { ref: keyOf(conn.target) };
    // One harmony edge per section: replace, don't stack.
    const edges = type === "harmony"
      ? [...graph.edges.filter((e) => !(e.type === "harmony" && e.from === conn.source)), { from: conn.source, to: conn.target, type, data }]
      : [...graph.edges, { from: conn.source, to: conn.target, type, data }];
    applyGraph({ nodes: graph.nodes, edges });
  }, [graph, doc]);

  const editEdge = (edge, data) => {
    applyGraph({
      nodes: graph.nodes,
      edges: graph.edges.map((e) => (e === edge ? { ...e, data } : e)),
    });
  };

  const removeEdge = (edge) => {
    applyGraph({ nodes: graph.nodes, edges: graph.edges.filter((e) => e !== edge) });
  };

  // Swap this section with its neighbor in form order: rebuild the order
  // edge chain so compile() reproduces the swapped sequence.
  const reorder = (nodeId, dir) => {
    const orderEdges = [...graph.edges.filter((e) => e.type === "order")].sort((a, b) => a.data.index - b.data.index);
    if (orderEdges.length === 0) return;
    const seq = [orderEdges[0].from, ...orderEdges.map((e) => e.to)];
    const i = seq.indexOf(nodeId);
    const j = i + dir;
    if (i < 0 || j < 0 || j >= seq.length) return;
    [seq[i], seq[j]] = [seq[j], seq[i]];
    const others = graph.edges.filter((e) => e.type !== "order");
    const rebuilt = seq.slice(1).map((to, k) => ({ from: seq[k], to, type: "order", data: { index: k } }));
    applyGraph({ nodes: graph.nodes, edges: [...others, ...rebuilt] });
  };

  // Live dangling-ref flags via the shared lint (same code as the harness).
  const dangling = React.useMemo(() => (doc ? danglingRefs(doc) : []), [doc]);

  const selected = graph.nodes.find((n) => n.id === selectedId) ?? null;

  return (
    <div>
      <header>
        <h1>Muse Composer</h1>
        <span className="meta">{docName ?? "no document loaded"}</span>
        {" — "}
        <a href="/">explorer</a>
      </header>
      <div className="loader">
        {["minimal", "full"].map((name) => (
          <button key={name} onClick={async () => {
            const res = await fetch(`/examples/${name}.muse.json`);
            if (res.ok) loadText(await res.text(), `${name} example`);
          }}>{name} example</button>
        ))}
        <input
          type="file"
          accept=".json,application/json"
          onChange={async (e) => {
            const f = e.target.files?.[0];
            if (f) loadText(await f.text(), f.name);
          }}
        />
      </div>
      <div className="composer-palette">
        {PALETTE.map(([kind, label]) => (
          <button key={kind} onClick={() => doc && addNode(kind)}>{label}</button>
        ))}
        {doc && (
          <button
            className="export"
            onClick={() => download(withExportProvenance(doc), exportFilename(docName))}
          >
            ⬇ export .muse.json
          </button>
        )}
      </div>
      {doc && (issues.length > 0 || dangling.length > 0) && (
        <div className="view composer-errors">
          <h2>Validation — {issues.length + dangling.length} issue(s)</h2>
          {issues.map((i, n) => (
            <div className="issue" key={n}><span className="channel">[{i.channel}]</span>{i.message}</div>
          ))}
          {dangling.map((d, n) => (
            <div className="issue" key={`d${n}`}><span className="channel">[refs]</span>{d.path}: {d.ref}</div>
          ))}
        </div>
      )}
      {doc && issues.length === 0 && dangling.length === 0 && (
        <div className="view"><p className="ok">clean — schema, cross-refs, and semantics all pass</p></div>
      )}
      <div className="composer-main">
        <div className="graph composer-canvas">
          <ReactFlow
            nodes={flowNodes(graph, selectedId)}
            edges={flowEdges(graph)}
            onNodeClick={(_, n) => setSelectedId(n.id)}
            onPaneClick={() => setSelectedId(null)}
            onConnect={onConnect}
            fitView
            proOptions={{ hideAttribution: true }}
          >
            <Background color="#2c313c" />
            <Controls showInteractive={false} />
          </ReactFlow>
        </div>
        <aside className="composer-inspector">
          <Inspector node={selected} graph={graph} onEdit={editField} onEditEdge={editEdge} onRemoveEdge={removeEdge} onReorder={reorder} />
        </aside>
      </div>
    </div>
  );
}

// Mount only in a browser with the entry element — importing this module in
// tests must not touch the DOM.
if (typeof document !== "undefined" && document.getElementById("root"))
  createRoot(document.getElementById("root")).render(<Composer />);
