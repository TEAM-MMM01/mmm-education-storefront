#!/usr/bin/env python3
"""Build the Preparation Station landing page and storefront mockups.

Inlines the subset webfonts from fonts/ into each source page and writes
self-contained HTML documents. No build dependencies, no network, no CDN —
these pages have to work when dropped onto a static host or opened from
a USB stick.

    python3 build.py

Produces:
    index.html                 main landing page, from src/page.html
    store/shop.html             ESA store mockup: category grid
    store/product.html          ESA store mockup: product detail
    store/order.html             ESA store mockup: order/quote review
    store/track.html             secure order-history entry point
    general-store/shop.html      General Store mockup: category grid
    general-store/product.html   General Store mockup: product detail
    general-store/checkout.html  General Store mockup: checkout

Both mockup sets share store/shared_style.css (font-inlined once), spliced
in at each page's __STORE_SHARED_CSS__ marker, so the design tokens stay in
one place instead of being copy-pasted six times. Cross-links between the
two mockup sets use MAIN_SITE_URL / ESA_SHOP_URL placeholders, resolved
here to relative paths for the repo build — see resolve_cross_links().
Each set also loads its own cart.js directly (a relative <script src>, not
inlined) since the mockups aren't meant to be single-file-portable the way
index.html is.

The fonts in fonts/ were subset from their upstream Google Fonts releases to
Latin text plus the punctuation this page actually uses, and the variable
faces were instanced down to a single optical size. See fonts/README.md.
"""
import base64
import pathlib
import re

HERE = pathlib.Path(__file__).parent
# Source-controlled build stamp. Bump this manually when a dated rebuild is
# intentional; deriving it from wall-clock time would rewrite the committed
# generated pages on every future build and fail the "generated pages are
# committed" CI check.
BUILD_DATE = "August 19, 2026"
FONTS = {
    "__MONO4__": "dmmono400.woff2",
    "__MONO5__": "dmmono500.woff2",
    "__SAT4__": "satoshi400.woff2",
    "__SAT5__": "satoshi500.woff2",
    "__SAT7__": "satoshi700.woff2",
    "__CAB5__": "cabinet500.woff2",
    "__CAB7__": "cabinet700.woff2",
    "__CAB8__": "cabinet800.woff2",
}


def inline_fonts(text: str, label: str) -> str:
    for token, filename in FONTS.items():
        if token not in text:
            raise SystemExit(f"{token} missing from {label}")
        data = (HERE / "fonts" / filename).read_bytes()
        text = text.replace(token, base64.b64encode(data).decode())
    return text


def standalone_document(body_html: str, description: str) -> str:
    m = re.search(r"<title>(.*?)</title>\s*", body_html, re.S)
    title, inner = m.group(1), body_html[: m.start()] + body_html[m.end() :]
    return f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{title}</title>
<meta name="description" content="{description}">
<meta name="color-scheme" content="light dark">
<link rel="icon" href="data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 32 32'%3E%3Crect width='32' height='32' rx='7' fill='%23123f35'/%3E%3Ctext x='16' y='22' font-family='monospace' font-size='15' font-weight='700' fill='%23fffdf9' text-anchor='middle'%3EPS%3C/text%3E%3C/svg%3E">
<meta property="og:title" content="{title}">
<meta property="og:description" content="{description}">
<meta property="og:type" content="website">
<style>
  *,*::before,*::after{{box-sizing:border-box}}
  html,body{{margin:0; padding:0}}
  img,svg,video{{max-width:100%; height:auto; display:block}}
</style>
</head>
<body>
{inner}
</body>
</html>
"""


def build_main_page():
    page = inline_fonts((HERE / "src" / "page.html").read_text(), "src/page.html")
    page = page.replace("BUILD_DATE", BUILD_DATE)
    desc = (
        "Practical curriculum for life ahead. Hands-on project kits, workbooks, and curriculum guides "
        "for ages 3-17 covering practical skills, self-command, design, and emerging tech."
    )
    out = HERE / "index.html"
    out.write_text(standalone_document(page, desc))
    print(f"index.html  {out.stat().st_size / 1024:.0f} KB")


def build_store_pages(shared_css: str):
    store = HERE / "store"
    desc = (
        "Preparation Station educational products; approved TEFA offerings are "
        "purchased through the official Odyssey Marketplace."
    )
    for name in ("shop", "product", "order", "track"):
        src = (store / "src" / f"{name}.html").read_text()
        if "__STORE_SHARED_CSS__" not in src:
            raise SystemExit(f"__STORE_SHARED_CSS__ missing from store/src/{name}.html")
        page = src.replace("__STORE_SHARED_CSS__", shared_css)
        page = page.replace("BUILD_DATE", BUILD_DATE)
        page = resolve_cross_links(
            page, main="../index.html", esa_shop="shop.html", general_store="../general-store/shop.html"
        )
        out = store / f"{name}.html"
        if name == "shop":
            redirect = """<!doctype html><html lang=\"en\"><head><meta charset=\"utf-8\"><meta name=\"viewport\" content=\"width=device-width,initial-scale=1\"><meta http-equiv=\"refresh\" content=\"0;url=../catalog.html\"><link rel=\"canonical\" href=\"https://preparationstation.org/catalog\"><title>Catalog — Preparation Station</title></head><body><p>The Preparation Station catalog has moved. <a href=\"../catalog.html\">Continue to the catalog</a>.</p></body></html>"""
            out.write_text(redirect)
        else:
            page = page.replace('href="shop.html"', 'href="../catalog.html"')
            out.write_text(standalone_document(page, desc))
        print(f"store/{name}.html  {out.stat().st_size / 1024:.0f} KB")


