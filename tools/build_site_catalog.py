#!/usr/bin/env python3
"""Generate catalog.html and products/*.html from src/data/site-catalog.json."""
from __future__ import annotations

import html
import json
import re
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATA = json.loads((ROOT / "src" / "data" / "site-catalog.json").read_text())

STATUS_LABEL = {
    "marketplace_listed": "Marketplace listed",
    "offering_review": "Offering review",
    "planning_concept": "Planning concept",
    "free_resource": "Free resource",
    "external_resource": "External resource",
}
CTA_LABEL = {
    "request_availability": "Request availability update",
    "ask_concept": "Ask about this concept",
    "open_printable": "Open printable",
    "view_marketplace": "View official marketplace listing",
}
TEFA = (
    "TEFA-funded purchases are available only for the exact Preparation Station "
    "offering that is approved and published in the official marketplace. We confirm "
    "the current purchase path in writing before a family spends program funds."
)
PAY = "This website does not process TEFA payments or collect program-account details."
PRICE = "Final marketplace eligibility and verified price are shown only for the exact SKU published in Odyssey."


def esc(value) -> str:
    return html.escape("" if value is None else str(value), quote=True)


def money(n) -> str:
    return f"${n:,.0f}"


def register_price(item: dict) -> str:
    label = price_html(item)
    if label == "Price: Not published":
        return "Unpublished"
    return label


def price_html(item: dict) -> str:
    status = item.get("status")
    pstat = item.get("price_status")
    if status == "free_resource":
        return "Free resource"
    if status == "marketplace_listed":
        return "Verified price: view the exact official marketplace listing."
    if pstat == "planning_listing" and item.get("planning_price_usd"):
        return f"Planning listing price: {money(item['planning_price_usd'])}"
    if item.get("kind") == "kit":
        return "Price: Not published"
    return "No purchase path is currently available."


def cta_href(item: dict) -> str:
    if item.get("cta") == "open_printable":
        return item.get("resource_path") or "resources/"
    if item.get("cta") == "view_marketplace" and item.get("marketplace_url"):
        return item["marketplace_url"]
    topic = "concept" if item.get("cta") == "ask_concept" else "availability"
    return f"contact.html?sku={esc(item['sku'])}&topic={topic}"


def cta_label(item: dict) -> str:
    return CTA_LABEL.get(item.get("cta"), "Request a pathway recommendation")


