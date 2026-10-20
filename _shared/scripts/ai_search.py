#!/usr/bin/env python3
"""
Unified AI-search capture for content briefs.

Gathers, for one primary keyword:
  - Google AI Overview  (default: DataForSEO live SERP with the async AI Overview loaded;
                         optional extra: Apify `scrape.badger~google-search-scraper`, via aio_scrape.py)
  - Google AI Mode      (DataForSEO only; skipped without it)
  - ChatGPT answer + citations  (default: DataForSEO LLM responses with web search on;
                         optional extra: Apify `apify~chatgpt-search-scraper`)
and emits one paste-ready block for a brief's "AI Search Visibility" field: AIO text + sources,
AI Mode text + sources, ChatGPT snippet + citations, and a deduped union of all AI-cited domains
tagged by engine.

Provider order: DataForSEO when DATAFORSEO_LOGIN + DATAFORSEO_PASSWORD resolve, else Apify when
APIFY_API_KEY resolves, else every engine reads "Not available (no DATAFORSEO key)". Force one
with --provider. Every DataForSEO cost is reported (stderr, and `cost_usd` in --json).

Cost-bounded: one call per engine per keyword. --skip-chatgpt / --skip-ai-mode / --skip-aio
drop an engine.

Usage:
  python3 ai_search.py "project management software for small agencies" --country au --md
  python3 ai_search.py "agency time tracking software" --country au --json --skip-chatgpt
  python3 ai_search.py "client portal software" --md --prompt "What is the best client portal for a small agency?"

Exit codes: 0 = ran (any engine may be empty or not available); 2 = provider error on a forced provider.
"""
import argparse
import json
import os
import sys
import urllib.error
import urllib.request
from urllib.parse import urlparse

sys.path.insert(0, os.path.dirname(os.path.realpath(__file__)))
import aio_scrape  # noqa: E402  (same dir)
import dataforseo_api as dfs  # noqa: E402
from apify_common import _load_apify_token  # noqa: E402

# 2026-08-04: tri_angle~gpt-search was removed from the Apify store (GET /acts returns
# 404 "Actor was not found or access denied"; it no longer appears in a store search).
# Its 403 "insufficient-permissions" was mistaken for the one-time actor-approval flow
# for months. Replaced with Apify's own first-party actor, which needs no approval.
CHATGPT_ACTOR = "apify~chatgpt-search-scraper"
API = "https://api.apify.com/v2"
_QUESTION_STARTS = ("what", "how", "is", "are", "can", "do", "does", "why", "who", "when", "where", "should")


def _root_domain(url: str) -> str:
    host = urlparse(url).netloc.lower()
    return host[4:] if host.startswith("www.") else host


_LOCALES = {"au": "Australian", "nz": "New Zealand", "uk": "UK", "gb": "UK", "us": "US", "ca": "Canadian"}


def _default_prompt(keyword: str, country: str = "au") -> str:
    """Build the ChatGPT prompt. The locale MUST be in the prompt text: the
    apify~chatgpt-search-scraper actor has no country input, so an unqualified
    question silently returns US-centric results."""
    k = keyword.strip()
    low = k.lower()
    locale = _LOCALES.get(country.lower(), "")
    if low.endswith("?") or low.split(" ", 1)[0] in _QUESTION_STARTS:
        if locale and locale.lower() not in low and country.lower() not in low:
            return f"{k.rstrip('?')}? Answer for a{'n' if locale[0] in 'AEIOU' else ''} {locale} audience."
        return k
    return f"What is {k}? Explain it for a{'n' if locale and locale[0] in 'AEIOU' else ''} {locale or 'general'} audience."


def capture_aio(keyword: str, country: str = "au") -> dict:
    """Thin wrapper over aio_scrape.capture()."""
    return aio_scrape.capture(keyword, country)


