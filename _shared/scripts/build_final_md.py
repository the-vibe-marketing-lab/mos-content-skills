#!/usr/bin/env python3
"""Turn a working master brief into the ONE final deliverable: <out-dir>/<date>-<slug>-brief.md.
Shared by every mos-content brief skill (mos-content-brief, mos-content-best-x-for-y).

Standard library only. The master (canonical labels, see templates/content-brief-template.md and
content-output-routing.md) is parsed directly: its bold-label fields fill a fixed row schema for the
three guideline tables, which are written as 2-column Markdown tables. The result is assembled as:

  top block (everything in the master above "# The Brief"; may be empty)
  + Research / Brand / Content / Publishing guideline tables ("## Client Guidelines" is accepted
    as a legacy name for "## Brand Guidelines"; the output always says Brand Guidelines)
  + "# Page Copy + Optimisation Notes" (optimisation briefs) or "# Article Outline" (new content)
Internal sections after the outline (Schema Spec, Cluster / Funnel Context, API Data Notes,
developer notes) are appended at the end under "# Supporting Notes", so writers have one file.

Row rules:
  - fields are matched to rows by normalised label (aliases below), never by position
  - optional rows (Topical map, Featured Snippet, Map Pack, Surfer SEO, Author / Byline) are dropped
    when the master has no value for them; other empty rows say "Not provided"
  - a labelled field with no matching row is appended to the end of its table, never dropped
  - inline "**Label:** value" lines above the first guideline section fill rows the sections left empty
  - URL slug / Title tag / Meta description keep only the clean final value

House formatting rules applied:
  - no "The live page reproduced verbatim..." intro line
  - tight bullet lists (no blank line between items), no empty lines inside table cells
  - .webp images re-fetched as PNG where the CDN allows it (Contentful: fm=webp -> fm=png)
Nothing else is written: no .docx, outline or table side files.

Exits non-zero (and writes nothing) when the outline or "Focus keyword(s)" is empty.

Usage: build_final_md.py <master.md> <out-dir>
"""
import re
import sys
from pathlib import Path

LIST = re.compile(r"\s*([-*]|\d+\.)\s")

# ---------------------------------------------------------------------------
# Row schema: (label, hint shown under the label, default value, optional)
# ---------------------------------------------------------------------------
CLIENT_ROWS = [
    ("Customer Avatar", "", "", False),
    ("Tone of Voice", "", "", False),
    ("Restrictions and Guidelines", "", "", False),
    ("USPs", "", "", False),
    ("Author / Byline", "", "", True),
]
CONTENT_ROWS = [
    ("Focus keyword(s)", "", "", False),
    ("New or Optimisation", "", "", False),
    ("Search intent", "", "", False),
    ("Content type", "", "", False),
    ("Buying journey", "", "", False),
    ("Topical map", "", "", True),
    ("Internal Linking", "", "", False),
    ("External Linking", "", "", False),
    ("Target audience", "(Be more granular than the Customer Avatar above)", "", False),
    ("Word Count", "", "", False),
    ("What is missing in the SERPs?", "", "", False),
    ("Previous Content Examples", "", "", False),
    ("Content Goals", "(SEO + content goals)", "", False),
    ("Featured Snippet", "", "", True),
    ("Map Pack", "", "", True),
    ("Term Targets", "(phrases the top 10 use: usage range, pages using it)", "", False),
    ("Surfer SEO", "", "", True),
    ("Research Pages", "", "", False),
]
PUBLISHING_ROWS = [
    ("URL slug", "", "", False),
    ("Title tag", "(<60 characters)", "", False),
    ("Meta description", "(<160 characters)", "", False),
    ("Font size recommendations", "",
     "Headings: 1.96x larger than body content size.\nBody Copy: Between 16px and 20px.", False),
    ("Image size recommendations", "", "Ensure all images are below 100kb in size.", False),
    ("Additional publishing notes", "", "", False),
]
SCHEMA = {"client": CLIENT_ROWS, "content": CONTENT_ROWS, "publishing": PUBLISHING_ROWS}

