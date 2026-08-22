// Edge/reference editing pins (issue #81, docs/scope-composer.md task 3):
// typed connections, ref helper decomposition, order rebuild, live
// dangling-ref flagging — all driven through graph.mjs compile, the same
// path the UI's operations take.
import { describe, it, expect } from "vitest";
import { readFile } from "node:fs/promises";
import { edgeTypeFor, splitRef, TRANSFORMS } from "./main.jsx";
import { docToGraph, compile } from "./graph.mjs";
import { validateDocument } from "../validate.js";
import { danglingRefs } from "@muse-tools/refs.mjs";

const full = JSON.parse(await readFile(new URL("../../../examples/full.muse.json", import.meta.url), "utf8"));

describe("edge type inference", () => {
  const graph = docToGraph(full);
  const id = (kind, key) => `${kind}:${key}`;
  it("section → material is uses", () => {
    expect(edgeTypeFor(graph, id("section", "verse.1"), id("motif", "motif.a"))).toBe("uses");
    expect(edgeTypeFor(graph, id("section", "verse.1"), id("theme", "theme.1"))).toBe("uses");
    expect(edgeTypeFor(graph, id("section", "verse.1"), id("rhythm", "groove.1"))).toBe("uses");
  });
  it("section → progression is harmony", () => {
    expect(edgeTypeFor(graph, id("section", "verse.1"), id("progression", "prog.verse"))).toBe("harmony");
  });
  it("section → section is order", () => {
    expect(edgeTypeFor(graph, id("section", "verse.1"), id("section", "chorus.1"))).toBe("order");
  });
  it("theme → motif is phrase-motif", () => {
    expect(edgeTypeFor(graph, id("theme", "theme.1"), id("motif", "motif.a"))).toBe("phrase-motif");
  });
  it("other pairs are rejected", () => {
    expect(edgeTypeFor(graph, id("motif", "motif.a"), id("section", "verse.1"))).toBeNull();
    expect(edgeTypeFor(graph, id("rendition", "r.synthwave"), id("motif", "motif.a"))).toBeNull();
    expect(edgeTypeFor(graph, id("section", "verse.1"), id("rendition", "r.synthwave"))).toBeNull();
  });
});

describe("ref helper", () => {
  it("splitRef decomposes base and suffix chain", () => {
    expect(splitRef("motif.a")).toEqual({ base: "motif.a", suffix: "" });
    expect(splitRef("motif.a#seq(+2)")).toEqual({ base: "motif.a", suffix: "#seq(+2)" });
    expect(splitRef("motif.a#inv#seq(+2)")).toEqual({ base: "motif.a", suffix: "#inv#seq(+2)" });
  });
  it("transform vocabulary matches the §2.3 grammar families", () => {
    expect(TRANSFORMS).toEqual(["seq(+n)", "seq(-n)", "inv", "retro", "aug(n)", "dim(n)"]);
  });
});

describe("edge operations through compile", () => {
  it("adding a uses edge compiles to uses[].ref and validates", () => {
    const graph = docToGraph(full);
    const edited = {
      nodes: graph.nodes,
      edges: [...graph.edges, { from: "section:chorus.1", to: "rhythm:groove.1", type: "uses", data: { ref: "groove.1" } }],
    };
    const out = compile(edited, full);
    const chorus = out.form.sections.find((s) => s.id === "chorus.1");
    expect(chorus.uses.some((u) => u.ref === "groove.1")).toBe(true);
    expect(validateDocument(out)).toEqual([]);
  });

  it("editing a uses ref to a dangling id is flagged live by the shared lint", () => {
    const graph = docToGraph(full);
    const edited = {
      nodes: graph.nodes,
      edges: graph.edges.map((e) =>
        e.type === "uses" && e.from === "section:verse.1" ? { ...e, data: { ...e.data, ref: "motif.ghost" } } : e),
    };
    const out = compile(edited, full);
    expect(danglingRefs(out).some((d) => d.ref === "motif.ghost")).toBe(true);
  });

  it("transform-suffixed ref edit stays valid (transform grammar enforced)", () => {
    const graph = docToGraph(full);
    const edited = {
      nodes: graph.nodes,
      edges: graph.edges.map((e) =>
        e.type === "uses" && e.from === "section:verse.1" ? { ...e, data: { ...e.data, ref: "theme.1#aug(2)" } } : e),
    };
    const out = compile(edited, full);
    expect(validateDocument(out)).toEqual([]);
    expect(danglingRefs(out)).toEqual([]);
  });

  it("removing a harmony edge drops section.harmony", () => {
    const graph = docToGraph(full);
    const edited = {
      nodes: graph.nodes,
      edges: graph.edges.filter((e) => !(e.type === "harmony" && e.from === "section:verse.1")),
    };
    const out = compile(edited, full);
    expect(out.form.sections.find((s) => s.id === "verse.1").harmony).toBeUndefined();
  });

  it("reorder rebuilds form.order through the order edge chain", () => {
    const graph = docToGraph(full);
    const orderEdges = [...graph.edges.filter((e) => e.type === "order")].sort((a, b) => a.data.index - b.data.index);
    const seq = [orderEdges[0].from, ...orderEdges.map((e) => e.to)];
    // swap first two
    [seq[0], seq[1]] = [seq[1], seq[0]];
    const others = graph.edges.filter((e) => e.type !== "order");
    const rebuilt = seq.slice(1).map((to, k) => ({ from: seq[k], to, type: "order", data: { index: k } }));
    const out = compile({ nodes: graph.nodes, edges: [...others, ...rebuilt] }, full);
    expect(out.form.order[0]).toBe("chorus.1");
    expect(out.form.order[1]).toBe("verse.1");
    expect(validateDocument(out)).toEqual([]);
  });

  it("duplicate uses edges stay allowed (schema permits duplicate uses entries)", () => {
    const graph = docToGraph(full);
    const edited = {
      nodes: graph.nodes,
      edges: [
        ...graph.edges,
        { from: "section:chorus.1", to: "theme:theme.1", type: "uses", data: { ref: "theme.1" } },
        { from: "section:chorus.1", to: "theme:theme.1", type: "uses", data: { ref: "theme.1" } },
      ],
    };
    const out = compile(edited, full);
    // Pin the dedup decision: duplicates mirror the schema (uses[] is an
    // array; repeated material in a section is legal). If a UX-level dedup
    // is ever wanted, it lands deliberately, not silently.
    expect(validateDocument(out)).toEqual([]);
  });
});
