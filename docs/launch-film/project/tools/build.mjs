// Clueproof launch film: build step.
// Reads tools/narration.json, looks for the ElevenLabs clips in ../vo/L01.mp3 .. L16.mp3,
// and regenerates three things so they always agree:
//   1. the audio block in index.html (music edit, ducking under any voice clip, sound effects, voice clips)
//   2. compositions/captions.html (kinetic captions, timed to the real clips when they exist)
//   3. ../clueproof-launch.srt (English subtitles)
// Run from the project folder:  node tools/build.mjs
import fs from "node:fs";
import path from "node:path";
import { execFileSync } from "node:child_process";
import { fileURLToPath } from "node:url";

const here = path.dirname(fileURLToPath(import.meta.url));
const root = path.resolve(here, "..");
const voSrcDir = path.resolve(root, "..", "vo");
const voDstDir = path.join(root, "assets", "vo");
const data = JSON.parse(fs.readFileSync(path.join(here, "narration.json"), "utf8"));

// Overall level of the music bed (1 = as mastered). Tuned so the music-only cut measures about -16 LUFS.
const MUSIC_GAIN = Number(process.env.MUSIC_GAIN || 1.0);
const DUCK = Math.pow(10, -8 / 20); // -8 dB under speech
const VO_GAIN = Number(process.env.VO_GAIN || 1.0);

function probe(file) {
  try {
    const out = execFileSync("ffprobe", ["-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", file], { encoding: "utf8" });
    const d = parseFloat(out.trim());
    return Number.isFinite(d) ? d : null;
  } catch {
    return null;
  }
}

// ---------- voice clips ----------
fs.mkdirSync(voDstDir, { recursive: true });
for (const f of fs.readdirSync(voDstDir)) if (/^L\d\d\.(mp3|wav)$/i.test(f)) fs.unlinkSync(path.join(voDstDir, f));
const vo = {};
for (const line of data.lines) {
  for (const ext of ["mp3", "wav"]) {
    const src = path.join(voSrcDir, `${line.id}.${ext}`);
    if (fs.existsSync(src)) {
      const dst = path.join(voDstDir, `${line.id}.${ext}`);
      fs.copyFileSync(src, dst);
      const dur = probe(dst);
      vo[line.id] = { file: `assets/vo/${line.id}.${ext}`, dur: dur ?? line.target };
      break;
    }
  }
}
const voCount = Object.keys(vo).length;

