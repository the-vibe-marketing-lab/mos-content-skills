#!/usr/bin/env python3
"""Convert a Markdown article to clean semantic HTML for a CMS paste.

Minimal output: no styling and no full-page boilerplate. Bold markers are
stripped from headings and [IMAGE: ...] markers become HTML comments.
Requires the `markdown` package (pip install markdown).

Usage:
    python3 generate_article_html.py <input.md> <output.html>
"""

import argparse
import re
import sys


def strip_front_matter(text: str) -> str:
    """Remove YAML front matter delimited by --- markers."""
    if text.startswith("---"):
        end = text.find("---", 3)
        if end != -1:
            return text[end + 3:].lstrip("\n")
    return text


def strip_bold_from_headings(text: str) -> str:
    """Turn '## **Heading**' into '## Heading'."""
    return re.sub(r"^(#{1,6}\s+)\*\*(.+?)\*\*", r"\1\2", text, flags=re.MULTILINE)


def convert_image_markers(text: str) -> str:
    """Convert [IMAGE: ...] markers to HTML comments."""
    return re.sub(r"\[IMAGE:\s*([^\]]*)\]", r"<!-- IMAGE: \1 -->", text)


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Convert a Markdown article to minimal semantic HTML."
    )
    parser.add_argument("input_md", help="the article .md file")
    parser.add_argument("output_html", help="where to write the .html file")
    args = parser.parse_args()

    try:
        import markdown
    except ImportError:
        print("Error: the markdown package is required (pip install markdown).", file=sys.stderr)
        sys.exit(1)

    try:
        with open(args.input_md, "r", encoding="utf-8") as f:
            content = f.read()
    except FileNotFoundError:
        print(f"Error: file not found: {args.input_md}", file=sys.stderr)
        sys.exit(1)

    content = convert_image_markers(strip_bold_from_headings(strip_front_matter(content)))
    html = markdown.markdown(content, extensions=["tables", "fenced_code"], output_format="html5")

    with open(args.output_html, "w", encoding="utf-8") as f:
        f.write(f'<div class="article-content">\n{html}\n</div>\n')

    print(f"HTML saved to: {args.output_html}")


if __name__ == "__main__":
    main()
