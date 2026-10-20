# Writing rules

The SEO, GEO and structure rules for articles written by mos-content-writer. Prose craft,
brand voice, punctuation and spelling are not repeated here. They come from two places:

- **The brain's voice file**, found through `$SKILL/../_shared/brain-context.md` (`$SKILL` is the writer's resolved folder). It always wins
  on tone and locale.
- **The `mos-copywriting` skill**, especially `references/prose-craft-rules.md` (sentence
  craft, punctuation, the em dash ban) and its body-copy frameworks
  (`sugarman-slippery-slide.md`, `ogilvy-body-copy.md`, `halbert-principles.md`).

This file holds what is this skill's own domain: search optimisation, AI-citation
structure, EEAT, internal linking, tables, brand positioning and CTA placement.

One article-output rule: **no horizontal rules.** Never use `---` or `<hr>` in an article.
Use the heading hierarchy and white space instead.

## Awareness stage

Open each section where the reader is, using the brief's awareness stage:

- **Unaware or problem aware:** lead with the situation or the problem in the reader's words.
- **Solution aware:** lead with how the approach works and why it beats the alternatives.
- **Product aware or most aware:** lead with proof, specifics and the next step.

Respect market sophistication. In a tired market (stage 4 or 5), a bare promise is dead:
lead with the mechanism or the identity angle.

## SEO integration

- **Primary keyword:** in the H1 (exact or close variant), in the first 100 words, and in
  2 or more H2s where it reads naturally.
- **Secondary keywords:** map each to its most relevant section; each appears at least once.
- **Never keyword stuff.** If it sounds wrong read aloud, rewrite it.
- **Internal links:** woven into sentences, never listed.
  - Right: "Teams using [a content calendar](URL) ship more consistently."
  - Wrong: "Related: https://example.com/content-calendar"
- **External links:** only to reputable sources (government, standards bodies, academic
  work, recognised publications, official documentation). Never to direct competitors in a
  standard article.
- **Meta description:** under 160 characters, includes the primary keyword, gives a reason
  to click.
- **Image alt text:** describes the image; a keyword only where natural.
- **URL slugs:** short, hyphenated, keyword-relevant.

## GEO (AI citation rules)

Reference: Daniel Shashko's sentence-level citation study (42,971 citations, 520 queries,
6 platforms).

### Sentence level

- **Key claims: 6 to 15 words, one fact per sentence, declarative.** Single-fact sentences
  are cited far more often than compound ones.
- **Citable claims stay under 17 words.**
- **Front-load key claims in each section's first 3 paragraphs.** Most citations come from
  the top half of a page.
- **Use H2 and H3 for topic sections.** Structured pages are cited more.
- **Lists and tables for enumerations.**
- **Answer first, then context.**

### Section level

- **FAQ answers** open with a standalone direct answer (6 to 15 words) that fully answers
  the question.
- **Key takeaways:** each bullet is a self-contained claim under 17 words.
- **Definitions** open with a clean "X is Y" sentence.

### Self-contained passages

- Each paragraph makes sense on its own.
- **No cross-references:** never "as discussed above", "see below", "as mentioned earlier".
- **One concept per paragraph.**
- **Match the structure AI uses for this query type:** if answers to it come back as
  numbered lists, write a numbered list.

### Readability

- Consumer queries: plain words, short sentences, relatable examples.
- B2B or technical queries: precise language; industry terms are expected.

## EEAT signals

### Author

- Recommend a byline with specific, relevant credentials in the verification report.
- Specific qualifications beat generic titles.

### Third-party validation: neutral authorities only

- Back every significant claim with a credible named source.
- Valid sources: government bodies and regulators, peer-reviewed research, standards
  bodies, official statistics, official product documentation, and the brand's own
  first-party data.
- **Standard articles never name or attribute a claim to a competitor.** If a fact only
  appears on a competitor's site, trace it to the neutral source or state it plainly.
- Name the source in the text, not only in a link.

### Specificity

- Replace vague marketing claims with checkable detail.
  - Weak: "tried-and-trusted security"
  - Strong: "SOC 2 Type II certified, with data stored in Sydney data centres"
- Test: could an AI cross-check this claim against an outside source? If not, rewrite it.

### Authenticity

- Never fabricate credentials, ratings or statistics. Unsupported claims reduce citations.

## Internal link patterns

- Descriptive anchor text that tells the reader what they will find.
- 3 to 5 internal links per 1,000 words, spread through the article.
- Never "click here", "read more", "learn more" or "this article".
- Link on the first mention only.
- Every internal link in the brief appears somewhere in the article.
- Grammar beats placement: if a link would break a sentence, place it on a nearby phrase or
  flag it for the editor.

## Comparison tables

- Clean Markdown, aligned columns, 3 to 10 words per cell.
- Always a "Best for" column with one honest niche per entry.
- Product comparisons also get a "Not for" column, including the user's own brand.
- Order: standard articles sort by relevance. Best X for Y pages follow the brief's ranking,
  and the user's brand is never first by default.
- Prices come from a named source or the vendor's pricing page, with a capture date. A
  value nobody publishes is "Not published". Never guess.
- Consistent formatting inside a column.

## Brand positioning

- When content fails to say what makes a brand distinct, AI fills the gap with generic
  descriptions averaged across the market.
- Say what the brand is, what it is not, and how it differs, with specifics from the
  brain's context files.
- Commercial content puts positioning in the first 3 sections.
- On a best-x-for-y page, positioning lives inside the brand's own pick entry, held to the
  same evidence standard as every other entry.

## Objections and deal breakers

- Lead with the direct answer, then the detail (pricing, contracts, support, security,
  integrations, onboarding).
- Source objections from the brain's research bank, FAQs and sales notes where they exist.

## CTA rules

- **Every article ends with a clear call to action.** It names the next step and the means
  (form, link, phone, booking) per the brief.
- It lives in the final main section. If an FAQ follows, the CTA still closes the main body
  before it.
- A section that only describes the brand is not a CTA.
- **Soft by default:** a helpful next step, not a hard sell.
- **One hard CTA at most**, only at the very end.
- **No mid-article hard sells, ever.**
- **Best X for Y pages:** one soft next step at the end only.
- **No urgency manipulation** ("act now", "limited time") in informational content.
