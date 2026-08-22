// Composer shell pins (issue #80): the shell's constants and the
// edit → compile → validate loop it wires together.
import { describe, it, expect } from "vitest";
import { readFile } from "node:fs/promises";
import { execFileSync } from "node:child_process";
import { SECTION_ROLES, PALETTE, addPaletteNode } from "./main.jsx";
import { docToGraph, compile } from "./graph.mjs";
import { validateDocument } from "../validate.js";

const formSchema = JSON.parse(await readFile(new URL("../../../schema/form.schema.json", import.meta.url), "utf8"));
const full = JSON.parse(await readFile(new URL("../../../examples/full.muse.json", import.meta.url), "utf8"));

describe("composer shell", () => {
  it("SECTION_ROLES matches the v0.2 schema enum exactly", () => {
    expect([...SECTION_ROLES].sort()).toEqual(
      [...formSchema.properties.sections.items.properties.role.enum].sort()
    );
  });

  it("palette covers the eight schema construct types", () => {
    expect(PALETTE.map(([k]) => k).sort()).toEqual(
      ["constraints", "globals", "motif", "progression", "rendition", "rhythm", "section", "theme"].sort()
    );
  });

  it("scalar edit → compile → validate loop: section energy edit keeps doc valid", () => {
    const graph = docToGraph(full);
    const section = graph.nodes.find((n) => n.kind === "section");
    const edited = {
      nodes: graph.nodes.map((n) => (n.id === section.id ? { ...n, fields: { ...n.fields, energy: 0.95 } } : n)),
      edges: graph.edges,
    };
    const out = compile(edited, full);
    const target = out.form.sections.find((s) => s.id === section.key);
    expect(target.energy).toBe(0.95);
    expect(validateDocument(out)).toEqual([]);
  });

  it("scalar edit → compile: globals bpm edit propagates", () => {
    const graph = docToGraph(full);
    const globals = graph.nodes.find((n) => n.kind === "globals");
    const edited = {
      nodes: graph.nodes.map((n) => (n.id === globals.id ? { ...n, fields: { ...n.fields, bpm: 120 } } : n)),
      edges: graph.edges,
    };
    expect(compile(edited, full).globals.tempo.bpm).toBe(120);
  });

  it("invalid scalar (energy > 1) surfaces through validateDocument, not silently", () => {
    const graph = docToGraph(full);
    const section = graph.nodes.find((n) => n.kind === "section");
    const edited = {
      nodes: graph.nodes.map((n) => (n.id === section.id ? { ...n, fields: { ...n.fields, energy: 2 } } : n)),
      edges: graph.edges,
    };
    const issues = validateDocument(compile(edited, full));
    expect(issues.length).toBeGreaterThan(0);
  });
});

describe("palette add-node (issue #93)", () => {
  const graph = docToGraph(full);

  it("new node appears with a fresh key", () => {
    const next = addPaletteNode(graph, "motif");
    const added = next.nodes.at(-1);
    expect(next.nodes.length).toBe(graph.nodes.length + 1);
    expect(added.kind).toBe("motif");
    expect(added.key).toMatch(/^motif\.new_\d+$/);
    expect(added.fields.id).toBe(added.key);
  });

  it("globals/constraints singleton guard blocks a second add", () => {
    expect(addPaletteNode(graph, "globals")).toBe(graph);
    expect(addPaletteNode(graph, "constraints")).toBe(graph);
  });

  it("section nodes default role custom (schema-valid)", () => {
    const empty = { nodes: [], edges: [] };
    const withSection = addPaletteNode(empty, "section");
    expect(withSection.nodes[0].fields.role).toBe("custom");
    expect(SECTION_ROLES).toContain("custom");
  });

  it("added section node compiles into a schema-valid doc", () => {
    const minimal = JSON.parse(JSON.stringify(full));
    const g = docToGraph(minimal);
    const next = addPaletteNode(g, "section");
    const out = compile(next, minimal);
    expect(validateDocument(out)).toEqual([]);
  });
});

describe("build regression pin (issue #93)", () => {
  it("vite build emits both index.html and composer.html", () => {
    const out = execFileSync("npx", ["vite", "build"], { cwd: new URL("../..", import.meta.url).pathname, encoding: "utf8" });
    expect(out).toContain("index.html");
    expect(out).toContain("composer.html");
  }, 30000);
});
