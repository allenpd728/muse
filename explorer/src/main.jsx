import React from "react";
import { createRoot } from "react-dom/client";
import ReactFlow, { Background, Controls } from "reactflow";
import "reactflow/dist/style.css";
import { validateDocument } from "./validate.js";
import ListenTab from "./listen/ListenTab.jsx";
import "./styles.css";

const EXAMPLES = ["minimal", "full"];

// --- View 1: validation panel ---
function ValidationPanel({ doc }) {
  const issues = React.useMemo(() => (doc ? validateDocument(doc) : []), [doc]);
  if (!doc) return null;
  return (
    <section>
      <h2>Validation</h2>
      {issues.length === 0
        ? <p className="ok">clean — schema, cross-refs, and semantics all pass</p>
        : issues.map((i, n) => (
            <div className="issue" key={n}>
              <span className="channel">[{i.channel}]</span>{i.message}
            </div>
          ))}
    </section>
  );
}

// --- View 2: document tree ---
function TreeNode({ name, value }) {
  if (value === null || typeof value !== "object") {
    return (
      <div>
        <span className="key">{name}</span>: <span className="val">{JSON.stringify(value)}</span>
      </div>
    );
  }
  const entries = Array.isArray(value) ? value.map((v, i) => [i, v]) : Object.entries(value);
  return (
    <details open={name === "(root)"}>
      <summary>
        <span className="key">{name}</span> <span className="muted">{Array.isArray(value) ? `[${value.length}]` : `{${entries.length}}`}</span>
      </summary>
      {entries.map(([k, v]) => <TreeNode key={k} name={k} value={v} />)}
    </details>
  );
}

// --- View 3: form graph ---
function FormGraph({ doc }) {
  const sections = doc?.form?.sections ?? [];
  if (!sections.length) return <p className="muted">no form sections</p>;
  const order = doc?.form?.order ?? sections.map((s) => s.id);
  const byId = Object.fromEntries(sections.map((s) => [s.id, s]));
  const rep = doc?.form?.repetition ?? {};
  const nodes = order.map((id, i) => {
    const s = byId[id];
    const label = s
      ? `${id}\n${s.role ?? "custom"} · ${s.bars ?? "?"} bars${rep[id] ? ` · ×${rep[id].min}–${rep[id].max}` : ""}`
      : `${id}\n(ghost — not defined)`;
    return {
      id: `${id}#${i}`,
      position: { x: i * 240, y: 80 },
      data: { label },
      style: {
        background: s ? "#1c1f26" : "#3a1e28",
        color: "#d7dce4",
        border: `1px solid ${s ? "#7aa2f7" : "#f7768e"}`,
        borderRadius: 6,
        whiteSpace: "pre-line",
        fontSize: 12,
        width: 200,
      },
    };
  });
  const edges = order.slice(1).map((id, i) => ({
    id: `e${i}`,
    source: `${order[i]}#${i}`,
    target: `${id}#${i + 1}`,
    animated: true,
    style: { stroke: "#7aa2f7" },
  }));
  return (
    <div className="graph">
      <ReactFlow nodes={nodes} edges={edges} fitView proOptions={{ hideAttribution: true }} nodesDraggable={false} nodesConnectable={false}>
        <Background color="#2c313c" />
        <Controls showInteractive={false} />
      </ReactFlow>
    </div>
  );
}

// --- View 4: material browser ---
function MaterialBrowser({ doc }) {
  const m = doc?.material;
  if (!m) return <p className="muted">no material</p>;
  const card = (title, fields) => (
    <div className="card" key={title}>
      <h3>{title}</h3>
      <dl>{fields.filter(([, v]) => v !== undefined).map(([k, v]) => (
        <React.Fragment key={k}><dt>{k}</dt><dd>{v}</dd></React.Fragment>
      ))}</dl>
    </div>
  );
  return (
    <div>
      <h2>Motifs</h2>
      <div className="cards">
        {(m.motifs ?? []).map((x) => card(x.id, [
          ["kind", x.kind],
          ["pitches", x.pitches?.join(" ")],
          ["durations", x.durations?.join(" ")],
          ["contour", x.contour],
          ["tags", x.tags?.join(", ")],
        ]))}
      </div>
      <h2>Themes</h2>
      <div className="cards">
        {(m.themes ?? []).map((x) => card(x.id, [
          ["phrases", x.phrases?.map((p) => (p.motifs ?? []).join(", ")).join(" | ")],
          ["cadence", x.cadence],
        ]))}
      </div>
      <h2>Rhythms</h2>
      <div className="cards">
        {(m.rhythms ?? []).map((x) => card(x.id, [
          ["pattern", x.pattern?.join(" ")],
          ["grid", x.grid],
        ]))}
      </div>
      <h2>Harmony</h2>
      <div className="cards">
        {(m.harmony?.progressions ?? []).map((x) => card(x.id, [
          ["chords", x.chords?.join(" → ")],
          ["bars/chord", x.bars_per_chord],
        ]))}
        {m.harmony?.vocabulary && card("vocabulary", [["value", m.harmony.vocabulary]])}
      </div>
    </div>
  );
}

