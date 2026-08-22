// Lockfile invariant (issue #41, per tests/open_20260822-022430_lockfile.md).
// CI's `npm ci` is the primary detector; this suite is the equivalent harness
// step so the invariant also fails locally under `npm test`.
// Standalone runner: `node tests/lockfile.test.mjs`; also folded into npm test.
import { readFile } from "node:fs/promises";

let passed = 0, failed = 0;
const check = (name, cond) => {
  if (cond) { passed++; console.log(`ok   ${name}`); }
  else { failed++; console.error(`FAIL ${name}`); }
};

const pkg = JSON.parse(await readFile(new URL("../package.json", import.meta.url), "utf8"));
const lock = JSON.parse(await readFile(new URL("../package-lock.json", import.meta.url), "utf8"));
const gitignore = await readFile(new URL("../.gitignore", import.meta.url), "utf8");

check("package-lock.json exists and parses", !!lock);
check("package-lock.json not matched by .gitignore",
  !gitignore.split("\n").some((l) => l.trim() && !l.trim().startsWith("#") && l.includes("package-lock")));
// lockfileVersion 3 needs npm >= 7; CI pins node 22 (npm 10). Bump deliberately.
check("lockfileVersion is 3", lock.lockfileVersion === 3);

// Sync check mirroring npm ci's failure mode: package.json dependency specs
// must equal the lockfile's root entries exactly.
const lockRoot = lock.packages?.[""] ?? {};
for (const field of ["dependencies", "devDependencies"]) {
  const declared = pkg[field] ?? {};
  const locked = lockRoot[field] ?? {};
  check(`${field}: same package set in package.json and lockfile`,
    JSON.stringify(Object.keys(declared).sort()) === JSON.stringify(Object.keys(locked).sort()));
  check(`${field}: version specs in sync`,
    Object.entries(declared).every(([name, spec]) => locked[name] === spec));
}

console.log(`${passed} passed, ${failed} failed`);
process.exit(failed ? 1 : 0);
