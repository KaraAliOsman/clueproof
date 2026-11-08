"""Build submission/proposal.pdf from submission/proposal.md.

    python tools/make_proposal.py            count words, render HTML, print PDF
    python tools/make_proposal.py --count    only count words

Rules enforced (UGREEN Hackathon 2026, Round 1):
  * the ten answers must total at most 500 English words (question headings excluded)
  * the PDF must be at most 1 MB
PDF rendering uses a locally installed Chrome or Edge in headless mode.
"""

from __future__ import annotations

import html
import re
import shutil
import subprocess
import sys
from pathlib import Path

import markdown

ROOT = Path(__file__).resolve().parent.parent
SRC = ROOT / "submission" / "proposal.md"
HTML_OUT = ROOT / "submission" / "proposal.html"
PDF_OUT = ROOT / "submission" / "proposal.pdf"
WORD_LIMIT = 500
PDF_LIMIT = 1024 * 1024

BROWSERS = [
    r"C:\Program Files\Google\Chrome\Application\chrome.exe",
    r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe",
    "google-chrome",
    "chromium",
    "msedge",
]


def split_front_matter(text: str) -> tuple[dict[str, str], str]:
    match = re.match(r"^---\n(.*?)\n---\n", text, re.S)
    if not match:
        return {}, text
    meta = {}
    for line in match.group(1).splitlines():
        key, _, value = line.partition(":")
        meta[key.strip()] = value.strip().strip('"')
    return meta, text[match.end():]


def count_answers(body: str) -> list[tuple[str, int]]:
    section = body.split("<!-- answers:start -->", 1)[1].split("<!-- answers:end -->", 1)[0]
    counts: list[tuple[str, int]] = []
    current = None
    words = 0
    for line in section.splitlines():
        if line.startswith("## "):
            if current:
                counts.append((current, words))
            current, words = line[3:].strip(), 0
            continue
        words += sum(1 for token in line.split() if re.search(r"[A-Za-z0-9]", token))
    if current:
        counts.append((current, words))
    return counts


CSS = """
@page { size: A4; margin: 15mm 17mm 14mm; }
:root { --ink:#16181d; --muted:#5b6170; --rule:#d9dce3; --accent:#c2410c; --accent-soft:#fff3ec; }
* { box-sizing: border-box; }
html { -webkit-print-color-adjust: exact; print-color-adjust: exact; }
body { font-family: "Segoe UI", "Helvetica Neue", Arial, sans-serif; color: var(--ink); font-size: 9.35pt; line-height: 1.38; margin: 0; }
header { border-bottom: 2px solid var(--ink); padding-bottom: 7px; margin-bottom: 9px; }
.kicker { font-size: 7.6pt; letter-spacing: .12em; text-transform: uppercase; color: var(--accent); font-weight: 700; }
h1 { font-size: 21pt; margin: 2px 0 1px; letter-spacing: -.01em; }
.sub { color: var(--muted); font-size: 9.2pt; margin: 0; }
.meta { margin-top: 6px; font-size: 7.9pt; color: var(--ink); background: var(--accent-soft); border-left: 3px solid var(--accent); padding: 4px 8px; }
.tagline { font-size: 10.5pt; font-weight: 600; margin: 0 0 8px; }
h2 { font-size: 9.6pt; margin: 8px 0 2px; color: var(--ink); break-after: avoid; }
h2 .n { display: inline-block; min-width: 1.5em; color: var(--accent); }
p { margin: 0 0 3px; }
.answers { columns: 2; column-gap: 7mm; }
.answers section { break-inside: avoid; }
.extra { border-top: 1px solid var(--rule); margin-top: 8px; padding-top: 5px; font-size: 7.8pt; color: var(--muted); }
.extra h2 { font-size: 8.4pt; margin-top: 0; }
.extra ul { margin: 0; padding-left: 14px; }
.extra li { margin: 0 0 1px; }
footer { margin-top: 6px; font-size: 7.4pt; color: var(--muted); display: flex; justify-content: space-between; }
.flow { margin: 10px 0 0; break-inside: avoid; break-before: page; }
.flow svg { width: 100%; height: auto; display: block; }
.flow figcaption { font-size: 7.6pt; color: var(--muted); margin-top: 3px; }
"""


def _box(x: int, y: int, title: str, sub: str, accent: bool = False) -> str:
    fill = "#fff3ec" if accent else "#ffffff"
    stroke = "#c2410c" if accent else "#16181d"
    return (
        f'<rect x="{x}" y="{y}" width="124" height="52" rx="7" fill="{fill}" stroke="{stroke}" stroke-width="1.3"/>'
        f'<text x="{x + 62}" y="{y + 22}" text-anchor="middle" font-size="12.5" font-weight="700" fill="#16181d">{html.escape(title)}</text>'
        f'<text x="{x + 62}" y="{y + 39}" text-anchor="middle" font-size="10" fill="#5b6170">{html.escape(sub)}</text>'
    )


def _arrow(x1: int, y: int, x2: int) -> str:
    return f'<line x1="{x1}" y1="{y}" x2="{x2 - 4}" y2="{y}" stroke="#16181d" stroke-width="1.3" marker-end="url(#ah)"/>'


