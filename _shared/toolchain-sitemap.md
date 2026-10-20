# Sitemap Verification Toolchain

Shared reference for internal link verification via the live sitemap across mos-content skills.

## Why This Matters

- Hallucinated URLs create broken links if writers use them verbatim
- The sitemap is the single source of truth for what pages exist on the live site
- Blog posts are often missed when links are guessed from memory: the sitemap reveals all published content

## Process

### Step 1: Check for Existing Reference File

Look anywhere in the brain for: `**/*-sitemap-urls.md` (never assume a folder exists)
- If exists and < 30 days old → use as source of truth
- If missing or stale → proceed to Step 2

### Step 2: Scrape the Live Sitemap

1. `WebFetch` (or `fetch_page.py --text`) → `https://<domain>/sitemap.xml`, then `sitemap_index.xml`, then any `Sitemap:` line in `robots.txt`
2. If sitemap index (contains `<sitemap>` entries) → fetch each child sitemap:
   - page-sitemap.xml, post-sitemap.xml, product-sitemap.xml, category-sitemap.xml, etc.
3. Extract ALL URLs with last modified dates
4. Save to the brief's `research/YYYY-MM-DD-<brand-slug>-sitemap-urls.md` (or where the brain's CLAUDE.md routes it)
5. No sitemap at all: list only URLs you have fetched and seen return 200. Never guess a URL.

### Reference File Format

```markdown
# <Brand> Sitemap URLs

**Date:** YYYY-MM-DD
**Source:** https://<domain>/sitemap.xml

## Pages
- https://<domain>/page-1/
...

## Blog Posts
- https://<domain>/blog/post-1/
...

## Products
- https://<domain>/products/product-1/
...

## URLs That Do NOT Exist
(Previously-assumed URLs that turned out to be wrong)
```

### Step 3: Select Internal Links

Pick 5-10 URLs from the verified sitemap, prioritised by:
1. Service/product pages directly relevant to the topic
2. Blog posts on related topics (for topical clustering)
3. Industry/category pages matching target audience
4. Parent/sibling pages in site hierarchy

Format: `https://domain.com/path/ (anchor: natural anchor text)`

### Step 4: Cross-Check the brain's link list

If the brain's CLAUDE.md or a `reference/` file keeps an internal link list:
- Check every URL against the sitemap
- Flag URLs not found in sitemap
- Note these for cleanup
