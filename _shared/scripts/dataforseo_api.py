#!/usr/bin/env python3
"""
dataforseo_api — DataForSEO v3 REST helper for mos-content skills.

Why this exists: DataForSEO is the pack's one recommended data key. It is pay per
use (no subscription), and one client covers keyword volume, Labs keyword research,
the live Google SERP (with the AI Overview), Google AI Mode, ChatGPT answers and a
domain's ranked keywords. Endpoint paths and request shapes were checked against
docs.dataforseo.com on 2026-10-21.

Auth is HTTP Basic (login:password), NOT a bearer token. Credentials resolve in
the same order as apify_common._load_apify_token:
  1. environment (DATAFORSEO_LOGIN + DATAFORSEO_PASSWORD)
  2. an explicit .env passed by the caller (optional), then a .env walked up from
     CWD to filesystem root (normally the brain root). `export KEY=value` lines work.

This module is the ONE owner of DataForSEO HTTP, credentials and location codes in
the pack. Other scripts import it (by realpath, never a copy):
  find_credentials(env_file)      (login, password) or (None, None); never exits
  search_volume(keywords, country, login, password)
                                  {keyword: {volume, cpc, competition}}; raises
                                  DataForSEOError instead of exiting
The CLI and the other public functions exit with a message on failure.

Commands:
  balance                       account balance + whether Backlinks API is enabled
  summary   --target DOMAIN     profile totals (backlinks, refdomains, IPs, subnets)
  backlinks --target DOMAIN     the link rows (auto-paged)
  refdomains --target DOMAIN    referring-domain aggregates (auto-paged)
  anchors   --target DOMAIN     anchor-text distribution (auto-paged)
  networks  --target DOMAIN     referring subnet clusters (auto-paged)
  volume    --keywords "a,b"    Google Ads search volume, CPC and competition per keyword
  overview  --keywords "a,b"    Labs volume, CPC, competition, KD and intent (cheapest metrics call)
  related   --keyword K         Labs related keywords (volume, CPC, competition, KD)
  suggestions --keyword K       Labs keyword suggestions (long-tail and question variants)
  difficulty --keywords "a,b"   Labs bulk keyword difficulty (0-100)
  serp      --keyword K         live Google top 10: organic, AI Overview, People Also Ask
  ai-mode   --keyword K         Google AI Mode answer and its references
  llm       --prompt P          ChatGPT answer with web search and its citations
  ranked    --target DOMAIN     the keywords a domain ranks for (cannibalisation check)
  All keyword commands take --country (default au).

Stdlib only. Every command prints JSON to stdout so callers can pipe or cache.

Cost control: every response carries a `cost` field; this module accumulates it in
TOTAL_COST and the CLI prints the total to stderr so a run can never spend
silently.
"""
from __future__ import annotations

import argparse
import base64
import json
import os
import sys
import time
import urllib.error
import urllib.parse
import urllib.request

API_ROOT = "https://api.dataforseo.com/v3"

# .strip()/.strip(quotes) guards against a trailing \r from a CRLF .env (common
# on Windows) - an unstripped \r corrupts the Basic auth header and 401s.

# Accumulated API spend for this process, in USD.
TOTAL_COST = 0.0

# DataForSEO caps list endpoints at 1000 rows per request.
PAGE_SIZE = 1000
# Politeness delay between paged calls.
PAGE_DELAY = 0.3


class DataForSEOError(RuntimeError):
    """A DataForSEO call failed. Raised by the non-exiting helpers."""


def _env_candidates(env_file: str | None = None) -> list[str]:
    candidates = [env_file] if env_file else []
    here = os.path.abspath(os.getcwd())
    while True:
        candidates.append(os.path.join(here, ".env"))
        parent = os.path.dirname(here)
        if parent == here:
            break
        here = parent
    return candidates


def find_credentials(env_file: str | None = None) -> tuple[str | None, str | None]:
    """Resolve (login, password) without exiting; (None, None) when absent."""
    wanted = {"DATAFORSEO_LOGIN": os.environ.get("DATAFORSEO_LOGIN", "").strip(),
              "DATAFORSEO_PASSWORD": os.environ.get("DATAFORSEO_PASSWORD", "").strip()}
    if all(wanted.values()):
        return wanted["DATAFORSEO_LOGIN"], wanted["DATAFORSEO_PASSWORD"]
    for path in _env_candidates(env_file):
        if not os.path.isfile(path):
            continue
        with open(path, encoding="utf-8", errors="replace") as fh:
            for line in fh:
                line = line.strip()
                if line.startswith("export "):
                    line = line[len("export "):].lstrip()
                for key in wanted:
                    if not wanted[key] and line.startswith(key + "="):
                        wanted[key] = line.split("=", 1)[1].strip().strip('"').strip("'")
        if all(wanted.values()):
            return wanted["DATAFORSEO_LOGIN"], wanted["DATAFORSEO_PASSWORD"]
    return None, None


