#!/usr/bin/env python3
"""
SERP outline builder (mos-content-best-x-for-y).

Thin wrapper over the pack's shared `_shared/scripts/serp_research.py` with the buyer's
guide themes added (picks, methodology, product_review, best_for, not_for, alternatives),
which are matched before the generic article themes. DataForSEO supplies the top 10 URLs,
Scrapling fetches them, and headings, word counts, themes and term targets are extracted
locally. Thruuu is an optional extra (only when THRUUU_API_KEY is set and DataForSEO is not).
No key at all: pass the WebSearch result URLs with --urls (labelled approximate).

Prints JSON on stdout; progress, gaps and the DataForSEO cost go to stderr. Exits 0 even when
a provider is missing: read `gaps`.

Usage:
  python3 serp_outline_builder.py "<keyword>" [--country au] [--urls "u1,u2"] [--terms-md]
"""
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.realpath(__file__)), "..", "_shared", "scripts"))
import serp_research as sr  # noqa: E402

GUIDE_THEMES = ('picks', 'methodology', 'best_for', 'not_for', 'alternatives', 'product_review')

THEME_KEYWORDS = {
    **sr.THEME_KEYWORDS,
    'picks': ['our picks', 'quick picks', 'top picks', 'at a glance', 'the list', 'ranked'],
    'methodology': ['how we chose', 'how we tested', 'methodology', 'how we picked', 'criteria', 'how we rank'],
    'product_review': ['review', 'reviews', 'rated', 'rating', 'tested'],
    'best_for': ['best for', 'ideal for', 'suited for', 'recommended for', 'good for'],
    'not_for': ['not for', 'skip it if', 'avoid if', 'not ideal', 'downsides', 'cons'],
    'alternatives': ['alternative', 'alternatives to', 'instead of', 'switch from'],
}

if __name__ == "__main__":
    sys.exit(sr.run_cli(THEME_KEYWORDS, priority=GUIDE_THEMES, prog="serp_outline_builder.py",
                        description="SERP heading, word count, theme and term analysis for a "
                                    "best-X-for-Y buyer's guide brief."))
