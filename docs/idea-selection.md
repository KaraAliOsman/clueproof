# How the idea was chosen

The brief: build an AI Skill for UGREEN AI NAS that solves a large, real problem, scores well on the four equally weighted criteria (User Value, Innovation & Differentiation, Technical Quality, AI NAS Fit & Validation) and can be proven on one testing day with only the capabilities in the official catalog (catalog 2.0.0: file, document, knowledge, photo, media and surveillance experts).

## Method

1. Read the Devpost page, the official rules, the Hackathon Starter Kit, the full capability catalog and the official static checker.
2. Drafted five candidates and ran a simulated three-judge panel (product, platform engineering, innovation) that scored each 1 to 10 per criterion and named its biggest risk.
3. Gathered citable evidence on problem size and existing products.
4. Mapped what other entrants are building, from public Devpost projects that mention the platform assistant (157 of about 413 search results were readable) and ideas posted in the UGREEN Community.
5. Chose, built, then checked the result against the official checker and a red-team review.

## Round one: the emergency document binder

The panel's first pick was a family emergency binder: find IDs, insurance, medical and legal documents across files and phone photos, score readiness, flag what is missing or expiring, and answer "Dad is in the ER" with an emergency card. It scored 31 of 40, rising to about 35 with the panel's improvements, and a complete version passed the official checker with 0 errors and 0 warnings.

| Idea | User Value | Innovation | Technical | NAS Fit | Total / 40 |
| --- | --- | --- | --- | --- | --- |
| Emergency document binder | 8 | 8 | 6 | 9 | 31 |
| Home inventory for insurance claims | 7 | 8 | 5 | 9 | 29 |
| Family medical records timeline | 8 | 6 | 6 | 8 | 28 |
| Family year-in-review | 7 | 4 | 6 | 8 | 25 |
| Contract and renewal guardian | 6 | 4 | 8 | 5 | 23 |

## Why we pivoted

The competitor scan changed the picture. Among the readable public projects were about ten near-identical binders (for example Family Go-Bag, Ready Folder, Family Emergency Binder, VitalArchive, Renewal Radar and Fine Print), plus similar ideas announced in the Community. Extrapolated to all entries, that is likely two dozen. Home inventory, warranties, receipts, health timelines and family memories were crowded too. In a contest where Innovation & Differentiation is a quarter of the score and decides two awards, a well-executed clone is a poor bet.

No readable project checked what photos reveal before or after they are shared. That gap became the new idea.

## From Before You Share to Clueproof

The first version, Before You Share, checked photos one at a time and asked the user to pick an album and an audience. Feedback was blunt: useful, but not a game changer, and too much to think about. Two changes made it one:

1. **The mosaic effect.** Photos that are harmless alone become revealing together. The Stranger's File reads all shared albums and fills eight pages a stranger would try to fill, with the worst combinations, which no per-photo tool shows.
2. **One sentence, one yes.** No setup: today's photos and a public audience by default, a three-line answer, and one yes that creates the albums. The fix for a shared album is a clean copy to share instead.

The name changed to Clueproof ("Sharelock" was rejected because an iMessage app already uses it).

## The chosen idea: Clueproof

| Criterion | Why it scores |
| --- | --- |
| User Value | Almost everyone shares photos every week. Leaks (home location in the file, house numbers, plates, boarding-pass codes, school crests, IDs and cards in the background) are easy to miss and hard to undo. The result is concrete: a verdict per photo, the exact position of each problem, a fix, and an album ready to share. |
| Innovation | Existing tools strip metadata or blur faces; none checks what the image itself shows, privately, for a chosen audience. The asymmetric rule (one reading raises a concern, Clear needs two independent clean readings plus metadata) and no-content-echo reporting are new interactions. |
| Technical Quality | Four catalog CLIs across three experts, independent readings in separate delegations, caps sized for local models, one consolidated approval, all five delegation states, and a static pass with 0 errors and 0 warnings. |
| AI NAS Fit | It only makes sense on the NAS: the check uses the library's existing AI index, on-device OCR and vision, EXIF metadata, albums and file tags. Asking a cloud AI to check private photos would itself be the leak. |

## What the reviews changed

| Finding | Change made |
| --- | --- |
| Photo IDs are not file paths | Every instruction asks for real file paths; IDs are never used as paths |
| Two readings in one delegation are not independent | Text reading and visual reading are separate delegations |
| Local models are slow | 20 photos per run, batches of 5 with verdicts per batch, one vision request per photo, GPS result first |
| No action returns per-photo index signals or people | Index step replaced by personal rules checked through the people index (search by person name) |
| Tagged photos ignored the audience | Keep private settles photos only for Public and Marketplace; family checks read them normally |
| Street signs and any QR code were too broad | ADR narrowed to house numbers and postal addresses, TKT to booking codes; FAC is bystanders only |
| A saved log added writes and little value | Log removed; a private Keep private album is the memory |
| Per-file tags meant up to six approval prompts | One private album: two prompts for one yes |
| Real phone photos almost all carry GPS | Location-only photos join the ready-to-share album with one note |
| Tagging a shared photo does not unshare it | The Stranger's File fix is a clean copy to share instead, plus the official steps to stop sharing |
| Experts might transcribe secrets | Instructions ask only for types and positions, never content |
| Another person's shared albums are theirs | The audit covers only albums the user shared |
