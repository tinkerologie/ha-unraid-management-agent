"""Regression tests for bounded blog reports and duplicate detection."""

# ruff: noqa: S101 - assertions are intentional in this standalone regression test
import importlib.util
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

spec = importlib.util.spec_from_file_location(
    "watch", Path(__file__).with_name("watch.py")
)
watch = importlib.util.module_from_spec(spec)
spec.loader.exec_module(watch)


class BlogReports(unittest.TestCase):
    """Exercise issue size limits and idempotent rescans."""

    def test_large_post_is_bounded_and_source_remains_deduplicatable(self):
        """Keep oversized posts below GitHub limits without losing deduplication."""
        link = "https://developers.home-assistant.io/blog/test-post"
        prose = "".join(
            f"<p><code>symbol_{i}</code> is deprecated " + "x" * 2000 + "</p>"
            for i in range(100)
        )
        date = watch.datetime.now(watch.UTC).strftime("%a, %d %b %Y %H:%M:%S GMT")
        feed = (
            f"<rss><channel><item><title>Change</title><link>{link}</link>"
            f"<pubDate>{date}</pubDate><description><![CDATA[{prose}]]>"
            "</description></item></channel></rss>"
        )
        with (
            tempfile.TemporaryDirectory() as tmp,
            patch.object(watch, "fetch", return_value=feed),
            patch.object(
                watch, "find_matches", return_value=[f"file.py:{i}" for i in range(100)]
            ),
        ):
            out = Path(tmp)
            watch.scan(8, [], out)
            report = json.loads((out / "new_issues.jsonl").read_text())
            assert len(report["body"]) < 65536
            assert report["body"].startswith(link)
            assert "truncated" in report["body"]
            watch.scan(8, [{"number": 1, "body": report["body"]}], out)
            assert (out / "new_issues.jsonl").read_text() == ""
            assert "already reported (#1)" in (out / "summary.md").read_text()


if __name__ == "__main__":
    unittest.main()
