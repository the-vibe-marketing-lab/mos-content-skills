---
name: mos-content-writer
description: >
  Write a publication-ready SEO + GEO article FROM AN EXISTING, APPROVED BRIEF.
  Downstream of mos-content-brief, mos-content-best-x-for-y and mos-geo-vs-content
  (mos-geo-skills pack, for 1v1 vs pages): a -brief.md file is a hard precondition. Loads the MarketingOS brain's voice and audience, follows the
  brief's outline section by section with the Copywriter agent (or in session),
  runs the mandatory humanizer pass, then a linter, word counter and checklist
  verifier. The chain is brief, then write, then mos-proofread.
  Trigger when: "write the content from this brief", "write this brief",
  "execute this brief", "write the article from [brief path]", "content from brief",
  "draft [brief name]", "write the latest brief".
  NOT FOR: "write an article about X" with no brief (run mos-content-brief or
  mos-content-best-x-for-y first; for a 1v1 vs page, mos-geo-vs-content); sales pages, emails, ads or social posts with no
  search target (mos-copy-research then mos-copywriting); proofreading a finished
  draft (mos-proofread).
allowed-tools:
  - Read
  - Grep
  - Glob
  - Bash
  - Write
  - Edit
  - WebFetch
  - Task
  - AskUserQuestion
---

# Content Writer: from brief to article

Write a full article from a completed brief. Three brief types are supported:

