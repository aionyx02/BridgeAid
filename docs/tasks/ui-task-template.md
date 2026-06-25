---
type: task_template
status: template
priority: p2
updated: 2026-05-24
context_policy: on_demand
owner: project
---

# UI TASK.NNN - Task Title

## Goal

(what the user should be able to do)

## Scope

### In Scope

- (item)

### Out of Scope

- (item)

## Relevant Docs

- `docs/ui.md`
- `docs/html-guidelines.md`
- `docs/design-system.md`
- `docs/accessibility.md`
- Related ADR: (adr or none)

## Acceptance Criteria

- [ ] Semantic HTML is used correctly.
- [ ] Keyboard navigation works.
- [ ] Responsive layout works.
- [ ] Loading, empty, error, and success states are handled.
- [ ] No unrelated UI redesign is introduced.
- [ ] Relevant tests pass.

## Validation Commands

```bash
npm run lint --if-present
npm run test --if-present
npm run build --if-present
npm run docs:refresh
```

## Risks

| Risk | Mitigation |
|---|---|
| (risk) | (mitigation) |
