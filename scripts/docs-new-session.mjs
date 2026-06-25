import { exists, read, today, write } from './docs-utils.mjs';
import { requireIdentity } from './team-utils.mjs';

const date = today();
const { identity, member } = requireIdentity();
const file = `docs/memory/sessions/${date}-${identity.memberId}.md`;

if (exists(file)) {
  console.log(`${file} already exists`);
  process.exit(0);
}

const template = exists('docs/memory/sessions/YYYY-MM-DD.md')
  ? read('docs/memory/sessions/YYYY-MM-DD.md')
    .replaceAll('YYYY-MM-DD', date)
    .replace('owner: project', `owner: ${identity.memberId}`)
    .replace(`# Session Log: ${date}`, `# Session Log: ${date} - ${member.displayName}`)
  : `---\ntype: session_log\nstatus: archive\nupdated: ${date}\ncontext_policy: historical\nowner: ${identity.memberId}\n---\n\n# Session Log: ${date} - ${member.displayName}\n`;

write(file, template);
console.log(`created ${file}`);
