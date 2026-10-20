# The buyer's guide method (best X for Y)

This file replaces the self-promotional listicle formula this skill was ported from. That
formula ranked the brand first, wrote it at three times the depth of everyone else, and
narrowed every competitor to a niche so the brand looked category-spanning. This method does
the opposite: it sends every reader to the option that suits them, and the brand earns its
place by being the most useful page on the question.

## Why the rules are strict

Each rule below exists because of a specific piece of evidence. Do not relax one without
re-reading the reason.

1. **Cited is not recommended.** When a brand's own list was cited by an AI engine, its odds
   of being the recommended option rose only from about 4% to about 7% (Scrunch, Sep 2026,
   about 10,000 cited URLs across 7 surfaces, with a placebo test explaining a quarter to a
   third of that rise). In 63.9% of answers that cited a listicle, no brand was recommended at
   all. Lily Ray found AI Overviews left the list's author out of the recommendation 69% of
   the time its own "best of" list was cited (224 of 323, B2B software, Apr to Jun 2026).
   A list that ranks its author first is mostly a citation for someone else. So the skill
   measures citation and recommendation as two separate numbers.
2. **Google has already hit the scaled self-ranked version.** In late January 2026, seven SaaS
   sites carrying 10 to 340 self-promotional "best" lists each lost 29% to 49% of Sistrix
   visibility (Lily Ray, 3 Feb 2026; Google has not confirmed the cause). The shared patterns:
   ranking yourself #1 with no disclosure or method, a year stuffed into the title, fake
   freshness (the date changed, the content did not), AggregateRating schema on pages that do
   not qualify, and templated, unreviewed content. Every one of those is banned here, and the
   skill writes 3 to 5 pages, never hundreds.
3. **Google's review guidance is the spec** (updated 10 Dec 2025). For any "best overall" or
   "best for" pick, say why, with first-hand supporting evidence where you have it. Share
   quantitative measures. Cover pros and cons. Explain which option suits which use. Make the
   ranked list useful on its own. Consider linking to more than one seller.
   https://developers.google.com/search/docs/specialty/ecommerce/write-high-quality-reviews
4. **Competitor claims are a legal exposure.** In Australia, comparative content falls under
   s18 of the Australian Consumer Law (misleading or deceptive conduct). Every claim about a
   competitor needs substantiation, a claim true of only one of their ranges can mislead, and
   a competitor's price change can make a live page misleading overnight. Other markets have
   equivalents (the FTC Act in the US, the CAP Code in the UK). Hence: source, date and
   verbatim quote on every competitor fact, "Not published" for unknowns, and a 90-day
   re-check.
5. **4 to 10 entries.** Lists of 4 to 10 brands did better for their author than lists of 2 to
   3 or 11 to 15 (Scrunch). Fewer than 4 is a comparison, which belongs on a vs page:
   `mos-geo-vs-content` (planned, not yet released).
6. **Expect a moving target.** Listicle share of ChatGPT citations reportedly halved after
   GPT 5.6 (Peec AI, Aug 2026, disputed by a smaller hotel-search corpus), and listicle share
   of Google AI Overview citations fell from about 26% to about 18% between Q1 and July 2026
   (Promptwatch, vendor data). Do not sell these pages as a sure win. Sell them as a page type
   that is still retrieved for "best" prompts, and measure the brand's own prompts before and
   after.

Source quality: an SEO tool vendor's own study, Lily Ray's February post, Scrunch (via a detailed write-up linking the
primary report) and Google's docs were read directly. Delta V, Promptwatch, Peec and the 69%
AIO figure are vendor or second-hand data, and most of these vendors sell AI-visibility tools.

## The five eligibility tests

Run per page (per Y). The brand is on the page only if it passes all five. User seeds get no
free pass.

| Test | Pass means | Typical fail |
|---|---|---|
| Offer | The brand actually sells this X | It sells something adjacent |
| Audience | It is built for this Y, not merely usable by them | A beginner page for an advanced product |
| Proof | There is evidence it delivers for Y (results, testimonials, case studies, reviews) | No proof from anyone like Y |
| Price | It is an honest pick at this price point | A "best free" page for a paid product |
| Availability | A reader can buy or join it today, in this market | Waitlist, pre-launch, not sold here |

A pre-launch brand passes nowhere. Its pages can still be written as neutral guides with a
disclosure that says what the author is building.

When a user seed fails, say which test failed and why in one plain sentence, and offer the
nearest Y that passes. A page the brand fails can still be built as a genuine guide that
recommends others; that is the user's call.

## Candidate set (per page)

Union of three sources, then trim to 4 to 10 with a reason per entry:

