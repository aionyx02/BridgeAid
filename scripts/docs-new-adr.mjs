import { exists, today, walk, write } from './docs-utils.mjs';

const title = process.argv.slice(2).join(' ').trim();

if (!title) {
  console.error('Usage: npm run docs:new-adr -- "Decision title"');
  process.exit(1);
}

function slugify(value) {
  const slug = value
    .normalize('NFKD')
    .toLowerCase()
    .replace(/[^a-z0-9]+/g, '-')
    .replace(/^-+|-+$/g, '')
    .replace(/-{2,}/g, '-')
    .slice(0, 60)
    .replace(/-+$/g, '');
  return slug || 'decision';
}

const ids = walk('docs/adr', file => /^docs\/adr\/\d{4}-[a-z0-9-]+\.md$/.test(file))
  .map(file => Number(file.match(/^docs\/adr\/(\d{4})-/)?.[1]))
  .filter(Number.isFinite);

const next = String(Math.max(0, ...ids) + 1).padStart(4, '0');
const file = `docs/adr/${next}-${slugify(title)}.md`;

if (exists(file)) {
  console.error(`ADR exists: ${file}`);
  process.exit(1);
}

const body = `---\ntype: adr\nstatus: proposed\npriority: p1\nupdated: ${today()}\ncontext_policy: on_demand\nowner: project\n---\n\n# ADR-${next}: ${title}\n\n## Status\n\nProposed\n\n## Context\n\nWhat problem forces a decision? Include constraints, prior state, and security or performance concerns.\n\n## Decision\n\nWhat decision is being proposed?\n\n## Consequences\n\n### Positive\n\n- TBD\n\n### Negative\n\n- TBD\n\n### Neutral / Tradeoffs\n\n- TBD\n\n## Alternatives Considered\n\n| Option | Pros | Cons | Reason not chosen |\n|---|---|---|---|\n| TBD | TBD | TBD | TBD |\n\n## Security Review\n\n- Trust boundary impact: TBD\n- Sensitive data impact: TBD\n- Permission impact: TBD\n- Failure mode: TBD\n\n## Resource Impact\n\n- Memory impact: TBD\n- CPU impact: TBD\n- I/O impact: TBD\n\n## Rollback Plan\n\n- TBD\n`;

write(file, body);
console.log(`created ${file}`);
