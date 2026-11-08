# Devpost project story

Copy each section into the matching field of the Devpost submission form.

**Project name:** Clueproof

**Tagline:** Every photo leaves clues. Clueproof finds them first, privately, on your NAS.

**Track:** Open Innovation

## Inspiration

Picture an ordinary summer album shared with friends and a few people you barely know. One photo shows the house number on your front door. Another shows the crest on your child's school blazer. A third has a boarding pass on the table, and the first one still carries the GPS position of where it was taken. None of them looks dangerous. Together, they tell a stranger where you live, where your children study and when the house will be empty.

About 3 in 4 parents share content about their children online, and 21 to 23% of those who share post content with a location tagged (DPC and CNIL, 2026). Every tool we found looks at one photo at a time and mostly at metadata. Nobody shows what a stranger could piece together from a whole shared album, and checking private photos with a cloud AI would upload exactly what you want to protect. A family's photos already live on the NAS, and its AI has already indexed them. The check belongs there.

## What it does

Clueproof answers two questions, one sentence each, with no setup.

- **"Is this safe to post?"** Clueproof takes today's photos, assumes a public audience and says so. It reads every photo twice and answers in three lines: how many are ready to post, which ones give clues away (house number, boarding pass, school crest, address label) and which need a fix (license plate, keys). One yes creates a "Ready to share" album and a private "Keep private" album, so those photos are flagged instantly next time.
- **"What could a stranger find out about us?"** Clueproof reads the albums you have shared and fills the **Stranger's File**: eight pages a stranger would try to fill. They cover where you live, your children, your car, where you go, who you are, how to get in, your health, and other people. It shows how many pages are filled ("5 of 8"), the **worst combinations** ("where your children live and study"), and offers a clean copy of the album with only the photos that fill no page, to share instead.

It covers fourteen clue types: GPS location, house numbers, address labels, license plates, boarding passes and barcodes, school crests and name labels, ID and payment cards, screens with accounts, notes with passwords, keys, prescription labels, bystanders, and owner metadata. Personal rules such as "never show Mia's face publicly" are checked with the NAS's own face recognition.

## How we built it

Clueproof is a Markdown-only Skill built with the official UGOS Skill Creation Tool. The parent workflow only delegates self-contained tasks to three registered NAS experts and passes real file paths through named slots:

- **photo-agent** selects photos and shared albums and shortlists likely clues from the existing AI index. It reads metadata and applies personal rules with face recognition. It runs the text reading (OCR) and, in a separate delegation, the visual reading (vision model). It also creates the albums.
- **file-agent** resolves folders the user names.
- **knowledge-agent** fetches the official UGOS steps to share without location or to stop sharing an album.

The design rules are:

- **Two witnesses:** one reading is enough to raise a concern, but a photo is Clear only when both readings and the metadata complete clean.
- **No echo:** Clueproof says "house number, top right", never the number.
- **Location only:** photos whose only clue is GPS still go into the album, with one note, so real phone photos are not all flagged.
- **One yes:** read-only until the user says yes, and the NAS still asks its own approval for each write.

Every delegation handles completed, failed, cancelled, waiting_user and waiting_approval. The package passes the official checker with status static-pass, 0 errors and 0 warnings. We tested the logic on 20 real, freely licensed Wikimedia Commons photos with expected results, and built an interactive demo and a launch film.

## Challenges we ran into

- **Our first idea was taken.** We first built an emergency-document binder, then found about ten near-identical public projects. We pivoted to the gap nobody covered.
- **Not becoming the leak.** An AI that reads secrets aloud is a new leak, so every instruction asks for the type and position of a clue, never its value. Even our public demo pixelates real people's plates and card digits.
- **Real phone photos carry GPS.** A naive rule would flag every photo; "location only" keeps the answer useful.
- **One yes should mean one yes.** We replaced per-file tags with a private album, cutting the NAS approval prompts from up to six to two.
- **Slow local models.** We read 20 photos per run in batches of 5, give the GPS count in seconds, and show progress.

## Accomplishments that we're proud of

- The Stranger's File: a privacy check that reasons across photos, not one at a time.
- A design that never needs to repeat a secret to warn you about it.
- A clean pass of the official checker.

## What we learned

The most dangerous clues are the ones that look harmless on their own. A privacy tool has to think like the stranger, and talk like a friend.

## What's next

- Validate expert outputs on real hardware and tune the visual questions.
- Shared folders and File Manager share links.
- Region-specific cues (plate formats, uniforms, ID layouts) built with local communities.

## Built with

UGREEN AI NAS, UGOS, UGOS Skill Creation Tool, Markdown, Claude Code
