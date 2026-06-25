import { exists, read } from './docs-utils.mjs';
import { findMember, loadMembers, readIdentity, MEMBERS_FILE } from './team-utils.mjs';

const members = loadMembers();
let failed = false;

if (!exists(MEMBERS_FILE)) {
  console.error(`TEAM FAIL: missing ${MEMBERS_FILE}`);
  failed = true;
}

if (!members.length) {
  console.error(`TEAM FAIL: ${MEMBERS_FILE} must register at least one active member`);
  failed = true;
}

const memberIds = new Set(members.map(member => member.id));
if (memberIds.size !== members.length) {
  console.error(`TEAM FAIL: duplicate member id in ${MEMBERS_FILE}`);
  failed = true;
}

for (const member of members) {
  if (!/^[a-z0-9_-]+$/.test(member.id)) {
    console.error(`TEAM MEMBER FAIL ${MEMBERS_FILE}: invalid id ${member.id}`);
    failed = true;
  }
}

const active = exists('docs/tasks/active.md') ? read('docs/tasks/active.md') : '';
const tasks = active.split(/^###\s+/m).slice(1);
for (const rawTask of tasks) {
  const title = rawTask.split('\n')[0].trim();
  const status = rawTask.match(/^- Status:\s*([^\n]+)/m)?.[1]?.trim();
  const owner = rawTask.match(/^- Owner:\s*([^\n]+)/m)?.[1]?.trim();
  if (!owner) {
    console.error(`TASK OWNER FAIL docs/tasks/active.md: ${title} missing Owner`);
    failed = true;
    continue;
  }
  if (!findMember(owner, members)) {
    console.error(`TASK OWNER FAIL docs/tasks/active.md: ${title} owner ${owner} is not registered`);
    failed = true;
  }
  if (status === 'doing' && owner === 'project') {
    console.error(`TASK OWNER FAIL docs/tasks/active.md: ${title} doing tasks must be owned by a real member, not project`);
    failed = true;
  }
}

if (process.env.TEAM_REQUIRE_IDENTITY === '1') {
  const identity = readIdentity();
  if (!identity) {
    console.error('TEAM IDENTITY FAIL: run npm run team:whoami -- <member-id> before starting a session');
    failed = true;
  } else {
    const member = findMember(identity.memberId, members);
    if (!member || !member.active) {
      console.error(`TEAM IDENTITY FAIL: ${identity.memberId} is not an active registered member`);
      failed = true;
    }
  }
}

if (!failed) console.log('team guard ok');
process.exit(failed ? 1 : 0);
