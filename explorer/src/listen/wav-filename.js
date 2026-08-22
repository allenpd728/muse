// WAV download filename (issue #100/#104): <title>.<rendition-id>.wav with
// spaces collapsed to hyphens; missing/empty/whitespace title → "muse".
// Extracted from ListenTab so the policy is testable in vitest.
export default function wavFilename(metadata, renditionId) {
  const title = (metadata?.title ?? "").trim();
  return `${title ? title.replace(/\s+/g, "-") : "muse"}.${renditionId}.wav`;
}
