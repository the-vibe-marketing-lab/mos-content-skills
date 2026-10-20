#!/usr/bin/env python3
"""bxy.py: the deterministic half of mos-content-best-x-for-y.

The model does the judgement (which Ys, does the brand pass, which criteria,
who is "best for" what). This script does the parts that must not rest on a
model's say-so:

  volume  Google search volume per keyword and market via DataForSEO
          (Google Ads search volume). Missing credentials are reported, never
          guessed: every value becomes null with a reason.
  gate    Apply the eligibility rule to the model's per-page test results:
          the brand is on a page only if it passes all five tests
          (offer, audience, proof, price, availability), and a pre-launch
          brand passes nowhere. Ranks the shortlist for the user to pick from.
  check   Fail the brief build on the banned patterns: a year in the title,
          AggregateRating guidance, no disclosure, no methodology, no
          "last checked" instruction, no ItemList guidance, an entry count
          outside 4 to 10, an entry with no "best for" / "not for" /
          criterion / evidence, the brand on a page it failed the gate for,
          the brand at #1 without a stated winning criterion, and evidence
          rows that are stale, unsourced, or whose quote is not in the saved
          snapshot.

Standard library only. DataForSEO HTTP, credentials and location codes are
owned by the pack's shared `_shared/scripts/dataforseo_api.py`, imported here
through this file's real path (so a symlinked skill folder still finds the
pack's copy, never another pack's `_shared`). Credentials resolve from (1) the
environment, then (2) --env-file, then (3) a .env walked up from the current
folder. No hardcoded paths.
"""
from __future__ import annotations

import argparse
import csv
import datetime as dt
import json
import os
import re
import sys
from pathlib import Path

_SHARED_SCRIPTS = Path(os.path.realpath(__file__)).parents[2] / "_shared" / "scripts"
sys.path.insert(0, str(_SHARED_SCRIPTS))
import dataforseo_api as dfs  # noqa: E402

TESTS = ("offer", "audience", "proof", "price", "availability")
NEGATION = re.compile(r"\b(never|not|no|don't|do not|avoid|without|ban|banned)\b", re.I)
YEAR = re.compile(r"\b(19|20)\d{2}\b")
EVIDENCE_COLUMNS = ("id", "entry", "claim", "value", "source_url",
                    "snapshot_path", "captured_on", "quote")


# --------------------------------------------------------------------------
# volume (HTTP and credentials: _shared/scripts/dataforseo_api.py)
# --------------------------------------------------------------------------

def cmd_volume(args) -> int:
    keywords = list(args.keywords or [])
    if args.keywords_file:
        keywords += [k.strip() for k in Path(args.keywords_file).read_text(encoding="utf-8").splitlines()
                     if k.strip() and not k.lstrip().startswith("#")]
    keywords = list(dict.fromkeys(k.lower() for k in keywords))
    if not keywords:
        print("ERROR: no keywords given (--keywords or --keywords-file)", file=sys.stderr)
        return 2
    countries = [c.upper() for c in (args.country or ["AU"])]
    login, password = dfs.find_credentials(args.env_file)
    cost_before = dfs.TOTAL_COST
    result = {"provider": "dataforseo", "captured_on": dt.date.today().isoformat(),
              "countries": countries, "keywords": {k: {} for k in keywords}, "notes": []}
    if not (login and password):
        msg = "Not available (no DATAFORSEO key): set DATAFORSEO_LOGIN and DATAFORSEO_PASSWORD"
        result["status"] = "no_key"
        result["notes"].append(msg)
        for k in keywords:
            for c in countries:
                result["keywords"][k][c] = None
        print(msg, file=sys.stderr)
    else:
        result["status"] = "ok"
        for c in countries:
            try:
                vols = dfs.search_volume(keywords, c, login, password)
            except dfs.DataForSEOError as e:
                result["status"] = "partial"
                result["notes"].append(f"{c}: {e}")
                vols = {}
            for k in keywords:
                row = vols.get(k)
                result["keywords"][k][c] = row["volume"] if row else None
                if row:
                    result["keywords"][k][f"cpc_{c}"] = row["cpc"]
    result["cost_usd"] = round(dfs.TOTAL_COST - cost_before, 4)
    Path(args.out).parent.mkdir(parents=True, exist_ok=True)
    Path(args.out).write_text(json.dumps(result, indent=1), encoding="utf-8")
    for k in keywords:
        cells = "  ".join(f"{c}={result['keywords'][k].get(c)}" for c in countries)
        print(f"{k}: {cells}")
    print(f"wrote {args.out} (status: {result['status']})", file=sys.stderr)
    print(f"[cost] DataForSEO ${result['cost_usd']:.4f}", file=sys.stderr)
    return 0


