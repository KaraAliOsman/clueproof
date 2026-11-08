# Report format

## First result (Step 3)

As soon as the metadata step completes, show one line while the readings run, for example: "GPS location stored in 1 of 12 photos. Reading each photo twice with the NAS's local models now; this takes a few minutes."

## Chat report (Step 8)

Start with one summary line, then the photos that need attention, most severe verdict first, then what was not checked. Clear photos are counted, not listed, unless the user asks.

Each photo line gives: verdict, file name, finding in plain words, position, which readings saw it, and the fix. Never quote the number, code, name, address, place name or coordinates found.

Example with the fictional specimen album "Beach day", audience Public:

```text
12 photos checked for a public post: 6 Clear, 2 Fix first, 1 Check this, 3 Keep private.

Keep private · B07-house-front.jpg · House number visible, top right (text and vision) · Crop the top right, or leave this photo out.
Keep private · B09-boarding-pass.jpg · Boarding pass with a barcode, middle center (text and vision) · The code can reveal your booking; leave it out.
Keep private · B10-backpack.jpg · School crest and name label on a backpack, middle left (text and vision) · Crop or blur the label and crest.
Check this · B12-parking.jpg · Possible license plate, bottom left (vision only, text unreadable) · Look at the bottom left before sharing.
Fix first · B01-beach-wide.jpg · GPS location stored in the file; anyone who gets the original file can see where it was taken · Share a copy without location.
Fix first · B08-car.jpg · License plate readable, bottom center (text and vision) · Crop or blur the plate.

Not checked: none. A second look is not a guarantee; tiny text and reflections can still slip through.
```

Location findings say only that GPS data is stored; place names and coordinates are never shown or saved.

When a personal rule matched, the line names the rule as the user wrote it ("your rule: never show Mia's face publicly") and nothing else about the person.

## Write plan (Step 8)

List each option with what it will do and its default, then ask one question:

```text
Ready to write, after your approval:
a. Create the album "Share-ready - Beach day - 2026-11-20" with the 6 Clear photos (on)
b. Tag 3 photos Keep private so future public checks settle them at once (on)
c. Show the official steps to share without location data (read-only)
Approve all, change something, or stop?
```

After the user changes a Check this photo to Clear, it may join the album; record that the user decided it.

## Album name

`Share-ready - <selection label> - <YYYY-MM-DD>`, for example `Share-ready - Beach day - 2026-11-20`. The label is the album name or the user's own words, shortened to 40 characters, without street names, house numbers or full names of people.

## Shared-album audit report

Same layout, grouped by album, with the album name before its photos and one closing line per album, for example "Shared by you · 2 photos need attention". End by offering option c with the topic "how to remove a photo from a shared album or change who can see the album", and say that a Keep private tag does not remove a photo from an album.
