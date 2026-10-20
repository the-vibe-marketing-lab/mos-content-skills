---
title: Review fixes for the mos-content port
date: 2026-10-21
status: done
---

# Review fixes

Two read-only reviews (publish safety, integration) found the issues below. Each fix is binding. "Done" means every check at the bottom passes.

## Blockers and high

1. **Brief template shape.** `_shared/templates/content-brief-template.md`: change `### Brand Guidelines` / `### Content Guidelines` (and any other guideline heading) to `##`, and add `## Article Outline` before the outline. `_shared/scripts/build_final_md.py`: exit non-zero with a clear message when the outline is empty or `Focus keyword(s)` is empty. Prove it: a master that follows the template literally builds with no "Not provided" on required rows.
2. **Writer reads best-x-for-y evidence.** In `mos-content-writer` (SKILL.md Phase 0 best-x-for-y step, `references/brief-type-handlers.md`), read `<brief dir>/research/evidence.csv`, `picks.json` and `criteria.md` (match the names `mos-content-best-x-for-y/references/data-files.md` actually defines). Stop if they are missing. Pass them to the section writer and the content verifier.
3. **Pack path resolution.** `~/.claude/skills/_shared` belongs to another skill pack and has same-named, different files, so a lexically normalised `../_shared/x` silently reads the wrong file. In `mos-content-writer` and `mos-content-humanizer`, add the same `$SKILL` resolver block `mos-content-brief` uses (`readlink -f` on `~/.claude/skills/<name>/SKILL.md`), and rewrite every bare `../_shared/X` or `../../_shared/X` (SKILL.md, agents, references, markdown links) as `$SKILL/../_shared/X`. Each skill that hands work to agents tells them to use the resolved `$SKILL`. `../mos-content-humanizer/SKILL.md` style sibling-skill paths are fine as they are.
4. **Python sibling lookup.** `_shared/scripts/ai_search.py` and `aio_scrape.py`: `os.path.abspath(__file__)` becomes `os.path.realpath(__file__)`. Check every other `.py` in the repo for the same pattern.
5. **`mos-geo-vs-content` is planned, not released.** Every mention (writer SKILL.md and description, best-x-for-y SKILL.md and `references/buyers-guide-method.md`) says "(planned, not yet released)", and the writer's Phase 0 does not dead-end a user there: it says no vs-page skill exists yet.
6. **Descriptions at most 1,024 characters.** Trim the writer, brief and best-x-for-y descriptions. Keep triggers and NOT FOR routes.
7. **Overlap with `mos-copy-brief` (engine skill, NOT in this repo, do not edit it).** In `mos-content-brief`'s description, state it is the full research pipeline (keyword, SERP, information gain, sitemap) and add "NOT FOR a quick no-API copy brief (mos-copy-brief)". Record the collision in the README follow-ups (the orchestrator writes the README; just report it).
8. **Client residue (publish blocker).** Replace every example carried over from the source agency's client work with neutral, invented examples that map to no real company (e.g. "project management software for small agencies"):
   - the industrial-product example keyword, brand description and third-party testing claim in `mos-content-brief/SKILL.md`, its agents and `_shared/content-output-routing.md`.
   - the telecoms keyword set in `_shared/toolchain-surfer.md` and `_shared/scripts/surfer_api.py`.
   - the insurance-product example keywords in `_shared/scripts/ai_search.py`.
   - First-person agency ops notes in `_shared/toolchain-surfer.md` (volume and support history): reword neutrally.
   - The agency brand colour in `_shared/scripts/drive_upload.py`: switch to a neutral colour.
9. **Plan docs.** Rewrite `docs/plans/2026-10-21-port-content-skills.md` so it names no agency entity, client, email, or local path: describe the sources as "the private agency skill pack this was ported from". Keep the decisions and method. Same rule for this file.

## Low

10. Revert "AU English" to "Australian English" (writer SKILL.md, `agents/content-verifier.md`, `references/quality-checklists.md`).
11. `mos-content-humanizer` description: lead with MarketingOS and add "NOT FOR general text outside a MarketingOS brain (use humanizer)".
12. One owner for DataForSEO volume: `_shared/scripts/dataforseo_api.py` owns HTTP, credentials and location codes (add ZA and `export ` handling in `.env`, plus a raising variant for callers that must not exit). `bxy.py volume` keeps its orchestration but imports from the shared script via `realpath(__file__)`; delete its private copy. Keep the 13 tests green and add one for the import.
13. Document the best-x-for-y shortlist-run folder in `_shared/content-output-routing.md`.
14. `mos-content-brief`: refuse "Optimisation" content type up front (no optimisation skill in this pack yet).

## Done checks

Search patterns below use a bracketed last letter (`prosperit[y]`) so the regex still matches the real word but this file does not match itself.

- `grep -rniE "pm-o[s]|pm-brai[n]|prosperit[y]|PROSPERIT[Y]_|clients/[<]|/mnt/[c]/Users|/home/richar[d]|asan[a]|everhou[r]|ventilatio[n]|CSIR[O]|virtual phon[e]|salary continuanc[e]|key perso[n]|buy sel[l]|52217[6]" --exclude-dir=__pycache__ --exclude=humanizer.md .` returns nothing.
- `grep -rnP '(?<!\$SKILL/)\.\./_shared' mos-content-writer mos-content-humanizer` returns nothing (only `$SKILL/../_shared`). The first draft of this check, `(^|[^$A-Z_])\.\./(\.\./)?_shared`, flags every correct `$SKILL/../_shared` too, because the character before `../` is always `/`.
- All `.py` compile; every CLI answers `--help`; `python3 -m unittest mos-content-best-x-for-y/scripts/test_bxy.py` passes.
- Template-literal master builds clean; a valid best-x-for-y brief passes `bxy.py check`; a year in the title fails it.
- Each description is 1,024 characters or fewer.
- No em dashes in any `.md` you edit.
