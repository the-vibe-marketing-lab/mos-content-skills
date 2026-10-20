# Content output routing: where briefs and articles go

The one convention for where mos-content skills save briefs and articles, what they are called, and how they reach Google Drive. `mos-content-brief`, `mos-content-best-x-for-y` and `mos-content-writer` all follow it. Finding the brain root is covered in `brain-context.md`.

## Markdown is the deliverable

One Markdown file per stage. No `.docx` by default.

- **Brief:** ONE `<date>-<slug>-brief.md`: an optional top block (summary table and key findings), the guideline tables, the article outline, and any `# Supporting Notes`.
- **Article:** ONE `<date>-<slug>-article.md`.
- Everything else (Information Gain research, sitemap list, SERP and competitor extracts, AI-search captures, notes) goes in that stage's `research/` folder.
- **House formatting:** tight bullet lists (no blank line between items), no empty lines inside table cells, no horizontal rules, no `.webp` images (Google Docs cannot show them; re-fetch as PNG or JPG. Contentful `fm=webp` becomes `fm=png` automatically in `build_final_md.py`).

## Folder structure

Default route, relative to the brain root:

```
content/
  <YYYY>/                                   e.g. 2026
    <MM-Mon>/                               e.g. 10-Oct
      <YYYY-MM-DD>-<slug>/                  the topic folder, dated the day it is created
        blog/
          brief/
            <YYYY-MM-DD>-<slug>-brief.md    THE brief
            research/                       information gain, sitemap, SERP extracts, notes
          article/
            <YYYY-MM-DD>-<slug>-article.md  THE article (added by mos-content-writer)
```

- **Month folders are `MM-Mon`**: zero-padded number plus the three-letter month (`01-Jan` to `12-Dec`, `09-Sep`, never `Sept` and never a bare `09`). If `.mos/config.yaml` sets a different `month_folder`, use that.
- **Reuse before you create.** `ls content/<YYYY>/<MM-Mon>/` first. If a topic folder for the same slug exists (for example one with a YouTube or social stage already in it), add `blog/` inside it rather than making a second topic folder.
- **The brain wins.** If the brain's `.mos/config.yaml`, `CLAUDE.md` or `AGENTS.md` declares a different content route (for example a separate blog folder), follow it and keep the same file names inside.
- Create only the folders a file is actually written into. Never create empty stage folders.

### Best X for Y: the shortlist-run folder

`mos-content-best-x-for-y` writes one extra folder per run, BEFORE any page brief exists: the shortlist run, shared by every page it produces. Same month-folder and reuse rules; the slug is the category plus `-best-x-for-y`:

```
content/<YYYY>/<MM-Mon>/<YYYY-MM-DD>-<category-slug>-best-x-for-y/
  shortlist.md                              the ranked shortlist the user picked from, with gate reasons
  research/                                 seeds.json, candidates.json, keywords.txt, volume.json,
                                            prompts.json, engines/, gate.json, gate-result.json
```

Each page the user picks then gets its own topic folder in the default shape above (`<YYYY-MM-DD>-<page-slug>/blog/brief/`), whose `research/` holds that page's `entries.json`, `criteria.md`, `evidence.csv`, `snapshots/` and `picks.json`. The shortlist run is never a brief and never holds a `-brief.md`. File-by-file schema: `mos-content-best-x-for-y/references/data-files.md`.

## Naming rules

- **`<YYYY-MM-DD>`** (file prefix): the date that file is generated. A brief written one day and its article the next carry different dates, on purpose.
- **`<slug>`**: the focus keyword, lowercased, spaces to hyphens, punctuation stripped, repeated hyphens collapsed, capped at about 70 characters. For a "best X for Y" buyer's guide use the guide's keyword (`best-crm-for-tradies`).
- **Suffix:** `-brief` or `-article`; inside `research/`: `-information-gain`, `-sitemap-urls`, `-serp`, `-ai-search`, `-notes`.

Example (keyword "project management software for small agencies", brief generated 2026-10-21):
`content/2026/10-Oct/2026-10-21-project-management-software-for-small-agencies/blog/brief/2026-10-21-project-management-software-for-small-agencies-brief.md`

## Building the brief

Every brief skill writes a **working master** with the canonical labels below to a temp folder, then builds the one final file:

