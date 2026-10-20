#!/usr/bin/env python3
"""
fetch_page.py — the single page fetcher for every mos-content skill that reads a live URL.

Why this exists: skills were each rolling their own fetch — WebFetch here, `curl | sed`
there, Firecrawl somewhere else. Three problems followed. (1) `curl` and WebFetch cannot
render JavaScript, so a JS-built storefront returns HTTP 200 with an empty <title> and the
caller happily reports "extracted successfully" from nothing. That exact failure hit a
competitor research run in August 2026: two JS storefronts both returned 200 and no content. (2) Every skill paid Firecrawl credits for pages that
plain HTTP would have handled fine. (3) Each skill had a different idea of what "the fetch
failed" meant.

This module fixes all three with one escalating ladder. Each tier is tried only when the
cheaper tier below it produced something genuinely unusable, judged on *content*, not on
the HTTP status code:

  Tier 1  scrapling.Fetcher            HTTP only, no browser.  ~0.5-2s.   Free.
  Tier 2  scrapling.StealthyFetcher    Real browser, renders JS. ~5-25s.  Free.
  Tier 3  Firecrawl REST v2            Hosted render + markdown. ~3-15s.  Costs credits.

Most pages resolve at tier 1. Escalation is the exception, and the JSON records which tier
answered and why it climbed, so a caller can report honestly instead of guessing.

WINDOWS NOTE — the one non-obvious flag. Scrapling's browser tiers launch a *persistent*
browser context. On some Windows machines the chromium build that Patchright bundles fails that
launch with "spawn UNKNOWN" (a plain non-persistent launch works, so the browser binary is
fine — it is persistent-context specific, and it reproduces under git-bash, cmd and
PowerShell alike). Passing real_chrome=True uses the installed Google Chrome instead and
works. So tier 2 tries real Chrome first and only falls back to the bundled build. If you
are on macOS or Linux and have no Chrome installed, the bundled build is used and is fine.

Setup, once per machine, if tier 2 is to be available at all:
    scrapling install                 # or: python -m patchright install chromium

Usage:
    python3 fetch_page.py <url>                        # JSON to stdout (default)
    python3 fetch_page.py <url> --md                   # markdown document
    python3 fetch_page.py <url> --text                 # clean text only
    python3 fetch_page.py <url> --tier browser         # force a tier
    python3 fetch_page.py <url> --min-text 1500        # stricter quality gate
    python3 fetch_page.py --check                      # report which tiers are usable

Exit codes: 0 = a tier returned usable content, 3 = every tier failed (details in JSON).
A page that is genuinely thin (a stub contact page) still exits 0 — "little content" and
"failed to fetch" are different answers and callers need to tell them apart.
"""

from __future__ import annotations

import argparse
import io
import json
import os
import re
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path
from typing import Any

# Scrapling logs "INFO: Fetched (200) <GET ...>" for every request. It goes to stderr, so
# stdout stays clean JSON — but callers piping this script should still redirect 2>/dev/null
# to keep those lines out of an agent's transcript.
os.environ.setdefault("PYTHONIOENCODING", "utf-8")

# Windows consoles default to cp1252 and Scrapling's banners contain box-drawing characters,
# so an otherwise-successful run dies in the print with a UnicodeEncodeError. Force UTF-8.
if sys.stdout.encoding and sys.stdout.encoding.lower() not in ("utf-8", "utf8"):
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8", errors="replace")

DEFAULT_MIN_TEXT = 600
DEFAULT_TIMEOUT = 30
BROWSER_TIMEOUT_MS = 45_000
FIRECRAWL_ENDPOINT = "https://api.firecrawl.dev/v2/scrape"


# --------------------------------------------------------------------------- credentials


def _load_key(name: str) -> str:
    """Resolve an API key from the environment, then any .env walked up from CWD (normally
    the MarketingOS brain root). No other locations. Shell state does not survive between separate Bash tool calls, so
    a script that trusts os.environ alone fails whenever the caller did not source .env in
    the very same command — the same trap documented in apify_common.py."""
    val = os.environ.get(name)
    if val and val.strip():
        return val.strip()

    candidates = []
    here = os.path.abspath(os.getcwd())
    while True:
        candidates.append(os.path.join(here, ".env"))
        parent = os.path.dirname(here)
        if parent == here:
            break
        here = parent

    for path in candidates:
        if os.path.isfile(path):
            try:
                with open(path, encoding="utf-8") as fh:
                    for line in fh:
                        line = line.strip()
                        if line.startswith(f"{name}="):
                            # .strip of quotes and \r guards against a CRLF .env (common on Windows).
                            return line.split("=", 1)[1].strip().strip('"').strip("'").strip()
            except OSError:
                continue
    return ""


