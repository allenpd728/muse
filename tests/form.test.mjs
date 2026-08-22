// Tests for schema/form.schema.json (issue #7, spec §2.4).
// Standalone runner: `node tests/form.test.mjs`; also folded into npm test.
import { readFile } from "node:fs/promises";
import Ajv from "ajv/dist/2020.js";

const schema = JSON.parse(await readFile(new URL("../schema/form.schema.json", import.meta.url), "utf8"));
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

const specSnippet = {
  sections: [
    { id: "verse.1", role: "verse", bars: 16, uses: [{ ref: "theme.1", variation: "plain" }], harmony: "prog.verse", energy: 0.4 },
    { id: "chorus.1", role: "chorus", bars: 8, uses: [{ ref: "theme.1", variation: "developed#aug(2)+orn" }], energy: 0.9 }
  ],
  order: ["verse.1", "chorus.1", "verse.1", "chorus.1"],
  repetition: { "verse.1": { min: 2, max: 4 } }
};

check("spec §2.4 snippet valid", validate(specSnippet));
check("repeated ids in order accepted", validate({ sections: [{ id: "v", role: "verse" }], order: ["v", "v", "v"] }));
check("every role enum value accepted", ["intro", "verse", "pre_chorus", "chorus", "bridge", "solo", "outro", "custom"]
  .every((role) => validate({ sections: [{ id: "x", role }], order: ["x"] })));
check("unknown role rejected", !validate({ sections: [{ id: "x", role: "refrain" }], order: ["x"] }));
check("energy 0 and 1 accepted", validate({ sections: [{ id: "x", role: "verse", energy: 0 }], order: ["x"] })
  && validate({ sections: [{ id: "x", role: "verse", energy: 1 }], order: ["x"] }));
check("energy above 1 rejected", !validate({ sections: [{ id: "x", role: "verse", energy: 1.1 }], order: ["x"] }));
check("energy below 0 rejected", !validate({ sections: [{ id: "x", role: "verse", energy: -0.1 }], order: ["x"] }));
check("uses entry without ref rejected", !validate({ sections: [{ id: "x", role: "verse", uses: [{ variation: "plain" }] }], order: ["x"] }));
check("empty sections rejected", !validate({ sections: [], order: ["x"] }));
check("order with empty string rejected", !validate({ sections: [{ id: "x", role: "verse" }], order: [""] }));
check("unknown member rejected", !validate({ sections: [{ id: "x", role: "verse" }], order: ["x"], coda: {} }));
check("repetition missing min/max rejected", !validate({ sections: [{ id: "x", role: "verse" }], order: ["x"], repetition: { x: { min: 2 } } }));

console.log(`${passed} passed, ${failed} failed`);
process.exit(failed ? 1 : 0);