CSS = """
:root{
  --bg:#F6F2EA; --bg-alt:#EFE7DB; --surface:#FCFAF6; --surface-2:#F2ECE2;
  --border:#D8CFC2; --text:#2B2925; --muted:#6E675F;
  --accent:#0E6B6F; --accent-hover:#0A5356; --gold:#C58B44;
  --listed:#3E6B3F; --review:#8A5A1F; --planning:#7A6D92;
  --error:#8F3D3D; --on-accent:#FCFAF6;
  --radius:14px; --shadow:0 8px 28px rgba(43,41,37,.07);
  --font: ui-sans-serif, system-ui, -apple-system, "Segoe UI", sans-serif;
  --ease:cubic-bezier(.16,1,.3,1); --dur:220ms;
}
*{box-sizing:border-box}
html,body{margin:0;padding:0}
body{font-family:var(--font);background:var(--bg);color:var(--text);line-height:1.6;-webkit-font-smoothing:antialiased}
img{max-width:100%;height:auto;display:block}
a{color:var(--accent)}
:focus-visible{outline:3px solid var(--accent);outline-offset:3px}
.container{max-width:1120px;margin:0 auto;padding:0 24px}
.btn{display:inline-flex;align-items:center;justify-content:center;min-height:44px;padding:10px 18px;border-radius:10px;font-weight:700;font-size:.95rem;text-decoration:none;border:2px solid transparent;cursor:pointer;transition:transform var(--dur) var(--ease),background var(--dur) var(--ease)}
.btn--primary{background:var(--accent);color:var(--on-accent);border-color:var(--accent)}
.btn--primary:hover{background:var(--accent-hover)}
.btn--outline{background:transparent;color:var(--accent);border-color:var(--accent)}
.site-header{position:sticky;top:0;z-index:40;background:rgba(246,242,234,.96);border-bottom:1px solid var(--border);backdrop-filter:blur(16px)}
.header-inner{display:flex;align-items:center;justify-content:space-between;gap:12px;min-height:64px;max-width:1120px;margin:0 auto;padding:8px 24px;flex-wrap:wrap}
.brand{text-decoration:none;color:var(--text)}
.brand__wordmark{font-weight:800;letter-spacing:-.02em}
.brand__tagline{display:block;font-size:.72rem;color:var(--muted)}
.site-nav{display:flex;flex-wrap:wrap;gap:4px;list-style:none;margin:0;padding:0}
.site-nav a{display:inline-flex;align-items:center;min-height:44px;padding:0 10px;border-radius:8px;color:var(--muted);text-decoration:none;font-weight:600;font-size:.88rem}
.site-nav a:hover,.site-nav a[aria-current="page"]{color:var(--text);background:var(--surface-2)}
.nav-toggle{display:none;min-height:44px;min-width:44px;border:1px solid var(--border);border-radius:10px;background:var(--surface)}
.hero{padding:40px 0 20px}
.hero h1{font-size:clamp(1.8rem,4vw,2.8rem);letter-spacing:-.03em;line-height:1.15;margin:0 0 12px}
.lede{color:var(--muted);max-width:62ch;font-size:1.05rem}
.cluster{display:flex;flex-wrap:wrap;gap:10px;margin-top:16px}
.reviewer,.legend,.policy{background:var(--surface);border:1px solid var(--border);border-radius:var(--radius);padding:20px;margin:18px 0}
.reviewer h2,.legend h2,.policy h2,.section h2{margin:0 0 10px;font-size:1.2rem}
.reviewer dl{display:grid;grid-template-columns:160px 1fr;gap:8px 16px;margin:0}
.reviewer dt{font-size:.72rem;text-transform:uppercase;letter-spacing:.08em;color:var(--muted)}
.reviewer dd{margin:0}
.legend{display:grid;gap:8px}
.pill{display:inline-flex;align-items:center;min-height:28px;padding:2px 10px;border-radius:999px;font-size:.75rem;font-weight:700;border:1px solid var(--border);background:var(--surface-2)}
.pill--review{color:var(--review);border-color:#e2c49a;background:#f7edd9}
.pill--plan{color:var(--planning);border-color:#d5cde4;background:#f3eef8}
.pill--free{color:var(--listed);border-color:#c9ddc4;background:#eef6ec}
.pill--listed{color:var(--listed);border-color:#c9ddc4;background:#eef6ec}
.tools{background:var(--surface);border-top:1px solid var(--border);border-bottom:1px solid var(--border);padding:14px 0;position:sticky;top:64px;z-index:30}
.tools-grid{display:grid;grid-template-columns:1.2fr repeat(4,1fr);gap:10px;align-items:end}
.tools label{font-size:.72rem;font-weight:800;text-transform:uppercase;letter-spacing:.06em;color:var(--muted)}
.tools input,.tools select{width:100%;min-height:44px;margin-top:4px;border:1px solid var(--border);border-radius:8px;background:var(--surface);color:var(--text);padding:8px 10px;font:inherit}
.section{padding:36px 0}
.section--alt{background:var(--bg-alt)}
.grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(250px,1fr));gap:16px}
.card{display:flex;flex-direction:column;background:var(--surface);border:1px solid var(--border);border-radius:var(--radius);overflow:hidden;min-height:100%;box-shadow:var(--shadow);transition:transform var(--dur) var(--ease)}
.card[hidden]{display:none!important}
.card:hover{transform:translateY(-2px)}
.card img{width:100%;height:140px;object-fit:cover;background:var(--surface-2)}
.card-body{display:flex;flex-direction:column;gap:8px;padding:16px;flex:1}
.card h3{margin:0;font-size:1.05rem;letter-spacing:-.02em}
.meta{font-size:.8rem;color:var(--muted)}
.card-cta{margin-top:auto;padding-top:10px}
.table-wrap{overflow:auto;max-width:100%;border:1px solid var(--border);border-radius:12px;background:var(--surface)}
table{width:100%;border-collapse:collapse;font-size:.85rem}
th,td{text-align:left;padding:10px 12px;border-bottom:1px solid var(--border);vertical-align:top}
th{font-size:.72rem;text-transform:uppercase;letter-spacing:.06em;color:var(--muted)}
.footer{background:#2B2925;color:#F2ECE2;padding:36px 0 24px;margin-top:24px}
.footer a{color:#E7D3A8}
.footer-grid{display:grid;grid-template-columns:2fr 1fr 1fr 1fr;gap:20px}
.pd-grid{display:grid;grid-template-columns:minmax(0,1fr) minmax(0,1fr);gap:28px;padding:28px 0}
.pd-grid > *{min-width:0}
.pd-grid img{width:100%;max-width:100%;height:auto}
.pd-block{background:var(--surface);border:1px solid var(--border);border-radius:var(--radius);padding:18px;margin:14px 0}
.crumb{font-size:.85rem;color:var(--muted);padding-top:18px}
.empty{display:none;padding:24px;border:1px dashed var(--border);border-radius:12px;background:var(--surface)}
.cta-bar{background:var(--accent);color:var(--on-accent);padding:18px 0}
.cta-bar a{color:#fff}
@media (max-width:900px){
  .tools-grid,.footer-grid,.reviewer dl{grid-template-columns:1fr 1fr}
  .pd-grid{grid-template-columns:minmax(0,1fr)}
  .nav-toggle{display:inline-flex}
  .site-nav{display:none}
  .site-nav.is-open{display:flex;flex-direction:column;position:absolute;left:0;right:0;top:64px;background:var(--bg);padding:12px 24px 20px;border-bottom:1px solid var(--border)}
}
@media (max-width:640px){
  .container,.header-inner{padding-left:24px;padding-right:24px}
  .tools-grid,.footer-grid,.pd-grid,.reviewer dl{grid-template-columns:1fr}
  .header-inner .btn{width:100%}
  body{overflow-x:hidden}
}
@media (prefers-reduced-motion:reduce){
  *{transition:none!important;animation:none!important}
}
"""


