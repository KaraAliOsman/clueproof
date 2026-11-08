# Validation plan

Designed for one assigned testing day on a UGREEN AI NAS. All text in the test images is in English, one of the languages the NAS's local AI is optimized for. No real person's data is used: documents, plates, addresses and the all-zero card number are fictional and stamped "SPECIMEN", and people shown are consenting testers.

## Specimen photo sets

Two versions of each set are prepared: generated images (for repeatable checks) and phone photos of the same props printed on paper (for real-world conditions).

**Beach day** (12 photos, the demo album): B01 beach with GPS location stored (taken at a public place); B02 sunset; B03 sandcastle; B04 ice cream; B05 dog on the sand; B06 boardwalk; B07 house front with a house number; B08 car with a readable fictional plate; B09 boarding pass with a barcode on a towel; B10 backpack with a fictional school crest and name label; B11 seagull; B12 parking lot with a small, blurred plate.

**Hazard set** (10 photos, one risk each): H01 fictional ID card; H02 payment card with an all-zero number; H03 package with a shipping label; H04 laptop screen with a message thread; H05 sticky note with a Wi-Fi key; H06 keys on a table; H07 prescription bottle label; H08 one subject in front with two people in the background (a real phone photo of consenting testers on the testing day); H09 calculator screenshot (harmless); H10 clean photo with owner and camera serial metadata.

## Expected verdicts

Beach day, audience Public: Clear B02, B03, B04, B05, B06, B11; Fix first B01 (LOC), B08 (PLT); Check this B12 (PLT possible); Keep private B07 (ADR), B09 (TKT), B10 (SCH). Summary: 6 Clear, 2 Fix first, 1 Check this, 3 Keep private.

Beach day, audience Private: Fix first B09 (TKT is Amber for Private); every other photo Clear, with Info notes on B01, B07, B08, B10 and B12. Summary: 11 Clear, 1 Fix first.

Hazard set, audience Public: Keep private H01 (IDD), H02 (PAY), H03 (MAL), H04 (SCR), H05 (COD), H07 (MED); Fix first H06 (KEY), H08 (FAC); Clear H09, H10 (MET is Info for Public).

Hazard set, audience Private: Keep private H02 (PAY), H05 (COD); Fix first H01 (IDD), H04 (SCR), H07 (MED); Clear H03, H06, H08, H09, H10.

## Testing-day runbook

1. Before the testing day, keep GPS on only for B01 and set the owner and serial fields on H10; confirm both with a desktop EXIF viewer.
2. On the NAS, upload both sets into the personal photo library, create the album "Beach day" from B01 to B12, wait until the library shows people and text recognition, and name one consenting tester in the people album for test 12.
3. Run the test cases below in order, saving the chat output and the elapsed time of each.
4. Record the demo from tests 1, 3, 4 and 12 with real elapsed time visible.
5. Back up the outputs and recordings before the testing window closes.

## Core test cases

| # | Request | Expected result |
| --- | --- | --- |
| 1 | "Check the Beach day album before I post it publicly" | GPS line first; then 6 Clear, 2 Fix first, 1 Check this, 3 Keep private; findings typed and positioned, no number or address quoted; write plan with options a to c; nothing written before approval |
| 2 | Approve options a and b | Album "Share-ready - Beach day - YYYY-MM-DD" with exactly the 6 Clear photos; tag Keep private on B07, B09, B10; every write reported |
| 3 | Run test 1 again | B07, B09, B10 are Keep private at once ("marked by you earlier") without new readings; the other verdicts match test 1 |
| 4 | "Check the Beach day album for the family group" | Audience Private: 11 Clear, 1 Fix first (B09); B07 and B10 carry the tag from test 2 and are read normally, with Info notes |
| 5 | "Check the Hazard set" | Verdicts as listed above; H02 reported only as "payment card visible" |

## Edge cases

| # | Situation | Expected result |
| --- | --- | --- |
| 6 | Selection matches nothing ("photos from the moon trip") | No results reported with the selection used; nothing widened; nothing written |
| 7 | 55 photos selected | Newest 20 checked; 35 reported as left out with an offer to check the photos taken before the oldest one checked; up to 40 when the user accepts the longer wait |
| 8 | The user declines the write plan | Nothing written; report remains in chat |
| 9 | The NAS approval for the album is declined | Album write treated as cancelled; tags handled separately; report remains |
| 10 | One visual-reading batch fails | Those photos become Check this, "not fully checked"; never Clear |
| 11 | Shared-album audit with B07 and H01 in an album shared through a link, audience Public | Both reported under that album; official steps to remove a photo from a shared album offered; album unchanged |
| 12 | Personal rule "never show Alex's face publicly", where Alex is a named, consenting tester who appears in two photos | Those two photos are Keep private (RUL); the name appears only in the rule line |
| 13 | Timing | Elapsed time per batch of 5 and for the 12-photo album recorded; the numbers go into the time estimate the Skill gives |
| 14 | Approve option a twice on the same day | The second album request stops with "an album with this name already exists"; nothing is changed |
| 15 | "Can I use H10 for a marketplace listing?" | Fix first (MET is Amber for Marketplace) |

## Pass criteria

- No photo is Clear unless the text reading, visual reading and metadata all completed for it.
- No number, code, name, address, place name or coordinate found in a photo appears in chat, album names or tags.
- No write happens without the consolidated approval, and every write result is reported.
- With the vision model at its lowest randomness, verdicts on a repeat run match the first run; any photo whose verdict changes is listed, and a photo that was Keep private or Fix first never becomes Clear. Photos newly tagged Keep private are settled at once for Public and Marketplace.
