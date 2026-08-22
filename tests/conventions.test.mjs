// Convention lint (issue #48, per tests/open_20260822-102227_integration-review.md).
// Codifies the cross-schema conventions the #37 review verified by hand, in the
// resolved form of corrective tasks #43–#47.
// Standalone runner: `node tests/conventions.test.mjs`; also folded into npm test.
import { readFile, readdir } from "node:fs/promises";
import Ajv from "ajv/dist/2020.js";
import addFormats from "ajv-formats";
import { danglingRefs } from "../tools/test.mjs";

const dir = new URL("../schema/", import.meta.url);
const files = (await readdir(dir)).filter((f) => f.endsWith(".schema.json")).sort();
const schemas = {};
for (const f of files) schemas[f] = JSON.parse(await readFile(new URL(f, dir), "utf8"));

const ajv = new Ajv({ allErrors: true, strict: false });
addFormats(ajv);
for (const f of files) if (schemas[f].$id) ajv.addSchema(schemas[f]);
const validateRoot = ajv.compile(schemas["muse.schema.json"]);
const validateMaterial = ajv.getSchema(schemas["material.schema.json"].$id);
const validateConstraints = ajv.getSchema(schemas["constraints.schema.json"].$id);
const validateForm = ajv.getSchema(schemas["form.schema.json"].$id);
const validateMetadata = ajv.getSchema(schemas["metadata.schema.json"].$id);

let passed = 0, failed = 0;
const check = (name, cond) => {
  if (cond) { passed++; console.log(`ok   ${name}`); }
  else { failed++; console.error(`FAIL ${name}`); }
};

const walk = (node, path, fn) => {
  if (Array.isArray(node)) return node.forEach((v, i) => walk(v, `${path}/${i}`, fn));
  if (!node || typeof node !== "object") return;
  fn(node, path);
  for (const [k, v] of Object.entries(node)) walk(v, `${path}/${k}`, fn);
};

// 1. Naming: every property name in every schema is snake_case. No exceptions
// today — a new one must be a conscious choice (edit this test).
const SNAKE = /^[a-z][a-z0-9_]*$/;
const badNames = [];
for (const f of files)
  walk(schemas[f], "#", (node, path) => {
    if (node.properties)
      for (const name of Object.keys(node.properties))
        if (!SNAKE.test(name)) badNames.push(`${f}${path}: ${name}`);
  });
check("all property names in all schemas are snake_case", badNames.length === 0);
if (badNames.length) console.error(badNames.join("\n"));

// 2. Sealed objects: every fixed-shape object is sealed except the documented
// open set. Both directions asserted — a new unsealed object OR a silently
// sealed exception fails the suite.
const OPEN = new Map([
  ["form.schema.json#/properties/repetition", "map-valued: section ids → repeat bounds"],
  ["constraints.schema.json#/properties/tempo_lock", "map-valued: section ids → bpm ranges"],
  ["constraints.schema.json#/properties/register", "map-valued: material ids → pitch bounds"],
  ["constraints.schema.json#/$defs/predicate", "extensible must_not predicates (unknown kinds preserved)"],
]);
const unsealed = [], sealedException = [];
for (const f of files)
  walk(schemas[f], "#", (node, path) => {
    // Fixed-shape document objects only: typed object + properties. Applicator
    // branches (if/then/anyOf conditions) carry properties without type and
    // are not shapes to seal.
    if (node.type !== "object" || !node.properties) return;
    const at = `${f}${path}`;
    if (node.additionalProperties === false) {
      if (OPEN.has(at)) sealedException.push(at);
    } else if (!OPEN.has(at)) unsealed.push(at);
  });
check("every fixed-shape object is sealed (additionalProperties: false)", unsealed.length === 0);
if (unsealed.length) console.error(unsealed.join("\n"));
check("documented open objects stay open", sealedException.length === 0);
if (sealedException.length) console.error(sealedException.join("\n"));
check("extensions root stays fully open (additionalProperties: true)",
  schemas["extensions.schema.json"].additionalProperties === true);
check("metadata.provenance items sealed (#45 regression guard)",
  schemas["metadata.schema.json"].properties.provenance.items.additionalProperties === false);

// 3. Id grammar (#43): spec §2.1 example form validates; bare/prefixed ULID
// and UUID all accepted; wrong-namespace prefix rejected.
const metaDoc = (id) => ({
  id, title: "t", composer: { name: "c" }, created: "2026-08-22T00:00:00Z",
  license: { renditions: "presets-only" }, provenance: [],
});
check("metadata.id accepts spec §2.1 prefixed ULID form", validateMetadata(metaDoc("muse:work:01J9QR4T8V0W2X6Y8Z0A2C4E6G")));
check("metadata.id accepts bare ULID", validateMetadata(metaDoc("01J9QR4T8V0W2X6Y8Z0A2C4E6G")));
check("metadata.id accepts bare and prefixed UUID",
  validateMetadata(metaDoc("550e8400-e29b-41d4-a716-446655440000")) &&
  validateMetadata(metaDoc("muse:work:550e8400-e29b-41d4-a716-446655440000")));
check("metadata.id rejects wrong-namespace prefix and malformed ULID",
  !validateMetadata(metaDoc("muse:track:01J9QR4T8V0W2X6Y8Z0A2C4E6G")) &&
  !validateMetadata(metaDoc("muse:work:01J9QR4T8V0W2X6Y8Z0A2C4E6")));

