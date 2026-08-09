#!/usr/bin/env python3
"""Validate Preparation Station's canonical facts and product catalog."""

from __future__ import annotations

import json
import re
from html.parser import HTMLParser
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
STATE_PATH = ROOT / "config" / "project-state.json"
BOOKS_PATH = ROOT / "catalog" / "books.json"
GENERATED_HTML = [
    ROOT / "index.html",
    ROOT / "store" / "shop.html",
    ROOT / "store" / "product.html",
    ROOT / "store" / "order.html",
    ROOT / "general-store" / "shop.html",
    ROOT / "general-store" / "product.html",
    ROOT / "general-store" / "checkout.html",
]


class HtmlStructureCollector(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.ids: list[str] = []
        self.start_tags: list[str] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        self.start_tags.append(tag)
        for name, value in attrs:
            if name == "id" and value:
                self.ids.append(value)


def load_json(path: Path) -> dict:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError as exc:
        raise SystemExit(f"Missing required file: {path.relative_to(ROOT)}") from exc
    except json.JSONDecodeError as exc:
        raise SystemExit(f"Invalid JSON in {path.relative_to(ROOT)}: {exc}") from exc


def require(condition: bool, message: str) -> None:
    if not condition:
        raise SystemExit(message)


def valid_isbn(value: str) -> bool:
    digits = re.sub(r"[^0-9Xx]", "", value)
    if len(digits) == 10:
        if "X" in digits[:-1].upper():
            return False
        total = 0
        for index, character in enumerate(digits):
            number = 10 if character.upper() == "X" and index == 9 else int(character)
            total += number * (10 - index)
        return total % 11 == 0
    if len(digits) == 13 and digits.isdigit():
        total = sum(
            int(character) * (1 if index % 2 == 0 else 3)
            for index, character in enumerate(digits)
        )
        return total % 10 == 0
    return False


def validate_public_source() -> None:
    source_paths = [
        ROOT / "src" / "page.html",
        *sorted((ROOT / "store" / "src").glob("*.html")),
        *sorted((ROOT / "general-store" / "src").glob("*.html")),
    ]
    forbidden = {
        "MMM Investment": "legacy storefront brand",
        "ESA eligible": "unsupported generic product-eligibility claim",
        "$8.95": "unverified coloring-book concept price",
        "?sku=MMM-": "legacy product-link prefix",
        'data-qty-for="MMM-': "legacy cart SKU prefix",
    }
    for path in source_paths:
        text = path.read_text(encoding="utf-8")
        for needle, label in forbidden.items():
            require(
                needle not in text,
                f"{path.relative_to(ROOT)} contains {label}: {needle}",
            )


def validate_generated_html() -> None:
    forbidden = {
        "MMM Investment": "legacy storefront brand",
        "ESA eligible": "unsupported generic product-eligibility claim",
        "$8.95": "unverified coloring-book concept price",
        "?sku=MMM-": "legacy product-link prefix",
        'data-qty-for="MMM-': "legacy cart SKU prefix",
    }
    for path in GENERATED_HTML:
        text = path.read_text(encoding="utf-8")
        parser = HtmlStructureCollector()
        parser.feed(text)
        require(parser.start_tags.count("html") == 1, f"Expected one html element: {path}")
        require(parser.start_tags.count("head") == 1, f"Expected one head element: {path}")
        require(parser.start_tags.count("title") == 1, f"Expected one title element: {path}")
        require(parser.start_tags.count("body") == 1, f"Expected one body element: {path}")
        duplicates = sorted({value for value in parser.ids if parser.ids.count(value) > 1})
        require(not duplicates, f"Duplicate HTML ids in {path.relative_to(ROOT)}: {duplicates}")
        for needle, label in forbidden.items():
            require(
                needle not in text,
                f"{path.relative_to(ROOT)} contains {label}: {needle}",
            )


def validate_state(state: dict) -> None:
    require(state.get("schema_version") == 1, "Unsupported project-state schema")
    repository = state.get("repository", {})
    business = state.get("business", {})
    programs = state.get("programs", {})
    agents = state.get("agents", {})

    require(
        repository.get("current") == "TEAM-MMM01/mmm-education-storefront",
        "Current repository name changed without updating the migration record",
    )
    require(business.get("brand") == "Preparation Station", "Unexpected public brand")
    require(
        business.get("legal_operator") == "Nationwide Acquisitions, LLC",
        "Unexpected legal operator",
    )
    require(
        business.get("public_operator_disclosure")
        == "Preparation Station is operated by Nationwide Acquisitions, LLC.",
        "Operator disclosure must use the approved wording",
    )

    tefa = programs.get("tefa", {})
    pdses = programs.get("pdses_classwallet", {})
    require(tefa.get("approval_status") == "owner_confirmed", "Unexpected TEFA status")
    if tefa.get("evidence_status") != "verified_repository_record":
        require(
            tefa.get("public_approval_claim_allowed") is False,
            "TEFA public approval claim requires verified repository evidence",
        )
    require(
        pdses.get("approval_status") in {"unknown", "approved", "not_approved"},
        "Unexpected PDSES/ClassWallet status",
    )
    if pdses.get("evidence_status") != "verified_repository_record":
        require(
            pdses.get("public_approval_claim_allowed") is False,
            "PDSES public approval claim requires verified repository evidence",
        )

    required_agents = {"codex", "claude", "devin", "omniroute"}
    require(required_agents <= set(agents), "Missing required agent access record")
    for name, record in agents.items():
        require(
            record.get("write_policy")
            in {"branch_and_pull_request_only", "no_shared_repository_credential"},
            f"Unsafe write policy for {name}",
        )


def validate_books(catalog: dict) -> None:
    require(catalog.get("schema_version") == 1, "Unsupported books schema")
    require(
        catalog.get("canonical_record_owner") == "Royal Collexions",
        "Royal Collexions must own canonical book records",
    )
    items = catalog.get("items")
    require(isinstance(items, list) and items, "Book catalog must contain items")

    seen: set[str] = set()
    for item in items:
        sku = item.get("sku")
        require(isinstance(sku, str) and sku, "Every item requires a SKU")
        require(sku not in seen, f"Duplicate SKU: {sku}")
        seen.add(sku)
        require(
            set(item.get("channels", []))
            == {"preparation_station", "royal_collexions"},
            f"{sku} must retain both approved sales channels",
        )

        mode = item.get("pricing_mode")
        price = item.get("retail_price_usd")
        require(mode in {"fixed", "quote_only", "not_for_sale"}, f"Invalid pricing mode: {sku}")
        if mode == "fixed":
            require(isinstance(price, (int, float)) and price > 0, f"Fixed price missing: {sku}")
        else:
            require(price is None, f"Unverified price must be null: {sku}")

        if item.get("record_status") == "concept":
            require(item.get("public_listing_allowed") is False, f"Concept cannot be public: {sku}")
            require(mode == "not_for_sale", f"Concept cannot be priced: {sku}")

        eligibility = item.get("funding_eligibility", {})
        require("tefa" in eligibility, f"Missing TEFA status: {sku}")
        require("pdses_classwallet" in eligibility, f"Missing PDSES status: {sku}")

    vulturian = next((item for item in items if item.get("sku") == "GEN-BK-001"), None)
    require(vulturian is not None, "The Vulturian record is required")
    require(vulturian.get("title") == "The Vulturian", "The Vulturian title changed")
    require(vulturian.get("title_status") == "confirmed", "The Vulturian is a confirmed title")
    isbn_status = vulturian.get("isbn_status")
    isbn = vulturian.get("isbn")
    require(isbn_status in {"pending", "verified"}, "Invalid The Vulturian ISBN status")
    if isbn_status == "verified":
        require(isinstance(isbn, str) and valid_isbn(isbn), "Verified ISBN is invalid")
    else:
        require(isbn is None, "Pending ISBN must remain null")


def main() -> None:
    validate_state(load_json(STATE_PATH))
    validate_books(load_json(BOOKS_PATH))
    validate_public_source()
    validate_generated_html()
    print("Project state and book catalog are valid.")


if __name__ == "__main__":
    main()
