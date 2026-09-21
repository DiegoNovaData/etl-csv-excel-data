# 0001. Record architecture decisions

## Status
Accepted

## Context
This project will grow through several stages (Extract, Transform, Load) and will
be shared publicly as part of a freelance portfolio. Decisions about data sources,
storage formats, and pipeline design need to be traceable so that future
contributors (or the author, months later) understand *why* a choice was made,
not just *what* was implemented.

## Decision
We will use Architecture Decision Records (ADRs), as described by
[Michael Nygard](https://cognitect.com/blog/2011/11/15/documenting-architecture-decisions),
to capture significant architectural decisions made throughout this project.

Each ADR is a short Markdown file in `docs/adr/`, numbered sequentially, with the
following sections: Status, Context, Decision, Consequences.

## Consequences
- Every non-trivial architectural choice (data source, storage format, tooling,
  pipeline structure) should be documented as a new ADR.
- ADRs are immutable once accepted; a changed decision is recorded as a new ADR
  that supersedes the previous one, rather than editing history.
