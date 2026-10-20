---
title: Port four agency content skills into mos-content-skills
date: 2026-10-21
status: done
owner: Richard
---

# Port the agency content skills into mos-content-skills

## Objective

`mos-content-skills` is a companion pack to the MarketingOS engine, built the same way as `mos-geo-skills` (flat skill folders, `_shared/`, `setup.sh`). This plan ports four skills from the private agency skill pack this was ported from, renamed to the `mos-content-*` family and stripped of every agency-only path, client and tool.

| Source (read-only, in the private agency skill pack) | Target | Unit |
|---|---|---|
| The source pack's shared folder (only the files listed below) | `_shared/` | U1 |
| The source standard-brief skill | `mos-content-brief/` | U1 |
| The source brief-to-article writer skill | `mos-content-writer/` | U2 |
| The source listicle-brief skill | `mos-content-best-x-for-y/` | U3 |
| The source humanizer wrapper skill | `mos-content-humanizer/` | U4 |

**Source updated 2026-10-21:** the source pack added a humanizer wrapper and wired it into every brief and writing skill as a mandatory step. U1 to U3 must port that wiring, pointing at `mos-content-humanizer` (see decision 10).

The source pack is never edited. Paths below are relative to the root of this repo.

## Decisions already made (do not reopen)

1. **Names:** `mos-content-brief`, `mos-content-writer`, `mos-content-best-x-for-y`, `mos-content-humanizer`. Every reference to a source skill inside the ported files is renamed to its new name. References to source skills that are NOT ported (the source QA, comparison-brief, optimisation-brief, copywriter and Google Doc formatter skills, and the source workspace skills) are removed or replaced: QA → `mos-proofread`; copy craft → `mos-copywriting`; reader research → `mos-copy-research`; comparison (1v1) pages → `mos-geo-vs-content` (planned, not yet released, in mos-geo-skills).
2. **No agency specifics.** No agency workspace names or environment variables, no per-client folder layout or client registry, no agency name, no agency MCP tools, no named agency clients, no agency-branded writer or proofreader agents, no project-management or time-tracking tools, no agency email addresses, and no hardcoded local paths. The skills work in any MarketingOS brain.
3. **Brain, not client.** The working context is the MarketingOS brain the user is in (the git root, which holds `.mos/config.yaml` when it is a brain). Brand voice and audience come from the brain's own context files: read `.mos/config.yaml` and the brain's `business/` and `reference/` folders when present, and ask the user when they are missing. Never assume a folder exists. Agencies with client brains run the skill inside that client's brain.
4. **Output location.** Default: `content/YYYY/MM-Mon/YYYY-MM-DD-<slug>/blog/` in the brain (month folders are `MM-Mon`, e.g. `10-Oct`). Inside it: `brief/<date>-<slug>-brief.md` (the one deliverable) plus `brief/research/` for supporting files; the writer adds `article/<date>-<slug>-article.md`. If the brain's `.mos/config.yaml` or CLAUDE.md declares a different content route, that wins. Document this once in `_shared/content-output-routing.md` (rewritten for brains) and point every skill at it.
5. **Data providers are optional and resolved from the brain.** Keep the Ahrefs API, DataForSEO, Thruuu, Firecrawl and Surfer integrations, but API keys resolve as: (1) environment variable, (2) a `.env` found walking up from the current directory. No hardcoded fallback paths. When a key is missing the skill says which one, says what that step would have added, and carries on with the steps it can still run (WebSearch/WebFetch fallback where the source skill already has one). Never invent numbers: a missing metric is written as "Not available (no <PROVIDER> key)".
6. **Deprecated code is not ported.** The source brief skill's own deprecated generators, renderers and Drive helper are not copied (the build path is `_shared/scripts/build_final_md.py`). Port only what the current SKILL.md instructions actually call. If a SKILL.md step still calls a deprecated script, rewrite the step to the current path.
7. **Markdown is the deliverable.** No `.docx` output by default, matching the source house standard. The optional Google Drive upload step stays, generic: it uploads to a folder the user names, using whichever Google auth the user has (`gws` CLI or the Google Drive connector), and it is skipped silently when neither is present.
8. **Voice and spelling:** Australian English in SKILL.md prose; no em dashes in any prose file you write; plain verbs.
9. **Best X for Y is a genuine buyer's guide, not a self-promotional listicle.** See U3. This is the one unit that changes behaviour, not just names.
10. **Humanizer pass is mandatory in all three content skills.** Port the source's humanizer phase and checklist line from each source skill, renamed to `mos-content-humanizer` and referenced as `../mos-content-humanizer/SKILL.md`. Brief skills humanize the copy they draft (title tag, meta description, sample intro/FAQ/CTA), never keyword data, figures, SERP-dictated headings, URLs or anchors; character limits still apply afterwards. The writer humanizes the full draft before handing it to `mos-proofread`.

## `_shared/` contract (U1 owns it; U2 and U3 only read it)

Vendor these from the source pack's shared folder, strip workspace paths and key fallbacks per decision 5, and keep the rest of each file's behaviour:

- `scripts/ahrefs_api.py`, `scripts/dataforseo_api.py`, `scripts/fetch_page.py`, `scripts/build_final_md.py`, `scripts/drive_upload.py`, `scripts/surfer_api.py`, `scripts/apify_common.py`, `scripts/ai_search.py`, `scripts/ai_citation_themes.py`, `scripts/aio_scrape.py`
- `templates/content-brief-template.md`
- `toolchain-ahrefs.md`, `toolchain-thruuu.md`, `toolchain-sitemap.md`, `toolchain-surfer.md`
- `content-output-routing.md`: rewritten for brains (decision 4)
- New `brain-context.md`: replaces the source's client-folder resolution doc and path helper. How a skill finds the brain root, its brand voice, audience, sitemap/domain and competitors (decision 3).

