// Shared transform-ref grammar parity (issue #46, residual coverage issue #54):
// one case list drives both `material.themes[].phrases[].motifs[]` and
// `form.sections[].uses[].ref` — the two positions share materialRef, so they
// can never drift apart. Standalone runner + npm test pickup.
import { readFile } from "node:fs/promises";
import Ajv from "ajv/dist/2020.js";

const ajv = new Ajv({ allErrors: true, strict: false });
const material = JSON.parse(await readFile(new URL("../schema/material.schema.json", import.meta.url), "utf8"));
// form.schema.json refs material.schema.json#/$defs/materialRef — pre-register.
ajv.addSchema(material);
const form = JSON.parse(await readFile(new URL("../schema/form.schema.json", import.meta.url), "utf8"));
const validateMaterial = ajv.compile(material);
const validateForm = ajv.compile(form);

const phrase = (ref) => ({ themes: [{ id: "theme.1", phrases: [{ motifs: [ref] }] }] });
const use = (ref) => ({ sections: [{ id: "s.1", role: "verse", uses: [{ ref }] }], order: ["s.1"] });

let passed = 0, failed = 0;
const check = (name, cond) => {
  if (cond) { passed++; console.log(`ok   ${name}`); }
  else {
    failed++;
    console.error(`FAIL ${name}`);
  }
};

const ACCEPT = [
  "motif.a", "theme.1", "groove.1",          // bare ids of all three material kinds
  "motif.a#seq(+2)", "motif.a#seq(-1)",
  "motif.a#inv", "motif.a#retro",
  "motif.a#aug(2)", "motif.a#dim(0.5)",
  "motif.a#inv#seq(+2)",                     // stacked transforms
];
const REJECT = [
  "motif.a#bogus",                           // unknown transform
  "motif.a#seq(+)", "motif.a#aug()",         // malformed args
  "#inv",                                    // empty id
  "motif.a#", "#motif.a",                    // trailing / leading #
  "motif.a###garbage",
];

for (const ref of ACCEPT) {
  check(`phrase position accepts "${ref}"`, validateMaterial(phrase(ref)));
  check(`uses position accepts "${ref}" (parity)`, validateForm(use(ref)));
}
for (const ref of REJECT) {
  check(`phrase position rejects "${ref}"`, !validateMaterial(phrase(ref)));
  check(`uses position rejects "${ref}" (parity)`, !validateForm(use(ref)));
}

// variation is free text (spec §2.4) — not checked against the transform grammar.
check("variation free text accepted", validateForm({
  sections: [{ id: "s.1", role: "verse", uses: [{ ref: "theme.1", variation: "developed, ornamented" }] }],
  order: ["s.1"],
}) && validateForm({
  sections: [{ id: "s.1", role: "verse", uses: [{ ref: "theme.1", variation: "developed#aug(2)+orn" }] }],
  order: ["s.1"],
}));

console.log(`${passed} passed, ${failed} failed`);
process.exit(failed ? 1 : 0);
