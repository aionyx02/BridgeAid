import fs from 'node:fs';
import path from 'node:path';

export const ROOT = process.cwd();
export const DOCS = path.join(ROOT, 'docs');

export function toPosixPath(file) {
  return file.replaceAll('\\', '/');
}

export function resolve(file) {
  return path.join(ROOT, ...toPosixPath(file).split('/'));
}

export function read(file) {
  return fs.readFileSync(resolve(file), 'utf8');
}

export function write(file, content) {
  const full = resolve(file);
  fs.mkdirSync(path.dirname(full), { recursive: true });
  fs.writeFileSync(full, content, 'utf8');
}

export function writeIfChanged(file, content) {
  if (exists(file) && read(file) === content) return false;
  write(file, content);
  return true;
}

export function exists(file) {
  return fs.existsSync(resolve(file));
}

export function walk(dir, predicate = () => true) {
  const base = resolve(dir);
  if (!fs.existsSync(base)) return [];
  const out = [];
  for (const entry of fs.readdirSync(base, { withFileTypes: true })) {
    const rel = toPosixPath(path.join(dir, entry.name));
    if (entry.isDirectory()) out.push(...walk(rel, predicate));
    else if (predicate(rel)) out.push(rel);
  }
  return out;
}

export function parseFrontmatter(content) {
  if (!content.startsWith('---\n')) return null;
  const end = content.indexOf('\n---', 4);
  if (end === -1) return null;
  const raw = content.slice(4, end).trim();
  const data = {};
  for (const line of raw.split('\n')) {
    const m = line.match(/^([A-Za-z0-9_-]+):\s*(.*)$/);
    if (m) data[m[1]] = m[2].replace(/^['"]|['"]$/g, '');
  }
  return data;
}

export function today() {
  return new Date().toISOString().slice(0, 10);
}

export function replaceSection(content, marker, replacement) {
  if (content.includes(marker)) return content.slice(0, content.indexOf(marker)) + replacement;
  const prefix = content.endsWith('\n') ? content : `${content}\n`;
  return `${prefix}\n${replacement}`;
}

export function writeGeneratedFile(file, build) {
  if (exists(file)) {
    const current = read(file);
    const currentUpdated = parseFrontmatter(current)?.updated;
    if (currentUpdated && build(currentUpdated) === current) return false;
  }
  return writeIfChanged(file, build(today()));
}
