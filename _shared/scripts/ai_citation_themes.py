#!/usr/bin/env python3
"""
"Only Cited by AI" theme analysis.

Classifies the pages AI engines cite (from ai_search.py JSON) into the same 16 content themes
the brief's SERP analysis uses, then diffs them against the organic top-10 SERP themes. Surfaces
themes that AI engines reward (cite) but that the organic top-10 barely cover — i.e. content
angles worth owning for GEO/AEO.

v1 is deliberately cheap: it classifies from each cited page's TITLE + URL slug (both already
returned by the scrapers) — no page fetch. v2 could scrape cited-page headings for more depth.

THEME_KEYWORDS comes from serp_research.py (the same table the SERP analysis clusters with),
so the AI side and the organic side always use one definition. The organic side is read from
serp_outline_builder.py JSON output (its `theme_counts`), or from a raw Thruuu cache when the
optional Thruuu extra produced one.

Usage:
  python3 ai_citation_themes.py --ai-search-json ai.json --serp-themes-json serp.json --md
  python3 ai_citation_themes.py --ai-search-json ai.json --serp-counts-json counts.json --json
"""
import argparse
import json
import os
import sys
from urllib.parse import urlparse

sys.path.insert(0, os.path.dirname(os.path.realpath(__file__)))
from serp_research import THEME_KEYWORDS, cluster_themes  # noqa: E402  (same folder, no side effects)


def _haystack(title: str, url: str) -> str:
    """Title + URL slug words, lowercased — what we match themes against."""
    path = urlparse(url).path
    slug = path.replace("-", " ").replace("_", " ").replace("/", " ")
    return f"{title} {slug}".lower()


def classify_cited_pages(ai_search_result: dict) -> dict:
    """Return {theme: [url, ...]} for every AI-cited page that matches a theme."""
    cited = []
    aio = ai_search_result.get("aio") or {}
    for r in aio.get("references") or []:
        cited.append((r.get("title", ""), r.get("link", "")))
    cg = ai_search_result.get("chatgpt") or {}
    for c in cg.get("citations") or []:
        cited.append((c.get("title", ""), c.get("url", "")))

    themes: dict[str, list] = {}
    for title, url in cited:
        if not url:
            continue
        hay = _haystack(title, url)
        for theme, kws in THEME_KEYWORDS.items():
            if any(kw in hay for kw in kws):
                themes.setdefault(theme, [])
                if url not in themes[theme]:
                    themes[theme].append(url)
                break
    return themes


def organic_theme_counts(serp_json: dict) -> dict:
    """Organic top-10 theme counts from serp_outline_builder.py output, or a raw Thruuu cache."""
    if isinstance(serp_json.get("theme_counts"), dict):
        return serp_json["theme_counts"]
    competitors = [{"h2": r.get("h2", []), "h3": r.get("h3", [])} for r in serp_json.get("result", [])]
    counts, _ = cluster_themes(competitors)
    return counts


def diff_vs_serp_themes(ai_themes: dict, serp_counts: dict, min_serp_count: int = 2) -> dict:
    """Themes cited by AI but weakly/never in organic top-10 vs covered by both vs organic-only."""
    ai_keys = set(ai_themes)
    serp_strong = {t for t, n in serp_counts.items() if n >= min_serp_count}
    return {
        "only_in_ai": sorted(ai_keys - serp_strong),
        "overlap": sorted(ai_keys & serp_strong),
        "only_in_serp": sorted(serp_strong - ai_keys),
    }


def to_markdown_summary(diff: dict, ai_themes: dict) -> str:
    out = ["**Only Cited by AI (weak/absent in organic top-10)**", ""]
    if diff["only_in_ai"]:
        for t in diff["only_in_ai"]:
            ex = ai_themes.get(t, [])[:3]
            out.append(f"- {t}: " + ", ".join(ex) if ex else f"- {t}")
    else:
        out.append("- (none — AI citations align with organic coverage)")
    out += ["", "**Covered by both AI and organic**", ""]
    out.append("- " + ", ".join(diff["overlap"]) if diff["overlap"] else "- (none)")
    return "\n".join(out)


def main() -> None:
    p = argparse.ArgumentParser(description='"Only Cited by AI" theme diff for a brief.')
    p.add_argument("--ai-search-json", required=True, help="ai_search.py --json output file")
    g = p.add_mutually_exclusive_group(required=True)
    g.add_argument("--serp-themes-json", help="serp_outline_builder.py JSON output (or a raw Thruuu cache)")
    g.add_argument("--serp-counts-json", help="precomputed {theme: count} JSON")
    p.add_argument("--min-serp-count", type=int, default=2)
    p.add_argument("--md", action="store_true")
    p.add_argument("--json", action="store_true")
    a = p.parse_args()

    ai_res = json.loads(open(a.ai_search_json, encoding="utf-8").read())
    ai_themes = classify_cited_pages(ai_res)
    if a.serp_counts_json:
        serp_counts = json.loads(open(a.serp_counts_json, encoding="utf-8").read())
    else:
        serp_counts = organic_theme_counts(
            json.loads(open(a.serp_themes_json, encoding="utf-8").read()))

    diff = diff_vs_serp_themes(ai_themes, serp_counts, a.min_serp_count)
    if a.json:
        print(json.dumps({"ai_themes": ai_themes, "serp_counts": serp_counts, "diff": diff},
                         indent=2, ensure_ascii=False))
    else:
        print(to_markdown_summary(diff, ai_themes))


if __name__ == "__main__":
    main()
