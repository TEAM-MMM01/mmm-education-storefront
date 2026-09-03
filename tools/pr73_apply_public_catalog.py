#!/usr/bin/env python3
"""Apply PR 73 public catalog fixes on a checkout. Safe to re-run."""
from __future__ import annotations

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ODYSSEY = "https://support.withodyssey.com/hc/en-us/articles/51195311077019-How-to-Use-the-Odyssey-Marketplace"
FINDER = "https://finder.educationfreedom.texas.gov/"
LINK_HTML = (
    f'<a href="{ODYSSEY}" rel="noopener noreferrer" target="_blank">How to buy in the Odyssey Marketplace</a>'
    f' · <a href="{FINDER}" rel="noopener noreferrer" target="_blank">Official TEFA Vendor Finder</a>'
)


def insert_after(text: str, anchor: str, insertion: str) -> str:
    if insertion.strip()[:40] in text:
        return text
    if anchor not in text:
        raise SystemExit(f"missing anchor: {anchor[:80]}")
    return text.replace(anchor, anchor + insertion, 1)


def main() -> None:
    catalog = ROOT / "catalog.html"
    t = catalog.read_text(encoding="utf-8")
    t = re.sub(
        r'\n      <div class="product-card"><a class="product-card__hit" href="products/PS-HS-503.html".*?</div>\n        </div>\n      </div>',
        "",
        t,
        count=1,
        flags=re.S,
    )
    t = t.replace("Core Subjects Workbook Set", "Weekly Evidence Binder")
    t = t.replace(
        "Comprehensive workbook set covering core subjects for structured learning.",
        "Weekly evidence binder for work samples, attendance notes, and homeschool documentation.",
    )
    t = t.replace(
        "4 items · Core workbooks, assessment, supply restock, art and craft foundations.",
        "3 items · Weekly evidence binder, assessment, and art and craft foundations. Consumable restock is not listed.",
    )
    t = t.replace(
        "These four digital curriculum pathways are separate from the 18 fixed-kit references below.",
        "These four digital curriculum pathways are separate from the kit references below. One previously planned consumable-restock SKU is not listed.",
    )
    if "How to buy in Odyssey" not in t:
        needle = '<a class="btn btn--outline" href="contact.html?topic=catalog">Start a request</a>'
        extra = (
            f'\n      <a class="btn btn--outline" href="{ODYSSEY}" rel="noopener noreferrer" target="_blank">How to buy in Odyssey</a>'
            f'\n      <a class="btn btn--outline" href="{FINDER}" rel="noopener noreferrer" target="_blank">TEFA Vendor Finder</a>'
        )
        t = insert_after(t, needle, extra)
    if "PS-HS-503" in t or "Daily Supply Restock Box" in t:
        raise SystemExit("catalog still names HS-503")
    catalog.write_text(t, encoding="utf-8")

    validate = ROOT / "tools" / "validate_project_state.py"
    vt = validate.read_text(encoding="utf-8")
    if "PS-HS-503 must be absent from the public catalog" not in vt:
        vt = vt.replace(
            "    public_catalog = (ROOT / \"catalog.html\").read_text(encoding=\"utf-8\")\n    for sku in seen:",
            "    public_catalog = (ROOT / \"catalog.html\").read_text(encoding=\"utf-8\")\n"
            "    require(\"PS-HS-503\" not in public_catalog, \"PS-HS-503 must be absent from the public catalog\")\n"
            "    require(\"Daily Supply Restock Box\" not in public_catalog, \"Daily Supply Restock Box must not appear on /catalog\")\n"
            "    public_skus = seen - {\"PS-HS-503\"}\n    for sku in public_skus:",
        )
        vt = vt.replace("len(seen)", "len(public_skus)", 1)
        vt = vt.replace(
            "Every fixed-kit catalog card must show its truthful unpublished price state",
            "Every public fixed-kit catalog card must show its truthful unpublished price state",
        )
        validate.write_text(vt, encoding="utf-8")

    for path in ["src/page.html", "index.html"]:
        p = ROOT / path
        t = p.read_text(encoding="utf-8")
        t = t.replace("Core Subjects Workbook Set", "Weekly Evidence Binder")
        t = t.replace(
            "Core subjects workbook set, assessment and portfolio kit, daily supply restock box, art and craft foundations.",
            "Weekly evidence binder, assessment and portfolio kit, and art and craft foundations.",
        )
        t = t.replace("Explore five departments and 18 items.", "Explore five departments and the catalog listings.")
        t = t.replace("All 18 catalog items are under offering review.", "Catalog kits remain under offering review.")
        t = t.replace("a.href='products/'+it.sku+'.html'", "a.href='catalog.html'")
        if "4 items · under review" in t and "Weekly evidence binder, assessment and portfolio kit" in t:
            t = t.replace("4 items · under review", "3 items · under review", 1)
        if ODYSSEY not in t:
            t = insert_after(
                t,
                "purchases and official order history stay in Odyssey.</p>",
                f'\n        <p style="margin-top:.7rem">{LINK_HTML}</p>',
            )
        p.write_text(t, encoding="utf-8")

    for path in ["src/info/tefa.html", "tefa.html"]:
        p = ROOT / path
        t = p.read_text(encoding="utf-8")
        if ODYSSEY not in t:
            t = insert_after(
                t,
                "Vendor approval is not item approval.</li>\n      </ol>",
                f'\n      <p style="margin-top:1rem">{LINK_HTML}</p>',
            )
        t = t.replace(
            "PS-HS-501 remains Core Subjects Workbook Set; no unverified title swap is published.",
            "The consumable restock SKU is excluded from /catalog. PS-HS-501 is published as Weekly Evidence Binder. Kit prices are not published.",
        )
        p.write_text(t, encoding="utf-8")

    for path in ["src/info/contact.html", "contact.html"]:
        p = ROOT / path
        t = p.read_text(encoding="utf-8")
        if ODYSSEY not in t:
            t = insert_after(
                t,
                '<a href="tefa.html">See funding help & eligibility</a>.</p>',
                f'\n        <p style="margin-top:.75rem">{LINK_HTML}</p>',
            )
        p.write_text(t, encoding="utf-8")

    for path in ["src/info/shop-by-age.html", "shop-by-age.html"]:
        p = ROOT / path
        t = p.read_text(encoding="utf-8")
        t = t.replace("Core Subjects Workbook Set", "Weekly Evidence Binder")
        t = t.replace(
            "Comprehensive workbook set covering core subjects for structured learning.",
            "Weekly evidence binder for work samples, attendance notes, and homeschool documentation.",
        )
        t = re.sub(r"\n        <div[^>]*>[\s\S]{0,900}?PS-HS-503[\s\S]{0,500}?</div>\s*</div>\s*</div>", "", t)
        t = re.sub(
            r'\n      <div class="product-card"[^>]*>\s*<div[^>]*>\s*<img[^>]*alt="Daily Supply Restock Box"[^>]*>\s*</div>(?:\s*</div>)?',
            "",
            t,
        )
        p.write_text(t, encoding="utf-8")

    pdp = ROOT / "products" / "PS-HS-501.html"
    pdp.write_text(pdp.read_text(encoding="utf-8").replace("Core Subjects Workbook Set", "Weekly Evidence Binder"), encoding="utf-8")

    shop = ROOT / "store" / "src" / "shop.html"
    shop.write_text(shop.read_text(encoding="utf-8").replace("Core Subjects Workbook Set", "Weekly Evidence Binder"), encoding="utf-8")

    pricing = ROOT / "PRICING.md"
    pricing.write_text(
        pricing.read_text(encoding="utf-8").replace(
            "| PS-HS-501 | Core Subjects Workbook Set |",
            "| PS-HS-501 | Weekly Evidence Binder |",
        ),
        encoding="utf-8",
    )

    print("pr73 public catalog fixes applied")


if __name__ == "__main__":
    main()
