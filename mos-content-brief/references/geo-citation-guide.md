# GEO & AI Citation Optimisation Guide

Reference data from Daniel Shashko's sentence-level citation study (March 2026): 42,971 citations across 520 queries on 6 AI platforms. Treat the numbers as one study's findings, not guarantees.

## Why This Matters

Google's AI Mode, Gemini, ChatGPT, Perplexity, Copilot, and Grok all cite web content differently. 74.7% of cited URLs don't appear in the organic top-10: meaning AI citation is a separate channel from traditional SEO. Content structure and sentence design directly influence whether a page gets cited.

## Sentence-Level Rules

These rules come from decoding the `#:~:text=` fragments Google embeds in AI Mode citation URLs: the exact sentences Google extracts.

| Rule | Evidence |
|------|----------|
| Key claims should be 6-15 words | Median cited sentence: 10 words. Max: 17 words. 92.4% fall within 6-20 words. |
| One fact per sentence | Google uses sentence-boundary chunking with per-sentence scoring. Zero mid-sentence fragments found. |
| Declarative tone: no hedging | Cited sentences are self-contained single-claim statements ("atomic facts"). |
| No sentence should exceed 17 words | Nothing over 17 words appears in the 11,672-sentence dataset. |

## Page Structure Rules

| Rule | Evidence |
|------|----------|
| Front-load key claims in first 3 paragraphs | 75% of citations come from top half of page. Mean position: 34.9%. |
| Use H2/H3 for topic sections | Mean heading count on cited pages: 24. |
| Use lists and tables for enumerations | Structured pages: 91.3% match rate vs 39.3% for unstructured (2.3x advantage). |
| Lead with answer, then context | Positional bias is statistically significant (p < 10^-150). |
| Use query term verbatim in first paragraph | Topical signal matching improves citation probability. |

## Readability

Readability follows a **bimodal** pattern: very easy (Flesch 90-100) and college-level (Flesch <30) are both heavily cited. The "muddy middle" (Flesch 50-59) is the least cited tier at only 5.0%.

**Rule:** Match readability to query intent. Consumer health/lifestyle queries → write very simply. Technical/professional/B2B queries → write with precision and domain terminology.

## Platform-Specific Levers

| Platform | Primary Lever | Organic Top-10 Overlap |
|----------|--------------|----------------------|
| Perplexity | Organic ranking + freshness | 43.5% |
| Copilot | Positions 1-3 + Bing SEO | 32.5% |
| AI Mode | Sentence structure + page position | 25.1% |
| Grok | Domain-wide topical authority | 22.2% |
| Gemini | Sentence structure (different sources to AI Mode) | 15.3% |
| ChatGPT | Brand presence + freshness | 6.5% |

## How to Apply in Content Briefs

### For New Content Briefs

Add these as writing recommendations in the outline instructions:

1. **Opening paragraph instruction**: include a note to front-load the primary answer in a short declarative sentence (6-15 words) within the first 2-3 sentences
2. **Section instructions**: remind writers to lead each section with a direct answer sentence before expanding, and use lists/tables where enumerations exist
3. **FAQ section**: instruct writers to answer each FAQ with a standalone sentence of 6-15 words before elaborating (these are prime citation targets)
4. **Key Takeaways**: each bullet should be a self-contained claim under 17 words

### For Optimisation Briefs

Flag these specific issues in the audit:

1. **Opening position**: is the primary answer buried below the fold? Flag for restructuring
2. **Sentence length**: are key claims wrapped in 25+ word sentences? Flag for splitting
3. **Structure**: are there sections of unbroken prose without lists, tables, or subheadings? Flag for restructuring
4. **FAQ answers**: do FAQ answers start with a direct statement or do they meander? Flag for tightening
5. **Key Takeaways**: are they present? Are they under 17 words each? Flag if missing or too long