- **Standard article brief** from `mos-content-brief`.
- **Best X for Y brief** (a genuine buyer's guide) from `mos-content-best-x-for-y`.
- **vs brief** (one brand against one competitor) from `mos-geo-vs-content` in the
  mos-geo-skills pack, saved at
  `campaigns/geo/YYYY-MM/content-ideas/vs-content/publishing/NN-<slug>/<slug>-brief.md`.

## Hard precondition: a brief must exist first

This skill is not a standalone "write me an article" tool. The brief sets the outline,
keywords, internal links, guidelines and the reader's awareness stage. Writing without
one ships the wrong voice, misses the gaps in the search results and skips the GEO
structure. The workflow is always:

```
brief skill -> <date>-<slug>-brief.md (reviewed) -> mos-content-writer -> <date>-<slug>-article.md -> mos-proofread
```

If the user asks for an article without pointing at a brief, do not start this skill.
Confirm the topic and content type, then run the matching brief skill first:

- Standard article: `mos-content-brief`
- "Best X for Y" buyer's guide: `mos-content-best-x-for-y`
- Head-to-head comparison of exactly two products: `mos-geo-vs-content` (mos-geo-skills
  pack). It writes a writer-ready brief per page to
  `campaigns/geo/YYYY-MM/content-ideas/vs-content/publishing/NN-*/`, with its evidence in
  that folder's `research/evidence.csv`.

Let the user review the brief (its tables are an intentional checkpoint), then run this
skill against the approved file. Phase 0 enforces this: no resolvable brief means stop.

## Before you start: paths

This skill's shared files live in the pack's `_shared/` folder, next to this skill folder in
the mos-content-skills repo. `setup.sh` links only the skill folders into `~/.claude/skills/`,
so resolve the real path first and use `$SKILL/../_shared/...` everywhere:

```bash
SKILL="$(cd "$(dirname "$(readlink -f ~/.claude/skills/mos-content-writer/SKILL.md)")" && pwd)"
BRAIN=$(git rev-parse --show-toplevel 2>/dev/null || pwd)
```

`~/.claude/skills/_shared` is a different folder from another pack. Never read from it. Pass the
resolved `$SKILL` to every agent and Task this skill spawns, and tell them to read pack files as
`$SKILL/../_shared/...`, never as a bare relative `_shared` path.

## Inputs

| # | Input | Required | Notes |
|---|-------|----------|-------|
| 1 | Brief file path | Yes | A path to a `-brief.md`, or "the latest brief" (resolved in Phase 0) |
| 2 | Additional instructions | No | Tone adjustments, special requests |

The working context is the MarketingOS brain the user is in. How to find the brain root,
its voice, audience, domain and competitors: `$SKILL/../_shared/brain-context.md`. Where files
are saved: `$SKILL/../_shared/content-output-routing.md`.

## Phase 0: resolve and parse the brief (blocking)

If this phase fails, stop and route the user back to a brief skill. Never invent an outline.

1. **Locate the brief.**
   - Explicit path: read it. Fail if the file does not exist.
   - "The latest brief": glob `content/**/brief/*-brief.md` from the brain root (plus any
     content route the brain declares, per `$SKILL/../_shared/content-output-routing.md`, and
     `campaigns/geo/*/content-ideas/vs-content/publishing/*/*-brief.md` for vs briefs), sort
     by modification time and take the newest. Zero matches is a failure.
   - The brief is ONE file: the guideline tables plus `# Article Outline`. Read both
     from it.
2. **No brief found:** stop and reply:
   > I can't find a brief for this. `mos-content-writer` only writes from an approved brief. Which brief skill should I run first?
   > - Standard article: `mos-content-brief`
   > - "Best X for Y" buyer's guide: `mos-content-best-x-for-y`
   >
   > - Head-to-head vs page (your brand against one competitor): `mos-geo-vs-content` (mos-geo-skills pack), which writes the brief to `campaigns/geo/YYYY-MM/content-ideas/vs-content/publishing/NN-*/`
3. **Sanity-check the file** before trusting it:
   - The filename ends in `-brief.md`.
   - It has a `Content Guidelines` table and an outline (`# Article Outline`, or `##`/`###`
     sections with writing instructions).
   - `Focus keyword(s)` and `Word Count` are filled in.
   If anything is missing it is probably a research note or a draft. Tell the user and
   offer to regenerate the brief.
4. **Extract** from the brief:
   - The guidelines tables: `Brand Guidelines` (older briefs: `Client Guidelines`),
     `Content Guidelines` and `Publishing Guidelines` (URL slug, title tag, meta description).
   - The outline: heading structure plus each section's writing instructions.
   - `Research Pages`, `Internal Linking` (URL plus anchor), `Word Count`, `Focus keyword(s)`.
   - **Awareness stage and market sophistication** (the brief's `Buying journey` or
     `Awareness Stage` field). This is where the copy starts, so carry it into every
     section. If the brief has neither, infer it once from search intent and the search
     results (unaware, problem aware, solution aware, product aware, most aware; market
     sophistication 1 to 5) and say that you inferred it.
5. **Detect the brief type** from `Content type` (and the outline):
   - Starts with "1v1 comparison (vs page)": **vs**.
   - Mentions "best X for Y", "buyer's guide", or the outline has a methodology block and
     "Best for" picks: **best-x-for-y**.
   - `New or Optimisation` says "Optimisation": stop. This pack has no optimisation brief
     yet; tell the user and offer to write a fresh standard brief with `mos-content-brief`.
   - Anything else: **standard**.
6. **best-x-for-y only: load the evidence files (blocking).** The brief's research folder is
   `<brief dir>/research/` (the folder holding the `-brief.md`, then `research/`; layout in
   `$SKILL/../mos-content-best-x-for-y/references/data-files.md`). Read all three:
   - `research/evidence.csv`: one row per fact (id, entry, claim, value, source_url,
     snapshot_path, captured_on, quote).
   - `research/picks.json`: position, Best for, Not for, criterion and evidence ids per entry,
     plus `best_overall`.
   - `research/criteria.md`: the approved criteria and methodology block.
   If any of the three is missing or empty, stop. Tell the user the brief's evidence is
   incomplete and offer to re-run `mos-content-best-x-for-y` for this page. Never write picks
   from the brief prose alone.
   **vs only: load the evidence file (blocking).** Read `<brief dir>/research/evidence.csv`
   (columns `brand`, `dimension`, `value`, `verbatim_quote`, `source_url`, `snapshot_file`,
   `captured_on`). If it is missing or has no data rows, stop. Tell the user the brief's
   evidence is missing and offer to re-run `mos-geo-vs-content` for this page. Never write a
   competitor fact from the brief prose alone.
7. **Split the outline into sections**, each with heading level and text, writing
   instructions, word target, and the internal links that belong to it. For best-x-for-y,
   also carry the methodology block, the criteria, each pick's "Best for" and "Not for",
   the evidence rows from `evidence.csv` (source URL, capture date, verbatim quote), the
   picks from `picks.json`, the criteria from `criteria.md`, the disclosure line and which
   entries are the user's brand. For vs, carry each comparison section's `evidence.csv` rows
   (matched on `dimension`), the brief's Rules list, the disclosure and the capture dates.

Parsing details per type: `references/brief-type-handlers.md`.

## Phase 1: load the brain's voice and audience (parallel with Phase 2)

Follow `$SKILL/../_shared/brain-context.md` to find, from the brain root:

1. The brand voice file (tone of voice) and the audience or avatar file. These are the
   voice source for every section.
2. Product names, differentiators, restrictions and named competitors.
3. A reader research bank from `mos-copy-research`, if the brain has one. Pull the reader
   sketch and 3 to 6 verbatim reader quotes that fit this topic.

If no voice file exists, ask the user for a one-line voice description (or a link to one)
before drafting. Do not guess a voice.

Then spawn a Task with `agents/style-analyzer.md`: glob the brain's `content/**/*.md` for
3 to 5 recent articles (files without a Content Guidelines table) and pass their paths.
It returns a style profile. With no previous articles, skip it and rely on the voice file
plus `references/writing-rules.md`.

## Phase 2: load the research (parallel with Phase 1)

Spawn a Task with `agents/research-loader.md`, passing the brief's top 3 to 5 Research
Pages. It fetches each page and extracts statistics, quotes, pricing, examples and unique
angles, each with its source URL. A page that fails to load is noted as a gap.

For best-x-for-y and vs briefs, the rows in `research/evidence.csv` (snapshot, URL, capture
date, verbatim quote) are the only allowed source for competitor facts. The research loader adds context;
it never replaces or overrides the brief's evidence.

## Phase 3: write section by section (sequential)

Work through the outline in order. Sequential, because each section opens from the
previous section's closing paragraph.

For each section:

1. **Gather the section context:** heading and level, writing instructions, matching
   research, the internal links for this section, the previous section's closing
   paragraph, the word target, and the awareness stage and market sophistication.
2. **Set the brief-type flags** (rules in `references/brief-type-handlers.md`):
   - Standard: none.
   - best-x-for-y answer block and guide sections: `ANSWER_FIRST=true`.
   - best-x-for-y methodology block: `METHODOLOGY_VERBATIM=true`.
   - best-x-for-y pick entries: `PICK_ENTRY=true`, plus `OWN_BRAND=true` on the user's
     own brand where it passed the eligibility gate.
   - vs answer and comparison sections: `ANSWER_FIRST=true` and `VS_ROW=true`; the two
     "Choose ... if" sections: `VS_CHOOSE=true`; "How we compared": `METHODOLOGY_VERBATIM=true`.
3. **Draft the section with the `Copywriter` agent.** The agent owns the craft; this skill
   owns the guardrails, passed as hard constraints so they beat the agent's instincts.
   Spawn `Agent(subagent_type="Copywriter")` with a brief containing:
   - **Surface and format:** "One section of an SEO + GEO article. Markdown body." Plus the
     locale from the voice file (default Australian English when the brain does not say).
   - **Voice file and avatar file:** their paths from Phase 1, with the line "These files
     override any default house voice you carry."
   - **Research basis:** the brief's audience fields and awareness stage as the reader
     sketch, the reader quotes from Phase 1 when they exist, and this section's research
     notes. This is the documented research basis the agent requires.
   - **The one idea:** the heading and the point this section must land.
   - **Awareness stage and market sophistication** from Phase 0.
   - **Hook structure:** only when the section needs one (usually the introduction).
   - **best-x-for-y pick entries and the methodology block:** this entry's rows from
     `evidence.csv` (verbatim, with `source_url` and `captured_on`), its `picks.json` record,
     and the full `criteria.md`. The agent may state a competitor fact only from these rows.
   - **vs sections:** the section's `evidence.csv` rows for both brands (verbatim, with
     `source_url` and `captured_on`) and the brief's Rules list. Same rule: competitor facts
     only from these rows.
   - **Hard constraints (verbatim, these win):** the section word target; the exact
     internal links (absolute URLs); the brief-type flags from step 2; the SEO, GEO and
     EEAT rules in `references/writing-rules.md`; never mention the research or competitor
     analysis process; zero em dashes; and the previous section's closing paragraph, so
     the prose flows on from it.
   - Keep the returned `=== DRAFT ===` as the section, store its closing paragraph for the
     next section, and keep `=== CRAFT NOTES ===` for the verifier.
   - **If the agent returns `=== BLOCKED: NEEDS RESEARCH ===`:** offer to run
     `mos-copy-research` for this brain. If the user declines, re-brief the agent with
     "ungrounded is acceptable for this piece" and flag the article as ungrounded in the
     final report.

   **Fallback when no `Copywriter` agent is installed:** write the section in session with
   `agents/section-writer.md`, using the same inputs and constraints. Craft reference:
   the `mos-copywriting` skill, especially its `references/prose-craft-rules.md`.
