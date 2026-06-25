import { findMember, loadMembers, readIdentity, writeIdentity } from './team-utils.mjs';

const [rawId] = process.argv.slice(2);

if (!rawId) {
  const identity = readIdentity();
  if (!identity) {
    console.log('No local team identity set. Run: npm run team:whoami -- <member-id>');
    process.exit(0);
  }
  console.log(`current identity: ${identity.memberId}`);
  process.exit(0);
}

const memberId = rawId.trim();
const member = findMember(memberId, loadMembers());

if (!member) {
  console.error(`TEAM WHOAMI FAIL: ${memberId} is not registered. Run: npm run team:register -- ${memberId} "Display Name"`);
  process.exit(1);
}

if (!member.active) {
  console.error(`TEAM WHOAMI FAIL: ${memberId} is not active`);
  process.exit(1);
}

writeIdentity(memberId);
console.log(`current identity: ${memberId}`);
