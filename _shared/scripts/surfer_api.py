#!/usr/bin/env python3
"""
SurferSEO API helper - the primary way mos-content brief skills talk to Surfer.

Reads SURFERSEO_API_KEY (and the optional SURFER_WORKSPACE_ID) from the environment,
then from a .env found walking up from the current directory (normally the
MarketingOS brain root), so skills never depend on a shell that has already sourced
it. With no SURFER_WORKSPACE_ID, the first workspace on the account is used.

Usage:
  python3 surfer_api.py check                       # free auth smoke test
  python3 surfer_api.py locations [--grep australia]
  python3 surfer_api.py find    --main-keyword "project management software" [--days 30]
  python3 surfer_api.py create  --main-keyword "..." [--secondary "..." ...] \
                                [--location Australia] [--device mobile] \
                                [--target-word-count 1800] [--notes "..."] \
                                [--import-content-url https://...] [--client acme]
  python3 surfer_api.py wait        --id 12345 [--timeout 600]
  python3 surfer_api.py permalink   --id 12345
  python3 surfer_api.py guidelines  --id 12345
  python3 surfer_api.py ai-facts    --id 12345
  python3 surfer_api.py outline     --id 12345
  python3 surfer_api.py brief-block --main-keyword "..." --client acme [--secondary ...] ...

All commands print JSON to stdout, except `outline` (markdown) and `brief-block`
(the ready-to-paste markdown block for the brief). Non-zero exit on credential
errors. `brief-block` NEVER exits non-zero on a Surfer-side failure — it emits a
placeholder block so the brief still ships.

COST: only `create` (and `brief-block`, which wraps it) spends anything — one
Content Editor credit per successful create, the same as making it by hand in the
UI. Every read below is free. Two guards keep it at one: an Idempotency-Key on the
create, and a `find`-before-create reuse check.

There is NO folder API in Surfer v1 or v2 (re-verified against the live spec
2026-07-27). Folder assignment stays a manual drag in the UI; the --notes stamp is
what makes the new editor findable in the list.
"""
import argparse
import datetime as _dt
import hashlib
import json
import os
import sys
import time
import urllib.error
import urllib.parse
import urllib.request

BASE = "https://app.surferseo.com"

# Surfer sits behind Cloudflare, which intermittently 1010-bans non-browser
# user agents. Always send a browser UA.
USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36"
)


class SurferError(Exception):
    """HTTP-level failure carrying the status code so callers can branch on it."""

    def __init__(self, code, body, path):
        self.code = code
        self.body = body
        self.path = path
        super().__init__(f"Surfer API {code} on {path}\n{body}")


def _env(name: str) -> str:
    """Return `name` from the environment, else from a .env walked up from CWD, else ""."""
    val = os.environ.get(name)
    if val and val.strip():
        return val.strip()
    here = os.path.abspath(os.getcwd())
    while True:
        path = os.path.join(here, ".env")
        if os.path.isfile(path):
            with open(path, encoding="utf-8") as fh:
                for line in fh:
                    # .strip() guards against CRLF .env files: a trailing \r
                    # corrupts the HTTP header.
                    line = line.strip()
                    if line.startswith(name + "="):
                        return line.split("=", 1)[1].strip().strip('"').strip("'")
        parent = os.path.dirname(here)
        if parent == here:
            return ""
        here = parent


def _load_api_key() -> str:
    key = _env("SURFERSEO_API_KEY")
    if key:
        return key
    sys.exit(
        "ERROR: SURFERSEO_API_KEY not found in env or any .env "
        "(searched up from the current directory). Add it to the brain's .env or export it."
    )


_WORKSPACE_CACHE = []


def _workspace() -> str:
    """SURFER_WORKSPACE_ID when set, else the first workspace on the account."""
    if _WORKSPACE_CACHE:
        return _WORKSPACE_CACHE[0]
    ws = _env("SURFER_WORKSPACE_ID")
    if not ws:
        _, out = _request("/api/v2/workspaces")
        items = out if isinstance(out, list) else out.get("data", [])
        if not items or "id" not in items[0]:
            raise SurferError(0, "no workspace found on this Surfer account; "
                                 "set SURFER_WORKSPACE_ID", "/api/v2/workspaces")
        ws = str(items[0]["id"])
    _WORKSPACE_CACHE.append(ws)
    return ws


