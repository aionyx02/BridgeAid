---
type: coding_conventions
status: active
priority: p1
updated: 2026-06-04
context_policy: retrieve_when_planning
owner: project
---

# Coding Conventions

## Purpose

Keep implementation style stable across AI-assisted sessions. This file should contain durable conventions only, not temporary task notes.

## Naming

| Item | Convention |
|---|---|
| Files | Use `kebab-case` for source files, docs, scripts, and modules unless the language ecosystem has a stronger standard. |
| Functions | Use `camelCase` for functions and methods. Prefer verb-first names for behavior and noun-first names for pure selectors or accessors. |
| Classes / Components | Use `PascalCase` for classes, UI components, and dependency container types. |
| Tests | Use `*.test.<ext>` for executable tests and keep the filename aligned with the unit or module under test. |

## Code Style

- Follow the relevant Google coding style guide for the implementation language unless the repository already enforces a stricter local formatter or linter.
- Prefer small modules and functions with one clear responsibility.
- Keep side effects at application boundaries and keep core logic framework-agnostic when practical.
- Avoid hidden global state, ambient mutation, and implicit cross-module coupling.
- Do not introduce a new dependency when an existing dependency or standard library feature is enough.
- Prefer explicit validation, error paths, and return contracts over silent fallback behavior.
- Optimize for readability and reviewability before cleverness.

## Architectural Shape

- Default to decoupled layers: interface, application orchestration, domain logic, and infrastructure adapters.
- Depend on stable contracts instead of concrete implementations when crossing layers.
- Prefer composition and dependency injection over hard-coded singletons.
- Keep persistence, transport, and framework code replaceable without rewriting domain logic.

## Resource Efficiency

- Avoid repeated parsing, serialization, allocation, and I/O when the same result can be reused safely.
- Use data structures and algorithms that match the expected access pattern instead of optimizing for hypothetical scale.
- Add caching, batching, or concurrency only when the cost model is understood and the lifecycle is bounded.

## Error Handling

- User-facing errors should be actionable and avoid leaking internals.
- Internal errors should preserve enough context for debugging and incident review.
- Do not swallow exceptions silently.
- Do not expose secrets, credentials, tokens, or private paths in error messages.

## Logging

- Logs must not contain secrets or sensitive user data.
- Debug logs should be removable, gated, or clearly scoped.
- Long command output belongs in session logs, not in always-retrievable docs.
- Security-relevant warnings should be structured enough to support triage.