RESEARCH_INTRO = ("Use the following process below to ensure that your content is well-researched, "
                  "and that you are covering the searcher's intent.")
PUBLISHING_INTRO = "Please use the following guidelines to ensure your page is as optimised as possible!"


def norm(label):
    s = label.split("\n")[0]
    s = re.sub(r"\([^)]*\)", " ", s)
    s = s.replace("&", " and ").lower()
    return re.sub(r"[^a-z0-9]+", " ", s).strip()


ALIASES = {
    "title tag": "title link",
    "surferseo link": "surfer seo",
    "brand voice": "tone of voice",
    "tone target": "tone of voice",
    "compliance": "restrictions and guidelines",
    "compliance non negotiable": "restrictions and guidelines",
    "restrictions": "restrictions and guidelines",
    "key differentiators": "usps",
    "key differentiators to use": "usps",
    "usp": "usps",
    "author byline": "author byline",
    "author": "author byline",
    "byline": "author byline",
    "internal links": "internal linking",
    "external links": "external linking",
    "research competitor pages": "research pages",
    "research pages competitors": "research pages",
    "featured snippet serp shape": "featured snippet",
    "what s missing in the serp": "what is missing in the serps",
    "what s missing in the serps": "what is missing in the serps",
    "whats missing in the serp": "what is missing in the serps",
    "content audit": "content audit summary",
    "awareness stage": "buying journey",
}


def canon(label):
    return ALIASES.get(norm(label), norm(label))


# ---------------------------------------------------------------------------
# Parse the master into guideline fields + outline + notes
# ---------------------------------------------------------------------------
SECTION_RE = re.compile(r"^##\s+(.+?)\s*$")
HEADER_RE = re.compile(r"^#{1,2}\s+(.+?)\s*$")
BOLD_LABEL_RE = re.compile(r"^\*\*([^*]+)\*\*\s*$")
INLINE_FM_RE = re.compile(r"^\*\*([^*]+?):\*\*\s*(.+?)\s*$")
GUIDELINE_SECTIONS = {"brand guidelines": "client", "client guidelines": "client", "content guidelines": "content",
                      "publishing guidelines": "publishing", "publishing": "publishing"}


def is_internal_section(sn):
    return (sn in ("schema spec", "cluster funnel context", "api data notes")
            or "schema" in sn or "funnel" in sn or "api data" in sn or "developer" in sn)


def parse(md):
    lines = md.split("\n")
    outline_start = notes_start = None
    for i, ln in enumerate(lines):
        m = HEADER_RE.match(ln)
        if not m:
            continue
        sn = norm(m.group(1))
        if outline_start is None and (sn == "article outline" or sn.startswith("page copy")):
            outline_start = i
        elif outline_start is not None and notes_start is None and is_internal_section(sn):
            notes_start = i
    end_table = outline_start if outline_start is not None else (notes_start or len(lines))
    end_outline = notes_start if notes_start is not None else len(lines)

    outline = []
    if outline_start is not None:
        outline = lines[outline_start + 1:end_outline]  # drop the zone marker itself
        while outline and not outline[0].strip():
            outline.pop(0)
        if outline and re.match(r"^\*[^*].*\*$", outline[0].strip()):  # italic explainer under it
            outline.pop(0)
    notes = "\n".join(lines[notes_start:]).strip() if notes_start is not None else ""

    first_g = end_table
    for i, ln in enumerate(lines[:end_table]):
        m = SECTION_RE.match(ln)
        if m and norm(m.group(1)) in GUIDELINE_SECTIONS:
            first_g = i
            break
    frontmatter = {}
    for ln in lines[:first_g]:
        fm = INLINE_FM_RE.match(ln)
        if fm:
            frontmatter[fm.group(1).strip()] = fm.group(2).strip()

    sections = {"client": {}, "content": {}, "publishing": {}}
    cur_section = cur_label = None
    buf = []

    def flush():
        if cur_section in sections and cur_label is not None:
            sections[cur_section][cur_label] = "\n".join(buf).strip()

    for ln in lines[:end_table]:
        m = SECTION_RE.match(ln)
        if m:
            sec = GUIDELINE_SECTIONS.get(norm(m.group(1)))
            if sec is not None:
                flush()
                buf, cur_label, cur_section = [], None, sec
                continue
            # An unknown "##" inside a field (e.g. a pasted AI-search block) stays as content.
            if cur_section in sections and cur_label is not None:
                buf.append(ln)
            continue
        if cur_section in sections:
            bm = BOLD_LABEL_RE.match(ln)
            if bm:
                flush()
                buf, cur_label = [], bm.group(1).strip()
            elif cur_label is not None:
                buf.append(ln)
    flush()
    return sections, frontmatter, "\n".join(outline).strip(), notes