def _request(path, method="GET", body=None, accept="application/json",
             extra_headers=None, timeout=60, auth=True):
    """Return (status, parsed_body). Raises SurferError on 4xx/5xx."""
    url = f"{BASE}{path}"
    headers = {"Accept": accept, "User-Agent": USER_AGENT}
    if auth:
        headers["API-KEY"] = _load_api_key()
    if extra_headers:
        headers.update(extra_headers)
    data = None
    if body is not None:
        data = json.dumps(body).encode("utf-8")
        headers["Content-Type"] = "application/json"
    req = urllib.request.Request(url, data=data, headers=headers, method=method)
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            raw = resp.read().decode("utf-8", "replace")
            if accept.startswith("application/json"):
                return resp.status, (json.loads(raw) if raw.strip() else {})
            return resp.status, raw
    except urllib.error.HTTPError as e:
        raise SurferError(e.code, e.read().decode("utf-8", "replace"), path) from e
    except Exception as e:  # noqa: BLE001
        raise SurferError(0, str(e), path) from e


# ---------------------------------------------------------------------------
# Commands
# ---------------------------------------------------------------------------
def cmd_check():
    """Free auth smoke test.

    Deliberately hits /api/v2/workspaces, NOT /api/v1/locations — that one is
    public and returns 200 with a bogus key or no key at all, so it validates
    nothing. A 401 here means the key is not resolving on Surfer's backend
    (historically fixed only by Surfer support regenerating it server-side);
    a 403 means the key is fine but the plan or billing is not.
    """
    _, out = _request("/api/v2/workspaces")
    return out


def cmd_locations(grep=None):
    _, out = _request("/api/v1/locations", auth=False)
    if grep:
        needle = grep.lower()
        items = out if isinstance(out, list) else out.get("data", out)
        if isinstance(items, list):
            return [i for i in items
                    if needle in json.dumps(i).lower()]
    return out


def _iter_editors(days):
    """Yield content editors created in the last `days` days (max 90 per the API)."""
    after = (_dt.datetime.now(_dt.timezone.utc)
             - _dt.timedelta(days=min(days, 90))).strftime("%Y-%m-%dT%H:%M:%SZ")
    page = 1
    while True:
        qs = urllib.parse.urlencode({
            "page": page,
            "page_size": 100,
            "sort": "inserted_at",
            "order": "desc",
            "filter[inserted_after]": after,
        })
        _, out = _request(f"/api/v2/workspaces/{_workspace()}/content_editors?{qs}")
        rows = out.get("data", [])
        for row in rows:
            yield row
        meta = out.get("meta", {})
        if page >= meta.get("total_pages", 1) or not rows:
            return
        page += 1


def cmd_find(main_keyword, days=30, client=None):
    """Credit guard: find an existing editor for this keyword before spending one.

    The workspace is shared across every client, and the same keyword genuinely
    recurs across clients — so a keyword match alone is NOT enough to reuse.
    Handing a brief the wrong client's Surfer editor is far worse than spending
    one credit, so reuse requires the `notes` stamp to name the same client.

    Returns (editor_or_None, unclaimed_matches). `unclaimed_matches` are
    same-keyword editors we deliberately refused to reuse — surfaced as a
    warning so a genuine duplicate is still visible to the operator.
    """
    needle = main_keyword.strip().lower()
    client_tag = (client or "").strip().lower()
    unclaimed = []
    for row in _iter_editors(days):
        if (row.get("main_keyword") or "").strip().lower() != needle:
            continue
        # The LIST endpoint returns ContentEditorSummary, which does NOT carry
        # `notes` — only the per-editor detail (ContentEditorDetail) does. Reading
        # notes off the list row always yields None, which silently defeats the
        # whole reuse guard, so re-fetch the detail for keyword matches. Matches
        # are rare and detail reads are free.
        try:
            row = cmd_get(row["id"])
        except SurferError:
            pass  # fall back to the summary row; it just won't match on notes
        notes = (row.get("notes") or "").lower()
        if client_tag and notes and client_tag in notes:
            return row, unclaimed
        unclaimed.append(row)
    return None, unclaimed


def _idempotency_key(client, main_keyword):
    seed = f"{client or ''}|{main_keyword}|{_dt.date.today().isoformat()}"
    return hashlib.sha256(seed.encode("utf-8")).hexdigest()[:40]