4. **best-x-for-y summary table:** build it after every pick is written. Columns: Pick,
   Best for, Not for, the stated criteria, and Price (or "Not published"). Order follows
   the brief's ranking. The user's brand is never placed first by default.

## Phase 4: assemble and flow edit

1. Assemble every section into one Markdown document in outline order, with bold headings
   (`## **Heading text**`).
2. Spawn a Task with `agents/flow-editor.md` on the assembled article. It smooths
   transitions, removes repetition, checks coherence and adds `[IMAGE: description]`
   markers. It does not change facts, tables, picks or the methodology block.
3. **Humanizer pass (mandatory).** Run `mos-content-humanizer` in embedded mode on the
   full assembled draft: read `../mos-content-humanizer/SKILL.md` and its
   `references/humanizer.md`, then edit the body prose in place. Out of bounds (its
   precedence list): brief-dictated headings, keywords, links, `[IMAGE: ...]` markers and
   the CTA. On best-x-for-y pages also leave alone the methodology block, the pick order,
   every "Best for" and "Not for" line, evidence quotes, "Not published" values and the
   disclosure line. On vs pages leave alone the at-a-glance table, evidence quotes, "Not
   published" values, capture dates and the disclosure. This runs before Phase 5, so the linter and verifier check the
   humanized text, and before the hand-off to `mos-proofread`.

