---
name: mos-content-best-x-for-y
description: >
  Build the brief for one "best X for Y" buyer's guide page: assembles 4 to 10 entries,
  gets your sign-off on criteria and methodology, captures sourced, dated evidence for
  every competitor fact, and assigns "Best for" / "Not for" to every entry. Your brand
  is never ranked first by default and only appears where it passed the eligibility
  gate. Starts from a mos-geo-best-x-for-y shortlist when one exists (gate
  result, handover), otherwise runs a light demand check and gate for that one page.
  Output: one brief per page (ItemList schema, disclosure line, no year in the title)
  for mos-content-writer. USE WHEN the user says "best X for Y brief", "buyer's guide
  brief", "buying guide", "listicle brief", "best of brief", "comparison list", "top
  picks page", "/mos-content-best-x-for-y", or hands over a shortlist page.
  NOT FOR deciding which best-for pages the brand should build (mos-geo-best-x-for-y),
  one-vs-one pages (mos-geo-vs-content), standard articles (mos-content-brief), or
  writing the page (mos-content-writer).
allowed-tools:
  - Read
  - Grep
  - Glob
  - Bash
  - Write
  - Edit
  - WebFetch
  - WebSearch
  - Agent
  - AskUserQuestion
---

# Best X for Y: buyer's guide briefs

You are building briefs for genuine buyer's guides: pages that send every reader to the option
that suits them, the brand's competitors included. The brand earns its place by being the most
useful page on the question, and appears only where it is an honest pick.

This skill was ported from a self-promotional listicle formula (brand ranked first, written at
three times the depth of everyone else, competitors narrowed to niches). That method is retired
here. Read `references/buyers-guide-method.md` before the first run in a session; it holds the
evidence behind every rule below.

## The rules that do not bend

1. **Ask the user first.** Before any research, ask for their page ideas, the avatars that
   matter and anything to avoid (Phase 1).
2. **The eligibility gate decides where the brand appears.** Five tests per page: offer,
   audience, proof, price, availability. Any fail means the brand is left off that page. A
   pre-launch brand passes nowhere. User seeds get no free pass (Phase 3).
3. **The brand is never #1 by default.** A "best overall" exists only when one entry wins on
   the stated criteria, with the evidence named. Otherwise the page leads with "Best for" picks.
4. **Every entry gets "Best for" and "Not for"**, each tied to a stated criterion and to
   evidence rows. The brand's "Not for" is as honest as everyone else's.
5. **The criteria and the methodology block are approved by the user before anything is
   ranked** (Phase 5).
6. **Every competitor fact has a saved snapshot, source URL, capture date and verbatim quote.**
   A value nobody publishes is "Not published". Never estimate.
7. **No year in the title, no fake "updated" dates, no AggregateRating or Review schema.**
   ItemList schema only. A visible "last checked" date replaces freshness theatre.
8. **3 to 5 pages per run.** Never scale to dozens; that is the pattern Google hit.
9. **Never invent numbers.** A metric a missing provider would have supplied is written
   "Not available (no <PROVIDER> key)", and the run carries on.

## Setup

Set `SKILL` to this skill's real folder so the pack's `_shared/` folder (which sits next to
it) resolves through the `~/.claude/skills` link:

```bash
SKILL="$(cd -P <this skill's folder> && pwd)"
```

Then find the brain and its context exactly as `$SKILL/../_shared/brain-context.md` describes:
the brain root, its brand voice, audience, offer, proof, domain and known competitors. Read
what exists; ask the user for anything missing that the gate needs (what the brand sells, who
it is for, price, availability today, proof). Never assume a folder exists.

Routing for every file this skill writes: `$SKILL/../_shared/content-output-routing.md`.
Data file layouts and schemas: `references/data-files.md`.

### Providers (no subscription needed)

