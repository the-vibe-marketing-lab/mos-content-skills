#!/usr/bin/env python3
"""
SERP outline builder (mos-content-brief).

Thin wrapper over the pack's shared `_shared/scripts/serp_research.py`: DataForSEO for the
top 10 URLs, Scrapling to fetch them, and local extraction of H1 to H3 headings, word counts,
themes and term targets. Thruuu is used only as an optional extra when THRUUU_API_KEY is set
and there are no DataForSEO credentials. With no key at all, pass the URLs you found by
WebSearch with --urls; the result is labelled approximate.

Prints JSON on stdout (competitors, theme_counts, theme_page_counts, theme_examples,
word_count_stats, terms, ai_overview, people_also_ask, gaps, cost_usd). Progress, gaps and
the DataForSEO cost go to stderr. Exits 0 even when a provider is missing: read `gaps`.

Usage:
  python3 serp_outline_builder.py "<keyword>" [--country au] [--urls "u1,u2"] [--terms-md]
"""
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.realpath(__file__)), "..", "_shared", "scripts"))
import serp_research as sr  # noqa: E402

THEME_KEYWORDS = sr.THEME_KEYWORDS

if __name__ == "__main__":
    sys.exit(sr.run_cli(THEME_KEYWORDS, prog="serp_outline_builder.py",
                        description="SERP heading, word count, theme and term analysis for an article brief."))
