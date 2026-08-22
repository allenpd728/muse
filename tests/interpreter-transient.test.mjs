// Transient-error backoff + attempt budget (issue #121): provider 429/5xx
// tagged transient by the adapters, expand() retries them with bounded
// backoff without burning the validation-attempt budget; backoff exhausted
// fails loudly with the provider error. All canned — no live calls.
// Standalone runner; folded into npm test.
import { readFile } from "node:fs/promises";
import { defaultModelConfig, expand } from "../interpreter/expand.mjs";

let passed = 0, failed = 0;
const check = (name, cond) => {
  if (cond) { passed++; console.log(`ok   ${name}`); }
  else { failed++; console.error(`FAIL ${name}`); }
};

const noSleep = () => {};
const minimal = JSON.parse(await readFile(new URL("../examples/minimal.muse.json", import.meta.url), "utf8"));
const fixture = JSON.parse(await readFile(new URL("../interpreter/fixtures/minimal-expansion.muse.perf.json", import.meta.url), "utf8"));

// Adapters tag 429/5xx as transient; 400 (bad key) is terminal.
const cfg = defaultModelConfig({ MUSE_PROVIDER: "gemini", MUSE_MODEL: "m", GEMINI_API_KEY: "k" });
for (const [status, expected] of [[503, true], [429, true], [400, false]]) {
  globalThis.fetch = async () => ({ ok: false, status, text: async () => "body" });
  let err = null;
  try { await cfg.callModel({ system: "s", user: "u" }); } catch (e) { err = e; }
  check(`${status} tagged transient=${expected}`, err !== null && (err.transient === true) === expected && err.message.includes(String(status)));
}

// 503 twice then success: one validation attempt, three calls, loop passes.
{
  let calls = 0;
  globalThis.fetch = async () => {
    calls++;
    if (calls <= 2) return { ok: false, status: 503, text: async () => "UNAVAILABLE" };
    return { ok: true, json: async () => ({ candidates: [{ content: { parts: [{ text: JSON.stringify(fixture) }] } }] }) };
  };
  const { perf, attempts } = await expand({ doc: minimal, callModel: cfg.callModel, model: "gemini-3.6-flash", at: "2026-08-22T22:00:00Z", sleep: noSleep });
  check("503,503 → backoff retries inside attempt 1 and succeeds", calls === 3 && attempts === 1 && !!perf);
}

// Transient beyond the backoff budget fails loudly with the provider error.
{
  globalThis.fetch = async () => ({ ok: false, status: 503, text: async () => "UNAVAILABLE" });
  let err = null;
  try { await expand({ doc: minimal, callModel: cfg.callModel, model: "m", maxAttempts: 1, sleep: noSleep }); }
  catch (e) { err = e; }
  check("backoff exhausted → provider error surfaces, not swallowed",
    err !== null && err.message.includes("503") && err.message.includes("UNAVAILABLE"));
}

// Non-transient provider error (400) is not retried: one call per attempt.
{
  let calls = 0;
  globalThis.fetch = async () => { calls++; return { ok: false, status: 400, text: async () => "bad key" }; };
  let err = null;
  try { await expand({ doc: minimal, callModel: cfg.callModel, model: "m", maxAttempts: 2, sleep: noSleep }); }
  catch (e) { err = e; }
  check("400 error: no transient retry, one call per attempt", calls === 2 && err !== null);
}

// MUSE_MAX_ATTEMPTS bounds the loop when maxAttempts isn't passed.
{
  const prev = process.env.MUSE_MAX_ATTEMPTS;
  process.env.MUSE_MAX_ATTEMPTS = "1";
  const alwaysBad = async () => "{}";
  let err = null;
  try { await expand({ doc: minimal, callModel: alwaysBad, model: "m", sleep: noSleep }); }
  catch (e) { err = e; }
  check("MUSE_MAX_ATTEMPTS=1 bounds the loop", err !== null && err.message.includes("after 1 attempts"));
  if (prev === undefined) delete process.env.MUSE_MAX_ATTEMPTS; else process.env.MUSE_MAX_ATTEMPTS = prev;
}

console.log(`${passed} passed, ${failed} failed`);
process.exit(failed ? 1 : 0);
