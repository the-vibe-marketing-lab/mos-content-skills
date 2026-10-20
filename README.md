# mos-content-skills

Claude Code skills for SEO and GEO content: research-backed article briefs, honest "best X for Y" buyer's guides, and the article written from either one. Built for The Vibe Marketing Lab as a companion pack to the MarketingOS engine (`pipx install marketing-os`). Same `mos-*` naming, and it installs next to the engine's own skills in `~/.claude/skills/`.

Every skill runs inside a MarketingOS brain. It reads the brand's voice, audience and offers from the brain, and saves its output to the brain's `content/` folder.

## What's in here

| Skill | What it does |
|---|---|
| `mos-content-brief/` | One Markdown brief for an article. Keyword research and the live top 10 (DataForSEO), competitor headings, word counts and term targets (pages fetched free with Scrapling and analysed locally), rare primary-source stats the ranking pages don't cite, what AI Overviews, AI Mode and ChatGPT cite today, and internal links checked against the live sitemap. No subscription needed: a missing key is named in the brief and skipped, never guessed. |
| `mos-content-best-x-for-y/` | Buyer's guide briefs. Asks for your page ideas first, checks demand (search volume plus who ChatGPT, AI Mode and Perplexity recommend now), and runs an eligibility gate so the brand only appears where it is an honest pick. Every entry gets a sourced, dated "Best for" and "Not for". The brand is never #1 by default. A code check blocks a year in the title, a missing methodology block or AggregateRating schema before the brief ships. |
| `mos-content-writer/` | Writes the article from an approved brief from either skill above. Drafts each section in the brain's voice, then runs the humanizer, a linter, a word count and a checklist, and hands over to `mos-proofread`. On buyer's guides it keeps the brief's ranking and only uses the captured evidence for competitor facts. |
| `mos-content-humanizer/` | Rewrites AI-sounding copy without changing what it says, at sentence, page and structure level. Vendors [blader/humanizer](https://github.com/blader/humanizer) (MIT) plus digests of Wikipedia's "Signs of AI writing" and the StoryScope research. Runs automatically inside the other three skills. |

The chain is: `mos-content-brief` or `mos-content-best-x-for-y`, then `mos-content-writer`, then `mos-proofread`.

## `_shared/`

Not a skill, never linked into `~/.claude/skills/`. Every skill in the pack reads from it:

- `brain-context.md`: how a skill finds the brain root, its voice and audience files, and API keys.
- `content-output-routing.md`: where briefs, articles and research files go.
- `templates/content-brief-template.md`: the brief's shape.
- `toolchain-*.md`: command references for DataForSEO, Scrapling and the sitemap check, plus the optional Thruuu and Surfer extras.
- `scripts/`: the provider clients, `serp_research.py` (SERP fetch plus local heading, word count, theme and term extraction) and `build_final_md.py`, which builds the one brief file.

Because `~/.claude/skills/_shared` can belong to another pack, each skill resolves its own real folder first and reads `$SKILL/../_shared/...`, never a bare `../_shared`.

## API keys

**One recommended key: DataForSEO** (`DATAFORSEO_LOGIN` + `DATAFORSEO_PASSWORD`). It is pay per use, with no subscription: keyword metrics, related keywords and questions, the live Google top 10 with its AI Overview, Google AI Mode, ChatGPT answers and the brand's own rankings all come from it. A full article brief costs roughly US$0.10 at October 2026 prices, and every script reports what each call cost. Sign up at dataforseo.com and use the API password from the dashboard.

**One recommended free tool: Scrapling** (`uv tool install "scrapling[shell]"`). It fetches the ranking pages so headings, word counts and term targets are extracted locally for nothing.

Keys are read from the environment, then from a `.env` found walking up from the current folder (normally the brain's root).

Optional extras, used only when their key is set: `THRUUU_API_KEY`, `SURFERSEO_API_KEY` (+ optional `SURFER_WORKSPACE_ID`), `APIFY_API_KEY` (or `APIFY_TOKEN`), `FIRECRAWL_API_KEY`. None of them is needed for a complete brief.

With no key at all, the skills still run on WebSearch, WebFetch and free page fetches, and every missing number reads "Not available (no X key)".

## Install

```bash
git clone https://github.com/the-vibe-marketing-lab/mos-content-skills.git ~/Desktop/mos-content-skills
cd ~/Desktop/mos-content-skills
bash setup.sh            # or: bash setup.sh --dry-run
```

`setup.sh` links each top-level skill folder into `~/.claude/skills/` (a junction on Windows). Restart Claude Code to pick them up.

## Follow-ups

- `mos-geo-vs-content` (one-vs-one pages) is planned in `mos-geo-skills`, not released yet.
- `mos-content-brief` overlaps with the engine's `mos-copy-brief` on "content brief" triggers. One of them should own that phrase.
- No optimisation-brief skill yet: rewrites of live pages aren't covered.