# --------------------------------------------------------------------------
# gate
# --------------------------------------------------------------------------

def evaluate_gate(spec: dict) -> dict:
    pre_launch = bool(spec.get("pre_launch"))
    pages_out = []
    for page in spec.get("pages", []):
        tests = page.get("tests") or {}
        failed, missing = [], []
        for t in TESTS:
            res = tests.get(t)
            if not isinstance(res, dict) or "pass" not in res:
                missing.append(t)
            elif not res.get("pass"):
                failed.append({"test": t, "why": res.get("why", "")})
        eligible = not pre_launch and not failed and not missing
        reason = ("pre-launch brand: passes nowhere" if pre_launch else
                  "missing test results: " + ", ".join(missing) if missing else
                  "failed: " + "; ".join(f"{f['test']} ({f['why']})" for f in failed) if failed else
                  "passed all five tests")
        demand = page.get("demand") or {}
        vols = demand.get("volume") or {}
        total = sum(v for v in vols.values() if isinstance(v, (int, float)))
        checked = demand.get("engines_checked") or 0
        named = demand.get("brand_named_by") or 0
        pages_out.append({
            "y": page.get("y"), "title": page.get("title"), "keyword": page.get("keyword"),
            "source": page.get("source", "discovered"),
            "brand_eligible": eligible, "reason": reason,
            "failed_tests": failed, "missing_tests": missing,
            "volume_total": total, "engines_checked": checked, "brand_named_by": named,
            "ai_gap": max(checked - named, 0),
        })
    pages_out.sort(key=lambda p: (-p["ai_gap"], -p["volume_total"], p["y"] or ""))
    for i, p in enumerate(pages_out, 1):
        p["rank"] = i
    return {"brand": spec.get("brand"), "pre_launch": pre_launch,
            "evaluated_on": dt.date.today().isoformat(), "pages": pages_out}


def cmd_gate(args) -> int:
    spec = json.loads(Path(args.input).read_text(encoding="utf-8"))
    out = evaluate_gate(spec)
    Path(args.out).write_text(json.dumps(out, indent=1), encoding="utf-8")
    print(f"{'#':>2}  {'src':<10} {'brand':<8} {'vol':>6} {'gap':>3}  page / reason")
    for p in out["pages"]:
        print(f"{p['rank']:>2}  {p['source']:<10} {'ON' if p['brand_eligible'] else 'off':<8} "
              f"{p['volume_total']:>6} {p['ai_gap']:>3}  {p['title'] or p['y']}  [{p['reason']}]")
    print(f"wrote {args.out}", file=sys.stderr)
    return 0


# --------------------------------------------------------------------------
# check
# --------------------------------------------------------------------------

def _norm(text: str) -> str:
    text = text.replace("’", "'").replace("‘", "'").replace("“", '"').replace("”", '"')
    return re.sub(r"\s+", " ", text).strip().lower()


