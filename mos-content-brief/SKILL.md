---
name: mos-content-brief
description: >
  Build an SEO + GEO article brief as ONE Markdown file through the full research
  pipeline (keyword, SERP, information gain, sitemap), grounded in the MarketingOS brain's
  voice, audience and offers: keyword data and the live top 10 (DataForSEO, pay per use),
  competitor headings, word counts and term targets (pages fetched free with Scrapling and
  analysed locally), primary-source stats the SERP misses, what AI Overviews, AI Mode and
  ChatGPT cite, and internal links checked against the live sitemap. No subscription.
  Writes one `-brief.md` (guideline tables plus a SERP-driven outline) and a `research/`
  folder. Missing keys are named and skipped.
  Use when the user says "content brief", "generate brief", "new brief", "write a brief",
  "create content brief", "SEO brief", "article brief", "blog brief" or "GEO brief".
  NOT FOR a quick no-API copy brief (mos-copy-brief); "best X for Y" buyer's guides
  (mos-content-best-x-for-y); page optimisation; writing the article (mos-content-writer);
  proofreading (mos-proofread).
allowed-tools:
  - Read
  - Grep
  - Glob
  - Bash
  - Write
  - Edit
  - WebFetch
  - WebSearch
  - Task
  - AskUserQuestion
---

# Content Brief Generator

Build a production-ready SEO and GEO content brief as one final Markdown file, for the brand whose MarketingOS brain you are in.

## Before you start: paths

This skill's shared files live in the pack's `_shared/` folder, next to this skill folder in the mos-content-skills repo. `setup.sh` links only the skill folders into `~/.claude/skills/`, so resolve the real path first and use `$SKILL/../_shared/...` everywhere:

```bash
SKILL="$(cd "$(dirname "$(readlink -f ~/.claude/skills/mos-content-brief/SKILL.md)")" && pwd)"
BRAIN=$(git rev-parse --show-toplevel 2>/dev/null || pwd)
```

`~/.claude/skills/_shared` is a different folder from another pack. Never read from it.

Read these once per run:

- `$SKILL/../_shared/brain-context.md`: how to find the brain, its voice, audience, offers, domain and market, and how API keys resolve
- `$SKILL/../_shared/content-output-routing.md`: where the brief goes, file names, canonical labels, the Drive step
- `$SKILL/../_shared/templates/content-brief-template.md`: the master shape you fill

> ## HARD RULE: bold-label blocks in the master
>
> The three guideline blocks in the working master (**Brand Guidelines**, **Content Guidelines**, **Publishing Guidelines**) use plain Markdown: `**Bold Label**` on its own line, a blank line, then the content (paragraphs and `- ` bullets). Never hand-write pipe tables in the master; the builder makes the tables.
>
> **The blank line after every bold label is mandatory.** Scan the master before building: if a bold label is followed directly by text on the next line, fix it.
>
> **Building the final file:** write the working master to a temp folder, then run `python3 "$SKILL/../_shared/scripts/build_final_md.py" <master.md> <brief folder>`. It needs only the Python standard library, builds the three guideline tables, adds the outline, applies the house formatting and writes ONE file: `<brief folder>/<date>-<slug>-brief.md`.

> ## HARD RULE: output standard
>
> **One deliverable file**: `<topic folder>/blog/brief/<date>-<slug>-brief.md`. Every supporting file (Information Gain research, sitemap list, SERP and competitor extracts, AI-search captures, notes) goes in `<topic folder>/blog/brief/research/`. Internal schema, funnel or developer sections go after the outline in the master and land in the brief under `# Supporting Notes`. No `.docx`, no side files.
>
> **Optional top block.** If the brief has a key strategic finding, put it ABOVE `# The Brief: Strategy & Guidelines` in the master (the builder keeps everything above that heading as the top block):
> 1. `# Content Brief: <Topic>`
> 2. A 2-column summary table (`| | |` header) with rows: Brand, Date, Primary keyword (with volume, KD and CPC, or "Not available (no DATAFORSEO key)"), Content type, Goal.
> 3. `## Key findings`: 3 to 5 bullets with **bold lead-ins**.
>
> Never use bare bold lines for this block; Markdown runs them together.
>
> **House formatting:** no "live page reproduced verbatim" intro line; tight lists (no blank line between bullet items, no empty lines inside table cells); no `.webp` images (Google Docs cannot show them: re-fetch as PNG or JPG); no horizontal rules (`---`, `* * *`).

## Toolchain

Seven systems feed the brief. **No subscription is needed.** The default stack is DataForSEO (one pay-per-use key, roughly US$0.10 a brief at October 2026 prices) plus Scrapling (free) plus WebSearch and WebFetch. Thruuu, Surfer, Apify and Firecrawl are optional extras, used only when their key is set. When a key is missing, say which one, say what that step would have added, and carry on with what still runs. A missing metric is written `Not available (no <PROVIDER> key)`. Never invent a number, a URL or a Surfer link.

Every DataForSEO call reports its cost (`[cost] $X` on stderr, `cost_usd` in JSON). Add them up and report the total spend in Phase 6.

