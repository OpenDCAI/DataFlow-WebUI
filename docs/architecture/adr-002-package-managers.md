# ADR-002: npm is the frontend package manager

- Status: accepted
- Date: 2026-07-29

## Context

The repository disagreed with itself about how to install frontend dependencies:

- `frontend/yarn.lock` is tracked; no `package-lock.json` exists
- `frontend/README.md` documents Yarn as the package manager, with an install
  section devoted to it
- `scripts/setup_all.sh` ran `npm install && npm run build`
- `scripts/build_release.sh` runs `npm ci` when a `package-lock.json` exists and
  otherwise `npm install --no-package-lock`, with a comment explaining that
  `yarn.lock` "contains platform-specific optional packages" that break Linux
  release builds
- `.github/workflows/release.yml` sets up Node with no cache; the `skills-agent`
  branch had tried `cache: npm` with `cache-dependency-path: frontend/yarn.lock`,
  which is incoherent

So the documented tool was Yarn, every executed path used npm, and the lockfile
belonged to Yarn while being deliberately bypassed. A contributor following the
README produced a dependency tree nobody's CI ever built.

## Decision

**npm is the package manager.** One canonical definition, in
`installers/config.sh`:

```sh
DF_NODE_PM="npm"
DF_NODE_PM_INSTALL_CMD="npm install --no-audit --no-fund"
```

Installer and docs read from there rather than restating a command.

`yarn.lock` stays tracked for now: deleting it and generating a
`package-lock.json` changes the resolved dependency tree, which is a separate
change with its own testing burden and does not belong in a repo-organization
pass. It is currently a stale artifact, not an input.

## Follow-up required

This decision is not finished until a lockfile npm actually reads exists:

1. Generate `frontend/package-lock.json` on Linux
2. Verify the frontend builds and the canvas works against it
3. Delete `frontend/yarn.lock`
4. Switch `build_release.sh` to `npm ci` unconditionally, and enable
   `cache: npm` with `cache-dependency-path: frontend/package-lock.json` in CI

Until then builds are not byte-reproducible: `npm install` without a lockfile
resolves versions afresh. That is the status quo this ADR inherits, not something
it introduces — but it should not be left indefinitely.

## Alternatives rejected

**Standardize on Yarn.** It matches the README and the tracked lockfile, but
every working install path and the release pipeline would have to change, and the
recorded reason for avoiding `yarn.lock` (platform-specific optional packages
breaking Linux release builds) is a concrete problem npm does not currently have
here.

**Support both.** Two lockfiles drift and produce different trees. The
inconsistency this ADR resolves is exactly that failure.

## Consequences

- `frontend/README.md` must be corrected to describe npm
- contributors using Yarn must switch
- builds stay non-reproducible until the follow-up lands
