// Clueproof launch film: one command from source to the delivered files.
//   node tools/render.mjs
// 1. tools/build.mjs (voice clips from ../vo, music ducking, captions, ../clueproof-launch.srt)
// 2. HyperFrames render (1920 x 1080, 30 fps, H.264 + AAC)
// 3. loudness: measured with ffmpeg, then one gain to -16 LUFS integrated and a peak limiter at -1.7 dBFS
// 4. ../poster.jpg (1280 x 720) from the reveal frame
import { execFileSync, spawnSync } from "node:child_process";
import fs from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";

const root = path.resolve(path.dirname(fileURLToPath(import.meta.url)), "..");
const out = path.resolve(root, "..");
const raw = path.join(root, "renders", "clueproof-raw.mp4");
const final = path.join(out, "clueproof-launch.mp4");
const poster = path.join(out, "poster.jpg");
const POSTER_AT = process.env.POSTER_AT || "40.2";
const run = (cmd, args, opts = {}) => {
  console.log("> " + [cmd, ...args].join(" "));
  const r = spawnSync(cmd, args, { stdio: "inherit", cwd: root, ...opts });
  if (r.status !== 0) throw new Error(`${cmd} failed (${r.status})`);
};

run("node", ["tools/build.mjs"]);
fs.mkdirSync(path.dirname(raw), { recursive: true });
if (!process.env.SKIP_RENDER) run("npx", ["--yes", "hyperframes@0.9.3", "render", "--crf", "19", "--skill=hyperframes", "-o", JSON.stringify(raw)], { shell: true });

// loudness: measure, then one gain and a limiter (keeps the music's dynamics, no pumping)
const m = spawnSync("ffmpeg", ["-hide_banner", "-i", raw, "-af", "loudnorm=I=-16:TP=-1.5:LRA=11:print_format=json", "-f", "null", "-"], { encoding: "utf8" });
const j = JSON.parse(m.stderr.slice(m.stderr.lastIndexOf("{"), m.stderr.lastIndexOf("}") + 1));
const gain = -16 - Number(j.input_i);
console.log(`measured ${j.input_i} LUFS, true peak ${j.input_tp} dBTP: applying ${gain.toFixed(2)} dB`);
const af = `aresample=192000,volume=${gain.toFixed(2)}dB,alimiter=limit=0.82:attack=4:release=60:level=false,aresample=48000`;
run("ffmpeg", ["-y", "-hide_banner", "-loglevel", "error", "-i", raw, "-c:v", "copy", "-af", af, "-c:a", "aac", "-b:a", "192k", "-movflags", "+faststart", final]);
run("ffmpeg", ["-y", "-hide_banner", "-loglevel", "error", "-ss", POSTER_AT, "-i", final, "-frames:v", "1", "-vf", "scale=1280:720:flags=lanczos", "-q:v", "2", poster]);

const check = spawnSync("ffmpeg", ["-hide_banner", "-i", final, "-af", "ebur128=peak=true", "-f", "null", "-"], { encoding: "utf8" }).stderr;
const summary = check.slice(check.lastIndexOf("Summary:"));
console.log(summary);
console.log(`wrote ${final} (${(fs.statSync(final).size / 1048576).toFixed(1)} MB) and ${poster}`);
