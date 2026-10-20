# SurferSEO API Toolchain (optional extra)

> **Optional.** The default term targets come free from the fetched top 10: `serp_outline_builder.py` returns a `terms` list (phrase, pages using it, min to max usage), built locally by `_shared/scripts/serp_research.py` (`toolchain-scrapling.md`). Surfer runs only when `SURFERSEO_API_KEY` is set, and adds a Content Editor link and Surfer's own ranges on top. With no key the Surfer row reads `Not available (no SURFERSEO key)` and the brief still carries the local term targets.

Shared reference for SurferSEO Content Editor creation and SEO Guidelines harvesting across mos-content brief skills.

## Overview

Surfer does two jobs in the brief chain:

1. **Creates the Content Editor** the writer works in, and returns its share link: replacing the manual "open Surfer, retype the keywords, copy the link" ritual.
2. **Supplies pre-brief context**: term targets with occurrence ranges, a SERP-derived word count, topics and People-Also-Ask questions, and AI Search facts with per-engine citation attribution.

Surfer **supplements** the SERP analysis; it does not replace it. The `serp_outline_builder.py` themes remain the outline driver.

## API Details

- **Base URL:** `https://app.surferseo.com`
- **Auth:** `API-KEY` header (NOT `Authorization: Bearer`)
- **Workspace:** `SURFER_WORKSPACE_ID` when set, otherwise the first workspace on the account
- **Script:** `_shared/scripts/surfer_api.py`
- **Key:** `SURFERSEO_API_KEY` in the environment or the brain's `.env`
- **Rate limit:** 10 requests/sec per endpoint
- **Plan:** API access depends on the Surfer plan; a `403` means the key is valid but the plan is not

### Endpoints used

| Endpoint | Method | Purpose | Cost |
|----------|--------|---------|------|
| `/api/v2/workspaces` | GET | Auth smoke test | free |
| `/api/v1/locations` | GET | Valid location strings | free |
| `/api/v2/workspaces/{ws}/content_editors` | GET | List / reuse lookup | free |
| `/api/v2/workspaces/{ws}/content_editors` | POST | **Create Content Editor** | **1 credit** |
| `…/content_editors/{id}` | GET | Poll state, read permalinks | free |
| `…/{id}/seo_guidelines/terms` | GET | Terms + `target_range` + `heading` flag | free |
| `…/{id}/seo_guidelines/structure` | GET | Target word count + structural ratios | free |
| `…/{id}/seo_guidelines/topics_and_questions` | GET | Topics + PAA questions | free |
| `…/{id}/seo_guidelines/competitors` | GET | SERP URLs + Surfer content score | free |
| `…/{id}/ai_search_guidelines/facts` | GET | Facts + `cited_by` per source | free |
| `…/{id}/outline` | GET | SERP-derived outline (`Accept: text/markdown`) | free |

### Create parameters

`main_keyword` is the only required field. Also accepts `secondary_keywords` (**max 19**: 20 total including the main one), `location` (display name, e.g. `"Australia"`), `device` (`mobile` default / `desktop`), `target_word_count`, `notes`, `custom_instructions`, `import_content_url`.

`target_word_count` can **only** be set at creation: `CustomizeContentEditorParams` (the PATCH body) omits it. This is why the create fires after the SERP analysis computes the target, not before.

## Script usage

```bash
S="$SKILL/../_shared/scripts/surfer_api.py"

python3 $S check                                    # free auth test
python3 $S locations --grep australia               # → ["Australia"]

# The one command a brief skill needs: create (or reuse) → poll → harvest → emit block
python3 $S brief-block \
  --client acme \
  --main-keyword "project management software for small agencies" \
  --secondary "project management software" --secondary "agency project management" \
  --location Australia --target-word-count 2200 \
  --notes "Acme | October 2026 | project-management-software-for-small-agencies"

# Re-harvest an existing editor without spending a credit (reruns, testing)
python3 $S brief-block --main-keyword "..." --editor-id 12345

# Preview the create payload without creating anything
python3 $S brief-block --main-keyword "..." --client acme --dry-run
```

