# Submission checklist

## Round 1 (deadline: Sunday 2026-11-15, 11:45 pm Pacific Time)

- [ ] Register on [ugreenhackathon.devpost.com](https://ugreenhackathon.devpost.com/) with "Join Hackathon" (individual entrant, or a team of up to three with one Representative).
- [ ] Confirm eligibility for your country of residence in the official rules.
- [ ] "Enter a Submission" and fill the form:
  - [ ] Project name, tagline and story: copy from [devpost-story.md](devpost-story.md).
  - [ ] Track: **Open Innovation**.
  - [ ] Project Proposal PDF: upload [proposal.pdf](proposal.pdf) (under 500 words, under 1 MB).
  - [ ] Pre-test Skill Package ZIP: upload [../dist/before-you-share.zip](../dist/before-you-share.zip) (6 Markdown files, about 16 KB of the 10 MB limit).
  - [ ] Optional links: this repository and the interactive simulation site.
- [ ] Rebuild both files after any edit: `node tools/build.mjs --kit path/to/uliya-skill-kit --strict` and `python tools/make_proposal.py`.
- [ ] Submit before the deadline; drafts can be saved and edited until then. Do not delete Round 1 materials later.

## Round 2 (only if selected; invitations on 2026-11-21)

- [ ] Read the email with the assigned testing day, device, credentials and private submission link (sent to the Representative only).
- [ ] Before the testing day: run `python tests/specimens/generate.py` and prepare the Beach day album and Hazard set as described in [tests/specimens/README.md](../tests/specimens/README.md).
- [ ] Testing day: follow the runbook in the [validation plan](../skill/before-you-share/references/validation-plan.md) and record with the [video script](../docs/video-script.md).
- [ ] Back up chat outputs and recordings before the testing window ends.
- [ ] Upload the final video to YouTube as public, under 3 minutes, English narration or full English subtitles.
- [ ] Submit the final Skill ZIP (same Skill, same standard) and the video link by 2026-11-30, 11:45 pm PT.