def check_evidence(csv_path: Path, max_age: int, today: dt.date) -> tuple[list[str], set[str]]:
    errors: list[str] = []
    ids: set[str] = set()
    if not csv_path.is_file():
        return [f"evidence: {csv_path} not found"], ids
    with csv_path.open(encoding="utf-8", newline="") as fh:
        reader = csv.DictReader(fh)
        cols = set(reader.fieldnames or [])
        missing = [c for c in EVIDENCE_COLUMNS if c not in cols]
        if missing:
            return [f"evidence: missing columns {', '.join(missing)}"], ids
        for n, row in enumerate(reader, 2):
            rid = (row["id"] or "").strip()
            where = f"evidence.csv line {n} ({rid or 'no id'})"
            if not rid:
                errors.append(f"{where}: empty id")
            ids.add(rid)
            if not (row["source_url"] or "").strip().lower().startswith(("http://", "https://")):
                errors.append(f"{where}: source_url is not a URL")
            try:
                captured = dt.date.fromisoformat((row["captured_on"] or "").strip())
                age = (today - captured).days
                if age > max_age:
                    errors.append(f"{where}: captured {age} days ago (limit {max_age}); re-capture it")
                if age < 0:
                    errors.append(f"{where}: captured_on is in the future")
            except ValueError:
                errors.append(f"{where}: captured_on is not YYYY-MM-DD")
            value = (row["value"] or "").strip()
            if value.lower() == "not published":
                continue  # the pages checked are the evidence; no quote exists to match
            quote = (row["quote"] or "").strip()
            if not quote:
                errors.append(f"{where}: no verbatim quote (use value 'Not published' if nobody publishes it)")
                continue
            snap = (row["snapshot_path"] or "").strip()
            snap_path = (csv_path.parent / snap) if snap else None
            if not snap_path or not snap_path.is_file():
                errors.append(f"{where}: snapshot '{snap}' not found")
                continue
            if _norm(quote) not in _norm(snap_path.read_text(encoding="utf-8", errors="replace")):
                errors.append(f"{where}: quote not found verbatim in {snap}")
            if value and any(ch.isdigit() for ch in value) and _norm(value) not in _norm(quote):
                errors.append(f"{where}: numeric value '{value}' does not appear in its quote")
    return errors, ids


def check_picks(picks: dict, gate: dict | None, page_y: str | None, ids: set[str]) -> list[str]:
    errors: list[str] = []
    entries = picks.get("entries") or []
    brand = (picks.get("brand") or (gate or {}).get("brand") or "").strip().lower()
    if not 4 <= len(entries) <= 10:
        errors.append(f"picks: {len(entries)} entries; a buyer's guide needs 4 to 10")
    for e in entries:
        name = e.get("name") or "?"
        for field in ("best_for", "not_for", "criterion"):
            if not str(e.get(field) or "").strip():
                errors.append(f"picks: '{name}' has no {field}")
        ev = e.get("evidence") or []
        if not ev:
            errors.append(f"picks: '{name}' cites no evidence rows")
        for rid in ev:
            if rid not in ids:
                errors.append(f"picks: '{name}' cites evidence '{rid}' which is not in evidence.csv")
    brand_entries = [e for e in entries
                     if e.get("is_brand") or (brand and str(e.get("name", "")).strip().lower() == brand)]
    if brand_entries:
        page = None
        y = (page_y or picks.get("page_y") or "").strip().lower()
        for p in (gate or {}).get("pages", []):
            if str(p.get("y") or "").strip().lower() == y or str(p.get("title") or "").strip().lower() == y:
                page = p
        if gate is None:
            errors.append("gate: the brand is listed but no gate result was given (--gate)")
        elif gate.get("pre_launch"):
            errors.append("gate: the brand is pre-launch and may not appear on any page")
        elif page is None:
            errors.append(f"gate: no gate result for page '{page_y or picks.get('page_y')}'")
        elif not page.get("brand_eligible"):
            errors.append(f"gate: the brand failed the gate for this page ({page.get('reason')}) but is listed")
    best = picks.get("best_overall") or {}
    for e in entries:
        if e.get("position") == 1 and e in brand_entries:
            ok = (str(best.get("entry", "")).strip().lower() == str(e.get("name", "")).strip().lower()
                  and str(best.get("criterion") or "").strip() and best.get("evidence"))
            if not ok:
                errors.append("picks: the brand is at position 1 without a best_overall record "
                              "naming the winning criterion and its evidence")
    return errors


