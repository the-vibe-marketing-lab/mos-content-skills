---
name: mos-content-humanizer
description: "MarketingOS humanizer: rewrites AI-sounding copy inside a MarketingOS brain so it reads as human-written in the brain's own voice, without changing what it says. Uses the vendored Humanizer pattern set (blader/humanizer, MIT) plus digests of Wikipedia's 'Signs of AI writing' and the StoryScope narrative-tells research, at sentence, page and structure level: not-X-but-Y contrasts, one-line closers, staged openers, forced triads, dashes, inflation, sales language, stock AI words, decorative bold. Runs automatically as a mandatory step inside mos-content-writer (on the full draft) and inside mos-content-brief and mos-content-best-x-for-y (on the copy each brief drafts). Triggers: 'humanize this', 'humanize this content', 'make this sound human', 'remove the AI tells', 'run the humanizer'. NOT FOR audit-only questions ('is this AI slop?', 'is this ready to ship?'): those go to mos-proofread. NOT FOR general text outside a MarketingOS brain (use humanizer)."
---

# mos-content-humanizer

A MarketingOS wrapper around [Humanizer](https://github.com/blader/humanizer). The pattern
catalogue and method are upstream's, kept verbatim in
[`references/humanizer.md`](references/humanizer.md). This page only adds what brand content
needs on top of it.

## Before you start: paths

This skill reads one shared file from the pack's `_shared/` folder, which sits next to this skill
folder in the mos-content-skills repo. `setup.sh` links only the skill folders into
`~/.claude/skills/`, so resolve the real path first and use `$SKILL/../_shared/...`:

```bash
SKILL="$(cd "$(dirname "$(readlink -f ~/.claude/skills/mos-content-humanizer/SKILL.md)")" && pwd)"
```

`~/.claude/skills/_shared` is a different folder from another pack. Never read from it. When a
calling skill runs this one in embedded mode, it resolves this skill's folder the same way.

## Find the brain first

The working context is the MarketingOS brain the user is in. Resolve its root, brand voice and
audience the way `$SKILL/../_shared/brain-context.md` describes: the git
root (it holds `.mos/config.yaml` when it is a brain), then `.mos/config.yaml`, the brain's
`CLAUDE.md`, and its `business/` and `reference/` folders when they exist. Never assume a folder
is there. When no voice file turns up and a brand is in play, ask the user for a writing sample
or a short description of the voice before rewriting.

## Read before editing

Three references, three levels. Read all three in full on every run:

1. [`references/humanizer.md`](references/humanizer.md): **sentence level.** The patterns and
   the method. This drives the rewrite.
2. [`references/wikipedia-signs-of-ai-writing.md`](references/wikipedia-signs-of-ai-writing.md):
   **page level.** The regress-to-the-mean test ("could this sentence sit unchanged on a
   competitor's page?") plus web-only checks: chatbot citation residue, `utm_source=chatgpt.com`,
   placeholders, sources that do not hold up, Markdown leaking into the CMS.
3. [`references/storyscope-narrative-tells.md`](references/storyscope-narrative-tells.md):
   **structure level.** How AI builds a piece (spelt-out lessons, tidy single-track sections,
   flat even pacing, Claude's own fingerprint). Word-level cleanup cannot fix these; restructure.

Work top-down when rewriting: structure first (3), then page (2), then sentences (1), so you do
not polish sentences you are about to cut.

Pinned version and update steps: [`UPSTREAM.md`](UPSTREAM.md).

## Precedence

Humanizer is written for any prose. Brand content has contracts it must not break, so these win
over the upstream patterns wherever they collide:

1. **The brain's own rules.** The brain's `CLAUDE.md`, `.mos/config.yaml` and whatever voice or
   tone file lives in its `business/` or `reference/` folder. That voice is the "writing sample"
   upstream's *Voice* section talks about; match it.
2. **The brief.** Never rewrite headings the brief dictates, the focus keyword and its
   exact-match variants, internal and external links (anchor text included), cited figures, FAQ
   questions, CTAs, or the brief tables at the top of a draft. In a brief, never touch keyword
   data, figures, SERP-dictated headings, URLs or anchors; humanize only the copy the brief
   drafts (title tag, meta description, sample intro, FAQ answers, CTA), and recheck character
   limits afterwards.
3. **Compliance text stays verbatim.** Disclaimers, regulatory wording, claims a legal or
   compliance review approved, and any banned-claims list the brain keeps.
4. **House formatting.** Australian English unless the brain says otherwise; `[IMAGE: ...]`
   markers kept; the article's heading style as the writing skill sets it. Upstream's bold,
   title-case heading and curly-quote patterns apply to body prose only, never to structure the
   brief or house style requires.
5. **Upstream patterns.** Everything else. Zero em dashes is already the house rule; keep it.

Upstream's "do not add a fact" rule is absolute here: no invented stats, names, dates, quotes or
brand claims. If a sentence needs a detail you lack, simplify it or flag
`[NEEDS BRAND DETAIL: ...]`.

## Modes

- **Embedded (default when mos-content-brief, mos-content-best-x-for-y or mos-content-writer
  calls this).** Input is a draft file. Edit body prose in place per upstream *File mode*, return
  a 3 to 6 line summary of the patterns removed. No draft or notes output.
- **Direct (the user pastes or names copy).** Upstream *Pasted text* mode: draft, remaining
  patterns, final rewrite. Load the brain's voice first when a brand is in play.

## After a pass

Re-run the deterministic linter from the `mos-copywriting` skill so a rewrite never ships a new
tell:

```bash
bun ~/.claude/skills/mos-copywriting/Tools/lint-copy.ts <file> --surface generic --body-only
```

Exit 1 means fix and re-run. If `bun` or the linter is not installed, say so and check em dashes,
ellipses, stacked triads, hype words and filler phrases by eye. The linter and Humanizer overlap
on purpose: the linter catches mechanical tells in code, Humanizer handles the structural ones
(staging, closers, triads at paragraph scale, wrong-reader replies) that need judgement.

For a full pre-publish review after humanizing (strategy, structure, clarity, cut, voice,
mechanics), hand the draft to `mos-proofread`.