### 1. DataForSEO (keyword research, SERP and the brand's rankings)
Full reference: `$SKILL/../_shared/toolchain-dataforseo.md`.

```bash
D="$SKILL/../_shared/scripts/dataforseo_api.py"
python3 "$D" overview    --keywords "<primary keyword>,<variant>" --country <cc>  # volume, CPC, competition, KD, intent
python3 "$D" related     --keyword  "<seed>" --limit 25 --country <cc>            # related keywords
python3 "$D" suggestions --keyword  "<seed>" --limit 25 --country <cc>            # long-tail and question variants
python3 "$D" ranked      --target   <brand-domain> --country <cc>                 # cannibalisation check, internal-link sources
```

The top 10, the AI Overview and People Also Ask come from the SERP call inside `serp_outline_builder.py` (system 2), so do not call `serp` separately.

Each prints JSON. If a call errors, report it. No DataForSEO key: People Also Ask and Google autocomplete seen through WebSearch supply the question variants (label them manual), every metric reads `Not available (no DATAFORSEO key)`, and the cannibalisation check reads the same.

**Country:** the brain's market from `.mos/config.yaml` or `CONTEXT.md`, else ask. `au` for Australia.

### 2. SERP content analysis (headings, word counts, themes, term targets)
Full references: `$SKILL/../_shared/toolchain-scrapling.md` and `$SKILL/../_shared/toolchain-dataforseo.md`. `serp_outline_builder.py` in this skill folder does the work:

1. Gets the top 10 from the DataForSEO live SERP (about US$0.004, AI Overview and People Also Ask included)
2. Fetches each page with Scrapling (`scrapling extract get`, then `fetch` for JavaScript pages), then `fetch_page.py` (Firecrawl only when its key is set); a page none of them could read is listed under `needs_webfetch` for you to read with WebFetch
3. Extracts H1 to H3 headings and body word counts locally, filtering noise (navigation, CTAs, pricing strings)
4. Clusters headings into themes and counts how many pages cover each (`theme_page_counts`): the common themes are table stakes, the rare ones are differentiation opportunities
5. Calculates word count stats (average, median, min, max) to set the target
6. Extracts term targets from the fetched pages (`terms`: phrase, pages using it, min to max usage); `--terms-md` prints them as brief-ready bullets

It caches to the system temp folder (`serp_<cc>_<keyword>.json`; `--no-cache` forces a fresh run) and exits 0 even when a provider is missing: read `gaps`. No DataForSEO key: run WebSearch for the keyword and pass the top result URLs with `--urls "u1,u2,..."`; the same local extraction runs for free and the SERP is labelled approximate. Thruuu is used instead of DataForSEO only when `THRUUU_API_KEY` is set and DataForSEO is not (`toolchain-thruuu.md`).

### 3. Brain context (voice, audience, offers, restrictions)
Read `$SKILL/../_shared/brain-context.md` and follow it. In short: `.mos/config.yaml`, `CONTEXT.md`, the brain's `CLAUDE.md`, `business/brand/` (brand and voice), `business/audience/`, `business/offers/`, `business/proof/`, `business/competitors/`, and `reference/` when present. Scan `content/` for earlier briefs and articles on related topics.

**You MUST read what exists before building the brief.** The brand's voice, offer, differentiators and restrictions shape the outline. When something the brief needs is missing, ask once (see Required Context) and record the assumption in the brief.

### 4. Sitemap verification (internal link validation)
Full reference: `$SKILL/../_shared/toolchain-sitemap.md`.

**Mandatory.** Every internal link in the brief is verified against the brand's live sitemap. Never guess, assume or hallucinate a URL.

1. Look anywhere in the brain for a `*-sitemap-urls.md` file under 30 days old; if found, it is the source of truth.
2. Otherwise read the live sitemap (`/sitemap.xml`, `/sitemap_index.xml`, or the `Sitemap:` line in `robots.txt`), including every child sitemap, and save the full list to the brief's `research/` folder.
3. Select internal links ONLY from that list: relevant service or product pages, related blog posts (topical clustering), audience or industry pages.
4. If the brain keeps its own internal link list (CLAUDE.md or `reference/`), cross-check it and flag URLs that do not exist.
5. Pre-launch brand with no site: say so, and the Internal Linking field reads "No live site yet".

Hallucinated URLs become broken links when writers use them verbatim. The sitemap also surfaces recent blog posts that guessing misses.

### 5. Information Gain Researcher (rare-stat mining from PDFs, slides, docs and sheets)
Mines deep-document sources (academic papers, government reports, standards bodies, industry research decks) for at least 20 rare, citable stats no competitor in the SERP uses. Output is a Markdown file in the brief's `research/` folder plus a short summary of the top 5 stats and where they fit in the outline.

**Why:** content that adds information the SERP does not already have is more citable, more linkable and harder for AI summaries to reproduce. SERP analysis tells us what everyone is saying; Information Gain tells us what nobody is citing yet. Background: <https://www.seoriddler.com/p/information-gain-in-seo>.

