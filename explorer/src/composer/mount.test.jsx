// DOM mount safety (issue #116): the composer shell mounts headlessly —
// nodes render without throwing, and an inspector edit recompiles through
// graph.mjs. jsdom, no real browser.
import { describe, it, expect, beforeAll } from "vitest";
import { readFile } from "node:fs/promises";

let Composer, React, createRoot, full;

beforeAll(async () => {
  const { JSDOM } = await import("jsdom");
  const dom = new JSDOM("<!doctype html><html><body><div id=\"root\"></div></body></html>", { url: "http://localhost/" });
  globalThis.document = dom.window.document;
  globalThis.window = dom.window;
  // navigator is a getter on jsdom's window — copy via defineProperty.
  Object.defineProperty(globalThis, "navigator", { value: dom.window.navigator, configurable: true });
  // jsdom has no ResizeObserver (reactflow requires it) — minimal stub.
  globalThis.ResizeObserver ??= class {
    observe() {}
    unobserve() {}
    disconnect() {}
  };
  // reactflow touches SVG globals jsdom doesn't define.
  for (const name of ["SVGElement", "SVGGraphicsElement", "DOMMatrixReadOnly"])
    globalThis[name] ??= dom.window[name] ?? class {};
  React = (await import("react")).default;
  createRoot = (await import("react-dom/client")).createRoot;
  full = JSON.parse(await readFile(new URL("../../../examples/full.muse.json", import.meta.url), "utf8"));
});

describe("composer shell DOM mount (issue #116)", () => {
  it("main.jsx mounts into #root without throwing on import safety guard", async () => {
    // The mount is guarded: with #root present in jsdom it should render.
    await expect(import("./main.jsx")).resolves.toBeTruthy();
    // React 18 renders async — flush the queue before asserting.
    await new Promise((r) => setTimeout(r, 50));
    expect(document.getElementById("root").innerHTML.length).toBeGreaterThan(0);
  });

  it("graph round-trip on a minimal doc does not throw at the data layer", async () => {
    const { docToGraph, compile } = await import("./graph.mjs");
    const minimal = JSON.parse(await readFile(new URL("../../../examples/minimal.muse.json", import.meta.url), "utf8"));
    const graph = docToGraph(minimal);
    expect(graph.nodes.length).toBeGreaterThan(0);
    expect(() => compile(graph, minimal)).not.toThrow();
    expect(compile(graph, minimal)).toEqual(minimal);
  });

  it("inspector scalar edit recompiles through graph.mjs", async () => {
    const { docToGraph, compile } = await import("./graph.mjs");
    const graph = docToGraph(full);
    const section = graph.nodes.find((n) => n.kind === "section");
    const edited = {
      nodes: graph.nodes.map((n) => (n.id === section.id ? { ...n, fields: { ...n.fields, energy: 0.77 } } : n)),
      edges: graph.edges,
    };
    const out = compile(edited, full);
    expect(out.form.sections.find((s) => s.id === section.key).energy).toBe(0.77);
  });
});
