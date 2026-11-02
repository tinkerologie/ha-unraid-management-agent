#!/usr/bin/env python3
# script/build-release.py: Build the reproducible HACS release ZIP
"""
Build the fixed-name HACS ZIP with tracked integration files at its root.

Timestamps, permissions, entry order and compression are fixed. Validate the
manifest version and runtime assets, and reject unresolved frontend imports
before writing the archive and SHA256SUMS. Adapted from ha-unraid's builder.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import posixpath
import re
import stat
import subprocess
import sys
import time
import zipfile
from collections.abc import Iterable, Iterator, Sequence
from dataclasses import dataclass
from pathlib import Path, PurePosixPath

ROOT = Path(__file__).resolve().parent.parent
PACKAGE = "custom_components/unraid_management_agent"
ZIP_NAME = "unraid_management_agent.zip"
CHECKSUMS_NAME = "SHA256SUMS"
REQUIRED_FILES = (
    "manifest.json",
    "__init__.py",
    "config_flow.py",
    "api/__init__.py",
    "strings.json",
    "translations/en.json",
    "services.yaml",
    "icons.json",
    "brand/icon.png",
    "brand/icon@2x.png",
    "brand/logo.png",
    "brand/logo@2x.png",
    "frontend/unraid-cards.js",
)

# 1980-01-01T00:00:00Z, the earliest timestamp a zip entry can store.
ZIP_EPOCH = 315532800
FILE_MODE = stat.S_IFREG | 0o644
COMPRESS_LEVEL = 9
UNIX_SYSTEM = 3  # external_attr then carries the Unix file mode

# JavaScript is tokenized (comments, strings, template literals and regular
# expression literals) so that text inside them is never read as an import.
JS_NAME = re.compile(r"[\w$\u0080-\uffff]+")
JS_PUNCTUATORS = ("?.", "...", "++", "--")
# A ")" closing the condition of these statements may be followed by a regex.
JS_CONDITION_KEYWORDS = frozenset({"for", "if", "while", "with"})
# A "/" after these keywords starts a regular expression, not a division.
JS_REGEX_KEYWORDS = frozenset(
    {
        "await",
        "case",
        "delete",
        "do",
        "else",
        "in",
        "instanceof",
        "new",
        "of",
        "return",
        "throw",
        "typeof",
        "void",
        "yield",
    }
)


class BuildError(Exception):
    """Raised when the release cannot be built."""


@dataclass(frozen=True, slots=True)
class JsToken:
    """
    One significant JavaScript token.

    ``kind`` is ``name``, ``punct``, ``number``, ``string``, ``template`` or
    ``regex``. A template that contains ``${...}`` has ``interpolated`` set; a
    ``)`` that closes an ``if``/``while``/``for``/``with`` condition has
    ``closes_condition`` set, because a regular expression may follow it.
    """

    kind: str
    value: str
    interpolated: bool = False
    closes_condition: bool = False


class JsScanError(Exception):
    """Raised when JavaScript cannot be tokenized (unterminated literal)."""


def _regex_allowed(tokens: list[JsToken]) -> bool:
    """Return whether a "/" at this point starts a regular expression literal."""
    if not tokens:
        return True
    last = tokens[-1]
    if last.kind == "name":
        return last.value in JS_REGEX_KEYWORDS
    if last.kind == "punct":
        # A "/" after a postfix ++ or -- is a division: count++ / 2.
        return last.closes_condition or last.value not in {")", "]", "}", "++", "--"}
    return False


def _end_of_quoted(source: str, start: int, quote: str) -> int:
    """Return the index after the string literal that starts at ``start``."""
    i = start + 1
    while i < len(source):
        char = source[i]
        if char == "\\":
            i += 2
            continue
        if char == quote:
            return i + 1
        if char == "\n":
            break
        i += 1
    raise JsScanError(f"unterminated string at offset {start}")


def _end_of_regex(source: str, start: int) -> int:
    """Return the index after the regular expression literal at ``start``."""
    i, in_class = start + 1, False
    while i < len(source):
        char = source[i]
        if char == "\\":
            i += 2
            continue
        if char == "\n":
            break
        if char == "[":
            in_class = True
        elif char == "]":
            in_class = False
        elif char == "/" and not in_class:
            i += 1
            while i < len(source) and (source[i].isalnum() or source[i] in "_$"):
                i += 1
            return i
        i += 1
    raise JsScanError(f"unterminated regular expression at offset {start}")


def _template_part(source: str, start: int) -> tuple[int, str, bool]:
    """Read template text from ``start`` to the closing backtick or ``${``."""
    i = start
    while i < len(source):
        char = source[i]
        if char == "\\":
            i += 2
            continue
        if char == "`":
            return i + 1, source[start:i], False
        if source.startswith("${", i):
            return i + 2, source[start:i], True
        i += 1
    raise JsScanError(f"unterminated template literal at offset {start - 1}")


def js_tokens(source: str) -> list[JsToken]:
    """Tokenize JavaScript, skipping comments and whitespace."""
    tokens: list[JsToken] = []
    # One entry per open brace: True when it closes a template substitution.
    braces: list[bool] = []
    # One entry per open parenthesis: True when it holds a statement condition.
    parens: list[bool] = []
    i = 0
    while i < len(source):
        char = source[i]
        if char.isspace():
            i += 1
        elif source.startswith("//", i):
            end = source.find("\n", i)
            i = len(source) if end < 0 else end
        elif source.startswith("/*", i):
            end = source.find("*/", i + 2)
            if end < 0:
                raise JsScanError(f"unterminated comment at offset {i}")
            i = end + 2
        elif char in "\"'":
            end = _end_of_quoted(source, i, char)
            tokens.append(JsToken("string", source[i + 1 : end - 1]))
            i = end
        elif char == "`":
            i, text, open_substitution = _template_part(source, i + 1)
            tokens.append(JsToken("template", text, open_substitution))
            if open_substitution:
                braces.append(True)
        elif char == "}" and braces and braces[-1]:
            braces.pop()
            i, _, open_substitution = _template_part(source, i + 1)
            if open_substitution:
                braces.append(True)
            else:
                tokens.append(JsToken("template", "", interpolated=True))
        elif char == "/" and _regex_allowed(tokens):
            end = _end_of_regex(source, i)
            tokens.append(JsToken("regex", source[i:end]))
            i = end
        elif char.isdigit():
            match = JS_NAME.match(source, i)
            end = match.end() if match else i + 1
            while end < len(source) and source[end] == "." and source[end - 1] != ".":
                match = JS_NAME.match(source, end + 1)
                end = match.end() if match else end + 1
            tokens.append(JsToken("number", source[i:end]))
            i = end
        elif match := JS_NAME.match(source, i):
            tokens.append(JsToken("name", match.group()))
            i = match.end()
        else:
            punct = next((p for p in JS_PUNCTUATORS if source.startswith(p, i)), char)
            closes_condition = False
            if char == "{":
                braces.append(False)
            elif char == "}" and braces:
                braces.pop()
            elif char == "(":
                last = tokens[-1] if tokens else None
                parens.append(
                    last is not None
                    and last.kind == "name"
                    and last.value in JS_CONDITION_KEYWORDS
                )
            elif char == ")" and parens:
                closes_condition = parens.pop()
            tokens.append(JsToken("punct", punct, closes_condition=closes_condition))
            i += len(punct)
    if braces and any(braces):
        message = "unterminated template literal"
        raise JsScanError(message)
    return tokens


def _matching_paren(tokens: list[JsToken], start: int) -> int | None:
    """Return the index of the ``)`` matching the ``(`` at ``start``."""
    depth = 0
    for index in range(start, len(tokens)):
        if tokens[index].kind != "punct":
            continue
        if tokens[index].value == "(":
            depth += 1
        elif tokens[index].value == ")":
            depth -= 1
            if depth == 0:
                return index
    return None


def js_import_specifiers(source: str) -> Iterator[JsToken | None]:
    """
    Yield the specifier token of every import; None for import(expression).

    Covers ``import "x"``, ``import ... from "x"``, ``export ... from "x"`` and
    ``import("x")`` (optionally with import attributes). Property access such
    as ``loader.import(...)`` or ``Array.from(...)``, ``import.meta``, and a
    method declared as ``import(name) {...}`` are not imports.
    """
    tokens = js_tokens(source)
    literal = {"string", "template"}

    def at(index: int) -> JsToken | None:
        return tokens[index] if 0 <= index < len(tokens) else None

    for index, token in enumerate(tokens):
        if token.kind != "name" or token.value not in {"import", "from"}:
            continue
        before, after = at(index - 1), at(index + 1)
        if after is None or (before is not None and before.value in {".", "?."}):
            continue
        if after.kind in literal:
            yield after
            continue
        if token.value != "import" or after.value != "(":
            continue
        close = _matching_paren(tokens, index + 1)
        following = at(close + 1) if close is not None else None
        if following is not None and following.value == "{":
            continue  # a method named import
        argument, end = at(index + 2), at(index + 3)
        if argument is not None and argument.interpolated:
            yield argument
            continue
        complete = end is not None and end.value in {")", ","}
        yield argument if argument and argument.kind in literal and complete else None


def _git(root: Path, *args: str) -> str:
    """Run Git in ``root`` and return its standard output."""
    try:
        result = subprocess.run(
            ["git", "-C", str(root), *args],
            check=True,
            capture_output=True,
            text=True,
        )
    except (OSError, subprocess.CalledProcessError) as err:
        raise BuildError(f"git {' '.join(args)} failed in {root}") from err
    return result.stdout


def tracked_files(root: Path) -> list[str]:
    """Return the package files Git tracks, relative to the package, sorted."""
    prefix = f"{PACKAGE}/"
    names = [
        name.removeprefix(prefix)
        for name in _git(root, "ls-files", "-z", "--", PACKAGE).split("\0")
        if name
    ]
    return sorted(names)


def source_date_epoch(root: Path, environ: dict[str, str] | None = None) -> int:
    """Return the entry timestamp: ``SOURCE_DATE_EPOCH`` or the HEAD commit time."""
    value = (os.environ if environ is None else environ).get("SOURCE_DATE_EPOCH")
    if not value:
        value = _git(root, "log", "-1", "--format=%ct", "HEAD").strip()
    try:
        epoch = int(value)
    except ValueError as err:
        raise BuildError(f"Invalid SOURCE_DATE_EPOCH: {value!r}") from err
    return min(max(epoch, ZIP_EPOCH), 4354819198)


def check_regular_files(package_dir: Path, names: Iterable[str]) -> list[str]:
    """Report tracked paths that are missing or are not regular files."""
    problems = []
    for name in names:
        try:
            mode = (package_dir / name).lstat().st_mode
        except FileNotFoundError:
            problems.append(f"{name} is tracked but missing from the checkout")
            continue
        if not stat.S_ISREG(mode):
            problems.append(f"{name} is not a regular file")
    return problems


def check_manifest(package_dir: Path, members: set[str], tag: str | None) -> list[str]:
    """Report missing required files and a manifest version that differs from tag."""
    problems = [
        f"{required} is missing from the package"
        for required in REQUIRED_FILES
        if required not in members
    ]
    if "manifest.json" not in members:
        return problems
    try:
        manifest = json.loads((package_dir / "manifest.json").read_text("utf-8"))
    except (OSError, ValueError) as err:
        return [*problems, f"manifest.json cannot be read: {err}"]
    version = manifest.get("version")
    expected = tag.removeprefix("v") if tag else version
    if not isinstance(version, str) or not version or version != expected:
        problems.append(f"manifest.json version {version!r} does not match tag {tag!r}")
    return problems


def check_js_imports(package_dir: Path, members: set[str]) -> list[str]:
    """Report frontend import specifiers that do not resolve inside the package."""
    problems = []
    for name in sorted(m for m in members if m.endswith(".js")):
        source = (package_dir / name).read_text("utf-8")
        try:
            specifiers = list(js_import_specifiers(source))
        except JsScanError as err:
            problems.append(f"{name} cannot be scanned for imports: {err}")
            continue
        for token in specifiers:
            if token is None:
                problems.append(f"{name} has a dynamic import() of an expression")
                continue
            spec = token.value
            if token.interpolated:
                problems.append(f"{name} has an interpolated import specifier {spec}")
                continue
            if not spec.startswith(("./", "../")):
                problems.append(f"{name} imports {spec}, which is not a relative path")
                continue
            target = posixpath.normpath(PurePosixPath(name).parent.joinpath(spec))
            if target not in members:
                problems.append(f"{name} imports {spec}, which is not in the package")
    return problems


def validate(package_dir: Path, names: Sequence[str], tag: str | None) -> list[str]:
    """Return every problem with the package; an empty list means it can ship."""
    members = set(names)
    problems = check_regular_files(package_dir, names)
    problems += check_manifest(package_dir, members, tag)
    # Content checks read the files, so only run them on regular files.
    readable = {
        name
        for name in members
        if (package_dir / name).is_file() and not (package_dir / name).is_symlink()
    }
    problems += check_js_imports(package_dir, readable)
    return problems


def write_zip(package_dir: Path, names: Sequence[str], path: Path, epoch: int) -> None:
    """Write the zip with fixed metadata so the same input gives the same bytes."""
    date_time = time.gmtime(epoch)[:6]
    with zipfile.ZipFile(path, "w") as archive:
        for name in names:
            info = zipfile.ZipInfo(name, date_time=date_time)
            info.compress_type = zipfile.ZIP_DEFLATED
            info.create_system = UNIX_SYSTEM
            info.external_attr = FILE_MODE << 16
            archive.writestr(
                info, (package_dir / name).read_bytes(), compresslevel=COMPRESS_LEVEL
            )


def build(
    root: Path, output_dir: Path, tag: str | None, environ: dict[str, str] | None = None
) -> Path:
    """Validate the package and write ``unraid_management_agent.zip`` and ``SHA256SUMS``."""
    package_dir = root / PACKAGE
    dirty = _git(root, "status", "--porcelain", "--untracked-files=no", "--", PACKAGE)
    if dirty:
        message = "Tracked integration files have uncommitted changes"
        raise BuildError(message)
    names = tracked_files(root)
    problems = validate(package_dir, names, tag)
    if problems:
        raise BuildError("\n".join(f"- {problem}" for problem in problems))
    epoch = source_date_epoch(root, environ)
    output_dir.mkdir(parents=True, exist_ok=True)
    zip_path = output_dir / ZIP_NAME
    write_zip(package_dir, names, zip_path, epoch)
    digest = hashlib.sha256(zip_path.read_bytes()).hexdigest()
    (output_dir / CHECKSUMS_NAME).write_text(f"{digest}  {ZIP_NAME}\n", "utf-8")
    return zip_path


def main(argv: Sequence[str] | None = None) -> int:
    """Run the command-line interface."""
    parser = argparse.ArgumentParser(description="Build the release zip.")
    parser.add_argument("--tag", help="Release tag, e.g. v2026.10.1")
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path("build"),
        help="Directory for unraid_management_agent.zip and SHA256SUMS (default: build)",
    )
    args = parser.parse_args(argv)

    try:
        zip_path = build(ROOT, args.output_dir, args.tag)
    except (BuildError, OSError, ValueError) as err:
        print(f"Cannot build {ZIP_NAME}:\n{err}", file=sys.stderr)
        return 1

    with zipfile.ZipFile(zip_path) as archive:
        count = len(archive.namelist())
    checksum = (zip_path.parent / CHECKSUMS_NAME).read_text("utf-8").split()[0]
    version = json.loads((ROOT / PACKAGE / "manifest.json").read_text("utf-8"))[
        "version"
    ]
    print(
        f"Built {zip_path}: version {version}, {count} files, {zip_path.stat().st_size} bytes, sha256 {checksum}"
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
