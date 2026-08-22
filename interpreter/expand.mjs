// Interpreter expansion harness (issue #23, per docs/scope-batch3.md).
// .muse.json + rendition → performance document via an LLM, with the
// generate → validate → fix loop: schema validation (ajv) then reference
// integrity (checkPerfRefs), error feedback into the retry, bounded
// attempts, fail loudly. Model-agnostic: callModel is injectable; the
// default resolves provider/model/key from env (never hard-coded).
// Provenance: model + timestamp stamped into metadata.interpreter by the
// harness — never trusted to the model.
import { readFile, readdir } from "node:fs/promises";
import path from "node:path";
import Ajv from "ajv/dist/2020.js";
import addFormats from "ajv-formats";
import { checkPerfRefs } from "../tools/semantics.mjs";

const REPO = new URL("..", import.meta.url);
const readJson = async (p) => JSON.parse(await readFile(p, "utf8"));

let validatorPromise;
const perfValidator = async () => {
  validatorPromise ??= (async () => {
    const dir = new URL("../schema/", import.meta.url);
    const ajv = new Ajv({ allErrors: true, strict: false });
    addFormats(ajv);
    for (const f of (await readdir(dir)).filter((f) => f.endsWith(".schema.json")))
      ajv.addSchema(await readJson(new URL(f, dir)));
    return ajv.getSchema("https://muse.dev/schema/performance.schema.json");
  })();
  return validatorPromise;
};

const IMPLICIT_DEFAULT = { id: "r.default", name: "Default" };

const resolveRendition = (doc, renditionId) => {
  const renditions = doc.renditions ?? [];
  if (renditionId) {
    const r = renditions.find((r) => r.id === renditionId);
    if (!r) throw new Error(`rendition "${renditionId}" not found in document`);
    return r;
  }
  // No sanctioned renditions = the work's untransformed default treatment
  // (importer convention, docs/scope-importer.md); zero is not ambiguous.
  if (renditions.length === 0) return IMPLICIT_DEFAULT;
  if (renditions.length > 1) throw new Error(`multiple renditions — pick one of: ${renditions.map((r) => r.id).join(", ")}`);
  return renditions[0];
};

export const buildPrompt = ({ doc, rendition, perfSchema, constraintSummary }) => ({
  system:
    "You are the Muse interpreter: you expand a .muse.json composition schema plus an active " +
    "rendition into exactly one performance-layer document. Output ONLY the performance " +
    "document as JSON — no prose, no markdown fences, no partial output. The document must " +
    "validate against the provided performance JSON Schema and satisfy the constraint summary. " +
    "Seconds are authoritative for playback; beats must agree with the tempo_map you emit. " +
    "Every constraints.must_contain motif must be realized recognizably.",
  user: JSON.stringify({
    muse_document: doc,
    active_rendition: rendition,
    performance_schema: perfSchema,
    constraint_summary: constraintSummary,
  }),
});

export const summarizeConstraints = (doc) => ({
  must_contain: doc.constraints?.must_contain ?? [],
  tempo: doc.globals?.tempo ?? null,
  register: doc.constraints?.register ?? {},
  tempo_lock: doc.constraints?.tempo_lock ?? {},
  form_deviation: doc.constraints?.structure?.form_deviation ?? "none",
});

// Strict parse: the contract is JSON-only output. Code fences tolerated
// (models add them despite instructions); prose around JSON is not.
export const parseModelOutput = (text) => {
  const trimmed = String(text).trim().replace(/^```(?:json)?\s*|\s*```$/g, "");
  return JSON.parse(trimmed);
};

const validatePerf = async (perf) => {
  const validate = await perfValidator();
  const schemaErrors = validate(perf) ? [] : (validate.errors ?? []).map((e) => `${e.instancePath || "/"} ${e.message}`);
  return [...schemaErrors, ...checkPerfRefs(perf)];
};