// --- View 5: rendition cards ---
function RenditionCards({ doc }) {
  const rs = doc?.renditions ?? [];
  if (!rs.length) return <p className="muted">no renditions</p>;
  return (
    <div className="cards">
      {rs.map((r) => (
        <div className="card" key={r.id}>
          <h3>{r.name ?? r.id}</h3>
          <dl>
            {r.style?.genre && <><dt>genre</dt><dd>{r.style.genre}{r.style.era ? ` (${r.style.era})` : ""}</dd></>}
            {r.style?.references && <><dt>references</dt><dd>{r.style.references.join(", ")}</dd></>}
            {r.params?.tempo_bpm !== undefined && <><dt>tempo</dt><dd>{r.params.tempo_bpm} bpm</dd></>}
            {r.params?.instrumentation && <><dt>instruments</dt><dd>{r.params.instrumentation.map((i) => (typeof i === "string" ? i : i.name)).join(", ")}</dd></>}
            {r.params?.density !== undefined && <><dt>density</dt><dd>{r.params.density}</dd></>}
            {r.params?.swing !== undefined && <><dt>swing</dt><dd>{r.params.swing}</dd></>}
            {r.author?.name && <><dt>author</dt><dd>{r.author.name}</dd></>}
          </dl>
        </div>
      ))}
    </div>
  );
}

// --- App shell ---
function App() {
  const [doc, setDoc] = React.useState(null);
  const [docName, setDocName] = React.useState(null);
  const [loadError, setLoadError] = React.useState(null);
  const [tab, setTab] = React.useState("validation");
  const urlRef = React.useRef();

  const loadText = (text, name) => {
    try {
      setDoc(JSON.parse(text));
      setDocName(name);
      setLoadError(null);
    } catch (e) {
      setDoc(null);
      setLoadError(`${name}: ${e.message}`);
    }
  };

  const loadUrl = async (url) => {
    try {
      const res = await fetch(url);
      if (!res.ok) throw new Error(`HTTP ${res.status}`);
      loadText(await res.text(), url);
    } catch (e) {
      setLoadError(`${url}: ${e.message}`);
    }
  };

  const tabs = [
    ["validation", "Validation"],
    ["tree", "Document tree"],
    ["form", "Form graph"],
    ["material", "Material"],
    ["renditions", "Renditions"],
    ["listen", "Listen"],
  ];

  return (
    <div>
      <header>
        <h1>Muse Explorer</h1>
        <span className="meta">{docName ?? "no document loaded"}</span>
        {doc?.metadata?.title && <span className="meta">— {doc.metadata.title}</span>}
      </header>
      <div className="loader">
        {EXAMPLES.map((name) => (
          <button key={name} onClick={() => loadUrl(`/examples/${name}.muse.json`)}>{name} example</button>
        ))}
        <input
          type="file"
          accept=".json,application/json"
          onChange={async (e) => {
            const f = e.target.files?.[0];
            if (f) loadText(await f.text(), f.name);
          }}
        />
        <input type="text" ref={urlRef} placeholder="https://…/file.muse.json" />
        <button onClick={() => urlRef.current?.value && loadUrl(urlRef.current.value)}>load URL</button>
      </div>
      {loadError && <div className="view"><p className="error">load error — {loadError}</p></div>}
      {doc && (
        <>
          <div className="tabs">
            {tabs.map(([id, label]) => (
              <button key={id} className={tab === id ? "active" : ""} onClick={() => setTab(id)}>{label}</button>
            ))}
          </div>
          <div className="view">
            {tab === "validation" && <ValidationPanel doc={doc} />}
            {tab === "tree" && <div className="tree"><TreeNode name="(root)" value={doc} /></div>}
            {tab === "form" && <FormGraph doc={doc} />}
            {tab === "material" && <MaterialBrowser doc={doc} />}
            {tab === "renditions" && <RenditionCards doc={doc} />}
            {tab === "listen" && <ListenTab doc={doc} />}
          </div>
        </>
      )}
    </div>
  );
}

createRoot(document.getElementById("root")).render(<App />);