def primary_keyword(sections):
    for label, val in sections["content"].items():
        if "focus keyword" in canon(label):
            for line in val.split("\n"):
                line = line.strip().lstrip("-").strip()
                line = re.sub(r"^(primary keyword|primary)\s*:\s*", "", line, flags=re.I)
                line = re.split(r"\s*[\(—\-]\s", line)[0].split("(")[0].strip().rstrip(":").strip()
                if line:
                    return line
    return None


# ---------------------------------------------------------------------------
# Single-value publishing rows: keep only the clean final value
# ---------------------------------------------------------------------------
URL_RE = re.compile(r"https?://[^\s)\]]+")


def clean_single(clabel, content):
    lines = [l.strip() for l in content.split("\n") if l.strip()]
    if not lines:
        return content
    if clabel == "url slug":
        urls = [(l.lower(), u) for l in lines for u in URL_RE.findall(l)]
        if not urls:
            return re.sub(r"\s*\([^)]*\)\s*\.?\s*$", "", lines[0]).strip()
        for kw in ("target", "post-301", "post 301", "new", "final", "canonical"):
            for low, u in reversed(urls):
                if kw in low:
                    return u
        return urls[0][1]
    if clabel == "title link":
        ticks = re.findall(r"`([^`]+)`", content)
        if ticks:
            return ticks[-1].strip()
        for l in lines:
            if re.match(r"(?i)^(current|note|target|replace|→)\b", l) or (l.startswith("(") and l.endswith(")")):
                continue
            return re.sub(r"\s*\([^)]*\)\s*$", "", l).strip()
        return lines[0]
    if clabel == "meta description":
        ticks = [t.strip() for t in re.findall(r"`([^`]+)`", content) if t.strip()]
        if ticks:
            under = [t for t in ticks if len(t) <= 165]
            return under[-1] if under else ticks[-1]
        cands = [re.sub(r"\s*[✅✓]\s*$", "", l).strip() for l in lines
                 if not re.match(r"(?i)^(note|use this|character count|current|target)\b", l)
                 and not (l.startswith("(") and l.endswith(")"))]
        cands = [c for c in cands if c]
        if not cands:
            return lines[0]
        under = [c for c in cands if len(c) <= 165]
        return under[-1] if under else cands[0]
    return content


# ---------------------------------------------------------------------------
# Markdown table rendering
# ---------------------------------------------------------------------------
NUM_LINE_RE = re.compile(r"^\s*\d+[.)]\s+")


def cell(content):
    out = []
    for raw in content.split("\n"):
        line = raw.strip()
        if not line:
            continue
        line = line.replace("|", "\\|")
        if line.startswith(("- ", "* ")):
            line = "• " + line[2:]
        elif re.match(r"^#{1,6}\s", line):  # a heading pasted inside a field
            line = "**" + re.sub(r"^#{1,6}\s+", "", line) + "**"
        out.append(line)
    return "<br>".join(out) or "Not provided"


def label_cell(label, hint=""):
    s = f"**{label}**"
    return s + (f"<br>**{hint}**" if hint else "")