def _load_credentials(env_file: str | None = None) -> tuple[str, str]:
    """Resolve (login, password). Exits with an actionable message if absent."""
    login, password = find_credentials(env_file)
    if login and password:
        return login, password
    sys.exit(
        "ERROR: DATAFORSEO_LOGIN / DATAFORSEO_PASSWORD not found in env or any .env "
        "(searched up from the current directory). Add them to the brain's .env or export them."
    )


def _headers(login: str | None = None, password: str | None = None) -> dict:
    if not (login and password):
        login, password = _load_credentials()
    token = base64.b64encode(f"{login}:{password}".encode()).decode()
    return {
        "Authorization": f"Basic {token}",
        "Content-Type": "application/json",
    }


def _request_raising(path: str, payload=None, method: str = "POST", timeout: int = 180,
                     login: str | None = None, password: str | None = None) -> dict:
    """Call the API with a 429/5xx retry. Accumulates TOTAL_COST. Raises DataForSEOError."""
    global TOTAL_COST
    url = API_ROOT + path
    data = json.dumps(payload).encode() if payload is not None else None
    headers = _headers(login, password)
    last_err = None

    for attempt in range(4):
        req = urllib.request.Request(url, data=data, headers=headers, method=method)
        try:
            with urllib.request.urlopen(req, timeout=timeout) as resp:
                body = json.loads(resp.read().decode())
            TOTAL_COST += float(body.get("cost") or 0.0)
            if body.get("status_code") not in (20000, None):
                raise DataForSEOError(
                    f"DataForSEO {path} returned status "
                    f"{body.get('status_code')}: {body.get('status_message')}"
                )
            return body
        except urllib.error.HTTPError as e:
            detail = e.read().decode("utf-8", "replace")[:400]
            last_err = f"{e.code} {detail}"
            if e.code in (429, 500, 502, 503, 504):
                time.sleep(2 * (attempt + 1))
                continue
            raise DataForSEOError(f"DataForSEO {path} HTTP {e.code}\n{detail}") from e
        except urllib.error.URLError as e:
            last_err = str(e)
            time.sleep(2 * (attempt + 1))

    raise DataForSEOError(f"DataForSEO {path} failed after retries: {last_err}")


def _request(path: str, payload=None, method: str = "POST", timeout: int = 180) -> dict:
    """CLI wrapper around _request_raising: exits with the message on failure."""
    try:
        return _request_raising(path, payload, method, timeout)
    except DataForSEOError as e:
        sys.exit(f"ERROR: {e}")


def _first_result(body: dict) -> dict:
    tasks = body.get("tasks") or []
    if not tasks:
        return {}
    result = tasks[0].get("result") or []
    return result[0] if result else {}


# --------------------------------------------------------------------------
# Public API
# --------------------------------------------------------------------------

def balance() -> dict:
    body = _request("/appendix/user_data", method="GET")
    res = _first_result(body)
    price = res.get("price") or {}
    return {
        "balance_usd": (res.get("money") or {}).get("balance"),
        "backlinks_api_enabled": bool(price.get("backlinks")),
        "labs_api_enabled": bool((price.get("dataforseo_labs") or {}).get("google")),
    }


def summary(target: str, include_subdomains: bool = True) -> dict:
    body = _request(
        "/backlinks/summary/live",
        [{
            "target": target,
            "include_subdomains": include_subdomains,
            "backlinks_status_type": "live",
            "internal_list_limit": 10,
        }],
    )
    return _first_result(body)


def _paged(path: str, base_payload: dict, expected: int | None = None) -> list[dict]:
    """Page a list endpoint until exhausted. DataForSEO caps at 1000 rows/request."""
    items: list[dict] = []
    offset = 0
    while True:
        payload = dict(base_payload)
        payload["limit"] = PAGE_SIZE
        payload["offset"] = offset
        res = _first_result(_request(path, [payload]))
        batch = res.get("items") or []
        items.extend(batch)
        total = res.get("total_count")
        if len(batch) < PAGE_SIZE:
            break
        offset += PAGE_SIZE
        if total is not None and offset >= total:
            break
        if expected is not None and offset >= expected:
            break
        time.sleep(PAGE_DELAY)
    return items


