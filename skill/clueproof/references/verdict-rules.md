# Verdict rules

These rules are the only source for confirming findings and giving verdicts. They are deliberately asymmetric: a single reading is enough to raise a concern, but a photo is called Clear only when every check completed and found nothing that matters for the audience.

## Audiences

| Audience | Who can see the photo | Typical use |
| --- | --- | --- |
| Private | Family or friends the user knows well | NAS family accounts, a family chat, grandparents |
| Public | Anyone, including people who reshare it | Social media, public links, communities, group chats with people the user does not know well (a class or neighborhood group) |
| Marketplace | Strangers who may contact or visit you | Selling or renting something online |

When the user does not say, use Public and tell the user.

## Risk types and severity

| Code | What gives it away | Private | Public | Marketplace | Suggested fix |
| --- | --- | --- | --- | --- | --- |
| LOC | GPS location stored in the file | Info | Amber | Amber | Share a copy without location data; NAS share links and file transfers send the original file with its location (Step 11 shows the official way when one exists) |
| ADR | House number or a readable postal address | Info | Red | Red | Crop or blur the area, or choose another photo |
| PLT | Readable vehicle license plate | Info | Amber | Amber | Crop or blur the plate |
| IDD | Identity document or ID card | Amber | Red | Red | Leave the photo out |
| PAY | Bank or payment card | Red | Red | Red | Leave the photo out; if it was already shared, contact the bank |
| TKT | Boarding pass, travel or event ticket, or a booking barcode or QR code | Amber | Red | Red | Crop out the code; codes can reveal bookings and names |
| MAL | Mail or package label with a name or address | Info | Red | Red | Crop or blur the label |
| SCR | Screen showing messages, email, accounts or codes | Amber | Red | Red | Crop the screen out |
| COD | Note with a password, Wi-Fi key, PIN or code | Red | Red | Red | Leave the photo out; change the code if it was already shared |
| KEY | House or car keys shown clearly enough to see their shape | Info | Amber | Amber | Crop or blur; clear photos of keys can be used to copy them |
| SCH | School name, logo, crest or name label on clothing or a bag | Info | Red | Red | Crop or blur the label or crest |
| MED | Prescription label or medical wristband | Amber | Red | Red | Crop or blur the label |
| FAC | Faces of people in the background who are not the subject | Info | Amber | Amber | Ask those people first, or crop them out |
| MET | Owner, artist, copyright or camera serial fields filled | Info | Info | Amber | Share a copy without metadata; only an owner, artist or copyright name counts toward the Stranger's File |
| RUL | A personal rule matches (a named person in a photo for an audience the rule covers) | As the rule says | Red | Red | Leave the photo out |

A rule such as "never show Mia's face publicly" covers Public and Marketplace. A rule that names every audience also makes the photo Keep private for Private.

## Which readings can confirm each type

| Code | Text reading (Step 5) | Visual reading (Step 6) | Other evidence |
| --- | --- | --- | --- |
| LOC, MET | not used | not used | Metadata (Step 3) is factual: always confirmed |
| ADR | house number or postal address | ADR | none |
| PLT | vehicle license plate | PLT | none |
| IDD | identity or document number | IDD | none |
| PAY | payment card number | PAY | none |
| TKT | flight, booking or ticket code | TKT | none |
| MAL | person name together with house number or postal address | MAL | none |
| SCR | messages, email or an account on a screen | SCR | none |
| COD | password, Wi-Fi key, PIN or one-time code | COD | none |
| SCH | school or club name | SCH | none |
| MED | medicine or prescription label | MED | none |
| KEY | not visible to text reading | KEY | Vision-only type: a clear "yes" confirms it |
| FAC | not used | FAC | Vision-only type: a clear "yes" confirms it |
| RUL | not used | not used | Step 4 returned the photo for a person named in the rule |

## Confirmed and possible

- **Confirmed**: both readings report the same type for the photo; or a metadata finding; or a vision-only type (KEY, FAC) answered "yes"; or a personal-rule match from Step 4.
- **Possible**: only one reading reports a two-reading type, or the visual reading answered "unsure".
- Positions are taken from the visual reading when it has one, otherwise from the text reading, otherwise "position unknown".

## Verdict per photo

Apply in this order; the first match wins.

1. **Keep private**: the photo is in a Keep private album (Step 2) and the audience is Public or Marketplace; or it has a confirmed Red finding; or it matches a personal rule.
2. **Check this**: a possible Red or Amber finding; or the text reading, visual reading or metadata did not complete for this photo ("not fully checked"); or Step 4 could not check this photo although the library knows the person named in the rule.
3. **Fix first**: only confirmed Amber findings remain; list one fix per finding.
4. **Clear**: no finding above Info, and the text reading, the visual reading and the metadata all completed for this photo.

Info findings never change a verdict, but they are listed in the details so the user learns what the photo contains. With a Private audience, being in a Keep private album is listed as Info.

**Location only.** A Fix first photo whose only finding above Info is LOC goes into the ready-to-share album together with the Clear photos. The answer gives the location fix once for all of them: "N still carry GPS location: post them through an app that removes location, not as a NAS share link." In the Stranger's File, LOC still fills its page, because a shared NAS album hands out the original files.

## What the verdicts promise

A verdict is a careful second look, not a guarantee. Clear means two independent readings and the metadata found nothing that matters for this audience. Reflections, very small text and context only a person would recognize can still slip through; the report says so once, briefly, at the end.
