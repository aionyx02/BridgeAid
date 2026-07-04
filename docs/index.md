---
type: docs_index
status: active
priority: p1
updated: 2026-06-04
context_policy: on_demand
owner: project
---

# Documentation Index

## Why this exists

Use this file as the first lookup step. The goal is retrieval-first context, not full-doc prompt injection.

## Default Read Order

1. `docs/index.md`
2. `docs/memory/current.md`
3. `docs/tasks/active.md`
4. Additional files by intent

## Retrieval Policy

- Do not read all docs recursively.
- Prefer the smallest relevant heading section.
- Startup context should stay below guard limits.
- `completed`, `sessions`, and `archive` files are historical context only.
- If sources conflict: active task + current memory > accepted ADRs > reference docs > sessions/archive.

## Intent Routing

| Intent | Primary docs |
|---|---|
| What should I do now? | `docs/memory/current.md`, `docs/tasks/active.md`, `docs/tasks/blocked.md` |
| Team identity / ownership | `docs/team/members.md`, `docs/tasks/active.md`, `docs/CLAUDE.md` |
| Planning / solution design | `docs/engineering-principles.md`, `docs/architecture.md`, `docs/security.md`, `docs/conventions.md` |
| Implementation | `docs/tasks/active.md`, related task plan, `docs/engineering-principles.md`, `docs/architecture.md`, `docs/conventions.md`, targeted code |
| Bug fix | `docs/testing.md`, `docs/testing-edge-cases.md`, `docs/conventions.md`, active task, related session log |
| Refactor | `docs/engineering-principles.md`, `docs/conventions.md`, `docs/architecture.md`, active task |
| Architecture decision | `docs/engineering-principles.md`, `docs/adr/*`, `docs/decisions.md`, `docs/architecture.md` |
| Dependency change | `docs/engineering-principles.md`, `docs/dependencies.md`, `docs/adr/*`, `docs/security.md` if relevant |
| Data model / schema | `docs/data.md`, `docs/architecture.md`, related ADR |
| API contract | `docs/data.md`, `docs/testing.md`, related ADR |
| Security / permission | `docs/engineering-principles.md`, `docs/tasks/blocked.md`, `docs/security.md`, relevant ADR |
| Testing / regression | `docs/testing.md`, `docs/testing-edge-cases.md`, active task |
| UI implementation | `docs/ui.md`, `docs/design-system.md`, `docs/accessibility.md`, related ADR |
| HTML structure | `docs/html-guidelines.md`, `docs/accessibility.md`, related task |
| Design decision | `docs/design-system.md`, `docs/adr/*`, `docs/decisions.md` |
| Accessibility / keyboard UX | `docs/accessibility.md`, `docs/testing.md` |
| Performance | `docs/engineering-principles.md`, `docs/architecture.md`, `docs/testing.md`, related benchmark notes |
| Release / deployment | `docs/release.md`, `docs/testing.md`, `docs/security.md` |
| Historical question | `docs/tasks/completed.md`, `docs/memory/sessions/*`, `docs/memory/archive/*` |
| Product scope | `docs/project.md`, `docs/memory/current.md`, roadmap/backlog |
| Onboarding | `README.md`, `docs/project.md`, `docs/team/members.md`, `docs/engineering-principles.md`, `docs/index.md` |

## Context Budget Example

| Context item | Budget |
|---|---:|
| User request | 1k |
| Current memory | 1k |
| Active tasks | 2k |
| Relevant architecture / ADR | 2k |
| Relevant code snippets | 4k |
| Recent actions / audit | 1k |
| Response reserve | 1k |

## Document Map

