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
PRODUCTS_PATH = ROOT / "catalog" / "products.json"
REQUEST_CONFIG_PATH = ROOT / "config" / "request-intake.json"
ORDER_PORTAL_CONFIG_PATH = ROOT / "config" / "order-portal.json"
ORDER_SCHEMA_PATH = ROOT / "schemas" / "order-record.schema.json"
GENERATED_HTML = [
    ROOT / "index.html",
    ROOT / "store" / "shop.html",
    ROOT / "store" / "product.html",
    ROOT / "store" / "order.html",
    ROOT / "store" / "track.html",
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
        "Carbon-neutral": "unsupported carbon-neutral claim",
        "carbon-neutral": "unsupported carbon-neutral claim",
        "Free shipping": "unsupported free-shipping claim",
        "% of every order": "unsupported environmental sales claim",
        "fixed share": "unsupported environmental sales claim",
        "carbon reinvested": "unsupported environmental sales claim",
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
        "Carbon-neutral": "unsupported carbon-neutral claim",
        "carbon-neutral": "unsupported carbon-neutral claim",
        "Free shipping": "unsupported free-shipping claim",
        "% of every order": "unsupported environmental sales claim",
        "fixed share": "unsupported environmental sales claim",
        "carbon reinvested": "unsupported environmental sales claim",
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
    require(tefa.get("approval_status") == "approved", "Unexpected TEFA status")
    require(
        tefa.get("approved_entity") == "Nationwide Acquisitions, LLC",
        "TEFA approval must remain attached to the legal entity",
    )
    require(
        tefa.get("evidence_status") == "owner_provided_approval_email",
        "TEFA vendor evidence reference changed",
    )
    require(
        tefa.get("public_approval_claim_allowed") is True,
        "Approved TEFA vendor claim should be publishable",
    )
    require(
        tefa.get("product_specific_eligibility_required") is True,
        "TEFA offerings must retain separate product review",
    )
    require(
        tefa.get("funded_purchase_system") == "Odyssey Marketplace",
        "TEFA funded purchases must remain in Odyssey",
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


def validate_products(catalog: dict) -> set[str]:
    require(catalog.get("schema_version") == 1, "Unsupported products schema")
    require(catalog.get("operator") == "Nationwide Acquisitions, LLC", "Unexpected product operator")
    require(catalog.get("storefront_brand") == "Preparation Station", "Unexpected product storefront")
    items = catalog.get("items")
    require(isinstance(items, list) and len(items) == 18, "Expected all 18 starter product records")

    seen: set[str] = set()
    for item in items:
        sku = item.get("sku")
        require(isinstance(sku, str) and re.fullmatch(r"PS-[A-Z]{2}-\d{3}", sku) is not None, "Invalid product SKU")
        require(sku not in seen, f"Duplicate product SKU: {sku}")
        seen.add(sku)
        require(isinstance(item.get("name"), str) and item["name"], f"Missing product name: {sku}")
        require(item.get("public_listing_allowed") is False, f"Unverified product cannot be public: {sku}")
        require(item.get("price_status") == "illustrative_unverified", f"Unexpected price status: {sku}")
        require(item.get("retail_price_usd") is None, f"Unverified public price must be null: {sku}")
        require(item.get("fulfillment_status") == "unknown", f"Unverified fulfillment status: {sku}")
        require(
            item.get("tefa_offering_status")
            in {"not_submitted_or_unknown", "submitted", "approved", "rejected", "archived"},
            f"Invalid Odyssey offering status: {sku}",
        )
        if item.get("tefa_offering_status") == "approved":
            require(bool(item.get("odyssey_offering_id")), f"Approved TEFA offering requires Odyssey ID: {sku}")
        require(item.get("direct_purchase_status") == "disabled", f"Direct purchase enabled without launch facts: {sku}")

    cart_source = (ROOT / "store" / "cart.js").read_text(encoding="utf-8")
    cart_skus = set(re.findall(r"'(PS-[A-Z]{2}-\d{3})':\s*\{", cart_source))
    require(seen == cart_skus, "Canonical products and storefront cart SKUs differ")
    require(
        re.search(r"'PS-[A-Z]{2}-\d{3}':\s*\{[^\n]*price:\s*\d", cart_source) is None,
        "Unverified numeric product price remains in the funded cart",
    )
    for path in [ROOT / "src" / "page.html", ROOT / "store" / "src" / "shop.html", ROOT / "store" / "src" / "product.html"]:
        text = path.read_text(encoding="utf-8")
        require(re.search(r"\$\d+\.\d{2}", text) is None, f"Unverified public price in {path.relative_to(ROOT)}")
        require("data-add-to-cart" not in text, f"Unverified product is addable in {path.relative_to(ROOT)}")
    request_button_skus = set(
        re.findall(
            r'data-request-sku="(PS-[A-Z]{2}-\d{3})"',
            (ROOT / "store" / "src" / "shop.html").read_text(encoding="utf-8"),
        )
    )
    request_button_skus.update(
        re.findall(
            r'data-request-sku="(PS-[A-Z]{2}-\d{3})"',
            (ROOT / "store" / "src" / "product.html").read_text(encoding="utf-8"),
        )
    )
    require(request_button_skus == seen, "Information-request controls must cover every canonical SKU")
    return seen


def validate_request_config(config: dict, state: dict, known_skus: set[str]) -> None:
    allowed_keys = {
        "schema_version",
        "provider",
        "enabled",
        "endpoint",
        "support_email",
        "retention_days",
        "allowed_skus",
        "allowed_submission_fields",
    }
    require(set(config) == allowed_keys, "Unexpected request-intake configuration keys")
    require(config.get("schema_version") == 1, "Unsupported request-intake schema")
    require(config.get("provider") == "formspree", "Unexpected request-intake provider")
    require(isinstance(config.get("enabled"), bool), "Request-intake enabled flag must be boolean")
    require(
        config.get("support_email") == state.get("business", {}).get("support_email"),
        "Request-intake support email must match canonical project state",
    )
    retention_days = config.get("retention_days")
    require(
        isinstance(retention_days, int) and 1 <= retention_days <= 90,
        "Request-intake retention must be between 1 and 90 days",
    )
    expected_fields = {
        "_gotcha",
        "adult_name",
        "cart_items",
        "client_reference",
        "email",
        "internal_owner",
        "notes",
        "program",
        "source",
        "submitted_at",
    }
    fields = config.get("allowed_submission_fields")
    require(isinstance(fields, list), "Request-intake field allowlist must be a list")
    require(set(fields) == expected_fields, "Request-intake field allowlist changed")
    require(len(fields) == len(expected_fields), "Request-intake field allowlist has duplicates")

    require(known_skus, "Could not identify request catalog SKUs")
    allowed_skus = config.get("allowed_skus")
    require(isinstance(allowed_skus, list), "Request-intake allowed SKUs must be a list")
    require(len(allowed_skus) == len(set(allowed_skus)), "Request-intake allowed SKUs have duplicates")
    require(
        all(isinstance(sku, str) and sku in known_skus for sku in allowed_skus),
        "Request-intake allowed SKUs must exist in the request catalog",
    )

    endpoint = config.get("endpoint")
    require(isinstance(endpoint, str), "Request-intake endpoint must be a string")
    if endpoint:
        require(
            re.fullmatch(r"https://formspree\.io/f/[A-Za-z0-9_-]+/?", endpoint) is not None,
            "Request-intake endpoint must be a current HTTPS Formspree form endpoint",
        )
    if config.get("enabled"):
        require(bool(endpoint), "Enabled request intake requires a Formspree endpoint")
        require(bool(allowed_skus), "Enabled request intake requires at least one allowed SKU")


def validate_request_form() -> None:
    source = (ROOT / "store" / "src" / "order.html").read_text(encoding="utf-8")
    form_match = re.search(r'<form id="quote-form"(?P<body>.*?)</form>', source, re.DOTALL)
    require(form_match is not None, "Quote request form is missing")
    form = form_match.group(0)
    require(" action=" not in form, "Quote request form must not have an unreviewed action")
    require(
        'id="quote-submit"' in form and " disabled" in form,
        "Quote request submit button must be disabled by default",
    )
    forbidden = {
        'type="file"': "file upload",
        'type="tel"': "phone collection",
        'name="student': "student field",
        'name="child': "child field",
        'name="school': "school field",
        'name="ssn': "Social Security field",
        'name="account': "account field",
        'name="payment': "payment field",
    }
    for needle, label in forbidden.items():
        require(needle not in form.lower(), f"Quote request form contains forbidden {label}")


def validate_order_portal(config: dict, known_skus: set[str]) -> None:
    require(config.get("schema_version") == 1, "Unsupported order-portal schema")
    require(config.get("provider") == "api_adapter", "Unexpected order-portal provider")
    require(config.get("authentication") == "email_magic_link", "Unsafe order authentication")
    require(
        set(config.get("customer_visible_sources", [])) == {"tefa_odyssey", "direct_site"},
        "Order portal must keep both approved order sources",
    )

    tefa = config.get("tefa", {})
    require(tefa.get("purchase_system") == "odyssey_marketplace", "TEFA purchase system changed")
    require(tefa.get("order_history_authority") == "odyssey", "Odyssey must remain TEFA history authority")
    require(
        tefa.get("preparation_station_role") == "fulfillment_status_mirror",
        "Preparation Station must not become a second TEFA checkout",
    )
    require(
        tefa.get("sync_mode") == "manual_or_approved_export_until_api_available",
        "Unapproved automatic Odyssey sync configured",
    )
    require(
        isinstance(tefa.get("family_order_help_url"), str)
        and tefa["family_order_help_url"].startswith("https://support.withodyssey.com/"),
        "TEFA family order help must use Odyssey support",
    )

    privacy = config.get("privacy", {})
    require(privacy.get("public_order_lookup_allowed") is False, "Public order lookup is unsafe")
    require(privacy.get("store_order_data_in_browser") is False, "Order data cannot be stored in the browser")
    require(privacy.get("child_data_allowed") is False, "Child data is forbidden in the order portal")

    direct = config.get("direct_commerce", {})
    require(direct.get("provider") == "stripe_checkout", "Unexpected direct-payment provider")
    require(direct.get("webhook_required") is True, "Direct orders require a verified payment webhook")
    allowed_skus = direct.get("allowed_skus")
    payment_links = direct.get("payment_links")
    require(isinstance(allowed_skus, list), "Direct-commerce SKU allowlist must be a list")
    require(len(allowed_skus) == len(set(allowed_skus)), "Direct-commerce SKU allowlist has duplicates")
    require(set(allowed_skus) <= known_skus, "Direct-commerce allowlist contains an unknown SKU")
    require(isinstance(payment_links, dict), "Direct-commerce payment links must be a map")
    require(set(payment_links) == set(allowed_skus), "Every direct SKU needs exactly one payment link")
    for sku, link in payment_links.items():
        require(re.fullmatch(r"https://buy\.stripe\.com/[A-Za-z0-9_-]+", link) is not None, f"Invalid payment link for {sku}")
    if direct.get("enabled"):
        require(bool(allowed_skus), "Enabled direct checkout needs a verified SKU")

    enabled = config.get("enabled")
    require(isinstance(enabled, bool), "Order-portal enabled flag must be boolean")
    api_base_url = config.get("api_base_url")
    require(isinstance(api_base_url, str), "Order-portal API URL must be a string")
    if enabled:
        require(re.fullmatch(r"https://[^\s/]+(?:/[^\s]*)?", api_base_url) is not None, "Enabled order portal requires HTTPS API")

    schema = load_json(ORDER_SCHEMA_PATH)
    require(schema.get("additionalProperties") is False, "Order records must reject undeclared fields")
    require(set(schema.get("properties", {}).get("source", {}).get("enum", [])) == {"tefa_odyssey", "direct_site"}, "Order schema source drift")
    require("customer_id" in schema.get("required", []), "Order records require customer authorization")

    source = (ROOT / "store" / "src" / "track.html").read_text(encoding="utf-8")
    require("Odyssey Marketplace" in source, "Order page must preserve the TEFA purchase boundary")
    require("not live yet" in source, "Track page must state that secure tracking is not live yet")
    require("Ask about an order by email" in source, "Track page must offer the email fallback")
    require("order-access-submit" not in source, "Removed disabled submit must stay removed (no fake buttons)")


def main() -> None:
    state = load_json(STATE_PATH)
    validate_state(state)
    validate_books(load_json(BOOKS_PATH))
    known_skus = validate_products(load_json(PRODUCTS_PATH))
    validate_request_config(load_json(REQUEST_CONFIG_PATH), state, known_skus)
    validate_request_form()
    validate_order_portal(load_json(ORDER_PORTAL_CONFIG_PATH), known_skus)
    validate_public_source()
    validate_generated_html()
    print("Project state, catalogs, request intake, and order portal are valid.")


if __name__ == "__main__":
    main()
