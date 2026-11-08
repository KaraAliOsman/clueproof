# Devpost project story

Copy each section into the matching field of the Devpost submission form.

**Project name:** Before You Share

**Tagline:** Your photos say more than you think. Before You Share reads them first, privately, on your NAS.

**Track:** Open Innovation

## Inspiration

Picture an ordinary beach album posted publicly: the house number on the front door in the last photo of the day, a boarding pass on the towel with its barcode, the school crest on a child's backpack, and the GPS position stored inside the first photo. Nobody means to share any of that, and nobody checks twelve photos pixel by pixel before tapping "share".

Photos leak in ways people rarely notice, and once a photo is out it cannot be recalled. The obvious fix, asking a cloud AI to check them, would upload exactly what you are trying to protect. A family's photos already live on the NAS, and its AI has already indexed them. The check belongs there.

## What it does

- **Check before sharing:** "Check the beach photos before I post them publicly." Every photo gets a verdict for the chosen audience (Private, Public or Marketplace): **Clear**, **Fix first**, **Check this** or **Keep private**, with the exact position of each finding and a fix ("house number visible, top right; crop it or leave this photo out").
- **Fourteen risk types:** GPS location, house numbers and addresses, license plates, ID documents, payment cards, boarding passes and barcodes, mail and package labels, screens with messages or accounts, notes with passwords or Wi-Fi keys, keys, school crests and name labels, prescription labels, bystanders' faces, and owner or camera-serial metadata.
- **Personal rules with local face recognition:** "never show Mia's face publicly" is checked by the NAS's own people index, so no face is uploaded anywhere to be matched.
- **Share-ready album:** after one approval, a new album with only the Clear photos.
- **Memory that respects the audience:** photos marked Keep private are tagged, so later public checks settle them at once, while a family check still reads them normally.
- **Shared-album audit:** the same check on albums you already shared, with the official steps to fix what it finds.

## How we built it

Before You Share is a Markdown-only Skill built with the official UGOS Skill Creation Tool. The parent workflow only delegates self-contained tasks to three registered NAS experts and passes real upstream file paths through named slots:

- **photo-agent** resolves the photo set, reads metadata, applies personal rules with the library's own face recognition, runs the text reading (OCR) and, in a separate delegation, the visual reading (vision model), creates the share-ready album and lists shared albums.
- **file-agent** checks and adds the Keep private tag and resolves folders.
- **knowledge-agent** fetches official UGOS guidance, such as how to share without location data or remove a photo from a shared album.

Design rules: the rule is asymmetric, so one reading is enough to raise a concern but Clear needs two independent clean readings plus clean metadata. Findings are reported as types and positions, so numbers, codes, names and addresses are never transcribed. Everything is read-only until one consolidated approval, and the NAS asks again before each write. Photos are never edited, moved, deleted or shared, and only the user's own photos and albums are checked. Every delegation handles completed, failed, cancelled, waiting_user and waiting_approval.

The package passes the official checker with status static-pass, 0 errors and 0 warnings. We also generated 22 fictional SPECIMEN photos with expected verdicts for every core and edge case, and built an interactive simulation.

## Challenges we ran into

- **Our first idea was taken.** We first built a family emergency-document binder, then found about ten near-identical public projects. We pivoted to the gap nobody covered.
- **Not becoming the leak.** An AI that reads secrets aloud is a new leak, so every instruction asks only for the type and position of a finding.
- **Trusting "clear".** A missed leak is worse than a false alarm, so Clear requires two independent readings and complete metadata.
- **Slow local models.** We sized runs to 20 photos, read them in batches of 5 with verdicts per batch, and show the GPS result first so the user sees progress in seconds.

## Accomplishments that we're proud of

- A clean pass of the official checker on the first run.
- Audience-aware verdicts: the same house number is fine for grandma and wrong for the internet.
- A design that never needs to see a secret in plain text to warn you about it.

## What we learned

For a privacy tool, how you report a finding matters as much as finding it.

## What's next

- Validate expert outputs on real hardware and tune the visual questions.
- Folder and document checks before sharing a shared folder.
- Region-specific cues (plate formats, school uniforms, ID layouts) built with local communities.

## Built with

UGREEN AI NAS, UGOS, UGOS Skill Creation Tool, Markdown, Claude Code