def header(active: str) -> str:
    links = [
        ("index.html", "Home"),
        ("catalog.html", "Catalog"),
        ("shop-by-age.html", "Shop by Age"),
        ("index.html#guide", "Mission Guide"),
        ("tefa.html", "Funding"),
        ("about.html", "About"),
        ("contact.html", "Contact"),
    ]
    nav = []
    for href, label in links:
        cur = ' aria-current="page"' if label == active else ""
        nav.append(f'<li><a href="{href}"{cur}>{esc(label)}</a></li>')
    return f"""<header class="site-header"><div class="header-inner">
  <a class="brand" href="index.html"><span class="brand__wordmark">Preparation Station</span><span class="brand__tagline">Practical curriculum for life ahead</span></a>
  <button class="nav-toggle" type="button" aria-expanded="false" aria-controls="siteNav">Menu</button>
  <nav><ul class="site-nav" id="siteNav">{''.join(nav)}</ul></nav>
  <a class="btn btn--primary" href="contact.html">Request recommendation</a>
</div></header>"""


def footer() -> str:
    d = DATA
    return f"""<footer class="footer"><div class="container footer-grid">
  <div><strong>Preparation Station</strong><p>Helps families build practical skills, habits, judgment, and readiness. Operated by {esc(d['operator'])}.</p>
  <p>{esc(PAY)}</p></div>
  <div><strong>Catalog</strong><p><a href="catalog.html">Official catalog</a><br><a href="shop-by-age.html">Shop by Age</a><br><a href="index.html#guide">Mission Guide</a></p></div>
  <div><strong>Support</strong><p><a href="tefa.html">Funding / TEFA</a><br><a href="faq.html">FAQ</a><br><a href="contact.html">Contact</a><br><a href="mailto:{esc(d['support_email'])}">{esc(d['support_email'])}</a></p></div>
  <div><strong>Legal</strong><p><a href="about.html">About</a><br><a href="privacy.html">Privacy</a><br><a href="terms.html">Terms</a><br><a href="shipping.html">Shipping &amp; returns</a></p></div>
</div><div class="container" style="margin-top:18px;font-size:.8rem;color:#cfc6b8">Updated {esc(d['updated_at'])} · {esc(d['response_commitment'])}</div></footer>
<script>
const tog=document.querySelector('.nav-toggle');const nav=document.getElementById('siteNav');
if(tog&&nav){{tog.addEventListener('click',()=>{{const open=nav.classList.toggle('is-open');tog.setAttribute('aria-expanded',open?'true':'false');}});}}
</script>"""