def backlinks(target: str, include_subdomains: bool = True,
              mode: str = "as_is", expected: int | None = None) -> list[dict]:
    """Live backlinks. mode='as_is' returns every link; 'one_per_domain' dedupes."""
    return _paged(
        "/backlinks/backlinks/live",
        {
            "target": target,
            "include_subdomains": include_subdomains,
            "mode": mode,
            "backlinks_status_type": "live",
            "order_by": ["domain_from_rank,asc"],
        },
        expected,
    )


def refdomains(target: str, include_subdomains: bool = True,
               expected: int | None = None) -> list[dict]:
    return _paged(
        "/backlinks/referring_domains/live",
        {
            "target": target,
            "include_subdomains": include_subdomains,
            "backlinks_status_type": "live",
            "order_by": ["backlinks,desc"],
        },
        expected,
    )


def anchors(target: str, include_subdomains: bool = True,
            expected: int | None = None) -> list[dict]:
    return _paged(
        "/backlinks/anchors/live",
        {
            "target": target,
            "include_subdomains": include_subdomains,
            "backlinks_status_type": "live",
            "order_by": ["backlinks,desc"],
        },
        expected,
    )


def networks(target: str, include_subdomains: bool = True,
             expected: int | None = None) -> list[dict]:
    """Referring subnets: the link-network signal most backlink exports do not carry."""
    return _paged(
        "/backlinks/referring_networks/live",
        {
            "target": target,
            "include_subdomains": include_subdomains,
            "network_address_type": "subnet",
            "backlinks_status_type": "live",
            "order_by": ["backlinks,desc"],
        },
        expected,
    )


# Google Ads location codes for the markets the content skills usually serve.
LOCATION_CODES = {"au": 2036, "nz": 2554, "us": 2840, "uk": 2826, "gb": 2826, "ca": 2124,
                  "ie": 2372, "sg": 2702, "in": 2356, "za": 2710}


def location_code(country: str) -> int:
    """Google Ads location code for a 2-letter market. Raises DataForSEOError if unknown."""
    code = LOCATION_CODES.get(country.strip().lower())
    if code is None:
        raise DataForSEOError(f"no DataForSEO location code for country '{country}'. "
                              f"Known: {sorted(LOCATION_CODES)}")
    return code


def _volume_rows(keywords: list[str], country: str, login=None, password=None) -> list[dict]:
    body = _request_raising("/keywords_data/google_ads/search_volume/live",
                            [{"keywords": keywords, "location_code": location_code(country),
                              "language_code": "en"}], login=login, password=password)
    task = (body.get("tasks") or [{}])[0]
    if task.get("status_code") not in (20000, None):
        raise DataForSEOError(f"DataForSEO error {task.get('status_code')}: {task.get('status_message')}")
    return task.get("result") or []


def search_volume(keywords: list[str], country: str = "au",
                  login: str | None = None, password: str | None = None) -> dict:
    """Non-exiting volume lookup for callers: {keyword (lower): {volume, cpc, competition}}.
    Raises DataForSEOError on any API, network, credential or location failure."""
    if not (login and password):
        login, password = find_credentials()
        if not (login and password):
            raise DataForSEOError("no DATAFORSEO_LOGIN / DATAFORSEO_PASSWORD in env or any .env")
    try:
        rows = _volume_rows(keywords, country, login, password)
    except urllib.error.URLError as e:
        raise DataForSEOError(str(e)) from e
    return {(r.get("keyword") or "").lower(): {"volume": r.get("search_volume"), "cpc": r.get("cpc"),
                                                "competition": r.get("competition")}
            for r in rows}


def volume(keywords: list[str], country: str = "au") -> list[dict]:
    """Search volume, CPC and competition for up to 1000 keywords in one call (CLI: exits on error)."""
    try:
        rows = _volume_rows(keywords, country)
    except DataForSEOError as e:
        sys.exit(f"ERROR: {e}")
    return [{"keyword": r.get("keyword"), "volume": r.get("search_volume"), "cpc": r.get("cpc"),
             "competition": r.get("competition"), "competition_index": r.get("competition_index")}
            for r in rows]


# --------------------------------------------------------------------------
# Keyword research, SERP and AI answers (all non-exiting: raise DataForSEOError)
# --------------------------------------------------------------------------

