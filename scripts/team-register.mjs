import { loadMembers, normalizeMemberId, writeMembers } from './team-utils.mjs';

const [rawId, rawDisplayName, rawRole] = process.argv.slice(2);

if (!rawId || !rawDisplayName) {
  console.error('Usage: npm run team:register -- <member-id> "Display Name" [role]');
  process.exit(1);
}

const id = normalizeMemberId(rawId);
if (!id) {
  console.error('TEAM REGISTER FAIL: member id must contain letters, numbers, underscores, or hyphens');
  process.exit(1);
}

const members = loadMembers();
const existing = members.find(member => member.id === id);

if (existing) {
  existing.displayName = rawDisplayName;
  existing.role = rawRole || existing.role || 'contributor';
  existing.active = true;
} else {
  members.push({
    id,
    displayName: rawDisplayName,
    role: rawRole || 'contributor',
    active: true,
    notes: ''
  });
}

writeMembers(members);
console.log(`${existing ? 'updated' : 'registered'} ${id}`);