# ------------------------------------------------------------------------------- helpers


def _clean(text: str | None) -> str:
    return re.sub(r"\s+", " ", text).strip() if text else ""


def _assess(title: str, text: str, html_bytes: int, min_text: int) -> tuple[bool, str]:
    """Decide whether a fetch produced something worth keeping.

    A 200 status means the server answered, not that the answer contains the page. A
    JS-rendered storefront returns a valid shell with an empty body, which is precisely the
    case that made callers report success on nothing. So judge the content — but carefully,
    because "short" and "unrendered" are not the same thing.

    A small contact page with 300 words is complete. Escalating it to a browser and then to
    Firecrawl wastes 30 seconds and real credits to re-fetch content already in hand. The
    signal that actually separates the two cases is the *ratio*: an unrendered SPA shell is a
    large HTML payload wrapped around almost no text, whereas a genuinely small page is small
    all the way through. So look for a missing title, a near-empty body, or the shell shape —
    and otherwise accept what came back.

    Returns (is_usable, reason_if_not).
    """
    chars = len(text)

    if not title:
        return False, "no <title> — page shell likely rendered client-side"
    if chars < 200 and html_bytes > 5_000:
        return False, f"near-empty body — {chars} chars of text inside {html_bytes:,} bytes of HTML"
    if chars < min_text and html_bytes > 40_000:
        return False, (f"shell shape — {html_bytes:,} bytes of HTML wrapping only {chars} chars "
                       f"of text, which usually means the body is rendered client-side")
    return True, ""


def _parse_scrapling(page: Any, url: str, tier: str, elapsed: float) -> dict:
    """Pull the structured fields a business-context scrape needs out of a Scrapling page.

    Note the idiom: Scrapling Selectors expose .get() and .getall(); there is no css_first,
    and indexing the result of a ::text selector raises "Text nodes do not have attributes".
    """
    title = _clean(page.css("title::text").get())
    text = re.sub(r"\n{3,}", "\n\n", page.get_all_text(ignore_tags=("script", "style", "noscript")))

    return {
        "url": url,
        "final_url": getattr(page, "url", url) or url,
        "status": getattr(page, "status", None),
        "tier": tier,
        "title": title,
        "meta_description": _clean(page.css("meta[name='description']::attr(content)").get()),
        "og_site_name": _clean(page.css("meta[property='og:site_name']::attr(content)").get()),
        "headings": {
            "h1": [_clean(h) for h in page.css("h1::text").getall() if _clean(h)][:10],
            "h2": [_clean(h) for h in page.css("h2::text").getall() if _clean(h)][:25],
        },
        "links": _dedupe(page.css("a::attr(href)").getall(), url)[:150],
        "emails": _find_emails(text),
        "phones": _find_phones(text),
        "text": text.strip(),
        "text_chars": len(text.strip()),
        "html_bytes": len(getattr(page, "html_content", "") or ""),
        "elapsed_s": round(elapsed, 2),
    }


def _dedupe(hrefs: list[str], base: str) -> list[str]:
    """Absolute URLs only — every brief rule in this workspace requires absolute links, and a
    relative href is useless to a downstream agent that no longer knows the base."""
    from urllib.parse import urljoin

    seen, out = set(), []
    for h in hrefs:
        if not h or h.startswith(("#", "javascript:", "mailto:", "tel:")):
            continue
        absolute = urljoin(base, h)
        if absolute not in seen:
            seen.add(absolute)
            out.append(absolute)
    return out


def _find_emails(text: str) -> list[str]:
    return sorted({m.lower() for m in re.findall(r"[\w.+-]+@[\w-]+\.[\w.-]+", text)})[:10]


def _find_phones(text: str) -> list[str]:
    """Australian-leaning patterns — landline, mobile and 1300/1800 service numbers."""
    pat = r"(?:\+?61[\s-]?)?(?:\(0\d\)|0\d)[\s-]?\d{4}[\s-]?\d{4}|1[38]00[\s-]?\d{3}[\s-]?\d{3}"
    return sorted({_clean(m) for m in re.findall(pat, text)})[:10]


# --------------------------------------------------------------------------------- tiers


def tier_http(url: str, timeout: int) -> dict:
    from scrapling.fetchers import Fetcher

    start = time.time()
    page = Fetcher.get(url, timeout=timeout, stealthy_headers=True)
    return _parse_scrapling(page, url, "http", time.time() - start)


