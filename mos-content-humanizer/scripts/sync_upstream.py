#!/usr/bin/env python3
"""Refresh the vendored Humanizer files from github.com/blader/humanizer."""

from __future__ import annotations

import argparse
import re
import shutil
import subprocess
import tempfile
from pathlib import Path

REPO = "https://github.com/blader/humanizer.git"
SKILL_DIR = Path(__file__).resolve().parents[1]


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--ref", default="main", help="Branch, tag or commit to vendor.")
    args = parser.parse_args()

    with tempfile.TemporaryDirectory() as tmp:
        checkout = Path(tmp) / "humanizer"
        subprocess.run(["git", "clone", "--quiet", REPO, str(checkout)], check=True)
        subprocess.run(["git", "-C", str(checkout), "checkout", "--quiet", args.ref], check=True)
        commit = subprocess.run(["git", "-C", str(checkout), "rev-parse", "HEAD"],
                                check=True, capture_output=True, text=True).stdout.strip()
        skill = (checkout / "SKILL.md").read_text(encoding="utf-8")
        version = re.search(r'(?m)^\s+version:\s*["\']?([0-9.]+)', skill)

        shutil.copyfile(checkout / "SKILL.md", SKILL_DIR / "references" / "humanizer.md")
        shutil.copyfile(checkout / "LICENSE", SKILL_DIR / "LICENSE")

    upstream = SKILL_DIR / "UPSTREAM.md"
    text = upstream.read_text(encoding="utf-8")
    text = re.sub(r"(?m)^\| Commit \| .* \|$", f"| Commit | {commit} |", text)
    if version:
        text = re.sub(r"(?m)^\| Version \| .* \|$", f"| Version | {version.group(1)} |", text)
    upstream.write_text(text, encoding="utf-8")

    print(f"Vendored humanizer {version.group(1) if version else '?'} at {commit}")
    print("Review with: git diff -- " + str(SKILL_DIR.relative_to(SKILL_DIR.parent)))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
