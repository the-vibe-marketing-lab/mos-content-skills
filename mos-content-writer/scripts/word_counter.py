#!/usr/bin/env python3
"""Deterministic word counter for Markdown articles.

Splits a Markdown file by H2 headings and prints per-section word counts as
JSON. The content verifier uses it because language models miscount words.

Usage:
    python3 word_counter.py <markdown_file_path>
"""

import argparse
import json
import re
import sys


def strip_front_matter(text: str) -> str:
    """Remove YAML front matter delimited by --- markers."""
    if text.startswith("---"):
        end = text.find("---", 3)
        if end != -1:
            return text[end + 3:].lstrip("\n")
    return text


def count_words(text: str) -> int:
    """Count whitespace-separated words in a block of text."""
    return len(text.split())


def split_by_h2(text: str) -> list[dict]:
    """Split Markdown content into sections at each H2 heading."""
    h2_pattern = re.compile(r"^## (.+)$", re.MULTILINE)
    matches = list(h2_pattern.finditer(text))
    sections = []

    intro_text = text[: matches[0].start()].strip() if matches else text.strip()
    if intro_text:
        sections.append({"heading": "Introduction", "words": count_words(intro_text)})

    for i, match in enumerate(matches):
        heading = match.group(1).strip()
        end = matches[i + 1].start() if i + 1 < len(matches) else len(text)
        body = text[match.end():end].strip()
        sections.append({"heading": heading, "words": count_words(body)})

    return sections


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Print per-H2-section word counts of a Markdown article as JSON."
    )
    parser.add_argument("markdown_file", help="path to the article .md file")
    args = parser.parse_args()

    try:
        with open(args.markdown_file, "r", encoding="utf-8") as f:
            content = f.read()
    except FileNotFoundError:
        print(f"Error: file not found: {args.markdown_file}", file=sys.stderr)
        sys.exit(1)

    sections = split_by_h2(strip_front_matter(content))
    result = {"total": sum(s["words"] for s in sections), "sections": sections}
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