def _creds(login=None, password=None) -> tuple[str, str]:
    if login and password:
        return login, password
    login, password = find_credentials()
    if not (login and password):
        raise DataForSEOError("Not available (no DATAFORSEO key): set DATAFORSEO_LOGIN and "
                              "DATAFORSEO_PASSWORD in the environment or the brain's .env")
    return login, password


def _task_results(path: str, task: dict, login=None, password=None, timeout: int = 180) -> list[dict]:
    """POST one task and return its result list. Raises on any task-level error."""
    login, password = _creds(login, password)
    body = _request_raising(path, [task], login=login, password=password, timeout=timeout)
    t = (body.get("tasks") or [{}])[0]
    if t.get("status_code") not in (20000, None):
        raise DataForSEOError(f"DataForSEO {path} task error {t.get('status_code')}: {t.get('status_message')}")
    return t.get("result") or []


def _all_items(results: list[dict]) -> list[dict]:
    """Collect items across every result element (Labs suggestions put seed data in result[0])."""
    out: list[dict] = []
    for r in results:
        out.extend(r.get("items") or [])
    return out


def _kw_row(keyword: str | None, info: dict | None, props: dict | None) -> dict:
    info, props = info or {}, props or {}
    return {"keyword": keyword, "volume": info.get("search_volume"), "cpc": info.get("cpc"),
            "competition": info.get("competition"), "competition_level": info.get("competition_level"),
            "kd": props.get("keyword_difficulty")}


def keyword_overview(keywords: list[str], country: str = "au", login=None, password=None) -> list[dict]:
    """Labs keyword overview: volume, CPC, competition, KD and main intent for up to 700 keywords
    in one call. The cheap default for keyword metrics (about US$0.01 a call in October 2026,
    against about US$0.09 for the Google Ads `volume` endpoint)."""
    items = _all_items(_task_results("/dataforseo_labs/google/keyword_overview/live", {
        "keywords": keywords, "location_code": location_code(country), "language_code": "en"},
        login, password))
    rows = []
    for it in items:
        row = _kw_row(it.get("keyword"), it.get("keyword_info"), it.get("keyword_properties"))
        row["intent"] = (it.get("search_intent_info") or {}).get("main_intent")
        rows.append(row)
    found = {(r["keyword"] or "").lower() for r in rows}
    rows += [{"keyword": k, "volume": None, "cpc": None, "competition": None, "competition_level": None,
              "kd": None, "intent": None, "note": "no data in DataForSEO Labs"}
             for k in keywords if k.lower() not in found]
    return rows


def related_keywords(keyword: str, country: str = "au", limit: int = 50, depth: int = 2,
                     login=None, password=None) -> list[dict]:
    """Labs related keywords ("searches related to" graph)."""
    items = _all_items(_task_results("/dataforseo_labs/google/related_keywords/live", {
        "keyword": keyword, "location_code": location_code(country), "language_code": "en",
        "depth": depth, "limit": limit}, login, password))
    rows = []
    for it in items:
        kd = it.get("keyword_data") or {}
        rows.append(_kw_row(kd.get("keyword"), kd.get("keyword_info"), kd.get("keyword_properties")))
    return rows


def keyword_suggestions(keyword: str, country: str = "au", limit: int = 50,
                        login=None, password=None) -> list[dict]:
    """Labs keyword suggestions: long-tail phrases containing the seed (question variants included)."""
    items = _all_items(_task_results("/dataforseo_labs/google/keyword_suggestions/live", {
        "keyword": keyword, "location_code": location_code(country), "language_code": "en",
        "limit": limit, "order_by": ["keyword_info.search_volume,desc"]}, login, password))
    return [_kw_row(it.get("keyword"), it.get("keyword_info"), it.get("keyword_properties")) for it in items]


def keyword_difficulty(keywords: list[str], country: str = "au", login=None, password=None) -> dict:
    """{keyword (lower): kd 0-100} from Labs bulk keyword difficulty."""
    items = _all_items(_task_results("/dataforseo_labs/google/bulk_keyword_difficulty/live", {
        "keywords": keywords, "location_code": location_code(country), "language_code": "en"},
        login, password))
    return {(it.get("keyword") or "").lower(): it.get("keyword_difficulty") for it in items}


