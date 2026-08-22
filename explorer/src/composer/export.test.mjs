// Validation + export pins (issue #83, docs/scope-composer.md task 5):
// export provenance shape + the inline error surfacing contract.
import { describe, it, expect } from "vitest";
import { readFile } from "node:fs/promises";
import { withExportProvenance } from "./main.jsx";
import { validateDocument } from "../validate.js";

const full = JSON.parse(await readFile(new URL("../../../examples/full.muse.json", import.meta.url), "utf8"));
const minimal = JSON.parse(await readFile(new URL("../../../examples/minimal.muse.json", import.meta.url), "utf8"));

describe("export provenance", () => {
  it("appends the scope-doc entry: edit / composer-tool / ai: false", () => {
    const out = withExportProvenance(full, { at: "2026-08-22T15:00:00Z" });
    const entry = out.metadata.provenance.at(-1);
    expect(entry).toEqual({ event: "edit", actor: "composer-tool", at: "2026-08-22T15:00:00Z", ai: false });
    expect(out.metadata.provenance.length).toBe(full.metadata.provenance.length + 1);
  });

  it("exported doc still validates (provenance entry is schema-legal)", () => {
    expect(validateDocument(withExportProvenance(full))).toEqual([]);
    expect(validateDocument(withExportProvenance(minimal))).toEqual([]);
  });

  it("does not mutate the source document", () => {
    const before = JSON.stringify(full);
    withExportProvenance(full);
    expect(JSON.stringify(full)).toBe(before);
  });

  it("double export appends two entries (each save is its own event)", () => {
    const once = withExportProvenance(full, { at: "2026-08-22T15:00:00Z" });
    const twice = withExportProvenance(once, { at: "2026-08-22T15:01:00Z" });
    expect(twice.metadata.provenance.length).toBe(full.metadata.provenance.length + 2);
  });
});

describe("inline error surfacing contract", () => {
  it("a doc broken by an edit surfaces issues through the shared validator", () => {
    const broken = withExportProvenance({ ...full, muse_version: "0.1" }); // non-semver
    const issues = validateDocument(broken);
    expect(issues.length).toBeGreaterThan(0);
    expect(issues.some((i) => i.channel === "schema")).toBe(true);
  });
});
