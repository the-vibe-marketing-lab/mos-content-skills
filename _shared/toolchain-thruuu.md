# Thruuu API Toolchain (optional extra)

> **Optional.** The default SERP path is DataForSEO for the top 10 plus Scrapling and local extraction (`toolchain-dataforseo.md`, `toolchain-scrapling.md`). Thruuu is used only when `THRUUU_API_KEY` is set **and** there are no DataForSEO credentials. Nothing in the pack needs a Thruuu subscription.

## Overview

Thruuu extracts competitor heading structures (H1-H4), word counts, and content patterns from SERP results. When it is the SERP source, `_shared/scripts/serp_research.py` (called by each skill's `serp_outline_builder.py`) takes its URL list and headings, still fetches the pages with Scrapling for term targets, and falls back to Thruuu's own headings for any page it cannot fetch.

## API Details

- **Base URL:** `https://api.thruuu.com/api/v2`
- **Auth:** Bearer token (`Authorization: Bearer $THRUUU_API_KEY`)
- **Script:** `_shared/scripts/serp_research.py` (`thruuu_serp`), reached through each skill's `serp_outline_builder.py`
- **Key:** `THRUUU_API_KEY` in the environment or the brain's `.env`. Without it nothing changes: DataForSEO, or WebSearch URLs passed with `--urls`, supply the top 10.

### Endpoints

| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/serps` | POST | Trigger SERP analysis for a keyword |
| `/serps?page=N&itemsPerPage=100` | GET | Poll for results |
| `/serps/{id}` | GET | Fetch full analysis data |

### Trigger Parameters
```json
{
  "keywords": ["<keyword>"],
  "parameters": {
    "search_engine": "<google domain for the market, e.g. google.com.au>",
    "country": "<country>",
    "language": "en",
    "device": "desktop",
    "num": 10,
    "search_volume": true,
    "analyze_headings": true,
    "analyze_top_topics": true
  }
}
```

### Caching
`serp_research.py` caches the whole analysis to `<temp dir>/serp_<cc>_<keyword_slug>.json` whichever provider ran; `--no-cache` forces a fresh run.

## Noise Filter Patterns

Headings matching these patterns are excluded from analysis:

`$`, `gst`, `enquire`, `Latest Articles`, `Contact Us`, `Testimonials`, `Get Your Free`, `Related Post`, `About us`, `Our Products`, `Quick Links`, `Footer`, `Newsletter`, `Follow Us`, `Share This`, `Recent posts`, `Quote Request`, `General Enquiry`, `Book Online`, `Call Us`, `Email Us`, `Request a Quote`, `Copyright`, `Categories`, `Table Of Contents`

Also reject headings shorter than 5 chars or longer than 120 chars.

## Theme Keywords for Clustering

The live table is `THEME_KEYWORDS` in `_shared/scripts/serp_research.py`; this copy is for reading.

| Theme | Trigger Words |
|-------|---------------|
| definition | what is, what are, definition, overview, introduction |
| how_it_works | how do, how does, how it works, mechanism |
| types | types, type of, kinds, varieties, options, different |
| installation | install, installation, fitting, mount |
| cost | cost, price, pricing, how much, budget |
| benefits | benefit, advantages, why, effective, worth, purpose |
| maintenance | maintenance, maintain, repair, replace, upkeep, care |
| sizing | how many, how often, number, size, sizing, capacity |
| comparison | vs, versus, compared, difference, alternative, compare |
| faq | faq, frequently asked, questions, common question |
| diy | diy, yourself, step by step, guide to |
| problems | problem, issue, disadvantage, downside, wrong, leak |
| choosing | choose, choosing, selecting, right, best, pick |
| location_service | near me, sydney, melbourne, brisbane, perth |
| why_choose_us | why choose, why us, our service, our process |
| conclusion | conclusion, final thoughts, summary, get started, next step |

## Word Count Benchmarking

From competitors with word count > 300:
- Calculate: average, median, min, max
- **Target:** `max(avg, median)` to `min(max, median + 800)`
- Cap at +800 above average to avoid over-ambitious targets

## SERP Gap Identification

- Themes with < 2 competitor headings = **underserved** = differentiation opportunity
- Flag commercial/industrial angles missing from residential-dominated SERPs
- Flag standards/compliance content missing
- Flag brand-specific capabilities no competitor mentions