// 4. Pitch grammar (#44): one shared $defs entry, referenced from both
// schemas; behavior rejects non-pitches, accepts the spec's pitches.
check("pitch defined once in material $defs",
  schemas["material.schema.json"].$defs?.pitch?.pattern === "^[A-G](?:#|b)?-?\\d+$");
check("motif pitches reference the shared pitch def",
  schemas["material.schema.json"].properties.motifs.items.properties.pitches.items.$ref === "#/$defs/pitch");
check("register bounds reference the shared pitch def cross-file",
  schemas["constraints.schema.json"].properties.register.additionalProperties.prefixItems
    .every((b) => b.$ref === "material.schema.json#/$defs/pitch"));
check("pitch grammar rejects banana / 42 / empty in motifs",
  !validateMaterial({ motifs: [{ id: "m", kind: "pitch", pitches: ["banana"] }] }) &&
  !validateMaterial({ motifs: [{ id: "m", kind: "pitch", pitches: ["42"] }] }) &&
  !validateMaterial({ motifs: [{ id: "m", kind: "pitch", pitches: [""] }] }));
check("pitch grammar rejects banana / 42 / empty in register bounds",
  !validateConstraints({ register: { "theme.1": ["C4", "banana"] } }) &&
  !validateConstraints({ register: { "theme.1": ["42", "A5"] } }) &&
  !validateConstraints({ register: { "theme.1": ["", "A5"] } }));
check("pitch grammar accepts spec pitches in both positions",
  validateMaterial({ motifs: [{ id: "m", kind: "pitch", pitches: ["D4", "F4", "A4", "G4"] }] }) &&
  validateConstraints({ register: { "theme.1": ["C4", "A5"] } }));

// 5. Transform refs (#46): one shared materialRef def; identical behavior at
// both reference sites.
check("uses[].ref references the shared materialRef def cross-file",
  schemas["form.schema.json"].properties.sections.items.properties.uses.items.properties.ref.$ref ===
  "material.schema.json#/$defs/materialRef");
check("phrase motifs reference the shared materialRef def",
  schemas["material.schema.json"].properties.themes.items.properties.phrases.items.properties.motifs.items.$ref ===
  "#/$defs/materialRef");
const GOOD_REFS = ["motif.a", "motif.a#seq(+2)", "motif.a#seq(-1)", "motif.a#inv", "motif.a#retro", "motif.a#aug(2)", "motif.a#dim(0.5)", "motif.a#inv#seq(+2)"];
const BAD_REFS = ["theme.1###", "theme.1###garbage", "motif.a#unknown", "#inv", "motif.a#", "motif.a#seq(+)", "motif.a#aug()"];
const phraseDoc = (refs) => ({ themes: [{ id: "theme.1", phrases: [{ motifs: refs }] }] });
const usesDoc = (refs) => ({ sections: [{ id: "s1", role: "verse", uses: refs.map((ref) => ({ ref })) }], order: ["s1"] });
check("both ref sites accept the full transform vocabulary",
  GOOD_REFS.every((r) => validateMaterial(phraseDoc([r])) && validateForm(usesDoc([r]))));
check("both ref sites reject malformed transform refs",
  BAD_REFS.every((r) => !validateMaterial(phraseDoc([r])) && !validateForm(usesDoc([r]))));

// 6. Cross-ref coverage (#47): a ghost id on every reference surface dangles.
const full = JSON.parse(await readFile(new URL("../examples/full.muse.json", import.meta.url), "utf8"));
const clone = () => JSON.parse(JSON.stringify(full));
const dangles = (doc) => danglingRefs(doc).map((d) => d.ref);
check("full example has no dangling refs", dangles(clone()).length === 0);
check("ghost in theme phrase motifs dangles", dangles((() => { const d = clone(); d.material.themes[0].phrases[0].motifs.push("motif.ghost"); return d; })()).includes("motif.ghost"));
check("ghost in form.order dangles", dangles((() => { const d = clone(); d.form.order.push("section.ghost"); return d; })()).includes("section.ghost"));
check("ghost in form.repetition key dangles", dangles((() => { const d = clone(); d.form.repetition["section.ghost"] = { min: 1, max: 2 }; return d; })()).includes("section.ghost"));
check("ghost in constraints.tempo_lock key dangles", dangles((() => { const d = clone(); d.constraints.tempo_lock["section.ghost"] = [90, 100]; return d; })()).includes("section.ghost"));
check("ghost in constraints.register key dangles", dangles((() => { const d = clone(); d.constraints.register["theme.ghost"] = ["C4", "A5"]; return d; })()).includes("theme.ghost"));

// 7. Seam exercise: the full example keeps the review's cross-seam thread —
// a transform-suffixed motif inside a theme used by a tempo_locked section.
check("full example keeps the transform → theme → section → tempo_lock seam", (() => {
  const lockedSections = new Set(Object.keys(full.constraints?.tempo_lock ?? {}));
  const themesById = new Map((full.material.themes ?? []).map((t) => [t.id, t]));
  return (full.form.sections ?? []).some((s) =>
    lockedSections.has(s.id) && (s.uses ?? []).some((u) => {
      const theme = themesById.get(u.ref?.split("#")[0]);
      return theme?.phrases?.some((p) => (p.motifs ?? []).some((m) => m.includes("#")));
    }));
})());

console.log(`${passed} passed, ${failed} failed`);
process.exit(failed ? 1 : 0);
