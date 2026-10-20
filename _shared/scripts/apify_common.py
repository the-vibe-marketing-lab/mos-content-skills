#!/usr/bin/env python3
"""
Canonical Apify token loader for mos-content scripts.

Why this exists: shell state does NOT persist between separate Bash tool calls, so a
script that only reads os.environ silently fails when the caller hasn't sourced .env in
the SAME command.

Resolution order (mirrors dataforseo_api.find_credentials / serp_research._thruuu_key):
  1. environment (APIFY_API_KEY, then APIFY_TOKEN)
  2. a .env walked up from CWD to filesystem root (normally the MarketingOS brain root)
No other locations are searched.
"""
import os

# .strip()/.strip(quotes) guards against a trailing \r from a CRLF .env (common on Windows).


def _load_apify_token(*, required: bool = True) -> str:
    """Resolve the Apify API token. Returns "" if not found and required=False;
    raises SystemExit if not found and required=True."""
    # 1. Environment
    tok = os.environ.get("APIFY_API_KEY") or os.environ.get("APIFY_TOKEN")
    if tok and tok.strip():
        return tok.strip()

    # 2. Walk up from CWD looking for a .env
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
            with open(path, encoding="utf-8") as fh:
                for line in fh:
                    line = line.strip()
                    if line.startswith("APIFY_API_KEY=") or line.startswith("APIFY_TOKEN="):
                        return line.split("=", 1)[1].strip().strip('"').strip("'")

    if required:
        raise SystemExit(
            "ERROR: Apify token not found in env (APIFY_API_KEY/APIFY_TOKEN), any .env "
            "(searched up from the current directory). "
            "Add APIFY_API_KEY to the brain's .env or export it."
        )
    return ""


if __name__ == "__main__":
    # Smoke test: print whether a token resolves (masked), never the full secret.
    t = _load_apify_token(required=False)
    print(f"apify token resolved: {bool(t)}" + (f" (…{t[-4:]})" if t else ""))
