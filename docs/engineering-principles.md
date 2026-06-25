---
type: engineering_policy
status: active
priority: p1
updated: 2026-06-04
context_policy: retrieve_when_planning
owner: project
---

# Engineering Principles

## Purpose

This file defines the default engineering policy for AI-assisted planning and implementation. Treat it as durable instruction, not temporary task narrative.

## Required Planning Order

When comparing implementation options, use this order:

1. Lower security risk first.
2. Improve memory and CPU efficiency second.
3. Preserve a decoupled architecture as the default design shape.
4. Optimize delivery speed only after the first three are satisfied.

If two options are similar in delivery time, choose the one with lower security exposure and cleaner architectural boundaries.

## Coding Style Baseline

- Follow the relevant Google coding style guide for the implementation language unless the repository already enforces a stricter local formatter or linter.
- Keep naming explicit, predictable, and readable over clever brevity.
- Prefer small units with one clear responsibility.
- Write comments for intent, invariants, or non-obvious tradeoffs, not for obvious line-by-line narration.
- Keep public interfaces stable and minimize surprising side effects.

## Security-First Design Rules

- Prefer least privilege for file, network, process, and data access.
- Validate all external input at the boundary where it enters the system.
- Avoid secret leakage in logs, errors, tests, fixtures, and sample configs.
- Prefer allowlists, explicit contracts, and safe defaults over permissive fallback behavior.
- Treat dependency additions, deserialization, shell execution, and dynamic code paths as elevated-risk areas.
- If a design improves speed but weakens auditability or isolation, reject it unless the user explicitly approves the tradeoff.

## Resource Efficiency Rules

- Reduce unnecessary allocations, copying, serialization, polling, and repeated computation.
- Prefer bounded concurrency, batching, streaming, caching, or memoization only when they improve measured or clearly expected cost.
- Choose data structures that match the expected access pattern and data volume.
- Avoid premature optimization that increases complexity without a realistic memory or CPU benefit.
- When performance work is relevant, document the expected hot path and how it was validated.

## Decoupled Architecture Rules

- Separate interface, application, domain, and infrastructure responsibilities.
- Keep side effects at boundaries and keep core logic independent from transport, storage, and UI frameworks.
- Depend on stable contracts, ports, or abstractions instead of concrete adapters when crossing layers.
- Prefer dependency injection, composition, and explicit module boundaries over hidden global coupling.
- Keep persistence, external services, and framework-specific code replaceable without rewriting domain logic.
- Favor event, command, or service contracts that are small and explicit.

## Implementation Expectations For AI

- Before planning implementation, read this file together with `docs/conventions.md`, `docs/architecture.md`, and `docs/security.md` when relevant.
- If a requested change alters security boundaries, architecture layers, public contracts, or dependency trust, create or update an ADR before broad implementation.
- When tradeoffs are unavoidable, explain the security impact first, then the memory and CPU impact, then the coupling impact.
- Do not merge modules or shortcuts just to save a small amount of code if doing so weakens isolation or testability.
