// Cross-reference integrity (code, not ajv) — pure ESM, no node imports, so
// the explorer can bundle it alongside tools/semantics.mjs.
// Material ids: motifs, themes, rhythms entries carry `id`; refs may carry
// transform suffixes (`motif.a#seq(+2)`) that strip to the base id.
const materialIds = (doc) => {
  const ids = new Set();
  for (const key of ["motifs", "themes", "rhythms"])
    for (const item of doc?.material?.[key] ?? []) if (item?.id) ids.add(item.id);
  return ids;
};
const progressionIds = (doc) =>
  new Set((doc?.material?.harmony?.progressions ?? []).map((p) => p?.id).filter(Boolean));

const sectionIds = (doc) =>
  new Set((doc?.form?.sections ?? []).map((s) => s?.id).filter(Boolean));

export const baseRef = (ref) => String(ref).split("#")[0];

export function danglingRefs(doc) {
  const ids = materialIds(doc);
  const progs = progressionIds(doc);
  const sections = sectionIds(doc);
  const out = [];
  // Intra-material: theme phrase motif refs (same id pool as uses refs).
  for (const t of doc?.material?.themes ?? [])
    for (const [pi, p] of (t?.phrases ?? []).entries())
      for (const ref of p?.motifs ?? [])
        if (ref && !ids.has(baseRef(ref)))
          out.push({ path: `material.themes[${t.id}].phrases[${pi}].motifs`, ref });
  for (const s of doc?.form?.sections ?? []) {
    if (s?.harmony && !progs.has(s.harmony))
      out.push({ path: `form.sections[${s.id}].harmony`, ref: s.harmony });
    for (const u of s?.uses ?? [])
      if (u?.ref && !ids.has(baseRef(u.ref)))
        out.push({ path: `form.sections[${s.id}].uses`, ref: u.ref });
  }
  // form.order entries, form.repetition keys, constraints.tempo_lock keys
  // are section ids; constraints.register keys are material ids.
  for (const ref of doc?.form?.order ?? [])
    if (ref && !sections.has(ref)) out.push({ path: "form.order", ref });
  for (const key of Object.keys(doc?.form?.repetition ?? {}))
    if (!sections.has(key)) out.push({ path: "form.repetition", ref: key });
  for (const ref of doc?.constraints?.must_contain ?? [])
    if (!ids.has(baseRef(ref))) out.push({ path: "constraints.must_contain", ref });
  for (const key of Object.keys(doc?.constraints?.tempo_lock ?? {}))
    if (!sections.has(key)) out.push({ path: "constraints.tempo_lock", ref: key });
  for (const key of Object.keys(doc?.constraints?.register ?? {}))
    if (!ids.has(key)) out.push({ path: "constraints.register", ref: key });
  return out;
}
