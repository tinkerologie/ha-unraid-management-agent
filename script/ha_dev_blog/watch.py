#!/usr/bin/env python3
# script/ha_dev_blog/watch.py: Find developer blog changes used by the integration
"""Match change-announcing inline code to integration source, without GitHub writes."""

from __future__ import annotations

import argparse
import json
import re
import sys
import urllib.request
import xml.etree.ElementTree as ET
from datetime import UTC, datetime, timedelta
from email.utils import parsedate_to_datetime
from html.parser import HTMLParser
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
PACKAGE = ROOT / "custom_components" / "unraid_management_agent"
FEED = "https://developers.home-assistant.io/blog/rss.xml"
ANNOUNCEMENT = re.compile(
    r"deprecated|removed|will be removed|no longer|breaking|stops? working|must now",
    re.IGNORECASE,
)


class UnraidAnnouncementParser(HTMLParser):
    """Assign inline code to its innermost paragraph or list item."""

    def __init__(self) -> None:
        """Initialise the block and inline-code stacks."""
        super().__init__(convert_charrefs=True)
        self.blocks: list[tuple[str, list[str], list[str]]] = []
        self.announced: dict[str, str] = {}
        self.code: list[str] | None = None
        self.pre = 0
        self.has_blocks = False

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        """Open a prose block or an inline-code span, excluding code examples."""
        if tag in {"p", "li"}:
            self.has_blocks = True
            self.blocks.append((tag, [], []))
        elif tag == "pre":
            self.pre += 1
        elif tag == "code" and self.blocks and not self.pre:
            self.code = []

    def handle_data(self, data: str) -> None:
        """Collect block text and the active inline-code span."""
        for _, text, _ in self.blocks:
            text.append(data)
        if self.code is not None:
            self.code.append(data)

    def handle_endtag(self, tag: str) -> None:
        """Retain code only when its own prose block announces a change."""
        if tag == "code" and self.code is not None:
            if self.blocks:
                self.blocks[-1][2].append("".join(self.code))
            self.code = None
        elif tag == "pre" and self.pre:
            self.pre -= 1
        elif tag in {"p", "li"} and self.blocks and self.blocks[-1][0] == tag:
            _, parts, codes = self.blocks.pop()
            text = " ".join("".join(parts).split())
            if ANNOUNCEMENT.search(text):
                for code in codes:
                    token = code.strip().removesuffix("()").strip()
                    if token:
                        self.announced[token] = text


def fetch(url: str) -> str:
    """Fetch a public HTTPS blog page with redirects and a bounded timeout."""
    if not url.startswith("https://"):
        raise ValueError(f"Blog URL must use HTTPS: {url}")
    request = urllib.request.Request(  # noqa: S310 - HTTPS validated above
        url, headers={"User-Agent": "ha-unraid-management-agent-blog-watch"}
    )
    with urllib.request.urlopen(request, timeout=30) as response:  # noqa: S310
        return response.read().decode("utf-8")


def find_matches(token: str, sources: dict[Path, str]) -> list[str]:
    """Find literal identifiers and dotted imports, preserving source line numbers."""
    patterns = [re.compile(rf"(?<!\w){re.escape(token)}(?!\w)")]
    if "." in token:
        parent, _, name = token.rpartition(".")
        patterns.append(
            re.compile(
                rf"\bfrom\s+{re.escape(parent)}\s+import\s+"
                rf"(?:\([^)]*?\b|[^\n]*?\b){re.escape(name)}\b",
                re.DOTALL,
            )
        )
    matches = set()
    for path, text in sources.items():
        for pattern in patterns:
            for match in pattern.finditer(text):
                line = text.count("\n", 0, match.start()) + 1
                matches.add(f"{path.relative_to(ROOT).as_posix()}:{line}")
    return sorted(matches)


def scan(days: int, existing: list[dict[str, Any]], out: Path) -> None:
    """Write proposed issues and a summary of every recent feed item."""
    feed = ET.fromstring(fetch(FEED))  # noqa: S314 - official public RSS feed
    items = feed.findall("./channel/item")
    if not items:
        message = "Developer blog feed contains no posts"
        raise ValueError(message)
    sources = {
        path: path.read_text("utf-8")
        for path in sorted(PACKAGE.rglob("*"))
        if path.is_file() and path.suffix in {".py", ".yaml", ".json"}
    }
    cutoff = datetime.now(UTC) - timedelta(days=days)
    summary = [f"## Home Assistant developer blog: last {days} days", ""]
    issues = []
    for item in items:
        title = (item.findtext("title") or "Untitled post").strip()
        link = (item.findtext("link") or "").strip()
        try:
            date = parsedate_to_datetime(item.findtext("pubDate") or "")
        except TypeError, ValueError:
            summary.append(f"- [{title}]({link}): skipped: no publication date")
            continue
        if date.astimezone(UTC) < cutoff:
            continue
        duplicate = next(
            (
                issue
                for issue in existing
                if link.rstrip("/") and link.rstrip("/") in (issue.get("body") or "")
            ),
            None,
        )
        if duplicate:
            summary.append(
                f"- [{title}]({link}): already reported (#{duplicate['number']})"
            )
            continue
        html = (
            item.findtext("{http://purl.org/rss/1.0/modules/content/}encoded")
            or item.findtext("description")
            or ""
        )
        parser = UnraidAnnouncementParser()
        parser.feed(html)
        if not parser.has_blocks:
            parser = UnraidAnnouncementParser()
            parser.feed(fetch(link))
        parser.close()
        matches = {token: find_matches(token, sources) for token in parser.announced}
        used = {token: locations for token, locations in matches.items() if locations}
        if used:
            body = [
                link,
                "",
                f"Published: {date.astimezone(UTC).date()}",
                "",
                "This post announces changes to code used by the integration:",
                "",
            ]
            for token, locations in used.items():
                body.extend(
                    [
                        f"- `{token}`: {parser.announced[token]}",
                        *[f"  - `{location}`" for location in locations],
                    ]
                )
            issues.append({"title": f"HA dev blog: {title}", "body": "\n".join(body)})
            status = "new issue"
        elif matches:
            status = "code not used by the integration; checked: " + ", ".join(
                f"`{token}`" for token in matches
            )
        else:
            status = "no change-announcing code"
        summary.append(f"- [{title}]({link}): {status}")
    out.mkdir(parents=True, exist_ok=True)
    (out / "new_issues.jsonl").write_text(
        "".join(json.dumps(issue) + "\n" for issue in issues), "utf-8"
    )
    (out / "summary.md").write_text("\n".join(summary) + "\n", "utf-8")


def main() -> int:
    """Parse CLI arguments and report feed or metadata errors clearly."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--days", type=int, default=8)
    parser.add_argument("--existing", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    if args.days <= 0:
        parser.error("--days must be positive")
    try:
        existing = [
            json.loads(line)
            for line in args.existing.read_text("utf-8").splitlines()
            if line.strip()
        ]
        scan(args.days, existing, args.out)
    except (OSError, ValueError, ET.ParseError) as err:
        print(f"Cannot scan Home Assistant developer blog: {err}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