| Provider | Key | Used for | Without it |
|---|---|---|---|
| DataForSEO (recommended, pay per use) | `DATAFORSEO_LOGIN` + `DATAFORSEO_PASSWORD` | volume per market (`bxy.py volume`), keyword metrics and questions, the live top 10, ChatGPT, AI Overview and AI Mode answers (`ai_search.py`), the brand's ranked keywords | WebSearch for the visible SERP and questions, labelled approximate; metrics "Not available (no DATAFORSEO key)" |
| Scrapling (free CLI, no key) | none | fetching the ranking pages and competitor pages | `fetch_page.py` tiers, then WebFetch |
| Apify (optional extra) | `APIFY_API_KEY` or `APIFY_TOKEN` | ChatGPT and AI Overview answers when DataForSEO is not set | `mos-geo-brand-360` runner if installed, else WebSearch, labelled as an approximation |
| Thruuu (optional extra) | `THRUUU_API_KEY` | SERP list and headings when DataForSEO is not set | WebSearch URLs passed to `serp_outline_builder.py --urls` |
| Firecrawl (optional extra) | `FIRECRAWL_API_KEY` | page fetch after Scrapling | WebFetch |
| Surfer (optional extra) | `SURFERSEO_API_KEY` | a Content Editor link on top of the local term targets | Surfer row reads "Not available (no SURFERSEO key)" |

Keys resolve from the environment, then a `.env` walked up from the current folder. Toolchain
notes: `$SKILL/../_shared/toolchain-dataforseo.md`, `toolchain-scrapling.md`,
`toolchain-sitemap.md`, and the optional `toolchain-thruuu.md` and `toolchain-surfer.md` (same
folder). At the start, list which providers are available (`dataforseo_api.py balance` is a
free check) and, for each missing one, what the run will lack. Do not stop for a missing key.
Every DataForSEO call reports its cost (`[cost]` on stderr, `cost_usd` in JSON); add them up
and report the run's total spend.

## Starting from a mos-geo-best-x-for-y shortlist

When the brain has `campaigns/geo/YYYY-MM/content-ideas/best-x-for-y/publishing/NN-<slug>.md`, or the user hands one over, the shortlist stage is already done for that page: the user picked it, demand was checked and the brand went through the five-test gate. Read the handover and reuse its seeds, candidates, gate result and engine answers. Skip Phases 1 to 3 and start at Phase 4. Do not re-gate the brand: pass the handover's `gate-result.json` to `bxy.py check --gate` so the built brief cannot put the brand on a page it failed. Run Phases 1 to 3 only when no shortlist exists, and then for this one page.

## Phase 1: Ask first

Before any research, one AskUserQuestion set (every question has a "Skip, you suggest"
option):

