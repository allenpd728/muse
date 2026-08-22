// Composer shell (issue #80, docs/scope-composer.md task 2): route + node
// palette + reactflow canvas + property inspector for scalar fields.
// The graph is a projection of the schema (task 1's graph.mjs); every edit
// recompiles and revalidates in memory — invalid states surface in the
// inspector, never silently dropped. No audio; export is MVP 5.
import React from "react";
import { createRoot } from "react-dom/client";
import ReactFlow, { Background, Controls } from "reactflow";
import "reactflow/dist/style.css";
import { docToGraph, compile } from "./graph.mjs";
import { validateDocument } from "../validate.js";
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

function Inspector({ node, onEdit }) {
  if (!node) return <p className="muted">select a node to edit its fields</p>;
  const fields = INSPECTOR_FIELDS[node.kind] ?? [];
  return (
    <div>
      <h3>{KIND_LABEL[node.kind] ?? node.kind} <span className="muted">{node.key ?? ""}</span></h3>
      {fields.length === 0 && <p className="muted">no scalar fields on this node yet</p>}
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

  const addNode = (kind) => {
    if ((kind === "globals" || kind === "constraints") && graph.nodes.some((n) => n.kind === kind)) return;
    const key = freshKey(kind);
    const fields = kind === "section" ? { id: key, role: "custom" } : { id: key };
    applyGraph({
      nodes: [...graph.nodes, { id: `${kind}:${key}`, kind, key, fields, _source: null }],
      edges: graph.edges,
    });
  };

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
      </div>
      {doc && issues.length > 0 && (
        <div className="view">
          {issues.map((i, n) => (
            <div className="issue" key={n}><span className="channel">[{i.channel}]</span>{i.message}</div>
          ))}
        </div>
      )}
      <div className="composer-main">
        <div className="graph composer-canvas">
          <ReactFlow
            nodes={flowNodes(graph, selectedId)}
            edges={flowEdges(graph)}
            onNodeClick={(_, n) => setSelectedId(n.id)}
            onPaneClick={() => setSelectedId(null)}
            fitView
            proOptions={{ hideAttribution: true }}
          >
            <Background color="#2c313c" />
            <Controls showInteractive={false} />
          </ReactFlow>
        </div>
        <aside className="composer-inspector">
          <Inspector node={selected} onEdit={editField} />
        </aside>
      </div>
    </div>
  );
}

// Mount only in a browser with the entry element — importing this module in
// tests must not touch the DOM.
if (typeof document !== "undefined" && document.getElementById("root"))
  createRoot(document.getElementById("root")).render(<Composer />);
