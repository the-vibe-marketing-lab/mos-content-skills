# Scrapling (free page fetching)

Scrapling fetches competitor pages for nothing. It replaces paid SERP-heading and page-render services for this pack: the pages DataForSEO ranks are fetched locally, and their headings, word counts and term usage are extracted in code (`_shared/scripts/serp_research.py`).

## Install (optional, recommended)

```bash
uv tool install "scrapling[shell]"        # or: pipx install "scrapling[shell]"
scrapling install                         # only needed for the browser fetch (JavaScript pages)
```

Nothing in the pack requires it. When the `scrapling` command is missing, the scripts say so in their `gaps` and fall back.

## Fetch order (every skill)

1. `scrapling extract get <url> page.html`: plain HTTP with browser-like headers. Most pages resolve here.
2. `scrapling extract fetch <url> page.html`: a real browser, for pages built by JavaScript.
3. `fetch_page.py` tiers: the Scrapling Python library (when importable), then Firecrawl when `FIRECRAWL_API_KEY` is set (optional extra, costs credits).
4. WebFetch in the session. `serp_outline_builder.py` lists any URL that needed it under `needs_webfetch`.

A page is accepted only when the extracted article holds at least 250 words; a 200 response with an empty shell climbs to the next tier.

## What is extracted locally

`serp_research.py` (stdlib only):

- **Headings:** H1 to H3, from the `<main>` or `<article>` region when it holds the article (sidebars and related-post rails are dropped), with navigation, header, footer, forms and scripts excluded. Noise headings (contact, newsletter, share, related posts) are filtered.
- **Word count:** the same region's body text.
- **Themes:** headings clustered into themes; each skill passes its own theme table.
- **Term targets:** 1 to 3 word phrases from the fetched pages, stop words trimmed, ranked by a TF-IDF style weight. Each term carries the number of pages using it and a min to max usage range, the shape writers know from paid term tools. Phrases only one page uses are dropped.

Check one saved page by hand:

```bash
python3 "$SKILL/../_shared/scripts/serp_research.py" --extract-file page.html
```
