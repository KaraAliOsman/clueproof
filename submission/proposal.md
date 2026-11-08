---
title: Before You Share
subtitle: Project Proposal · UGREEN Hackathon 2026 on AI NAS · Track: Open Innovation
tagline: Your photos say more than you think. Before You Share reads them first, privately, on your NAS.
meta: "Skill: before-you-share · Official UGOS Skill checker: static-pass, 0 errors, 0 warnings · Repository and interactive simulation: github.com/KaraAliOsman/before-you-share"
---

<!-- answers:start -->

## 1. What does your Skill do?

It privately checks photos on the NAS before sharing, shows what each gives away for the chosen audience, and builds a share-ready album of the cleared ones.

## 2. Who is your target user, and what is their problem?

Families and creators who share photos every week. About 3 in 4 parents share content about their children, and 21 to 23% of them post tagged locations (DPC and CNIL, 2026). Photos also show house numbers, plates, boarding-pass codes, school crests and IDs. Shared photos cannot be recalled; a cloud AI check would upload exactly what should stay private.

## 3. What is your solution?

A privacy check with fourteen risk types and three audiences (Private, Public, Marketplace). Each photo gets a verdict (Clear, Fix first, Check this, Keep private) with the position and fix of every finding. Personal rules such as "never show Mia's face publicly" use the NAS's face recognition. Approval creates a share-ready album and Keep private tags; an audit covers shared albums.

## 4. What is the main user flow?

"Check the beach photos before I post them" resolves the photos, reports stored GPS at once, applies tags and personal rules, runs separate text and visual readings, and gives verdicts per batch. One approval creates the album and tags. "What do my shared albums give away?" audits them.

## 5. How is your idea different from existing tools or common AI solutions?

Existing tools strip metadata or blur faces; none checks, privately and per audience, what the image itself shows. One reading raises a concern; Clear needs two independent clean readings plus clean metadata. Findings are types and positions, so secrets are never transcribed.

## 6. Which UGREEN AI NAS features does your Skill use, and at which step?

Photo search and albums select the set and list shared albums (Steps 1, A1). File tags remember Keep private photos (2, 10). EXIF metadata reveals location (3). Face recognition applies personal rules (4). On-device OCR and vision read every photo (5, 6). Album creation and official guidance finish (9, 11).

## 7. What is your technical approach?

The parent delegates self-contained tasks to photo-, file- and knowledge-agent, passing real upstream file paths through named slots. Text and visual readings are separate delegations; caps fit local models (20 photos per run, batches of 5). Inputs: selection, audience, personal rules. Read-only until one approval; photos are never edited, moved, deleted or shared. Models: the NAS's own OCR and vision; no external calls. All five delegation states handled.

## 8. What have you built so far? What is not built yet? What still needs testing on a NAS?

Built: the complete Skill (SKILL.md, five references) passing the official checker, 22 fictional specimen photos with expected verdicts, an interactive simulation. Not built: nothing in scope. NAS testing: real expert outputs (paths, face matches, exact-item albums), vision latency, approval prompts.

## 9. How will you test your Skill if you become a Finalist?

Core 1: Beach day for a public post gives 6 Clear, 2 Fix first, 1 Check this, 3 Keep private, quoting no number or address. Core 2: for the family it gives 11 Clear, 1 Fix first; a repeat run flags tagged photos instantly. Edge: a failed visual batch yields Check this, never Clear.

## 10. What are the known limits, risks, or outside dependencies of your Skill?

A second look, not a guarantee: tiny text or reflections can slip through. Local vision speed limits runs to 20 photos by default. It cannot edit images or strip metadata; fixes are suggestions with official steps. Videos are not checked.

<!-- answers:end -->

## Third-party components, licenses and AI tools

- **Third-party components and open source libraries:** none. The package contains only original Markdown; no libraries, scripts, binaries, models, datasets, external services or downloads.
- **Platform:** registered UGREEN AI NAS experts and the capability catalog of the official UGOS Skill Creation Tool (uliya-skill-kit 0.7.3, catalog 2.0.0), under UGREEN's Hackathon terms.
- **AI tools:** Claude (Anthropic) via Claude Code for research, drafting and review; the UGOS Skill Creation Tool for capability lookup and static checks.
- **Data:** testing uses generated SPECIMEN images, phone photos of printed fictional props and consenting testers; no one else's personal data.
- **Source cited:** Data Protection Commission (Ireland) and CNIL, Sharenting Research, 2026.