export async function expand({ doc, renditionId, callModel, model, maxAttempts = 3, at }) {
  const rendition = resolveRendition(doc, renditionId);
  const perfSchema = await readJson(new URL("../schema/performance.schema.json", import.meta.url));
  const prompt = buildPrompt({ doc, rendition, perfSchema, constraintSummary: summarizeConstraints(doc) });
  const stampedAt = at ?? new Date().toISOString();

  let feedback = null;
  let lastErrors = [];
  for (let attempt = 1; attempt <= maxAttempts; attempt++) {
    const messages = feedback ? { ...prompt, user: `${prompt.user}\n\nprevious attempt failed validation:\n${feedback}` } : prompt;
    let perf;
    try {
      perf = parseModelOutput(await callModel(messages, { attempt }));
    } catch (e) {
      lastErrors = [`output was not parseable JSON: ${e.message}`];
      feedback = lastErrors.join("\n");
      continue;
    }
    const errors = await validatePerf(perf);
    if (errors.length === 0) {
      // Provenance is stamped by the harness — never trusted to the model.
      perf.metadata.interpreter = { model, at: stampedAt };
      return { perf, rendition, attempts: attempt };
    }
    lastErrors = errors;
    feedback = errors.join("\n");
  }
  const err = new Error(`expansion failed after ${maxAttempts} attempts:\n${lastErrors.join("\n")}`);
  err.validationErrors = lastErrors;
  throw err;
}

// --- Default model adapter (env-configured; inject callModel to bypass) ---

const anthropicCall = async ({ model, apiKey, baseUrl, prompt }) => {
  const res = await fetch(`${baseUrl}/v1/messages`, {
    method: "POST",
    headers: { "content-type": "application/json", "x-api-key": apiKey, "anthropic-version": "2023-06-01" },
    body: JSON.stringify({
      model,
      max_tokens: 8192,
      system: prompt.system,
      messages: [{ role: "user", content: prompt.user }],
    }),
  });
  if (!res.ok) throw new Error(`anthropic ${res.status}: ${await res.text()}`);
  const data = await res.json();
  return data.content?.map((b) => b.text ?? "").join("") ?? "";
};

const openaiCall = async ({ model, apiKey, baseUrl, prompt }) => {
  const res = await fetch(`${baseUrl}/chat/completions`, {
    method: "POST",
    headers: { "content-type": "application/json", authorization: `Bearer ${apiKey}` },
    body: JSON.stringify({
      model,
      messages: [
        { role: "system", content: prompt.system },
        { role: "user", content: prompt.user },
      ],
      response_format: { type: "json_object" },
    }),
  });
  if (!res.ok) throw new Error(`openai ${res.status}: ${await res.text()}`);
  const data = await res.json();
  return data.choices?.[0]?.message?.content ?? "";
};

// Returns { callModel, model } from env config. Prompt-aware adapter
// selection lives here; provider adapters above are the wire shapes.
export const defaultModelConfig = (env = process.env) => {
  const provider = env.MUSE_PROVIDER ?? "anthropic";
  const model = env.MUSE_MODEL;
  if (!model) throw new Error("MUSE_MODEL is required (model-agnostic: no default model is hard-coded)");
  if (provider === "anthropic") {
    const apiKey = env.ANTHROPIC_API_KEY;
    if (!apiKey) throw new Error("ANTHROPIC_API_KEY is required for MUSE_PROVIDER=anthropic");
    const baseUrl = env.MUSE_BASE_URL ?? "https://api.anthropic.com";
    return { model, callModel: (prompt) => anthropicCall({ model, apiKey, baseUrl, prompt }) };
  }
  if (provider === "openai") {
    const apiKey = env.OPENAI_API_KEY;
    if (!apiKey) throw new Error("OPENAI_API_KEY is required for MUSE_PROVIDER=openai");
    const baseUrl = env.MUSE_BASE_URL ?? "https://api.openai.com/v1";
    return { model, callModel: (prompt) => openaiCall({ model, apiKey, baseUrl, prompt }) };
  }
  throw new Error(`unknown MUSE_PROVIDER "${provider}" (anthropic | openai)`);
};

// --- CLI ---
const invokedDirectly = process.argv[1] && path.resolve(process.argv[1]) === new URL(import.meta.url).pathname;
if (invokedDirectly) {
  const [docPath, renditionId, outPath] = process.argv.slice(2);
  if (!docPath) {
    console.error("usage: node interpreter/expand.mjs <doc.muse.json> [rendition-id] [out.muse.perf.json]");
    process.exit(1);
  }
  const doc = await readJson(docPath);
  const { callModel, model } = defaultModelConfig();
  const { perf, attempts } = await expand({ doc, renditionId, callModel, model });
  const { writeFile } = await import("node:fs/promises");
  const text = JSON.stringify(perf, null, 2) + "\n";
  if (outPath) await writeFile(outPath, text);
  else process.stdout.write(text);
  console.error(`expanded ${docPath} (rendition ${perf.metadata.source.rendition_id}) in ${attempts} attempt(s)`);
}
