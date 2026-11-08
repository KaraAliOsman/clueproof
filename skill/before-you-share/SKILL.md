---
name: before-you-share
description: Private pre-share privacy check for photos on UGREEN AI NAS. Reads photos the way a stranger would, using the NAS's own text recognition, vision model, face recognition and metadata, and reports what each photo gives away for the chosen audience (family, public post or marketplace listing): GPS location, house numbers and addresses, license plates, ID and payment cards, boarding passes and barcodes, mail and package labels, screens and notes with codes or passwords, keys, school names on children's clothing, prescription labels and faces of bystanders. Gives each photo a verdict of Clear, Fix first, Check this or Keep private, builds a share-ready album of cleared photos after approval, applies personal rules such as never showing a named child's face publicly, remembers photos marked Keep private, and audits albums already shared. Use when the user is about to share, post or send photos, asks whether a photo or album is safe to share, or wants to check what their shared albums reveal.
---

# Before You Share

Your photos say more than you think. Before You Share reads them first, privately, on your NAS.

A beach photo can carry the GPS position of where it was taken. A birthday photo can show your house number, your car plate, the school crest on a child's sweater, or the boarding pass on the table. People notice these leaks only after the photo is out. Checking photos with a cloud AI service would upload exactly what you are trying to protect, so this Skill uses the NAS's own experts and makes no external calls.

# Goal

For a set of photos the user is about to share, deliver:

1. **A verdict per photo** for the chosen audience: **Clear**, **Fix first** (share only after a listed fix, for example removing location or cropping), **Check this** (one reading saw a possible leak; the user decides), or **Keep private**.
2. **The type and position** of every finding ("house number visible, top right; seen by text and vision"), without ever reading out the number, code, name, address or coordinates.
3. **Personal rules** checked with the library's own face recognition, for example "never show Mia's face publicly".
4. **A share-ready album** containing only the Clear photos, created after the user approves.
5. **Memory**: photos marked Keep private are tagged, so later public checks settle them at once.
6. **Shared-album audit**: the same check on albums the user has already shared, with the official steps to fix what is found.

Supported scope: photos and screenshots in the current user's personal photo library, folders the user names, and albums the user created and shared. Out of scope: videos (reported as not checked), editing or blurring images, stripping metadata, changing sharing or permissions, other people's albums, and any upload or message outside the NAS.

# Modes

| Mode | Example requests | Writes to the NAS |
| --- | --- | --- |
| Check before sharing | "Check the beach photos before I post them", "Is the Birthday album safe for the class group?", "Can I post this photo?" | Only after one consolidated approval: share-ready album and Keep private tags |
| Shared-album audit | "What do my shared albums give away?", "Did I share anything I shouldn't have?" | Only Keep private tags, after approval |

# Required input

- **Which photos**: an album name, a date range, a place, people, a folder, or file names. Ask once if the request does not say.
- **Audience**: Private (family or friends the user knows well: NAS accounts, a family chat), Public (social media, public links, communities, and group chats with people the user does not know well, such as a class or neighborhood group) or Marketplace (selling something online). When the user does not say, use Public, the strictest common case, and say so.
- **Personal rules** (optional): for example "never show Mia's face publicly". The name must be a person the photo library has recognized; Step 4 checks it.
- **Reference date**: today's date as YYYY-MM-DD, taken from the conversation; ask only if it is not known. Used for the album name.

Never ask for passwords, PINs, account details or the content of any document. Do not pre-collect options that belong to a child expert.

# Generation-time capability evidence

- `ug-photo` → `photo-agent`
- `ug-filesystem` → `file-agent`
- `ug-filemgr` → `file-agent`
- `ug-knowledge` → `knowledge-agent`

Catalog actions each step relies on (catalog 2.0.0):

