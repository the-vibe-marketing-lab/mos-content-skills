#!/usr/bin/env python3
"""Sensor probes for bxy.py: a clean fixture must pass, and each planted fault must fail
with its rule named. A check never seen to fail is not a check.

Run: python3 -m unittest scripts/test_bxy.py   (from the skill folder)
"""
import csv
import io
import json
import sys
import tempfile
import unittest
from contextlib import redirect_stdout
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import bxy  # noqa: E402

TODAY = "2026-10-21"
BRIEF = """# Content Brief: Best CRM for Small Agencies

## Publishing Guidelines

**Title**

Best CRM for Small Agencies: 6 Picks Compared

**Additional publishing notes**

- ItemList schema only. Never add AggregateRating or Review schema.
- Show a visible "Last checked" date.
- Disclosure: we make Acme; here is how we chose.

## Article Outline

## How we chose
- Best for / Not for on every entry.
"""


def gate(eligible=True, pre_launch=False):
    tests = {t: {"pass": True, "why": "ok"} for t in bxy.TESTS}
    if not eligible:
        tests["price"] = {"pass": False, "why": "too expensive for this Y"}
    return bxy.evaluate_gate({"brand": "Acme", "pre_launch": pre_launch,
                              "pages": [{"y": "small agencies", "tests": tests}]})


class Probe(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp())
        (self.tmp / "snapshots").mkdir()
        rows, entries = [], []
        for i, name in enumerate(["Acme", "Beta", "Gamma", "Delta"], 1):
            snap = f"snapshots/{name.lower()}-pricing.txt"
            (self.tmp / snap).write_text(f"{name} pricing. Plans start at ${i}9 per month.", encoding="utf-8")
            rows.append({"id": f"E{i}", "entry": name, "claim": "starting price", "value": f"${i}9",
                         "source_url": f"https://{name.lower()}.example/pricing", "snapshot_path": snap,
                         "captured_on": TODAY, "quote": f"Plans start at ${i}9 per month."})
            entries.append({"position": i + 1 if name == "Acme" else i, "name": name,
                            "is_brand": name == "Acme", "best_for": "x", "not_for": "y",
                            "criterion": "price", "evidence": [f"E{i}"]})
        entries[0]["position"], entries[1]["position"] = 2, 1
        self.rows, self.entries = rows, entries
        self.gate = gate()
        self.brief = BRIEF

    def run_check(self):
        with (self.tmp / "evidence.csv").open("w", newline="", encoding="utf-8") as fh:
            w = csv.DictWriter(fh, fieldnames=bxy.EVIDENCE_COLUMNS)
            w.writeheader()
            w.writerows(self.rows)
        (self.tmp / "picks.json").write_text(json.dumps(
            {"brand": "Acme", "page_y": "small agencies", "best_overall": None, "entries": self.entries}))
        (self.tmp / "gate.json").write_text(json.dumps(self.gate))
        (self.tmp / "brief.md").write_text(self.brief, encoding="utf-8")
        buf = io.StringIO()
        with redirect_stdout(buf):
            code = bxy.main(["check", "--research", str(self.tmp), "--brief", str(self.tmp / "brief.md"),
                             "--gate", str(self.tmp / "gate.json"), "--page", "small agencies",
                             "--today", TODAY])
        return code, buf.getvalue()

    def assertFails(self, needle):
        code, out = self.run_check()
        self.assertEqual(code, 1, out)
        self.assertIn(needle, out)

    def test_clean_fixture_passes(self):
        code, out = self.run_check()
        self.assertEqual(code, 0, out)

    def test_year_in_title(self):
        self.brief = self.brief.replace("6 Picks Compared", "6 Picks Compared (2026)")
        self.assertFails("a year in the title")

    def test_aggregate_rating(self):
        self.brief += "\n- Add AggregateRating markup to each pick.\n"
        self.assertFails("AggregateRating")

    def test_missing_disclosure(self):
        self.brief = self.brief.replace("Disclosure: we make Acme; here is how we chose.", "")
        self.assertFails("disclosure")

    def test_missing_methodology(self):
        self.brief = self.brief.replace("## How we chose", "## Picks")
        self.assertFails("methodology")

    def test_brand_forced_first(self):
        self.entries[0]["position"], self.entries[1]["position"] = 1, 2
        self.assertFails("position 1")

    def test_brand_on_failed_gate_page(self):
        self.gate = gate(eligible=False)
        self.assertFails("failed the gate")

    def test_pre_launch_brand_listed(self):
        self.gate = gate(pre_launch=True)
        self.assertFails("pre-launch")

    def test_stale_evidence(self):
        self.rows[1]["captured_on"] = "2026-04-01"
        self.assertFails("days ago")

    def test_wrong_price(self):
        self.rows[2]["value"] = "$99"
        self.rows[2]["quote"] = "Plans start at $99 per month."
        self.assertFails("quote not found verbatim")

    def test_too_few_entries(self):
        self.entries = self.entries[:3]
        self.assertFails("needs 4 to 10")

    def test_missing_not_for(self):
        self.entries[2]["not_for"] = ""
        self.assertFails("has no not_for")

    def test_not_published_needs_no_quote(self):
        self.rows[3].update(value="Not published", quote="", snapshot_path="")
        code, out = self.run_check()
        self.assertEqual(code, 0, out)


class SharedImport(unittest.TestCase):
    def test_volume_uses_the_packs_shared_dataforseo_module(self):
        shared = Path(__file__).resolve().parents[2] / "_shared" / "scripts" / "dataforseo_api.py"
        self.assertEqual(Path(bxy.dfs.__file__).resolve(), shared)
        self.assertFalse(hasattr(bxy, "_dfs_volume"), "bxy.py still carries a private DataForSEO client")
        self.assertFalse(hasattr(bxy, "DFS_LOCATIONS"), "bxy.py still carries private location codes")
        self.assertEqual(bxy.dfs.location_code("ZA"), 2710)
        with self.assertRaises(bxy.dfs.DataForSEOError):
            bxy.dfs.location_code("XX")


if __name__ == "__main__":
    unittest.main()
