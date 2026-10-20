# Brain context: where a mos-content skill finds the brand

Every mos-content skill works inside the MarketingOS brain the user is in. This file says how a skill finds that brain and reads the brand's voice, audience, offer, domain, sitemap and competitors from it. Skills point here instead of repeating the rules.

## 1. Find the brain root

```bash
BRAIN=$(git rev-parse --show-toplevel 2>/dev/null || pwd)
test -f "$BRAIN/.mos/config.yaml" && echo "MarketingOS brain: $BRAIN" || echo "Not a brain: $BRAIN"
```

- **A brain** has `.mos/config.yaml` at its git root. Read it first: `business_name`, `mode` (`in-house` or `agency`), `month_folder` (normally `MM-Mon`) and any declared routes.
- **Not a brain** (no `.mos/config.yaml`): the skill still runs. Use the git root (or the current folder) as the working root, ask the user for the brand facts listed in section 3, and suggest `mos onboard` once at the end. Never create a brain on the user's behalf.
- **Agency brains:** each client has its own brain. Run the skill inside that client's brain. If the user is in the agency's own brain and names a client, ask which brain to work in rather than writing client work into the agency brain.

## 2. Where the brand facts live

Read what exists. Never assume a folder or file is there, and never invent its contents.

| Fact | Look in (first match wins) |
|---|---|
| Business name, mode, market | `.mos/config.yaml`, then `CONTEXT.md` |
| Current focus and constraints | `CONTEXT.md`, `BRAIN.md`, the brain's `CLAUDE.md` / `AGENTS.md` |
| Brand and positioning | `business/brand/brand.md` |
| Voice and tone | `business/brand/voice.md`, then any `*voice*` or `*tone*` file under `business/` or `reference/` |
| Audience / customer avatar | `business/audience/*.md` |
| Offers, USPs, pricing | `business/offers/<offer>/offer.md`, `business/strategy/strategy.md` |
| Proof (results, testimonials, case studies) | `business/proof/` |
| Competitors | `business/competitors/main-competitors/competitors.md` |
| Restrictions (banned words, legal, regulatory) | the brain's `CLAUDE.md`, `business/brand/*.md`, `business/operations/` |
| Previous content | `content/` (dated topic folders) |
| Extra reference material | `reference/` when present (some brains keep brand files there) |

Glob before you read, for example `ls "$BRAIN"/business/brand/ "$BRAIN"/business/audience/ 2>/dev/null`. A brain's own `CLAUDE.md` can route these somewhere else; when it does, it wins.

## 3. Domain, sitemap and market

- **Domain:** from `business/brand/brand.md`, `CONTEXT.md` or `.mos/config.yaml`. If none names it, ask. A pre-launch brand may have no site: say so and skip the steps that need one (sitemap links, existing rankings).
- **Sitemap:** read the live `https://<domain>/sitemap.xml` (see `toolchain-sitemap.md`). Reuse a `*-sitemap-urls.md` file already in the brain if it is under 30 days old.
- **Country / market:** from `.mos/config.yaml` or `CONTEXT.md`; otherwise ask. Pass it to every data provider (`--country au` for Australia).

## 4. When facts are missing

Ask the user once, in one AskUserQuestion call, for everything the brief cannot do without: domain, voice (or a sample of writing they like), audience, and any hard restrictions. Offer "Skip, use defaults" on each. Record what you assumed in the deliverable so the writer can see it, for example `Tone of Voice: not documented in the brain; assumed plain, direct, Australian English`.

## 5. API keys

Data providers are optional, and none needs a subscription. **DataForSEO is the one recommended key** (pay per use): it covers keyword metrics, the live SERP, AI Overview, AI Mode, ChatGPT answers and the brand's own rankings. Competitor pages are fetched free with Scrapling and analysed locally. Every shared script resolves its key from (1) the environment, then (2) a `.env` found walking up from the current directory, which is normally the brain root. Nothing else is searched. Keep keys in the brain's `.env` (git-ignored) or export them in the shell.

| Provider | Variables | Used for |
|---|---|---|
| DataForSEO (recommended) | `DATAFORSEO_LOGIN`, `DATAFORSEO_PASSWORD` | keyword metrics, related keywords and questions, KD, top 10 SERP, AI Overview, AI Mode, ChatGPT answers, the brand's ranked keywords (`toolchain-dataforseo.md`) |
| Scrapling (free CLI, no key) | none | fetching the top 10 pages for headings, word counts and term targets (`toolchain-scrapling.md`) |
| Thruuu (optional extra) | `THRUUU_API_KEY` | SERP list and headings, only when DataForSEO is not set |
| Apify (optional extra) | `APIFY_API_KEY` (or `APIFY_TOKEN`) | AI Overview and ChatGPT capture, only when DataForSEO is not set |
| Surfer (optional extra) | `SURFERSEO_API_KEY`, optional `SURFER_WORKSPACE_ID` | a Content Editor link and Surfer's own term ranges, on top of the local term targets |
| Firecrawl (optional extra) | `FIRECRAWL_API_KEY` | page fetch after Scrapling, before WebFetch |

When a key is missing, the skill says which one, says what that step would have added, and carries on with the steps it can still run. A missing metric is written as `Not available (no <PROVIDER> key)`. Never estimate a number to fill the gap.

## 6. Resolving this pack's own files

Skills reference shared files as `../_shared/...` relative to their own folder. `setup.sh` links each skill folder into `~/.claude/skills/`, but not `_shared/`, so resolve the skill's real path first:

```bash
SKILL="$(cd "$(dirname "$(readlink -f ~/.claude/skills/<skill-name>/SKILL.md)")" && pwd)"
SHARED="$SKILL/../_shared"
```

`~/.claude/skills/_shared` is a different folder that belongs to another skill pack. Never read from it.
