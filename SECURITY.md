# Security Policy

## Supported versions

Rubato (Muse) is pre-launch. Only the current `main` branch is supported;
older commits and the legacy `dev` branch receive no security fixes.

## Reporting a vulnerability

Please report suspected vulnerabilities privately — do not open a public issue.

- Preferred: use GitHub's private vulnerability reporting on this repository
  (Security → Report a vulnerability).
- If that is unavailable, email **pda728@gmail.com** with the details.

Please include: a description of the issue, the affected file or component, the
version/commit you tested, and reproduction steps or a proof of concept.

## What to expect

This is a single-maintainer project, so response times are best-effort:

| Stage | Target |
|---|---|
| Acknowledgement | within 7 days |
| Initial assessment | within 14 days |
| Fix or mitigation plan | as soon as a fix is available |

We will credit reporters in the advisory unless you ask to remain anonymous.

## Scope

In scope: the code and configuration in this repository, on `main`.

Out of scope: the reference corpus audio/scores (public-domain works), and any
third-party dependency vulnerability already covered by an upstream advisory —
we will still happily take a report that Dependabot missed.