def card(item: dict, prefix: str = "") -> str:
    img = prefix + item.get("image", "images/photo-catalog-banner.jpg")
    href = prefix + (item.get("resource_path") if item["kind"] == "free_resource" else f"products/{item['sku']}.html")
    st = item.get("status")
    pill = {"offering_review": "pill--review", "planning_concept": "pill--plan", "free_resource": "pill--free", "marketplace_listed": "pill--listed"}.get(st, "")
    return f"""<article class="card" data-status="{esc(st)}" data-dept="{esc(item.get('department'))}" data-age="{esc(item.get('age_range'))}" data-format="{esc(item.get('format'))}" data-kind="{esc(item.get('kind'))}" data-title="{esc(item.get('title'))}">
  <a href="{esc(href)}" aria-label="View {esc(item['title'])}"><img src="{esc(img)}" alt="" width="640" height="400" loading="lazy"></a>
  <div class="card-body">
    <span class="pill {pill}">{esc(STATUS_LABEL.get(st, st))}</span>
    <div class="meta">SKU: {esc(item.get('sku'))} · {esc(item.get('age_range'))}</div>
    <h3>{esc(item.get('title'))}</h3>
    <p class="meta">{esc(item.get('purpose'))}</p>
    <p class="meta">{esc(price_html(item))}</p>
    <div class="card-cta"><a class="btn btn--outline" href="{esc(href)}">View details</a></div>
  </div>
</article>"""


def on_public_catalog(item: dict) -> bool:
    sku = item.get("sku", "")
    if sku == "GEN-BK-001" or item.get("title") == "The Vulturian":
        return False
    pathway_skus = {
        row["sku"]
        for row in json.loads((ROOT / "catalog" / "pathways.json").read_text()).get("items", [])
    }
    if re.fullmatch(r"PS-[A-Z]{2}-\d{4,}", sku) and sku not in pathway_skus:
        return False
    return True