**Testing rule: never test `brief-block` on a throwaway keyword.** The key resolves from the brain's `.env` even when `SURFERSEO_API_KEY` is absent from the environment, so an "unset the key" test still authenticates and still spends a credit. Use `--dry-run` to check the payload, `--editor-id` to exercise the harvest and formatting path, and a deliberately **invalid** key (`SURFERSEO_API_KEY=deadbeef…`) to exercise the auth-failure path. Deleting a mistakenly created editor returns `204` but **does not refund the credit**.

`brief-block` prints the ready-to-paste markdown block to stdout and its cost decision (`CREATED` / `REUSED` / `USING`) to stderr. It **never exits non-zero on a Surfer-side failure**: on quota exhaustion, auth failure or timeout it emits the `[Insert Surfer SEO link here: …]` placeholder so the brief still generates.

## Credit model + guards

Each successful create consumes **one Content Editor credit: exactly what creating it by hand costs**. Automation adds no spend. Every read is free. There is no sandbox.

Two guards keep it at one credit:

- **`Idempotency-Key` header** on create, hashed from `brand|main_keyword|today`. Surfer replays the original response for a repeated key (24h expiry), so re-running a brief the same day cannot double-charge.
- **Reuse lookup before create.** Matches on `main_keyword` **and** requires the `notes` stamp to name the same brand (`--client`). An agency workspace is shared across brands and the same keyword genuinely recurs, so a keyword match alone is not sufficient: handing a brief another brand's editor is far worse than spending a credit. Same-keyword editors that fail the client check are reported as a warning, not silently reused.

## Constraints + gotchas

- **There is no folder API.** No folder parameter, no folder endpoint, no folder filter, in v1 or v2 (re-verified against the live spec 2026-07-27). Folder assignment stays a manual drag in the UI. Always pass `--notes "<Brand> | <Month YYYY> | <slug>"` so the new editor is identifiable in the list: and so the reuse guard can claim it next time.
- **`notes` is NOT returned by the list endpoint** (verified live 2026-07-27). `GET /content_editors` returns `ContentEditorSummary`, which omits `notes` entirely; only `GET /content_editors/{id}` (`ContentEditorDetail`) carries it. Reading `notes` off a list row silently yields `None`, which defeats any notes-based matching without erroring. `cmd_find` therefore re-fetches the detail for each keyword match. The same applies to `meta_title`, `meta_description` and `custom_instructions`: all detail-only.
- **`/api/v1/locations` is PUBLIC: never use it as an auth smoke test.** It returns 200 with a bogus key, or with no key at all. Use `/api/v2/workspaces`.
- **401 vs 403 is the diagnostic lever.** `401 unauthorized` = the key is not resolving on Surfer's backend; regenerating the key in-app may not fix it; Surfer support can regenerate it server-side. `403 permission_denied` = valid key, plan or billing problem. For a 401, send Surfer a fresh `cf-ray` plus the key fingerprint and ask them to regenerate.
- **Cloudflare 1010 bans non-browser user agents** intermittently. The script always sends a browser UA.
- **`.env` values may be CRLF** (common on Windows): strip every value or the trailing `\r` corrupts the HTTP header.
- **Guidelines endpoints 409 until the editor is `completed`.** Creation is async and returns `scheduled`. Poll `GET …/content_editors/{id}` for `state == completed` **and** `seo_guidelines.status == completed` before harvesting. `brief-block` handles this.
- **Surfer returns 60+ body terms.** The script caps at 25 per group by default (`--max-terms`) and reports the tail count: an uncapped list is unreadable in a brief.
- **Webhooks require manual setup via Surfer support.** Polling is sufficient for brief-by-brief use.

## Deep reference

Surfer's API documentation: https://docs.surferseo.com/en/articles/api