// ---------- word timing model ----------
const LEAD = 0.1, TAIL = 0.12, BREAK = 0.42, ELLIPSIS = 0.35, STOP = 0.22, COMMA = 0.1;
function timeLine(line) {
  const dur = vo[line.id]?.dur ?? line.target;
  const raw = line.text.split(/\s+/).filter(Boolean);
  const items = [];
  for (const tok of raw) {
    if (tok === "|") { items.push({ pause: BREAK }); continue; }
    const letters = tok.replace(/[^A-Za-z0-9']/g, "").length;
    items.push({ word: tok, w: Math.max(3, letters + 2) });
    if (/\.\.\.$/.test(tok)) items.push({ pause: ELLIPSIS, soft: true });
    else if (/[.?!]$/.test(tok)) items.push({ pause: STOP, soft: true });
    else if (/[,:]$/.test(tok)) items.push({ pause: COMMA, soft: true });
  }
  while (items.length && items[items.length - 1].pause) items.pop();
  const pauses = items.filter((i) => i.pause).reduce((a, i) => a + i.pause, 0);
  const weights = items.filter((i) => i.word).reduce((a, i) => a + i.w, 0);
  let speak = dur - LEAD - TAIL - pauses;
  let pauseScale = 1;
  if (speak < weights * 0.045) { pauseScale = Math.max(0.2, (dur - LEAD - TAIL - weights * 0.045) / pauses); speak = weights * 0.045; }
  const perW = speak / weights;
  let t = line.start + LEAD;
  const words = [];
  for (const it of items) {
    if (it.pause) { t += it.pause * pauseScale; if (words.length) words[words.length - 1].brk = it.soft ? "soft" : "hard"; continue; }
    const d = it.w * perW;
    words.push({ text: it.word, start: t, end: t + d });
    t += d;
  }
  return words;
}

function groupWords(words) {
  const groups = [];
  let cur = [];
  for (const w of words) {
    cur.push(w);
    const sentence = /(\.\.\.|[.?!])$/.test(w.text);
    const clause = /[,:]$/.test(w.text) && cur.length >= 3;
    if (sentence || clause || w.brk === "hard" || cur.length >= 6) { groups.push(cur); cur = []; }
  }
  if (cur.length) groups.push(cur);
  return groups;
}

const allGroups = [];
const srt = [];
for (const line of data.lines) {
  const words = timeLine(line);
  const groups = groupWords(words);
  // subtitles: one cue per sentence-ish group, merged to at most ~42 chars per line, two lines per cue
  let cue = [];
  const flush = () => {
    if (!cue.length) return;
    srt.push({ start: cue[0][0].start - 0.05, end: Math.min(cue[cue.length - 1].at(-1).end + 0.6, line.end - 0.04), text: cue.map((g) => g.map((w) => w.text).join(" ")).join(" ") });
    cue = [];
  };
  for (const g of groups) {
    const len = cue.flat().map((w) => w.text).join(" ").length + g.map((w) => w.text).join(" ").length;
    if (cue.length && len > 80) flush();
    cue.push(g);
  }
  flush();
  if (line.captions === false) continue;
  const light = line.start >= data.lightWorld[0] && line.start < data.lightWorld[1];
  for (const g of groups) allGroups.push({ line: line.id, words: g, light, beatEnd: line.end });
}
if (process.env.CAPTIONS === "off") allGroups.length = 0;
// group windows
for (const g of allGroups) g.start = Math.max(0.1, g.words[0].start - 0.12);
for (let i = 0; i < allGroups.length; i++) {
  const g = allGroups[i];
  const next = allGroups[i + 1];
  let end = g.words.at(-1).end + 0.7;
  const minEnd = g.start + 0.5 + 0.3 * g.words.length;
  end = Math.max(end, Math.min(minEnd, g.beatEnd - 0.05));
  if (next) end = Math.min(end, next.words[0].start - 0.16);
  end = Math.min(end, g.beatEnd - 0.04);
  g.end = Math.max(end, g.words.at(-1).end + 0.12);
  if (next) g.end = Math.min(g.end, next.start - 0.02);
}
// SRT cues must not overlap
srt.sort((a, b) => a.start - b.start);
for (let i = 0; i < srt.length - 1; i++) if (srt[i].end > srt[i + 1].start - 0.05) srt[i].end = srt[i + 1].start - 0.05;

// ---------- captions.html ----------
const esc = (s) => s.replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;");
const r3 = (x) => Math.round(x * 1000) / 1000;
let wi = 0;
const capMarkup = allGroups
  .map((g, gi) => {
    const spans = g.words.map((w) => { w.id = `cap-w${wi++}`; return `<span class="cw" id="${w.id}">${esc(w.text)}</span>`; }).join(" ");
    return `    <div class="cap-group${g.light ? " on-light" : ""}" id="cap-g${gi}" data-line="${g.line}"><span class="cap-line">${spans}</span></div>`;
  })
  .join("\n");
const capData = allGroups.map((g, gi) => ({ id: `cap-g${gi}`, s: r3(g.start), e: r3(g.end), w: g.words.map((w) => [w.id, r3(w.start)]) }));
const captionsHtml = `<template>
  <!-- Generated by tools/build.mjs from tools/narration.json. Edit the text there, then run: node tools/build.mjs -->
  <style>
    #root { position: absolute; inset: 0; pointer-events: none; }
    #root .cap-group { position: absolute; left: 0; top: 0; width: 1920px; height: 1080px; opacity: 0; }
    #root .cap-line { position: absolute; left: 160px; right: 160px; top: 902px; text-align: center; font-family: "Inter", sans-serif; font-weight: 600; font-size: 46px; line-height: 1.2; letter-spacing: -0.012em; color: #EEEDE7; text-shadow: 0 2px 14px rgba(5, 8, 7, 0.55); }
    #root .on-light .cap-line { color: #121715; text-shadow: none; }
    #root .cw { opacity: 0.22; }
  </style>
  <div id="root" data-composition-id="captions" data-width="1920" data-height="1080" data-layout-allow-caption-zone>
${capMarkup}
  </div>
  <script>
    (function () {
      const tl = gsap.timeline({ paused: true });
      const groups = ${JSON.stringify(capData)};
      for (const g of groups) {
        const el = "#" + g.id;
        gsap.set(el, { opacity: 0, visibility: "hidden" });
        tl.set(el, { visibility: "visible" }, g.s);
        tl.fromTo(el, { opacity: 0, filter: "blur(6px)" }, { opacity: 1, filter: "blur(0px)", duration: 0.18, ease: "power3.out" }, g.s);
        for (const [id, t] of g.w) {
          tl.to("#" + id, { opacity: 1, duration: 0.14, ease: "power1.out" }, t);
        }
        tl.to(el, { opacity: 0, filter: "blur(4px)", duration: 0.16, ease: "power2.in" }, g.e - 0.16);
        tl.set(el, { opacity: 0, visibility: "hidden" }, g.e);
      }
      tl.set({}, {}, 131);
      window.__timelines["captions"] = tl;
    })();
  </script>
</template>
`;
fs.writeFileSync(path.join(root, "compositions", "captions.html"), captionsHtml);

// ---------- SRT ----------
const ts = (x) => {
  const ms = Math.max(0, Math.round(x * 1000));
  const h = Math.floor(ms / 3600000), m = Math.floor((ms % 3600000) / 60000), s = Math.floor((ms % 60000) / 1000), f = ms % 1000;
  return `${String(h).padStart(2, "0")}:${String(m).padStart(2, "0")}:${String(s).padStart(2, "0")},${String(f).padStart(3, "0")}`;
};
function wrap(text) {
  if (text.length <= 42) return text;
  const words = text.split(" ");
  let best = null;
  for (let i = 1; i < words.length; i++) {
    const a = words.slice(0, i).join(" "), b = words.slice(i).join(" ");
    const score = Math.max(a.length, b.length) + (/[.,:?!]$/.test(a) ? -10 : 0) + (Math.max(a.length, b.length) > 42 ? 100 : 0);
    if (!best || score < best.score) best = { score, t: `${a}\n${b}` };
  }
  return best.t;
}
const srtText = srt.map((c, i) => `${i + 1}\n${ts(c.start)} --> ${ts(c.end)}\n${wrap(c.text)}\n`).join("\n");
fs.writeFileSync(path.resolve(root, "..", "clueproof-launch.srt"), srtText);

// ---------- music: edit and level ----------
// Track: "Impact Allegretto" by Kevin MacLeod. Music starts at track 2.0 s. Two edits on bar lines:
//   m1 film 4.0-20.0  = track 2.0-18.0
//   m2 film 20.0-104.6 = track 26.0-110.6   (skips 8 s = 4 bars, so the track's drop at 42.0 s lands on film 36.0)
//   m3 film 104.0-131 = track 154.0-181.0  (the final section: lift at 106, hits at 114 and 118, tail)
const G = [
  [4.0, 0.5], [13.0, 0.5], [20.0, 0.56], [34.9, 0.66], [36.0, 0.9], [40.5, 0.9], [42.0, 0.74], [57.5, 0.74], [58.5, 0.64],
  [92.5, 0.64], [93.5, 0.56], [100.0, 0.62], [104.0, 0.66], [104.3, 0.74], [117.5, 0.74], [118.0, 0.86], [129.0, 0.86], [131.0, 0.0],
];
const lerp = (pts, t) => {
  if (t <= pts[0][0]) return pts[0][1];
  for (let i = 1; i < pts.length; i++) if (t <= pts[i][0]) { const [t0, v0] = pts[i - 1], [t1, v1] = pts[i]; return v0 + ((v1 - v0) * (t - t0)) / (t1 - t0); }
  return pts.at(-1)[1];
};
const duckWins = data.lines.filter((l) => vo[l.id]).map((l) => [l.start - 0.12, l.start + vo[l.id].dur + 0.25]);
const duckAt = (t) => {
  let g = 1;
  for (const [a, b] of duckWins) {
    const r = 0.15;
    let k = 1;
    if (t >= a && t <= b) k = DUCK;
    else if (t > a - r && t < a) k = 1 - ((1 - DUCK) * (t - (a - r))) / r;
    else if (t > b && t < b + r) k = DUCK + ((1 - DUCK) * (t - b)) / r;
    g = Math.min(g, k);
  }
  return g;
};
function lane(filmStart, filmEnd, extra) {
  const times = new Set([filmStart, filmEnd]);
  for (const [t] of G) if (t > filmStart && t < filmEnd) times.add(t);
  for (const [a, b] of duckWins) for (const t of [a - 0.15, a, b, b + 0.15]) if (t > filmStart && t < filmEnd) times.add(r3(t));
  for (const [t] of extra) times.add(t);
  const pts = [...times].sort((a, b) => a - b).map((t) => {
    let v = lerp(G, t) * duckAt(t) * MUSIC_GAIN;
    for (const [et, ev] of extra) if (Math.abs(et - t) < 1e-6) v = ev === null ? v : ev;
    return { t: r3(t - filmStart), v: r3(v) };
  });
  return JSON.stringify({ version: 1, lanes: [{ target: "volume", points: pts }] }).replace(/"/g, "&quot;");
}
const m1 = lane(4.0, 20.03, []);
const m2Pts = [[104.0, null], [104.6, 0]];
const m2 = lane(19.99, 104.6, m2Pts);
const m3 = lane(104.0, 131.0, [[104.0, 0]]);

const sfx = [
  ["sfx-shutter", "click", 0.03, 0.9],
  ["sfx-deal", "whoosh", 5.05, 0.45],
  ["sfx-slam1", "impact-bass-1", 31.38, 0.2],
  ["sfx-slam2", "impact-bass-2", 32.38, 0.18],
  ["sfx-slam3", "impact-bass-1", 33.38, 0.2],
  ["sfx-type1", "typing", 36.3, 0.5],
  ["sfx-zoom", "whoosh-short", 57.45, 0.5],
  ["sfx-type2", "typing", 58.85, 0.42],
  ["sfx-send1", "click-soft", 60.4, 0.7],
  ["sfx-yes", "click", 86.6, 0.75],
  ["sfx-stamp", "impact-bass-2", 88.7, 0.14],
  ["sfx-type3", "typing", 93.85, 0.42],
  ["sfx-type4", "typing", 95.0, 0.36],
  ["sfx-send2", "click-soft", 96.25, 0.7],
];
const lines = [];
lines.push(`<!-- AUDIO:BEGIN (generated by tools/build.mjs: ${voCount} voice clip${voCount === 1 ? "" : "s"} found${voCount ? ", music ducked 8 dB under speech" : ", music-only cut"}) -->`);
lines.push(`      <audio id="music-a" class="clip" data-timeline-role="music" src="audio/impact-allegretto.mp3" data-start="4" data-media-start="2" data-duration="16.03" data-track-index="20" data-volume="1" data-automation="${m1}"></audio>`);
lines.push(`      <audio id="music-b" class="clip" src="audio/impact-allegretto.mp3" data-start="19.99" data-media-start="25.99" data-duration="84.61" data-track-index="21" data-volume="1" data-automation="${m2}"></audio>`);
lines.push(`      <audio id="music-c" class="clip" src="audio/impact-allegretto.mp3" data-start="104" data-media-start="154" data-duration="27" data-track-index="22" data-volume="1" data-automation="${m3}"></audio>`);
let ti = 30;
for (const [id, file, t, v] of sfx) lines.push(`      <audio id="${id}" class="clip" src="assets/sfx/${file}.mp3" data-start="${t}" data-track-index="${ti++}" data-volume="${v}"></audio>`);
for (const l of data.lines) if (vo[l.id]) lines.push(`      <audio id="vo-${l.id}" class="clip" src="${vo[l.id].file}" data-start="${l.start}" data-duration="${r3(vo[l.id].dur)}" data-track-index="10" data-volume="${VO_GAIN}"></audio>`);
// NAS screen recordings for the two slots (script.md L9 and L13): ../nas/slot-a.mp4 and ../nas/slot-b.mp4
const SLOTS = [
  { id: "slot-a", start: 58.0, dur: 5.0, from: Number(process.env.SLOT_A_FROM || 0) },
  { id: "slot-b", start: 93.0, dur: 7.0, from: Number(process.env.SLOT_B_FROM || 0) },
];
const nasDst = path.join(root, "assets", "nas");
for (const sl of SLOTS) {
  const src = path.resolve(root, "..", "nas", `${sl.id}.mp4`);
  if (!fs.existsSync(src)) continue;
  fs.mkdirSync(nasDst, { recursive: true });
  fs.copyFileSync(src, path.join(nasDst, `${sl.id}.mp4`));
  lines.push(`      <video id="${sl.id}" class="clip" src="assets/nas/${sl.id}.mp4" data-start="${sl.start}" data-duration="${sl.dur}" data-media-start="${sl.from}" data-track-index="3" muted playsinline style="position: absolute; left: 0; top: 0; width: 1920px; height: 1080px; object-fit: contain; background: #e9ece8; z-index: 6"></video>`);
  console.log(`NAS recording placed: ${sl.id} at ${sl.start} s for ${sl.dur} s (from ${sl.from} s into the file)`);
}
lines.push(`      <!-- AUDIO:END -->`);
const indexPath = path.join(root, "index.html");
let index = fs.readFileSync(indexPath, "utf8");
index = index.replace(/<!-- AUDIO:BEGIN[\s\S]*?<!-- AUDIO:END -->/, lines.join("\n"));
fs.writeFileSync(indexPath, index);

console.log(`voice clips: ${voCount}/16${voCount ? " (" + Object.keys(vo).join(", ") + ")" : ""}`);
console.log(`caption groups: ${allGroups.length}, srt cues: ${srt.length}`);
for (const l of data.lines) if (vo[l.id] && vo[l.id].dur > l.end - l.start) console.log(`WARNING ${l.id} is ${vo[l.id].dur.toFixed(2)} s, longer than its ${l.end - l.start} s beat`);
