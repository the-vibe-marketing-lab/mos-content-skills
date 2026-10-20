#!/usr/bin/env python3
"""Tests for the local SERP extraction (serp_research.py) and the DataForSEO response parsing.

No network: every DataForSEO call is replaced with a canned response, and the no-key path runs
from an empty temp folder with the credentials removed from the environment.

Run: python3 -m unittest _shared/scripts/test_serp_research.py
"""
import json
import os
import sys
import tempfile
import unittest
from unittest import mock

HERE = os.path.dirname(os.path.realpath(__file__))
sys.path.insert(0, HERE)

import ai_search  # noqa: E402
import dataforseo_api as dfs  # noqa: E402
import serp_research as sr  # noqa: E402

PAGE = """<!doctype html><html><head><title>Best Widgets 2026</title>
<script>var x = "<h2>not a heading</h2>";</script><style>h2{color:red}</style></head>
<body>
<header><nav><h2>Menu heading</h2><a href="/">Home</a> Products Pricing Login</nav></header>
<main>
<h1>Best Widgets for Small Teams</h1>
<p>Widgets help small teams plan work. Time tracking widgets save hours every week.</p>
<h2>What is a widget?</h2><p>A widget is a small tool. Time tracking matters for small teams.</p>
<h2>How much does a widget cost?</h2><p>Most widgets cost between ten and fifty dollars.</p>
<h3>Free widgets</h3><p>Some widgets are free for small teams.</p>
</main>
<div class="promo"><p>Promo words outside main.</p></div>
<aside><h2>Related posts</h2><p>Sidebar words that should not count at all here.</p></aside>
<footer><h2>Newsletter</h2><p>Copyright footer words.</p></footer>
</body></html>"""


def _no_creds_env():
    env = {k: v for k, v in os.environ.items()
           if not k.startswith(("DATAFORSEO_", "THRUUU_", "APIFY_", "FIRECRAWL_"))}
    return mock.patch.dict(os.environ, env, clear=True)


class ExtractHtml(unittest.TestCase):
    def test_headings_skip_nav_aside_footer_and_script(self):
        ex = sr.extract_html(PAGE, main_min_words=5)
        self.assertEqual(ex["title"], "Best Widgets 2026")
        self.assertEqual(ex["h1"], ["Best Widgets for Small Teams"])
        self.assertEqual(ex["h2"], ["What is a widget?", "How much does a widget cost?"])
        self.assertEqual(ex["h3"], ["Free widgets"])
        self.assertNotIn("Menu heading", ex["h2"])
        self.assertNotIn("not a heading", ex["text"])

    def test_main_region_word_count_excludes_chrome(self):
        ex = sr.extract_html(PAGE, main_min_words=5)
        self.assertEqual(ex["scope"], "main")
        self.assertNotIn("Sidebar", ex["text"])
        self.assertNotIn("Promo", ex["text"])
        self.assertNotIn("Copyright", ex["text"])
        self.assertGreater(ex["word_count"], 40)
        self.assertLess(ex["word_count"], 70)

    def test_falls_back_to_whole_page_when_main_is_thin(self):
        ex = sr.extract_html(PAGE, main_min_words=10_000)
        self.assertEqual(ex["scope"], "page")
        self.assertIn("Promo words outside main", ex["text"])
        self.assertNotIn("Sidebar", ex["text"])                 # aside always excluded
        self.assertNotIn("Products Pricing Login", ex["text"])  # nav always excluded

    def test_malformed_html_does_not_raise(self):
        ex = sr.extract_html("<h2>Open heading<p>text <b>bold</h2> trailing")
        self.assertEqual(ex["h2"], ["Open heading text bold"])

    def test_markdown_extraction(self):
        md = "# Title\n\nIntro [link](https://x.example) words.\n\n## Section one\n\nBody.\n\n### Sub **bold**\n"
        ex = sr.extract_markdown(md)
        self.assertEqual(ex["h1"], ["Title"])
        self.assertEqual(ex["h2"], ["Section one"])
        self.assertEqual(ex["h3"], ["Sub **bold"])  # trailing ** stripped, inner kept verbatim
        self.assertNotIn("https://", ex["text"])


class Terms(unittest.TestCase):
    DOCS = [
        "Time tracking for small teams. Time tracking saves hours. Resource planning helps.",
        "Our time tracking tool and resource planning features. Time tracking is free.",
        "Time tracking, invoicing and resource planning for agencies.",
        "A page about gardening with no overlap.",
    ]

    def test_shared_phrases_with_ranges_and_page_counts(self):
        terms = {t["term"]: t for t in sr.extract_terms(self.DOCS)}
        self.assertIn("time tracking", terms)
        self.assertEqual(terms["time tracking"]["pages"], 3)
        self.assertEqual((terms["time tracking"]["min"], terms["time tracking"]["max"]), (1, 2))
        self.assertIn("resource planning", terms)

    def test_single_page_phrases_and_stop_words_dropped(self):
        terms = [t["term"] for t in sr.extract_terms(self.DOCS)]
        self.assertNotIn("gardening", terms)
        self.assertFalse(any(t.split()[0] in sr.STOP_WORDS or t.split()[-1] in sr.STOP_WORDS for t in terms))

    def test_contained_term_with_same_pages_is_dropped(self):
        terms = [t["term"] for t in sr.extract_terms(self.DOCS)]
        self.assertNotIn("tracking", terms)  # inside "time tracking", same 3 pages

    def test_exclude_and_empty(self):
        self.assertEqual(sr.extract_terms([]), [])
        terms = [t["term"] for t in sr.extract_terms(self.DOCS, exclude={"time tracking"})]
        self.assertNotIn("time tracking", terms)

    def test_terms_markdown(self):
        md = sr.terms_markdown(sr.extract_terms(self.DOCS))
        self.assertIn("- time tracking (1-2, used by 3 pages)", md)
        self.assertTrue(sr.terms_markdown([]).startswith("Not available"))


