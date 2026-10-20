# StoryScope: narrative-level AI tells

Source: Russell, Rajendhran, Pham, Iyyer and Wieting, *StoryScope: Investigating idiosyncrasies
in AI fiction* ([arXiv 2604.03136](https://arxiv.org/abs/2604.03136); code and taxonomy at
[jenna-russell/storyscope](https://github.com/jenna-russell/storyscope), MIT). Digest written for
marketing content on 2026-10-20.

## Why this matters after Humanizer

Humanizer and the Wikipedia list work at the sentence level. StoryScope shows AI writing is
detectable **without any stylistic cue at all**: on 61,608 stories (human vs five LLMs),
narrative choices alone separated human from AI at 93.2% macro-F1, keeping over 97% of the signal
a style-aware detector gets. So a draft with every word-level tell removed can still read as AI
because of how it is built. These are the build-level defaults to push against.

The study is on fiction. The findings below are translated for brand content; they bite hardest
on narrative formats (case studies, About pages, founder stories, social posts, YouTube scripts,
email sequences) and more lightly on informational SEO articles.

## What AI does more than humans (AI rate vs human rate)

| Default | Finding | In brand content |
|---|---|---|
| Spells out the lesson | Narrator states the theme 77% vs 52%; more moralising overall | A section or case study that ends by telling the reader what it meant ("This shows that trust matters"). Cut it; let the result or number make the point (Humanizer §2). |
| Vague references | Implicit echoes 72% vs 50%; named references 24% vs 47% | "Industry leaders", "a recent study", "popular tools". Name the study, the tool, the place, the competitor where the brief allows. |
| Single-track, tidy structure | No subplots 79% vs 57%; tighter causal chains | Every section marching problem → solution → benefit in the same order. Vary it: lead with the outcome, open on a specific moment, allow a real complication. |
| Neat resolution | Resolves in internal understanding/acceptance 47% vs 27%; protagonist-driven resolution 69% vs 46% | Case studies where everything worked. Keep the honest caveat, the thing that took longer, the trade-off the customer chose. |
| Emotion through the body | Embodied emotion 81% vs 38%; explicit emotion words 8% vs 29% | Brand stories with "a weight lifted from her shoulders". Say what the customer felt or said, plainly, ideally in their words. |
| Sensory and setting padding | More sensory density, smell imagery 82% vs 57%, setting mirroring mood | Scene-setting intros ("the aroma of fresh coffee fills the air"). Cut to the fact. |
| Debate-shaped dialogue | Dialogue as philosophical debate 59% vs 34% | Quotes that sound like a thesis. Use real testimonial lines from customers, never invented ones. |

## What humans do more than AI

- **Address the reader** (direct address 0.28 vs 0.07; breaking the frame 0.67 vs 0.39). Second
  person and the odd aside are human; keep them where tone-of-voice allows.
- **Moral and practical ambivalence** (59% vs 38%). A real recommendation names who it is *not*
  for.
- **Non-linear order** to hold back a reveal (more time jumps and flashbacks). Opening on the end
  result and working back is a human move.
- **More variety**: more places, more voices, more dialogue against narration. Uniformity is the
  tell; vary section shape and length on purpose.

## Claude's own fingerprint (our writers run on Claude)

Claude was the most identifiable model: the flattest escalation of any source, the most uniform
narrative voice, a conventional ("honour the tradition") approach to form, and quiet endings
with epilogues. Expect drafts from our pipeline to be even, calm and evenly paced. Counter it:
put the strongest point or number where it lands hardest rather than spreading weight evenly, let
one section run long and another short, and end on the concrete result or the CTA rather than a
reflective coda.

## Limits

Fiction corpus, ~5,000-word stories, models current in 2025–2026. Treat it as a checklist of
defaults, not a detector. The brain's voice file and the brief still win (see `../SKILL.md`).