def tier_browser(url: str, timeout_ms: int = BROWSER_TIMEOUT_MS) -> dict:
    """Render with a real browser. Tries system Chrome first — see the Windows note in the
    module docstring for why the bundled build is the fallback rather than the default."""
    from scrapling.fetchers import StealthyFetcher

    errors = []
    for real_chrome in (True, False):
        start = time.time()
        try:
            # load_dom, not network_idle. Waiting for an idle network sounds thorough but many
            # commercial sites hold analytics and chat sockets open forever, so network_idle
            # never fires and the fetch burns the entire timeout — 122s on a page that had
            # finished rendering in about 8. Waiting for the DOM gets the same content quickly.
            page = StealthyFetcher.fetch(
                url,
                headless=True,
                timeout=timeout_ms,
                real_chrome=real_chrome,
                load_dom=True,
            )
            result = _parse_scrapling(page, url, "browser", time.time() - start)
            result["real_chrome"] = real_chrome
            return result
        except Exception as exc:  # noqa: BLE001 — every browser failure should fall through
            errors.append(f"real_chrome={real_chrome}: {type(exc).__name__}: {str(exc)[:160]}")
    raise RuntimeError(" | ".join(errors))


def tier_firecrawl(url: str) -> dict:
    """Hosted render. Costs credits, so it sits last — but it is the most reliable tier and
    the only one that returns clean markdown without a local conversion step."""
    key = _load_key("FIRECRAWL_API_KEY")
    if not key:
        raise RuntimeError("FIRECRAWL_API_KEY not found in environment or any .env")

    payload = json.dumps({"url": url, "formats": ["markdown"], "onlyMainContent": True}).encode()
    req = urllib.request.Request(
        FIRECRAWL_ENDPOINT,
        data=payload,
        headers={"Authorization": f"Bearer {key}", "Content-Type": "application/json"},
    )
    start = time.time()
    try:
        with urllib.request.urlopen(req, timeout=120) as resp:
            body = json.loads(resp.read().decode("utf-8", errors="replace"))
    except urllib.error.HTTPError as exc:
        raise RuntimeError(f"HTTP {exc.code}: {exc.read()[:200].decode(errors='replace')}") from None

    if not body.get("success"):
        raise RuntimeError(f"Firecrawl returned success=false: {str(body)[:200]}")

    data = body.get("data", {})
    meta = data.get("metadata", {})
    markdown = data.get("markdown", "") or ""
    text = re.sub(r"[#*`>\[\]()_]", " ", markdown)

    return {
        "url": url,
        "final_url": meta.get("sourceURL", url),
        "status": meta.get("statusCode"),
        "tier": "firecrawl",
        "title": _clean(meta.get("title")),
        "meta_description": _clean(meta.get("description")),
        "og_site_name": _clean(meta.get("ogSiteName")),
        "headings": {
            "h1": [_clean(m) for m in re.findall(r"^#\s+(.+)$", markdown, re.M)][:10],
            "h2": [_clean(m) for m in re.findall(r"^##\s+(.+)$", markdown, re.M)][:25],
        },
        "links": _dedupe(re.findall(r"\]\((https?://[^)\s]+)\)", markdown), url)[:150],
        "emails": _find_emails(markdown),
        "phones": _find_phones(markdown),
        "markdown": markdown,
        "text": re.sub(r"\s+", " ", text).strip(),
        "text_chars": len(markdown),
        "html_bytes": None,
        "elapsed_s": round(time.time() - start, 2),
    }


# ---------------------------------------------------------------------------- the ladder


TIERS = {"http": tier_http, "browser": tier_browser, "firecrawl": tier_firecrawl}


def fetch(url: str, *, tier: str = "auto", min_text: int = DEFAULT_MIN_TEXT,
          timeout: int = DEFAULT_TIMEOUT) -> dict:
    """Run the ladder and return the first genuinely usable result.

    When a tier is forced, its result is returned whatever its quality — the caller asked for
    that tier specifically and silently overriding them would be worse than an honest answer.
    """
    if tier != "auto":
        if tier not in TIERS:
            raise ValueError(f"unknown tier {tier!r}; choose from {', '.join(TIERS)} or auto")
        fn = TIERS[tier]
        result = fn(url, timeout) if tier == "http" else fn(url)
        result["ok"] = True
        result["escalations"] = []
        result["forced_tier"] = tier
        return result

    escalations: list[dict] = []
    last_thin: dict | None = None

    for name in ("http", "browser", "firecrawl"):
        try:
            fn = TIERS[name]
            result = fn(url, timeout) if name == "http" else fn(url)
        except Exception as exc:  # noqa: BLE001 — a broken tier must not end the ladder
            escalations.append({"tier": name, "reason": f"{type(exc).__name__}: {str(exc)[:200]}"})
            continue

        usable, why = _assess(result.get("title", ""), result.get("text", ""),
                              result.get("html_bytes") or 0, min_text)
        if usable:
            result["ok"] = True
            result["escalations"] = escalations
            return result

        escalations.append({"tier": name, "reason": why})
        last_thin = result

    # Every tier either errored or came back thin. If something was actually retrieved, hand it
    # back flagged rather than throwing it away — a genuinely sparse page is a real finding, and
    # the caller can see from `escalations` that the whole ladder was exhausted.
    if last_thin is not None:
        last_thin["ok"] = False
        last_thin["escalations"] = escalations
        last_thin["note"] = "all tiers returned thin content — the page may genuinely be sparse"
        return last_thin

    return {"url": url, "ok": False, "tier": None, "escalations": escalations,
            "error": "every tier failed to fetch this URL"}


