# Wikipedia: Signs of AI writing (brand-content digest)

Source: [Wikipedia:Signs of AI writing](https://en.wikipedia.org/wiki/Wikipedia:Signs_of_AI_writing),
maintained by WikiProject AI Cleanup, CC BY-SA 4.0. Digest written for marketing content on
2026-10-20; read the live page when a pattern here is unclear. Humanizer
(`humanizer.md`) is already built on this page, so this file covers only what Humanizer leaves out
or what matters more for web content than for prose.

## The principle behind every tell

A model predicts the most likely next words, so it regresses to the mean: the specific, unusual
fact (statistically rare) gets replaced with a generic, positive description (statistically
common) that could fit a hundred other subjects. When editing, the question is never only "is
there a tell here" but **"could this sentence appear unchanged on a competitor's page?"** If yes,
it needs the brand's specific fact, number, name or example, or it should go.

## Caveats (read before judging anyone's draft)

- Detector tools beat chance but have real error rates. Never treat a detector score as a verdict
  on a writer or a freelancer.
- People who rarely use LLMs judge AI text at roughly chance; heavy users do much better. Human
  writing is also absorbing AI habits. One tell proves nothing; act on clusters.
- The page is descriptive, not a style guide. A pattern is a sign of a problem, not the problem.

## Web-content checks Humanizer does not cover

| Check | What to look for | Fix |
|---|---|---|
| Chatbot citation residue | `:contentReference[oaicite:N]`, `oai_citation`, `turn0search0`, `[cite: 1]`, `[span_1](start_span)`, `grok_card`, lenticular brackets 【】, `attached_file` | Delete the token; re-source the claim properly or cut it |
| AI tracking parameters | `utm_source=chatgpt.com`, `utm_source=openai`, `utm_source=copilot.com`, `referrer=grok.com` on any link | Strip the parameter; it tells the reader (and Google) where the link came from |
| Unfilled placeholders | `[Client Name]`, `[insert statistic]`, `[Your Email Address]`, `Article Title 1` | Fill from the brief or the brain's own docs; never invent the value |
| Sources that do not hold up | Several dead links; DOIs that resolve to an unrelated paper; book citations with no page; a real source that does not say what the sentence claims | Open every outbound link before shipping; a citation must support the exact claim it sits on |
| Source-availability hedges | "while specific details are limited", "not widely documented", "based on available information", "should be treated as X rather than Y" | State what is known, or cut the sentence (pairs with Humanizer §23) |
| Small tables that should be prose | A two-column, four-row "Key statistics" table restating one paragraph | Fold into a sentence unless the brief asks for the table |
| Markdown leaking into the CMS | Literal `**`, `##`, `---` in a Doc, Shopify or WordPress body | Convert to native formatting |
| Heading errors | A heading that repeats the page title; skipped levels (H2 to H4); headings with nothing under them but more headings | One H1, sequential levels, every heading has body copy |
| Emoji as formatting | Emoji leading headings or list items in an article | Remove (Humanizer §20 covers the heading case) |
| Stock end sections | "Challenges and future outlook", "Legacy", "Awards and recognition" built from nothing specific | Cut, or rebuild from brand facts (Humanizer §13) |

## How this sits with the brain's rules

The brain's `CLAUDE.md` and voice files, the brief and compliance text still win (see `../SKILL.md`). A table or a
heading the brief requires stays, even if it matches a row above.
