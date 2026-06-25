import { spawnSync } from 'node:child_process';

const steps = [
  ['docs:completed-regen', process.execPath, ['scripts/docs-completed-regen.mjs']],
  ['docs:sync', process.execPath, ['scripts/docs-sync.mjs']],
  ['docs:guard-size', process.execPath, ['scripts/docs-guard-size.mjs']],
  ['docs:guard-schema', process.execPath, ['scripts/docs-guard-schema.mjs']],
  ['docs:guard-links', process.execPath, ['scripts/docs-guard-links.mjs']],
  ['docs:guard-secrets', process.execPath, ['scripts/docs-guard-secrets.mjs']],
  ['team:guard', process.execPath, ['scripts/team-guard.mjs']],
  ['docs:guard-placeholders', process.execPath, ['scripts/docs-guard-placeholders.mjs']],
  ['docs:guard-adr-status', process.execPath, ['scripts/docs-guard-adr-status.mjs']],
  ['docs:guard-task-status', process.execPath, ['scripts/docs-guard-task-status.mjs']],
  ['docs:audit-frontmatter', process.execPath, ['scripts/docs-audit-frontmatter.mjs']],
  ['docs:narrative-check', process.execPath, ['scripts/docs-narrative-check.mjs']]
];

for (const [name, cmd, args] of steps) {
  console.log(`\n> ${name}`);
  const result = spawnSync(cmd, args, { stdio: 'inherit' });
  if (result.status !== 0) process.exit(result.status ?? 1);
}
console.log('\ndocs refresh ok');
