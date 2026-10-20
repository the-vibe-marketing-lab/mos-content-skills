# DataForSEO (the one recommended key)

DataForSEO is pay per use: no subscription, no monthly minimum beyond the prepaid balance. One client, `_shared/scripts/dataforseo_api.py`, covers every keyword, SERP and AI-answer step in this pack. Endpoint paths and request shapes were checked against docs.dataforseo.com on 2026-10-21.

## Credentials

`DATAFORSEO_LOGIN` and `DATAFORSEO_PASSWORD` (HTTP Basic auth, the API password from the DataForSEO dashboard, not your account password). The scripts read them from the environment first, then from a `.env` walked up from the current folder, so run them from the brain root. Never paste them into chat or write them into a file yourself.

Check them for free:

```bash
python3 "$SKILL/../_shared/scripts/dataforseo_api.py" balance
```

## Commands

Every command prints JSON on stdout and `[cost] $X` on stderr. Keyword commands take `--country` (default `au`).

| Job | Command | Cost seen on 2026-10-21 |
|---|---|---|
| Volume, CPC, competition, KD, intent (up to 700 keywords) | `overview --keywords "a,b"` | $0.012 a call |
| Google Ads volume (only if you need Google Ads numbers exactly) | `volume --keywords "a,b"` | $0.090 a call |
| Related keywords | `related --keyword K --limit 50` | $0.012 a call (limit 3) |
| Long-tail and question variants | `suggestions --keyword K --limit 50` | not measured yet |
| Keyword difficulty only | `difficulty --keywords "a,b"` | not measured yet |
| Live Google top 10, AI Overview, People Also Ask | `serp --keyword K` | $0.004 (AI Overview load included) |
| Google AI Mode answer and sources | `ai-mode --keyword K` | $0.004 |
| ChatGPT answer with web search and citations | `llm --prompt P` | $0.029 (gpt-4.1-mini, short prompt) |
| Keywords a domain ranks for (cannibalisation) | `ranked --target example.com` | not measured yet |
| Backlink profile (other skills) | `summary`, `backlinks`, `refdomains`, `anchors`, `networks` | per request plus per row |

Prices move. The real figure for every call is in the API response and the scripts report it; quote that, not this table.

## Which script calls what

- `serp_outline_builder.py` (both brief skills) calls `serp` once, then fetches the top 10 with Scrapling. Its JSON already holds the AI Overview and People Also Ask, so do not call `serp` again for them.
- `ai_search.py` calls `ai-mode` and `llm`, and `serp` only when you do not pass `--serp-json` from the builder.
- The keyword-researcher agents call `overview`, `related`, `suggestions` and `ranked`.

## Without a key

Every step still runs or degrades by name:

- Keyword metrics read `Not available (no DATAFORSEO key)`; questions come from People Also Ask and autocomplete seen through WebSearch, labelled manual.
- The top 10 comes from WebSearch, labelled approximate, and is passed to `serp_outline_builder.py --urls` so headings, word counts and terms are still extracted locally for free.
- AI Overview, AI Mode and ChatGPT read `Not available (no DATAFORSEO key)` unless the optional Apify key is set.
- The cannibalisation check reads `Not available (no DATAFORSEO key)`.

## Location codes

`dataforseo_api.LOCATION_CODES` maps `au nz us uk gb ca ie sg in za`. Add a market there (Google Ads location codes) rather than passing raw numbers around.