def build_table(sec, data, frontmatter, used_fm):
    rows, matched = ["| | |", "|---|---|"], set()
    for label, hint, default, optional in SCHEMA[sec]:
        clabel = canon(label)
        hit = next((v for k, v in data.items() if canon(k) == clabel and v.strip()), None)
        if hit is None:
            for k, v in frontmatter.items():
                if canon(k) == clabel and v.strip():
                    hit = v
                    used_fm.add(k)
                    break
        if hit:
            if clabel in ("url slug", "title link", "meta description"):
                hit = clean_single(clabel, hit)
            matched.add(clabel)
        elif optional:
            continue
        else:
            hit = default
        rows.append(f"| {label_cell(label, hint)} | {cell(hit)} |")
    for k, v in data.items():  # labelled fields with no row: append, never drop
        if v.strip() and canon(k) not in matched:
            rows.append(f"| {label_cell(k.split(chr(10))[0].strip())} | {cell(v)} |")
            matched.add(canon(k))
    return "\n".join(rows)


def house_rules(s):
    s = re.sub(r"\n> The live page reproduced verbatim[^\n]*\n", "\n", s)
    s = re.sub(r"(fm=)webp", r"\1png", s)
    if re.search(r"\]\([^)]*\.webp\)", s):
        print("WARNING: a .webp image is left in the copy; re-fetch it as PNG/JPG from the live site.")
    s = re.sub(r"(<br>)+(?=<br>)", "", s)
    lines, res = s.split("\n"), []
    for i, l in enumerate(lines):
        if not l.strip() and res and LIST.match(res[-1]) and i + 1 < len(lines) and LIST.match(lines[i + 1]):
            continue
        res.append(l)
    return re.sub(r"\n{3,}", "\n\n", "\n".join(res)).strip() + "\n"


def main(master, out_dir):
    master, out_dir = Path(master), Path(out_dir)
    text = master.read_text(encoding="utf-8")
    top = text.split("# The Brief")[0].strip() if "# The Brief" in text else ""
    outline_h = ("# Page Copy + Optimisation Notes" if "# Page Copy + Optimisation Notes" in text
                 else "# Article Outline")
    sections, frontmatter, outline, notes = parse(text)
    problems = []
    if not outline.strip():
        problems.append('the article outline is empty: add "## Article Outline" (or "# Page Copy + '
                        'Optimisation Notes") followed by the outline headings')
    focus = next((v for k, v in sections["content"].items() if canon(k) == "focus keyword"), "")
    if not focus.strip():
        focus = next((v for k, v in frontmatter.items() if canon(k) == "focus keyword"), "")
    if not focus.strip():
        problems.append('"Focus keyword(s)" is empty: put the primary keyword under **Focus keyword(s)** '
                        'in "## Content Guidelines"')
    if problems:
        sys.exit("build_final_md.py: cannot build " + str(master) + ":\n  - " + "\n  - ".join(problems))
    used_fm = set()
    tables = {sec: build_table(sec, sections[sec], frontmatter, used_fm) for sec in SCHEMA}
    body = (f"## Research\n\n{RESEARCH_INTRO}\n\n## Brand Guidelines\n\n{tables['client']}\n\n"
            f"## Content Guidelines\n\n{tables['content']}\n\n## Publishing Guidelines\n\n"
            f"{PUBLISHING_INTRO}\n\n{tables['publishing']}\n\n{outline_h}\n\n{outline}")
    if not top:  # no top block: title from the primary keyword, else the file name
        kw = primary_keyword(sections)
        if not kw:
            kw = re.sub(r"^\d{4}-\d{2}-\d{2}-", "", master.stem).removesuffix("-brief").replace("-", " ")
        top = f"# Content Brief: {kw}"
    if notes:
        body += "\n\n# Supporting Notes\n\n" + re.sub(r"^#\s[^\n]*\n+", "", notes)
    out_dir.mkdir(parents=True, exist_ok=True)
    final = out_dir / master.name
    final.write_text(house_rules(f"{top}\n\n{body}"), encoding="utf-8")
    print(final)


if __name__ == "__main__":
    if len(sys.argv) != 3 or sys.argv[1] in ("-h", "--help"):
        print(__doc__)
        sys.exit(0 if len(sys.argv) == 2 and sys.argv[1] in ("-h", "--help") else 2)
    main(*sys.argv[1:])
