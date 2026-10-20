# Brief type handlers

How to detect and handle each brief type this skill writes from.

## Detecting the brief type

From the brief's Content Guidelines table and outline:

- `Content type` mentions "best X for Y" or "buyer's guide", or the outline has a
  methodology block and picks with "Best for" and "Not for": **best-x-for-y**.
- `New or Optimisation` is "Optimisation": **not supported**. Stop and offer a fresh
  standard brief from `mos-content-brief`.
- Anything else: **standard**.

The type decides the parsing, the writing flags and the checklist.

## Standard article briefs (from mos-content-brief)

### Outline format

The outline is real Markdown headings under `# Article Outline`:

- `#` is the article title (one per brief).
- `##` are the main sections, `###` the subsections.
- Each heading is followed by a writing-instructions block (a line or list starting
  "WRITING INSTRUCTIONS:" or "Writer guidelines"), which holds what to cover, the
  approximate word count, search-result references, gap markers ("SERP GAP") and the
  internal links for that section.
- Bullets under a heading (for example key takeaways) are content to write, not instructions.

### Writing flow

Work top to bottom. For each heading:

1. Find its writing instructions.
2. Write the section, following them exactly.
3. Land within 15% of the word target.
4. Weave in the section's internal links.
5. Answer every gap marker with original, sourced material.

## Best X for Y briefs (from mos-content-best-x-for-y)

A best-x-for-y page is a genuine buyer's guide, not a self-promotional listicle. The
brief has already done the judgement: demand checks, the eligibility gate, the candidate
set, the approved criteria and methodology, the evidence and the picks. The writer's job
is to write it faithfully, not to re-rank it.

### Evidence files (required)

Read three files from the brief's research folder, `<brief dir>/research/` (layout:
`$SKILL/../mos-content-best-x-for-y/references/data-files.md`):

- `evidence.csv`: one row per fact (`id`, `entry`, `claim`, `value`, `source_url`,
  `snapshot_path`, `captured_on`, `quote`).
- `picks.json`: per entry `position`, `name`, `is_brand`, `best_for`, `not_for`, `criterion`
  and `evidence` ids, plus `best_overall`.
- `criteria.md`: the approved criteria and the methodology block.

If any of them is missing or empty, stop and offer to re-run `mos-content-best-x-for-y`.
Pass each pick's evidence rows and `picks.json` record, plus `criteria.md`, to the section
writer, and all three paths to the content verifier.

### What to carry from the brief

- **Answer block:** the direct answer (the top picks in one or two sentences) that opens
  the page.
- **Disclosure line:** for example "We make X; here is how we chose." Use the brief's
  wording. It appears near the top, before the picks.
- **Methodology block:** the criteria and how they were weighed, as approved by the user
  (`criteria.md`).
- **Picks:** each entry with its "Best for", its "Not for", the criterion each one rests on,
  and its evidence ids (`picks.json`).
- **Evidence rows:** for every competitor fact, the source URL, the capture date and a
  verbatim quote from the saved snapshot (`evidence.csv`). A value nobody publishes is
  "Not published".
- **Eligibility result for the user's brand:** where it passed, its entry; where it failed,
  it does not appear on this page at all.

### Flags

**ANSWER_FIRST=true** (answer block and guide sections)
- The first sentence answers the query on its own. Context follows.
- Guide sections (what to look for, how to choose) teach the criteria the picks are judged
  on. They name no product unless the brief says so.

**METHODOLOGY_VERBATIM=true** (methodology block)
- Keep the criteria, their order and their weighting exactly as the brief states them.
  You may tighten wording; you may not add, drop or reweight a criterion.

**PICK_ENTRY=true** (each pick)
- Open with a plain declarative line: what the product is and who it suits.
- State "Best for" and "Not for" explicitly, each tied to a named criterion.
- Every factual claim about a competitor comes from the brief's evidence rows, with the
  source named in the text. Never state a weakness that has no evidence row.
- Use "Not published" where the brief says so. Never fill the gap with a guess.
- Every pick gets comparable depth. There is no depth asymmetry.

**OWN_BRAND=true** (the user's brand, only where it passed the gate)
- Same structure, same depth and same evidence standard as every other pick.
- Its position is the brief's position. It is never moved to first place by the writer.
- Its "Not for" line is as honest as everyone else's.

### Order of the page

Follow the brief's outline. The usual shape is: answer block, disclosure line, summary
table, methodology, picks, how to choose, FAQ, closing next step. Build the summary table
after the picks are written so it matches them.

### Things a best-x-for-y page never does

- Ranks the user's brand first by default, or includes it where it failed the gate.
- Puts a year in the title.
- Asks for AggregateRating or review-star schema. Recommend ItemList schema only.
- Invents ratings, prices or features.
- Uses hard-sell language. One soft next step at the end is the only CTA.