The brief tables are not copied into the article. The article file holds the article only.

## Phase 5: verify

1. **Run the deterministic linter first** (from the `mos-copywriting` skill):
   ```bash
   bun ~/.claude/skills/mos-copywriting/Tools/lint-copy.ts "<article_path>" --surface generic --body-only
   ```
   It checks em dashes, ellipses, stacked triads, hype words, filler phrases and SEO
   machinery tells in code. Exit 1 is a hard fail: fix in place and re-run until it exits
   0. If `bun` or the linter is not installed, say so in the report and let the verifier
   do these checks by eye.
2. **Count words:**
   ```bash
   python3 "$SKILL/scripts/word_counter.py" "<article_path>"
   ```
   (`$SKILL` is the resolved folder from "Before you start".) Returns per-section word counts as JSON.
3. Spawn a Task with `agents/content-verifier.md`, passing the article, the brief, the
   brief type, the word-count JSON, the internal links list, the linter report and
   `$SKILL`; for best-x-for-y also the paths to `research/evidence.csv`, `research/picks.json`
   and `research/criteria.md`, which it checks every pick and competitor fact against; for vs
   the path to `research/evidence.csv`. It runs
   the matching checklist in `references/quality-checklists.md` and returns a report plus a
   fixed article.
4. Apply the fixes, then re-run the linter (must exit 0) and the word counter.

