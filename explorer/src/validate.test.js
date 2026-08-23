// Validation parity: explorer/src/validate.js must agree with the repo
// tooling — examples validate clean; invalid examples fail through the
// sidecar's pinned channel with the pinned messages. Runs against the real
// bundled schema set + shared lint modules.
import { describe, test, expect } from "vitest";
import { readFileSync, readdirSync } from "node:fs";
import { validateDocument } from "./validate.js";

const EXAMPLES = "public/examples";
const readJson = (p) => JSON.parse(readFileSync(p, "utf8"));

describe("validation parity", () => {
  const validFiles = readdirSync(EXAMPLES).filter((f) => f.endsWith(".muse.json"));
  test("every examples/*.muse.json is clean", () => {
    for (const f of validFiles)
      expect(validateDocument(readJson(`${EXAMPLES}/${f}`)), f).toEqual([]);
  });

  const invalidDir = `${EXAMPLES}/invalid`;
  const invalidFiles = readdirSync(invalidDir).filter((f) => f.endsWith(".muse.json"));
  test("every examples/invalid/*.muse.json fails through its pinned channel", () => {
    for (const f of invalidFiles) {
      const sidecar = readJson(`${invalidDir}/${f.replace(/\.muse\.json$/, ".expected.json")}`);
      const issues = validateDocument(readJson(`${invalidDir}/${f}`));
      expect(issues.length, f).toBeGreaterThan(0);
      const fired = [
        ["schema", issues.some((i) => i.channel === "schema")],
        ["refs", issues.some((i) => i.channel === "refs")],
        ["semantics", issues.some((i) => i.channel === "semantics")],
      ].filter(([, hit]) => hit).map(([ch]) => ch);
      if (sidecar.channel) expect(fired[0], `${f}: first channel`).toEqual(sidecar.channel);
      for (const m of sidecar.messages ?? [])
        expect(issues.some((i) => i.message.includes(m)), `${f}: message "${m}"`).toBe(true);
    }
  });
});