def cmd_create(main_keyword, secondary=None, location="Australia", device="mobile",
               target_word_count=None, notes=None, import_content_url=None,
               client=None):
    payload = {"main_keyword": main_keyword}
    if secondary:
        # Surfer caps at 19 secondary keywords (20 total including the main one).
        payload["secondary_keywords"] = list(secondary)[:19]
    if location:
        payload["location"] = location
    if device:
        payload["device"] = device
    if target_word_count:
        payload["target_word_count"] = int(target_word_count)
    if notes:
        payload["notes"] = notes
    if import_content_url:
        payload["import_content_url"] = import_content_url
    _, out = _request(
        f"/api/v2/workspaces/{_workspace()}/content_editors",
        method="POST",
        body=payload,
        extra_headers={"Idempotency-Key": _idempotency_key(client, main_keyword)},
    )
    return out


def cmd_get(editor_id):
    _, out = _request(f"/api/v2/workspaces/{_workspace()}/content_editors/{editor_id}")
    return out


def cmd_wait(editor_id, timeout=600, interval=5, need_ai=False):
    """Poll until the editor is usable. Returns the editor object.

    The guidelines sub-endpoints 409 until state == completed, so this gate is
    mandatory before any harvest.
    """
    deadline = time.time() + timeout
    editor = {}
    while time.time() < deadline:
        editor = cmd_get(editor_id)
        state = editor.get("state")
        if state == "failed":
            raise SurferError(0, f"Content Editor {editor_id} failed: "
                                 f"{json.dumps(editor.get('error'))}", "wait")
        if state == "completed":
            seo = (editor.get("seo_guidelines") or {}).get("status")
            ai = (editor.get("ai_search_guidelines") or {}).get("status")
            if seo == "completed" and (not need_ai or ai in ("completed", "failed")):
                return editor
        time.sleep(interval)
    raise SurferError(0, f"Timed out after {timeout}s waiting for editor "
                         f"{editor_id} (last state: {editor.get('state')})", "wait")


def cmd_permalink(editor_id, kind="edit"):
    editor = cmd_get(editor_id)
    for link in editor.get("permalinks") or []:
        if link.get("type") == kind:
            return link.get("url")
    return None


def _sub(editor_id, leaf, accept="application/json"):
    path = (f"/api/v2/workspaces/{_workspace()}/content_editors/"
            f"{editor_id}/{leaf}")
    _, out = _request(path, accept=accept)
    return out


def cmd_guidelines(editor_id):
    """Fetch the four sub-blocks, not the parent — the parent response is large."""
    return {
        "structure": _sub(editor_id, "seo_guidelines/structure"),
        "terms": _sub(editor_id, "seo_guidelines/terms").get("data", []),
        "topics_and_questions": _sub(
            editor_id, "seo_guidelines/topics_and_questions").get("data", []),
        "competitors": _sub(editor_id, "seo_guidelines/competitors").get("data", []),
    }


def cmd_ai_facts(editor_id):
    return _sub(editor_id, "ai_search_guidelines/facts")


def cmd_outline(editor_id):
    return _sub(editor_id, "outline", accept="text/markdown")


# ---------------------------------------------------------------------------
# brief-block — the one command a SKILL.md needs
# ---------------------------------------------------------------------------
PLACEHOLDER = """**Surfer SEO**

- [Insert Surfer SEO link here — automated creation unavailable this run: {reason}]
"""


def _fmt_terms(terms, heading, limit=25):
    """Highest-weighted terms first, capped — Surfer routinely returns 60+ body
    terms, which is unreadable in a brief. The tail is reported as a count so the
    writer knows the full list lives in the editor."""
    picked = [t for t in terms
              if t.get("included") and bool(t.get("heading")) is heading
              and t.get("target_range")]
    picked.sort(key=lambda t: t["target_range"].get("max", 0), reverse=True)
    shown = picked[:limit]
    text = ", ".join(
        f"{t['item']} ({t['target_range']['min']}-{t['target_range']['max']})"
        for t in shown
    )
    if len(picked) > limit:
        text += f" — plus {len(picked) - limit} lower-weighted terms in the editor"
    return text


def _fmt_topics(topics, limit=15):
    picked = [t for t in topics if t.get("included")]
    out = [f"{t['item']} ({t.get('type', 'surfer').replace('_', ' ')})"
           for t in picked[:limit]]
    if len(picked) > limit:
        out.append(f"plus {len(picked) - limit} more in the editor")
    return out


def _fmt_ai_facts(payload, limit=8):
    lines = []
    for fact in (payload.get("data") or [])[:limit]:
        engines = sorted({e for src in fact.get("sources") or []
                          for e in src.get("cited_by") or []} - {"serp"})
        urls = [s["url"] for s in fact.get("sources") or [] if s.get("url")]
        tail = ""
        if engines:
            tail += f" [cited by: {', '.join(engines)}]"
        if urls:
            tail += f" — {urls[0]}"
        lines.append(f"- {fact['fact']}{tail}")
    return lines


