// Tests for schema v0.3 mix topology (issue #87, per
// tests/open_20260822-143500_mix-topology-v03.md).
// Standalone runner: `node tests/mix-topology.test.mjs`; also folded into npm test.
import { readFile, readdir } from "node:fs/promises";
import Ajv from "ajv/dist/2020.js";
import addFormats from "ajv-formats";
import { danglingRefs } from "../tools/refs.mjs";

const dir = new URL("../schema/", import.meta.url);
const schemas = {};
const ajv = new Ajv({ allErrors: true, strict: false });
addFormats(ajv);
for (const f of (await readdir(dir)).filter((f) => f.endsWith(".schema.json"))) {
  schemas[f] = JSON.parse(await readFile(new URL(f, dir), "utf8"));
  ajv.addSchema(schemas[f]);
}
const validate = ajv.getSchema("https://muse.dev/schema/renditions.schema.json");

const full = JSON.parse(await readFile(new URL("../examples/full.muse.json", import.meta.url), "utf8"));
const spec = await readFile(new URL("../SCHEMA_SPEC.md", import.meta.url), "utf8");

let passed = 0, failed = 0;
const check = (name, cond) => {
  if (cond) { passed++; console.log(`ok   ${name}`); }
  else {
    failed++;
    console.error(`FAIL ${name}`);
    console.error(JSON.stringify(validate.errors, null, 2));
  }
};

const rendition = (mix) => [{ id: "r.x", name: "X", params: { mix } }];

// Acceptance: r.chamber's mix block validates explicitly.
check("r.chamber mix block validates", validate([full.renditions.find((r) => r.id === "r.chamber")]));
check("group + send buses, routes, rangeable send validate", validate(rendition({
  buses: [{ id: "bus.drums", kind: "group" }, { id: "bus.verb", kind: "send", effect: "plate reverb" }],
  routes: [{ part: "drums", bus: "bus.drums" }, { part: "vocals", bus: "bus.verb", send: [0.2, 0.5] }],
  sidechains: [{ source: "kick", target: "bass", amount: 0.4 }],
})));
check("scalar send and amount validate", validate(rendition({
  buses: [{ id: "bus.verb", kind: "send" }],
  routes: [{ part: "vocals", bus: "bus.verb", send: 0.35 }],
  sidechains: [{ source: "kick", target: "bass", amount: 0.4 }],
})));

// Rejection paths.
check("bus missing id rejected", !validate(rendition({ buses: [{ kind: "group" }] })));
check("bus missing kind rejected", !validate(rendition({ buses: [{ id: "bus.x" }] })));
check("bus kind outside group|send rejected", !validate(rendition({ buses: [{ id: "bus.x", kind: "aux" }] })));
check("route missing part rejected", !validate(rendition({ routes: [{ bus: "bus.x" }] })));
check("route missing bus rejected", !validate(rendition({ routes: [{ part: "drums" }] })));
check("send as 3-element array rejected", !validate(rendition({
  buses: [{ id: "bus.verb", kind: "send" }],
  routes: [{ part: "vocals", bus: "bus.verb", send: [0.1, 0.2, 0.3] }],
})));
check("send out of 0..1 rejected", !validate(rendition({
  buses: [{ id: "bus.verb", kind: "send" }],
  routes: [{ part: "vocals", bus: "bus.verb", send: 1.5 }],
})));
check("amount out of 0..1 rejected", !validate(rendition({
  sidechains: [{ source: "kick", target: "bass", amount: 2 }],
})));
check("unknown property on bus rejected (sealed)", !validate(rendition({ buses: [{ id: "b", kind: "group", vendor: "x" }] })));
check("unknown property on route rejected (sealed)", !validate(rendition({ routes: [{ part: "p", bus: "b", dry: 0.5 }] })));
check("unknown property on sidechain rejected (sealed)", !validate(rendition({ sidechains: [{ source: "a", target: "b", amount: 0.5, ratio: 4 }] })));
check("unknown property on mix rejected (sealed)", !validate(rendition({ buses: [], master: { gain: 1 } })));

// Cross-ref decision (implementer's call per the spec): routes[].bus IS a
// harness lint surface — a route to an undeclared bus is a dangling ref,
// same class as a ghost section id.
{
  const doc = JSON.parse(JSON.stringify(full));
  const chamber = doc.renditions.find((r) => r.id === "r.chamber");
  check("full example routes resolve against declared buses", danglingRefs(doc).length === 0);
  chamber.params.mix.routes.push({ part: "Cello", bus: "bus.ghost" });
  const dangles = danglingRefs(doc);
  check("route to undeclared bus dangles via the shared lint",
    dangles.some((d) => d.ref === "bus.ghost" && d.path.includes("mix.routes")));
}

// Spec ↔ schema parity: §2.6 mix-topology bullets name buses/routes/
// sidechains — the schema's mix.properties must match.
{
  const schemaKeys = Object.keys(schemas["renditions.schema.json"].items.properties.params.properties.mix.properties).sort();
  const bullets = [...spec.matchAll(/- \*\*`?(buses|routes|sidechains)`?\*\*/g)].map((m) => m[1]).sort();
  check("spec §2.6 mix-topology keys match schema mix.properties",
    JSON.stringify([...new Set(bullets)]) === JSON.stringify(schemaKeys));
}

console.log(`${passed} passed, ${failed} failed`);
process.exit(failed ? 1 : 0);
