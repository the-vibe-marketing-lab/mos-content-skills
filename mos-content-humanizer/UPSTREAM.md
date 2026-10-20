# Upstream

| | |
|---|---|
| Source | https://github.com/blader/humanizer |
| Version | 3.1.0 |
| Commit | 8c307f367c91bd974002f10f2be2965d642c13df |
| License | MIT (Siqi Chen), copied to `LICENSE` |

`references/humanizer.md` is upstream's `SKILL.md`, byte for byte. Do not edit it here: put
MarketingOS rules in this skill's own `SKILL.md`, so an update stays a clean file replacement.

## Updating

```bash
python3 scripts/sync_upstream.py            # latest main
python3 scripts/sync_upstream.py --ref <sha-or-tag>
```

The script refreshes `references/humanizer.md` and `LICENSE` and rewrites the table above.
Read the diff before committing: everyone who installs mos-content-skills receives it.

## Other references (digests, not vendored copies)

| File | Source | Licence | Retrieved |
|---|---|---|---|
| `references/wikipedia-signs-of-ai-writing.md` | https://en.wikipedia.org/wiki/Wikipedia:Signs_of_AI_writing | CC BY-SA 4.0 | 2026-10-20 |
| `references/storyscope-narrative-tells.md` | https://arxiv.org/abs/2604.03136 · https://github.com/jenna-russell/storyscope (b82d935) | MIT (code) | 2026-10-20 |

Both are written in our own words for brand content and are not touched by
`sync_upstream.py`. The Wikipedia page changes often: re-read it every few months and update the
digest by hand when new web-relevant tells appear.
