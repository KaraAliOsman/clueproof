# Clueproof launch film

A 2:11 product film for Clueproof (2:05 of story plus a 6 s credits roll), 1920 x 1080, 30 fps, H.264 + AAC. It follows `script.md` beat for beat: the cold open on one photo, the stranger's reading, the reveal at 0:36, three proof moments (the answer, the double reading, one yes), the Stranger's File, and the end card.

| File | What it is |
| --- | --- |
| `clueproof-launch.mp4` | The film: narration, music and burned-in English captions. |
| `clueproof-launch.srt` | English subtitles of the narration, timed to the spoken words. |
| `vo/` | The ElevenLabs take (`take-1.mp3`) and its cue sheet (`take-1.json`). |
| `poster.jpg` | 1280 x 720 poster frame (the reveal at 0:40). |
| `CREDITS.md` | Music, photo and sound credits with their licences. |
| `script.md`, `elevenlabs.md` | The shot list and the narration lines for ElevenLabs. |
| `project/` | The HyperFrames source: `index.html` (scenes, music, sound), `compositions/` (one file per scene), `tools/` (build and render scripts), `SPEC.md` (the look in numbers), `REVIEW.md` (the last review). |

## Re-render

Needs Node.js 22 or newer and FFmpeg (`ffmpeg` and `ffprobe` on the PATH). HyperFrames 0.9.3 and its Chrome are fetched by `npx` on the first run.

```bash
cd docs/launch-film/project
node tools/render.mjs
```

That one command:

1. runs `tools/build.mjs`, which reads `tools/narration.json`, looks for the voice clips, writes the audio block in `index.html`, the captions in `compositions/captions.html`, and `../clueproof-launch.srt`;
2. renders with `npx --yes hyperframes@0.9.3 render --crf 19` into `project/renders/clueproof-raw.mp4`;
3. normalises the mix to -16 LUFS integrated, about -2.5 dBTP (one measured gain and a peak limiter) into `../clueproof-launch.mp4`;
4. writes `../poster.jpg`.

On Windows, keep the repository in a short path (for example `C:\src\clueproof`): the renderer's temporary folders inside `project/.hyperframes/` fail when the full path passes 260 characters.

## The narration

The film uses one ElevenLabs take of all 16 lines, `vo/take-1.mp3`, and its cue sheet `vo/take-1.json`. The cue sheet lists 32 phrases: where each one sits in the take (cut on the take's own pauses, measured from the waveform), the film second it starts on and why (for example "A house number" as its red box draws, "Where you live" as that page fills), and the time of every word, measured with speech recognition and refined to the waveform. `build.mjs` cleans the take once (70 Hz high-pass, light de-essing, 2:1 compression), levels it to -18 LUFS with a -1.5 dBFS limiter, cuts the phrases with 12 ms and 40 ms fades, places them, ducks the music 10 dB under speech (one duck across phrases less than 0.9 s apart), and times the captions and the `.srt` to the real words. To move a phrase, change its `at` in `take-1.json` and render again; `DUCK_DB` and `VO_LUFS` set the balance.

In the three-line answer (1:02 to 1:12) and the Yes beat (1:26 to 1:32), the answer lines and the Keep private stamps were retimed by up to 1.25 s to land on the words that read them.

### Separate clips instead

1. Generate the 16 clips as described in `elevenlabs.md` and save them as `docs/launch-film/vo/L01.mp3` to `L16.mp3` (WAV also works).
2. Run the same command: `cd docs/launch-film/project && node tools/render.mjs`.

Remove `vo/take-1.json` first (the take wins). `build.mjs` then copies every clip it finds into `project/assets/vo/`, places each one at its beat's start (`tools/narration.json`), ducks the music (10 dB) from 0.12 s before each clip to 0.25 s after it, and re-times the captions and the `.srt` to the real clip lengths. Missing clips are simply skipped, so a partial set works. It prints a warning when a clip is longer than its beat; the fix is in `elevenlabs.md` (raise Speed to 1.0 rather than cutting words).

The burned-in captions stay on, as `script.md` asks. For a cut without them: `CAPTIONS=off node tools/render.mjs` (PowerShell: `$env:CAPTIONS="off"; node tools/render.mjs`). Music level under the voice: `MUSIC_GAIN` (default 1.0); voice level: `VO_GAIN` (default 1.0).

To preview and edit in the browser instead: `npx --yes hyperframes@0.9.3 preview` in `project/`.

## Slot A and Slot B: the NAS screen recordings

The two beats `script.md` reserves for real NAS footage use interface mock-ups for now, labelled "Interface mock-up" in the window header:

| Slot | Beat | Film time | Length | Shows |
| --- | --- | --- | --- | --- |
| A | L9 | 0:58.0 to 1:03.0 | 5.0 s | typing "Is this safe to post?" in the NAS AI assistant, and the first status line |
| B | L13 | 1:33.0 to 1:40.0 | 7.0 s | typing "What could a stranger find out about us?" and the first line of the answer |

To drop the recordings in:

1. Record the NAS screen at 1920 x 1080 (any aspect works; it is letterboxed on the light UI ground) and save the clips as `docs/launch-film/nas/slot-a.mp4` and `docs/launch-film/nas/slot-b.mp4`.
2. If the moment you want starts later in the file, give its offset in seconds: `SLOT_A_FROM=3.5 SLOT_B_FROM=12 node tools/render.mjs`.
3. Run `node tools/render.mjs`. `build.mjs` copies them to `project/assets/nas/` and places each one, muted, over its slot (above the mock-up, under the captions).

Keep each recording at least as long as its slot. The beats after each slot (the three-line answer and the Stranger's File) stay as built, so cut the recording on the moment the answer starts.

## Notes

- Numbers on screen come from the Skill's own example answers (`skill/clueproof/references/answer-format.md` and `strangers-file.md`): 6 of 12 ready to post, 4 give clues away, 2 need a fix; 5 of 8 pages, the two "Worst together" lines, pages closing to 0 of 8. Line L10 of the narration was updated to match ("Six photos are ready to post. Four give clues away. Two need a fix.").
- Clues are named, never shown: the license plates, the boarding-pass barcode, the postal code and the house number are pixelated in the film's photo copies, and the house number also gets an ink bar in the "never repeats what it found" beat.
- The music is a real, human-composed track: "Impact Allegretto" by Kevin MacLeod, CC BY 4.0 (see `CREDITS.md`).