def ranked_keywords(target: str, country: str = "au", limit: int = 100,
                    login=None, password=None) -> list[dict]:
    """Keywords a domain (or page URL) ranks for in organic search, highest volume first."""
    items = _all_items(_task_results("/dataforseo_labs/google/ranked_keywords/live", {
        "target": target, "location_code": location_code(country), "language_code": "en",
        "limit": limit, "item_types": ["organic"],
        "order_by": ["keyword_data.keyword_info.search_volume,desc"]}, login, password))
    rows = []
    for it in items:
        kd = it.get("keyword_data") or {}
        serp_item = (it.get("ranked_serp_element") or {}).get("serp_item") or {}
        rows.append({"keyword": kd.get("keyword"),
                     "volume": (kd.get("keyword_info") or {}).get("search_volume"),
                     "position": serp_item.get("rank_group"), "url": serp_item.get("url"),
                     "etv": serp_item.get("etv")})
    return rows


def _refs(refs) -> list[dict]:
    out, seen = [], set()
    for r in refs or []:
        url = (r.get("url") or "").strip()
        if not url or url in seen:
            continue
        seen.add(url)
        out.append({"link": url, "title": (r.get("title") or "").strip(),
                    "source": (r.get("domain") or r.get("source") or "").strip()})
    return out


def _ai_overview_block(item: dict) -> dict:
    """Normalise an ai_overview item to {present, text, references[{link, title, source}]}."""
    parts, refs = [], list(item.get("references") or [])
    if item.get("markdown"):
        parts.append(item["markdown"].strip())
    for el in item.get("items") or []:
        if not item.get("markdown"):
            txt = (el.get("markdown") or el.get("text") or "").strip()
            if txt:
                parts.append(txt)
        refs.extend(el.get("references") or [])
    text = "\n\n".join(p for p in parts if p)
    references = _refs(refs)
    return {"present": bool(text or references), "text": text, "references": references}


def serp(keyword: str, country: str = "au", depth: int = 10, ai_overview: bool = True,
         login=None, password=None) -> dict:
    """Live Google SERP (advanced): organic top N, AI Overview and People Also Ask questions."""
    task = {"keyword": keyword, "location_code": location_code(country), "language_code": "en",
            "depth": depth, "device": "desktop"}
    if ai_overview:
        task["load_async_ai_overview"] = True
    results = _task_results("/serp/google/organic/live/advanced", task, login, password)
    res = results[0] if results else {}
    organic, paa, aio = [], [], {"present": False, "text": "", "references": []}
    for it in res.get("items") or []:
        t = it.get("type")
        if t == "organic":
            organic.append({"position": it.get("rank_group"), "url": it.get("url"),
                            "title": it.get("title"), "domain": it.get("domain"),
                            "description": it.get("description")})
        elif t == "ai_overview":
            aio = _ai_overview_block(it)
        elif t == "people_also_ask":
            paa.extend((q.get("title") or "").strip() for q in it.get("items") or [] if q.get("title"))
    return {"keyword": keyword, "country": country.lower(), "item_types": res.get("item_types") or [],
            "organic": organic[:depth], "ai_overview": aio, "people_also_ask": paa,
            "featured_snippet": "featured_snippet" in (res.get("item_types") or [])}


def ai_mode(keyword: str, country: str = "au", login=None, password=None) -> dict:
    """Google AI Mode answer for the keyword: {present, text, references}."""
    results = _task_results("/serp/google/ai_mode/live/advanced", {
        "keyword": keyword, "location_code": location_code(country), "language_code": "en"},
        login, password)
    for r in results:
        for it in r.get("items") or []:
            if it.get("type") == "ai_overview":
                return _ai_overview_block(it)
    return {"present": False, "text": "", "references": []}


DEFAULT_LLM_MODEL = "gpt-4.1-mini"


def llm_response(prompt: str, country: str = "au", model: str = DEFAULT_LLM_MODEL,
                 login=None, password=None) -> dict:
    """ChatGPT answer with web search on: {present, prompt, response, citations[{title, url, source}]}."""
    task = {"user_prompt": prompt[:500], "model_name": model, "web_search": True,
            "web_search_country_iso_code": country.upper() if country.lower() != "uk" else "GB"}
    results = _task_results("/ai_optimization/chat_gpt/llm_responses/live", task, login, password,
                            timeout=180)
    texts, cites, seen = [], [], set()
    for r in results:
        for it in r.get("items") or []:
            if it.get("type") != "message":
                continue
            for sec in it.get("sections") or []:
                if sec.get("type") == "text" and sec.get("text"):
                    texts.append(sec["text"].strip())
                for a in sec.get("annotations") or []:
                    url = (a.get("url") or "").strip()
                    if url and url not in seen:
                        seen.add(url)
                        cites.append({"title": (a.get("title") or "").strip(), "url": url,
                                      "source": urllib.parse.urlparse(url).netloc.lower().removeprefix("www.")})
    answer = "\n\n".join(texts)
    return {"present": bool(answer or cites), "prompt": prompt, "response": answer,
            "response_snippet": answer[:300] + ("..." if len(answer) > 300 else ""),
            "citations": cites, "model": model}


