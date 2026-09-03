#!/usr/bin/env python3
"""Smoke-test the exact file and link boundary of a Pages release artifact."""

from __future__ import annotations

import argparse
import json
import posixpath
import re
from html.parser import HTMLParser
from pathlib import Path, PurePosixPath
from urllib.parse import unquote, urlsplit


ROOT = Path(__file__).resolve().parents[1]
MANIFEST_PATH = ROOT / "config" / "pages-release.json"
GENERATED_FILES = {".nojekyll", "robots.txt"}
FORBIDDEN_TOP_LEVEL = {
    ".git",
    ".github",
    "catalog",
    "docs",
    "fonts",
    "general-store",
    "src",
    "tools",
}
NOINDEX_PATTERN = re.compile(
    r'<meta\s+name=["\']robots["\']\s+content=["\']noindex,\s*nofollow,\s*noarchive["\']\s*/?>',
    re.IGNORECASE,
)


class ReferenceCollector(HTMLParser):
    """Collect browser-resolved paths without interpreting script contents."""

    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.references: list[str] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        for name, value in attrs:
            if value and name in {"action", "href", "src"}:
                self.references.append(value)


def require(condition: bool, message: str) -> None:
    if not condition:
        raise SystemExit(message)


def load_manifest() -> dict:
    try:
        return json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))
    except (FileNotFoundError, json.JSONDecodeError) as exc:
        raise SystemExit(f"Cannot read {MANIFEST_PATH.relative_to(ROOT)}: {exc}") from exc


def manifest_source_files(manifest: dict) -> set[str]:
    allowlist = manifest.get("source_allowlist", {})
    required = allowlist.get("required")
    optional = allowlist.get("optional")
    require(isinstance(required, list), "Release required allowlist must be a list")
    require(isinstance(optional, list), "Release optional allowlist must be a list")
    require(all(isinstance(path, str) for path in required + optional), "Allowlisted paths must be strings")
    require(len(set(required + optional)) == len(required + optional), "Release allowlist contains duplicates")

    selected = set(required)
    selected.update(path for path in optional if (ROOT / path).is_file())
    return selected


def safe_relative_path(value: str) -> PurePosixPath:
    path = PurePosixPath(value)
    require(value == path.as_posix(), f"Non-canonical release path: {value}")
    require(not path.is_absolute(), f"Absolute release path is forbidden: {value}")
    require(".." not in path.parts, f"Parent traversal is forbidden: {value}")
    require(path.parts, "Empty release path is forbidden")
    require(path.parts[0] not in FORBIDDEN_TOP_LEVEL, f"Repository-internal path is forbidden: {value}")
    if path.parts[0] == "config":
        require(
            value in {
                "config/request-intake.json",
                "config/formspree-intake.json",
                "config/order-portal.json",
            },
            f"Only reviewed public runtime configuration may be released: {value}",
        )
    return path


def artifact_files(artifact: Path) -> set[str]:
    require(artifact.is_dir(), f"Release artifact does not exist: {artifact}")
    found: set[str] = set()
    for path in artifact.rglob("*"):
        require(not path.is_symlink(), f"Symlink is forbidden in release artifact: {path}")
        if path.is_file():
            relative = path.relative_to(artifact).as_posix()
            safe_relative_path(relative)
            found.add(relative)
    return found


def validate_reference(artifact: Path, html_path: Path, reference: str) -> None:
    parsed = urlsplit(reference)
    if parsed.scheme or parsed.netloc or not parsed.path:
        return

    raw_path = unquote(parsed.path)
    require(not raw_path.startswith("/"), f"Root-absolute link is unsafe for project Pages: {reference}")
    normalized = posixpath.normpath(posixpath.join(html_path.parent.relative_to(artifact).as_posix(), raw_path))
    require(normalized != ".." and not normalized.startswith("../"), f"Link escapes release root: {reference}")
    safe_relative_path(normalized)
    require((artifact / normalized).is_file(), f"Release link target is missing: {html_path.name} -> {reference}")


def validate_artifact(artifact: Path) -> None:
    manifest = load_manifest()
    expected = manifest_source_files(manifest) | GENERATED_FILES
    for relative in expected:
        safe_relative_path(relative)

    actual = artifact_files(artifact)
    require(
        actual == expected,
        "Release artifact boundary mismatch. "
        f"Missing: {sorted(expected - actual)}; unexpected: {sorted(actual - expected)}",
    )

    robots = (artifact / "robots.txt").read_text(encoding="utf-8")
    require(robots == "User-agent: *\nDisallow: /\n", "robots.txt must block all crawling")
    require((artifact / ".nojekyll").read_bytes() == b"", ".nojekyll must be empty")

    for relative in sorted(actual):
        path = artifact / relative
        if path.suffix != ".html":
            continue
        text = path.read_text(encoding="utf-8")
        require(NOINDEX_PATTERN.search(text) is not None, f"Missing noindex metadata: {relative}")
        parser = ReferenceCollector()
        parser.feed(text)
        for reference in parser.references:
            lowered = unquote(reference).lower()
            require("general-store" not in lowered, f"General Store reference is forbidden: {relative} -> {reference}")
            validate_reference(artifact, path, reference)

    print("Pages release artifact boundary and link smoke checks passed.")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("artifact", type=Path, help="Artifact directory to inspect")
    args = parser.parse_args()
    validate_artifact(args.artifact.resolve())


if __name__ == "__main__":
    main()
