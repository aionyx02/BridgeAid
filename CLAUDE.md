---
type: agent_bootstrap
status: active
priority: p0
updated: 2026-06-04
context_policy: always_retrievable
owner: project
---

# CLAUDE.md

> Auto-loaded at session start. Detailed governance, ADR, and documentation-routing rules are in `docs/CLAUDE.md`.

## Session Start

1. Run `npm run team:status` when Node scripts are available.
2. If no local identity is set, ask the human to run `npm run team:whoami -- <member-id>` before starting task work.
3. Read `docs/team/members.md` for registered members.
4. Read `docs/index.md` for documentation routing.
5. Read `docs/memory/current.md` for current strategy, constraints, and next step.
6. Read `docs/tasks/active.md` for the active queue and only work on tasks owned by the current identity unless explicitly reassigned.
7. Retrieve additional documents by intent. For planning, implementation, refactor, or architecture work, read `docs/engineering-principles.md`. Do not recursively load all docs.

## Session Close

Before final response, handoff, or commit:

1. Update only the smallest matching state document.
2. Put detailed execution notes, debugging narrative, and command-output history in `docs/memory/sessions/YYYY-MM-DD.md`.
   - For team workflows, use per-member session files created by `npm run docs:new-session`.
3. Keep `docs/memory/current.md` and `docs/tasks/active.md` as current-state indexes only.
4. Put completed-task detail in the session log using `## COMPLETED: TASK_ID - summary`.
5. Run `npm run docs:refresh` when Node scripts are available.

## Project Overview

- Product: BridgeAid — Proactive Public Service Navigator (主動式公共服務導航系統)
- Primary goal: Let citizens describe a life situation in natural language and proactively surface eligible public services — AI is the entry/translation layer; a verifiable rule engine is the eligibility decider.
- Main users: Digitally excluded citizens, caregivers, renters, unemployed or emergency households, people near eligibility thresholds; plus social workers and NGOs.
- Supported platforms: LINE Bot + Web demo (voice as a later-stage extension). Entry for the 2026 Presidential Hackathon International Track.

## AI Skills

- `/new-service-data <服務名稱或官方網址>` — 從官方來源生成一筆 schema 合格的服務規則資料（含參照資料集與防護驗證）。產出一律 `needs_review`，經人工政策審核後才可轉 `active`。定義在 `.claude/skills/new-service-data/SKILL.md`。

## Git Workflow Rules

```text
main <- always releasable
dev  <- integration
feature/<name> <- work branches
```

- Do not merge without explicit developer confirmation.
- Create feature branches from `dev` unless the repository policy says otherwise.
- Show diffs and pass relevant checks before merge.
- Never rewrite shared history without explicit approval.

## Build / Test Commands

Two toolchains coexist: Node guards govern the docs/context system; Python serves the application (rule engine, FastAPI). Application code does not exist yet — Python commands are the agreed contract for when it lands.

Docs / context governance (Node):

```bash
npm install
npm run lint
npm run security:scan
npm test
npm run team:guard
npm run docs:refresh
npm run docs:ready
```

Application (Python 3.14, once code exists):

```bash
ruff check .
ruff format --check .
pytest
```

## Documentation Entry Points

- `docs/index.md` - documentation router
- `docs/project.md` - stable project facts
- `docs/team/members.md` - fake team registry and task owner IDs
- `docs/memory/current.md` - short working memory
- `docs/tasks/active.md` - active work only
- `docs/engineering-principles.md` - coding style, planning priorities, and decoupled architecture rules
- `docs/CLAUDE.md` - governance and ADR rules
