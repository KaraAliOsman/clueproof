---
title: Clueproof
subtitle: Project Proposal · UGREEN Hackathon 2026 on AI NAS · Track: Open Innovation
tagline: Every photo leaves clues. Clueproof finds them first, privately, on your NAS.
meta: "Skill: clueproof · Official UGOS Skill checker: static-pass, 0 errors, 0 warnings · Repository and interactive demo: github.com/KaraAliOsman/clueproof"
---

<!-- answers:start -->

## 1. What does your Skill do?

With one sentence, Clueproof shows privately on the NAS what a stranger could learn from your photos, and fixes it with one yes.

## 2. Who is your target user, and what is their problem?

Families and creators who share photos. About 3 in 4 parents share content about their children, and 21 to 23% of them post tagged locations (DPC and CNIL, 2026). One photo shows a house number, another a school crest, another a boarding pass: together they reveal where a family lives, studies and travels. A cloud AI check would upload exactly that.

## 3. What is your solution?

"Is this safe to post?" gives each photo a verdict (Clear, Fix first, Check this, Keep private) and, with one yes, a ready-to-share album of the clean ones. "What could a stranger find out about us?" builds the Stranger's File: eight pages (home, children, car, travel, identity, access, health, other people) filled from shared albums, its worst combinations, and a clean copy to share instead.

## 4. What is the main user flow?

The user asks; Clueproof defaults to today's photos and a public audience, reports stored GPS at once, reads each photo twice, answers in three lines and asks one question. Yes creates the album and keeps risky photos in a private album for next time.

## 5. How is your idea different from existing tools or common AI solutions?

Existing tools strip metadata or blur one photo at a time. Clueproof reasons across photos (the mosaic effect), calls a photo Clear only after two independent clean readings plus clean metadata, and never repeats a clue's value: it says "house number, top right", never the number.

## 6. Which UGREEN AI NAS features does your Skill use, and at which step?

Photo search selects photos and shared albums (Steps 1, F1). The AI index shortlists photos with text, cards or locations (F2). EXIF metadata reveals location (3). Face recognition applies rules like "never show Mia's face publicly" (4). On-device OCR and vision read each photo (5, 6). A private album remembers risky photos (2, 10); albums and official guidance finish (9, 11).

## 7. What is your technical approach?

The parent delegates self-contained tasks to photo-, file- and knowledge-agent, passing real file paths through named slots. Text and visual readings are separate delegations; caps fit local models (20 photos per run, batches of 5). Stranger's File pages use confirmed findings only. Read-only until one yes; photos are never edited, moved, deleted or shared. No external calls. All five delegation states handled.

## 8. What have you built so far? What is not built yet? What still needs testing on a NAS?

Built: the complete Skill (SKILL.md, six references) passing the official checker, 20 real licensed test photos with expected results, an interactive demo and a launch film; nothing in scope is missing. NAS testing: expert outputs (index shortlist, face matches, exact-item albums), latency, approval prompts.

## 9. How will you test your Skill if you become a Finalist?

Core 1: "Is Summer 2025 safe to post?" answers 6 ready, 4 clues, 2 fixes, quoting no value. Core 2: "What could a stranger find out about us?" fills 5 of 8 pages and offers a clean copy. Edge: a failed visual batch makes those photos Check this, never Clear.

## 10. What are the known limits, risks, or outside dependencies of your Skill?

A second look, not a guarantee: tiny text or reflections can slip through. Local vision limits runs to 20 photos. It cannot edit images, strip metadata or unshare; official steps cover that. Videos are not checked.

<!-- answers:end -->

## Third-party components, licenses and AI tools

- **Third-party components and open source libraries:** none. The package contains only original Markdown; no libraries, scripts, binaries, models, datasets, external services or downloads.
- **Platform:** registered UGREEN AI NAS experts and the capability catalog of the official UGOS Skill Creation Tool (uliya-skill-kit 0.7.3, catalog 2.0.0), under UGREEN's Hackathon terms.
- **AI tools:** Claude (Anthropic) via Claude Code for research, drafting and review; the UGOS Skill Creation Tool for capability lookup and static checks.
- **Test data:** real, freely licensed Wikimedia Commons photographs, credited in the repository; documents are official specimens or samples; no identifiable minors.
- **Source cited:** Data Protection Commission (Ireland) and CNIL, Sharenting Research, 2026.
