# Review: Clueproof launch film

## Creative calls

- Followed `script.md` beat for beat (the person's script), so no alternative storylines were built. The device is the Stranger's File as a case file on a dark desk; the product half moves to a light UI world so the turn from "the stranger's view" to "Clueproof's view" is felt as a change of world, not only of copy.
- One carrier runs through the film: the lens. It reads the contact sheet (L3), survives the snap to black (L5/L6), becomes the mark (L6), reads the conveyor (L7), shrinks into the NAS power light (L8); at the end the "0" of "0 of 8" turns back into the mark.
- Reveal timed to the music: the track's drop at 0:42 lands on film 0:36 through one 4-bar cut; the black snap sits on the track's own silence at 0:35.
- Wordmark set as "Clueproof" (title case, as in the README and site), not all caps.
- Counts on screen and in narration L10 follow the Skill's own answer (6 / 4 / 2), not the earlier script draft (5 / 4 / 3). The house-number position reads "top center" (the photo and `manifest.json`), not "top right" from the answer-format example.
- Captions are off in L4, L6 and L16, where large type on screen already says the line; the `.srt` keeps all 16 lines.

## Measured

- `hyperframes check`: 0 lint errors, 0 runtime errors, contrast pass. Layout findings fixed (markers under the close-ups, transient overlaps during the L11 takeover marked as intended occlusion).
- Kept craft warnings, on purpose: the status lines in the chat (L9, L13) and the after-fix line (L12) are on screen for less than their full reading time. They are product output that the caption and the next beat carry; the viewer needs their shape, not every word.
- Audio, measured on `clueproof-launch.mp4` with FFmpeg `ebur128`: -16.1 LUFS integrated, true peak -1.2 dBTP, LRA about 8 LU. The envelope shows silence from 0.4 to 4.0 s (cold open), the music dip at 35.0 s and the hits at 36.0 s and 118.0 s. Nobody listened to it: the edit points were chosen on the track's beat grid and energy envelope, not by ear. The page-slam impacts were lowered after the first render measured -7 dBFS RMS around 0:32.
- File: 1920 x 1080, 30 fps, H.264 High + AAC LC 48 kHz stereo, 131.0 s, 31.3 MB.

## Looked at

Contact sheets at 0, 0.4, 3, 5.6, 6, 7, 9, 12, 13.5, 15.2, 17.4, 19.6, 21.5, 23.5, 26, 27.25, 28.5, 29.8, 31, 33.4, 34.3, 35.2, 35.5, 36.15, 36.5, 37.6, 39.5, 41.3, 42.8, 43, 44.5, 45.5, 47.6, 47.9, 48.6, 49, 50, 51, 54, 55.5, 56.5, 57.7, 58.25, 59.5, 62, 63.5, 64.6, 66, 70, 72.2, 72.4, 74.5, 76, 77.25, 79.8, 81.2, 83.5, 85.2, 86.4, 88.2, 88.6, 90.5, 92.8, 93.3, 95, 98, 100.35, 100.7, 101, 104, 108, 111, 114.5, 116.5, 117.2, 117.45, 117.6, 117.8, 118.4, 120.5, 123, 127 s; then frames decoded from the final MP4.

## Weakest shots and what I would do with more time

- L9 opens on a mostly empty chat window for about 1.5 s; the real NAS recording (Slot A) will fix it.
- The "0 to mark" hand-off at 1:57 crossfades a heavy glyph into a thin ring; a true morph (an SVG outline of the 0 tweening its stroke) would read cleaner.
- Close-up S05 frames a small plaque; a slow push into the plaque would make the box read faster.

## Warnings kept

- `duplicate_media_discovery_risk` (lint): the desk scene shows the same photos twice on purpose (the sheet and the lens's magnified copy).
