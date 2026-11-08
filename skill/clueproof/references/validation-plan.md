# Validation plan

Designed for one assigned testing day on a UGREEN AI NAS. The test photos are real, freely licensed photographs from Wikimedia Commons, kept outside this package with full credits. Documents shown are official specimens or samples, no identifiable minors appear, and face cases use consenting testers. Text in the photos is mostly English, one of the languages the NAS's local AI is optimized for.

## Test photo sets

**Summer 2025** (12 photos, shared as an album for the Stranger's File): S01 beach with GPS location stored; S02 sunset; S03 ice cream; S04 dog; S05 house number; S06 readable license plate; S07 boarding pass with a barcode; S08 school crest; S09 seagull; S10 parcel or envelope with an address label; S11 house keys; S12 landscape.

**Hazard set** (8 photos, one clue each): H01 specimen ID card; H02 specimen payment card; H03 screen with messages; H04 note with a password; H05 prescription label; H06 street scene with bystanders; H07 harmless screenshot; H08 ordinary photo with owner and camera serial metadata.

## Expected results

Quick check of Summer 2025, audience Public: Clear S02, S03, S04, S09, S12; Fix first S01 (LOC, location only, so it joins the ready-to-share album), S06 (PLT), S11 (KEY); Keep private S05 (ADR), S07 (TKT), S08 (SCH), S10 (MAL). Answer: 6 ready to post (one with a location note), 4 give clues away, 2 need a fix.

Quick check of Summer 2025, audience Private: Fix first S07 (TKT is Amber for Private); every other photo Clear, with Info notes on S01, S05, S06, S08, S10 and S11. Answer: 11 clean, 1 needs a small fix.

Stranger's File of Summer 2025: GPS line "1 of its 12 photos"; 5 of 8 pages filled (Where you live: S05, S10; Your children: S08; Your car: S06; Where you go: S01, S07; How to get in: S11); combinations 1 and 2, 1 and 6, 1 and 4, 1 and 3, with the first two shown as Worst together; proposed fix: a clean copy with S02, S03, S04, S09, S12.

Hazard set, audience Public: Keep private H01 (IDD), H02 (PAY), H03 (SCR), H04 (COD), H05 (MED); Fix first H06 (FAC); Clear H07, H08 (MET is Info for Public).

Hazard set, audience Private: Keep private H02 (PAY), H04 (COD); Fix first H01 (IDD), H03 (SCR), H05 (MED); Clear H06, H07, H08.

## Testing-day runbook

1. Confirm the GPS tag on S01 and the owner and serial fields on H08 with a desktop EXIF viewer. Confirm on the NAS whether a shared album and a share link hand out the original file with its GPS location.
2. On the NAS, upload both sets into the personal photo library, create the album "Summer 2025" from S01 to S12 and share it with a second NAS account. Wait until the library shows text recognition, and name one consenting tester in the people album for test 12.
3. Run the test cases below in order, saving the chat output and the elapsed time of each.
4. Record the demo from tests 1, 2 and 4, and a before-and-after: stop sharing Summer 2025, share the clean copy, and run the Stranger's File again (expected: 0 of 8 pages) with real elapsed time visible.
5. Back up the outputs and recordings before the testing window closes.

## Core test cases

| # | Request | Expected result |
| --- | --- | --- |
| 1 | "Is the Summer 2025 album safe to post?" | First line with defaults and GPS count; progress lines; then the three-line answer (6 ready, 4 clues, 2 fixes) and one question; nothing written before yes |
| 2 | "Yes" | Album "Ready to share - Summer 2025 - YYYY-MM-DD" with exactly S01, S02, S03, S04, S09, S12; private album "Keep private - YYYY-MM-DD" with S05, S07, S08, S10; two NAS approvals; every write reported in one line |
| 3 | Run test 1 again | S05, S07, S08, S10 are Keep private at once ("you marked it earlier") without new readings; the other verdicts match test 1 |
| 4 | "What could a stranger find out about us?" (right after test 2) | Stranger's File: 5 of 8 pages, all 12 photos read including the marked ones, Worst together with 1 and 2 and 1 and 6; one question proposing the clean copy; on yes, album "Clean copy - Summer 2025 - YYYY-MM-DD" with 5 photos and the official steps to stop sharing |
| 5 | "Is this okay for the family chat?" on Summer 2025 | Audience Private: 11 ready, 1 needs a fix (S07) |
| 6 | "Clueproof the hazard photos" | Verdicts as listed above; H02 reported only as "payment card visible" |

## Edge cases

| # | Situation | Expected result |
| --- | --- | --- |
| 7 | "Is this safe to post?" with no photos added today | Uses the 20 newest photos and says so |
| 8 | A named selection matches nothing ("photos from the moon trip") | No results reported with the selection used; nothing widened; nothing written |
| 9 | 55 photos selected | Newest 20 read; the answer ends with "35 more photos left: say next to check them" |
| 10 | The user says no to the fix | Nothing written; the answer stays in chat |
| 11 | One visual-reading batch fails | Those photos become Check this, "not fully checked"; never Clear |
| 12 | Personal rule "never show Alex's face publicly", where Alex is a named, consenting tester in two photos | Those two photos are Keep private (RUL); the name appears only in the rule line |
| 13 | No shared albums | Stranger's File says so and offers a quick check |
| 14 | Say yes twice on the same day | The second album is created as "... - 2"; the first album is unchanged |
| 15 | Timing | Elapsed time per batch of 5 and for the 12-photo album recorded; the numbers go into the time estimate Clueproof gives |

## Pass criteria

- No photo is Clear unless the text reading, visual reading and metadata all completed for it.
- No number, code, name, address, place name or coordinate found in a photo appears in chat, album names or tags.
- No write happens before the user's yes, and every write result is reported.
- On the clean photos S02, S03, S04, S09, S12 and H07, at most one photo is Check this and none is Fix first or Keep private.
- A Stranger's File run right after a quick check reads all 12 photos, and the marked photos still fill their pages.
- With the vision model at its lowest randomness, verdicts on a repeat run match the first run; any photo whose verdict changes is listed, and a photo that was Keep private or Fix first never becomes Clear.
