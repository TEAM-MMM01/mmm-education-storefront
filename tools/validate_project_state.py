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
TEFA_OFFERINGS_PATH = ROOT / "catalog" / "tefa-offerings.json"
PATHWAYS_PATH = ROOT / "catalog" / "pathways.json"
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
        ROOT / "catalog.html",
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
        "Orders@preparationstation.org": "unverified Orders inbox",
        "orders@preparationstation.org": "unverified Orders inbox",
    }
    for path in source_paths:
        text = path.read_text(encoding="utf-8")
        for needle, label in forbidden.items():
            require(
                needle not in text,
                f"{path.relative_to(ROOT)} contains {label}: {needle}",
            )

    catalog_source = (ROOT / "catalog.html").read_text(encoding="utf-8")
    pathways = load_json(PATHWAYS_PATH)
    pathway_items = pathways.get("items", [])
    pathway_skus = {item["sku"] for item in pathway_items}
    published_pathway_skus = set(re.findall(r"PS-[A-Z]{2}-\d{4,}", catalog_source))
    require(
        published_pathway_skus == pathway_skus,
        "Public pathway SKUs must exactly match the canonical pathway catalog",
    )
    allowed_prices = {
        f"${item['retail_price_usd']:.2f}"
        for item in load_json(BOOKS_PATH)["items"]
        if item.get("public_listing_allowed") is True and item.get("pricing_mode") == "fixed"
    }
    allowed_prices.update(f"${item['current_public_price_usd']:,}" for item in pathway_items)
    published_prices = set(re.findall(r"\$\s*\d[\d,]*(?:\.\d{2})?", catalog_source))
    require(
        published_prices <= allowed_prices,
        "catalog.html contains a public price without a canonical record",
    )
    photo_tags = re.findall(r"<img\b[^>]*\bsrc=[\"']images/photo-[^\"']+[\"'][^>]*>", catalog_source)
    require(photo_tags, "catalog.html must contain its reviewed product photography")
    require(
        all(re.search(r"\bloading=[\"']lazy[\"']", tag) for tag in photo_tags),
        "Every catalog product photo must use loading=lazy",
    )
    require(
        "The Vulturian" not in catalog_source and "GEN-BK-001" not in catalog_source,
        "The Vulturian must remain unlisted while its canonical record disallows publication",
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


def validate_pathways(catalog: dict) -> set[str]:
    require(catalog.get("schema_version") == 1, "Unsupported pathways schema")
    require(catalog.get("price_context") == "current_public_ask_not_odyssey_verified", "Pathway price context drift")
    items = catalog.get("items")
    require(isinstance(items, list) and len(items) == 4, "Expected four public pathway records")
    skus: set[str] = set()
    for item in items:
        sku = item.get("sku")
        require(isinstance(sku, str) and re.fullmatch(r"PS-[A-Z]{2}-\d{4}", sku) is not None, "Invalid pathway SKU")
        require(sku not in skus, f"Duplicate pathway SKU: {sku}")
        skus.add(sku)
        require(isinstance(item.get("current_public_price_usd"), int) and item["current_public_price_usd"] > 0, f"Missing pathway public ask: {sku}")
        pdp = ROOT / str(item.get("pdp", ""))
        require(pdp.is_file(), f"Missing pathway PDP: {sku}")
        pdp_text = pdp.read_text(encoding="utf-8")
        require(sku in pdp_text and f"${item['current_public_price_usd']:,}" in pdp_text, f"Pathway PDP facts differ: {sku}")
        require("sized to the $2,000 homeschool award" not in pdp_text, f"Award-sized pricing copy remains: {sku}")
    return skus


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

    public_catalog = (ROOT / "catalog.html").read_text(encoding="utf-8")
    for sku in seen:
        require(f"SKU: {sku}" in public_catalog, f"Public catalog is missing SKU: {sku}")
    require(
        public_catalog.count("Price: Not published") == len(seen),
        "Every fixed-kit catalog card must show its truthful unpublished price state",
    )

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
    information_link_skus = set(
        re.findall(
            r'href="\.\./products/(PS-[A-Z]{2}-\d{3})\.html"',
            (ROOT / "store" / "src" / "shop.html").read_text(encoding="utf-8"),
        )
    )
    information_link_skus.update(
        re.findall(
            r'data-request-sku="(PS-[A-Z]{2}-\d{3})"',
            (ROOT / "store" / "src" / "product.html").read_text(encoding="utf-8"),
        )
    )
    require(information_link_skus == seen, "Information links must cover every canonical SKU")
    return seen


def validate_tefa_offerings(catalog: dict, product_skus: set[str]) -> set[str]:
    """Validate the separate verified-offerings catalog.

    catalog/products.json is the fixed 18-item illustrative set and can never be
    public or verified in place. Verified, launch-eligible offerings live here so
    a record can carry public_listing_allowed:true and verified TEFA product
    evidence (what tools/build_pages_release.py requires) without breaking the
    illustrative-catalog invariants. Starts empty and scales to many verified
    SKUs over time. See docs/workflow/SKU_VERIFICATION_RUNBOOK.md.
    """
    require(catalog.get("schema_version") == 1, "Unsupported TEFA offerings schema")
    require(catalog.get("operator") == "Nationwide Acquisitions, LLC", "Unexpected TEFA offerings operator")
    require(catalog.get("storefront_brand") == "Preparation Station", "Unexpected TEFA offerings storefront")
    items = catalog.get("items")
    require(isinstance(items, list), "TEFA offerings items must be a list")

    verified: set[str] = set()
    for item in items:
        sku = item.get("sku")
        require(isinstance(sku, str) and re.fullmatch(r"PS-[A-Z]{2}-\d{3}", sku) is not None, "Invalid TEFA offering SKU")
        require(sku not in verified, f"Duplicate TEFA offering SKU: {sku}")
        require(sku in product_skus, f"Verified offering SKU must exist in the canonical product catalog: {sku}")
        verified.add(sku)
        require(isinstance(item.get("name"), str) and item["name"], f"Missing TEFA offering name: {sku}")
        # A record only belongs here once it is genuinely verified for release.
        require(item.get("public_listing_allowed") is True, f"TEFA offering must be public-listing verified: {sku}")
        require(item.get("tefa_offering_status") == "approved", f"TEFA offering must be Odyssey-approved: {sku}")
        require(bool(item.get("odyssey_offering_id")), f"Approved TEFA offering requires an Odyssey ID: {sku}")
        eligibility = item.get("funding_eligibility", {})
        require(
            eligibility.get("tefa") == "verified_product_evidence",
            f"TEFA offering must record verified product evidence: {sku}",
        )
        # Prices are set at the Odyssey offering record, not published on this
        # site; keep any recorded price non-negative when present.
        price = item.get("retail_price_usd")
        require(price is None or (isinstance(price, (int, float)) and price >= 0), f"Invalid TEFA offering price: {sku}")
        # Optional growth/profitability fields, validated only when present so the
        # schema can carry margin and time-buyback signals as the catalog grows.
        margin = item.get("target_margin_pct")
        require(margin is None or (isinstance(margin, (int, float)) and 0 <= margin <= 100), f"Invalid target margin: {sku}")
        fulfillment = item.get("fulfillment_mode")
        require(
            fulfillment in {None, "digital_zero_marginal", "physical_kit", "made_to_order", "dropship"},
            f"Invalid fulfillment mode: {sku}",
        )
    return verified


def validate_request_config(config: dict, state: dict, known_skus: set[str]) -> None:
    allowed_keys = {
        "schema_version",
        "provider",
        "enabled",
        "endpoint",
        "turnstile_sitekey",
        "support_email",
        "retention_days",
        "allowed_skus",
        "allowed_submission_fields",
    }
    require(set(config) == allowed_keys, "Unexpected request-intake configuration keys")
    require(config.get("schema_version") == 1, "Unsupported request-intake schema")
    require(config.get("provider") == "cloudflare-worker", "Unexpected request-intake provider")
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
        "age_band",
        "client_reference",
        "email",
        "goal",
        "grade_band",
        "interest",
        "learner_count",
        "message",
        "organization",
        "purchase_path",
        "source",
        "submitted_at",
        "timeline",
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
    sitekey = config.get("turnstile_sitekey")
    require(isinstance(sitekey, str), "Request-intake Turnstile sitekey must be a string")
    require("secret" not in sitekey.lower(), "Turnstile secret must not appear in request-intake.json")
    if endpoint:
        require(
            re.fullmatch(r"https://[A-Za-z0-9.-]+(?:/.*)?", endpoint) is not None,
            "Request-intake endpoint must be a current HTTPS Worker endpoint",
        )
    if config.get("enabled"):
        require(bool(endpoint), "Enabled request intake requires a Worker endpoint")
        require(bool(sitekey), "Enabled request intake requires a public Turnstile sitekey")


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


def validate_public_contact_intake(config: dict) -> None:
    source = (ROOT / "src" / "info" / "contact.html").read_text(encoding="utf-8")
    generated = (ROOT / "contact.html").read_text(encoding="utf-8")
    worker = (ROOT / "workers" / "preparation-station-intake" / "src" / "index.js").read_text(encoding="utf-8")
    require('data-request-intake="__INTAKE_STATE__"' in source, "Contact source must bake intake state from config")
    require("x-intake-secret" not in source, "Contact source must not send x-intake-secret")
    require("x-intake-secret" not in generated, "Generated contact page must not send x-intake-secret")
    require("INTAKE_SHARED_SECRET" not in worker, "Worker must not require a browser-shared intake secret")
    require("TURNSTILE_SECRET_KEY" in worker, "Worker must verify Turnstile with a server-only secret")
    privacy = "Do not include student records, health information, payment details, or program-account credentials."
    success = "Request received. We'll reply within one business day with best-fit options, current status, and the correct purchase path."
    failure = "We could not send your request right now. Please try again shortly. If the issue continues, use the support contact listed below."
    require(privacy in source, "Contact source is missing the required privacy copy")
    require(success in source, "Contact source is missing the required success copy")
    require(failure in source, "Contact source is missing the required failure copy")
    expected_state = "enabled" if config.get("enabled") else "disabled"
    require(
        f'data-request-intake="{expected_state}"' in generated,
        "Generated contact forms must match request-intake enabled flag",
    )
    if not config.get("enabled"):
        require('data-intake-endpoint=""' in generated, "Disabled intake must not publish a Worker endpoint")
        require('data-turnstile-sitekey=""' in generated, "Disabled intake must not publish a Turnstile sitekey")


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
    pathway_skus = validate_pathways(load_json(PATHWAYS_PATH))
    product_skus = validate_products(load_json(PRODUCTS_PATH))
    verified_skus = validate_tefa_offerings(load_json(TEFA_OFFERINGS_PATH), product_skus)
    known_skus = product_skus | pathway_skus | verified_skus
    request_config = load_json(REQUEST_CONFIG_PATH)
    validate_request_config(request_config, state, known_skus)
    validate_request_form()
    validate_public_contact_intake(request_config)
    validate_order_portal(load_json(ORDER_PORTAL_CONFIG_PATH), known_skus)
    validate_public_source()
    validate_generated_html()
    print("Project state, catalogs, request intake, and order portal are valid.")


if __name__ == "__main__":
    main()