def check_brief(text: str, picks: dict) -> tuple[list[str], list[str]]:
    errors, warnings = [], []
    lower = text.lower()
    prev_label = ""
    for n, line in enumerate(text.splitlines(), 1):
        stripped = line.strip()
        if not stripped:
            continue
        is_h1 = bool(re.match(r"#\s", stripped))
        is_title = ((bool(re.search(r"\btitle\b", stripped, re.I)) and not re.match(r"#{2,}\s", stripped))
                    or bool(re.search(r"\b(title|h1)\b", prev_label, re.I)))
        prev_label = stripped if re.fullmatch(r"\*\*[^*]+\*\*:?", stripped) else ""
        if YEAR.search(stripped) and (is_h1 or is_title):
            if not re.search(r"\b(date|captured|checked|generated)\b", stripped, re.I):
                errors.append(f"brief line {n}: a year in the title ({stripped[:80]})")
        elif YEAR.search(stripped) and re.match(r"#{2,}\s", stripped):
            warnings.append(f"brief line {n}: a year in a heading ({stripped[:80]})")
        if re.search(r"aggregaterating|review schema", stripped, re.I) and not NEGATION.search(stripped):
            errors.append(f"brief line {n}: AggregateRating / Review schema guidance ({stripped[:80]})")
        if re.match(r"#{1,4}\s.*best overall", stripped, re.I) and not picks.get("best_overall"):
            errors.append(f"brief line {n}: a 'best overall' heading with no best_overall record in picks.json")
    for needle, label in (("disclosure", "a disclosure line"),
                          ("last checked", "a visible 'last checked' date instruction"),
                          ("itemlist", "ItemList schema guidance")):
        if needle not in lower:
            errors.append(f"brief: missing {label}")
    if not re.search(r"^#{1,4}\s.*(how we chose|methodology)", text, re.I | re.M):
        errors.append("brief: missing the methodology block (a 'How we chose' heading)")
    if "best for" not in lower or "not for" not in lower:
        errors.append("brief: the outline has no 'Best for' / 'Not for' instructions")
    return errors, warnings


def cmd_check(args) -> int:
    today = dt.date.fromisoformat(args.today) if args.today else dt.date.today()
    research = Path(args.research)
    gate = json.loads(Path(args.gate).read_text(encoding="utf-8")) if args.gate else None
    picks_path = research / "picks.json"
    picks = json.loads(picks_path.read_text(encoding="utf-8")) if picks_path.is_file() else {}
    errors: list[str] = []
    warnings: list[str] = []
    if not picks:
        errors.append(f"picks: {picks_path} not found or empty")
    ev_errors, ids = check_evidence(research / "evidence.csv", args.max_age_days, today)
    errors += ev_errors
    if picks:
        errors += check_picks(picks, gate, args.page, ids)
    if args.brief:
        b_err, b_warn = check_brief(Path(args.brief).read_text(encoding="utf-8"), picks)
        errors += b_err
        warnings += b_warn
    for w in warnings:
        print(f"WARN  {w}")
    for e in errors:
        print(f"FAIL  {e}")
    if errors:
        print(f"\n{len(errors)} check(s) failed. Fix them before the brief ships.")
        return 1
    print("PASS  all checks green" + (f" ({len(warnings)} warning(s))" if warnings else ""))
    return 0


# --------------------------------------------------------------------------

def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(prog="bxy.py", description=__doc__.split("\n\n")[0])
    sub = ap.add_subparsers(dest="cmd", required=True)

    v = sub.add_parser("volume", help="Google search volume per keyword and market (DataForSEO)")
    v.add_argument("--keywords", nargs="*", help="keywords, space separated (quote each)")
    v.add_argument("--keywords-file", help="one keyword per line")
    v.add_argument("--country", action="append", help="2-letter market; repeat for several (default AU)")
    v.add_argument("--env-file", help="a .env to read first (optional)")
    v.add_argument("--out", required=True, help="where to write volume.json")
    v.set_defaults(func=cmd_volume)

    g = sub.add_parser("gate", help="apply the five-test eligibility rule and rank the shortlist")
    g.add_argument("--in", dest="input", required=True, help="gate.json written by the model")
    g.add_argument("--out", required=True, help="where to write gate-result.json")
    g.set_defaults(func=cmd_gate)

    c = sub.add_parser("check", help="fail the build on banned patterns and weak evidence")
    c.add_argument("--research", required=True, help="the page's brief/research folder "
                   "(holds picks.json, evidence.csv, snapshots/)")
    c.add_argument("--brief", help="the built -brief.md to scan")
    c.add_argument("--gate", help="gate-result.json from the shortlist run")
    c.add_argument("--page", help="the page's Y or title as written in gate-result.json")
    c.add_argument("--max-age-days", type=int, default=90)
    c.add_argument("--today", help="override today's date (YYYY-MM-DD), for tests")
    c.set_defaults(func=cmd_check)
    return ap


def main(argv=None) -> int:
    args = build_parser().parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