def build_catalog() -> str:
    items = DATA["items"]
    paid = [i for i in items if i["kind"] in {"pathway", "kit", "book"} and on_public_catalog(i)]
    free = [i for i in items if i["kind"] == "free_resource"]
    by_dept: dict[str, list] = defaultdict(list)
    for it in paid:
        by_dept[it["department"]].append(it)
    dept_aliases = {
        "Curriculum pathways": ["pathways"],
        "Practical & Trade": ["d01"],
        "Situation Handling & Self-Command": ["d02"],
        "Design & Motion Studio": ["d03"],
        "AI & Emerging Tech Bench": ["d04"],
        "Homeschool Essentials": ["d05"],
    }
    sections = []
    for dept, group in by_dept.items():
        sid = dept.lower().replace(" ", "-").replace("&", "and")
        aliases = "".join(
            f'<span id="{esc(alias)}" hidden></span>' for alias in dept_aliases.get(dept, [])
        )
        sections.append(
            f'<section class="section" id="{esc(sid)}">{aliases}<div class="container"><h2>{esc(dept)}</h2><div class="grid">{"".join(card(i) for i in group)}</div></div></section>'
        )
    rows = []
    for it in paid:
        rows.append(
            "<tr>"
            f"<td>{esc(it['sku'])}</td><td><a href='products/{esc(it['sku'])}.html'>{esc(it['title'])}</a></td>"
            f"<td>{esc(it['department'])}</td><td>{esc(it['age_range'])}</td><td>{esc(it['duration'])}</td>"
            f"<td>{esc(it['format'])}</td><td>{esc(it['license'])}</td><td>{esc(it['delivery'])}</td>"
            f"<td>{esc(it['purpose'])}</td><td>{esc(register_price(it))}</td>"
            f"<td>{esc(STATUS_LABEL.get(it['status']))}</td><td>{esc(it['canonical_url'])}</td>"
            f"<td>{esc(it['last_updated'])}</td></tr>"
        )
    return f"""<!DOCTYPE html>
<html lang="en"><head>
<meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<title>Catalog — Preparation Station</title>
<meta name="description" content="Official Preparation Station catalog for families and TEFA/Odyssey reviewers. Exact SKUs, status, and planning prices. Not checkout.">
<link rel="canonical" href="https://preparationstation.org/catalog">
<meta property="og:title" content="Preparation Station catalog">
<meta property="og:url" content="https://preparationstation.org/catalog">
<meta property="og:image" content="https://preparationstation.org/images/photo-catalog-banner.jpg">
<style>{CSS}</style>
</head><body>
{header("Catalog")}
<main>
<section class="hero"><div class="container">
  <p class="pill pill--review">Official catalog URL</p>
  <h1>Preparation Station catalog</h1>
  <p class="lede">Authoritative product records for families and Odyssey reviewers. Nothing here is checkout. {esc(TEFA)}</p>
  <div class="cluster">
    <a class="btn btn--primary" href="#register">SKU register</a>
    <a class="btn btn--outline" href="contact.html">Request a written pathway recommendation</a>
  </div>
</div></section>
<div class="container">
  <aside class="reviewer" id="reviewer-facts">
    <h2>Reviewer quick facts</h2>
    <dl>
      <dt>Legal entity</dt><dd>{esc(DATA['operator'])}</dd>
      <dt>Brand / DBA</dt><dd>{esc(DATA['dba'])}</dd>
      <dt>Website</dt><dd><a href="{esc(DATA['canonical_site'])}">{esc(DATA['canonical_site'])}</a></dd>
      <dt>Catalog URL</dt><dd><a href="{esc(DATA['canonical_catalog_url'])}">{esc(DATA['canonical_catalog_url'])}</a></dd>
      <dt>Support email</dt><dd><a href="mailto:{esc(DATA['support_email'])}">{esc(DATA['support_email'])}</a></dd>
      <dt>Response</dt><dd>{esc(DATA['response_commitment'])}</dd>
      <dt>Phone</dt><dd><a href="tel:+16822535459">{esc(DATA['phone'])}</a></dd>
      <dt>Mailing address</dt><dd>{esc(DATA['mailing_address'])}</dd>
      <dt>Vendor status</dt><dd>{esc(DATA['vendor_status'])}</dd>
      <dt>Payments</dt><dd>{esc(PAY)}</dd>
      <dt>Updated</dt><dd>{esc(DATA['updated_at'])}</dd>
      <dt>Policies</dt><dd><a href="privacy.html">Privacy</a> · <a href="terms.html">Terms</a> · <a href="shipping.html">Shipping &amp; returns</a></dd>
    </dl>
  </aside>
  <aside class="legend">
    <h2>How catalog status works</h2>
    <p><span class="pill pill--listed">Marketplace listed</span> Exact SKU is approved and published in Odyssey.</p>
    <p><span class="pill pill--review">Offering review</span> Submitted, pending, or being prepared. Not purchasable yet.</p>
    <p><span class="pill pill--plan">Planning concept</span> Future catalog candidate. Not submitted or purchasable.</p>
    <p><span class="pill pill--free">Free resource</span> Preparation Station educational tool. Not a paid offering.</p>
    <p><span class="pill">External resource</span> Third-party. No affiliation unless stated.</p>
  </aside>
  <aside class="policy">
    <h2>How to verify an offering</h2>
    <ol>
      <li>Find the exact Preparation Station SKU on this catalog.</li>
      <li>Confirm that exact SKU appears in the official marketplace.</li>
      <li>Review the verified marketplace price and eligibility there.</li>
      <li>Complete the TEFA-funded purchase through the official marketplace.</li>
    </ol>
    <p>{esc(PRICE)}</p>
    <p>{esc(PAY)}</p>
  </aside>
</div>
<div class="tools"><div class="container tools-grid">
  <label>Search<input id="q" type="search" placeholder="SKU or title"></label>
  <label>Department<select id="dept"><option value="all">All</option></select></label>
  <label>Status<select id="status"><option value="all">All</option>
    <option value="offering_review">Offering review</option>
    <option value="planning_concept">Planning concept</option>
    <option value="free_resource">Free resource</option>
    <option value="marketplace_listed">Marketplace listed</option></select></label>
  <label>Format<select id="format"><option value="all">All</option></select></label>
  <label>Sort<select id="sort"><option value="recommended">Recommended</option><option value="title">Title A–Z</option><option value="department">Department</option><option value="status">Status</option></select></label>
</div><div class="container"><p id="count" aria-live="polite"></p><button class="btn btn--outline" id="reset" type="button">Clear filters</button></div></div>
<div class="container"><p class="empty" id="empty">No items match these filters. Clear filters to see the full catalog.</p></div>
{''.join(sections)}
<section class="section section--alt" id="free"><div class="container"><h2>Free resources</h2><div class="grid">{''.join(card(i) for i in free)}</div></div></section>
<section class="section" id="register"><div class="container">
  <h2>SKU register</h2>
  <div class="table-wrap"><table>
    <thead><tr><th>SKU</th><th>Title</th><th>Department</th><th>Age</th><th>Duration</th><th>Format</th><th>License</th><th>Delivery</th><th>Purpose</th><th>Price status</th><th>Marketplace status</th><th>URL</th><th>Updated</th></tr></thead>
    <tbody>{''.join(rows)}</tbody>
  </table></div>
</div></section>
</main>
<aside class="cta-bar"><div class="container"><strong>Need a written pathway recommendation?</strong> We reply within one business day with best-fit options, current status, and the correct purchase path. <a class="btn btn--outline" href="contact.html">Request recommendation</a></div></aside>
{footer()}
<script>
const cards=[...document.querySelectorAll('.card')];
const dept=document.getElementById('dept');
const format=document.getElementById('format');
[...new Set(cards.map(c=>c.dataset.dept).filter(Boolean))].sort().forEach(v=>{{const o=document.createElement('option');o.value=v;o.textContent=v;dept.appendChild(o);}});
[...new Set(cards.map(c=>c.dataset.format).filter(Boolean))].sort().forEach(v=>{{const o=document.createElement('option');o.value=v;o.textContent=v;format.appendChild(o);}});
function apply(){{
  const q=(document.getElementById('q').value||'').toLowerCase();
  const d=dept.value,s=document.getElementById('status').value,f=format.value,sort=document.getElementById('sort').value;
  let n=0;
  cards.forEach(c=>{{
    const hay=(c.dataset.title+' '+c.dataset.dept+' '+(c.querySelector('.meta')?.textContent||'')).toLowerCase();
    const ok=(!q||hay.includes(q))&&(d==='all'||c.dataset.dept===d)&&(s==='all'||c.dataset.status===s)&&(f==='all'||c.dataset.format===f);
    c.hidden=!ok; if(ok) n++;
  }});
  document.getElementById('count').textContent=n+' items shown';
  document.getElementById('empty').style.display=n?'none':'block';
  const key={{title:c=>c.dataset.title,department:c=>c.dataset.dept,status:c=>c.dataset.status}}[sort];
  if(key){{[...new Set(cards.map(c=>c.parentElement))].forEach(g=>{{[...g.querySelectorAll('.card')].filter(c=>!c.hidden).sort((a,b)=>key(a).localeCompare(key(b))).forEach(c=>g.appendChild(c));}});}}
}}
['q','dept','status','format','sort'].forEach(id=>{{const el=document.getElementById(id);el.addEventListener('input',apply);el.addEventListener('change',apply);}});
document.getElementById('reset').addEventListener('click',()=>{{document.getElementById('q').value='';dept.value='all';document.getElementById('status').value='all';format.value='all';document.getElementById('sort').value='recommended';apply();}});
apply();
</script>
</body></html>
"""


