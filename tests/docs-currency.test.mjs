// Docs currency guard (issue #117, per tests/open_20260822-212650_agents-md.md):
// AGENTS.md's named commands resolve, and every directory in its layout block
// exists on disk. Documentation is executable claims — pin it.
// Standalone runner: `node tests/docs-currency.test.mjs`; also folded into npm test.
import { readFile } from "node:fs/promises";
import { existsSync } from "node:fs";

const agents = await readFile(new URL("../AGENTS.md", import.meta.url), "utf8");
const pkg = JSON.parse(await readFile(new URL("../package.json", import.meta.url), "utf8"));

let passed = 0, failed = 0;
const check = (name, cond) => {
  if (cond) { passed++; console.log(`ok   ${name}`); }
  else { failed++; console.error(`FAIL ${name}`); }
};

// Named npm commands in the Build/test section resolve as package scripts.
const buildSection = agents.slice(agents.indexOf("## Build / test"), agents.indexOf("## Repository layout"));
const npmRuns = [...buildSection.matchAll(/npm run ([a-z:-]+)/g)].map((m) => m[1]);
check("Build/test names at least validate + test:explorer",
  npmRuns.includes("validate") && npmRuns.includes("test:explorer"));
for (const script of new Set(npmRuns))
  check(`npm run ${script} resolves in package.json scripts`, script in (pkg.scripts ?? {}));
check("npm test is named and resolves",
  buildSection.includes("npm test") && "test" in (pkg.scripts ?? {}));
check("benchmark metrics CLI named",
  buildSection.includes("benchmark/metrics.mjs") && existsSync(new URL("../benchmark/metrics.mjs", import.meta.url)));

// Layout block: every top-level directory listed exists on disk.
const layoutBlock = agents.slice(agents.indexOf("## Repository layout"));
const dirs = [...layoutBlock.matchAll(/^([a-z][a-z0-9_-]+\/)\s/gm)].map((m) => m[1]);
check("layout block lists directories", dirs.length >= 8);
for (const d of dirs)
  check(`${d} exists on disk`, existsSync(new URL(`../${d}`, import.meta.url)));

console.log(`${passed} passed, ${failed} failed`);
process.exit(failed ? 1 : 0);
