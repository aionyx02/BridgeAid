import { parseFrontmatter, read, walk } from './docs-utils.mjs';

const required = ['type', 'status', 'updated', 'context_policy', 'owner'];
const priorityPattern = /^p[0-3]$/;
const updatedPattern = /^\d{4}-\d{2}-\d{2}$/;
let failed = false;

for (const file of walk('docs', f => f.endsWith('.md'))) {
  const fm = parseFrontmatter(read(file));
  if (!fm) {
    console.error(`FRONTMATTER MISSING ${file}`);
    failed = true;
    continue;
  }
  for (const key of required) {
    if (!fm[key]) {
      console.error(`FRONTMATTER KEY MISSING ${file}: ${key}`);
      failed = true;
    }
  }
  const isDateTemplate = file.endsWith('/YYYY-MM-DD.md') && fm.updated === 'YYYY-MM-DD';
  if (fm.updated && !isDateTemplate && !updatedPattern.test(fm.updated)) {
    console.error(`FRONTMATTER DATE FAIL ${file}: updated must use YYYY-MM-DD`);
    failed = true;
  }
  if (fm.priority && !priorityPattern.test(fm.priority)) {
    console.error(`FRONTMATTER PRIORITY FAIL ${file}: ${fm.priority}`);
    failed = true;
  }
}

if (!failed) console.log('schema ok');
process.exit(failed ? 1 : 0);
