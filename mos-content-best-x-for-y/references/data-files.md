# Data files

Two folders. The shortlist run is shared by every page it produces; each chosen page then gets
its own brief folder.

```
content/YYYY/MM-Mon/YYYY-MM-DD-<category-slug>-best-x-for-y/      shortlist run
├── shortlist.md            the ranked shortlist the user picked from, with gate reasons
└── research/
    ├── seeds.json          the user's answers to the ask-first questions
    ├── candidates.json     every candidate Y, tagged yours or discovered
    ├── keywords.txt        one keyword per line (input to bxy.py volume)
    ├── volume.json         bxy.py volume output
    ├── prompts.json        the buyer prompt per candidate Y
    ├── engines/            raw engine answers (ai_search.py or brand360.py output)
    ├── gate.json           the model's five-test results per Y
    └── gate-result.json    bxy.py gate output (the rule applied, ranked)

content/YYYY/MM-Mon/YYYY-MM-DD-<page-slug>/blog/brief/          one per chosen page
├── YYYY-MM-DD-<page-slug>-brief.md   THE deliverable
└── research/
    ├── entries.json        the candidate set and why each entry is in (or was cut)
    ├── criteria.md         approved criteria + methodology block
    ├── evidence.csv        one row per fact
    ├── snapshots/          the saved page text every quote is matched against
    ├── picks.json          Best for / Not for / criterion / evidence per entry
    └── serp.json, keywords.md, sitemap-links.md and other research notes
```

Use the date and month-folder rules in `$SKILL/../_shared/content-output-routing.md`; if the brain
declares a different content route, that wins for both folders.

## seeds.json

```json
{"asked_on": "2026-10-21", "skipped": false,
 "pages_in_mind": ["best CRM for small agencies"],
 "avatars": ["agency owner, 2 to 10 staff"],
 "avoid": ["enterprise"]}
```

An empty file with `"skipped": true` is fine.

## candidates.json

```json
[{"y": "small agencies", "title": "Best CRM for Small Agencies",
  "keyword": "best crm for small agencies",
  "prompt": "What's the best CRM for a small marketing agency?",
  "source": "yours"}]
```

`source` is `yours` (from seeds.json) or `discovered`.

## gate.json (written by the model, read by `bxy.py gate`)

```json
{"brand": "Acme", "pre_launch": false,
 "pages": [{
   "y": "small agencies", "title": "Best CRM for Small Agencies",
   "keyword": "best crm for small agencies", "source": "yours",
   "tests": {
     "offer":        {"pass": true,  "why": "sells a CRM"},
     "audience":     {"pass": true,  "why": "pricing page targets teams of 2 to 20"},
     "proof":        {"pass": true,  "why": "3 agency case studies on /customers"},
     "price":        {"pass": false, "why": "starts at $99/user, double the field"},
     "availability": {"pass": true,  "why": "self-serve signup, AU billing"}
   },
   "demand": {"volume": {"AU": 90, "US": 480}, "engines_checked": 3, "brand_named_by": 0}
 }]}
```

`bxy.py gate` marks the brand eligible only when all five tests are present and pass, and
never when `pre_launch` is true. It ranks pages by AI gap (engines checked minus engines that
named the brand), then total volume.

## evidence.csv

| Column | Rule |
|---|---|
| id | Unique, e.g. `E14` |
| entry | The option the fact is about (the brand included) |
| claim | What the fact is, e.g. `starting price` |
| value | The value as it appears, or `Not published` |
| source_url | The page it came from (for `Not published`: the main page checked) |
| snapshot_path | Path to the saved page text, relative to `research/` (empty for `Not published`) |
| captured_on | `YYYY-MM-DD`, within 90 days at ship |
| quote | Verbatim from the snapshot; any number in `value` must appear in it |

Save snapshots with `python3 "$SKILL/../_shared/scripts/fetch_page.py" <url> --text > research/snapshots/<entry>-<page>.txt`.

## picks.json

```json
{"brand": "Acme", "page_y": "small agencies",
 "best_overall": null,
 "entries": [
   {"position": 1, "name": "Beta", "is_brand": false,
    "best_for": "agencies that live in their inbox",
    "not_for": "teams that need client portals",
    "criterion": "time to set up for a team of one", "evidence": ["E3", "E4"]},
   {"position": 2, "name": "Acme", "is_brand": true,
    "best_for": "agencies that bill retainers",
    "not_for": "solo freelancers on a tight budget",
    "criterion": "price per seat", "evidence": ["E1", "E2"]}
 ]}
```

`best_overall`, when used: `{"entry": "Beta", "criterion": "...", "evidence": ["E3"]}`.
The brand may hold position 1 only when `best_overall` names it with a criterion and evidence.