1. "Which 'best X for Y' pages do you already have in mind?" (free text via Other)
2. "Which avatars or use cases matter most?" (offer the avatars found in the brain, plus Other)
3. "Anything to avoid?" (segments, competitors you will not name, claims you cannot make)
4. "Which market?" (default the brain's market, else AU)

Save the answers to the shortlist run's `research/seeds.json`. An empty answer is fine.
Everything from here on tags the user's ideas `yours` and the skill's ideas `discovered`.

## Phase 2: Candidates and demand check

1. **Candidate Ys.** Start from the seeds, then add Ys from the brain's avatars crossed with
   use cases and constraints (budget, team size, skill level, industry, location), plus
   keyword suggestions. Aim for 15 to 30 candidates. Save `candidates.json`, each with a
   keyword, a natural buyer prompt ("What's the best CRM for a small marketing agency?") and
   its `source`.
2. **Volume.**
   ```bash
   python3 "$SKILL/scripts/bxy.py" volume --keywords-file research/keywords.txt \
     --country AU --country US --out research/volume.json
   ```
   With no DataForSEO key, volume is "Not available (no DATAFORSEO key)" and the AI answers
   carry the decision. Small volumes
   are normal for these terms; volume is a tiebreaker, not the case.
3. **What the engines recommend today.** Run each buyer prompt through the AI engines and
   record who they recommend, which domains they cite, and whether the brand appears:
   - If `mos-geo-brand-360` is installed, its runner covers ChatGPT, AI Mode and Perplexity:
     `python3 <brand-360 folder>/scripts/brand360.py run --brand "<brand>" --industry "<x>"
     --prompts research/prompts.json --out research/engines --phases api-search,app
     --country <CC>` (prompt format: that skill's `references/prompt-set.md`), then its
     `summarise` command.
   - Otherwise, per prompt: `python3 "$SKILL/../_shared/scripts/ai_search.py" "<keyword>"
     --prompt "<buyer prompt>" --country <cc> --json > research/engines/<id>.json`
     (ChatGPT, the Google AI Overview and AI Mode, through DataForSEO by default; Apify only
     when DataForSEO is not set).
   - With neither, WebSearch the buyer prompt and record the sources that come up, labelled
     "approximation: no AI engine run". Do not present it as what the engines said.
   One run per prompt is a snapshot, not a ranking; say so in the shortlist.

## Phase 3: Eligibility gate and shortlist

For every candidate Y, judge the five tests (offer, audience, proof, price, availability) from
the brain's offer, audience and proof files and the brand's public pages. Write one plain
"why" per test. Then let code apply the rule:

```bash
python3 "$SKILL/scripts/bxy.py" gate --in research/gate.json --out research/gate-result.json
```

The brand is eligible on a page only if all five pass, and never while pre-launch. When a
user seed fails, say which test failed in one sentence and offer the nearest Y that passes.
A failed page can still be a neutral guide that recommends others; that is the user's call.

Write `shortlist.md`: the ranked pages with source (`yours` / `discovered`), volume, AI gap
(engines that did not name the brand), brand on or off, and the gate reason. **Ask the user to
pick 3 to 5 pages** (AskUserQuestion, multi-select, with their own seeds marked). Everything
after this runs once per chosen page; independent pages can run in parallel.

`references/worked-example.md` shows a real shortlist run, including a high-volume Y the gate
correctly rejected.

## Phase 4: Research per page (parallel agents)

Spawn these with the Agent tool in one block, each with the brief inputs listed in its file:

- `agents/keyword-researcher.md`: keyword metrics, questions, SERP, brand rankings.
- `agents/sitemap-verifier.md`: verified internal links (no product links if the brand
  failed the gate for this page).
- `agents/serp-analyzer.md`: heading themes, word count, and what the ranking pages get wrong
  (self-ranking, no method, no downsides, stale prices).

Then build the **candidate set**: the union of the options the engines recommended, the
brands across the Google top 10 and the review-site or directory leaders. Trim to 4 to 10 with
a reason per entry (fewer than 4 is a comparison page: stop and route the user to `mos-geo-vs-content` in the
mos-geo-skills pack, which writes a writer-ready brief per vs page to
`campaigns/geo/YYYY-MM/content-ideas/vs-content/publishing/NN-*/`).
Include the brand only if it passed the gate for this page. Save `entries.json`.

## Phase 5: Criteria and methodology (user approval gate)

Draft 4 to 6 decision criteria for this Y from the questions, the fan-out, the brand's known
objections and reviewers' complaints. The criteria are the same for every entry and none is
chosen to flatter the brand. Draft the methodology block (`references/buyers-guide-method.md`,
"Criteria and the methodology block"): what was compared and why, how facts were gathered and
when, who did it, what was not tested, and the disclosure line ("We make {brand}. It is one of
the options below, judged on the same criteria."; when the brand is off the page, the
disclosure says the author works in the category).

Show both to the user and get approval (AskUserQuestion: approve / edit). Save to
`criteria.md`. **Nothing is ranked before this approval.**

## Phase 6: Evidence capture

Spawn `agents/competitor-researcher.md` (one agent per page, or split entries across 2 to 3
agents for big pages) with the approved criteria and entries. It snapshots each entry's own
pricing and feature pages with `$SKILL/../_shared/scripts/fetch_page.py`, pulls attributed
review quotes, and writes `evidence.csv` plus `snapshots/`. The brand gets exactly the same
treatment. Slots only the brand owner can fill (screenshots, hands-on trials) become
`[OWNER: ...]` placeholders for the writer, and the methodology says what was not tested.

## Phase 7: Picks

For every entry write `picks.json`: position, "Best for" (a real strength a buyer in Y would
value), "Not for" (who should choose something else), the criterion each rests on, and the
evidence ids. Then test fairness before moving on:

- Would each competitor call its "Best for" a genuine strength?
- Is the brand winning more picks than the criteria justify?
- If a competitor is the better fit for one of the brain's avatars, does the page say so?

Order the entries by the approved criteria. The brand is never first by default; a
`best_overall` record is allowed only when one entry wins on the stated criteria, naming the
criterion and the evidence.

## Phase 8: Build the outline

Answer-first, identical structure for every entry. Writer guidelines are scannable bullets
under a `**Writer guidelines**: target ~N words` line, one idea per bullet, full absolute URLs
for every link. Apply `references/geo-citation-guide.md` (standalone 6 to 15 word claim
sentences, front-loaded answers, tables for enumerations).

1. **H1:** "Best {X} for {Y}" plus an honest qualifier if useful. No year. No "#1".
2. **Opening (~120 words):** the quick picks and who each suits, in the first two sentences.
3. **Quick picks table:** Option | Best for | Not for | Starting price (sourced) | Last checked.
4. **How we chose (~200 words):** the approved methodology block and the disclosure line.
5. **One H2 per entry, same template for all (~150 to 300 words each):**
   - Verdict: one standalone sentence.
   - **Best for:** {pick}, because {criterion and evidence}.
   - **Not for:** {who}, because {criterion and evidence}.
   - Price and plans (sourced, dated; "Not published" where it is).
   - What reviewers say (attributed quotes).
   - Evidence ids the writer must keep, and any `[OWNER: ...]` slots.
6. **How to choose for your situation (~200 to 300 words):** by avatar or constraint; it can
   send readers to any entry.
7. **FAQ (4 to 6 questions):** from the question list; each answer opens with a standalone
   sentence; no self-referencing answers.
8. **Close (~80 words):** one soft call to action, only on pages where the brand passed the
   gate; otherwise a pointer to the decision guide.

**Term targets.** `python3 "$SKILL/serp_outline_builder.py" "<kw>" --country <cc> --terms-md`
prints the phrases the ranking pages share, with usage ranges, from the SERP analysis cache.
Paste it into the `**Term Targets**` field.

**Surfer (optional extra, only with a Surfer key).** After the word count is set:
`python3 "$SKILL/../_shared/scripts/surfer_api.py" brief-block --main-keyword "<kw>"
--secondary "<kw2>" --location "<country>" --target-word-count <n> --notes "<brand> | <Month
YYYY> | <slug> (best-x-for-y)"`. Paste stdout verbatim into the Surfer field. It never blocks;
on failure the placeholder ships and the report flags it. Never invent a Surfer link.

## Phase 8.9: Humanizer pass (mandatory, runs automatically)

Before writing the master, run `mos-content-humanizer` in embedded mode on every piece of
**publishable copy this brief drafts**: the title tag, the meta description, and any sample
opening, verdict line, FAQ answer, CTA or paragraph the writer is meant to reuse. Read
`../mos-content-humanizer/SKILL.md` (relative to this skill's folder) and its `references/`
files, then edit that copy in place. Out of bounds: keyword data, DataForSEO, SERP-analysis,
term-target and Surfer figures, outline headings the SERP research dictates, URLs, internal links and
anchors, evidence quotes, prices and ratings, and entry names. Character limits still apply
after the rewrite (title under 60, meta under 160). If `mos-content-humanizer` is not
installed, say so in the report and carry on; the writer will run it on the full draft.

## Phase 9: Write the master and build the one brief

1. Write the working master to a temp dir (`mktemp -d`) as
   `<YYYY-MM-DD>-<page-slug>-brief.md`, using the canonical section and label names in
   `$SKILL/../_shared/content-output-routing.md` and the shape in
   `$SKILL/../_shared/templates/content-brief-template.md`: an optional top block (summary
   table + `## Key findings`), then `## Brand Guidelines`, `## Content Guidelines`,
   `## Publishing Guidelines` (bold-label blocks, blank line after every label), then
   `## Article Outline`. Populate Brand Guidelines from the brain's audience, voice, offer and
   restrictions files. Field values specific to this skill:

   | Field | Value |
   |---|---|
   | Content type | "Best X for Y buyer's guide ({n} entries; brand {included / not included} per eligibility gate)" |
   | Buying journey | Awareness stage: Solution-Aware by default (they know options exist and are weighing them); Product-Aware if the keyword names a brand. Market sophistication: usually Stage 3 to 5 on "best" SERPs, so the page wins on a clear selection method, not a bare "here are the best" claim. One line of rationale each. |
   | Word Count | the serp-analyzer's recommended range, never padded |
   | External Linking | each entry's own pricing or product page (linking to multiple sellers is expected), review sites quoted, and the sources behind the methodology |
   | What is missing in the SERPs? | the serp-analyzer's "what the ranking pages get wrong" list |
   | Research Pages | every snapshot URL, absolute |
   | Title tag | no year, no "#1", under 60 characters |
   | Additional publishing notes | must include: "ItemList schema only. Never add AggregateRating or Review schema."; "Show a visible 'Last checked' date; change it only when the facts were re-checked."; "Disclosure line in the methodology block: {text}."; "Re-check every competitor fact within 90 days of publishing and every 90 days after."; "Australian English" (or the brain's own spelling rule); "Humanizer: the draft must clear mos-content-humanizer before mos-proofread (no not-X-but-Y contrasts, one-line closers, forced triads, stock AI words, decorative bold)." |

2. Build the final file:
   ```bash
   python3 "$SKILL/../_shared/scripts/build_final_md.py" "<tmp>/<date>-<slug>-brief.md" "<page>/blog/brief"
   ```
   Keep `entries.json`, `criteria.md`, `evidence.csv`, `snapshots/`, `picks.json` and every
   other research file in `brief/research/`. Delete the temp master.
3. **Run the sensor; it must pass before the brief ships:**
   ```bash
   python3 "$SKILL/scripts/bxy.py" check --research "<page>/blog/brief/research" \
     --brief "<page>/blog/brief/<date>-<slug>-brief.md" \
     --gate "<shortlist>/research/gate-result.json" --page "<Y>"
   ```
   It fails on a year in the title, AggregateRating guidance, a missing disclosure, methodology
   heading, "last checked" or ItemList instruction, fewer than 4 or more than 10 entries, an
   entry without "Best for" / "Not for" / criterion / evidence, the brand on a page it failed
   the gate for, the brand at #1 without a best_overall record, and evidence that is stale
   (over 90 days), unsourced, or whose quote is not in its snapshot. Fix and re-run until it
   passes. (`python3 -m unittest scripts/test_bxy.py` proves each rule fails when it should.)

## Phase 10: Verify and report

Check, and report pass or fail per item:

- [ ] User was asked first; seeds saved; every seed went through the gate
- [ ] Shortlist shows source, volume (or "Not available"), AI gap and gate reason; the user
      picked 3 to 5 pages
- [ ] 4 to 10 entries, each with a reason it is in
- [ ] Criteria and methodology approved by the user before ranking
- [ ] Every entry has "Best for" and "Not for" tied to a criterion and evidence
- [ ] The brand appears only where it passed the gate and is not #1 by default
- [ ] `bxy.py check` passed
- [ ] Title tag, meta description and drafted sample copy went through a
      `mos-content-humanizer` embedded pass; publishing notes carry the humanizer line
- [ ] Internal links verified against the sitemap
- [ ] Title under 60 characters, meta under 160, no year in either
- [ ] One `-brief.md` in `brief/`, research files in `brief/research/`, no `.docx`
- [ ] Every missing provider named, with what it would have added

Report per page: the brief path, entry count, whether the brand is on the page and why, the
picks in one line each, evidence row count, any `[OWNER: ...]` slots, and the check result.

## Phase 11: Optional Google Drive upload

Ask (AskUserQuestion): "Upload the brief to a Google Drive folder?" with "Paste a folder link"
(via Other) and "Skip, keep it local". Never guess a folder. On a link:
`python3 "$SKILL/../_shared/scripts/drive_upload.py" "<brief.md>" "<folder link or id>"`.
If neither the `gws` CLI nor a Google Drive connector is available, skip silently.

## Next steps to offer (never auto-run)

- "Write this brief" runs `mos-content-writer` on the approved brief; its draft then goes
  through `mos-proofread`.
- After publishing: re-run the Phase 2 prompts 2 to 4 weeks later and log, per engine,
  citation and recommendation as two separate numbers. Re-capture competitor facts every
  90 days.
- One-vs-one pages for the 2 or 3 names the engines put next to the brand: `mos-geo-vs-content`
  (mos-geo-skills pack). It writes a writer-ready brief per page to
  `campaigns/geo/YYYY-MM/content-ideas/vs-content/publishing/NN-*/`, which `mos-content-writer`
  then writes from.

## Files in this skill

| File | Use |
|---|---|
| `references/buyers-guide-method.md` | The method and the evidence behind every rule |
| `references/data-files.md` | Folder layout and the JSON / CSV schemas |
| `references/geo-citation-guide.md` | Sentence and structure rules for AI citation |
| `references/worked-example.md` | A labelled real run of the demand check and gate |
| `agents/*.md` | Briefs for the research agents |
| `scripts/bxy.py` | `volume`, `gate`, `check` (deterministic) |
| `scripts/test_bxy.py` | Sensor probes for `check` |
| `serp_outline_builder.py` | SERP analysis: DataForSEO top 10, Scrapling fetch, local headings, themes and term targets |
