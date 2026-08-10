#!/usr/bin/env python3
"""Build the explicit, noindex Pages artifact and enforce launch gates on demand."""

from __future__ import annotations

import argparse
import json
import re
import shutil
from datetime import datetime
from pathlib import Path

from test_pages_release import manifest_source_files, safe_relative_path, validate_artifact


ROOT = Path(__file__).resolve().parents[1]
MANIFEST_PATH = ROOT / "config" / "pages-release.json"
STATE_PATH = ROOT / "config" / "project-state.json"
REQUEST_PATH = ROOT / "config" / "request-intake.json"
CATALOG_DIR = ROOT / "catalog"
NOINDEX_META = '<meta name="robots" content="noindex, nofollow, noarchive">'
SKU_PATTERN = re.compile(r"(?<![A-Z0-9])(?:[A-Z]{2,}-){2}\d{3}(?![A-Z0-9])")
FORMSPREE_PATTERN = re.compile(r"https://formspree\.io/f/[A-Za-z0-9_-]+/?")


def load_json(path: Path) -> dict:
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (FileNotFoundError, json.JSONDecodeError) as exc:
        raise SystemExit(f"Cannot read {path.relative_to(ROOT)}: {exc}") from exc
    if not isinstance(data, dict):
        raise SystemExit(f"Expected an object in {path.relative_to(ROOT)}")
    return data


def maybe_load_json(path: Path) -> dict | None:
    if not path.is_file():
        return None
    return load_json(path)


def validate_manifest(manifest: dict) -> None:
    expected = {
        "schema_version",
        "deployment_enabled",
        "release_skus",
        "request_backend",
        "source_allowlist",
    }
    if set(manifest) != expected:
        raise SystemExit("Unexpected pages-release configuration keys")
    if manifest.get("schema_version") != 1:
        raise SystemExit("Unsupported pages-release schema")
    if not isinstance(manifest.get("deployment_enabled"), bool):
        raise SystemExit("deployment_enabled must be boolean")
    release_skus = manifest.get("release_skus")
    if not isinstance(release_skus, list) or not all(isinstance(sku, str) and sku for sku in release_skus):
        raise SystemExit("release_skus must be a list of non-empty strings")
    if len(set(release_skus)) != len(release_skus):
        raise SystemExit("release_skus contains duplicates")
    request_backend = manifest.get("request_backend")
    required_backend_keys = {
        "e2e_verified",
        "verified_at",
        "owner_notification_verified",
        "customer_confirmation_verified",
    }
    if not isinstance(request_backend, dict) or set(request_backend) != required_backend_keys:
        raise SystemExit("Unexpected request_backend release-gate keys")
    for key in required_backend_keys - {"verified_at"}:
        if not isinstance(request_backend.get(key), bool):
            raise SystemExit(f"request_backend.{key} must be boolean")
    manifest_source_files(manifest)


def catalog_items() -> dict[str, list[dict]]:
    by_sku: dict[str, list[dict]] = {}
    for path in sorted(CATALOG_DIR.glob("*.json")):
        data = load_json(path)
        items = data.get("items", [])
        if not isinstance(items, list):
            continue
        for item in items:
            if isinstance(item, dict) and isinstance(item.get("sku"), str):
                by_sku.setdefault(item["sku"], []).append(item)
    return by_sku


def public_source_skus(manifest: dict) -> set[str]:
    found: set[str] = set()
    for relative in manifest_source_files(manifest):
        if not relative.endswith((".html", ".js", ".json")):
            continue
        text = (ROOT / relative).read_text(encoding="utf-8")
        found.update(SKU_PATTERN.findall(text))
    return found


def valid_verified_at(value: object) -> bool:
    if not isinstance(value, str) or not value:
        return False
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return False
    return parsed.tzinfo is not None