def capture_chatgpt(keyword: str, country: str = "AU", prompt: str | None = None) -> dict:
    """Run the ChatGPT search actor (run-sync) for a single prompt. Returns
    {present, prompt, response_snippet, response, citations[{title,url,source}]}."""
    token = _load_apify_token()
    prompt = prompt or _default_prompt(keyword, country)
    url = f"{API}/acts/{CHATGPT_ACTOR}/run-sync-get-dataset-items?token={token}"
    # apify~chatgpt-search-scraper takes a single `queries` STRING (its input schema
    # lists only `queries` as required) and has no country parameter, so the locale
    # has to be carried in the prompt text itself.
    body = json.dumps({"queries": prompt}).encode("utf-8")
    # The actor's own defaultRunOptions.timeoutSecs is 1200, so a 300s client timeout
    # aborts perfectly healthy slow runs. Allow the full run, and retry once on a
    # transient network/timeout error before giving up (observed 2026-08-04: the same
    # keyword failed on the first call and returned 9 cited domains on the second).
    items = None
    last_err = None
    for attempt in (1, 2):
        req = urllib.request.Request(url, data=body, headers={"Content-Type": "application/json"})
        try:
            with urllib.request.urlopen(req, timeout=900) as resp:
                items = json.loads(resp.read())
            break
        except urllib.error.HTTPError as e:
            try:
                err = json.loads(e.read())
            except Exception:
                err = {}
            etype = err.get("error", {}).get("type")
            if etype == "full-permission-actor-not-approved":
                approval = err["error"]["data"]["approvalUrl"]
                sys.exit(f"ERROR: Approve the ChatGPT actor once at:\n  {approval}\nThen re-run.")
            if etype in ("record-or-token-not-found", "insufficient-permissions"):
                sys.exit(
                    f"ERROR: Apify {e.code} on {CHATGPT_ACTOR}: {err or e.reason}\n"
                    f"  Check the actor still exists before assuming a token/approval problem:\n"
                    f"    curl -s 'https://api.apify.com/v2/acts/{CHATGPT_ACTOR}?token=$APIFY_API_KEY'\n"
                    f"  A 404 'Actor was not found' means the actor was removed from the store and\n"
                    f"  CHATGPT_ACTOR needs repointing (this is what happened to tri_angle~gpt-search)."
                )
            sys.exit(f"ERROR: Apify HTTPError {e.code} on {CHATGPT_ACTOR}: {err or e.reason}")
        except (urllib.error.URLError, TimeoutError, json.JSONDecodeError) as e:
            last_err = e
            if attempt == 2:
                sys.exit(f"ERROR: {CHATGPT_ACTOR} unreachable after 2 attempts: {e}")
            print(f"  ChatGPT actor attempt {attempt} failed ({e}); retrying once…", file=sys.stderr)
    if items is None:
        sys.exit(f"ERROR: {CHATGPT_ACTOR} returned no data: {last_err}")

    item = items[0] if isinstance(items, list) and items else {}
    answer = (item.get("response") or item.get("answer") or item.get("text") or "").strip()
    cites = []
    seen = set()
    # apify~chatgpt-search-scraper returns citations under `sources`; the older actors
    # used `citations`. Accept either so the parser survives another actor swap.
    for c in (item.get("citations") or item.get("sources") or []):
        link = (c.get("url") or c.get("link") or "").strip()
        if not link or link in seen:
            continue
        seen.add(link)
        cites.append({
            "title": (c.get("title") or "").strip(),
            "url": link,
            "source": (c.get("source") or _root_domain(link)),
        })
    return {
        "present": bool(answer or cites),
        "prompt": prompt,
        "response": answer,
        "response_snippet": answer[:300] + ("…" if len(answer) > 300 else ""),
        "citations": cites,
    }


def _cited_domains_union(aio: dict | None, chatgpt: dict | None, ai_mode: dict | None = None) -> list[dict]:
    """Deduped union of AI-cited root domains, tagged by which engine(s) cited them."""
    engines: dict[str, set] = {}
    for label, block in (("AIO", aio), ("AI Mode", ai_mode)):
        if block and block.get("present"):
            for r in block.get("references") or []:
                d = (_root_domain(r.get("link", "")) or r.get("source") or "").lower()
                if d:
                    engines.setdefault(d, set()).add(label)
    if chatgpt and chatgpt.get("present"):
        for c in chatgpt.get("citations") or []:
            d = (c.get("source") or _root_domain(c.get("url", ""))).lower()
            if d:
                engines.setdefault(d, set()).add("ChatGPT")
    order = {"AIO": 0, "AI Mode": 1, "ChatGPT": 2}
    return [
        {"domain": d, "engines": sorted(engines[d], key=lambda e: order.get(e, 9))}
        for d in sorted(engines)
    ]


def _not_available(reason: str) -> dict:
    return {"present": False, "not_available": reason}


def to_markdown(keyword: str, country: str, aio: dict | None, chatgpt: dict | None,
                ai_mode: dict | None = None) -> str:
    out = [f'## AI Search Visibility: "{keyword}" ({country.upper()})', ""]

    out.append("**Google AI Overview**")
    out.append("")
    if aio and aio.get("not_available"):
        out.append(aio["not_available"])
    elif aio and aio.get("present"):
        out.append(aio["text"])
        if aio.get("references"):
            out += ["", "Sources:"]
            seen = set()
            for r in aio["references"]:
                u = r["link"].strip()
                if u and u not in seen:
                    seen.add(u)
                    out.append(f"- {u}")
    else:
        out.append("None present at capture time.")
    out.append("")

    out.append("**Google AI Mode**")
    out.append("")
    if ai_mode is None:
        out.append("Skipped.")
    elif ai_mode.get("not_available"):
        out.append(ai_mode["not_available"])
    elif ai_mode.get("present"):
        out.append(ai_mode["text"][:1200] + ("..." if len(ai_mode["text"]) > 1200 else ""))
        if ai_mode.get("references"):
            out += ["", "Sources:"] + [f"- {r['link']}" for r in ai_mode["references"]]
    else:
        out.append("None returned.")
    out.append("")

    out.append("**ChatGPT**")
    out.append("")
    if chatgpt is not None and chatgpt.get("not_available"):
        out.append(chatgpt["not_available"])
    elif chatgpt is None:
        out.append("Skipped (--skip-chatgpt).")
    elif chatgpt.get("present"):
        out.append(chatgpt["response_snippet"] or "(no answer text returned)")
        if chatgpt.get("citations"):
            out += ["", "Citations:"]
            for c in chatgpt["citations"]:
                title = f" ({c['title']})" if c.get("title") else ""
                out.append(f"- {c['url']}{title}")
    else:
        out.append("None returned.")
    out.append("")

    union = _cited_domains_union(aio, chatgpt, ai_mode)
    if union:
        out.append("**AI-cited domains (deduped union)**")
        out.append("")
        for d in union:
            out.append(f"- {d['domain']} ({' + '.join(d['engines'])})")
    return "\n".join(out)