```bash
python3 "$SKILL/../_shared/scripts/build_final_md.py" "$TMP/<YYYY-MM-DD>-<slug>-brief.md" "<topic folder>/blog/brief"
```

The script needs only the Python standard library. It fills the Research, Brand, Content and Publishing tables as two-column Markdown tables, adds the outline, appends internal sections under `# Supporting Notes`, and applies the house formatting. Everything above `# The Brief` in the master is kept as the top block; with no top block it adds `# Content Brief: <keyword>`. Delete the temp master afterwards.

## Canonical brief labels

The builder matches rows by label, so every brief skill emits these exact section headers and bold labels. Each `**Label**` sits on its own line with a blank line after it.

- `## Brand Guidelines` (legacy `## Client Guidelines` is accepted): `**Customer Avatar**`, `**Tone of Voice**`, `**Restrictions and Guidelines**`, `**USPs**`, optional `**Author / Byline**`
- `## Content Guidelines`: `**Focus keyword(s)**`, `**New or Optimisation**`, `**Search intent**`, `**Content type**`, `**Buying journey**` (legacy `**Awareness Stage**` is accepted), `**Internal Linking**`, `**External Linking**`, `**Target audience**`, `**Word Count**`, `**What is missing in the SERPs?**`, `**Previous Content Examples**`, `**Content Goals**`, `**Featured Snippet**`, `**AI Search Visibility**`, `**Term Targets**`, `**Surfer SEO**`, `**Research Pages**`
- `## Publishing Guidelines`: `**URL slug**`, `**Title tag**`, `**Meta description**`, `**Additional publishing notes**`
- `## Article Outline`: the writer outline as real Markdown headings (`#`, `##`, `###`)
- Internal sections after the outline (`## Schema Spec`, `## Cluster / Funnel Context`, `## API Data Notes`) are moved to the end under `# Supporting Notes`.

A labelled field with no matching row is appended to its table, never dropped. Optional rows (Topical map, Featured Snippet, Map Pack, Surfer SEO, Author / Byline) disappear when empty; any other empty row reads "Not provided".

### What goes in each field

- **URL slug:** the full absolute URL and nothing else. Put redirect or architecture notes in Additional publishing notes.
- **Title tag:** the final title only, under 60 characters. No "current vs new" prose, no character counts.
- **Meta description:** the final meta only, under 160 characters.
- **Internal Linking:** one line per link, full absolute URL plus anchor, e.g. `https://example.com/page/ (anchor: "natural anchor text")`. Only URLs verified against the live sitemap.
- **Research Pages:** one line per source, full absolute URL.
- **Term Targets:** `serp_outline_builder.py --terms-md` output, verbatim. Fewer than 2 pages fetched: `Not available (fewer than 2 competitor pages fetched)`.
- **Surfer SEO (optional extra):** the stdout of `surfer_api.py brief-block`, pasted verbatim as dot points. Without a Surfer key, write `Not available (no SURFERSEO key)`. Never fabricate a Surfer link.
- **Any metric with no provider:** `Not available (no <PROVIDER> key)`. Never an estimate.

## Google Drive upload (separate step, always asked)

Only after the user names a folder (AskUserQuestion: "Which Google Drive folder should I upload this to?", with a link pasted via Other, or "Skip, keep it local"). Never guess a folder.

1. **`gws` CLI installed and signed in:** `python3 "$SKILL/../_shared/scripts/drive_upload.py" "<final .md>" "<folder link or id>"`. It uploads ONE styled Google Doc (slate section bars, grey label column, highlighted Surfer and Featured Snippet rows, tight bullets, full-width tables); articles get dark bold headings and grey table header rows. `--with-md` also uploads the raw `.md`. Without `gws` it prints a skip notice and exits 0.
2. **Google Drive connector available instead:** create the file in the named folder with the connector (a Google Doc converted from the Markdown, named like the file minus `.md`).
3. **Neither:** skip silently and leave the file local.

Report the Doc link. Re-uploading creates a new file; remove superseded copies only when the user asks.

## How the skills cooperate

- **Brief:** temp master, then `build_final_md.py`, then `blog/brief/<date>-<slug>-brief.md` (plus `research/`), then the optional Drive step.
- **Article:** `mos-content-writer` reads `blog/brief/<…>-brief.md`, writes `blog/article/<date>-<slug>-article.md`, runs `mos-content-humanizer`, then hands the draft to `mos-proofread`.
