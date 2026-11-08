#!/usr/bin/env node
// Validate and package the Skill for submission.
//
//   node tools/build.mjs                 preflight + zip
//   node tools/build.mjs --kit <dir>     also run the official UGOS checker (uliya-skill-kit)
//   node tools/build.mjs --strict        fail on any official warning (require "static-pass")
//
// The official checker is NOT redistributed in this repo. Download the UGOS Skill
// Creation Tool from https://ai.ugreen.com/pages/hackathon-starter-kit and pass its
// folder with --kit (or set ULIYA_KIT).
//
// Zero dependencies: the ZIP writer below uses only node:zlib.

import { spawnSync } from "node:child_process";
import { existsSync, mkdirSync, readdirSync, readFileSync, statSync, writeFileSync } from "node:fs";
import path from "node:path";
import { crc32, deflateRawSync } from "node:zlib";
import { fileURLToPath } from "node:url";

const root = path.resolve(path.dirname(fileURLToPath(import.meta.url)), "..");
const skillParent = path.join(root, "skill");
const distDir = path.join(root, "dist");

const LIMITS = { fileBytes: 1024 * 1024, totalBytes: 10 * 1024 * 1024, files: 100 };

const args = process.argv.slice(2);
const strict = args.includes("--strict");
const kitIndex = args.indexOf("--kit");
const kitDir = kitIndex !== -1 ? args[kitIndex + 1] : process.env.ULIYA_KIT;

function fail(message) {
  console.error(`✗ ${message}`);
  process.exit(1);
}

function walk(dir, base = dir) {
  const out = [];
  for (const entry of readdirSync(dir, { withFileTypes: true }).sort((a, b) => a.name.localeCompare(b.name))) {
    const full = path.join(dir, entry.name);
    if (entry.isDirectory()) out.push(...walk(full, base));
    else out.push({ full, rel: path.relative(base, full).split(path.sep).join("/") });
  }
  return out;
}

// ---------------------------------------------------------------- locate skill
const candidates = readdirSync(skillParent, { withFileTypes: true }).filter((e) => e.isDirectory());
if (candidates.length !== 1) fail(`expected exactly one skill folder in skill/, found ${candidates.length}`);
const skillName = candidates[0].name;
const skillDir = path.join(skillParent, skillName);
console.log(`Skill: ${skillName}`);

// ---------------------------------------------------------------- preflight
const files = walk(skillDir);
const problems = [];
let total = 0;
for (const f of files) {
  const size = statSync(f.full).size;
  total += size;
  const allowed = f.rel === "SKILL.md" || (f.rel.startsWith("references/") && f.rel.endsWith(".md"));
  if (!allowed) problems.push(`unsupported file in package: ${f.rel}`);
  if (size > LIMITS.fileBytes) problems.push(`file over 1 MB: ${f.rel}`);
}
if (files.length > LIMITS.files) problems.push(`more than ${LIMITS.files} files`);
if (total > LIMITS.totalBytes) problems.push("package over 10 MB");

const skillSource = readFileSync(path.join(skillDir, "SKILL.md"), "utf8");
const fm = skillSource.match(/^---\r?\n([\s\S]*?)\r?\n---/);
if (!fm) problems.push("SKILL.md has no frontmatter");
else {
  const name = fm[1].match(/^name:\s*(.+)$/m)?.[1].trim();
  const description = fm[1].match(/^description:\s*(.+)$/m)?.[1].trim() ?? "";
  if (name !== skillName) problems.push(`frontmatter name "${name}" does not match folder "${skillName}"`);
  if (!/^[a-z0-9]+(?:-[a-z0-9]+)*$/.test(name ?? "") || name.length < 2 || name.length > 64) problems.push("invalid skill name");
  if ([...description].length > 1024) problems.push(`description is ${[...description].length} chars (max 1024)`);
}
const linked = new Set([...skillSource.matchAll(/\]\((references\/[A-Za-z0-9._/-]+\.md)/g)].map((m) => m[1]));
for (const f of files.filter((x) => x.rel.startsWith("references/"))) {
  if (!linked.has(f.rel)) problems.push(`reference not linked from SKILL.md: ${f.rel}`);
}
for (const link of linked) if (!existsSync(path.join(skillDir, link))) problems.push(`broken link in SKILL.md: ${link}`);

if (problems.length) fail(`preflight failed:\n  - ${problems.join("\n  - ")}`);
console.log(`✓ preflight: ${files.length} files, ${total} bytes, all Markdown, all references linked`);