def pick_provider(requested: str = "auto") -> str | None:
    if requested != "auto":
        return requested
    login, password = dfs.find_credentials()
    if login and password:
        return "dataforseo"
    if _load_apify_token(required=False):
        return "apify"
    return None


def capture_all(keyword: str, country: str = "au", prompt: str | None = None, provider: str = "auto",
                skip_aio: bool = False, skip_ai_mode: bool = False, skip_chatgpt: bool = False,
                serp_json: dict | None = None) -> dict:
    """Run every requested engine on the chosen provider. Never raises for a missing key."""
    prov = pick_provider(provider)
    before = dfs.TOTAL_COST
    na = _not_available("Not available (no DATAFORSEO key)")
    aio = ai_mode = chatgpt = None
    errors = []
    if prov == "dataforseo":
        def _run(fn, *a):
            try:
                return fn(*a)
            except dfs.DataForSEOError as e:
                errors.append(str(e))
                return _not_available(f"DataForSEO error: {e}")
        if skip_aio:
            aio = None
        elif serp_json and isinstance(serp_json.get("ai_overview"), dict):
            aio = serp_json["ai_overview"]  # already paid for in serp_outline_builder.py
        else:
            aio = _run(lambda: dfs.serp(keyword, country, depth=10)["ai_overview"])
        ai_mode = None if skip_ai_mode else _run(lambda: dfs.ai_mode(keyword, country))
        chatgpt = None if skip_chatgpt else _run(
            lambda: dfs.llm_response(prompt or _default_prompt(keyword, country), country))
    elif prov == "apify":
        aio = None if skip_aio else capture_aio(keyword, country)
        ai_mode = None if skip_ai_mode else _not_available("Not available (no DATAFORSEO key): AI Mode needs DataForSEO")
        chatgpt = None if skip_chatgpt else capture_chatgpt(keyword, country, prompt)
    else:
        aio = None if skip_aio else na
        ai_mode = None if skip_ai_mode else na
        chatgpt = None if skip_chatgpt else na
    return {"keyword": keyword, "country": country, "provider": prov or "none",
            "aio": aio, "ai_mode": ai_mode, "chatgpt": chatgpt,
            "ai_cited_domains": _cited_domains_union(aio, chatgpt, ai_mode),
            "errors": errors, "cost_usd": round(dfs.TOTAL_COST - before, 4)}


def main() -> None:
    p = argparse.ArgumentParser(description="Unified AI-search capture (Google AI Overview, AI Mode, "
                                            "ChatGPT) for a keyword. DataForSEO by default, Apify optional.")
    p.add_argument("keyword")
    p.add_argument("--country", default="au")
    p.add_argument("--prompt", default=None, help="override the ChatGPT prompt (default: derived from keyword)")
    p.add_argument("--provider", default="auto", choices=["auto", "dataforseo", "apify"])
    p.add_argument("--md", action="store_true", help="emit a markdown block for a brief")
    p.add_argument("--json", action="store_true", help="emit structured JSON")
    p.add_argument("--skip-chatgpt", action="store_true", help="drop the ChatGPT engine")
    p.add_argument("--skip-ai-mode", action="store_true", help="drop the Google AI Mode engine")
    p.add_argument("--skip-aio", action="store_true", help="drop the Google AI Overview engine")
    p.add_argument("--serp-json", default=None,
                   help="serp_outline_builder.py JSON: reuse its AI Overview instead of a second SERP call")
    a = p.parse_args()
    serp_json = None
    if a.serp_json:
        with open(a.serp_json, encoding="utf-8") as fh:
            serp_json = json.load(fh)

    res = capture_all(a.keyword, a.country, a.prompt, a.provider, a.skip_aio, a.skip_ai_mode, a.skip_chatgpt, serp_json)
    if a.json:
        print(json.dumps(res, indent=2, ensure_ascii=False))
    else:
        print(to_markdown(a.keyword, a.country, res["aio"], res["chatgpt"], res["ai_mode"]))
    print(f"[provider] {res['provider']}  [cost] DataForSEO ${res['cost_usd']:.4f}", file=sys.stderr)
    if res["errors"] and a.provider != "auto":
        sys.exit(2)


if __name__ == "__main__":
    main()
