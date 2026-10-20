# Content Brief Template (master shape)

> **This is the canonical master shape for mos-content briefs.** Write the working master in this shape (the three `##` guideline blocks, then `## Article Outline` and the outline), then build the final file with `../scripts/build_final_md.py`. Don't invent a different layout; populate this one. Labels and routing: `../content-output-routing.md`.

> ## HARD RULE: bold-label blocks in the master
>
> The three guideline blocks (**Brand Guidelines**, **Content Guidelines**, **Publishing Guidelines**) use plain Markdown in the master: `**Bold Label**` on its own line, a blank line, then the content (paragraphs and `- ` bullets). The builder turns them into tables; never hand-write pipe tables here.
>
> **The blank line after every bold label is mandatory.** Without it the builder cannot see where the label ends.
>
> This rule applies to every brief skill in the pack: `mos-content-brief` and `mos-content-best-x-for-y`.

## Research

*Use the following process below to ensure that your content is well-researched, and that you are covering the searcher's intent.*

## Brand Guidelines

**Customer Avatar**

Summarise the brain's audience file (`business/audience/*.md`, see `../brain-context.md`). If the brain has none, say what you assumed.

**Tone of Voice**

From the brain's voice file (`business/brand/voice.md` or similar): the attributes the copy must embody. This is the voice source `mos-content-writer` writes to.

**Restrictions and Guidelines**

Banned words, legal or regulatory wording, brand do's and don'ts (from `business/` and the brain's CLAUDE.md).

**USPs**

The brand's key differentiators, each with one line of proof.

**Author / Byline**

The ideal author profile + specific credentials for this topic (e.g. "Dr Sarah Chen, Board-Certified Endocrinologist, 12 yrs clinical"). EEAT signal: named, credentialled authors are cited by AI far more than anonymous content. Match expertise to the topic.

## Content Guidelines

**Focus keyword(s)**

Primary Keyword: … (vol/mo, KD, CPC, AU)

Secondary:
- Keyword …
- Keyword …

**New or Optimisation**

New / Optimisation

**Search intent**

One paragraph on the searcher persona + bullets of what they want to know.

**Content type**

informational long-form article / blog post · Listicle · How-to guide · News Article · Comparison / VS page · Landing page

**Buying journey**

Funnel: Awareness (TOFU) / Interest (MOFU) / Desire (MOFU) / Action (BOFU) / Loyalty / Advocacy. Awareness Stage: Unaware / Problem-Aware / Solution-Aware / Product-Aware / Most-Aware (+ one line of rationale). Market Sophistication: Stage 1-5 (+ rationale). The Schwartz lines are the source of truth for *where the copy opens*. Inferred from search intent (informational: Unaware or Problem-Aware; "best", "vs", "reviews": Solution-Aware; branded or "pricing": Product-Aware or Most-Aware), cross-checked against the audience file.

**Topical map**

*(If applicable)*

**Internal Linking**

- URL (anchor: "anchor text")
- URL (anchor: "anchor text")

**External Linking**

Only reputable sources (.gov, .org, academic, industry reports). Never link competitors.

**Target audience**

Primary: …

Secondary: …

**Word Count**

Target range (from the SERP word-count benchmark in `serp_outline_builder.py`).

**What is missing in the SERPs?**

- Gap 1
- Gap 2

**Previous Content Examples**

- https://example.com/path/ (description)

**Content Goals**

- SEO: …
- Lead-gen: …
- Education: …

**Featured Snippet**

Exists / doesn't + the opportunity.

**AI Search Visibility**

The live AI-search capture for the primary keyword via `../scripts/ai_search.py "<primary keyword>" --country <cc> --serp-json <serp.json> --md` (DataForSEO by default: the Google AI Overview from the SERP call already made, Google AI Mode, and a ChatGPT answer with web search; Apify is an optional extra used only when DataForSEO is not set). Paste the block verbatim: (1) the AI Overview text + `Sources:` URLs, (2) the AI Mode text + sources, (3) the ChatGPT snippet + `Citations:` URLs, (4) the deduped **AI-cited domains** union. Optionally append the "Only Cited by AI" theme diff (`ai_citation_themes.py`). Then add 1-2 lines of citability strategy targeting the cited-but-not-owned domains. "None present" for any engine is a valid result; with no key each reads `Not available (no DATAFORSEO key)`.

**Map Pack**

Whether a map pack shows (local-intent signal).

**Term Targets**

From `serp_outline_builder.py --terms-md` (or the `terms` list in its JSON): phrases the fetched top 10 use, with each phrase's usage range across the pages that use it, as dot points:

- `<term> (<min>-<max>, used by <n> pages)`

Fewer than 2 pages fetched: `Not available (fewer than 2 competitor pages fetched)`.

**Surfer SEO**

Optional extra. Only with a Surfer key: populated by `../scripts/surfer_api.py brief-block`: paste its stdout here verbatim. The block is dot points, never a table:

- Editor: `https://app.surferseo.com/drafts/s/<hash>` (the writer's share link)
- Surfer target word count: `<n>`: cross-check against the SERP benchmark target; where they disagree the brief's figure wins
- Terms to use in headings: `<term> (<min>-<max>)`, …
- Terms to use in body copy: `<term> (<min>-<max>)`, …
- Topics Surfer expects: `<topic> (<source>)`; …

If Surfer is unreachable the script emits an `[Insert Surfer SEO link here ...]` placeholder with the reason. Leave it in and flag it in the run summary. With no Surfer key at all, write `Not available (no SURFERSEO key)`. Never fabricate a Surfer link.

**Reminder:** Surfer has no folder API. After the brief generates, drag the new editor into the right folder in the Surfer UI: the `notes` stamp (`<Brand> | <Month YYYY> | <slug>`) is there to make it easy to find.

**Research Pages**

- URL (#position, ~word count)

## Publishing Guidelines

*Please use the following guidelines to ensure your page is as optimised as possible!*

**URL slug**

…

**Title tag (<60 characters)**

Title-case; every word capitalised.

**Meta description (<160 characters)**

Includes primary keyword + a reason to click.

**Additional publishing notes**

Brand constraints, CTA targets, spelling conventions, schema recommendations.

## Article Outline

*The content to publish is located below this line ↓*

# [Heading]

## [Subheading]

## [Subheading]

## [Subheading]

## [Subheading]

## [Subheading]