// ---------------------------------------------------------------- official checker
if (kitDir) {
  const checker = path.join(kitDir, "scripts", "check-skill.mjs");
  if (!existsSync(checker)) fail(`official checker not found at ${checker}`);
  const run = spawnSync(process.execPath, [checker, skillDir], { encoding: "utf8" });
  if (run.status === 2) fail(`official checker could not run:\n${run.stderr}`);
  const result = JSON.parse(run.stdout);
  const { errors, warnings, info } = result.summary;
  console.log(`✓ official checker (catalog ${result.catalog.checkedVersion}): status=${result.status} errors=${errors} warnings=${warnings} info=${info}`);
  for (const d of result.diagnostics) console.log(`    [${d.severity}] ${d.code} ${d.file ?? ""}:${d.line ?? ""} ${d.message}`);
  if (result.status === "not-uploadable") fail("official checker reports not-uploadable");
  if (strict && result.status !== "static-pass") fail("strict mode requires static-pass (zero warnings)");
  mkdirSync(distDir, { recursive: true });
  writeFileSync(path.join(distDir, "check-result.json"), JSON.stringify(result, null, 2) + "\n");
} else {
  console.log("• official checker skipped (pass --kit <uliya-skill-kit folder> or set ULIYA_KIT)");
}

// ---------------------------------------------------------------- zip
function dosDateTime(date) {
  const time = (date.getHours() << 11) | (date.getMinutes() << 5) | Math.floor(date.getSeconds() / 2);
  const day = ((date.getFullYear() - 1980) << 9) | ((date.getMonth() + 1) << 5) | date.getDate();
  return { time, day };
}

function buildZip(entries) {
  const local = [];
  const central = [];
  let offset = 0;
  const { time, day } = dosDateTime(new Date(2026, 10, 15, 12, 0, 0)); // fixed stamp => reproducible zip
  for (const { name, data } of entries) {
    const nameBytes = Buffer.from(name, "utf8");
    const compressed = deflateRawSync(data, { level: 9 });
    const crc = crc32(data) >>> 0;
    const header = Buffer.alloc(30);
    header.writeUInt32LE(0x04034b50, 0);
    header.writeUInt16LE(20, 4);
    header.writeUInt16LE(0x0800, 6); // UTF-8 names
    header.writeUInt16LE(8, 8); // deflate
    header.writeUInt16LE(time, 10);
    header.writeUInt16LE(day, 12);
    header.writeUInt32LE(crc, 14);
    header.writeUInt32LE(compressed.length, 18);
    header.writeUInt32LE(data.length, 22);
    header.writeUInt16LE(nameBytes.length, 26);
    header.writeUInt16LE(0, 28);
    local.push(header, nameBytes, compressed);

    const dir = Buffer.alloc(46);
    dir.writeUInt32LE(0x02014b50, 0);
    dir.writeUInt16LE(20, 4);
    dir.writeUInt16LE(20, 6);
    dir.writeUInt16LE(0x0800, 8);
    dir.writeUInt16LE(8, 10);
    dir.writeUInt16LE(time, 12);
    dir.writeUInt16LE(day, 14);
    dir.writeUInt32LE(crc, 16);
    dir.writeUInt32LE(compressed.length, 20);
    dir.writeUInt32LE(data.length, 24);
    dir.writeUInt16LE(nameBytes.length, 28);
    dir.writeUInt32LE(offset, 42);
    central.push(dir, nameBytes);
    offset += header.length + nameBytes.length + compressed.length;
  }
  const centralBuf = Buffer.concat(central);
  const end = Buffer.alloc(22);
  end.writeUInt32LE(0x06054b50, 0);
  end.writeUInt16LE(entries.length, 8);
  end.writeUInt16LE(entries.length, 10);
  end.writeUInt32LE(centralBuf.length, 12);
  end.writeUInt32LE(offset, 16);
  return Buffer.concat([...local, centralBuf, end]);
}

const zip = buildZip(files.map((f) => ({ name: `${skillName}/${f.rel}`, data: readFileSync(f.full) })));
if (zip.length > LIMITS.totalBytes) fail("zip over 10 MB");
mkdirSync(distDir, { recursive: true });
const zipPath = path.join(distDir, `${skillName}.zip`);
writeFileSync(zipPath, zip);
console.log(`✓ packaged ${path.relative(root, zipPath)} (${zip.length} bytes, ${files.length} files)`);
