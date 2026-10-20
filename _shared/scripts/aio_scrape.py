#!/usr/bin/env python3
"""
Live AI Overview capture — runs the `scrape.badger/google-search-scraper` Apify actor
for a keyword and prints the ACTUAL Google AI Overview (verbatim text + cited sources).

The brief skills call this so the brief's "AI Overview" row contains the real AIO for the
primary keyword, not a guess. Reads APIFY_API_KEY from the environment or the brain's .env automatically.

Why this actor: tested 2026-05-29 against AU question queries. The dedicated
`clearpath/google-ai-overview` actor timed out / returned nothing twice; scrape.badger
(16k+ runs) returned a clean `ai_overview` object reliably, ~0.2c/query, AIO + full SERP.

Usage:
  python3 aio_scrape.py "does income protection cover redundancy"            # human-readable
  python3 aio_scrape.py "does income protection cover redundancy" --country au --json
  python3 aio_scrape.py "<keyword>" --md       # markdown block ready to paste into a brief

Exit codes: 0 = ran OK (AIO may or may not be present), 2 = actor/credential error.
A "no AI Overview present" result is a valid, successful outcome (exit 0) — report it as-is.
"""
import argparse
import json
import os
import sys
import time
import urllib.parse
import urllib.request

ACTOR = "scrape.badger~google-search-scraper"
API = "https://api.apify.com/v2"
POLL_SECS = 12
MAX_WAIT_SECS = 360


def _load_token() -> str:
    # Delegates to the shared loader: env -> .env walked up from CWD.
    sys.path.insert(0, os.path.dirname(os.path.realpath(__file__)))
    from apify_common import _load_apify_token
    return _load_apify_token()


def _post(url: str, body: dict) -> dict:
    req = urllib.request.Request(
        url, data=json.dumps(body).encode(), method="POST",
        headers={"Content-Type": "application/json"},
    )
    with urllib.request.urlopen(req, timeout=60) as r:
        return json.loads(r.read().decode())


def _get(url: str) -> dict:
    with urllib.request.urlopen(url, timeout=60) as r:
        return json.loads(r.read().decode())


def capture(keyword: str, country: str = "au") -> dict:
    """Run the actor and return {present, text, text_blocks, references, query, country}."""
    token = _load_token()
    domain = f"google.com.{country}" if country.lower() == "au" else "google.com"
    body = {
        "q": keyword, "mode": "full", "gl": country.lower(), "hl": "en",
        "domain": domain, "ai_overview": True, "max_pages": 1,
    }
    run = _post(f"{API}/acts/{ACTOR}/runs?token={token}", body)["data"]
    run_id = run["id"]

    waited = 0
    status = run["status"]
    while status not in ("SUCCEEDED", "FAILED", "TIMED-OUT", "ABORTED"):
        if waited >= MAX_WAIT_SECS:
            sys.exit(f"ERROR: AIO run {run_id} still {status} after {MAX_WAIT_SECS}s.")
        time.sleep(POLL_SECS)
        waited += POLL_SECS
        status = _get(f"{API}/actor-runs/{run_id}?token={token}")["data"]["status"]
    if status != "SUCCEEDED":
        sys.exit(f"ERROR: AIO run {run_id} ended {status}.")

    ds = _get(f"{API}/actor-runs/{run_id}?token={token}")["data"]["defaultDatasetId"]
    items = _get(f"{API}/datasets/{ds}/items?token={token}")
    item = items[0] if isinstance(items, list) and items else {}
    aio = item.get("ai_overview") or {}

    blocks = aio.get("text_blocks") or []
    text = "\n\n".join(
        b.get("snippet", "").strip() for b in blocks if b.get("snippet")
    ).strip()
    refs = [
        {"title": r.get("title", ""), "link": r.get("link", ""), "source": r.get("source", "")}
        for r in (aio.get("references") or [])
        if r.get("link")
    ]
    return {
        "query": keyword, "country": country,
        "present": bool(text or refs),
        "text": text, "text_blocks": blocks, "references": refs,
    }


def to_markdown(res: dict) -> str:
    """Brief-ready block: the AI Overview verbatim, then 'Sources:' + the exact URLs.

    Format is deliberate (2026-05-29): the verbatim AIO so the writer sees
    exactly what Google says, then the EXACT source URLs underneath so they can open
    and check each one. Plain URLs (not title-links) — one per line, complete and clickable.
    """
    if not res["present"]:
        return (f"AI Overview: none present for \"{res['query']}\" "
                f"({res['country'].upper()}) at capture time.")
    lines = [res["text"]]
    if res["references"]:
        lines += ["", "Sources:"]
        seen = set()
        for r in res["references"]:
            url = r["link"].strip()
            if url and url not in seen:
                seen.add(url)
                lines.append(url)
    return "\n".join(lines)


def main() -> None:
    p = argparse.ArgumentParser(description="Capture the live Google AI Overview for a keyword.")
    p.add_argument("keyword")
    p.add_argument("--country", default="au")
    p.add_argument("--json", action="store_true", help="emit structured JSON")
    p.add_argument("--md", action="store_true", help="emit a markdown block for a brief")
    a = p.parse_args()

    res = capture(a.keyword, a.country)
    if a.json:
        print(json.dumps(res, indent=2, ensure_ascii=False))
    elif a.md:
        print(to_markdown(res))
    else:
        if not res["present"]:
            print(f"No AI Overview present for \"{a.keyword}\" ({a.country.upper()}).")
        else:
            print(f"=== AI Overview for \"{a.keyword}\" ({a.country.upper()}) ===\n")
            print(res["text"])
            print(f"\n--- {len(res['references'])} cited sources ---")
            for i, r in enumerate(res["references"], 1):
                print(f"{i}. {r['title'][:90]}  [{r['source']}]  {r['link']}")


if __name__ == "__main__":
    main()