def cmd_brief_block(args):
    """create (or reuse) → wait → harvest → emit the markdown block.

    Never raises. On any Surfer-side failure it returns the placeholder block so
    the brief still generates.
    """
    warnings = []
    try:
        if getattr(args, "editor_id", None):
            # Explicit re-harvest of a known editor — never creates, never charges.
            editor = cmd_get(args.editor_id)
            print(f"USING existing editor #{editor['id']} (--editor-id) — "
                  f"no credit spent.", file=sys.stderr)
            existing, unclaimed = editor, []
        else:
            existing, unclaimed = cmd_find(args.main_keyword,
                                           days=args.reuse_days,
                                           client=args.client)
        if unclaimed and not existing:
            ids = ", ".join(f"#{r['id']}" for r in unclaimed[:5])
            msg = (f"{len(unclaimed)} existing editor(s) share this keyword "
                   f"({ids}) but none is stamped for this client — created a new "
                   f"one rather than risk reusing another client's editor")
            warnings.append(msg)
            print(f"NOTE: {msg}.", file=sys.stderr)
        if existing and getattr(args, "editor_id", None):
            editor = existing
        elif existing:
            editor = existing
            print(f"REUSED existing editor #{editor['id']} "
                  f"(created {editor.get('inserted_at')}) — no credit spent.",
                  file=sys.stderr)
        elif getattr(args, "dry_run", False):
            payload = {
                "main_keyword": args.main_keyword,
                "secondary_keywords": list(args.secondary or [])[:19],
                "location": args.location, "device": args.device,
                "target_word_count": args.target_word_count,
                "notes": args.notes, "import_content_url": args.import_content_url,
            }
            print("DRY RUN — would create a Content Editor (1 credit) with:\n"
                  + json.dumps(payload, indent=2), file=sys.stderr)
            return ("**Surfer SEO**\n\n- [DRY RUN — no editor created, no credit spent]\n")
        else:
            editor = cmd_create(
                main_keyword=args.main_keyword,
                secondary=args.secondary,
                location=args.location,
                device=args.device,
                target_word_count=args.target_word_count,
                notes=args.notes,
                import_content_url=args.import_content_url,
                client=args.client,
            )
            print(f"CREATED editor #{editor['id']} — 1 Content Editor credit spent.",
                  file=sys.stderr)

        editor = cmd_wait(editor["id"], timeout=args.timeout, need_ai=not args.skip_ai)
        permalink = next((l["url"] for l in editor.get("permalinks") or []
                          if l.get("type") == "edit"), None)
        guidelines = cmd_guidelines(editor["id"])

        ai_lines = []
        if not args.skip_ai:
            try:
                ai_lines = _fmt_ai_facts(cmd_ai_facts(editor["id"]))
            except SurferError as e:
                warnings.append(f"AI Search facts unavailable ({e.code})")
    except SurferError as e:
        reason = f"HTTP {e.code}" if e.code else "request failed"
        if e.code == 422:
            reason = "Surfer credit quota exceeded"
        elif e.code == 401:
            reason = "Surfer key not authenticating"
        sys.stderr.write(f"WARNING: Surfer step failed — {e}\n")
        return PLACEHOLDER.format(reason=reason)
    except SystemExit:
        # _load_api_key() exits when the key is missing entirely.
        sys.stderr.write("WARNING: SURFERSEO_API_KEY not configured.\n")
        return PLACEHOLDER.format(reason="SURFERSEO_API_KEY not configured")

    structure = guidelines["structure"] or {}
    surfer_wc = structure.get("word_count")
    heading_terms = _fmt_terms(guidelines["terms"], heading=True,
                               limit=args.max_terms)
    body_terms = _fmt_terms(guidelines["terms"], heading=False,
                            limit=args.max_terms)
    topics = _fmt_topics(guidelines["topics_and_questions"],
                         limit=args.max_topics)

    out = ["**Surfer SEO**", ""]
    out.append(f"- Editor: {permalink or '[permalink not yet issued]'}")
    if surfer_wc:
        thruuu = (f" (Thruuu target: {args.target_word_count} — use the brief's "
                  f"figure where they disagree)" if args.target_word_count else "")
        out.append(f"- Surfer target word count: {int(surfer_wc)}{thruuu}")
    if heading_terms:
        out.append(f"- Terms to use in headings: {heading_terms}")
    if body_terms:
        out.append(f"- Terms to use in body copy: {body_terms}")
    if topics:
        out.append(f"- Topics Surfer expects: {'; '.join(topics)}")
    for w in warnings:
        out.append(f"- Note: {w}")

    if ai_lines:
        out += ["", "**Surfer AI Search facts** "
                    "(append under AI Search Visibility, do not replace the Apify capture)", ""]
        out += ai_lines

    return "\n".join(out) + "\n"