# ----------------------------------------------------------------------------- diagnostics


def check() -> dict:
    """Report which tiers this machine can actually use. Run this before blaming a skill for a
    bad scrape — a missing browser and a blocked site look identical from the output alone."""
    report: dict[str, Any] = {}

    try:
        import scrapling
        report["scrapling"] = {"available": True, "version": scrapling.__version__}
    except ImportError as exc:
        report["scrapling"] = {"available": False, "error": str(exc), "fix": "pip install scrapling"}

    try:
        page = tier_http("https://example.com", 20)
        report["tier_1_http"] = {"available": True, "status": page["status"]}
    except Exception as exc:  # noqa: BLE001
        report["tier_1_http"] = {"available": False, "error": f"{type(exc).__name__}: {exc}"}

    try:
        page = tier_browser("https://example.com", timeout_ms=90_000)
        report["tier_2_browser"] = {"available": True, "real_chrome": page.get("real_chrome")}
    except Exception as exc:  # noqa: BLE001
        report["tier_2_browser"] = {
            "available": False,
            "error": str(exc)[:300],
            "fix": "run `scrapling install`; on Windows also `python -m patchright install chromium`. "
                   "If the error is 'spawn UNKNOWN', install Google Chrome — real_chrome=True is the "
                   "working path on Windows.",
        }

    key = _load_key("FIRECRAWL_API_KEY")
    report["tier_3_firecrawl"] = (
        {"available": True, "key_source": ".env or environment"}
        if key else {"available": False, "fix": "add FIRECRAWL_API_KEY to the brain's .env or export it"}
    )
    return report


# ----------------------------------------------------------------------------------- CLI


def to_markdown(r: dict) -> str:
    if r.get("markdown"):
        head = f"# {r.get('title') or r['url']}\n\n**Source:** {r.get('final_url', r['url'])}\n" \
               f"**Fetched via:** {r.get('tier')}\n\n---\n\n"
        return head + r["markdown"]

    lines = [f"# {r.get('title') or r['url']}", ""]
    lines += [f"**Source:** {r.get('final_url', r['url'])}", f"**Fetched via:** {r.get('tier')}", ""]
    if r.get("meta_description"):
        lines += [f"> {r['meta_description']}", ""]
    for level, key in (("##", "h1"), ("###", "h2")):
        for h in r.get("headings", {}).get(key, []):
            lines.append(f"{level} {h}")
    if r.get("emails") or r.get("phones"):
        lines += ["", "## Contact details found", ""]
        lines += [f"- {e}" for e in r.get("emails", [])]
        lines += [f"- {p}" for p in r.get("phones", [])]
    lines += ["", "## Page text", "", r.get("text", "")]
    return "\n".join(lines)


def main() -> int:
    ap = argparse.ArgumentParser(description="Fetch a page via Scrapling, falling back to Firecrawl.")
    ap.add_argument("url", nargs="?", help="URL to fetch")
    ap.add_argument("--tier", default="auto", choices=["auto", "http", "browser", "firecrawl"],
                    help="force a specific tier instead of escalating (default: auto)")
    ap.add_argument("--min-text", type=int, default=DEFAULT_MIN_TEXT,
                    help=f"chars of text below which a tier is judged to have failed (default {DEFAULT_MIN_TEXT})")
    ap.add_argument("--timeout", type=int, default=DEFAULT_TIMEOUT, help="HTTP tier timeout in seconds")
    ap.add_argument("--md", action="store_true", help="emit a markdown document")
    ap.add_argument("--text", action="store_true", help="emit clean text only")
    ap.add_argument("--check", action="store_true", help="report which tiers this machine can use")
    args = ap.parse_args()

    if args.check:
        print(json.dumps(check(), indent=2))
        return 0
    if not args.url:
        ap.error("a URL is required unless --check is given")

    result = fetch(args.url, tier=args.tier, min_text=args.min_text, timeout=args.timeout)

    if args.text:
        print(result.get("text", ""))
    elif args.md:
        print(to_markdown(result))
    else:
        print(json.dumps(result, indent=2, ensure_ascii=False))

    if not result.get("ok") and result.get("tier") is None:
        return 3
    return 0


if __name__ == "__main__":
    sys.exit(main())
