import { exists, read, walk } from './docs-utils.mjs';

const files = [
  'README.md',
  'CLAUDE.md',
  'EXTRACTED_WORKFLOW.md',
  ...walk('docs', file => file.endsWith('.md')),
  ...walk('.github', file => /\.(?:yml|yaml|md|json)$/i.test(file))
].filter((file, index, list) => exists(file) && list.indexOf(file) === index);

const patterns = [
  ['AWS access key', /\bAKIA[0-9A-Z]{16}\b/g],
  ['GitHub token', /\bgh[pousr]_[A-Za-z0-9]{20,255}\b/g],
  ['Google API key', /\bAIza[0-9A-Za-z_-]{35}\b/g],
  ['Slack token', /\bxox[baprs]-[A-Za-z0-9-]{10,}\b/g],
  ['Private key block', /-----BEGIN (?:RSA |EC |DSA |OPENSSH )?PRIVATE KEY-----/g]
];

let failed = false;

for (const file of files) {
  const content = read(file);
  for (const [label, pattern] of patterns) {
    pattern.lastIndex = 0;
    if (!pattern.test(content)) continue;
    console.error(`SECRET FAIL ${file}: detected ${label}`);
    failed = true;
  }
}

if (!failed) console.log('secret scan ok');
process.exit(failed ? 1 : 0);