1. The options the AI engines recommended for the page's buyer prompt (the demand check).
2. The brands that appear across the Google top 10 for the page keyword.
3. Review-site and directory leaders for the category (G2, Capterra, Trustpilot,
   ProductReview, category directories, marketplaces).

Trim reasons that are fine: not sold in this market, discontinued, a near-duplicate of another
entry, not genuinely for Y. Trim reasons that are not fine: "they would beat us".

## Criteria and the methodology block

4 to 6 decision criteria for this Y, drawn from the buyer prompt's sub-questions (fan-out),
the brand's known objections (dealbreakers) and what reviewers complain about. Criteria are
the same for every entry, and none is picked to flatter the brand.

The methodology block on the page states:

- What was compared, against which criteria, and why those criteria matter for Y.
- How the facts were gathered (public pricing and feature pages, review sites, hands-on use if
  any) and the date they were checked.
- Who did the work.
- What was not tested (for example: "we did not buy every plan").
- The disclosure: "We make {brand}. It is one of the options below, and it is judged on the
  same criteria." If the brand is not on the page, the disclosure says the author works in the
  category.

The user approves the criteria and the methodology block before any entry is ranked.

## Evidence rules

- Every fact about any entry, the brand included, is a row in `evidence.csv`: id, entry,
  claim, value, source_url, snapshot_path, captured_on, quote. Schema in `data-files.md`.
- The quote is copied verbatim from the saved snapshot. Prices and numbers must appear in the
  quote exactly as they appear on the page.
- A value nobody publishes is written `Not published`, with the pages checked as its source.
  Never estimate, never infer from a third-party average without saying so.
- Third-party opinions (review sites, forums) are quoted and attributed. Your own judgement is
  allowed, and is stated as judgement against a named criterion ("on onboarding time, B is
  slower for a team of one"), never dressed as fact.
- First-hand evidence (screenshots, a trial, a measurement) is the strongest kind. Where only
  the owner can supply it, the brief leaves a labelled `[OWNER: ...]` slot for the writer.
  Pages without first-hand evidence say so in the methodology.
- Evidence older than 90 days is re-captured before the brief ships, and again every 90 days
  while the page is live.

## Pick assignment

- Every entry gets a "Best for" (a real strength a buyer in Y would value) and a "Not for"
  (who should pick something else), each tied to a stated criterion and citing evidence rows.
- The brand's "Not for" is as honest as everyone else's. If a competitor is the better fit for
  an avatar, the page says so.
- A "best overall" is allowed only when one entry wins on the stated criteria, and the pick
  record names the criterion and the evidence. The brand is never placed first by default.
  If there is no clear overall winner, there is no "best overall"; the page leads with
  "best for" picks instead.
- The structure and depth are the same for every entry. The brand does not get a longer
  write-up because the author knows more about it; that extra knowledge goes into evidence
  everyone can check.

## Page shape the brief instructs

1. **Answer first.** The opening two sentences name the quick picks and who each is for, in
   standalone sentences of 6 to 15 words (citation targets).
2. **Quick-picks table:** Option | Best for | Not for | Starting price (sourced) | Last checked.
   Plain HTML table, placed high on the page.
3. **How we chose** (the methodology block and disclosure).
4. **One section per entry,** identical structure: one-line verdict, who it is for, who it is
   not for, price (sourced), what reviewers say (attributed quotes), the evidence it rests on.
5. **How to choose for your situation:** a short decision guide by avatar or constraint that
   can send readers to any entry.
6. **FAQ** from search suggestions and fan-out, each answer opening with a standalone sentence.
   No self-referencing answers ("What is the best X? Our product is...").
7. **A single soft call to action** at most, and only on pages where the brand passed the gate.

## Banned patterns (the `bxy.py check` sensor fails on these)

- A year in the title tag or H1. A refreshed page shows a visible "last checked" date instead.
- AggregateRating or Review schema. Use ItemList schema only.
- An "updated" date without a real content change.
- The brand at #1 without a best_overall record that names the winning criterion.
- The brand on a page it failed the gate for, or on any page while pre-launch.
- Fewer than 4 or more than 10 entries.
- An entry with no "Best for", "Not for", criterion or evidence.
- A competitor fact without a source, a capture date within 90 days, and a verbatim quote
  found in its snapshot.
- No disclosure, no methodology heading, no "last checked" instruction.

## After publishing

Re-run the demand-check prompts 2 to 4 weeks after launch. Log, per engine, whether the page is
cited and, separately, whether the brand is recommended. Re-capture competitor facts every 90
days and flag rows that drifted.