class Themes(unittest.TestCase):
    def test_priority_theme_wins(self):
        comps = [{"h2": ["Best for freelancers", "How much does it cost?"], "h3": []}]
        themes = {**sr.THEME_KEYWORDS, "best_for": ["best for"]}
        counts, _ = sr.cluster_themes(comps, themes, priority=("best_for",))
        self.assertEqual(counts, {"best_for": 1, "cost": 1})
        counts, _ = sr.cluster_themes(comps, themes)  # without priority, "best" -> choosing
        self.assertIn("choosing", counts)

    def test_page_counts_and_word_count_stats(self):
        comps = [{"h2": ["What is X?", "What is Y?"], "h3": [], "word_count": 1000},
                 {"h2": ["Cost of X"], "h3": [], "word_count": 2000}]
        self.assertEqual(sr.theme_page_counts(comps), {"definition": 1, "cost": 1})
        wc = sr.word_count_stats(comps)
        self.assertEqual((wc["avg"], wc["min"], wc["max"], wc["count"]), (1500, 1000, 2000, 2))


class NoKeyPath(unittest.TestCase):
    def test_analyse_with_no_keys_names_the_gap_and_spends_nothing(self):
        with _no_creds_env(), tempfile.TemporaryDirectory() as tmp:
            cwd = os.getcwd()
            os.chdir(tmp)
            try:
                res = sr.analyse("widgets for small teams", "au", use_cache=False, cache_dir=tmp)
            finally:
                os.chdir(cwd)
        self.assertEqual(res["competitors"], [])
        self.assertEqual(res["cost_usd"], 0.0)
        self.assertTrue(any("no DATAFORSEO key" in g for g in res["gaps"]))

    def test_ai_search_with_no_keys(self):
        with _no_creds_env(), tempfile.TemporaryDirectory() as tmp:
            cwd = os.getcwd()
            os.chdir(tmp)
            try:
                res = ai_search.capture_all("widgets", "au")
            finally:
                os.chdir(cwd)
        self.assertEqual(res["provider"], "none")
        for engine in ("aio", "ai_mode", "chatgpt"):
            self.assertEqual(res[engine]["not_available"], "Not available (no DATAFORSEO key)")
        self.assertIn("Not available (no DATAFORSEO key)", ai_search.to_markdown(
            "widgets", "au", res["aio"], res["chatgpt"], res["ai_mode"]))


class DataForSEOParsing(unittest.TestCase):
    SERP_BODY = {"status_code": 20000, "cost": 0.004, "tasks": [{"status_code": 20000, "result": [{
        "item_types": ["ai_overview", "organic", "people_also_ask"],
        "items": [
            {"type": "ai_overview", "markdown": "Widgets are tools.", "items": [
                {"type": "ai_overview_element", "references": [
                    {"url": "https://a.example/x", "domain": "a.example", "title": "A"}]}],
             "references": [{"url": "https://a.example/x", "domain": "a.example", "title": "A"},
                            {"url": "https://b.example/y", "domain": "b.example", "title": "B"}]},
            {"type": "organic", "rank_group": 1, "url": "https://c.example/", "title": "C",
             "domain": "c.example", "description": "d"},
            {"type": "people_also_ask", "items": [{"title": "What is a widget?"}]},
        ]}]}]}

    def test_serp_normalised_and_cost_counted(self):
        before = dfs.TOTAL_COST

        def fake(path, payload=None, method="POST", timeout=180, login=None, password=None):
            dfs.TOTAL_COST += self.SERP_BODY["cost"]
            self.assertEqual(path, "/serp/google/organic/live/advanced")
            self.assertTrue(payload[0]["load_async_ai_overview"])
            self.assertEqual(payload[0]["location_code"], 2036)
            return self.SERP_BODY

        with mock.patch.object(dfs, "_request_raising", side_effect=fake):
            s = dfs.serp("widgets", "au", login="l", password="p")
        self.assertEqual(s["organic"][0]["url"], "https://c.example/")
        self.assertTrue(s["ai_overview"]["present"])
        self.assertEqual([r["link"] for r in s["ai_overview"]["references"]],
                         ["https://a.example/x", "https://b.example/y"])  # deduped
        self.assertEqual(s["people_also_ask"], ["What is a widget?"])
        self.assertAlmostEqual(dfs.TOTAL_COST - before, 0.004)

    def test_overview_marks_missing_keywords(self):
        body = {"status_code": 20000, "tasks": [{"status_code": 20000, "result": [{"items": [
            {"keyword": "a", "keyword_info": {"search_volume": 10, "cpc": 1.5},
             "keyword_properties": {"keyword_difficulty": 7},
             "search_intent_info": {"main_intent": "commercial"}}]}]}]}
        with mock.patch.object(dfs, "_request_raising", return_value=body):
            rows = dfs.keyword_overview(["a", "b"], "au", login="l", password="p")
        self.assertEqual(rows[0]["volume"], 10)
        self.assertEqual(rows[0]["kd"], 7)
        self.assertEqual(rows[1]["keyword"], "b")
        self.assertIsNone(rows[1]["volume"])

    def test_task_error_raises(self):
        body = {"status_code": 20000, "tasks": [{"status_code": 40501, "status_message": "Invalid Field"}]}
        with mock.patch.object(dfs, "_request_raising", return_value=body):
            with self.assertRaises(dfs.DataForSEOError):
                dfs.related_keywords("a", "au", login="l", password="p")


if __name__ == "__main__":
    unittest.main()