It runs 12+ file-type-operator searches (`filetype:pdf "topic"`, `inurl:"gov" filetype:pdf "topic"`, `site:edu filetype:xlsx "topic"` and so on) with WebSearch and WebFetch, filters out blog posts and news, favours `.gov`, `.edu`, `.org` and international institutions, and flags anything older than 5 years. It needs no API key. Full instructions: `agents/information-gain-researcher.md`.

### 6. AI search capture (Google AI Overview, AI Mode and ChatGPT)
`ai_search.py` captures the AI Overview (text and sources), the Google AI Mode answer and the ChatGPT answer and citations for the primary keyword. Default provider: DataForSEO (pass `--serp-json` with the builder's JSON so the AI Overview is reused, not paid for twice). Apify is an optional extra used only when DataForSEO is not set. With neither, each engine reads `Not available (no DATAFORSEO key)`; you may add what a manual WebSearch shows of the AI Overview, labelled as a manual check.

### 7. SurferSEO (Content Editor, optional extra)
Full reference: `$SKILL/../_shared/toolchain-surfer.md`.

Only when `SURFERSEO_API_KEY` is set. It creates the Content Editor the writer works in and adds Surfer's own term ranges, topics and AI Search facts on top of the local term targets from system 2. Without it the brief still carries the local `**Term Targets**` and the Surfer row reads `Not available (no SURFERSEO key)`.

**Cost:** 1 Content Editor credit per create, the same as creating it by hand. Every read is free. The script guards against double-spend with an `Idempotency-Key` and a same-brand reuse lookup. There is no folder API, so filing the editor into a folder stays a manual drag in the Surfer UI.

## Required Context: what the user provides

Before generating a brief you need the following. Ask for anything missing in ONE AskUserQuestion call, offering sensible defaults ("Skip, you suggest") where Claude can propose a value. Do not guess silently.

| # | What | Example | Why |
|---|------|---------|-----|
| 1 | **Primary keyword** | "project management software for small agencies" | The target search term |
| 2 | **Content type** | Blog post, Pillar page, Landing page | Shapes outline structure and depth |
| 3 | **New or Optimisation** | "New" | Must be "New": optimisation briefs are refused (see below) |
| 4 | **URL** | "https://example.com/blog/project-management-software-small-agencies/" | Where it will be published (Claude can propose one) |
| 5 | **Title tag** | "Project Management Software for Small Agencies" | Under 60 characters (Claude can propose one) |
| 6 | **Meta description** | "Compare tools that plan, track and bill client work..." | Under 160 characters (Claude can propose one) |
| 7 | **Publishing notes** | "Australian English, mention the free 14-day trial" | Writer instructions |

The brand itself, its domain, voice and audience come from the brain (`brain-context.md`). Ask for them only when the brain does not have them.

**Optimisation is refused up front.** This pack has no optimisation-brief skill yet. If the user asks to optimise, refresh or rewrite an existing live page, or answers "Optimisation" to row 3, stop before any research or API spend and say so: "mos-content-brief only builds briefs for new content. There is no optimisation brief in this pack yet. I can write a fresh brief for a new page on this keyword instead." Continue only if they choose a new page; the `New or Optimisation` field is then always `New`.

### Auto-gathered by Claude

| What | Source | Output |
|------|--------|--------|
| Search volume, KD, CPC | DataForSEO `overview` | e.g. "700/mo, KD 2, CPC $0.90" |
| Secondary keywords and volumes | DataForSEO `related` and `suggestions` (WebSearch PAA fallback) | 5 to 10 related terms |
| SERP landscape | `serp_outline_builder.py` (DataForSEO SERP; WebSearch `--urls` fallback) | Top 10 URLs, titles, positions |
| Competitor heading structures | `serp_outline_builder.py` (Scrapling fetch, local extraction) | H1/H2/H3 per competitor page |
| Theme frequency and gaps | Theme clustering | Table stakes vs opportunities |
| Word count benchmarks | `serp_outline_builder.py` | Average, median, target |
| Term targets | `serp_outline_builder.py --terms-md` | Phrases with usage ranges and page counts |
| Brand's existing rankings | DataForSEO `ranked` | Cannibalisation check |
| Featured snippet, AI Overview, People Also Ask | the builder's SERP call | Opportunity assessment, FAQ questions |
| **Internal links (verified)** | **Live sitemap** | **5 to 10 verified URLs with anchor text** |
| **AI search visibility** | **`ai_search.py` (DataForSEO)** | **AI Overview, AI Mode and ChatGPT citations** |
| **Surfer editor (optional)** | **`surfer_api.py brief-block`** | **Share link, Surfer term ranges, topics** |

## Workflow

### Phase 0: Provider check (fast, never blocking)

Check which providers are available before research, so the run summary can say what was skipped. Run from the brain root so the scripts find its `.env`. Every probe here is free:

```bash
cd "$BRAIN"
S="$SKILL/../_shared/scripts"
python3 "$S/dataforseo_api.py" balance >/dev/null 2>&1 && echo "DataForSEO: ok" || echo "DataForSEO: unavailable"
command -v scrapling >/dev/null && echo "Scrapling: ok" || echo "Scrapling: not installed (fetch_page.py tiers, then WebFetch)"
# Optional extras, reported only:
python3 "$S/apify_common.py"                                   # apify token resolved: True/False
python3 "$S/surfer_api.py" check >/dev/null 2>&1 && echo "Surfer: ok" || echo "Surfer: unavailable"
python3 "$S/fetch_page.py" --check                             # which fetch tiers (incl. Firecrawl) are usable
```

Surfer: a `401` means the key is not resolving on Surfer's side, a `403` means the key is fine but the plan is not; do not use `/api/v1/locations` as a test (it is public).

Print a one-block summary, for example:

```
DataForSEO: ok (keyword data, top 10, AI Overview, AI Mode, ChatGPT)
Scrapling: ok (free page fetches)
Surfer: unavailable (no SURFERSEO_API_KEY): optional, local term targets cover it
Proceeding to Phase 1...
```

If DataForSEO is unavailable, say once that it is the one recommended key (pay per use, a few cents a brief) and that the brief will run on WebSearch with every metric marked `Not available (no DATAFORSEO key)`. If the user wants a provider they have a key for, they can add it to the brain's `.env` and re-run. Never ask for a key in chat and never write one into a file yourself.

### Phase 1: Load brain context

1. Find the brain root and read `.mos/config.yaml`, `CONTEXT.md` and the brain's `CLAUDE.md`.
2. Read the brand, voice, audience, offers, proof, competitors and restriction files that exist (`brain-context.md` section 2).
3. Scan `content/` for earlier briefs and articles to reference and to avoid duplicating.
4. Ask for anything missing (Required Context), in one AskUserQuestion call.

### Phase 1.5: Verify internal links (sitemap)

**Mandatory.** Spawn an agent with `agents/sitemap-verifier.md`, passing the brand name, domain, keyword, brain root and the brief's `research/` path. Run it in parallel with Phase 2.

It returns 5 to 10 verified links, formatted `https://example.com/path/ (anchor: natural anchor text)`, and saves the full URL list to `research/`.

### Phase 2: Keyword research

Spawn an agent with `agents/keyword-researcher.md`, passing the primary keyword, brand domain, country and the shared scripts path. Run it in parallel with Phase 1.5.

1. **Overview:** volume, KD, CPC and intent for the primary keyword and close variants (`overview`)
2. **Related keywords:** volume above 10, same intent; the 5 to 8 strongest secondary keywords (`related`)
3. **Suggestions:** "how to", "what is", "cost of", "best" variations (these feed the FAQ), plus the People Also Ask questions from the Phase 3 SERP call (`suggestions`)
4. **Brand's ranked keywords:** flag cannibalisation and note the brand's strongest ranking pages as internal-link sources (`ranked`)

### Phase 3: SERP content analysis

Spawn an agent with `agents/serp-analyzer.md`, passing the primary keyword, country, this skill's real path, and the brief's research folder, date and slug. Spawn it in the **same turn** as the Phase 3.5 Information Gain agent so they run in parallel.

1. Run `serp_outline_builder.py "<keyword>" --country <cc>` (no DataForSEO key: pass WebSearch result URLs with `--urls`); keep its JSON in `research/` as `<YYYY-MM-DD>-<slug>-serp.json`
2. It extracts competitor H1 to H3 headings and word counts; only pages over 300 words with real H2s count. Read any `needs_webfetch` URLs with WebFetch if their headings matter
3. Use `theme_page_counts` for how many competitors cover each theme
4. Word count stats; target the top quartile (average to max, capped at 800 above the average)
5. **SERP gaps:** themes fewer than 2 competitors cover; missing commercial or technical angles; missing standards or compliance content; brand capabilities no competitor mentions
6. **Term targets:** `serp_outline_builder.py "<keyword>" --terms-md` prints the `**Term Targets**` field from the cache (no second SERP call)

### Phase 3.4: Surfer Content Editor and guidelines (optional extra)

Skip this phase when Phase 0 found no working Surfer key; the Surfer row then reads `Not available (no SURFERSEO key)` and the local Term Targets stand on their own.

Run it AFTER Phase 3 has set the target word count (Surfer only accepts it at creation), while the Information Gain agent is still running:

```bash
python3 "$SKILL/../_shared/scripts/surfer_api.py" brief-block \
  --client "<brand>" \
  --main-keyword "<primary keyword>" \
  --secondary "<secondary 1>" --secondary "<secondary 2>" \
  --location "<Surfer location, e.g. Australia>" \
  --target-word-count <Phase 3 target> \
  --notes "<Brand> | <Month YYYY> | <slug>"
```

- **Secondary keywords** come from Phase 2; the script caps at Surfer's limit of 19.
- **The `--notes` stamp is mandatory.** It makes the editor findable for the manual folder drag and lets the reuse guard claim it on a re-run instead of spending a second credit.
- **`--location`** must be a valid Surfer location string; check with `surfer_api.py locations --grep <country>`.
- **Cost: 1 Content Editor credit**, unless the script reuses a same-keyword, same-brand editor from the last 30 days. It prints `CREATED` / `REUSED` to stderr.
- **Never blocks.** On quota exhaustion, auth failure or timeout it emits a placeholder block and exits 0. Note the warning for the Phase 6 summary.

Capture stdout verbatim; it is the `**Surfer SEO**` field. The command polls until Surfer finishes (typically 1 to 3 minutes).

### Phase 3.5: Information Gain research

Spawn an agent with `agents/information-gain-researcher.md` in the **same turn** as the Phase 3 SERP analyser. Pass:

- **Primary keyword**
- **Brand name and a one-line industry description** (from the brain)
- **Output path**: `<topic folder>/blog/brief/research/<YYYY-MM-DD>-<slug>-information-gain.md` (Markdown only, same date and slug as the brief)
- **SERP gap themes**, if Phase 3 has already returned; otherwise the researcher mines the topic broadly
- **Data type preference**: default "mix of stats, quotes, case studies, charts"
- **Document type preference**: default "all types (PDF, PPTX, DOCX, XLSX, Google Docs, Google Sheets)"

It returns a **TOP 5 STATS TO WEAVE INTO THE BRIEF OUTLINE** summary. Those become explicit `Cite stat:` bullets in the outline (Phase 4D). The research file is the writer's deep reference; the bullets tell them where each stat goes.

Fewer than 10 usable stats does not block the brief. Note the gap in the summary: thin primary-source data is itself a signal worth recording.

### Phase 4: Build the brief data

The brief has four parts, mapping to the final file's three guideline tables plus the outline.

#### A. Brand Guidelines

Populate every field from the brain. Never carry values over from an earlier brief for another brand.

| Field | Source | How to populate |
|-------|--------|----------------|
| Customer Avatar | `business/audience/*.md` | Brand name and headline, then `- ` bullets for each audience segment with key pains and goals |
| Tone of Voice | `business/brand/voice.md` (or the brain's voice file) | Headline per segment, then `- ` bullets of voice attributes (plain, expert, no jargon and so on) |
| Restrictions and Guidelines | brain `CLAUDE.md`, `business/brand/`, `business/operations/` | "CANNOT Do:" then `- ` bullets (regulatory, legal, brand); a blank line; "MUST Do:" then `- ` bullets |
| USPs | `business/offers/`, `business/proof/` | `- ` bullets: each USP as a short name plus one line of proof (results, awards, client count, guarantees) |
| Author / Byline (optional) | the brain, or ask | The ideal author and the credentials that fit this topic |

If a field has no source in the brain, write what you assumed and mark it, for example `Not documented in the brain; assumed: plain, direct, Australian English`.

#### B. Content Guidelines

**List format:** `- ` starts a bullet; a blank line separates logical groups; anything else is a plain paragraph.

| Field | How to populate |
|-------|----------------|
| Focus keyword(s) | Primary line with metrics (or `Not available (no DATAFORSEO key)`), blank line, "Secondary:", then `- keyword (vol/mo)` per secondary keyword |
| New or Optimisation | From the user |
| Search intent | A paragraph on the searcher, "They want to understand:", `- ` bullets of intent points, then a closing paragraph |
| Content type | From the user |
| Buying journey | A two-line Schwartz read; this is the source of truth the writer inherits for where the article opens. **Awareness Stage**: Unaware, Problem-Aware, Solution-Aware, Product-Aware or Most-Aware, inferred from intent (informational: Unaware or Problem-Aware; "best", "vs", "reviews": Solution-Aware; branded or "pricing": Product-Aware or Most-Aware) and cross-checked against the audience file. **Market Sophistication**: Stage 1 to 5, judged from the live SERP (if every competitor makes the same claim, you are at Stage 3 or above and a bare claim will not land: a mechanism or identity angle is needed). One line of rationale each. |
| Internal Linking | `- URL (anchor: anchor text)` per verified link |
| External Linking | Default: "Only link out to reputable sources (.gov, .org, academic journals). Never link to competitors." |
| Target audience | "Primary: ...", blank line, "Secondary: ..." |
| Word Count | "{target_min} to {target_max} words" |
| What is missing in the SERPs? | `- ` bullets, one per gap from Phase 3 |
| Previous Content Examples | `- ` bullets of related briefs or articles from the brain's `content/` (full URLs where published) |
| Content Goals | `- SEO: ...`, `- Lead generation: ...`, `- Education: ...` |
| Featured Snippet | One paragraph: whether one exists, and the opportunity |
| AI Search Visibility | **Capture live AI search:** `python3 "$SKILL/../_shared/scripts/ai_search.py" "<primary keyword>" --country <cc> --serp-json <research/...-serp.json> --md` and paste the output **verbatim** (AI Overview text and sources; AI Mode text and sources; ChatGPT snippet and citations; the deduped AI-cited domains). For the "Only cited by AI" theme diff, also run it with `--json > ai.json`, then `python3 "$SKILL/../_shared/scripts/ai_citation_themes.py" --ai-search-json ai.json --serp-themes-json <research/...-serp.json> --md` and append it. Then add 1 to 2 lines of citability strategy (answer-first H2s, 40 to 60 word answers, named stats, FAQ) aimed at the cited-but-not-owned domains; `references/geo-citation-guide.md` has the sentence-level rules. `--skip-chatgpt` saves about US$0.03 per call. "None present" is a valid result. Then append Surfer's AI Search facts block from Phase 3.4 if present. No DataForSEO or Apify key: `Not available (no DATAFORSEO key)`. |
| Term Targets | **Paste `serp_outline_builder.py "<keyword>" --terms-md` output verbatim**: the phrases the top 10 use, each with its usage range and page count. Work the strongest ones into the relevant outline sections as writer bullets (`- Use terms: ...`). Fewer than 2 pages fetched: `Not available (fewer than 2 competitor pages fetched)`. |
| Surfer SEO (optional) | Only with a Surfer key: **paste the Phase 3.4 stdout verbatim**, as dot points: the editor permalink, Surfer's word count (cross-checked against the SERP benchmark target), heading and body terms with `(min-max)` ranges, and expected topics. Any Surfer topic or People Also Ask question the outline does not cover becomes an explicit writer bullet in the relevant section (Phase 4D). No Surfer: `Not available (no SURFERSEO key)`. **Never fabricate a Surfer link.** |
| Research Pages | `- URL (description)` per competitor page studied |

#### C. Publishing Guidelines

| Field | How to populate |
|-------|----------------|
| URL slug | The full absolute URL, from the user or proposed |
| Title tag | Under 60 characters |
| Meta description | Under 160 characters |
| Additional publishing notes | 5 to 8 bullets: brand restrictions, differentiation angles from the gap analysis, tone instructions, CTA targets, spelling conventions. **Always** include the bullet "Humanizer: the draft must clear mos-content-humanizer before proofreading (no not-X-but-Y contrasts, one-line closers, forced triads, stock AI words, decorative bold)" |

#### D. SERP-driven article outline

The core deliverable, built from the theme data, the SERP data and the brand context.

**Heading format (REQUIRED):** every outline heading is a real Markdown heading at its true level (`# Title`, `## Section`, `### Subsection`), as in the template. Never prefix headings with `H1:` / `H2:` labels, never bracket the level, never flatten levels. The hash count IS the level, so the writer can copy a heading as-is.

**Construction rules:**
1. **Table-stakes themes first:** themes 3+ competitors cover MUST be in the outline.
2. **Gap themes as differentiators:** themes fewer than 2 competitors cover are the unique angle; mark them `**SERP gap:**` in the writer guidelines.
3. **Brand sections:** a "Why choose [Brand]" section built from the brain's differentiators and proof, and a CTA conclusion linking to the relevant verified pages.
4. **FAQ section:** 4 to 6 questions from search suggestions, FAQ-theme headings and common objections in competitor content.
5. **Key Takeaways:** near the top, the 4 to 5 most important points, each a self-contained claim under 17 words.
6. **Information Gain stats:** weave the top 5 stats into the sections they fit best. Each gets its own bullet:

   `- Cite stat: "<verbatim stat>" (<Source Name>, <Year>), see the Information Gain research file for the full URL`

   The intro hook, a benefits or cost section and the conclusion are the highest-value placements.
7. **GEO structure:** answer-first sentences at the top of each section, lists and tables for enumerations, and short declarative key claims (see `references/geo-citation-guide.md`).

**Writer guidelines format (REQUIRED):** under every heading, scannable bullets, not a paragraph of bracketed instructions.

- Every section opens with `**Writer guidelines**: target ~XXX words` (plain paragraph)
- Then `- ` bullets, each ONE idea, under about 20 words

Example master outline:

```markdown
## Article Outline

# Main Title Targeting the Primary Keyword

**Writer guidelines**: target ~120 words

- Open with [hook]
- State [key claim or stat]
- Promise what the article delivers
- Include link: https://example.com/page/ (anchor: "anchor text")

## Key Takeaways

- Takeaway 1: key fact or benefit
- Takeaway 2: ...

## Section From a Table-Stakes Theme

**Writer guidelines**: target ~150 words

- Cover: [topic A]
- Reference competitors: [X #7 and Y #15 both cover this; match their depth]
- Go deeper on: [differentiation angle]
- Cite stat: "<verbatim stat>" (Source Name, Year), see the Information Gain research file for the full URL
- Include link: https://example.com/service/ (anchor: "service name")

### Subsection

**Writer guidelines**: target ~100 words

- **SERP gap:** no competitor covers [angle]; own it
- Cover specific detail: [what]

## Why Choose [Brand]?

**Writer guidelines**: ~30 words intro plus bullets

- Differentiator 1 from the brain, with its proof
- Differentiator 2

## Frequently Asked Questions

### Question From Search Suggestions?

**Writer guidelines**: ~60 to 80 words

- Answer the question directly in the first sentence
- Expand with [specific detail]

## Conclusion

**Writer guidelines**: target ~120 words

- Summarise the key message
- Strong CTA
- Include link: https://example.com/contact/ (anchor: "get in touch")
```

**Every section's writer guidelines include:** the target word count; what to cover; which SERP competitors informed it (where relevant); where to differentiate (`**SERP gap:**`); Information Gain stats where they fit; internal links as FULL URLs with anchor text, never relative paths or bare domains.

### Phase 4.9: Humanizer pass (mandatory, runs automatically)

Before writing the master, run `mos-content-humanizer` in embedded mode on every piece of **publishable copy this brief drafts**: the title tag, the meta description, and any sample intro, FAQ answer, CTA or paragraph the writer is meant to reuse. Read `$SKILL/../mos-content-humanizer/SKILL.md` and its `references/` files, then edit that copy in place.

Out of bounds: keyword data, DataForSEO, SERP-analysis, term-target and Surfer figures, outline headings the SERP research dictates, URLs, internal links and anchors, and `Cite stat:` figures. Character limits still apply after the rewrite (title under 60, meta under 160).

If `mos-content-humanizer` is not installed, say so in the run summary and apply its core checks by hand: no not-X-but-Y contrasts, no one-line closers, no forced triads, no stock AI words, no decorative bold, no em dashes.

### Phase 5: Build the final Markdown file

The deliverable is ONE file, `<topic folder>/blog/brief/<YYYY-MM-DD>-<slug>-brief.md`, built by `build_final_md.py`. Routing, naming and month folders (`MM-Mon`): `$SKILL/../_shared/content-output-routing.md`. Reuse an existing topic folder for the same slug before creating one.

1. **Write the working master to a temp folder** (`TMP=$(mktemp -d)`), named `<YYYY-MM-DD>-<slug>-brief.md`, using the canonical section and label names:
   - Optional top block (HARD RULE above): `# Content Brief: <Topic>`, the 2-column summary table, `## Key findings`
   - `# The Brief: Strategy & Guidelines`
   - `## Brand Guidelines` (`**Customer Avatar**`, `**Tone of Voice**`, `**Restrictions and Guidelines**`, `**USPs**`, optional `**Author / Byline**`), `## Content Guidelines` (Focus keyword(s) through Research Pages, including `**Buying journey**` and `**AI Search Visibility**`), `## Publishing Guidelines` (URL slug, Title tag, Meta description, Additional publishing notes), all as bold-label blocks
   - `## Article Outline` as real Markdown headings, then any internal `## Schema Spec` / `## Cluster / Funnel Context` / `## API Data Notes`

   Exact labels are what make the tables fill completely.
2. **Build the final file:**
   ```bash
   python3 "$SKILL/../_shared/scripts/build_final_md.py" \
     "$TMP/<YYYY-MM-DD>-<slug>-brief.md" \
     "$BRAIN/content/<YYYY>/<MM-Mon>/<YYYY-MM-DD>-<slug>/blog/brief"
   ```
   It prints the path of the file it wrote.
3. **Delete the temp master** (`rm -rf "$TMP"`). The final `-brief.md` is now the editable source.

### Phase 6: Verify and report

1. `blog/brief/` holds exactly one `-brief.md` plus `research/`. No `.docx`, no side files, no leftover master.
2. Open the final file: the three guideline tables are filled (rows start `| `; "Not provided" only where the brain genuinely had nothing), the outline uses real `#`/`##`/`###` headings, and the top block (if used) has its summary table and `## Key findings`.
3. House formatting: no "live page reproduced" line, no blank lines between list items, no `.webp` (`rg -n "webp"` returns nothing), no `---` or `* * *` rules.
4. The Surfer row holds either a real `https://app.surferseo.com/...` permalink or an honest `Not available` / placeholder line, never an invented link.
5. Report to the user:
   - The final `-brief.md` path
   - Brief title, primary keyword and volume (or "not available")
   - Number of H2 sections and the target word count
   - Key SERP gaps and the differentiators used
   - **Providers:** which ran, which were skipped for a missing key, and what each skipped step would have added
   - **Spend:** the total DataForSEO cost of the run (sum of every `[cost]` / `cost_usd`), plus any Surfer credit
   - **Surfer** (if used): the editor link, `CREATED` (1 credit) or `REUSED` (0 credits), any warning, and the manual step: drag the editor into the right Surfer folder (it is stamped `<Brand> | <Month YYYY> | <slug>`)

### Phase 7: Google Drive upload (separate final step: ASK, never assume)

After reporting, always ask with AskUserQuestion: *"Which Google Drive folder should I upload this brief to?"* The user pastes a folder link via Other, or picks "Skip, keep it local". Never guess a folder. If the brain records a briefs folder, offer it as an option; the user still picks.

Then follow the Drive step in `content-output-routing.md`: the `gws` CLI path (`drive_upload.py "<final .md>" "<folder link or id>"`, one styled Google Doc), else the Google Drive connector, else skip silently. Report the Doc link.

## Output folder structure

```
content/<YYYY>/<MM-Mon>/<YYYY-MM-DD>-<slug>/
└── blog/
    └── brief/
        ├── <YYYY-MM-DD>-<slug>-brief.md                 THE deliverable (built by build_final_md.py)
        └── research/
            ├── <YYYY-MM-DD>-<slug>-information-gain.md  Information Gain stats (Phase 3.5)
            ├── <YYYY-MM-DD>-<brand>-sitemap-urls.md     verified sitemap list (Phase 1.5)
            └── ...                                      SERP extracts, AI-search capture, notes
```

`mos-content-writer` later adds `blog/article/<YYYY-MM-DD>-<slug>-article.md`. A brain whose `.mos/config.yaml` or CLAUDE.md declares a different content route wins.

## Quality checklist

- [ ] Brain context read (config, CONTEXT, CLAUDE.md, brand, voice, audience, offers, proof) and reflected; gaps asked about or marked as assumptions
- [ ] Keyword data gathered (volume, KD, CPC, related terms), or each missing metric written `Not available (no <PROVIDER> key)`
- [ ] SERP analysis done: competitor headings extracted and clustered (`serp_outline_builder.py`), term targets in the brief
- [ ] Total DataForSEO spend reported
- [ ] Information Gain research done: 20+ stats in the research file (or the gap noted), saved as Markdown in `research/`
- [ ] Top 5 Information Gain stats woven into the outline as `Cite stat:` bullets
- [ ] Primary keyword and 3+ secondary keywords included, with volumes where available
- [ ] Search intent describes who is searching, mapped to the brain's audience
- [ ] Buying journey has an Awareness Stage and a Market Sophistication line, each with rationale
- [ ] At least 1 SERP gap identified and marked `**SERP gap:**` in the outline
- [ ] Outline has 8 to 14 H2 sections, as real Markdown headings
- [ ] Every section opens with `**Writer guidelines**: target ~XXX words` and uses scannable one-idea bullets
- [ ] Every internal link is a full URL verified against the live sitemap, never relative or guessed
- [ ] Competitor references included where relevant
- [ ] FAQ has 4 to 6 questions from search suggestions and SERP data
- [ ] Title tag under 60 characters, meta description under 160
- [ ] Content goals cover SEO, lead generation and education
- [ ] Word count target benchmarked against competitor data
- [ ] "Why choose [Brand]" uses the brain's differentiators and proof
- [ ] Conclusion CTA links to relevant verified pages
- [ ] No keyword cannibalisation with the brand's existing rankings (checked, or marked not available)
- [ ] Title tag, meta description and any sample copy the brief drafts (intro, FAQ answers) went through a `mos-content-humanizer` embedded pass
- [ ] Additional publishing notes include the Humanizer bullet
- [ ] No invented numbers, URLs or Surfer links anywhere
- [ ] ONE final `-brief.md` in `blog/brief/`, built by `build_final_md.py`; temp master deleted; supporting files in `research/`
- [ ] Top block (if used) sits above `# The Brief`, with summary table and `## Key findings` bullets with bold lead-ins
- [ ] House formatting: no "live page reproduced" line, tight lists, no empty lines in table cells, no `.webp`, no horizontal rules

If the user named a Drive folder:

- [ ] The folder came from the user via AskUserQuestion, never guessed
- [ ] Uploaded as ONE Google Doc (no `--with-md` unless the user asked)
- [ ] Doc link reported

## Example invocation

User (inside a brain): "Create a content brief for 'project management software for small agencies'"

Claude should:
1. Resolve `$SKILL` and `$BRAIN`; read `brain-context.md`, `content-output-routing.md` and the template
2. Phase 0: check providers (free probes) and print what is available
3. Read the brain's config, CONTEXT, CLAUDE.md, brand, voice, audience, offers and proof; scan `content/`
4. Ask in one AskUserQuestion call for content type, URL, title, meta and publishing notes (offering to propose them), plus anything the brain lacks
5. Run sitemap verification and keyword research in parallel
6. Run the SERP analyser and Information Gain researcher in parallel; create the Surfer editor only if a Surfer key is set
7. Capture AI search visibility
8. Build the guideline fields and the SERP-driven outline with `Cite stat:` bullets
9. Run the humanizer pass on the title, meta and any sample copy
10. Write the temp master, run `build_final_md.py` into `content/<YYYY>/<MM-Mon>/<YYYY-MM-DD>-<slug>/blog/brief`, delete the temp master
11. Report the path, H2 count, word count target, key gaps and which providers were skipped
12. Ask about the Google Drive upload
13. Tell the user: "The brief is ready for your review. Once you've approved it, say 'write this brief' and I'll run `mos-content-writer` against this file." Do NOT start the writer automatically: the brief is an intentional review checkpoint.

## Tips for writers using these briefs

- **Writer guidelines bullets** tell you what to write; they are not the content itself
- **Word counts** per section are guidelines
- **SERP references** (e.g. "X #7 covers this") show what competitors do: match or exceed their depth
- **`SERP gap:` markers** are your differentiation opportunities: go deep there
- **`Cite stat:` bullets** point at primary-source data nobody else in the SERP uses: open the Information Gain file in `research/` for the source URL and context before you use the stat
- **Internal links** should be woven into the prose naturally, not listed at the bottom
- **Theme frequency** (e.g. "9 of 10 competitors cover this") tells you which sections are essential
