---
title: Affordable provider swap
date: 2026-10-21
status: done
---

# Affordable provider swap

**Richard's calls (2026-10-21, these override the table below where they differ):**
- **Ahrefs is removed**, not kept as an optional extra. DataForSEO replaces every Ahrefs call (API and MCP). Delete `_shared/scripts/ahrefs_api.py` and `toolchain-ahrefs.md` and every Ahrefs step.
- **Thruuu is replaced** by DataForSEO SERP (top 10 URLs) + Scrapling fetch + local heading/word-count/theme extraction. Thruuu stays only as an optional extra if its key is set. An Apify actor was considered and not used: it costs per result for work our own script does free after the one SERP call.
- **Surfer is replaced** by local term extraction from the same fetched top 10 (TF-IDF / n-grams). Surfer stays only as an optional extra if its key is set.
- **Fetching: Scrapling first, Firecrawl as the fallback**, then WebFetch.

Richard asked for the paid tools in this pack to be swapped for cheaper ones. Default stack after this change: **DataForSEO (pay per use) + Scrapling (free) + WebSearch/WebFetch**. Ahrefs API, Thruuu, Surfer, Apify and Firecrawl stay as optional extras for users who already pay for them, used only when their key is present. No skill may need a subscription to run fully.

## Provider order (every skill, every step)

| Job | Default | Optional extras (only if key set) | No-key fallback |
|---|---|---|---|
| Keyword volume, CPC, competition | DataForSEO Google Ads search volume (`_shared/scripts/dataforseo_api.py volume`) | Ahrefs API / MCP | "Not available (no DATAFORSEO key)" |
| Related keywords, questions, keyword difficulty | DataForSEO Labs (related keywords, keyword suggestions, keyword difficulty) | Ahrefs | Google autocomplete / People Also Ask via WebSearch, labelled manual |
| Top 10 SERP results | DataForSEO SERP organic (Google, chosen location) | Ahrefs SERP, Thruuu | WebSearch, labelled approximate |
| Competitor headings, word counts, themes | Fetch the top 10 with Scrapling, extract H1 to H3 and word counts locally, cluster themes in code or in session | Thruuu | WebFetch |
| Term targets for the writer | Local term extraction from the fetched top 10 (TF-IDF or n-gram frequency, stop words removed) | Surfer | Skip with a note |
| What AI Overviews / AI Mode / ChatGPT cite | DataForSEO SERP (AI Overview in organic results, AI Mode endpoint) and DataForSEO LLM responses where available | Apify actors | Skip with a note |
| Page fetch | Scrapling (`scrapling extract get`, then `fetch` for JavaScript pages) | Firecrawl | WebFetch |
| Site's own ranking pages / cannibalisation | DataForSEO Labs ranked keywords for the domain | Ahrefs | Skip with a note |

## Rules

1. Check DataForSEO's current endpoint names and request shapes against its live docs before coding them; do not guess paths. Reuse `dataforseo_api.py` as the single client (add subcommands there).
2. Every DataForSEO call records its cost from the API response, and each skill run reports total spend.
3. Scrapling is invoked as a CLI if present; when missing, fall back to `fetch_page.py`'s existing tiers, then WebFetch. Never require it.
4. Update the SKILL.md provider checks (Phase 0) so the default path is DataForSEO + Scrapling and the extras are clearly optional.
5. Update `_shared/toolchain-*.md`: add `toolchain-dataforseo.md` and `toolchain-scrapling.md`; mark Ahrefs, Thruuu and Surfer docs as optional extras.
6. Update README "API keys" so DataForSEO is the one recommended key.
7. No invented numbers; a missing metric reads "Not available (no X key)".
8. Keep `$SKILL/../_shared` path resolution, Australian English, no em dashes in prose, descriptions at most 1,024 characters.

## Done checks

- A brief can be produced end to end with only DataForSEO credentials set (Ahrefs, Thruuu, Surfer, Apify, Firecrawl keys unset): run the SERP + headings + terms steps on one real keyword and show output plus reported cost.
- The same steps run with no keys at all and degrade with named gaps, no traceback.
- All `.py` compile, every CLI answers `--help`, `test_bxy.py` passes, new code has at least one test for the local heading/term extraction.
- Residue grep from `2026-10-21-review-fixes.md` still returns nothing.