def build_general_store_pages(shared_css: str):
    gs = HERE / "general-store"
    desc = (
        "General Store preview: family titles and activity books sold at retail, "
        "kept separate from the ESA/TEFA-funded storefront."
    )
    for name in ("shop", "product", "checkout"):
        src = (gs / "src" / f"{name}.html").read_text()
        if "__STORE_SHARED_CSS__" not in src:
            raise SystemExit(f"__STORE_SHARED_CSS__ missing from general-store/src/{name}.html")
        page = src.replace("__STORE_SHARED_CSS__", shared_css)
        page = page.replace("BUILD_DATE", BUILD_DATE)
        page = resolve_cross_links(
            page, main="../index.html", esa_shop="../catalog.html", general_store="shop.html"
        )
        out = gs / f"{name}.html"
        out.write_text(standalone_document(page, desc))
        print(f"general-store/{name}.html  {out.stat().st_size / 1024:.0f} KB")


def build_info_pages(shared_css: str):
    info = HERE / "src" / "info"
    descriptions = {
        "about": "About Preparation Station — operated by Nationwide Acquisitions, LLC. Practical curriculum for career readiness, financial foundations, and independent living.",
        "contact": "Contact Preparation Station — submit a request, ask about TEFA eligibility, or get help with your learning pathway. Responses within one business day.",
        "privacy": "Preparation Station Privacy Policy — how we collect, use, and protect your information. We never collect payment or program account details.",
        "terms": "Preparation Station Terms & Conditions — guidelines for using our site, requesting information, and understanding TEFA purchase pathways.",
        "shipping": "Preparation Station Shipping & Returns — information about delivery, returns, and refunds for products purchased through approved pathways.",
        "shop-by-age": "Homeschool kits and curriculum by age band: Launchpad (3–5), Explorer (6–8), Mission Control (9–12), Advanced Command (13–17), Planner Mode. Preparation Station is an approved TEFA Marketplace vendor.",
        "faq": "Frequently asked questions about Preparation Station — TEFA eligibility, pricing, ordering, and how to use your education funding.",
        "tefa": "Preparation Station TEFA & Funding Guide — approved marketplace vendor information, eligibility requirements, and purchase pathways through Odyssey.",
    }
    for name in ("about", "contact", "privacy", "terms", "shipping", "shop-by-age", "faq", "tefa"):
        src = (info / f"{name}.html").read_text()
        if "__INFO_SHARED_CSS__" not in src:
            raise SystemExit(f"__INFO_SHARED_CSS__ missing from src/info/{name}.html")
        page = src.replace("__INFO_SHARED_CSS__", shared_css)
        page = page.replace("BUILD_DATE", BUILD_DATE)
        page = resolve_cross_links(page, main="index.html", esa_shop="store/shop.html", general_store="")
        out = HERE / f"{name}.html"
        out.write_text(standalone_document(page, descriptions[name]))
        print(f"{name}.html  {out.stat().st_size / 1024:.0f} KB")


def resolve_cross_links(page: str, main: str, esa_shop: str, general_store: str) -> str:
    return (
        page.replace("MAIN_SITE_URL", main)
        .replace("ESA_SHOP_URL", esa_shop)
        .replace("GENERAL_STORE_URL", general_store)
    )


def build_site_catalog():
    import subprocess
    import sys
    script = HERE / "tools" / "build_site_catalog.py"
    subprocess.check_call([sys.executable, str(script)])


if __name__ == "__main__":
    build_site_catalog()
    build_main_page()
    _base_css = (HERE / "src" / "base" / "design-system.css").read_text()
    _shared_css = _base_css + inline_fonts(
        (HERE / "store" / "shared_style.css").read_text(), "store/shared_style.css"
    )
    build_store_pages(_shared_css)
    build_general_store_pages(_shared_css)
    _info_css = _base_css + inline_fonts(
        (HERE / "src" / "info" / "shared.css").read_text(), "src/info/shared.css"
    )
    build_info_pages(_info_css)
