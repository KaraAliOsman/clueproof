# Clueproof launch film: spec

GOAL:    A viewer who shares family photos understands in one viewing that a stranger can put
         harmless clues together, and that Clueproof finds them first, on the NAS, with one yes.
OUTPUT:  HyperFrames, 1920 x 1080, 30 fps, H.264 + AAC, under 60 MB.
TIME:    131 s x 30 = 3930 frames. Music 120.4 BPM (15 frames a beat, a bar every 2 s).
         Beats follow docs/launch-film/script.md exactly (L1 0:00 ... L16 1:57); credits 2:04.6 to 2:11.

## Look (the Stranger's File, then the product)

- Worlds, in order: the DESK (case file), BLACK (reveal), the NAS BLUEPRINT, the UI (light), back to DESK (end card).
- DESK ground #0D1211 with a key light from upper left (radial #19211F at 28% 18%, 1500 px) and 3.5% fibre grain. Never a void: the hero fills 40%+ of the frame.
- Ink on dark #EEEDE7; muted #98A29E. Evidence red #E2383F (thread, markers, clue boxes: the stranger's colour). Clueproof mint #5ED6A5 (only after the reveal: the mark's bar, "first", the boundary, the URL).
- UI world ground #E9ECE8, cards #FFFFFF, ink #121715, muted #5B6662, mint-deep #12885C, red #CF2E35, amber #A86F00. Verdict colours are product status colours: Clear mint, Fix first amber, Keep private red.
- Type: Inter 900 for hero words (110-180 px, tracking -0.035em), Inter 700/600 for UI and captions, JetBrains Mono 700 for exhibit codes (30 px, +0.06em). Nothing under 28 px.
- Prints: real photos with a 24 px ivory border (#F2EFE7, scales with the print), contact shadow 0 2 3 / 0 30 60 -18 at 0.7. Rotations from a fixed table (-1.9 to 1.8 deg).
- Redaction: Clueproof names the clue, never the value. Plates, barcode, postal code and house number are pixelated in the photo files (assets/photos) and the house number also gets a solid ink bar in L11.

## Objects

- Evidence marker: red disc 56 px, white Inter 900 numeral, 2 px ivory rim, drop shadow; numbered in the order the lens finds it (S01=1, S08=2, S07=3, S06=4, S05=5, S10=6, S11=7).
- The lens: ivory ring (SVG r 42 of 100, stroke 2.4), 400 px box, magnifies the sheet 1.9x inside it.
- The mark: the same ring, stroke 7, with a mint redaction bar through its centre (the lens that hides the value).
- The red thread: 4 px #D6262F with a 6 px dark shadow, sagging 36 px between pins.
- File pages: paper #EDE9DF cards 600 x 400, header in mono, title Inter 900 64 px.
- NAS: line drawing in ivory 3 px, 4 drive trays, the mark's ring becomes its power light; the boundary is a house outline in mint.
- Chat: white window 900 x 750 radius 28 at x 130, y 120; header with the mark; input field; the album panel at x 1100 with the 12 thumbnails (3 x 4).
- Stranger's File: one white file 1680 x 760; counter "n of 8" Inter 900 200 px; eight page rows with index tabs.

## Motion

- Arrivals expo.out / power4.out 0.5-0.7 s; camera and morphs power2.inOut / power3.inOut 0.6-1.1 s; exits power3.in, 40-50% shorter.
- Words: blur 6 px -> 0 and opacity, 0.15 s, 0.07 s apart. Landed titles hold dead still.
- The conveyor in L7 runs linear at 520 px/s (constant speed is the point).
- Cuts: hard cuts only inside L4; between beats the carrier is an object: print -> sheet, lens -> mark -> NAS light, NAS -> UI (zoom through + flood), chat -> file (window grows), "0" -> mark (match + flood).

## Shots (film seconds)

| t | hero move | reads | sound |
| --- | --- | --- | --- |
| 0.0-5.0 | aperture opens on S01 as a print, push 1.00 -> 1.05 | "This is a photo." | shutter click on frame 1, silence |
| 4.0 | | | music enters on its downbeat (track 2.0 s) |
| 5.0-13.0 | S01 shrinks into a 4 x 3 contact sheet while 11 prints deal in | "Summer 2025 · 12 photos", pill Shared · family -> anyone with the link | whoosh on the deal |
| 13.0-20.0 | light drops 62%; the lens sweeps an S path; 7 markers pop | lens magnifies the real prints | |
| 20.0-27.0 | three hard cuts: S05, S08, S07 as large prints; red box draws; label | House number / School crest / Boarding pass (type only) | |
| 27.0-35.0 | zoom out to the sheet; one red thread joins the 7 markers; 3 file pages slam | Where you live / Your children / When you're away | 3 impacts |
| 35.0 | snap to black, only the lens ring | | music gap |
| 36.0-41.0 | ring -> mark; Clueproof types in; tagline per word | Every photo leaves clues. Clueproof finds them first. | music hit at 36.0, typing |
| 41.0-48.0 | ring grows to a lens; 5 photos pass through it and come out with clue boxes or a check | License plate, Address label, Keys, House number, No clues | |
| 48.0-58.0 | ring shrinks into the NAS power light; NAS draws; photos fly into trays; a house boundary draws; outward lines stop at it | UGREEN AI NAS · No external calls. | |
| 58.0-63.0 | zoom through into the light UI; question types; status line | Is this safe to post? | typing, send click |
| 63.0-72.0 | three-line answer builds; grid recolours by verdict | 6 of 12 / 4 give clues away / 2 need a fix / Nothing was skipped. | |
| 72.0-85.0 | S05 opens into Text reading / Visual reading; S12 gets two ticks before Clear; S05 gets an ink bar | House number · top center | |
| 85.0-93.0 | cursor clicks Yes; 6 thumbs fly into Ready to share; 4 stamped Keep private | the after-fix line | click, stamp |
| 93.0-100.0 | clean chat; second question types | What could a stranger find out about us? | typing |
| 100.0-112.0 | the window grows into the Stranger's File; pages fill; counter 0 -> 5 | 5 of 8 pages · Worst together | music lift at 104 |
| 112.0-117.0 | pages close one by one; counter 5 -> 0 | Clean copy · 0 of 8 | hit at 114 |
| 117.0-118.0 | the "0" leaves the counter, ground floods dark, it becomes the ring | | |
| 118.0-124.6 | bar slides into the ring on the final hit; wordmark wipes in; lines land | Share the moment. Not the clues. · An AI Skill for UGREEN AI NAS · repo · Not an official UGREEN product. | final hit 118.0 |
| 124.6-131.0 | credits roll in and hold | music and photo credits | music tail |

## Captions (music-only cut)

Narration as kinetic captions: Inter 600 46 px, centred, bottom band (centre y 936), one group of 2-7 words at a time, each word inks from 22% to 100% at its spoken time; ivory on dark worlds, ink on the light UI world. Captions are off for L4, L6 and L16, where the type on screen carries the line.

## BANNED

Dark void with small floating things; glow, bloom, particles; purple/blue gradients, glass cards; everything centred; everything fading up; titles that drift after landing; breathing/pulsing loops; corner brackets and HUD decoration; three cards in a row; the logo docked in a corner; CSS blur or filters on photographs; any readable plate, card number, barcode, Wi-Fi password, postal code or house number; UGREEN logos (name as text only).

## QA frames

3, 8, 16, 21, 30, 36.5, 38, 44, 52, 56, 61, 66, 74, 79, 83, 88, 97, 105, 110, 115, 117.5, 120, 128.