## Phase 6: save and report

Markdown is the deliverable. No `.docx`.

1. **Save the article** in the same topic folder as the brief, following
   `$SKILL/../_shared/content-output-routing.md` (a content route declared in the brain's
   `.mos/config.yaml` or CLAUDE.md wins). The default is:
   ```
   content/<YYYY>/<MM-Mon>/<YYYY-MM-DD>-<slug>/blog/article/<YYYY-MM-DD>-<slug>-article.md
   ```
   - `<slug>` and the topic folder are the brief's; the file date is today.
   - vs briefs live under `campaigns/geo/`, not a content topic folder: take `<slug>` from
     the brief's URL slug and create the topic folder on the default route.
   - Month folders are `MM-Mon` (for example `10-Oct`). Reuse an existing month folder.
   - The file holds the article only: no brief tables, no YAML frontmatter.
   - Working files (research notes, word-count JSON, verifier report) go in
     `article/research/`. Nothing else sits beside the article.
2. **Optional HTML for a CMS paste**, only when the user asks:
   ```bash
   python3 "$SKILL/scripts/generate_article_html.py" "<article.md>" "<article.html>"
   ```
   It needs the `markdown` package; without it, run `uv run --with markdown python ...`.
3. **House formatting check:** tight bullet lists (no blank lines between items), no empty
   lines inside table cells, no horizontal rules, no `.webp` images (re-fetch as PNG or JPG).
4. **Report to the user:** the article path; word count against target; sections written;
   internal links used (X of Y); confirmation the humanizer pass ran; verification pass rate and what was fixed; research gaps;
   and whether the copy is flagged ungrounded.
5. **Hand off to QA.** The chain is brief, write, QA. Say the draft is ready and offer the
   next step:
   > Draft complete. Next step: `mos-proofread` for the independent proofread (strategy,
   > structure, clarity, cut, voice, mechanics, read-aloud). Want me to run it now?

## Phase 7: upload to Google Drive (optional, always ask)

Skip this phase silently when the user has neither the `gws` CLI nor a Google Drive
connector. Otherwise ask with AskUserQuestion: "Which Google Drive folder should I upload
this to?" (paste a folder link via Other, or "Skip, keep it local"). Never guess a folder
and never upload without an answer.

```bash
python3 "$SKILL/../_shared/scripts/drive_upload.py" "<final .md>" "<folder link or id>"
```

`<final .md>` is the proofread copy if `mos-proofread` ran, otherwise the article. Report
the link. A re-upload creates a new file; trash superseded copies only when asked.

## Key references

| Reference | Path | Purpose |
|-----------|------|---------|
| Brain context | `$SKILL/../_shared/brain-context.md` | Brain root, voice, audience, domain, competitors |
| Output routing | `$SKILL/../_shared/content-output-routing.md` | Where briefs and articles are saved |
| Writing rules | `references/writing-rules.md` | SEO, GEO, EEAT, linking, tables, CTA rules |
| Brief type handlers | `references/brief-type-handlers.md` | Parsing and writing rules per brief type |
| Quality checklists | `references/quality-checklists.md` | Verification checklists per brief type |
| Prose craft | `mos-copywriting` skill, `references/prose-craft-rules.md` | Sentence craft, punctuation, locale |
| Linter | `mos-copywriting` skill, `Tools/lint-copy.ts` | Deterministic anti-slop checks |
| Humanizer | `../mos-content-humanizer/SKILL.md` | Mandatory de-AI pass on the full draft (Phase 4) |
| Reader research | `mos-copy-research` skill | The reader research bank the Copywriter reads |
| QA | `mos-proofread` skill | The independent pre-publish pass |
