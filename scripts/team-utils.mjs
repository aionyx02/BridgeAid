import fs from 'node:fs';
import path from 'node:path';
import { exists, read, resolve, write } from './docs-utils.mjs';

export const MEMBERS_FILE = 'docs/team/members.md';
export const IDENTITY_FILE = '.context/identity.json';

export function normalizeMemberId(value) {
  return value
    .trim()
    .toLowerCase()
    .replace(/[^a-z0-9_-]+/g, '-')
    .replace(/^-+|-+$/g, '');
}

export function loadMembers() {
  if (!exists(MEMBERS_FILE)) return [];
  const content = read(MEMBERS_FILE);
  const rows = [];

  for (const line of content.split('\n')) {
    if (!line.startsWith('|')) continue;
    if (line.includes('---')) continue;
    const cells = line.split('|').slice(1, -1).map(cell => cell.trim());
    if (cells.length < 4 || cells[0] === 'ID') continue;
    rows.push({
      id: cells[0].replaceAll('`', ''),
      displayName: cells[1],
      role: cells[2],
      active: /^true$/i.test(cells[3]),
      notes: cells[4] || ''
    });
  }

  return rows;
}

export function writeMembers(members) {
  const sorted = [...members].sort((a, b) => a.id.localeCompare(b.id));
  let body = `---\ntype: team_registry\nstatus: active\npriority: p1\nupdated: ${new Date().toISOString().slice(0, 10)}\ncontext_policy: retrieve_when_planning\nowner: project\n---\n\n# Team Members\n\nThis fake registry identifies who is allowed to own tasks and create session logs. It is not authentication; it is coordination metadata for shared context engineering.\n\n| ID | Display name | Role | Active | Notes |\n|---|---|---|---|---|\n`;
  for (const member of sorted) {
    body += `| \`${member.id}\` | ${member.displayName} | ${member.role || 'contributor'} | ${member.active ? 'true' : 'false'} | ${member.notes || ''} |\n`;
  }
  write(MEMBERS_FILE, body);
}

export function findMember(id, members = loadMembers()) {
  return members.find(member => member.id === id);
}

export function readIdentity() {
  if (!exists(IDENTITY_FILE)) return null;
  try {
    const identity = JSON.parse(read(IDENTITY_FILE));
    if (!identity.member_id) return null;
    return { memberId: identity.member_id };
  } catch {
    return null;
  }
}

export function writeIdentity(memberId) {
  const full = resolve(IDENTITY_FILE);
  fs.mkdirSync(path.dirname(full), { recursive: true });
  fs.writeFileSync(full, `${JSON.stringify({ member_id: memberId }, null, 2)}\n`, 'utf8');
}

export function requireIdentity() {
  const identity = readIdentity();
  if (!identity) {
    console.error('TEAM IDENTITY FAIL: run npm run team:whoami -- <member-id> before starting a session');
    process.exit(1);
  }

  const member = findMember(identity.memberId);
  if (!member || !member.active) {
    console.error(`TEAM IDENTITY FAIL: ${identity.memberId} is not an active member in ${MEMBERS_FILE}`);
    process.exit(1);
  }

  return { identity, member };
}
