import { read } from './docs-utils.mjs';
import { loadMembers, readIdentity } from './team-utils.mjs';

const identity = readIdentity();
const members = loadMembers();
const active = read('docs/tasks/active.md');
const taskRows = [];

for (const rawTask of active.split(/^###\s+/m).slice(1)) {
  const title = rawTask.split('\n')[0].trim();
  const status = rawTask.match(/^- Status:\s*([^\n]+)/m)?.[1]?.trim() || '(missing)';
  const owner = rawTask.match(/^- Owner:\s*([^\n]+)/m)?.[1]?.trim() || '(missing)';
  taskRows.push({ title, status, owner });
}

console.log(`current identity: ${identity?.memberId || '(not set)'}`);
console.log(`registered members: ${members.filter(member => member.active).length} active / ${members.length} total`);

if (!taskRows.length) {
  console.log('active tasks: none');
} else {
  console.log('active tasks:');
  for (const task of taskRows) {
    console.log(`- ${task.title} [${task.status}] owner=${task.owner}`);
  }
}
