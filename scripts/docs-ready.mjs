import { spawnSync } from 'node:child_process';

const steps = [
  ['lint', process.execPath, ['scripts/repo-lint.mjs']],
  ['security:scan', process.execPath, ['scripts/docs-guard-secrets.mjs']],
  ['test', process.execPath, ['--test']],
  ['docs:refresh', process.execPath, ['scripts/docs-refresh.mjs']],
  [
    'docs:guard-placeholders strict',
    process.execPath,
    ['scripts/docs-guard-placeholders.mjs'],
    { STRICT_PLACEHOLDERS: '1' }
  ]
];

for (const [name, cmd, args, env = {}] of steps) {
  console.log(`\n> ${name}`);
  const result = spawnSync(cmd, args, {
    stdio: 'inherit',
    env: { ...process.env, ...env }
  });
  if (result.status !== 0) process.exit(result.status ?? 1);
}

console.log('\ndocs ready ok');
