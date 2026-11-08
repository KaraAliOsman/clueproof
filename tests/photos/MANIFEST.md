# Test photo manifest

Expected results for the 20 real photos. Severity per risk is shown as Public/Private. Verdict: **Keep private** if any finding is Red, **Fix first** if only Amber, **Clear** otherwise.
Positions use a 3x3 grid of the image. Normalized boxes `[x, y, w, h]` are in `docs/assets/photos/manifest.json`. LOC (S01) and MET (H08) exist only in EXIF and have no image area.

| File | Set | Risk codes | Position | Public verdict | Private verdict | Severities (Public/Private) |
|---|---|---|---|---|---|---|
| S01-beach.jpg | Summer 2025 | LOC | LOC: EXIF only | Fix first | Clear | LOC Amber/Info |
| S02-sunset.jpg | Summer 2025 | none | - | Clear | Clear | - |
| S03-ice-cream.jpg | Summer 2025 | none | - | Clear | Clear | - |
| S04-dog-beach.jpg | Summer 2025 | none | - | Clear | Clear | - |
| S05-house-number.jpg | Summer 2025 | ADR | ADR: top center | Keep private | Clear | ADR Red/Info |
| S06-license-plate.jpg | Summer 2025 | PLT | PLT: bottom left | Fix first | Clear | PLT Amber/Info |
| S07-boarding-pass.jpg | Summer 2025 | TKT | TKT: center | Keep private | Fix first | TKT Red/Amber |
| S08-school-crest.jpg | Summer 2025 | SCH | SCH: center | Keep private | Clear | SCH Red/Info |
| S09-seagull.jpg | Summer 2025 | none | - | Clear | Clear | - |
| S10-parcel-label.jpg | Summer 2025 | MAL | MAL: top left | Keep private | Clear | MAL Red/Info |
| S11-house-key.jpg | Summer 2025 | KEY | KEY: center | Fix first | Clear | KEY Amber/Info |
| S12-mountain-lake.jpg | Summer 2025 | none | - | Clear | Clear | - |
| H01-id-card.jpg | Hazard set | IDD | IDD: center | Keep private | Fix first | IDD Red/Amber |
| H02-payment-card.jpg | Hazard set | PAY | PAY: center | Keep private | Keep private | PAY Red/Red |
| H03-chat-screen.jpg | Hazard set | SCR | SCR: center | Keep private | Fix first | SCR Red/Amber |
| H04-wifi-password.jpg | Hazard set | COD | COD: center | Keep private | Keep private | COD Red/Red |
| H05-prescription.jpg | Hazard set | MED | MED: middle right | Keep private | Fix first | MED Red/Amber |
| H06-plaza.jpg | Hazard set | FAC | FAC: bottom left | Fix first | Clear | FAC Amber/Info |
| H07-calculator.jpg | Hazard set | none | - | Clear | Clear | - |
| H08-coffee.jpg | Hazard set | MET | MET: EXIF only | Clear | Clear | MET Info/Info |

## Severity table

| Code | Meaning | Public | Private |
|---|---|---|---|
| LOC | GPS location | Amber | Info |
| ADR | House number | Red | Info |
| PLT | License plate | Amber | Info |
| TKT | Boarding pass | Red | Amber |
| SCH | School crest | Red | Info |
| MAL | Shipping label | Red | Info |
| KEY | House key | Amber | Info |
| IDD | Identity card | Red | Amber |
| PAY | Payment card | Red | Red |
| SCR | Chat screen | Red | Amber |
| COD | Written password | Red | Red |
| MED | Prescription label | Red | Amber |
| FAC | Bystander faces | Amber | Info |
| MET | Owner metadata | Info | Info |