def build_figure() -> str:
    step = 147
    lane1 = [("Today's photos", "default selection"), ("Tags + rules", "EXIF, face rules"), ("Text reading", "photo-agent OCR"),
             ("Visual reading", "photo-agent vision"), ("3-line answer", "asymmetric rule"), ("One yes", "album + tags")]
    lane2 = [("Shared albums", "shared by the user"), ("Index shortlist", "text, cards, GPS"), ("Two readings", "text + vision"),
             ("Stranger's File", "8 pages, combinations")]
    parts = ['<svg viewBox="0 0 890 250" xmlns="http://www.w3.org/2000/svg" font-family="Segoe UI, Helvetica, Arial, sans-serif">',
             '<defs><marker id="ah" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="7" markerHeight="7" orient="auto">'
             '<path d="M0,0 L10,5 L0,10 z" fill="#16181d"/></marker></defs>',
             '<text x="8" y="16" font-size="11" font-weight="700" letter-spacing="1.2" fill="#c2410c">IS THIS SAFE TO POST?</text>']
    for i, (title, sub) in enumerate(lane1):
        x = 8 + i * step
        parts.append(_box(x, 26, title, sub, accent=(i == 4)))
        if i:
            parts.append(_arrow(x - step + 124, 52, x))
    parts.append('<text x="449" y="100" text-anchor="middle" font-size="10.5" fill="#5b6170">'
                 'Text and visual readings run as separate delegations. One reading raises a concern; '
                 'Clear needs both readings and the metadata to complete clean.</text>')
    parts.append('<text x="8" y="140" font-size="11" font-weight="700" letter-spacing="1.2" fill="#c2410c">WHAT COULD A STRANGER FIND OUT ABOUT US?</text>')
    for i, (title, sub) in enumerate(lane2):
        x = 8 + i * step
        parts.append(_box(x, 150, title, sub, accent=(i == 3)))
        if i:
            parts.append(_arrow(x - step + 124, 176, x))
    parts.append('<text x="8" y="226" font-size="10.5" fill="#5b6170">'
                 'Pages count confirmed clues only and never state their values. One yes marks the photos Keep private and shows the official steps to unshare.</text>')
    parts.append('</svg>')
    return "".join(parts)


FIGURE = build_figure()


def render_html(meta: dict[str, str], body: str, total: int) -> str:
    answers_md = body.split("<!-- answers:start -->", 1)[1].split("<!-- answers:end -->", 1)[0]
    extra_md = body.split("<!-- answers:end -->", 1)[1]

    sections = []
    for block in re.split(r"(?m)^## ", answers_md)[1:]:
        heading, _, rest = block.partition("\n")
        number, _, question = heading.partition(". ")
        sections.append(
            f'<section><h2><span class="n">{html.escape(number)}</span>{html.escape(question)}</h2>'
            f"{markdown.markdown(rest.strip())}</section>"
        )

    return f"""<!doctype html>
<html lang="en"><head><meta charset="utf-8"><title>{html.escape(meta.get('title', 'Proposal'))} · Proposal</title>
<style>{CSS}</style></head><body>
<header>
  <div class="kicker">Project Proposal · Round 1</div>
  <h1>{html.escape(meta.get('title', ''))}</h1>
  <p class="sub">{html.escape(meta.get('subtitle', ''))}</p>
  <div class="meta">{html.escape(meta.get('meta', ''))}</div>
</header>
<p class="tagline">{html.escape(meta.get('tagline', ''))}</p>
<div class="answers">{''.join(sections)}</div>
<figure class="flow">{FIGURE}<figcaption>Figure. Orchestration at a glance (labels only; all steps delegate to registered NAS experts).</figcaption></figure>
<div class="extra">{markdown.markdown(extra_md.strip())}</div>
<footer><span>Ten answers: {total} words (limit {WORD_LIMIT}).</span><span>Not an official UGREEN product.</span></footer>
</body></html>"""


def find_browser() -> str | None:
    for candidate in BROWSERS:
        if Path(candidate).exists():
            return candidate
        found = shutil.which(candidate)
        if found:
            return found
    return None


def main() -> int:
    meta, body = split_front_matter(SRC.read_text(encoding="utf-8").replace("\r\n", "\n"))
    counts = count_answers(body)
    total = sum(n for _, n in counts)
    for question, n in counts:
        print(f"{n:4d}  {question}")
    print(f"{total:4d}  TOTAL (limit {WORD_LIMIT}) across {len(counts)} answers")
    section = body.split("<!-- answers:start -->", 1)[1].split("<!-- answers:end -->", 1)[0]
    naive = sum(len(line.split()) for line in section.splitlines() if line.strip() and not line.startswith("## "))
    print(f"{naive:4d}  naive whitespace count (every token, symbols included)")
    total = max(total, naive)
    if len(counts) != 10:
        print("error: expected exactly ten answers", file=sys.stderr)
        return 1
    if total > WORD_LIMIT:
        print("error: word limit exceeded", file=sys.stderr)
        return 1
    if "--count" in sys.argv:
        return 0

    HTML_OUT.write_text(render_html(meta, body, total), encoding="utf-8")
    browser = find_browser()
    if not browser:
        print("error: Chrome or Edge not found for PDF rendering", file=sys.stderr)
        return 1
    subprocess.run(
        [browser, "--headless=new", "--disable-gpu", "--no-pdf-header-footer",
         f"--print-to-pdf={PDF_OUT}", HTML_OUT.as_uri()],
        check=True, capture_output=True, timeout=120,
    )
    size = PDF_OUT.stat().st_size
    print(f"PDF: {PDF_OUT.relative_to(ROOT)} ({size} bytes, limit {PDF_LIMIT})")
    if size > PDF_LIMIT:
        print("error: PDF over 1 MB", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
