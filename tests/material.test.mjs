// Tests for schema/material.schema.json (issue #29, per
// tests/open_20260822-001000_material-schema.md).
// Standalone runner: `node tests/material.test.mjs`; also folded into npm test.
import { readFile } from "node:fs/promises";
import Ajv from "ajv/dist/2020.js";

const schema = JSON.parse(await readFile(new URL("../schema/material.schema.json", import.meta.url), "utf8"));
const ajv = new Ajv({ allErrors: true, strict: false });
const validate = ajv.compile(schema);

let passed = 0, failed = 0;
const check = (name, cond) => {
  if (cond) { passed++; console.log(`ok   ${name}`); }
  else {
    failed++;
    console.error(`FAIL ${name}`);
    console.error(JSON.stringify(validate.errors, null, 2));
  }
};

const themeWith = (motifRefs) => ({ themes: [{ id: "theme.1", phrases: [{ motifs: motifRefs }] }] });

// Full spec §2.3 example validates.
const specSnippet = {
  motifs: [
    {
      id: "motif.a",
      kind: "pitch_rhythm",
      pitches: ["D4", "F4", "A4", "G4"],
      durations: [0.5, 0.5, 1.0, 1.0],
      contour: "up-up-down",
      tags: ["primary", "opening"],
    },
  ],
  themes: [
    {
      id: "theme.1",
      phrases: [{ motifs: ["motif.a", "motif.a#seq(+2)"] }],
      cadence: "half",
    },
  ],
  rhythms: [
    { id: "groove.1", pattern: [1, 0, 0.75, 0, 1, 0, 0.75, 0.25], grid: "8n" },
  ],
  harmony: {
    progressions: [
      { id: "prog.verse", chords: ["Dm7", "G7", "Cmaj7", "Am7"], bars_per_chord: 1 },
    ],
    vocabulary: "diatonic-plus-bVII",
  },
};
check("spec §2.3 example validates", validate(specSnippet));

// Top-level shape
check("empty {} validates (all sub-objects optional)", validate({}));
check("unknown top-level property rejected", !validate({ bogus: true }));

// motifs[].kind enum + required
check("motif kind enum accepted", validate({ motifs: [{ id: "m", kind: "timbre" }] }));
check("motif kind outside enum rejected", !validate({ motifs: [{ id: "m", kind: "melodic" }] }));
check("motif missing kind rejected", !validate({ motifs: [{ id: "m" }] }));

// Transform references (motifRef pattern)
check("plain motif id valid", validate(themeWith(["motif.a"])));
check("#seq(+2) valid", validate(themeWith(["motif.a#seq(+2)"])));
check("#seq(-1) valid", validate(themeWith(["motif.a#seq(-1)"])));
check("#inv valid", validate(themeWith(["motif.a#inv"])));
check("#retro valid", validate(themeWith(["motif.a#retro"])));
check("#aug(2) valid", validate(themeWith(["motif.a#aug(2)"])));
check("#dim(0.5) valid", validate(themeWith(["motif.a#dim(0.5)"])));
check("chained #retro#aug(2) valid", validate(themeWith(["motif.a#retro#aug(2)"])));
check("unknown transform #bogus rejected", !validate(themeWith(["motif.a#bogus"])));
check("bare #inv (no id) rejected", !validate(themeWith(["#inv"])));

// Numeric edge cases
check("durations entry 0 rejected", !validate({ motifs: [{ id: "m", kind: "rhythm", durations: [0] }] }));
check("durations entry negative rejected", !validate({ motifs: [{ id: "m", kind: "rhythm", durations: [-0.5] }] }));
check("rhythms pattern 0 allowed (rest)", validate({ rhythms: [{ id: "r", pattern: [1, 0] }] }));
check("rhythms pattern negative rejected", !validate({ rhythms: [{ id: "r", pattern: [-1] }] }));
check("bars_per_chord 0 rejected", !validate({ harmony: { progressions: [{ id: "p", chords: ["Dm7"], bars_per_chord: 0 }] } }));

console.log(`${passed} passed, ${failed} failed`);
process.exit(failed ? 1 : 0);