| Step | Expert | Catalog actions | Effect | Approval |
| --- | --- | --- | --- | --- |
| 1 Photo set | photo-agent or file-agent | ug-photo search-picture, albums, album-detail; ug-filesystem find | read | none |
| 2 Known private | file-agent | ug-filemgr tag-get-by-name, tag-get-file | read | none |
| 3 Metadata | photo-agent | ug-photo meta | read | none |
| 4 Personal rules | photo-agent | ug-photo search-classify, search-picture (figure-name) | read | none |
| 5 Text reading | photo-agent | ug-photo vision-ocr | read | none |
| 6 Visual reading | photo-agent | ug-photo vision-vlm | read | none |
| 9 Share-ready album | photo-agent | ug-photo create-album | state-change | workflow |
| 10 Keep private tags | file-agent | ug-filemgr tag-get-by-name, tag-add, tag-add-file | state-change | gateway, conditional |
| 11 Official guidance | knowledge-agent | ug-knowledge answer-official | read | none |
| A1 Shared albums | photo-agent | ug-photo albums (share-select shared-by-me) | read | none |

# Orchestration

## Rules for every delegation

- **Real results only.** Values in braces, such as {PHOTO_SET}, are filled only with the real result of the upstream step named in the slot table, using the real file paths the expert returned. Never use an internal photo or album ID as a path, never guess a path, and write `none` for an optional slot that has no value. If a required slot cannot be filled from a completed upstream result, stop that branch and tell the user why.
- **Quoting.** Any apostrophe inside a filled value is written as `'"'"'` so the instruction stays one single-quoted string. Filled values never contain table pipes, backticks or angle brackets.
- **Caps and time.** At most 20 photos are checked per run by default, newest first, or up to 40 when the user accepts the longer wait. Both readings run in batches of 5. Before the readings start, tell the user that each photo is read twice by the NAS's local models and that this takes a few minutes. When the selection is larger, say how many were left out and offer to check the rest in a new run, described as the same selection taken before the date of the oldest photo checked.
- **Independent readings.** Text reading (Step 5) and visual reading (Step 6) are separate delegations, and neither instruction mentions the other's results. Read [verdict rules](references/verdict-rules.md) before Step 7.
- **No content echo.** Instructions never ask an expert to transcribe numbers, codes, names, addresses or coordinates. Findings are reported as a type and a position. If an expert's answer still contains such text, never repeat it in chat, album names or tags; keep only the type and the position.
- **Order.** Steps 2, 3 and 4 may run in parallel after Step 1. Steps 5 and 6 wait for Step 2 and read only {TO_READ}. For each batch, run Step 5 and then Step 6, and give the verdicts for that batch before starting the next one. Every other step waits for the result it depends on.

| Slot | Filled from |
| --- | --- |
| {SELECTION} | The user's description of the photos (album, dates, place, people) |
| {FOLDER} | A folder the user named |
| {PHOTO_SET} | Up to 20 (or 40) real photo paths from Step 1 |
| {TO_READ} | {PHOTO_SET} without the photos Step 2 settled as Keep private |
| {BATCH} | One batch of up to 5 paths from {TO_READ} |
| {RULE_PERSON} | One person named in a personal rule, exactly as the user wrote the name |
| {ALBUM_NAME} | `Share-ready`, the selection label and {TODAY}, joined by " - " |
| {CLEAR_PHOTOS} | Paths with verdict Clear that the user approved in Step 8 |
| {PRIVATE_PHOTOS} | Paths with verdict Keep private that the user approved for tagging in Step 8 and that do not carry the tag yet |
| {SHARED_ALBUMS} | Album names from Step A1 chosen by the user |
| {GUIDANCE_TOPIC} | One topic the user picked in Step 8 |
| {TODAY} | Reference date, YYYY-MM-DD |

Read [privacy and safety rules](references/privacy-and-safety.md) at the start of every run.

## Minimum path

The core result needs only Steps 1, 3, 5, 6 and 7 and the report in Step 8, and writes nothing. Every other step adds memory, personal rules or convenience. If an optional step fails, finish the core report and say what was not done.

## Check before sharing

### Step 1: Resolve the photo set (read-only)

When the user describes photos by album, date, place or people:

`delegate --target photo-agent --instruction 'In the personal photo library of the current user, find the items that match this selection: {SELECTION}. Return each item with its real file path, date taken, whether it is a photo or a video and, when the selection names albums, the album it belongs to; newest first, at most 200 items, plus the total count. Return real file paths only: if you find items but cannot give their real file paths, say so instead of returning internal IDs. Read-only: do not create, move, tag or edit anything. If nothing matches, return an empty list and say so.'`

When the user names a folder:

`delegate --target file-agent --instruction 'Inside the folder {FOLDER} and its subfolders, find image files such as JPG, PNG, HEIC and WEBP. Return each file with its real path and modified time, newest first, at most 200 files, plus the total count. Read-only. If the folder does not exist, cannot be read or holds no images, say so.'`

If photo-agent finds the photos but cannot give real file paths, ask the user once for the folder that holds them and use the folder variant. Keep photos and screenshots; list videos as not checked. Take the newest 20 (or 40) for {PHOTO_SET} and say how many were left out.

### Step 2: Known private photos (file-agent, read-only)

`delegate --target file-agent --instruction 'Check whether the file tag Keep private exists. If it does, return which of these files carry it: {PHOTO_SET}. If the tag does not exist yet, say so and return an empty list. If a file cannot be checked, list it with the reason. Read-only.'`

With a Public or Marketplace audience, photos that carry the tag get the verdict Keep private ("marked by you earlier") and are not read again. With a Private audience they are read like any other photo, and the tag is listed as Info. If Step 2 fails, read every photo and say that earlier marks could not be checked.

### Step 3: Metadata (photo-agent, read-only)

`delegate --target photo-agent --instruction 'Read the stored metadata of each of these photos: {PHOTO_SET}. Return one line per photo: the file path, GPS location stored yes or no, and owner, artist, copyright or camera serial field filled yes or no. Never return coordinates, place names, addresses or the content of any field. List separately any photo whose metadata cannot be read, with the reason. Read-only.'`

Show this result at once, for example "GPS location stored in 5 of 12 photos", while the readings run.

### Step 4: Personal rules (photo-agent, read-only, only when the user gave a personal rule)

`delegate --target photo-agent --instruction 'Using only the people the photo library has already recognized, check whether a recognized person named {RULE_PERSON} exists and, if so, which of these photos show that person: {PHOTO_SET}. Use the existing people index and photo search only; do not run text recognition or the vision model in this step. Return the matching file paths, or an empty list when none of these photos show this person. If no recognized person has this name, say so. Read-only.'`

Run it once per person named in a personal rule. A returned photo matches the rule (RUL). If the library does not know the person or the step fails, tell the user before the readings start and ask once whether to continue without that rule; by default continue and say in the report that the rule was not applied.

### Step 5: Text reading, first witness (photo-agent, read-only, batches of 5)

`delegate --target photo-agent --instruction 'Run text recognition once on each of these photos: {BATCH}. Never return the recognized text and never transcribe numbers, codes, names, addresses or coordinates. Return one line per photo: the file path, then each kind of text found from this list with its position as top, middle or bottom and left, center or right, or position unknown when the recognition gives none: house number or postal address; vehicle license plate; person name; identity or document number; payment card number; flight, booking or ticket code; school or club name; medicine or prescription label; password, Wi-Fi key, PIN or one-time code; messages, email or an account on a screen. Write none when no such text appears and unreadable when the photo cannot be read. Return a line for every photo in the list. Read-only.'`

### Step 6: Visual reading, second witness (photo-agent, read-only, batches of 5)

`delegate --target photo-agent --instruction 'Look at each of these photos with the vision model: {BATCH}. Send one vision request per photo that asks all the questions below together, using the lowest randomness setting the model allows. Return one line per photo: the file path, then each code with yes, no or unsure, adding the position as top, middle or bottom and left, center or right for every yes. ADR: a house number or a readable postal address. PLT: a readable vehicle license plate. IDD: an identity document or ID card. PAY: a bank or payment card. TKT: a boarding pass, travel or event ticket, or a booking barcode or QR code. MAL: mail or a package label with a name or address. SCR: a screen showing messages, email, accounts or codes. COD: a note with a password, Wi-Fi key, PIN or code. KEY: house or car keys shown clearly enough to see their shape. SCH: a school name, logo, uniform crest or name label on clothing or a bag. MED: a prescription label or medical wristband. FAC: faces of people in the background who are not the subject of the photo. Never read out numbers, codes, names or addresses. Write unreadable for a photo that cannot be analyzed, and return a line for every photo in the list. Read-only.'`