def readiness_blockers(manifest: dict) -> list[str]:
    blockers: list[str] = []
    if manifest.get("deployment_enabled") is not True:
        blockers.append("config/pages-release.json deployment_enabled is false")

    release_skus = manifest.get("release_skus", [])
    if len(release_skus) != 1:
        blockers.append("release_skus must contain exactly one verified TEFA SKU")

    state = load_json(STATE_PATH)
    tefa = state.get("programs", {}).get("tefa", {})
    if tefa.get("evidence_status") != "verified_repository_record":
        blockers.append("TEFA company approval evidence is not a verified repository record")
    if tefa.get("public_approval_claim_allowed") is not True:
        blockers.append("the canonical state does not allow a public TEFA approval claim")

    items = catalog_items()
    if len(release_skus) == 1:
        sku = release_skus[0]
        matches = items.get(sku, [])
        if len(matches) != 1:
            blockers.append(f"release SKU {sku} must exist exactly once across catalog JSON files")
        else:
            item = matches[0]
            if item.get("public_listing_allowed") is not True:
                blockers.append(f"release SKU {sku} is not approved for a public listing")
            eligibility = item.get("funding_eligibility", {})
            if eligibility.get("tefa") != "verified_product_evidence":
                blockers.append(f"release SKU {sku} lacks verified product-specific TEFA evidence")

        source_skus = public_source_skus(manifest)
        if source_skus != {sku}:
            blockers.append(
                "public artifact sources must contain only the selected release SKU; "
                f"found {sorted(source_skus)}"
            )

    request = maybe_load_json(REQUEST_PATH)
    if request is None:
        blockers.append("config/request-intake.json is missing")
    else:
        if request.get("enabled") is not True:
            blockers.append("request intake is not enabled")
        endpoint = request.get("endpoint")
        if not isinstance(endpoint, str) or FORMSPREE_PATTERN.fullmatch(endpoint) is None:
            blockers.append("request intake lacks a valid HTTPS Formspree endpoint")

    backend = manifest.get("request_backend", {})
    if backend.get("e2e_verified") is not True:
        blockers.append("request backend end-to-end verification is not recorded")
    if backend.get("owner_notification_verified") is not True:
        blockers.append("owner request notification is not verified")
    if backend.get("customer_confirmation_verified") is not True:
        blockers.append("customer on-page confirmation is not verified")
    if not valid_verified_at(backend.get("verified_at")):
        blockers.append("request backend verified_at must be a timezone-aware ISO timestamp")
    return blockers


def inject_noindex(text: str, relative: str) -> str:
    if re.search(r'<meta\s+name=["\']robots["\']', text, re.IGNORECASE):
        raise SystemExit(f"Source already contains robots metadata; review it explicitly: {relative}")
    marker = "<head>"
    if text.count(marker) != 1:
        raise SystemExit(f"Expected one literal <head> in {relative}")
    return text.replace(marker, f"{marker}\n{NOINDEX_META}", 1)


def prepare_empty_output(output: Path) -> None:
    resolved = output.resolve()
    if resolved in {Path("/").resolve(), ROOT.resolve()}:
        raise SystemExit(f"Refusing unsafe release output: {resolved}")
    if resolved.exists():
        if not resolved.is_dir():
            raise SystemExit(f"Release output exists and is not a directory: {resolved}")
        if any(resolved.iterdir()):
            raise SystemExit(f"Release output must be absent or empty: {resolved}")
    else:
        resolved.mkdir(parents=True)


def build_artifact(manifest: dict, output: Path) -> None:
    prepare_empty_output(output)
    for relative in sorted(manifest_source_files(manifest)):
        safe_relative_path(relative)
        source = ROOT / relative
        if not source.is_file() or source.is_symlink():
            raise SystemExit(f"Allowlisted release source is missing or unsafe: {relative}")
        destination = output / relative
        destination.parent.mkdir(parents=True, exist_ok=True)
        if source.suffix == ".html":
            destination.write_text(
                inject_noindex(source.read_text(encoding="utf-8"), relative),
                encoding="utf-8",
            )
        else:
            shutil.copy2(source, destination)

    (output / "robots.txt").write_text("User-agent: *\nDisallow: /\n", encoding="utf-8")
    (output / ".nojekyll").write_bytes(b"")
    validate_artifact(output)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", required=True, type=Path, help="New or empty artifact directory")
    parser.add_argument(
        "--require-ready",
        action="store_true",
        help="Fail unless all business, SKU, and request-backend gates are satisfied",
    )
    args = parser.parse_args()

    manifest = load_json(MANIFEST_PATH)
    validate_manifest(manifest)
    blockers = readiness_blockers(manifest)
    if args.require_ready and blockers:
        raise SystemExit("Release is blocked:\n- " + "\n- ".join(blockers))

    build_artifact(manifest, args.output.resolve())
    if blockers:
        print("Artifact shape validated for CI; deployment remains blocked:")
        for blocker in blockers:
            print(f"- {blocker}")
    else:
        print("All release-readiness gates passed.")


if __name__ == "__main__":
    main()