def lis(values: list[str]) -> str:
    if not values:
        return "<p>Not published yet.</p>"
    return "<ul>" + "".join(f"<li>{esc(v)}</li>" for v in values) + "</ul>"


def build_pdp(item: dict) -> str:
    st = item.get("status")
    img = "../" + item.get("image", "images/photo-catalog-banner.jpg")
    related = [
        o
        for o in DATA["items"]
        if o["sku"] != item["sku"]
        and o.get("department") == item.get("department")
        and o["kind"] != "free_resource"
        and on_public_catalog(o)
    ][:3]
    faq = "".join(f"<details><summary>{esc(x['q'])}</summary><p>{esc(x['a'])}</p></details>" for x in item.get("faq") or [])
    href = cta_href(item)
    if not href.startswith("http") and not href.startswith("contact") and not href.startswith("resources"):
        href = "../" + href
    elif href.startswith("contact") or href.startswith("resources"):
        href = "../" + href
    return f"""<!DOCTYPE html>
<html lang="en"><head>
<meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<title>{esc(item['title'])} — Preparation Station</title>
<meta name="description" content="{esc(item.get('purpose'))}">
<link rel="canonical" href="{esc(item.get('canonical_url'))}">
<style>{CSS}</style>
</head><body>
{header("Catalog").replace('href="', 'href="../')}
<main class="container">
  <p class="crumb"><a href="../catalog.html">Catalog</a> / {esc(item.get('department'))} / {esc(item['title'])}</p>
  <div class="pd-grid">
    <div><img src="{esc(img)}" alt="" width="960" height="540"></div>
    <div>
      <span class="pill pill--review">{esc(STATUS_LABEL.get(st))}</span>
      <h1>{esc(item['title'])}</h1>
      <p class="lede">{esc(item.get('purpose'))}</p>
      <p class="meta">SKU: {esc(item['sku'])} · {esc(item.get('age_range'))} · {esc(item.get('duration'))} · {esc(item.get('format'))}</p>
      <p><strong>{esc(price_html(item))}</strong></p>
      <p class="meta">{esc(PRICE)}</p>
      <div class="cluster">
        <a class="btn btn--primary" href="{esc(href)}">{esc(cta_label(item))}</a>
        <a class="btn btn--outline" href="../catalog.html">Back to catalog</a>
      </div>
    </div>
  </div>
  <div class="pd-block"><h2>Educational purpose</h2><p>{esc(item.get('purpose'))}</p></div>
  <div class="pd-block"><h2>Learning outcomes</h2>{lis(item.get('outcomes') or [])}</div>
  <div class="pd-block"><h2>What is included</h2>{lis(item.get('included') or [])}</div>
  <div class="pd-block"><h2>What is not included</h2>{lis(item.get('not_included') or [])}</div>
  <div class="pd-block"><h2>Best fit</h2>{lis(item.get('best_fit') or [])}</div>
  <div class="pd-block"><h2>Not ideal for</h2>{lis(item.get('not_ideal') or [])}</div>
  <div class="pd-block"><h2>How families use it</h2>{lis(item.get('how_families_use') or [])}</div>
  <div class="pd-block"><h2>Implementation requirements</h2>{lis(item.get('requirements') or [])}</div>
  <div class="pd-block"><h2>License and delivery</h2><p>{esc(item.get('license'))}. {esc(item.get('delivery'))}</p></div>
  <div class="pd-block"><h2>TEFA purchase path</h2><p>{esc(TEFA)}</p><p>{esc(PAY)}</p></div>
  <div class="pd-block"><h2>Product FAQ</h2>{faq}</div>
  <div class="pd-block"><h2>Related catalog items</h2>{''.join(f"<p><a href='{esc(r['sku'])}.html'>{esc(r['title'])}</a> · {esc(r['sku'])}</p>" for r in related) or "<p>See the full catalog.</p>"}</div>
  <p class="meta">Last updated {esc(item.get('last_updated'))}</p>
</main>
{footer().replace('href="', 'href="../').replace("href='../mailto:", "href='mailto:").replace('href="../mailto:', 'href="mailto:').replace('href="../tel:', 'href="tel:')}
</body></html>
"""


def main() -> None:
    catalog = build_catalog()
    (ROOT / "catalog.html").write_text(catalog)
    products = ROOT / "products"
    products.mkdir(exist_ok=True)
    n = 0
    for item in DATA["items"]:
        if item["kind"] == "free_resource":
            continue
        (products / f"{item['sku']}.html").write_text(build_pdp(item))
        n += 1
    print(f"catalog.html + {n} product pages")


if __name__ == "__main__":
    main()