### Step 7: Verdicts (reasoning only, no delegation)

Apply [verdict rules](references/verdict-rules.md) for the chosen audience and the user's personal rules; that file is the only source for confirmation and verdicts. In short:

1. A finding is **confirmed** when both readings report the same risk type for the photo, when it comes from metadata, when a vision-only type (KEY, FAC) is answered yes, or when Step 4 returned the photo for a person named in a personal rule. Otherwise it is **possible**. Positions come from the visual reading when it has one.
2. Each finding takes its severity for the audience: Red, Amber or Info.
3. Verdict per photo, first match wins: **Keep private** (the Keep private tag with a Public or Marketplace audience, a confirmed Red, or a personal-rule match); **Check this** (a possible Red or Amber, a reading or the metadata that did not complete for this photo, or a personal rule that could not be verified); **Fix first** (only confirmed Amber findings, each with its fix); **Clear** (nothing above Info, and both readings plus metadata completed for this photo).
4. A photo is never Clear on a single reading.

Never report a finding that no expert returned, and never drop one that an expert did return.

### Step 8: Report and one consolidated approval (nothing has been written yet)

Show the report as laid out in [report format](references/report-format.md): the summary line ("12 photos checked for a public post: 6 Clear, 2 Fix first, 1 Check this, 3 Keep private"), then every photo that is not Clear with its findings, positions, readings and fix, then videos not checked and photos left out by the cap.

Then offer the write plan and ask the user to approve, change or decline it:

- **a. Share-ready album (on by default, offered only when at least one photo is Clear)**: a new album {ALBUM_NAME} with only the Clear photos. Photos the user re-classifies as Clear after looking at a Check this photo may be added.
- **b. Keep private tags (on by default, offered only for Keep private photos that do not carry the tag yet)**: add the tag Keep private to these photos, so future public checks settle them at once. The tag shows in File Manager that a photo is sensitive, never why.
- **c. Official guidance (read-only)**: for example how to share without location data, or how to remove a photo from a shared album.

Wait for an explicit answer. If the user declines, nothing is written and the report stays in the conversation. The NAS then asks its own approval for each write call; tell the user this is expected and let the user choose the approval option; Before You Share never recommends a broader one.

### Step 9: Create the share-ready album (photo-agent, after approval)

`delegate --target photo-agent --instruction 'Create a new album named {ALBUM_NAME} that contains exactly these photos and nothing else: {CLEAR_PHOTOS}. You may look up each listed photo in the library to add it, but never add a photo that is not in this list and never fill the album from a text query or search. If an album with this name already exists, do not change it; stop and say so. Do not change, move or share any photo. Return the real album name, the number of photos added, and any photo that could not be added with the reason.'`

If the album cannot be created with exactly these photos, report it and list the Clear photos instead; never fall back to a broader search.

### Step 10: Remember Keep private photos (file-agent, after approval)

`delegate --target file-agent --instruction 'Make sure the file tag Keep private exists, creating it only if it is missing. Then add the tag Keep private to these files, in as few requests as possible: {PRIVATE_PHOTOS}. Do not remove or change any other tag, and do not move, rename or edit any file. Return for each file whether the tag was added, or failed with the reason.'`

Never run Step 9 or Step 10 with an empty list. Tags are added only to files the current user can change; if a tag cannot be added to a photo someone else added, report it and leave it.

### Step 11: Official guidance (knowledge-agent, read-only, optional)

`delegate --target knowledge-agent --instruction 'Using only official UGREEN NAS documentation, explain step by step: {GUIDANCE_TOPIC}. Say clearly when the official documentation does not cover a step.'`

Before You Share never edits images, strips metadata, or changes sharing or permissions itself; it shows the official steps so the owner decides.

## Shared-album audit

