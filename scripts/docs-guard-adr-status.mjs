import { parseFrontmatter, read, walk } from './docs-utils.mjs';

const allowed = new Set(['proposed', 'accepted', 'rejected', 'superseded', 'template']);
const templateFile = 'docs/adr/0000-template.md';
const adrFilePattern = /^docs\/adr\/\d{4}-[a-z0-9-]+\.md$/;
let failed = false;

for (const file of walk('docs/adr', f => f.endsWith('.md'))) {
  if (file !== templateFile && !adrFilePattern.test(file)) {
    console.error(`ADR NAME FAIL ${file}: expected docs/adr/0001-short-title.md`);
    failed = true;
  }

  const content = read(file);
  const fm = parseFrontmatter(content) || {};
  const currentAdrId = content.match(/^#\s+ADR-(\d{4}):/m)?.[1];

  if (!allowed.has(fm.status)) {
    console.error(`ADR STATUS FAIL ${file}: ${fm.status || '(missing)'}`);
    failed = true;
  }

  if (file === templateFile && fm.status !== 'template') {
    console.error(`ADR TEMPLATE FAIL ${file}: template file must use status: template`);
    failed = true;
  }

  if (fm.status === 'accepted') {
    for (const heading of ['## Decision', '## Consequences']) {
      if (!content.includes(heading)) {
        console.error(`ADR ACCEPTED FAIL ${file}: missing ${heading}`);
        failed = true;
      }
    }
  }

  const referencedAdrIds = [
    ...content.matchAll(/ADR-(\d{4})|docs\/adr\/(\d{4})-/gi)
  ].map(match => match[1] || match[2]);
  const namesReplacement = /superseded by|replaced by/i.test(content)
    || referencedAdrIds.some(id => id !== currentAdrId);

  if (fm.status === 'superseded' && !namesReplacement) {
    console.error(`ADR SUPERSEDED FAIL ${file}: must identify replacement ADR`);
    failed = true;
  }
}

if (!failed) console.log('adr status ok');
process.exit(failed ? 1 : 0);
