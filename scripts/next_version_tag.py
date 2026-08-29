#!/usr/bin/env python3
"""Print the next vMAJOR.MINOR.PATCH tag."""

from __future__ import annotations

import argparse
import re
import subprocess
import sys

TAG_RE = re.compile(r"^v(\d+)(?:\.(\d+))?(?:\.(\d+))?(?:\..*)?$")


def parse_version(tag: str):
    match = TAG_RE.fullmatch(tag.strip())
    if not match:
        return None
    major = int(match.group(1))
    minor = int(match.group(2) or 0)
    patch = int(match.group(3) or 0)
    return (major, minor, patch)


def format_tag(version):
    major, minor, patch = version
    return f"v{major}.{minor}.{patch}"


def existing_tags(provided=None):
    if provided is not None:
        return list(provided)
    result = subprocess.run(
        ["git", "tag", "--list", "v*"],
        check=False,
        capture_output=True,
        text=True,
    )
    if result.returncode != 0 or not result.stdout.strip():
        return []
    return [line.strip() for line in result.stdout.splitlines() if line.strip()]


def next_version_tag(tags=None):
    parsed = []
    raw_tags = existing_tags(tags)
    for tag in raw_tags:
        version = parse_version(tag)
        if version is not None:
            parsed.append(version)

    if not parsed:
        return "v1.0.0"

    major, minor, patch = max(parsed)
    candidate = (major, minor, patch + 1)
    known = {format_tag(item) for item in parsed}
    # Also treat unparsable provided tags as occupied names.
    known.update(raw_tags)
    while format_tag(candidate) in known:
        candidate = (candidate[0], candidate[1], candidate[2] + 1)
    return format_tag(candidate)


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("tags", nargs="*", help="Optional tags to bump from (for tests)")
    args = parser.parse_args(argv)
    tags = args.tags or None
    sys.stdout.write(next_version_tag(tags) + "\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
