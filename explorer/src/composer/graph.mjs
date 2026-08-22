// Composer graph model (docs/scope-composer.md, task 1): schema doc →
// node/edge graph → compiled doc. The graph is a projection of the schema —
// docToGraph extracts nodes/edges with provenance; compile reassembles the
// document by overlaying projected fields onto the original JSON, so every
// unprojected value (provenance, extensions, constraints detail, …)
// round-trips losslessly by construction. No DOM, no reactflow — pure data.
import { baseRef } from "@muse-tools/refs.mjs";

let seq = 0;
const nid = (kind, key) => `${kind}:${key ?? `new-${++seq}`}`;

// Schema doc → { nodes, edges }. Each node carries kind, a stable key, its
// projected fields, and _source — a reference to the original JSON object it
// was projected from. Edges carry the data needed to rebuild references on
// compile (transform suffixes for uses refs, etc.).
export function docToGraph(doc) {
  const nodes = [];
  const edges = [];
  const node = (kind, key, fields, source) => {
    nodes.push({ id: nid(kind, key), kind, key: key ?? null, fields, _source: source });
    return nodes[nodes.length - 1];
  };

  if (doc.globals) node("globals", null, {
    bpm: doc.globals.tempo?.bpm,
    tempo_range: doc.globals.tempo?.range,
    feel: doc.globals.tempo?.feel,
    meter: doc.globals.meter,
    key: doc.globals.key,
    duration_bars: doc.globals.duration_bars,
  }, doc.globals);
  if (doc.constraints) node("constraints", null, doc.constraints, doc.constraints);

  const m = doc.material ?? {};
  for (const motif of m.motifs ?? []) node("motif", motif.id, motif, motif);
  for (const theme of m.themes ?? []) {
    node("theme", theme.id, theme, theme);
    // Intra-material refs: phrase motif entries → target material nodes.
    for (const p of theme.phrases ?? [])
      for (const ref of p.motifs ?? [])
        edges.push({ from: nid("theme", theme.id), to: nid("motif", baseRef(ref)), type: "phrase-motif", data: { ref } });
  }
  for (const r of m.rhythms ?? []) node("rhythm", r.id, r, r);
  for (const p of m.harmony?.progressions ?? []) node("progression", p.id, p, p);

  for (const s of doc.form?.sections ?? []) {
    node("section", s.id, s, s);
    for (const u of s.uses ?? []) {
      const base = baseRef(u.ref);
      for (const kind of ["theme", "motif", "rhythm"])
        if (nodes.some((n) => n.id === nid(kind, base))) {
          edges.push({ from: nid("section", s.id), to: nid(kind, base), type: "uses", data: { ref: u.ref, variation: u.variation } });
          break;
        }
    }
    if (s.harmony) edges.push({ from: nid("section", s.id), to: nid("progression", s.harmony), type: "harmony", data: { ref: s.harmony } });
  }
  const order = doc.form?.order ?? [];
  order.slice(1).forEach((id, i) =>
    edges.push({ from: nid("section", order[i]), to: nid("section", id), type: "order", data: { index: i } }));

  for (const r of doc.renditions ?? []) node("rendition", r.id, r, r);
  return { nodes, edges };
}

// { nodes, edges } → schema doc. Overlay: each node's projected fields are
// shallow-copied over its _source object; the out doc reuses the input
// document's untouched sections verbatim. `originalDoc` supplies the base
// (metadata, extensions, unprojected values) — pass the document the graph
// was derived from; a bare skeleton is synthesized only when compiling a
// from-scratch graph.
export function compile(graph, originalDoc = {}) {
  const byKind = (kind) => graph.nodes.filter((n) => n.kind === kind);
  const projected = (n) => {
    const out = { ...(n._source ?? {}), ...n.fields };
    for (const k of Object.keys(out)) if (out[k] === undefined) delete out[k];
    return out;
  };

  const out = JSON.parse(JSON.stringify(originalDoc));

  const globals = byKind("globals")[0];
  if (globals) {
    const f = globals.fields;
    const g = { ...(globals._source ?? {}) };
    g.tempo = { ...(g.tempo ?? {}) };
    if (f.bpm !== undefined) g.tempo.bpm = f.bpm;
    if (f.tempo_range !== undefined) g.tempo.range = f.tempo_range;
    if (f.feel !== undefined) g.tempo.feel = f.feel;
    if (f.meter !== undefined) g.meter = f.meter;
    if (f.key !== undefined) g.key = f.key;
    if (f.duration_bars !== undefined) g.duration_bars = f.duration_bars;
    out.globals = g;
  }

  const constraints = byKind("constraints")[0];
  if (constraints) out.constraints = projected(constraints);

  const material = { ...(originalDoc.material ?? {}) };
  const motifs = byKind("motif").map(projected);
  const themes = byKind("theme").map(projected);
  const rhythms = byKind("rhythm").map(projected);
  const progressions = byKind("progression").map(projected);
  if (motifs.length) material.motifs = motifs;
  if (themes.length) material.themes = themes;
  if (rhythms.length) material.rhythms = rhythms;
  if (progressions.length) material.harmony = { ...(material.harmony ?? {}), progressions };
  if (Object.keys(material).length) out.material = material;

  // Sections: projected fields, with uses/harmony rebuilt from edges
  // (edge edits win over stale projected fields).
  const usesEdges = graph.edges.filter((e) => e.type === "uses");
  const harmonyEdges = graph.edges.filter((e) => e.type === "harmony");
  const sections = byKind("section").map((n) => {
    const s = projected(n);
    const uses = usesEdges
      .filter((e) => e.from === n.id)
      .map((e) => ({ ref: e.data.ref, ...(e.data.variation !== undefined ? { variation: e.data.variation } : {}) }));
    if (uses.length) s.uses = uses;
    const h = harmonyEdges.find((e) => e.from === n.id);
    if (h) s.harmony = h.data.ref;
    return s;
  });
  const orderEdges = [...graph.edges.filter((e) => e.type === "order")].sort((a, b) => a.data.index - b.data.index);
  if (sections.length || orderEdges.length) {
    const form = { ...(originalDoc.form ?? {}) };
    if (sections.length) form.sections = sections;
    if (orderEdges.length) {
      const keyOf = (nodeId) => nodeId.split(":").slice(1).join(":");
      form.order = [keyOf(orderEdges[0].from), ...orderEdges.map((e) => keyOf(e.to))];
    }
    out.form = form;
  }

  const renditions = byKind("rendition").map(projected);
  if (renditions.length) out.renditions = renditions;

  return out;
}
