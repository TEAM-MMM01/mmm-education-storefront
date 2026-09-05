#!/usr/bin/env python3
"""One-shot catalog cleanup for PR 80. Safe to re-run."""

from __future__ import annotations

import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

ODYSSEY_HOWTO = "https://support.withodyssey.com/hc/en-us/articles/51195311077019-How-to-Use-the-Odyssey-Marketplace"
ODYSSEY_FINDER = "https://finder.educationfreedom.texas.gov/"
ODYSSEY_P = (
    f'<p style="margin-top:.75rem"><a href="{ODYSSEY_HOWTO}" rel="noopener noreferrer" target="_blank">'
    "How to buy in the Odyssey Marketplace</a> · "
    f'<a href="{ODYSSEY_FINDER}" rel="noopener noreferrer" target="_blank">'
    "Official TEFA Vendor Finder</a></p>"
)
HOME_ODYSSEY_P = (
    f'<p style="margin-top:.7rem"><a href="{ODYSSEY_HOWTO}" rel="noopener noreferrer" target="_blank">'
    "How to buy in the Odyssey Marketplace</a> · "
    f'<a href="{ODYSSEY_FINDER}" rel="noopener noreferrer" target="_blank">'
    "Official TEFA Vendor Finder</a></p>"
)


def replace_all(path: Path, old: str, new: str) -> bool:
    text = path.read_text(encoding="utf-8")
    if old == new:
        return False
    if old not in text:
        return False
    path.write_text(text.replace(old, new), encoding="utf-8")
    print(f"updated {path.relative_to(ROOT)}")
    return True


def ensure_contains(path: Path, needle: str, insert_after: str | None = None) -> None:
    text = path.read_text(encoding="utf-8")
    if needle in text:
        return
    if insert_after and insert_after in text:
        path.write_text(text.replace(insert_after, insert_after + "\n" + needle, 1), encoding="utf-8")
        print(f"inserted into {path.relative_to(ROOT)}")
        return
    raise SystemExit(f"Could not insert into {path}")


def strip_hs503_cards(path: Path) -> None:
    text = path.read_text(encoding="utf-8")
    pattern = re.compile(
        r'<div class="product-card"[\s\S]*?PS-HS-503[\s\S]*?</div>\s*</div>\s*</div>',
        re.MULTILINE,
    )
    new, n = pattern.subn("", text)
    if n:
        path.write_text(new, encoding="utf-8")
        print(f"removed {n} HS-503 card(s) from {path.relative_to(ROOT)}")


