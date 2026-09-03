#!/usr/bin/env python3
"""Apply PR 73 public catalog fixes on a checkout. Safe to re-run."""
from __future__ import annotations

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ODYSSEY = "https://support.withodyssey.com/hc/en-us/articles/51195311077019-How-to-Use-the-Odyssey-Marketplace"
FINDER = "https://finder.educationfreedom.texas.gov/"


def sub_once(text: str, old: str, new: str, label: str) -> str:
    if old not in text:
        raise SystemExit(f"missing pattern: {label}")
    return text.replace(old, new, 1)


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
        t = sub_once(
            t,
            """    <div class=\"hero__actions\">
      <a class=\"btn btn--primary\" href=\"#d01\">Browse catalog references</a>
      <a class=\"btn btn--outline\" href=\"contact.html?topic=catalog\">Start a request</a>
      <button type=\"button\" class=\"btn btn--outline\" onclick=\"navigator.clipboard.writeText('https://preparationstation.org/catalog').then(()=>{this.textContent='Catalog URL copied'})\">Copy catalog URL</button>
    </div>""",
            f"""    <div class=\"hero__actions\">
      <a class=\"btn btn--primary\" href=\"#d01\">Browse catalog references</a>
      <a class=\"btn btn--outline\" href=\"contact.html?topic=catalog\">Start a request</a>
      <a class=\"btn btn--outline\" href=\"{ODYSSEY}\" rel=\"noopener noreferrer\" target=\"_blank\">How to buy in Odyssey</a>
      <a class=\"btn btn--outline\" href=\"{FINDER}\" rel=\"noopener noreferrer\" target=\"_blank\">TEFA Vendor Finder</a>
      <button type=\"button\" class=\"btn btn--outline\" onclick=\"navigator.clipboard.writeText('https://preparationstation.org/catalog').then(()=>{{this.textContent='Catalog URL copied'}})\">Copy catalog URL</button>
    </div>""",
            "catalog hero actions",
        )
    if "PS-HS-503" in t or "Daily Supply Restock Box" in t:
        raise SystemExit("catalog still names HS-503")
    catalog.write_text(t, encoding="utf-8")

    validate = ROOT / "tools" / "validate_project_state.py"
    vt = validate.read_text(encoding="utf-8")
    old = """    public_catalog = (ROOT / \"catalog.html\").read_text(encoding=\"utf-8\")
    for sku in seen:
        require(f\"SKU: {sku}\" in public_catalog, f\"Public catalog is missing SKU: {sku}\")
    require(
        public_catalog.count(\"Price: Not published\") == len(seen),
        \"Every fixed-kit catalog card must show its truthful unpublished price state\",
    )"""
    new = """    public_catalog = (ROOT / \"catalog.html\").read_text(encoding=\"utf-8\")
    require(\"PS-HS-503\" not in public_catalog, \"PS-HS-503 must be absent from the public catalog\")
    require(\"Daily Supply Restock Box\" not in public_catalog, \"Daily Supply Restock Box must not appear on /catalog\")
    public_skus = seen - {\"PS-HS-503\"}
    for sku in public_skus:
        require(f\"SKU: {sku}\" in public_catalog, f\"Public catalog is missing SKU: {sku}\")
    require(
        public_catalog.count(\"Price: Not published\") == len(public_skus),
        \"Every public fixed-kit catalog card must show its truthful unpublished price state\",
    )"""
    if old in vt:
        validate.write_text(vt.replace(old, new), encoding="utf-8")

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
        note = """        <p class=\"g-note\" style=\"margin-top:.8rem\">No payment is collected on this site. TEFA
          purchases and official order history stay in Odyssey.</p>"""
        links = f"""        <p class=\"g-note\" style=\"margin-top:.8rem\">No payment is collected on this site. TEFA
          purchases and official order history stay in Odyssey.</p>
        <p style=\"margin-top:.7rem\"><a href=\"{ODYSSEY}\" rel=\"noopener noreferrer\" target=\"_blank\">How to buy in the Odyssey Marketplace</a> · <a href=\"{FINDER}\" rel=\"noopener noreferrer\" target=\"_blank\">Official TEFA Vendor Finder</a></p>"""
        if ODYSSEY not in t:
            t = sub_once(t, note, links, f"{path} four-step")
        p.write_text(t, encoding="utf-8")

    for path in ["src/info/tefa.html", "tefa.html"]:
        p = ROOT / path
        t = p.read_text(encoding="utf-8")
        old_steps = """        <li><strong>Purchase in Odyssey</strong> only after that exact SKU is listed as available. Vendor approval is not item approval.</li>
      </ol>
    </div>"""
        new_steps = f"""        <li><strong>Purchase in Odyssey</strong> only after that exact SKU is listed as available. Vendor approval is not item approval.</li>
      </ol>
      <p style=\"margin-top:1rem\"><a href=\"{ODYSSEY}\" rel=\"noopener noreferrer\" target=\"_blank\">How to buy in the Odyssey Marketplace</a> · <a href=\"{FINDER}\" rel=\"noopener noreferrer\" target=\"_blank\">Official TEFA Vendor Finder</a></p>
    </div>"""
        if ODYSSEY not in t:
            t = sub_once(t, old_steps, new_steps, f"{path} steps")
        t = t.replace(
            "PS-HS-501 remains Core Subjects Workbook Set; no unverified title swap is published.",
            "The consumable restock SKU is excluded from /catalog. PS-HS-501 is published as Weekly Evidence Binder. Kit prices are not published.",
        )
        p.write_text(t, encoding="utf-8")

    for path in ["src/info/contact.html", "contact.html"]:
        p = ROOT / path
        t = p.read_text(encoding="utf-8")
        old_c = """        <p>For TEFA, purchase only offerings shown as available in the official Odyssey
          Marketplace. <a href=\"tefa.html\">See funding help &amp; eligibility</a>.</p>"""
        new_c = f"""        <p>For TEFA, purchase only offerings shown as available in the official Odyssey
          Marketplace. <a href=\"tefa.html\">See funding help &amp; eligibility</a>.</p>
        <p style=\"margin-top:.75rem\"><a href=\"{ODYSSEY}\" rel=\"noopener noreferrer\" target=\"_blank\">How to buy in the Odyssey Marketplace</a> · <a href=\"{FINDER}\" rel=\"noopener noreferrer\" target=\"_blank\">Official TEFA Vendor Finder</a></p>"""
        if ODYSSEY not in t:
            t = sub_once(t, old_c, new_c, f"{path} contact")
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
