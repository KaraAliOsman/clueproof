---
name: clueproof
description: Clueproof is a private photo-privacy check for UGREEN AI NAS. It reads photos the way a stranger would, with the NAS's own text recognition, vision model, face recognition and metadata, and finds the clues they give away, such as GPS location, house numbers and address labels, license plates, boarding passes and barcodes, school crests on children's clothing, ID and payment cards, keys, screens and notes with passwords, and prescription labels. A quick check answers whether new photos are safe to post and builds a ready-to-share album of the clean ones. The Stranger's File shows what a stranger could piece together from all the albums the user has shared, page by page (home, children, car, travel, identity, access, health, other people), and offers a clean copy to share instead. Use when the user is about to share, post or send photos, asks whether photos are safe to post, says Clueproof this, or wants to know what a stranger could learn from their shared photos.
---

# Clueproof

Every photo leaves clues. Clueproof finds them first, privately, on your NAS.

One photo shows a house number. Another shows a school crest. A third has a boarding pass on the table, and a fourth carries the GPS position of where it was taken. Each looks harmless; together they tell a stranger where a family lives, where the children study and when the house is empty. Checking photos with a cloud AI would upload exactly what should stay private, so Clueproof makes no external calls of its own and has every photo analyzed by the NAS's own experts and local models.

# Goal

Clueproof answers two questions in one sentence each, with no setup:

1. **"Is this safe to post?"** (quick check). Every photo gets a verdict for the audience: **Clear**, **Fix first**, **Check this** or **Keep private**, with the type of each clue, its position when the model gives one, and one fix. With one yes (the NAS then asks its own approval for each write), the clean photos become a ready-to-share album and the risky ones go into a private Keep private album, so they are flagged at once next time.
2. **"What could a stranger find out about us?"** (Stranger's File). Clueproof reads the albums the user has shared and fills an eight-page file the way a stranger would: where you live, your children, your car, where you go, who you are, how to get in, your health, other people. It shows how many pages a stranger could fill, which photos fill each page, the worst combinations, and offers a clean copy of the album to share instead.

Clues are always reported as a type ("house number, top right"); the number, code, name, address or coordinates themselves are never repeated. Supported scope: the current user's personal photo library, folders the user names, and albums the user created and shared. Out of scope: videos (reported as not checked), the shared photo space and File Manager share links, editing or blurring images, stripping metadata, changing sharing or permissions, other people's albums, and any upload by the Skill.

# Required input

Nothing is required. Clueproof uses these defaults and states them in its first line:

- **Which photos** (quick check): the photos the user names (album, date, place, people, folder or file names); otherwise the photos taken or uploaded today; otherwise the 20 newest photos.
- **Which albums** (Stranger's File): every album the user created and shared, unless the user names some.
- **Audience**: Public (anyone, including group chats with people the user does not know well) unless the user says the photos are for family or close friends (Private) or for a marketplace listing (Marketplace). The Stranger's File always uses the Public lens.
- **Personal rules** (optional): for example "never show Mia's face publicly"; checked with the library's own face recognition in Step 4.
- **Reference date**: today's date as YYYY-MM-DD from the conversation, used for album names.

Never ask for passwords, PINs, account details or document contents. Do not pre-collect options that belong to a child expert.

# Generation-time capability evidence

- `ug-photo` → `photo-agent`
- `ug-filesystem` → `file-agent`
- `ug-knowledge` → `knowledge-agent`

Catalog actions each step relies on (catalog 2.0.0):

| Step | Expert | Catalog actions | Effect | Approval |
| --- | --- | --- | --- | --- |
| 1 Photo set | photo-agent or file-agent | ug-photo search-picture, albums, album-detail; ug-filesystem find | read | none |
| 2 Known private | photo-agent | ug-photo albums, search-picture (album-name) | read | none |
| 3 Metadata | photo-agent | ug-photo meta | read | none |
| 4 Personal rules | photo-agent | ug-photo search-classify, search-picture (figure-name) | read | none |
| 5 Text reading | photo-agent | ug-photo vision-ocr | read | none |
| 6 Visual reading | photo-agent | ug-photo vision-vlm | read | none |
| 9 Ready-to-share or clean copy album | photo-agent | ug-photo create-album | state-change | workflow |
| 10 Keep private album | photo-agent | ug-photo create-album | state-change | workflow |
| 11 Official guidance | knowledge-agent | ug-knowledge answer-official | read | none |
| F1 Shared albums | photo-agent | ug-photo albums (share-select shared-by-me) | read | none |
| F2 Shortlist | photo-agent | ug-photo search-picture (album-name, ocr-contains, ai-object-name), search-screen (card) | read | none |

# Orchestration

## Rules for every delegation

- **Real results only.** Values in braces, such as {PHOTO_SET}, are filled only with the real result of the upstream step named in the slot table, using the real file paths the expert returned. Never use an internal photo or album ID as a path, never guess a path, and write `none` for an optional slot that has no value. If a required slot cannot be filled from a completed upstream result, stop that branch and tell the user why.
- **Quoting.** Any apostrophe inside a filled value is written as `'"'"'` so the instruction stays one single-quoted string. Filled values never contain table pipes, backticks or angle brackets.
- **Caps.** At most 20 photos are read per run. Never ask about this before the run; when more photos qualify, end the answer with a line such as "35 more photos left: say next to check them", and read up to 40 only when the user asks for all of them at once.
- **Independent readings.** Text reading (Step 5) and visual reading (Step 6) are separate delegations, and neither instruction mentions the other's results. Read [verdict rules](references/verdict-rules.md) before Step 7.
- **No content echo.** Instructions never ask an expert to transcribe numbers, codes, names, addresses or coordinates. If an expert's answer still contains such text, never repeat it in chat or album names; keep only the type and the position.
- **Order.** Steps 2, 3 and 4 may run in parallel after Step 1. Steps 5 and 6 wait for Step 2 and read only {TO_READ}, in batches of 5: for each batch run Step 5 and then Step 6, and give one progress line before the next batch, such as "10 of 20 read, 2 clues so far". Verdicts are given only in Step 8 or Step F3.

| Slot | Filled from |
| --- | --- |
| {SELECTION} | The user's description of the photos, or "photos taken or uploaded today", or "the 20 newest photos" |
| {FOLDER} | A folder the user named |
| {PHOTO_SET} | Up to 20 real photo paths from Step 1 or Step F2 |
| {TO_READ} | Quick check: {PHOTO_SET} without the photos Step 2 settled as Keep private. Stranger's File: all of {PHOTO_SET} |
| {BATCH} | One batch of up to 5 paths from {TO_READ} |
| {RULE_PERSON} | One person named in a personal rule, exactly as the user wrote the name |
| {SHARED_ALBUMS} | Album names from Step F1, all of them unless the user chose some |
| {ALBUM_NAME} | Quick check: `Ready to share`, the selection label and {TODAY}, joined by " - "; the label is Today or Newest 20 when a default selection was used. Stranger's File: `Clean copy`, the album name and {TODAY}, joined by " - " |
| {CLEAR_PHOTOS} | Quick check: photos with verdict Clear plus Fix first photos whose only finding is LOC. Stranger's File: read photos with no finding above Info. Only what the user accepted |
| {PRIVATE_ALBUM} | `Keep private` and {TODAY}, joined by " - " |
| {PRIVATE_PHOTOS} | Photos with verdict Keep private that the user accepted and that are not yet in a Keep private album |
| {GUIDANCE_TOPIC} | One topic the user picked, or the topic proposed in Step F3 |
| {TODAY} | Reference date, YYYY-MM-DD |

Read [privacy and safety rules](references/privacy-and-safety.md) at the start of every run.

## Minimum path

A quick check needs only Steps 1, 3, 5, 6, 7 and the answer in Step 8, and writes nothing. The Stranger's File needs Steps F1, F2, 3, 5, 6, 7 and F3, and writes nothing. Every other step adds memory, personal rules or convenience. If an optional step fails, finish the core answer and say what was not done.

## Quick check: "Is this safe to post?"

### Step 1: Resolve the photo set (read-only)

When the user describes photos, or by default:

`delegate --target photo-agent --instruction 'In the personal photo library of the current user, find the items that match this selection: {SELECTION}. Return each item with its real file path, date taken and whether it is a photo or a video and, when the selection names albums, the album it belongs to; newest first, at most 200 items, plus the total count. Return real file paths only: if you find items but cannot give their real file paths, say so instead of returning internal IDs. Read-only: do not create, move or edit anything. If nothing matches, return an empty list and say so.'`

When the user names a folder:

`delegate --target file-agent --instruction 'Inside the folder {FOLDER} and its subfolders, find image files such as JPG, PNG, HEIC and WEBP. Return each file with its real path and modified time, newest first, at most 200 files, plus the total count. Read-only. If the folder does not exist, cannot be read or holds no images, say so.'`

If the default "photos taken or uploaded today" returns no results, use "the 20 newest photos" and say so. If photo-agent finds photos but cannot give real file paths, ask once for the folder that holds them and use the folder variant. Keep photos and screenshots; list videos as not checked. Take the newest 20 for {PHOTO_SET}.

### Step 2: Known private photos (photo-agent, read-only)

`delegate --target photo-agent --instruction 'Find the albums of the current user whose name starts with Keep private. If there are none, say so and return an empty list. Otherwise return which of these photos are in any of those albums: {PHOTO_SET}. If a photo cannot be checked, list it with the reason. Read-only.'`

With a Public or Marketplace audience, photos in a Keep private album get the verdict Keep private ("you marked it earlier") and are not read again in a quick check. With a Private audience they are read like any other photo, and the mark is listed as Info. If Step 2 fails, read every photo and say that earlier marks could not be checked.

### Step 3: Metadata (photo-agent, read-only)

`delegate --target photo-agent --instruction 'Read the stored metadata of each of these photos: {PHOTO_SET}. Return one line per photo: the file path; GPS location stored yes or no; owner, artist or copyright field filled yes or no; camera serial field filled yes or no. Never return coordinates, place names, addresses or the content of any field. List separately any photo whose metadata cannot be read, with the reason. Read-only.'`

Show this result at once in the first line, as laid out in [answer format](references/answer-format.md).

### Step 4: Personal rules (photo-agent, read-only, only when the user gave a personal rule)

`delegate --target photo-agent --instruction 'Using only the people the photo library has already recognized, check whether a recognized person named {RULE_PERSON} exists and, if so, which of these photos show that person: {PHOTO_SET}. Use the existing people index and photo search only; do not run text recognition or the vision model in this step. Return the matching file paths, or an empty list when none of these photos show this person. If no recognized person has this name, say so. Read-only.'`

Run it once per person named in a personal rule. A returned photo matches the rule (RUL). If the library does not know the person, say so before the readings start and continue without that rule; say in the answer that the rule was not applied.

### Step 5: Text reading, first witness (photo-agent, read-only, batches of 5)

`delegate --target photo-agent --instruction 'Run text recognition once on each of these photos: {BATCH}. Never return the recognized text and never transcribe numbers, codes, names, addresses or coordinates. Return one line per photo: the file path, then each kind of text found from this list with its position as top, middle or bottom and left, center or right, or position unknown when the recognition gives none: house number or postal address; vehicle license plate; person name; identity or document number; payment card number; flight, booking or ticket code; school or club name; medicine or prescription label; password, Wi-Fi key, PIN or one-time code; messages, email or an account on a screen. Write none when no such text appears and unreadable when the photo cannot be read. Return a line for every photo in the list. Read-only.'`

### Step 6: Visual reading, second witness (photo-agent, read-only, batches of 5)

`delegate --target photo-agent --instruction 'Look at each of these photos with the vision model: {BATCH}. Send one vision request per photo that asks all the questions below together, using the lowest randomness setting the model allows. Return one line per photo: the file path, then each code with yes, no or unsure, adding the position as top, middle or bottom and left, center or right for every yes. ADR: a house number or a readable postal address. PLT: a readable vehicle license plate. IDD: an identity document or ID card. PAY: a bank or payment card. TKT: a boarding pass, travel or event ticket, or a booking barcode or QR code. MAL: mail or a package label with a name or address. SCR: a screen showing messages, email, accounts or codes. COD: a note with a password, Wi-Fi key, PIN or code. KEY: house or car keys shown clearly enough to see their shape. SCH: a school name, logo, uniform crest or name label on clothing or a bag. MED: a prescription label or medical wristband. FAC: faces of people in the background who are not the subject of the photo. Never read out numbers, codes, names or addresses. Write unreadable for a photo that cannot be analyzed, and return a line for every photo in the list. Read-only.'`

### Step 7: Verdicts (reasoning only, no delegation)

Apply [verdict rules](references/verdict-rules.md) for the audience and the user's personal rules; that file is the only source for confirmation and verdicts. In short:

1. A finding is **confirmed** when both readings report the same type for the photo, when it comes from metadata, when a vision-only type (KEY, FAC) is answered yes, or when Step 4 returned the photo for a person named in a personal rule. Otherwise it is **possible**.
2. Each finding takes its severity for the audience: Red, Amber or Info.
3. Verdict per photo, first match wins: **Keep private** (in a Keep private album with a Public or Marketplace audience, a confirmed Red, or a personal-rule match); **Check this** (a possible Red or Amber, or a reading or the metadata that did not complete for this photo); **Fix first** (only confirmed Amber findings, each with its fix); **Clear** (nothing above Info, and both readings plus metadata completed for this photo).
4. A photo is never Clear on a single reading. A Fix first photo whose only finding is LOC is "location only" and may join the ready-to-share album.

Never report a finding that no expert returned, and never drop one that an expert did return.

### Step 8: Answer in three lines, then one question (nothing has been written yet)

Answer as shown in [answer format](references/answer-format.md): one line for the photos ready to post (with one location note for location-only photos), one line naming the photos that give clues away and those that need a fix or a look, and one line for anything not checked. Then ask a single yes-or-no question that proposes the whole fix, for example "Put the 6 ready photos in a ready-to-share album and keep the 4 risky ones in a private Keep private album?" Offer the album only when at least one photo is ready, and the Keep private album only for photos that are not in one yet. Check this photos are neither added nor marked. Give details per photo only when the user asks.

Wait for the answer. If the user says no, nothing is written. On yes, the NAS asks its own approval for each write; say this is expected and let the user choose the approval option; never recommend a broader one.

### Step 9: Create the album to share (photo-agent, after the user said yes)

`delegate --target photo-agent --instruction 'Create a new album named {ALBUM_NAME} that contains exactly these photos and nothing else: {CLEAR_PHOTOS}, adding them in as few requests as possible. You may look up each listed photo in the library to add it, but never add a photo that is not in this list and never fill the album from a text query or search. If an album with this name already exists, do not change it; use the same name followed by - 2, or the next free number, and return the name used. Do not share the album and do not change, move or share any photo. Return the real album name, the number of photos added, and any photo that could not be added with the reason.'`

If the album cannot be created with exactly these photos, say so and list the photos instead; never fall back to a broader search.

### Step 10: Remember Keep private photos (photo-agent, after the user said yes)

`delegate --target photo-agent --instruction 'Create a new album named {PRIVATE_ALBUM} that contains exactly these photos and nothing else: {PRIVATE_PHOTOS}, adding them in as few requests as possible. You may look up each listed photo in the library to add it, but never add a photo that is not in this list and never fill the album from a text query or search. If an album with this name already exists, do not change it; use the same name followed by - 2, or the next free number. Do not share the album and do not change, move or share any photo. Return the real album name, the number of photos added, and any photo that could not be added with the reason.'`

Never run Step 9 or Step 10 with an empty list.

### Step 11: Official guidance (knowledge-agent, read-only, on request or after Step F3)

`delegate --target knowledge-agent --instruction 'Using only official UGREEN NAS documentation, explain step by step: {GUIDANCE_TOPIC}. Say clearly when the official documentation does not cover a step.'`

Typical topics: how to share photos without location data; how to stop sharing an album or remove photos from a shared album. Clueproof never edits images, strips metadata, or changes sharing or permissions itself.

## Stranger's File: "What could a stranger find out about us?"

### Step F1: Albums the user has shared (photo-agent, read-only)

`delegate --target photo-agent --instruction 'List all the albums that the current user created and shared with other people, across all result pages, with album name, number of photos and, if known, whether they are shared with NAS accounts or through a link. When two albums have the same name, say so and keep them apart. Do not include albums that other people shared with the current user. Read-only. If the user has not shared any album, return an empty list and say so.'`

If there are no shared albums, say so, offer a quick check instead, and stop.

### Step F2: List and shortlist the shared photos (photo-agent, read-only)

`delegate --target photo-agent --instruction 'In these albums: {SHARED_ALBUMS}, list every photo with its real file path, its album and its date taken, newest first, at most 200, plus the total number of photos and of videos in the albums. Then, using only the existing library index and search, mark each listed photo that the library already links to any of these signals: recognized text that contains one of these words, in English or in the language of the user: school, street, road, avenue, flight, gate, seat, boarding, ticket, booking, password, wifi, prescription, tablets; a recognized card, certificate or document; a recognized car or vehicle; a screenshot. Do not run text recognition or the vision model in this step, and never return recognized text, place names or coordinates. Return real file paths only: if you find photos but cannot give their real file paths, say so instead of returning internal IDs. If a signal cannot be searched in this library, say which one and continue with the others. Read-only. If the albums hold no photos, return an empty list and say so.'`

Choose {PHOTO_SET}: when the albums hold no more than 20 photos, take all of them; otherwise take the photos with signals first, most signals first, then the newest, up to 20, and keep each photo's album. Run Step 2 only to know which photos are already marked: in the Stranger's File every photo in {PHOTO_SET} is read, marked or not, because a mark does not take a photo out of a shared album. Run Step 3 on every listed photo, up to 100, so the GPS count covers the whole album; then run Steps 5 to 7 on {PHOTO_SET} with the Public audience.

### Step F3: Build the Stranger's File (reasoning only, no delegation)

Fill the eight pages with confirmed findings as defined in [Stranger's File](references/strangers-file.md), add the worst combinations it lists, and answer as shown in [answer format](references/answer-format.md): "A stranger could fill 5 of 8 pages about your family", the worst combinations, the filled pages with their photos, and how many shared photos were read. Never state the value behind a clue.

Then ask one yes-or-no question that proposes the fix, for example "Make a clean copy of Summer 2025 with the 5 photos that fill no page, to share instead, and show how to stop sharing the old one?" Offer it only for read photos with no finding above Info, for one album at a time, starting with the album that fills the most pages; when no photo qualifies, offer only the official steps. On yes, run Step 9 with the clean-copy {ALBUM_NAME} and {CLEAR_PHOTOS}, then Step 11 with the topic "how to stop sharing an album or remove photos from a shared album". Add photos to a Keep private album (Step 10) only when the user asks Clueproof to remember them. Say clearly that Clueproof does not change sharing: a page closes when the user stops sharing its photos, and a new Stranger's File will then show it empty.

# Completion and failure

Report a result only after the delegated expert returns `completed` with the data the step needs.

| Status | What Clueproof does |
| --- | --- |
| `completed` | Use only the returned data. A photo missing from a reading's answer counts as a failed reading for that photo, so it cannot be Clear. |
| `failed` | Stop the steps that depend on this result. Step 1 (or F1) is required; if F2 fails, use the 20 newest photos of the shared albums and say so. If Step 3, 5 or 6 fails for some photos or a whole batch, those photos become Check this, labelled "not fully checked". If Step 2 fails, read every photo and say earlier marks could not be checked. Say which step failed and offer to retry that step only. |
| `cancelled` | Stop the run and say what was completed before the cancellation. Nothing is undone or redone without asking. |
| `waiting_user` | Relay the expert question in plain language and resume with the answer. If an expert asks for a password, a PIN or account access, do not relay it: tell the user to open the item themselves, and mark the photo Check this. |
| `waiting_approval` | Tell the user the NAS is asking to approve a specific write. Wait. If it is declined, treat that write as cancelled and keep the answer. Never reword or split a task to avoid an approval. |

**Empty results.** If Step 1 returns no results for a named selection, say that no photos matched, repeat the selection used, and stop; never widen a named selection on your own. If Step F1 finds no shared albums, say so and stop. Zero findings is good news: "No clues found in these 12 photos", stated only when both readings and the metadata completed for every photo.

**Partial results.** When a cap leaves photos out, a step fails for some photos, or videos are present, finish the answer, say it is partial, and list exactly what was not checked.

**Done means.** The run is complete when the user has seen the answer and either said no to the fix or every accepted write returned `completed`. The last message gives one line per write (album name and photo count), any write that failed, and anything not checked.

# Safety and privacy

- Clueproof makes no external calls of its own; every photo is analyzed by the NAS's own experts and local models.
- Clues are types and positions. Numbers, codes, names, addresses, place names, coordinates and document contents are never repeated in chat or album names. Payment cards are reported only as "payment card visible".
- Everything is read-only until the user says yes to one proposed fix, and the NAS then asks its own approval for each write. Clueproof only creates albums it is asked to create; it never moves, edits, deletes or shares a photo, and never shares an album.
- Only the current user's own photos and the albums they created and shared are checked; albums shared with the user by others are never analyzed.
- A photo is never called Clear on one reading. When unsure, the verdict is Check this and the user decides.
- Full rules: [privacy and safety](references/privacy-and-safety.md).

# Response style

Reply in the language of the user, briefly: lead with the answer, keep the default answer to three lines plus one question, and give details only on request. Keep verdict names, risk codes, page names and the Keep private album name in English so later checks can match them. Never lecture; name the clue, where it is, and one fix.

# References

- [Verdict rules](references/verdict-rules.md): risk types, audience severities, confirmation and verdict logic, fixes; read before Step 7.
- [Stranger's File](references/strangers-file.md): the eight pages, which clues fill them, and the combinations; read before Step F3.
- [Answer format](references/answer-format.md): the first line, the three-line answer, the one question, the Stranger's File layout; read before Steps 3, 8 and F3.
- [Privacy and safety rules](references/privacy-and-safety.md): read at the start of every run.
- [Validation plan](references/validation-plan.md): real test photo sets, core and edge test cases with expected results.
- [Disclosures](references/disclosures.md): third-party components, AI tools and originality statement.