Path convention (tightened in review): `setup.sh` links only skill folders into `~/.claude/skills/`, and `~/.claude/skills/_shared` belongs to a different pack with same-named files. Every skill therefore resolves its real folder first (`SKILL="$(cd "$(dirname "$(readlink -f ~/.claude/skills/<name>/SKILL.md)")" && pwd)"`) and reads shared files as `$SKILL/../_shared/...`, never as a bare `../_shared/...`. Python scripts find their siblings with `os.path.realpath(__file__)`.

## Units

### U1: `_shared/` + `mos-content-brief` (runs first)

Port the source standard-brief skill as `mos-content-brief`: SKILL.md, `agents/`, `references/`, `serp_outline_builder.py`. Rewrite the frontmatter description for MarketingOS users (trigger phrases kept; mention it is an SEO + GEO article brief built on the full research pipeline; NOT FOR: listicles/"best X for Y" → `mos-content-best-x-for-y`; writing the article → `mos-content-writer`; a quick no-API copy brief → `mos-copy-brief`). Remove `allowed-tools` entries for tools that no longer apply.

### U2: `mos-content-writer` (after U1)

Port the source writer skill. Strictly downstream: a brief from `mos-content-brief` or `mos-content-best-x-for-y` is a hard precondition. The copy step uses the generic `Copywriter` agent if available, otherwise writes in-session, always grounded in the brain's voice file and the brief. For best-x-for-y briefs it reads the brief's `research/evidence.csv`, `picks.json` and `criteria.md` and stops when they are missing. Chain: brief → write → `mos-proofread`. Keep `agents/`, `references/`, `scripts/word_counter.py`, `scripts/generate_article_html.py`; drop the `.docx` generator (decision 7).

### U3: `mos-content-best-x-for-y` (after U1)

Port the source listicle-brief skill, then change its method from a self-promotional listicle (brand ranked #1) to a genuine buyer's guide. Method sources: the best-x-for-y section of the GEO comparison-content plan in mos-geo-skills (2026-10-20) and the 2026-10-20 GEO comparison-pages research note. Required behaviour:

1. **Ask the user first** (AskUserQuestion, "Skip, you suggest" always available): pages they already have in mind, avatars/use cases that matter most, anything to avoid. Their ideas are tagged `yours`, discovered ones `discovered`.
2. **Demand check** per candidate Y: keyword volume (Ahrefs or DataForSEO when a key exists) and, when possible, the buyer prompt run through AI engines to record who they recommend today.
3. **Eligibility gate** per Y: the brand passes or fails on offer, audience, proof, price and availability today. A fail means the brand is left off that page (the page can still be built as a guide). A pre-launch brand passes nowhere. The user picks the final 3 to 5 pages.
4. **Candidate set** per page: brands the AI engines name, the Google top 10 and review-site leaders, trimmed to 4 to 10.
5. **Criteria and methodology block**, approved by the user before anything is ranked.
6. **Evidence:** every competitor fact has a saved snapshot, source URL, capture date and a verbatim quote. A value nobody publishes is "Not published".
7. **Picks:** every entry gets "Best for…" and "Not for…", tied to a stated criterion. The brand is never #1 by default and only appears where it passed the gate.
8. **Brief output** follows the same one-file standard as mos-content-brief, with an answer-first outline, a disclosure line ("we make X; here is how we chose"), ItemList schema guidance only (never AggregateRating), and no year stuffed into the title.

Keep the useful source machinery (keyword research, SERP analysis, competitor/review research agents, `serp_outline_builder.py`). Retire the source's self-promotion formula reference; write `references/buyers-guide-method.md` in its place. Drop the source's own brief generator (deprecated pattern, decision 6) unless the SKILL.md genuinely depends on it, in which case report it as a blocker rather than porting it silently.

### U4: `mos-content-humanizer` (independent)

Port the source humanizer wrapper. First run its `scripts/sync_upstream.py` against the latest blader/humanizer `main` so `references/humanizer.md` and `LICENSE` are current, then update `UPSTREAM.md`. `references/humanizer.md` stays byte for byte upstream (it is exempt from the grep and em-dash criteria). Rewrite the wrapper SKILL.md for brains: the client root becomes the brain root per `$SKILL/../_shared/brain-context.md`; voice rules come from the brain's own files; the skills that call it are `mos-content-brief`, `mos-content-best-x-for-y` and `mos-content-writer`; audit-only questions go to `mos-proofread`. Keep the Wikipedia and StoryScope digests and their attribution.

## Acceptance criteria (every unit self-checks before returning)

1. Each target folder has a SKILL.md with valid YAML frontmatter whose `name:` equals the folder name.
2. The agency-residue grep in `docs/plans/2026-10-21-review-fixes.md` (Done checks) returns nothing.
3. No source skill name survives in the unit folders.
4. Every `$SKILL/../_shared/...` path a SKILL.md mentions exists on disk.
5. Every ported `.py` compiles: `python3 -m py_compile <file>`; every CLI script answers `--help` without a traceback.
6. No em dashes in any prose `.md` you wrote (the U+2014 count is 0 on files you authored; vendored code comments may keep theirs).
7. U3 only: the SKILL.md contains the ask-first step, the eligibility gate, "Best for"/"Not for", the methodology block, and states the brand is never #1 by default.

## Out of scope

Pushing, publishing the repo, editing the source pack, building the brand-audit workbook integration, and running the skills end to end on a real brand. The orchestrator handles commits, README and setup.
