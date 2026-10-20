# Quality checklists

Verification checklists for mos-content-writer, by brief type.

## Standard article checklist

**Points S1 to S3 are must-fix safety rules. Any failure ships an embarrassing mistake;
fix it before output.**

- **S1. No competitor named** in the body or citations: no "As [Brand] notes", no
  competitor links. Claims are re-attributed to neutral authorities or stated plainly.
- **S2. No research or process disclosure:** zero "competitor article we reviewed", "other
  guides", "unlike most articles", "pages we looked at" and the like. Insights are stated
  directly.
- **S3. A real closing CTA:** the article ends with a call to action that asks for the
  action and gives the means (form, link, phone, booking) per the brief, placed before any
  FAQ. A section that only describes the brand is not a CTA.

1. Total word count within 15% of target.
2. Section word counts within 15% of their targets.
3. Every internal link from the brief used.
4. Primary keyword in the H1.
5. Primary keyword in the first 100 words.
6. Primary keyword in 2 or more H2s.
7. Each secondary keyword in at least one section.
8. Spelling matches the brain's locale (Australian English unless the voice file says otherwise).
9. External links only to reputable, non-competing sources.
10. Every heading from the brief's outline present.
11. GEO: key claims are short declarative sentences (under 17 words).
12. GEO: FAQ answers open with a standalone direct answer.
13. EEAT: significant claims backed by named third-party sources (no bare "studies show"). <!-- copy-ignore -->
14. EEAT: no vague marketing language without data or attribution.
15. GEO: no cross-reference phrases ("as discussed above", "see below").
16. GEO: one concept per paragraph.
17. Brand positioning: at least one clear differentiator in the first 3 sections.
18. Zero em dashes in the article.
19. No 3+ word phrase repeated 3+ times (keywords and brand name excepted).
20. The introduction acknowledges the reader's situation before informing.
21. At least one concrete example per H2.
22. The `mos-content-humanizer` pass ran on the full draft before verification.

**Pass threshold:** every point passes (S1 to S3 and 1 to 21).

## Best X for Y checklist

**Points B1 to B5 are must-fix integrity rules.**

- **B1. The user's brand is not first by default.** Its position matches the brief, and it
  appears only on pages where it passed the eligibility gate.
- **B2. Every competitor fact traces to an evidence row** in the brief (source URL, capture
  date, verbatim quote), and the source is named in the text.
- **B3. Every pick has "Best for" and "Not for"**, each tied to a stated criterion.
- **B4. The methodology block matches the approved criteria** (none added, dropped or
  reweighted).
- **B5. The disclosure line is present** near the top, before the picks.

1. The page opens with a direct answer to the query.
2. "Not published" is used wherever the brief has no published value; no guessed numbers.
3. Picks get comparable depth (no thin competitor entries beside a long brand entry).
4. Summary table matches the picks: same order, same "Best for" and "Not for".
5. No year in the title or H1.
6. Schema note recommends ItemList only; never AggregateRating or review stars.
7. Every internal link from the brief used.
8. Primary keyword in the H1 and the first 100 words.
9. Total word count within 15% of target.
10. Every heading from the brief's outline present.
11. GEO: FAQ answers open with a standalone direct answer.
12. GEO: no cross-reference phrases; one concept per paragraph.
13. No hard-sell CTA anywhere; one soft next step at the end.
14. Zero em dashes in the article.
15. No 3+ word phrase repeated 3+ times (keywords and product names excepted).
16. Spelling matches the brain's locale.
17. The `mos-content-humanizer` pass ran on the full draft before verification.

**Pass threshold:** every point passes (B1 to B5 and 1 to 16). Integrity failures come
first in revision.

## vs checklist

**Points V1 to V5 are must-fix integrity rules.**

- **V1. No brand-first framing.** The user's brand is not declared the winner by default,
  does not lead the answer, and gets no more depth than the competitor.
- **V2. Every competitor fact traces to a row** in `research/evidence.csv` (source URL,
  capture date, verbatim quote), and the source is named in the text.
- **V3. "Not published" is kept** wherever the evidence says so, for either brand.
- **V4. Capture dates are shown** for the evidence (in the table or next to each fact).
- **V5. The disclosure is present** (the user's brand publishes the page) with the method.

1. The page opens with a direct answer saying who each option suits.
2. Every comparison row from the brief is present, for both brands.
3. Both "Choose ... if" sections are present, each bullet tied to a row.
4. No year in the title or H1; no "#1" or unsourced superlatives.
5. Schema note recommends Article (plus FAQPage if there is an FAQ) only; never
   AggregateRating, Review or a ranked ItemList.
6. Every internal link from the brief used.
7. Primary keyword in the H1 and the first 100 words.
8. Total word count within the brief's range.
9. GEO: FAQ answers open with a standalone direct answer.
10. No hard-sell CTA anywhere; one soft next step at the end.
11. Zero em dashes in the article.
12. Spelling matches the brain's locale.
13. The `mos-content-humanizer` pass ran on the full draft before verification.

**Pass threshold:** every point passes (V1 to V5 and 1 to 13). Integrity failures come
first in revision.

## Running the checklists

- Run the checklist after the full draft, not during writing.
- Report a pass or fail table: point number, description, status.
- For each failure, name the location in the article and the fix.
- After fixing, re-run only the failed points.
- Never ship content that fails a point.