# ---------------------------------------------------------------------------
def main() -> None:
    p = argparse.ArgumentParser(description="SurferSEO API helper.")
    sub = p.add_subparsers(dest="cmd", required=True)

    sub.add_parser("check")

    sp = sub.add_parser("locations")
    sp.add_argument("--grep", default=None)

    sp = sub.add_parser("find")
    sp.add_argument("--main-keyword", required=True)
    sp.add_argument("--days", type=int, default=30)
    sp.add_argument("--client", default=None,
                    help="Required for a reuse match — the notes stamp must name "
                         "this client, since the workspace is shared across clients")

    def create_args(sp):
        sp.add_argument("--main-keyword", required=True)
        sp.add_argument("--secondary", action="append", default=[])
        sp.add_argument("--location", default="Australia")
        sp.add_argument("--device", default="mobile", choices=["mobile", "desktop"])
        sp.add_argument("--target-word-count", type=int, default=None)
        sp.add_argument("--notes", default=None,
                        help='Stamp shown in the Surfer list, e.g. '
                             '"Acme | October 2026 | project-management-software"')
        sp.add_argument("--import-content-url", default=None,
                        help="Optimisation briefs: pull the live page in and score it")
        sp.add_argument("--client", default=None,
                        help="Used only to salt the Idempotency-Key")

    create_args(sub.add_parser("create"))

    sp = sub.add_parser("wait")
    sp.add_argument("--id", required=True)
    sp.add_argument("--timeout", type=int, default=600)

    sp = sub.add_parser("permalink")
    sp.add_argument("--id", required=True)
    sp.add_argument("--kind", default="edit", choices=["edit", "comment"])

    for name in ("guidelines", "ai-facts", "outline"):
        sp = sub.add_parser(name)
        sp.add_argument("--id", required=True)

    sp = sub.add_parser("brief-block")
    create_args(sp)
    sp.add_argument("--timeout", type=int, default=600)
    sp.add_argument("--reuse-days", type=int, default=30)
    sp.add_argument("--editor-id", default=None,
                    help="Re-harvest a known editor instead of creating one. "
                         "Never spends a credit — use for reruns and testing.")
    sp.add_argument("--dry-run", action="store_true",
                    help="Show the create payload and exit without creating. "
                         "Spends nothing — use to sanity-check keywords first.")
    sp.add_argument("--skip-ai", action="store_true",
                    help="Skip the AI Search facts harvest (faster)")
    sp.add_argument("--max-terms", type=int, default=25,
                    help="Cap terms per group (Surfer returns 60+ body terms)")
    sp.add_argument("--max-topics", type=int, default=15)

    a = p.parse_args()

    try:
        if a.cmd == "check":
            out = cmd_check()
        elif a.cmd == "locations":
            out = cmd_locations(a.grep)
        elif a.cmd == "find":
            match, unclaimed = cmd_find(a.main_keyword, a.days, a.client)
            out = {
                "match": match,
                "unclaimed_same_keyword": [
                    {"id": r["id"], "inserted_at": r.get("inserted_at"),
                     "notes": r.get("notes")} for r in unclaimed
                ],
            }
        elif a.cmd == "create":
            out = cmd_create(
                main_keyword=a.main_keyword, secondary=a.secondary,
                location=a.location, device=a.device,
                target_word_count=a.target_word_count, notes=a.notes,
                import_content_url=a.import_content_url, client=a.client,
            )
        elif a.cmd == "wait":
            out = cmd_wait(a.id, timeout=a.timeout)
        elif a.cmd == "permalink":
            print(cmd_permalink(a.id, a.kind) or "")
            return
        elif a.cmd == "guidelines":
            out = cmd_guidelines(a.id)
        elif a.cmd == "ai-facts":
            out = cmd_ai_facts(a.id)
        elif a.cmd == "outline":
            print(cmd_outline(a.id))
            return
        elif a.cmd == "brief-block":
            print(cmd_brief_block(a))
            return
        else:  # pragma: no cover
            p.error(f"unknown command {a.cmd}")
    except SurferError as e:
        sys.exit(f"ERROR: {e}")

    print(json.dumps(out, indent=2))


if __name__ == "__main__":
    main()