| Path | Type | Status | Context policy | Purpose |
|---|---|---|---|---|
| `docs/accessibility.md` | `accessibility_policy` | `active` | `retrieve_when_planning` | Accessibility Policy |
| `docs/adr/0000-template.md` | `adr` | `template` | `on_demand` | Decision Title |
| `docs/adr/0001-html-ui-documentation-boundary.md` | `adr` | `proposed` | `on_demand` | HTML And UI Documentation Boundary |
| `docs/adr/0002-bridgeaid-initial-architecture-and-ai-boundary.md` | `adr` | `accepted` | `on_demand` | BridgeAid initial architecture and AI boundary |
| `docs/adr/0003-backend-skeleton-persistence-secrets-and-api-surface.md` | `adr` | `accepted` | `on_demand` | Backend skeleton: persistence, secrets, and API surface |
| `docs/adr/0004-llm-intent-parser-via-local-ollama.md` | `adr` | `accepted` | `on_demand` | LLM intent parser via local Ollama |
| `docs/adr/0005-opt-in-reminder-system-and-source-trace-endpoints.md` | `adr` | `accepted` | `on_demand` | Opt-in reminder system and source-trace endpoints |
| `docs/adr/0006-reminder-delivery-via-lightweight-in-process-scheduler.md` | `adr` | `accepted` | `on_demand` | Reminder delivery via lightweight in-process scheduler |
| `docs/adr/0007-application-process-data-contract-and-line-interactive-layer.md` | `adr` | `proposed` | `on_demand` | Application process data contract and LINE interactive layer |
| `docs/adr/0008-income-amount-extraction-and-question-strategy.md` | `adr` | `proposed` | `on_demand` | Income amount extraction and question strategy |
| `docs/architecture.md` | `architecture_spec` | `active` | `retrieve_only` | Architecture |
| `docs/CLAUDE.md` | `agent_policy` | `active` | `on_demand` | AI Agent Governance And ADR Policy |
| `docs/conventions.md` | `coding_conventions` | `active` | `retrieve_when_planning` | Coding Conventions |
| `docs/data.md` | `data_contracts` | `active` | `retrieve_when_planning` | Data Contracts |
| `docs/decisions.md` | `decision_index` | `active` | `retrieve_only` | Decision Index |
| `docs/dependencies.md` | `dependency_policy` | `active` | `retrieve_when_planning` | Dependencies |
| `docs/design-system.md` | `design_system` | `active` | `retrieve_when_planning` | Design System |
| `docs/engineering-principles.md` | `engineering_policy` | `active` | `retrieve_when_planning` | Engineering Principles |
| `docs/html-guidelines.md` | `html_guidelines` | `active` | `retrieve_when_planning` | HTML Guidelines |
| `docs/index.md` | `docs_index` | `active` | `on_demand` | Documentation Index |
| `docs/memory/current.md` | `working_memory` | `active` | `always_retrievable` | Current Project Memory |
| `docs/project.md` | `project_overview` | `active` | `always_retrievable` | Project Overview |
| `docs/release.md` | `release_policy` | `active` | `retrieve_when_planning` | Release And Deployment |
| `docs/security.md` | `security_policy` | `active` | `retrieve_only` | Security And Permission Boundary |
| `docs/tasks/active.md` | `task_index` | `active` | `always_retrievable` | Active Tasks |
| `docs/tasks/backlog.md` | `task_index` | `backlog` | `on_demand` | Backlog |
| `docs/tasks/blocked.md` | `task_blockers` | `active` | `retrieve_when_planning` | Blocked / Approval-Gated Work |
| `docs/tasks/completed.md` | `task_archive_index` | `archive` | `on_demand` | Completed Task Index |
| `docs/tasks/task-template.md` | `task_template` | `template` | `on_demand` | TASK.NNN - Task Title |
| `docs/tasks/ui-task-template.md` | `task_template` | `template` | `on_demand` | UI TASK.NNN - Task Title |
| `docs/team/members.md` | `team_registry` | `active` | `retrieve_when_planning` | Team Members |
| `docs/testing-edge-cases.md` | `testing_reference` | `active` | `retrieve_when_debugging` | Testing Edge Cases |
| `docs/testing.md` | `testing_policy` | `active` | `retrieve_when_debugging` | Testing Strategy |
| `docs/ui.md` | `ui_spec` | `active` | `retrieve_when_planning` | UI Architecture |

## Automation Commands

```bash
npm run lint
npm run security:scan
npm test
npm run team:register -- shawn "Shawn"
npm run team:whoami -- shawn
npm run team:status
npm run team:guard
npm run docs:ready
npm run docs:new-adr -- "Decision title"
npm run docs:new-session
npm run docs:sync
npm run docs:guard-size
npm run docs:guard-schema
npm run docs:guard-links
npm run docs:guard-secrets
npm run docs:guard-placeholders
npm run docs:guard-adr-status
npm run docs:guard-task-status
npm run docs:audit-frontmatter
npm run docs:narrative-check
npm run docs:completed-regen
npm run docs:refresh
```