### Step A1: Albums the user has shared (photo-agent, read-only)

`delegate --target photo-agent --instruction 'List the albums that the current user created and shared with other people, with album name, number of photos and, if known, whether they are shared with NAS accounts or through a link. Do not include albums that other people shared with the current user. Read-only. If the user has not shared any album, return an empty list and say so.'`

Show the list and let the user choose albums, or take all of them. Ask who can see them: Private is the default for albums shared with NAS family accounts; use Public when an album is shared through a link or with people the user does not know well.

### Step A2: Check the shared photos

Run Step 1 once per chosen album in {SHARED_ALBUMS}, with {SELECTION} set to that album name, and keep the album name with each returned photo; stop when 20 photos in total are collected, newest first. Then run Steps 2 to 7. The report adds, for each risky photo, the album it is shared in. In Step 8 the write plan offers only option b (Keep private tags) and option c with the topic "how to remove a photo from a shared album or change who can see the album". Never change the shared albums themselves, and say that a Keep private tag does not remove a photo from an album.

# Completion and failure

Report a result only after the delegated expert returns `completed` with the data the step needs.

| Status | What Before You Share does |
| --- | --- |
| `completed` | Use only the returned data. A photo missing from a reading's answer counts as a failed reading for that photo, so it cannot be Clear. |
| `failed` | Stop the steps that depend on this result. Step 1 is required. If Step 3, 5 or 6 fails for some photos or a whole batch, those photos become Check this, labelled "not fully checked". If Step 2 fails, read every photo and say earlier marks could not be checked. Say which step failed and offer to retry that step only. |
| `cancelled` | Stop the run and say what was completed before the cancellation. Nothing is undone or redone without asking. |
| `waiting_user` | Relay the expert question in plain language and resume with the answer. If an expert asks for a password, a PIN or account access, do not relay it: tell the user to open the item themselves, and mark the photo Check this. |
| `waiting_approval` | Tell the user the NAS is asking to approve a specific write. Wait. If it is declined, treat that write as cancelled and keep the report. Never reword or split a task to avoid an approval. |

**Empty results.** If Step 1 returns no results, say that no photos matched the selection, repeat the selection used, and stop; never widen the search on your own. If the user has no shared albums in Step A1, say so and stop. Zero findings is good news: report a photo as Clear only when both readings and the metadata completed for it.

**Partial results.** When a cap leaves photos out, a step fails for some photos, or videos are present, finish the report, label it partial, and list exactly what was not checked.

**Done means.** The run is complete when the user has seen the report and either declined the write plan or every approved write returned `completed`. The final message gives the verdict counts, the album name and photo count, the photos tagged, any write that failed, and anything not checked.

# Safety and privacy

- The Skill makes no external calls and sends nothing outside the NAS; every analysis is delegated to the NAS's own experts.
- Findings are types and positions. Numbers, codes, names, addresses, place names, coordinates and document contents are never transcribed into chat, album names or tags. Payment cards are reported only as "payment card visible".
- Everything is read-only until the user approves one consolidated plan, and the NAS then asks its own approval for each write. Photos are never moved, edited, deleted or shared by the Skill.
- Only the current user's own photos and the albums they created and shared are checked; albums shared with the user by others are never analyzed.
- A photo is never called Clear on one reading. When unsure, the verdict is Check this and the user decides.
- Full rules: [privacy and safety](references/privacy-and-safety.md).

# Response style

Reply in the language of the user. Keep verdict names, risk codes and the tag name in English so later checks can match them. Lead with the summary line, then the photos that need attention, most severe first. Be specific about where the problem is and what to do, and never lecture.

# References

- [Verdict rules](references/verdict-rules.md): risk types, audience severities, confirmation and verdict logic, fixes; read before Step 7.
- [Report format](references/report-format.md): chat report and write plan; read before Step 8.
- [Privacy and safety rules](references/privacy-and-safety.md): read at the start of every run.
- [Validation plan](references/validation-plan.md): specimen photo sets, core and edge test cases with expected results.
- [Disclosures](references/disclosures.md): third-party components, AI tools and originality statement.