def main() -> int:
    replace_all(ROOT / "store/cart.js", "Core Subjects Workbook Set", "Weekly Evidence Binder")
    replace_all(ROOT / "PRICING.md", "| PS-HS-501 | Core Subjects Workbook Set |", "| PS-HS-501 | Weekly Evidence Binder |")
    replace_all(ROOT / "src/data/site-catalog.json", '"title": "Core Subjects Workbook Set"', '"title": "Weekly Evidence Binder"')
    replace_all(
        ROOT / "src/data/site-catalog.json",
        '"purpose": "Core-subject workbook practice for homeschool planning."',
        '"purpose": "Weekly evidence binder for work samples, attendance notes, and homeschool documentation."',
    )
    replace_all(
        ROOT / "tools/gen_site_catalog_json.py",
        '("PS-HS-501", "Core Subjects Workbook Set", "Homeschool Essentials", "d05", "Ages 3–12", "images/core-subjects-workbook-set.svg", "Core-subject workbook practice for homeschool planning.", "organization"),',
        '("PS-HS-501", "Weekly Evidence Binder", "Homeschool Essentials", "d05", "Ages 3–12", "images/core-subjects-workbook-set.svg", "Weekly evidence binder for work samples, attendance notes, and homeschool documentation.", "organization"),',
    )

    builder = ROOT / "tools/build_site_catalog.py"
    replace_all(
        builder,
        'if sku == "GEN-BK-001" or item.get("title") == "The Vulturian":',
        'if sku in {"GEN-BK-001", "PS-HS-503"} or item.get("title") in {"The Vulturian", "Daily Supply Restock Box"}:',
    )
    if "How to buy in Odyssey" not in builder.read_text(encoding="utf-8"):
        replace_all(
            builder,
            '    <a class="btn btn--outline" href="contact.html">Request a written pathway recommendation</a>\n  </div>',
            '    <a class="btn btn--outline" href="contact.html">Request a written pathway recommendation</a>\n'
            f'    <a class="btn btn--outline" href="{ODYSSEY_HOWTO}" rel="noopener noreferrer" target="_blank">How to buy in Odyssey</a>\n'
            f'    <a class="btn btn--outline" href="{ODYSSEY_FINDER}" rel="noopener noreferrer" target="_blank">TEFA Vendor Finder</a>\n  </div>',
        )

    validator = ROOT / "tools/validate_project_state.py"
    text = validator.read_text(encoding="utf-8")
    if 'require("PS-HS-503" not in public_catalog' not in text:
        text = text.replace(
            "    public_catalog = (ROOT / \"catalog.html\").read_text(encoding=\"utf-8\")\n    for sku in seen:",
            "    public_catalog = (ROOT / \"catalog.html\").read_text(encoding=\"utf-8\")\n"
            "    require(\"PS-HS-503\" not in public_catalog, \"PS-HS-503 must be absent from the public catalog\")\n"
            "    require(\"Daily Supply Restock Box\" not in public_catalog, \"Daily Supply Restock Box must not appear on /catalog\")\n"
            "    public_skus = seen - {\"PS-HS-503\"}\n"
            "    for sku in public_skus:",
        )
        text = text.replace(
            "        public_catalog.count(\"Price: Not published\") == len(seen),\n"
            "        \"Every fixed-kit catalog card must show its truthful unpublished price state\",",
            "        public_catalog.count(\"Price: Not published\") == len(public_skus),\n"
            "        \"Every public fixed-kit catalog card must show its truthful unpublished price state\",",
        )
        validator.write_text(text, encoding="utf-8")
        print("updated tools/validate_project_state.py")

    page = ROOT / "src/page.html"
    replace_all(page, "Core Subjects Workbook Set", "Weekly Evidence Binder")
    replace_all(
        page,
        "Families still need the award math and the other products in one place.",
        "Families still need the catalog records and the other products in one place.",
    )
    replace_all(
        page,
        "a.href='products/'+it.sku+'.html'",
        "a.href='catalog.html'",
    )
    ensure_contains(
        page,
        HOME_ODYSSEY_P,
        insert_after="          purchases and official order history stay in Odyssey.</p>",
    )

    contact_src = ROOT / "src/info/contact.html"
    ensure_contains(
        contact_src,
        ODYSSEY_P,
        insert_after="          Marketplace. <a href=\"tefa.html\">See funding help &amp; eligibility</a>.</p>",
    )

    shop_src = ROOT / "src/info/shop-by-age.html"
    replace_all(shop_src, "Core Subjects Workbook Set", "Weekly Evidence Binder")
    strip_hs503_cards(shop_src)

    shop_store = ROOT / "store/src/shop.html"
    if shop_store.exists():
        replace_all(shop_store, "Core Subjects Workbook Set", "Weekly Evidence Binder")
        replace_all(shop_store, 'href="/products/"', 'href="/catalog"')
        replace_all(shop_store, 'href="products/"', 'href="../catalog.html"')

    subprocess.check_call([sys.executable, str(ROOT / "tools/build_site_catalog.py")], cwd=ROOT)
    subprocess.check_call([sys.executable, str(ROOT / "build.py")], cwd=ROOT)
    subprocess.check_call([sys.executable, str(ROOT / "tools/validate_project_state.py")], cwd=ROOT)
    print("catalog cleanup applied")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