def _cli(fn, *a, **k):
    try:
        return fn(*a, **k)
    except DataForSEOError as e:
        sys.exit(f"ERROR: {e}")


def main() -> None:
    ap = argparse.ArgumentParser(prog="dataforseo_api")
    sub = ap.add_subparsers(dest="cmd", required=True)

    sub.add_parser("balance")
    for name in ("summary", "backlinks", "refdomains", "anchors", "networks"):
        p = sub.add_parser(name)
        p.add_argument("--target", required=True)
        p.add_argument("--no-subdomains", action="store_true")
        if name == "backlinks":
            p.add_argument("--mode", default="as_is",
                           choices=["as_is", "one_per_domain", "one_per_anchor"])

    p = sub.add_parser("volume")
    p.add_argument("--keywords", required=True, help="comma-separated keywords")
    p.add_argument("--country", default="au")

    for name in ("related", "suggestions", "serp", "ai-mode"):
        p = sub.add_parser(name)
        p.add_argument("--keyword", required=True)
        p.add_argument("--country", default="au")
        if name in ("related", "suggestions"):
            p.add_argument("--limit", type=int, default=50)
        if name == "serp":
            p.add_argument("--depth", type=int, default=10)
            p.add_argument("--no-ai-overview", action="store_true",
                           help="skip the async AI Overview load (saves $0.002)")
    p = sub.add_parser("overview")
    p.add_argument("--keywords", required=True, help="comma-separated keywords (up to 700)")
    p.add_argument("--country", default="au")
    p = sub.add_parser("difficulty")
    p.add_argument("--keywords", required=True, help="comma-separated keywords")
    p.add_argument("--country", default="au")
    p = sub.add_parser("llm")
    p.add_argument("--prompt", required=True)
    p.add_argument("--country", default="au")
    p.add_argument("--model", default=DEFAULT_LLM_MODEL)
    p = sub.add_parser("ranked")
    p.add_argument("--target", required=True, help="domain (no https://) or full page URL")
    p.add_argument("--country", default="au")
    p.add_argument("--limit", type=int, default=100)

    args = ap.parse_args()
    subs = not getattr(args, "no_subdomains", False)

    if args.cmd == "balance":
        out = balance()
    elif args.cmd == "summary":
        out = summary(args.target, subs)
    elif args.cmd == "backlinks":
        out = backlinks(args.target, subs, args.mode)
    elif args.cmd == "refdomains":
        out = refdomains(args.target, subs)
    elif args.cmd == "volume":
        out = volume([k.strip() for k in args.keywords.split(",") if k.strip()], args.country)
    elif args.cmd == "overview":
        out = _cli(keyword_overview, [k.strip() for k in args.keywords.split(",") if k.strip()],
                   args.country)
    elif args.cmd == "related":
        out = _cli(related_keywords, args.keyword, args.country, args.limit)
    elif args.cmd == "suggestions":
        out = _cli(keyword_suggestions, args.keyword, args.country, args.limit)
    elif args.cmd == "difficulty":
        out = _cli(keyword_difficulty, [k.strip() for k in args.keywords.split(",") if k.strip()],
                   args.country)
    elif args.cmd == "serp":
        out = _cli(serp, args.keyword, args.country, args.depth, not args.no_ai_overview)
    elif args.cmd == "ai-mode":
        out = _cli(ai_mode, args.keyword, args.country)
    elif args.cmd == "llm":
        out = _cli(llm_response, args.prompt, args.country, args.model)
    elif args.cmd == "ranked":
        out = _cli(ranked_keywords, args.target, args.country, args.limit)
    elif args.cmd == "anchors":
        out = anchors(args.target, subs)
    else:
        out = networks(args.target, subs)

    print(json.dumps(out, indent=2, ensure_ascii=False))
    sys.stderr.write(f"[cost] ${TOTAL_COST:.4f}\n")


if __name__ == "__main__":
    main()
