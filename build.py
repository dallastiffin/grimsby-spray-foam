#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Local trade website generator
=============================

    python build.py            rebuild every HTML page (fast, no dependencies)
    python build.py --images   also re-export the photos (needs Pillow)

The markdown file is the single source of truth for all copy. Edit it, run this
script, and every page is rebuilt with consistent navigation, schema, CTAs and
forms. Do not hand-edit the HTML in site/ - it gets overwritten.

site/style.css and site/script.js are NOT generated. Edit those directly.


SPINNING UP A NEW CITY
----------------------
Everything city-specific lives in the CONFIG block below. See NEW-CITY.md for
the full runbook, or run:  python tools/new-city.py --help
"""
import os, re, json, html, sys, hashlib, datetime

ROOT = os.path.dirname(os.path.abspath(__file__))
OUT  = os.path.join(ROOT, "site")            # <- this folder is what deploys
IMG  = os.path.join(OUT, "images")

BUILD_IMAGES = "--images" in sys.argv


# ==========================================================================
#  CONFIG
#  Everything city-specific lives here. Nothing below this block needs
#  editing to launch another city.
# ==========================================================================

# --- business identity ----------------------------------------------------
BUSINESS      = "Grimsby Spray Foam Insulation"
CITY          = "Grimsby"
CITY_SLUG     = "grimsby"
PROVINCE      = "Ontario"
PROVINCE_CODE = "ON"
REGION        = "Niagara Region"
CITY_PROV     = "%s, %s" % (CITY, PROVINCE)

PHONE_DISPLAY = "(289) 672-4160"
PHONE_HREF    = "+12896724160"

# CANONICAL DOMAIN. Feeds canonical tags, Open Graph, sitemap.xml and schema.
# Must match the hostname the site actually serves, with no redirect in
# between, or Google indexes a URL that bounces. The www host is the one
# is a new registration with nothing indexed against it, so the apex is
# canonical and www redirects to it.
DOMAIN = "https://www.grimsbysprayfoaminsulation.com"

# The markdown file holding all copy, in this folder.
CONTENT_FILE = "Grimsby-Spray-Foam-Insulation-Website-Content.md"

# Colour stamped into <meta name="theme-color"> and site.webmanifest. Must
# agree with --color-primary in site/style.css.
THEME_COLOR = "#17382C"

# Microsoft Clarity project ID. Leave "" until the owner creates the project;
# an empty or placeholder ID would otherwise ship a broken script tag on every
# page. The snippet is injected into <head> only when this is non-empty.
CLARITY_ID = ""

# Google Maps embed for the service-area section. A plain coordinate embed,
# not a place-ID "pb=" embed, so the pin and zoom are under our control.
# The zoom was checked by looking at the rendered map, not by reasoning
# about the number - the pin sits on Grimsby and the zoom is set to hold
# Beamsville, Vineland and Smithville in frame without losing the town
# itself. Grimsby is small, so z=12 rather than the z=11 a region needs.
MAP_EMBED = "https://maps.google.com/maps?q=43.1948,-79.5856&z=12&output=embed"

# --- location details, for LocalBusiness schema ---------------------------
STREET_ADDRESS = "PLACEHOLDER - add street address"
POSTAL_CODE    = "PLACEHOLDER"
COUNTRY        = "CA"
LATITUDE       = "43.1948"
LONGITUDE      = "-79.5856"
OPENING_DAYS   = ["Monday","Tuesday","Wednesday","Thursday","Friday","Saturday"]
OPENING_TIME   = "07:00"
CLOSING_TIME   = "18:00"
HOURS_TEXT     = "Monday to Saturday, 7:00am to 6:00pm"

# --- service area ---------------------------------------------------------
# Goes into schema areaServed. TOPBAR_AREA is the short version shown in the
# thin bar above the header.
SERVICE_AREA = [
    "Grimsby",
    "Beamsville",
    "Vineland",
    "Jordan",
    "Campden",
    "Smithville",
    "Winona",
    "Stoney Creek",
    "Grassie",
    "Caistor Centre",
    "St. Catharines",
    "Hamilton",
]
TOPBAR_AREA = "Grimsby, Beamsville, Vineland, Smithville &amp; across west Niagara"

# --- legacy URLs ----------------------------------------------------------
# grimsbysprayfoaminsulation.com has indexed history on the www host, so
# there is nothing to preserve and the template's own slugs are used as-is.
# If a legacy URL ever has to be honoured, map it here: every URL passes
# through one of three choke points below (write, public_url, rewrite_links)
# and each of them applies this map, so no literal in this file has to change.
SLUG_ALIAS = {
    "about.html":   "about-us.html",
    "contact.html": "contact-us.html",
}

# ==========================================================================
#  END CONFIG
# ==========================================================================

# Freshness signal. This is the date the pages were last generated, which is
# literally true and verifiable, rather than an invented publish date. Only
# modified_time is emitted: the original publish date of this content is not
# something the generator knows, and guessing it would be a false claim.
BUILD_DATE = datetime.date.today().isoformat()

# The date this version of the site was published. Set ONCE, by hand, and
# left alone. It must never be wired to today's date: a publish date that
# moves every time the generator runs is a false freshness signal, and a
# crawler that notices will trust the rest of the markup less.
SITE_PUBLISHED = "2026-10-03"

SRC = os.path.join(ROOT, CONTENT_FILE)

os.makedirs(OUT, exist_ok=True)
os.makedirs(IMG, exist_ok=True)

def asset_v(name):
    """Append a content fingerprint to CSS/JS URLs.

    _headers caches these files hard at the edge and in the browser. Without a
    fingerprint, an edit to style.css would not reach anyone who had already
    visited until the cache expired. The hash changes whenever the file
    changes, so updates are picked up immediately.

    NOTE: rerun build.py after editing style.css or script.js, or the hash in
    the HTML will be stale.
    """
    path = os.path.join(OUT, name)
    if not os.path.exists(path):
        return name
    digest = hashlib.md5(open(path, "rb").read()).hexdigest()[:8]
    return "%s?v=%s" % (name, digest)


def alias(slug):
    return SLUG_ALIAS.get(slug, slug)


def public_url(slug):
    """The path Cloudflare actually serves a page at.

    wrangler.toml uses html_handling = "auto-trailing-slash", so about.html is
    served at /about and index.html at /. Canonical tags, Open Graph URLs,
    breadcrumbs, the sitemap and every internal link all use this form, so no
    link ever hits a redirect.
    """
    slug = alias(slug)
    if slug in ("index.html", ""):
        return "/"
    return "/" + slug[:-5] if slug.endswith(".html") else "/" + slug


def clarity_tag():
    """Microsoft Clarity snippet, or nothing at all.

    Returns "" when CLARITY_ID is empty so no broken <script> ships. Kept out
    of the critical path with async.
    """
    if not CLARITY_ID:
        return ""
    return ("\n<script type=\"text/javascript\">\n"
            "(function(c,l,a,r,i,t,y){c[a]=c[a]||function(){(c[a].q=c[a].q||[]).push(arguments)};\n"
            "t=l.createElement(r);t.async=1;t.src=\"https://www.clarity.ms/tag/\"+i;\n"
            "y=l.getElementsByTagName(r)[0];y.parentNode.insertBefore(t,y);\n"
            "})(window, document, \"clarity\", \"script\", \"%s\");\n"
            "</script>" % CLARITY_ID)


def esc(s):
    return html.escape(s, quote=False)

EXTERNAL_REL = "noopener"

INLINE_LINK_RE = re.compile(r'\[([^\]]+)\]\(([^)\s]+)(?:\s+"([^"]*)")?\)')

def rich(text):
    """Render prose, escaping normally but converting exactly [text](url)
    into a real link. Internal targets use the same 'slug.html' / 'index.html'
    convention as every other link in this file, so rewrite_links() turns them
    into the extensionless form Cloudflare serves at write time.

    External links (http/https) open in a new tab with rel="noopener";
    EXTERNAL_REL is one constant so a paid placement can become
    rel="sponsored" with a one-line change. An optional quoted title of
    "nf" adds nofollow to that one link."""
    out = []
    pos = 0
    for m in INLINE_LINK_RE.finditer(text):
        out.append(esc(text[pos:m.start()]))
        label, url, title = m.group(1), m.group(2), m.group(3)
        if url.startswith("http://") or url.startswith("https://"):
            rel = EXTERNAL_REL + (" nofollow" if title == "nf" else "")
            out.append('<a class="ext-link" href="%s" target="_blank" rel="%s">%s</a>'
                       % (html.escape(url, quote=True), rel, esc(label)))
        else:
            rel = ' rel="nofollow"' if title == "nf" else ""
            out.append('<a href="%s"%s>%s</a>' % (esc(url), rel, esc(label)))
        pos = m.end()
    out.append(esc(text[pos:]))
    return "".join(out)

# ---------------------------------------------------------------- site map
# Defined up here, before block parsing, so N_SERVICES can size the content
# file's expected block count. Adding a page beyond the template's original
# six means one new entry here and nothing else - SERVICE_IMG, SEO_LABELS,
# EXPECTED_BLOCKS and the parsed-block indices all derive from this list.
SERVICE_PAGES = [
    # slug (legacy slugs from the old SitePanda site, kept exactly), title, short.
    # "close-and-open-cell-spray-foam" is the live spelling - "close", not
    # "closed". It is what Google has indexed. Do not tidy it.
    ("attic-insulation.html",              "Attic Insulation",            "Attic"),
    ("garage-insulation.html",             "Garage Insulation",           "Garage"),
    ("basement-insulation.html",           "Basement Insulation",         "Basement"),
    ("crawl-space-insulation.html",        "Crawl Space Insulation",      "Crawl Space"),
    ("new-construction-insulation.html",   "New Construction Insulation", "New Construction"),
    ("close-and-open-cell-spray-foam.html","Closed Cell and Open Cell Spray Foam",
     "Closed and Open Cell"),
]
N_SERVICES = len(SERVICE_PAGES)
SERVICE_IMG = {slug: "images/service-%s.jpg" % slug[:-5] for slug, _, _ in SERVICE_PAGES}

# ---------------------------------------------------------------- parse md
raw = open(SRC, encoding="utf-8").read()
blocks = [b.strip() for b in re.split(r'\n---\n', raw) if b.strip()]

PAGE_MARKER = re.compile(r'^# (HOME PAGE|SERVICE PAGE \d+|ABOUT PAGE|CONTACT PAGE|FAQ SECTION|SEO TITLES AND META DESCRIPTIONS|SITE COPY)\s*$')

def parse_block(block):
    """-> (h1, [ {title, nodes:[('p'|'h3', text)]} ])"""
    lines = block.split("\n")
    h1 = None
    sections = []
    cur = None
    buf = []

    def flush_para():
        if buf:
            text = " ".join(x.strip() for x in buf if x.strip())
            if text and cur is not None:
                cur["nodes"].append(("p", text))
            del buf[:]

    for ln in lines:
        if PAGE_MARKER.match(ln.strip()):
            continue
        if ln.startswith("### "):
            flush_para()
            if cur is not None:
                cur["nodes"].append(("h3", ln[4:].strip()))
            continue
        if ln.startswith("## "):
            flush_para()
            cur = {"title": ln[3:].strip(), "nodes": []}
            sections.append(cur)
            continue
        if ln.startswith("# "):
            flush_para()
            h1 = ln[2:].strip()
            continue
        if not ln.strip():
            flush_para()
            continue
        buf.append(ln)
    flush_para()
    return h1, sections

# A finished content file has N_SERVICES+6 blocks separated by "---": home
# page, one per SERVICE_PAGES entry, about, contact, FAQ, the SEO table, and
# SITE COPY. Fail with something readable rather than an IndexError deeper down.
EXPECTED_BLOCKS = N_SERVICES + 6
if len(blocks) < EXPECTED_BLOCKS:
    sys.exit(
        "\nContent file does not have the expected structure.\n"
        "  file:   %s\n"
        "  found:  %d section(s) separated by '---'\n"
        "  needed: %d  (home, %d service pages, about, contact, FAQ, SEO table,\n"
        "          SITE COPY)\n\n"
        "If you have just scaffolded a new city, the real copy has not been\n"
        "written into that file yet. See NEW-CITY.md for the content prompt.\n"
        % (CONTENT_FILE, len(blocks), EXPECTED_BLOCKS, N_SERVICES))

parsed = [parse_block(b) for b in blocks]
HOME     = parsed[0]
SERVICES = parsed[1:1 + N_SERVICES]
ABOUT    = parsed[1 + N_SERVICES]
CONTACT  = parsed[2 + N_SERVICES]
FAQPAGE  = parsed[3 + N_SERVICES]
SEO_BLOCK_INDEX  = 4 + N_SERVICES
COPY_BLOCK_INDEX = 5 + N_SERVICES

# ---------------------------------------------------------------- site copy
# The SITE COPY block holds every reusable string that used to be hardcoded in this file:
# CTA headings, form intros, badges, photo alt text. Keeping it in the markdown
# means each city writes its own, instead of ten sites sharing one sentence.
_sc_h1, _sc_secs = parsed[COPY_BLOCK_INDEX] if len(parsed) > COPY_BLOCK_INDEX else (None, [])
SITE_COPY = {}
for _sec in _sc_secs:
    SITE_COPY[_sec["title"]] = [t for k, t in _sec["nodes"] if k == "p"]


def sc(key, fallback=None):
    """One string from the SITE COPY block."""
    vals = SITE_COPY.get(key)
    if vals:
        return vals[0]
    if fallback is not None:
        return fallback
    raise SystemExit("SITE COPY block is missing a '## %s' section." % key)


def sc_lines(key):
    """A list - each source line becomes one item (used for hero badges)."""
    vals = SITE_COPY.get(key)
    if not vals:
        raise SystemExit("SITE COPY block is missing a '## %s' section." % key)
    out = []
    for v in vals:
        out.extend([x.strip() for x in v.split("\n") if x.strip()])
    return out


def sc_map(key):
    """'slug: text' lines parsed into a dict (used for photo alt text)."""
    out = {}
    for line in SITE_COPY.get(key, []):
        for part in line.split("\n"):
            if ":" in part:
                k, v = part.split(":", 1)
                out[k.strip()] = v.strip()
    return out


ALT_TEXT = sc_map("Photo Alt Text")


def warn_missing_alt(keys):
    """Alt text falling back to another city's wording is a real duplicate
    content risk, so say so loudly rather than failing silently."""
    missing = [k for k in keys if k not in ALT_TEXT]
    if missing:
        sys.stderr.write(
            "\nWARNING: no alt text in the SITE COPY block for:\n" +
            "".join("    %s\n" % m for m in missing) +
            "  Falling back to the PHOTOS table, which carries the previous\n"
            "  city's wording. Add a line per image under '## Photo Alt Text'.\n\n")

# SEO block -> {page label: (title, meta)}
seo = {}
cur_label = None
for ln in blocks[SEO_BLOCK_INDEX].split("\n"):
    ln = ln.strip()
    if ln.startswith("## "):
        cur_label = ln[3:].strip()
        seo[cur_label] = {}
    elif ln.startswith("SEO Title:"):
        seo[cur_label]["title"] = ln.split(":", 1)[1].strip()
    elif ln.startswith("Meta Description:"):
        seo[cur_label]["meta"] = ln.split(":", 1)[1].strip()

# ---------------------------------------------------------------- partials
def head(title, meta, slug, extra_ld=""):
    url = DOMAIN + public_url(slug)
    ld_local = {
        "@context": "https://schema.org",
        "@type": "HomeAndConstructionBusiness",
        "@id": DOMAIN + "/#business",
        "name": BUSINESS,
        "description": "Spray foam insulation for attics, garages, basements, crawl spaces, rim joists and new construction in %s and across %s." % (CITY_PROV, REGION),
        "url": DOMAIN + "/",
        "telephone": PHONE_DISPLAY,
        "image": DOMAIN + "/images/og-image.jpg",
        "logo": DOMAIN + "/images/logo.jpg",
        "priceRange": "$$",
        # Address is emitted ONLY when a real one has been supplied. The
        # inherited version always emitted it, so every page carried
        # "streetAddress": "PLACEHOLDER - add street address" in its JSON-LD.
        # A service-area business with no address is valid structured data;
        # one advertising a placeholder is not. Locality/region/country are
        # still useful on their own, so they stay.
        "address": dict(
            {"@type": "PostalAddress",
             "addressLocality": CITY,
             "addressRegion": PROVINCE_CODE,
             "addressCountry": COUNTRY},
            **({"streetAddress": STREET_ADDRESS}
               if not STREET_ADDRESS.startswith("PLACEHOLDER") else {}),
            **({"postalCode": POSTAL_CODE}
               if not POSTAL_CODE.startswith("PLACEHOLDER") else {})
        ),
        "geo": {"@type": "GeoCoordinates", "latitude": LATITUDE, "longitude": LONGITUDE},
        "openingHoursSpecification": [{
            "@type": "OpeningHoursSpecification",
            "dayOfWeek": OPENING_DAYS,
            "opens": OPENING_TIME, "closes": CLOSING_TIME
        }],
        "areaServed": [{"@type": "City", "name": n} for n in
            SERVICE_AREA],
        "hasOfferCatalog": {
            "@type": "OfferCatalog", "name": "Spray Foam Insulation Services",
            "itemListElement": [
                {"@type": "Offer", "itemOffered": {"@type": "Service", "name": t}}
                for _, t, _ in SERVICE_PAGES
            ]
        }
    }
    return f"""<!DOCTYPE html>
<html lang="en-CA">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<meta name="theme-color" content="{THEME_COLOR}">

<!-- ===== SEO: unique title + description ===== -->
<title>{esc(title)}</title>
<meta name="description" content="{esc(meta)}">
<meta name="robots" content="index, follow, max-image-preview:large">
<meta name="author" content="{BUSINESS}">
<meta name="geo.region" content="{COUNTRY}-{PROVINCE_CODE}">
<meta name="geo.placename" content="{CITY_PROV}">

<!-- CANONICAL PLACEHOLDER - replace {DOMAIN} with the live domain before launch -->
<link rel="canonical" href="{url}">

<!-- ===== Open Graph / social sharing ===== -->
<meta property="og:type" content="website">
<meta property="article:published_time" content="{SITE_PUBLISHED}">
<meta property="article:modified_time" content="{BUILD_DATE}">
<meta property="og:site_name" content="{BUSINESS}">
<meta property="og:locale" content="en_CA">
<meta property="og:title" content="{esc(title)}">
<meta property="og:description" content="{esc(meta)}">
<meta property="og:url" content="{url}">
<meta property="og:image" content="{DOMAIN}/images/og-image.jpg">
<meta property="og:image:width" content="1200">
<meta property="og:image:height" content="630">
<meta property="og:image:type" content="image/jpeg">
<meta property="og:image:alt" content="{BUSINESS} - spray foam insulation in {CITY_PROV}">
<meta name="twitter:card" content="summary_large_image">
<meta name="twitter:title" content="{esc(title)}">
<meta name="twitter:description" content="{esc(meta)}">
<meta name="twitter:image" content="{DOMAIN}/images/og-image.jpg">

<link rel="icon" href="images/favicon.ico" sizes="any">
<link rel="icon" type="image/png" sizes="32x32" href="images/icon-32.png">
<link rel="icon" type="image/png" sizes="16x16" href="images/icon-16.png">
<link rel="apple-touch-icon" sizes="180x180" href="images/icon-180.png">
<link rel="manifest" href="site.webmanifest">
<link rel="stylesheet" href="{asset_v("style.css")}">
<script src="{asset_v("script.js")}" defer></script>

<!-- ===== Schema.org: Local Business ===== -->
<script type="application/ld+json">
{json.dumps(ld_local, indent=2)}
</script>{extra_ld}{clarity_tag()}
</head>
<body>
<a class="skip-link" href="#main">Skip to main content</a>
"""

def header(active):
    def cls(page):
        return ' aria-current="page"' if page == active else ''
    sub = "\n".join(
        f'            <li><a href="{slug}"{cls(slug)}>{esc(title)}</a></li>'
        for slug, title, _ in SERVICE_PAGES)
    services_open = ' aria-current="page"' if active in [s[0] for s in SERVICE_PAGES] + ["services.html"] else ''
    return f"""
<!-- ============================= TOP UTILITY BAR ============================= -->
<div class="topbar">
  <div class="container topbar__inner">
    <p style="margin:0;">Serving {TOPBAR_AREA}</p>
    <p style="margin:0;">Free written estimates &middot; <a href="tel:{PHONE_HREF}">{PHONE_DISPLAY}</a></p>
  </div>
</div>

<!-- ============================= STICKY HEADER ============================= -->
<header class="site-header">
  <div class="container site-header__inner">

    <a class="logo" href="index.html" aria-label="{BUSINESS} home page">
      <img src="images/icon-96.png" alt="{BUSINESS} logo"
           width="44" height="44" fetchpriority="high">
      <span class="logo__text">
        <span class="logo__name">{BUSINESS}</span>
        <span class="logo__tag">{CITY_PROV}</span>
      </span>
    </a>

    <button class="nav-burger" type="button" aria-expanded="false"
            aria-controls="primary-nav" aria-label="Open main menu">
      <span></span><span></span><span></span>
    </button>

    <nav class="nav" id="primary-nav" aria-label="Main navigation">
      <ul class="nav__list">
        <li><a class="nav__link" href="index.html"{cls('index.html')}>Home</a></li>
        <li class="nav__item--has-menu">
          <button class="nav__link nav__toggle" type="button"
                  aria-expanded="false" aria-controls="services-menu"{services_open}>Services</button>
          <ul class="nav__submenu" id="services-menu">
            <li><a href="services.html"{cls('services.html')}>All Services</a></li>
{sub}
          </ul>
        </li>
        <li><a class="nav__link" href="about.html"{cls('about.html')}>About</a></li>
        <li><a class="nav__link" href="faq.html"{cls('faq.html')}>FAQ</a></li>
        <li><a class="nav__link" href="contact.html"{cls('contact.html')}>Contact</a></li>
      </ul>
      <div class="header-cta">
        <a class="btn btn--primary btn--sm" href="#quote">Get a Free Quote</a>
      </div>
    </nav>
  </div>
</header>
"""

def breadcrumbs(trail):
    """trail = [(label, href or None)]"""
    items = []
    ld = []
    for i, (label, href) in enumerate(trail, start=1):
        if href:
            items.append(f'<li><a href="{href}">{esc(label)}</a></li>')
        else:
            items.append(f'<li><span aria-current="page">{esc(label)}</span></li>')
        ld.append({"@type": "ListItem", "position": i, "name": label,
                   "item": DOMAIN + public_url(href or "index.html")})
    nav = f"""
<!-- ============================= BREADCRUMBS ============================= -->
<nav class="breadcrumbs" aria-label="Breadcrumb">
  <div class="container">
    <ol>
      {"".join(items)}
    </ol>
  </div>
</nav>
"""
    schema = "\n<script type=\"application/ld+json\">\n" + json.dumps(
        {"@context": "https://schema.org", "@type": "BreadcrumbList", "itemListElement": ld},
        indent=2) + "\n</script>"
    return nav, schema

SERVICE_OPTIONS = "\n".join(
    f'            <option value="{esc(t)}">{esc(t)}</option>' for _, t, _ in SERVICE_PAGES)

def form_fields(pfx, compact=False):
    """The six intake fields. `pfx` keeps ids unique when a page carries
    more than one form (hero card + full section)."""
    rows = "" if compact else ""
    return f"""
          <div class="field">
            <label for="{pfx}-name">Name <span class="req" aria-hidden="true">*</span></label>
            <input type="text" id="{pfx}-name" name="name" autocomplete="name"
                   data-label="Name" placeholder="Your full name" required>
            <span class="field__error" aria-live="polite"></span>
          </div>

          <div class="field">
            <label for="{pfx}-phone">Phone <span class="req" aria-hidden="true">*</span></label>
            <input type="tel" id="{pfx}-phone" name="phone" autocomplete="tel"
                   data-label="Phone" placeholder="289-000-0000" required>
            <span class="field__error" aria-live="polite"></span>
          </div>

          <div class="field">
            <label for="{pfx}-email">Email <span class="req" aria-hidden="true">*</span></label>
            <input type="email" id="{pfx}-email" name="email" autocomplete="email"
                   data-label="Email" placeholder="you@example.com" required>
            <span class="field__error" aria-live="polite"></span>
          </div>

          <div class="field">
            <label for="{pfx}-city">City <span class="req" aria-hidden="true">*</span></label>
            <input type="text" id="{pfx}-city" name="city" autocomplete="address-level2"
                   data-label="City" placeholder="{CITY}" required>
            <span class="field__error" aria-live="polite"></span>
          </div>

          <div class="field field--full">
            <label for="{pfx}-service">Service Interested In <span class="req" aria-hidden="true">*</span></label>
            <select id="{pfx}-service" name="service" data-label="Service interested in" required>
            <option value="">Please choose a service</option>
{SERVICE_OPTIONS}
            <option value="Not sure yet">Not sure yet - please advise</option>
            </select>
            <span class="field__error" aria-live="polite"></span>
          </div>

          <div class="field field--full">
            <label for="{pfx}-message">Message <span class="req" aria-hidden="true">*</span></label>
            <textarea id="{pfx}-message" name="message" data-label="Message" required
                      {'rows="3"' if compact else ''}
                      placeholder="Tell us the approximate square footage, what the building is used for, and the current condition of the slab."></textarea>
            <span class="field__error" aria-live="polite"></span>
          </div>

          <!-- Honeypot: hidden from people, filled in by bots. Not a real field. -->
          <div class="field field--full" aria-hidden="true"
               style="position:absolute;left:-9999px;width:1px;height:1px;overflow:hidden;">
            <label for="{pfx}-botcheck">Leave this field empty</label>
            <input type="text" id="{pfx}-botcheck" name="botcheck" tabindex="-1" autocomplete="off">
          </div>
"""


def success_message(pfx):
    return f"""      <div class="form-success" role="status" aria-live="polite">
        <div>
          <strong>Thanks &mdash; your request has been received.</strong>
          {esc(sc("Form Success Message"))}
          For anything urgent, call <a href="tel:{PHONE_HREF}">{PHONE_DISPLAY}</a>.
        </div>
      </div>"""


def hero_form(page_label):
    """Compact estimate form that sits in the right of the hero."""
    return f"""      <div class="hero-form" id="hero-quote">
        <h2 class="hero-form__title" id="hero-form-heading">{esc(sc("Hero Form Heading"))}</h2>
        <p class="hero-form__sub">{esc(sc("Hero Form Intro"))}
          You can also call <a href="tel:{PHONE_HREF}">{PHONE_DISPLAY}</a>.</p>

{success_message('hf')}

        <form class="lead-form" action="#" method="post" novalidate
              data-source="{esc(page_label)} hero" aria-labelledby="hero-form-heading">
          <div class="form-grid">
{form_fields('hf', compact=True)}
            <div class="field field--full">
              <button class="btn btn--primary btn--block" type="submit">{esc(sc("Hero Form Button"))}</button>
              <p class="form-note">{esc(sc("Hero Form Note"))}</p>
            </div>
          </div>
        </form>
      </div>"""


def contact_form(page_label):
    """Full lead intake form - repeated on every page."""
    return f"""
<!-- ============================= LEAD INTAKE FORM ============================= -->
<section class="section section--alt" id="quote" aria-labelledby="quote-heading">
  <div class="container container--narrow">
    <div class="section-head is-centered">
      <span class="eyebrow">Free Estimate</span>
      <h2 id="quote-heading">{esc(sc("Form Section Heading"))}</h2>
      <p class="lead">{esc(sc("Form Section Intro"))}
        If you would rather talk it through, call <a href="tel:{PHONE_HREF}">{PHONE_DISPLAY}</a>.</p>
    </div>

    <div class="form-wrap">
      <!-- Success message: revealed by script.js after successful validation -->
{success_message('lf')}

      <!-- BACKEND: set SHEET_ENDPOINT in script.js to deliver these to your Google Sheet. -->
      <form class="lead-form" action="#" method="post" novalidate
            data-source="{esc(page_label)}" aria-labelledby="quote-heading">
        <div class="form-grid">
{form_fields('lf')}
          <div class="field field--full">
            <button class="btn btn--primary btn--lg btn--block" type="submit">Request an Estimate</button>
            <p class="form-note"><span class="req" aria-hidden="true">*</span>
              {esc(sc("Form Section Note"))}</p>
          </div>

        </div>
      </form>
    </div>
  </div>
</section>
"""


def cta_band(heading, text, variant=1):
    if variant == 1:
        buttons = f"""<a class="btn btn--primary btn--lg" href="#quote">Get a Free Quote</a>
        <a class="btn btn--ghost btn--lg" href="tel:{PHONE_HREF}">Call Now: {PHONE_DISPLAY}</a>"""
    else:
        buttons = f"""<a class="btn btn--primary btn--lg" href="#quote">Book Your Consultation</a>
        <a class="btn btn--ghost btn--lg" href="contact.html">Contact Us Today</a>"""
    return f"""
<!-- ============================= CTA BAND ============================= -->
<section class="cta-band" aria-label="Contact call to action">
  <div class="container">
    <h2>{esc(heading)}</h2>
    <p>{esc(text)}</p>
    <div class="btn-row is-centered">
        {buttons}
    </div>
  </div>
</section>
"""

CTA_INLINE = f"""
      <!-- Mid-content conversion prompt -->
      <aside class="cta-inline" aria-label="Estimate call to action">
        <p>{esc(sc("Inline CTA Text"))}</p>
        <div class="btn-row">
          <a class="btn btn--primary" href="#quote">Request an Estimate</a>
          <a class="btn btn--outline" href="tel:{PHONE_HREF}">Call Now</a>
        </div>
      </aside>
"""

SIDEBAR = f"""
      <!-- Sticky conversion sidebar -->
      <aside class="sidebar" aria-labelledby="sidebar-heading">
        <div class="card">
          <h3 id="sidebar-heading">{esc(sc("Sidebar Heading"))}</h3>
          <p>{esc(sc("Sidebar Text"))}</p>
          <p><a class="footer-phone" style="color:var(--color-accent-dark) !important;" href="tel:{PHONE_HREF}">{PHONE_DISPLAY}</a></p>
          <div class="btn-row">
            <a class="btn btn--primary btn--block" href="#quote">Get a Free Quote</a>
            <a class="btn btn--outline btn--block" href="contact.html">Contact Us Today</a>
          </div>
        </div>
        <div class="panel" style="margin-top:var(--space-5);">
          <h3>Spray Foam Insulation Services</h3>
          <ul class="footer-list" style="padding:0;">
            {"".join(f'<li><a href="{s}" style="color:var(--color-primary-light);">{esc(t)}</a></li>' for s, t, _ in SERVICE_PAGES)}
          </ul>
        </div>
      </aside>
"""

def intro_band(inner, label):
    """Intro prose sits BELOW the hero, never on it. Owner's standing rule:
    the hero carries the eyebrow, H1, badges, buttons and form only."""
    return f"""
<!-- ============================= INTRO (below the hero) ============================= -->
<section class="intro-band" aria-label="{esc(label)}">
  <div class="container container--narrow prose">
{inner}
  </div>
</section>
"""


def footer():
    svc = "".join(f'<li><a href="{s}">{esc(t)}</a></li>' for s, t, _ in SERVICE_PAGES)
    return f"""
<!-- ============================= FOOTER ============================= -->
<footer class="site-footer">
  <div class="container">
    <div class="footer-grid">

      <div class="footer-brand">
        <a class="footer-logo" href="index.html" aria-label="{BUSINESS} home page">
          <img src="images/wordmark-light-300.png"
               alt="{BUSINESS}" width="300" height="300" loading="lazy">
        </a>
        <p>{esc(sc("Footer Description"))}</p>
        <a class="footer-phone" href="tel:{PHONE_HREF}">{PHONE_DISPLAY}</a>
      </div>

      <nav aria-labelledby="footer-nav-heading">
        <h3 id="footer-nav-heading">Navigation</h3>
        <ul class="footer-list">
          <li><a href="index.html">Home</a></li>
          <li><a href="services.html">Services</a></li>
          <li><a href="about.html">About Us</a></li>
          <li><a href="faq.html">FAQ</a></li>
          <li><a href="contact.html">Contact</a></li>
        </ul>
      </nav>

      <nav aria-labelledby="footer-svc-heading">
        <h3 id="footer-svc-heading">Services</h3>
        <ul class="footer-list">{svc}</ul>
      </nav>

      <div>
        <h3>Contact Information</h3>
        <ul class="footer-list">
          <li>{BUSINESS}</li>
          <li>{CITY_PROV}</li>
          <li>Phone: <a href="tel:{PHONE_HREF}">{PHONE_DISPLAY}</a></li>
          <li>Hours: {HOURS_TEXT}</li>
          <li><!-- PLACEHOLDER: add street address and email once confirmed --></li>
        </ul>
        <div class="btn-row">
          <a class="btn btn--primary btn--sm" href="#quote">Get a Free Quote</a>
        </div>
      </div>

    </div>

    <div class="footer-bottom">
      <p style="margin:0;">&copy; <span data-year>2026</span> {BUSINESS}. All rights reserved.</p>
      <ul class="footer-legal">
        <li><a href="privacy-policy.html">Privacy Policy</a></li>
        <li><a href="terms.html">Terms &amp; Conditions</a></li>
        <li><a href="contact.html">Contact</a></li>
      </ul>
    </div>
  </div>
</footer>

<!-- Sticky mobile call bar -->
<div class="call-bar" role="region" aria-label="Quick contact">
  <a class="btn btn--primary" href="tel:{PHONE_HREF}">Call Now</a>
  <a class="btn btn--secondary" href="#quote">Get a Free Quote</a>
</div>

<!-- Scroll to top -->
<button class="to-top" type="button" aria-label="Scroll back to top of page">
  <svg viewBox="0 0 24 24" aria-hidden="true" focusable="false"><path d="M12 4l8 8h-5v8H9v-8H4z"/></svg>
</button>

</body>
</html>
"""

# ---------------------------------------------------------------- renderers
def nodes_html(nodes, indent="        "):
    out = []
    for kind, text in nodes:
        if kind == "p":
            out.append(f"{indent}<p>{rich(text)}</p>")
        else:
            out.append(f"{indent}<h3>{esc(text)}</h3>")
    return "\n".join(out)

def content_block(sec, level="h2"):
    return f"""      <section class="content-block">
        <{level}>{esc(sec['title'])}</{level}>
{nodes_html(sec['nodes'])}
      </section>
"""

def faq_accordion(sec, id_prefix):
    """Convert h3/p pairs inside a FAQ section into an accessible accordion."""
    pairs = []
    q = None
    ans = []
    for kind, text in sec["nodes"]:
        if kind == "h3":
            if q: pairs.append((q, ans)); ans = []
            q = text
        else:
            ans.append(text)
    if q: pairs.append((q, ans))

    items = []
    for i, (question, answers) in enumerate(pairs, start=1):
        body = "\n".join(f"          <p>{esc(a)}</p>" for a in answers)
        items.append(f"""      <div class="faq__item">
        <h3 class="faq__question">
          <button class="faq__trigger" type="button" id="{id_prefix}-q{i}"
                  aria-expanded="false" aria-controls="{id_prefix}-a{i}">
            <span>{esc(question)}</span>
            <span class="faq__icon" aria-hidden="true"></span>
          </button>
        </h3>
        <div class="faq__panel" id="{id_prefix}-a{i}" role="region" aria-labelledby="{id_prefix}-q{i}">
{body}
        </div>
      </div>""")

    ld = {"@context": "https://schema.org", "@type": "FAQPage",
          "mainEntity": [{"@type": "Question", "name": qq,
                          "acceptedAnswer": {"@type": "Answer", "text": " ".join(aa)}}
                         for qq, aa in pairs]}
    html_out = f"""
<!-- ============================= FAQ ACCORDION ============================= -->
<section class="section section--alt" id="faq" aria-labelledby="faq-heading">
  <div class="container">
    <div class="section-head is-centered">
      <span class="eyebrow">Answers</span>
      <h2 id="faq-heading">{esc(sec['title'])}</h2>
    </div>
    <div class="faq">
{chr(10).join(items)}
    </div>
    <div class="btn-row is-centered">
      <a class="btn btn--secondary" href="faq.html">Read More Questions</a>
      <a class="btn btn--primary" href="#quote">Get a Free Quote</a>
    </div>
  </div>
</section>
"""
    return html_out, "\n<script type=\"application/ld+json\">\n" + json.dumps(ld, indent=2) + "\n</script>"

def services_grid(exclude=None, heading=None, intro=None):
    heading = heading if heading is not None else sc("Services Grid Heading")
    intro   = intro   if intro   is not None else sc("Services Grid Intro")
    cards = []
    for i, (slug, title, _) in enumerate(SERVICE_PAGES):
        if slug == exclude:
            continue
        blurb = SERVICES[i][1][0]["nodes"][0][1]
        cards.append(f"""      <article class="service-card">
        <div class="service-card__media">
{picture(os.path.splitext(os.path.basename(SERVICE_IMG[slug]))[0],
         "(max-width: 620px) 92vw, (max-width: 1024px) 45vw, 340px", indent="          ")}
        </div>
        <div class="service-card__body">
          <h3><a href="{slug}" style="text-decoration:none;color:inherit;">{esc(title)}</a></h3>
          <p>{rich(blurb)}</p>
          <a class="service-card__link" href="{slug}">View {esc(title)}</a>
        </div>
      </article>""")
    return f"""
<!-- ============================= SERVICES GRID ============================= -->
<section class="section" id="services" aria-labelledby="services-heading">
  <div class="container">
    <div class="section-head is-centered">
      <span class="eyebrow">Spray Foam Insulation</span>
      <h2 id="services-heading">{esc(heading)}</h2>
      <p class="lead">{esc(intro)}</p>
    </div>
    <div class="grid grid--3">
{chr(10).join(cards)}
    </div>
    <div class="btn-row is-centered">
      <a class="btn btn--primary btn--lg" href="#quote">Get a Free Quote</a>
      <a class="btn btn--outline btn--lg" href="services.html">All Insulation Services</a>
    </div>
  </div>
</section>
"""


# ---------------------------------------------------------------- images
# Real project photography, exported as WebP with a JPG fallback at two
# widths each. width/height are always set so the browser reserves space
# and the layout does not shift while images load (CLS).
PHOTOS = {}

def _init_photos():
    """Derive the width/height/fallback-alt table from PAGE_PHOTOS so the two
    can never drift. Called right after PAGE_PHOTOS is defined below. A photo
    missing here used to throw KeyError deep inside rendering."""
    for _src, base, aspect, widths, alt in PAGE_PHOTOS:
        if base == "og-image":
            continue
        w = widths[0]
        PHOTOS[base] = {"widths": widths, "w": w,
                        "h": int(round(w * aspect[1] / aspect[0])), "alt": alt}


def picture(base, sizes, eager=False, alt=None, indent="        "):
    """Responsive <picture>: WebP first, JPG fallback for older browsers.

    Alt text is read from the SITE COPY block in the markdown, so each city
    writes its own rather than every site sharing the same sentence. The
    PHOTOS table below is only a fallback."""
    p = PHOTOS[base]
    if alt is None:
        alt = ALT_TEXT.get(base)
    webp = ", ".join("images/%s-%d.webp %dw" % (base, x, x) for x in p["widths"])
    jpg  = ", ".join("images/%s-%d.jpg %dw"  % (base, x, x) for x in p["widths"])
    loading = 'fetchpriority="high"' if eager else 'loading="lazy"'
    a = esc(alt or p["alt"])
    i = indent
    return (
f'{i}<picture>\n'
f'{i}  <source type="image/webp" srcset="{webp}" sizes="{sizes}">\n'
f'{i}  <img src="images/{base}-{p["widths"][0]}.jpg" srcset="{jpg}" sizes="{sizes}"\n'
f'{i}       alt="{a}" width="{p["w"]}" height="{p["h"]}" {loading} decoding="async">\n'
f'{i}</picture>')



# ==========================================================================
#  IMAGE PIPELINE  (only runs with --images; requires Pillow)
#  Photos are centre-cropped, resized, then exported as WebP + JPG.
# ==========================================================================
HERO_IMG     = "hero-spray-foam-insulation-%s" % CITY_SLUG
ABOUT_IMG    = "about-%s-spray-foam-insulation" % CITY_SLUG
SERVICES_IMG = "services-spray-foam-insulation-%s" % CITY_SLUG

PAGE_PHOTOS = [
  ("Finished Attic Spray Foam.png", HERO_IMG, (4,3), [800,1200],
   f"Attic in a {CITY} home finished ridge to eaves in spray foam insulation"),
  ("Finished Attic Spray Foam.png", "og-image", (1200,630), [1200],
   f"{BUSINESS} attic, garage, basement and crawl space spray foam insulation"),
  ("Spray Foam on Roof.png", "service-attic-insulation", (16,10), [640,960],
   f"Attic insulation going onto the underside of a roof deck between the rafters in {CITY}"),
  ("Garage Wall with Spray Foam Insulation.png", "service-garage-insulation", (16,10), [640,960],
   f"Garage insulation carried across the wall and up to the ceiling in a {CITY} home"),
  ("Basement walls getting insulated with spray foam.png", "service-basement-insulation",
   (16,10), [640,960],
   f"Closed cell spray foam basement insulation going onto a foundation wall in {CITY_PROV}"),
  ("Crawlspace Spray Foam.png", "service-crawl-space-insulation", (16,10), [640,960],
   f"Crawl space insulation sealing a perimeter wall over a taped ground sheet in {REGION}"),
  ("Two Storey Great Room.png", "service-new-construction-insulation", (16,10), [640,960],
   f"New construction insulation filling open stud bays before drywall in a {CITY} build"),
  ("Spray Foam Close UP.png", "service-close-and-open-cell-spray-foam", (16,10), [640,960],
   "Closed cell spray foam expanding out of the gun into a framed stud bay"),
  ("Crawl Space Installation.png", ABOUT_IMG, (4,3), [800,1200],
   f"A {BUSINESS} installer working a crawl space in full protective kit"),
  ("Basement fully insulated with spray foam.png", SERVICES_IMG, (4,3), [800,1200],
   f"Finished basement with every foundation wall sealed in spray foam insulation in {CITY}"),
]
_init_photos()


GALLERY_PHOTOS = [
 ("Finished Attic Spray Foam.png", "attic-finished-ridge-to-eaves",
  "Attic insulation finished from the ridge down to the eaves"),
 ("Basement fully insulated with spray foam.png", "basement-foundation-walls-sealed",
  "Basement with every foundation wall sealed in closed cell spray foam"),
 ("Crawlspace Spray Foam 2.png", "crawl-space-sheeted-and-sealed",
  "Crawl space insulation sealed over a taped ground sheet"),
 ("Crawl Space Installation.png", "crawl-space-installer-at-work",
  "Installer spraying foam insulation along a crawl space wall"),
 ("Old Wall Re-insulation.png", "century-home-wall-stripped-back",
  "Century home wall stripped back to bare framing before new insulation"),
 ("Basement walls getting insulated with spray foam.png", "basement-wall-in-progress",
  "Closed cell spray foam going onto a basement foundation wall"),
 ("Spray Foam on Roof.png", "roof-deck-between-rafters",
  "Spray foam insulation applied to a roof deck between the rafters"),
 ("Two Storey Great Room.png", "new-build-stud-bays",
  "Stud bays in a new two storey build filled with spray foam insulation"),
 ("Attic Insulation.png", "attic-rafters-sprayed",
  "Attic rafters sprayed with insulation from the ridge down"),
 ("Garage Wall with Spray Foam Insulation.png", "garage-wall-finished",
  "Garage wall insulation finished from the slab to the ceiling"),
]


# og-image is the social share graphic, never rendered as an <img>, so it
# needs no alt text.
warn_missing_alt([x[1] for x in PAGE_PHOTOS if x[1] != "og-image"] +
                 ["gallery-" + x[1] for x in GALLERY_PHOTOS])


def build_images():
    from PIL import Image, ImageFilter

    def export(src, base, aspect, widths):
        im = Image.open(os.path.join(ROOT, src)).convert("RGB")
        ar = aspect[0] / aspect[1]
        w, h = im.size
        if w / h > ar:
            nw = int(h * ar); im = im.crop(((w - nw)//2, 0, (w - nw)//2 + nw, h))
        else:
            nh = int(w / ar); im = im.crop((0, (h - nh)//2, w, (h - nh)//2 + nh))
        for width in widths:
            rs = im.resize((width, int(round(width / ar))), Image.LANCZOS)
            # Light pre-filter: the flake speckle is high-frequency detail that
            # inflates file size with no visible gain at display sizes.
            rs = rs.filter(ImageFilter.GaussianBlur(0.35))
            rs.save(os.path.join(IMG, "%s-%d.webp" % (base, width)),
                    "WEBP", quality=66, method=6)
            rs.save(os.path.join(IMG, "%s-%d.jpg" % (base, width)),
                    "JPEG", quality=72, optimize=True, progressive=True)

    for src, base, aspect, widths, _alt in PAGE_PHOTOS:
        export(src, base, aspect, widths)
        print("  image  %s" % base)

    for src, slug, _cap in GALLERY_PHOTOS:
        export(src, "gallery-" + slug, (4, 3), [400, 1000])
        print("  image  gallery-%s" % slug)

    # Social share image needs a plain, predictable name for scrapers
    src = os.path.join(IMG, "og-image-1200.jpg")
    if os.path.exists(src):
        os.replace(src, os.path.join(IMG, "og-image.jpg"))
    stale = os.path.join(IMG, "og-image-1200.webp")
    if os.path.exists(stale):
        os.remove(stale)


# ---------------------------------------------------------------- gallery
GALLERY = [{"slug": s, "caption": c} for _, s, c in GALLERY_PHOTOS]

GALLERY_ITEM = (
'      <li class="gallery__item">\n'
'        <button class="gallery__btn" type="button"\n'
'                data-large="images/gallery-{s}-1000.webp"\n'
'                data-large-fallback="images/gallery-{s}-1000.jpg"\n'
'                data-caption="{c}"\n'
'                aria-label="View a larger photo: {c}">\n'
'          <picture>\n'
'            <source type="image/webp" srcset="images/gallery-{s}-400.webp">\n'
'            <img src="images/gallery-{s}-400.jpg" alt="{c}"\n'
'                 width="400" height="300" loading="lazy" decoding="async">\n'
'          </picture>\n'
'          <span class="gallery__caption">{c}</span>\n'
'        </button>\n'
'      </li>')

def gallery_section():
    """Project gallery. Thumbnails are lazy-loaded; the 1000px version is only
    fetched when a visitor actually opens the lightbox."""
    if not GALLERY:
        return ""
    items = [GALLERY_ITEM.format(s=g["slug"], c=esc(ALT_TEXT.get("gallery-" + g["slug"], g["caption"])))
             for g in GALLERY]
    return """
<!-- ============================= PROJECT GALLERY ============================= -->
<section class="section" id="gallery" aria-labelledby="gallery-heading">
  <div class="container">
    <div class="section-head is-centered">
      <span class="eyebrow">Our Work</span>
      <h2 id="gallery-heading">__GALLERY_HEADING__</h2>
      <p class="lead">__GALLERY_INTRO__</p>
    </div>
    <ul class="gallery">
__ITEMS__
    </ul>
    <div class="btn-row is-centered">
      <a class="btn btn--primary btn--lg" href="#quote">Get a Free Quote</a>
      <a class="btn btn--outline btn--lg" href="tel:__PHONE__">Call Now</a>
    </div>
  </div>
</section>

<!-- Lightbox dialog: stays hidden until a gallery thumbnail is activated -->
<div class="lightbox" id="lightbox" role="dialog" aria-modal="true"
     aria-label="Project photo viewer" hidden>
  <button class="lightbox__close" type="button" data-lb-close aria-label="Close photo viewer">&times;</button>
  <button class="lightbox__nav lightbox__nav--prev" type="button" data-lb-prev aria-label="Previous photo">&#8249;</button>
  <figure class="lightbox__figure">
    <img class="lightbox__img" id="lightbox-img" src="" alt=""
         width="1000" height="750" decoding="async">
    <figcaption class="lightbox__caption" id="lightbox-caption"></figcaption>
  </figure>
  <button class="lightbox__nav lightbox__nav--next" type="button" data-lb-next aria-label="Next photo">&#8250;</button>
</div>
""".replace("__ITEMS__", chr(10).join(items)).replace("__PHONE__", PHONE_HREF)\
           .replace("__GALLERY_HEADING__", esc(sc("Gallery Heading")))\
           .replace("__GALLERY_INTRO__", esc(sc("Gallery Intro")))

LINK_RE = re.compile(r'href="(?!https?:|//|#|tel:|mailto:)([A-Za-z0-9._/-]+)\.html([#?][^"]*)?"')

def rewrite_links(content):
    """Turn href="about.html" into href="/about" and index.html into "/".
    Keeps every link on the exact URL Cloudflare serves, so no click and no
    canonical tag ever lands on a 307 redirect."""
    def sub(m):
        name, tail = m.group(1), m.group(2) or ""
        name = alias(name + ".html")[:-5]
        target = "/" if name == "index" else "/" + name
        return 'href="%s%s"' % (target, tail)
    return LINK_RE.sub(sub, content)


def write(slug, content):
    content = rewrite_links(content)
    slug = alias(slug)
    with open(os.path.join(OUT, slug), "w", encoding="utf-8") as f:
        f.write(content)
    print("wrote", slug, len(content))


# ============================================================================
#  IMAGES (optional pass)
# ============================================================================
if BUILD_IMAGES:
    print("Rebuilding images...")
    build_images()

# ============================================================================
#  HOME PAGE
# ============================================================================
h1, secs = HOME
by_title = {s["title"]: s for s in secs}
hero_sec   = secs[0]
faq_sec    = by_title["Frequently Asked Questions"]
# Benefits and process are looked up by prefix too, further down, once
# section_starting() exists.
# Looked up by prefix, not exact text, so a different city's headings
# ("Why Choose Grimsby Spray Foam Insulation?") still resolve.
def section_starting(prefix):
    for sec in secs:
        if sec["title"].lower().startswith(prefix.lower()):
            return sec
    raise SystemExit("Home page markdown needs a section starting: " + prefix)

def section_containing(needle):
    for sec in secs:
        if needle.lower() in sec["title"].lower():
            return sec
    raise SystemExit("Home page markdown needs a section whose heading contains: " + needle)

why        = section_starting("Why Choose")
standards  = section_containing("Every")   # "What Every <trade> Job Gets"
areas      = section_starting("Serving")
benefits   = section_starting("What Are The Benefits")
process    = section_starting("What Happens During")

special = {hero_sec["title"], faq_sec["title"], benefits["title"],
           process["title"], why["title"], areas["title"], standards["title"]}
body_sections = [s for s in secs if s["title"] not in special]

hero_paras = "\n".join(f"      <p>{rich(t)}</p>" for k, t in hero_sec["nodes"] if k == "p")

# Benefit cards - one card per source paragraph (no text removed)
benefit_cards = "\n".join(f"""      <article class="feature">
        <div class="feature__icon" aria-hidden="true">&#10003;</div>
        <p>{esc(t)}</p>
      </article>""" for k, t in benefits["nodes"] if k == "p")

# Process steps - one step per source paragraph
step_cards = "\n".join(f"""      <li class="step">
        <p>{esc(t)}</p>
      </li>""" for k, t in process["nodes"] if k == "p")

# Standards callout - one commitment per source paragraph. Scotland layout
# profile. An earlier version of this block listed four things the business
# will NOT do; the owner asked for the same substance stated positively, so
# each line is now a commitment rather than a refusal.
standards_items = "\n".join(f"""        <li>{esc(t)}</li>"""
                            for k, t in standards["nodes"] if k == "p")
STANDARDS_BLOCK = f"""
<!-- ============================= HOW WE WORK ============================= -->
<section class="section" aria-labelledby="standards-heading">
  <div class="container container--narrow">
    <div class="panel panel--standards">
      <span class="eyebrow">How We Work</span>
      <h2 id="standards-heading">{esc(standards['title'])}</h2>
      <ul class="standards-list">
{standards_items}
      </ul>
    </div>
  </div>
</section>
"""

mid = len(body_sections) // 2
main_blocks = []
for i, s in enumerate(body_sections):
    main_blocks.append(content_block(s))
    if i == mid:
        main_blocks.append(CTA_INLINE)

faq_html, faq_ld = faq_accordion(faq_sec, "home-faq")

home = head(seo["Home Page"]["title"], seo["Home Page"]["meta"], "index.html", faq_ld)
home = home.replace('<link rel="stylesheet" href="%s">' % asset_v("style.css"),
    '<!-- Preload the LCP hero image so it starts downloading with the stylesheet -->\n'
    '<link rel="preload" as="image" href="images/%s-1200.jpg"\n'
    '      imagesrcset="images/%s-800.webp 800w, images/%s-1200.webp 1200w"\n'
    '      imagesizes="100vw" type="image/webp">\n'
    '<link rel="stylesheet" href="%s">' % (HERO_IMG, HERO_IMG, HERO_IMG, asset_v("style.css")))
home += header("index.html")
home += f"""
<main id="main">

<!-- ============================= HERO ============================= -->
<section class="hero hero--home" aria-labelledby="hero-heading">

  <!-- Background photograph. Decorative here, so it carries an empty alt and
       is hidden from assistive tech - the headline conveys the meaning. -->
  <div class="hero__bg" aria-hidden="true">
    <picture>
      <source type="image/webp"
              srcset="images/{HERO_IMG}-800.webp 800w, images/{HERO_IMG}-1200.webp 1200w"
              sizes="100vw">
      <img src="images/{HERO_IMG}-1200.jpg"
           srcset="images/{HERO_IMG}-800.jpg 800w, images/{HERO_IMG}-1200.jpg 1200w"
           sizes="100vw" alt="" width="1200" height="900"
           fetchpriority="high" decoding="async">
    </picture>
  </div>

  <div class="container hero__inner">

    <!-- Business name as a masthead across the top of the hero.
         Deliberately a paragraph, not a heading, so the page keeps exactly
         one top-level heading - the search term line directly beneath it. -->
    <p class="hero__brand">{BUSINESS}</p>

    <div class="hero__intro">
      <h1 id="hero-heading">{esc(h1)}</h1>
      <ul class="hero__badges">
{chr(10).join('        <li>%s</li>' % esc(b) for b in sc_lines("Hero Badges"))}
      </ul>
      <div class="btn-row">
        <a class="btn btn--primary btn--lg" href="tel:{PHONE_HREF}">Call Now: {PHONE_DISPLAY}</a>
        <a class="btn btn--ghost btn--lg" href="#services">See Our Services</a>
      </div>
    </div>

{hero_form("Home Page")}
  </div>
</section>

{intro_band(hero_paras, "Introduction")}

<!-- ============================= TRUST STRIP ============================= -->
<!-- Secondary service navigation. Built from SERVICE_PAGES so the labels and
     targets can never drift apart. -->
<nav class="trust-strip" aria-label="Spray foam insulation services">
  <div class="container">
    <ul>
{chr(10).join('      <li><a href="%s">%s</a></li>' % (slug, esc(title)) for slug, title, _ in SERVICE_PAGES)}
    </ul>
  </div>
</nav>

<!-- ============================= WHY CHOOSE US ============================= -->
<section class="section" aria-labelledby="why-heading">
  <div class="container container--narrow prose">
    <span class="eyebrow">Why Us</span>
    <h2 id="why-heading">{esc(why['title'])}</h2>
{nodes_html(why['nodes'], "    ")}
    <div class="btn-row">
      <a class="btn btn--primary" href="#quote">Request an Estimate</a>
      <a class="btn btn--outline" href="about.html">About {BUSINESS}</a>
    </div>
  </div>
</section>

{services_grid()}

{STANDARDS_BLOCK}

<!-- ============================= BENEFITS ============================= -->
<section class="section section--alt" aria-labelledby="benefits-heading">
  <div class="container">
    <div class="section-head is-centered">
      <span class="eyebrow">Benefits</span>
      <h2 id="benefits-heading">{esc(benefits['title'])}</h2>
    </div>
    <div class="grid grid--3">
{benefit_cards}
    </div>
  </div>
</section>

{cta_band(sc("Consultation CTA Heading"), sc("Consultation CTA Text"), 2)}

<!-- ============================= MAIN CONTENT ============================= -->
<section class="section" aria-labelledby="detail-heading">
  <div class="container">
    <h2 id="detail-heading" class="visually-hidden">Spray foam insulation information for {CITY} homeowners</h2>
    <div class="layout-split">
      <div class="prose">
{"".join(main_blocks)}      </div>
{SIDEBAR}
    </div>
  </div>
</section>

<!-- ============================= PROCESS ============================= -->
<section class="section section--alt" aria-labelledby="process-heading">
  <div class="container">
    <div class="section-head is-centered">
      <span class="eyebrow">Our Process</span>
      <h2 id="process-heading">{esc(process['title'])}</h2>
    </div>
    <ol class="steps grid grid--3">
{step_cards}
    </ol>
    <div class="btn-row is-centered">
      <a class="btn btn--primary btn--lg" href="#quote">Book Your Consultation</a>
    </div>
  </div>
</section>

{gallery_section()}

{cta_band(sc("Closing CTA Heading"), sc("Closing CTA Text"))}

<!-- ============================= SERVICE AREA + MAP ============================= -->
<section class="section section--alt" aria-labelledby="areas-heading">
  <div class="container">
    <div class="layout-split layout-split--even">
      <div class="prose">
        <span class="eyebrow">Service Area</span>
        <h2 id="areas-heading">{esc(areas['title'])}</h2>
{nodes_html(areas['nodes'], "        ")}
        <div class="btn-row">
          <a class="btn btn--primary" href="#quote">Get a Free Quote</a>
          <a class="btn btn--outline" href="contact.html">Contact Us Today</a>
        </div>
      </div>
      <div class="map-wrap">
        <iframe src="{MAP_EMBED}" title="Map of the {CITY_PROV} and {REGION} spray foam insulation service area"
                width="600" height="450" loading="lazy" referrerpolicy="no-referrer-when-downgrade"
                allowfullscreen></iframe>
      </div>
    </div>
  </div>
</section>

{contact_form("Home Page")}

{faq_html}
</main>
"""
home += footer()
write("index.html", home)

# ============================================================================
#  SERVICE PAGES
# ============================================================================
SEO_LABELS = [title for _, title, _ in SERVICE_PAGES]
NUM_WORDS = {6: "Six", 7: "Seven", 8: "Eight", 9: "Nine", 10: "Ten"}

for idx, (slug, title, short) in enumerate(SERVICE_PAGES):
    sh1, ssecs = SERVICES[idx]
    label = SEO_LABELS[idx]
    overview = ssecs[0]
    closing  = ssecs[-1]
    middle   = ssecs[1:-1]

    crumbs, crumb_ld = breadcrumbs([("Home", "index.html"), ("Services", "services.html"), (title, None)])

    service_ld = {
        "@context": "https://schema.org", "@type": "Service",
        "serviceType": title,
        "name": sh1,
        "description": seo[label]["meta"],
        "provider": {"@type": "HomeAndConstructionBusiness", "@id": DOMAIN + "/#business",
                     "name": BUSINESS, "telephone": PHONE_DISPLAY},
        "areaServed": {"@type": "City", "name": CITY_PROV},
        "url": DOMAIN + "/" + slug
    }
    extra_ld = crumb_ld + "\n<script type=\"application/ld+json\">\n" + json.dumps(service_ld, indent=2) + "\n</script>"

    over_paras = "\n".join(f"      <p>{rich(t)}</p>" for k, t in overview["nodes"] if k == "p")

    blocks_html = []
    for i, s in enumerate(middle):
        blocks_html.append(content_block(s))
        if i == len(middle) // 2:
            blocks_html.append(CTA_INLINE)

    page = head(seo[label]["title"], seo[label]["meta"], slug, extra_ld)
    page += header(slug)
    page += crumbs
    page += f"""
<main id="main">

<!-- ============================= HERO ============================= -->
<section class="hero hero--page" aria-labelledby="hero-heading">
  <div class="container hero__inner">
    <div class="hero__intro">
      <span class="eyebrow" style="color:var(--color-accent-light);">{esc(title)}</span>
      <h1 id="hero-heading">{esc(sh1)}</h1>
      <div class="btn-row">
        <a class="btn btn--primary btn--lg" href="#quote">Get a Free Quote</a>
        <a class="btn btn--ghost btn--lg" href="tel:{PHONE_HREF}">Call Now: {PHONE_DISPLAY}</a>
      </div>
    </div>
  </div>
</section>

{intro_band(over_paras, title + " overview")}

<!-- ============================= SERVICE DETAIL ============================= -->
<section class="section" aria-labelledby="detail-heading">
  <div class="container">
    <h2 id="detail-heading" class="visually-hidden">{esc(title)} details</h2>
    <div class="layout-split">
      <div class="prose">
{"".join(blocks_html)}      </div>
{SIDEBAR}
    </div>
  </div>
</section>

<!-- ============================= CLOSING CTA (from source copy) ============================= -->
<section class="cta-band" aria-labelledby="closing-heading">
  <div class="container">
    <h2 id="closing-heading">{esc(closing['title'])}</h2>
{nodes_html(closing['nodes'], "    ")}
    <div class="btn-row is-centered">
      <a class="btn btn--primary btn--lg" href="#quote">Request an Estimate</a>
      <a class="btn btn--ghost btn--lg" href="tel:{PHONE_HREF}">Call Now: {PHONE_DISPLAY}</a>
    </div>
  </div>
</section>

{services_grid(exclude=slug, heading=sc("Other Services Heading"), intro=sc("Other Services Intro"))}

{cta_band(sc("Service Page CTA Heading"), sc("Service Page CTA Text"), 2)}

{contact_form(title)}
</main>
"""
    page += footer()
    write(slug, page)

# ============================================================================
#  SERVICES HUB PAGE
# ============================================================================
crumbs, crumb_ld = breadcrumbs([("Home", "index.html"), ("Services", None)])
svc_page = head(f"Spray Foam Insulation Services | {CITY_PROV}",
                f"Attic, garage, basement, crawl space and new construction spray foam insulation in {CITY_PROV}. Free written quotes. Call {PHONE_DISPLAY}.",
                "services.html", crumb_ld)
svc_page += header("services.html")
svc_page += crumbs
svc_page += f"""
<main id="main">

<section class="hero hero--page hero--split" aria-labelledby="hero-heading">
  <div class="container hero__inner">
    <div class="hero__intro">
      <span class="eyebrow" style="color:var(--color-accent-light);">Services</span>
      <h1 id="hero-heading">{esc(sc("Services Page Heading"))}</h1>
      <div class="btn-row">
        <a class="btn btn--primary btn--lg" href="#quote">Get a Free Quote</a>
        <a class="btn btn--ghost btn--lg" href="tel:{PHONE_HREF}">Call Now: {PHONE_DISPLAY}</a>
      </div>
    </div>
    <div class="hero__media">
{picture(SERVICES_IMG, "(max-width: 1024px) 92vw, 460px", eager=True, indent="      ")}
    </div>
  </div>
</section>

{intro_band("    <p>%s</p>" % esc(sc("Services Page Intro")), "Introduction")}

{services_grid(heading=sc("Services Page Grid Heading"), intro=sc("Services Page Grid Intro"))}

{cta_band(sc("Services Page CTA Heading"), sc("Services Page CTA Text"), 2)}

{contact_form("Services")}
</main>
"""
svc_page += footer()
write("services.html", svc_page)

# ============================================================================
#  ABOUT PAGE
# ============================================================================
ah1, asecs = ABOUT
crumbs, crumb_ld = breadcrumbs([("Home", "index.html"), ("About Us", None)])
about_lead = asecs[0]
about_close = asecs[-1]
about_mid = asecs[1:-1]

mid_blocks = []
for i, s in enumerate(about_mid):
    mid_blocks.append(content_block(s))
    if i == len(about_mid) // 2:
        mid_blocks.append(CTA_INLINE)

about = head(seo["About Page"]["title"], seo["About Page"]["meta"], "about.html", crumb_ld)
about += header("about.html")
about += crumbs
about += f"""
<main id="main">

<section class="hero hero--page hero--split" aria-labelledby="hero-heading">
  <div class="container hero__inner">
    <div class="hero__intro">
      <span class="eyebrow" style="color:var(--color-accent-light);">About Us</span>
      <h1 id="hero-heading">{esc(ah1)}</h1>
      <div class="btn-row">
        <a class="btn btn--primary btn--lg" href="#quote">Get a Free Quote</a>
        <a class="btn btn--ghost btn--lg" href="tel:{PHONE_HREF}">Call Now: {PHONE_DISPLAY}</a>
      </div>
    </div>
    <div class="hero__media">
{picture(ABOUT_IMG, "(max-width: 1024px) 92vw, 460px", eager=True, indent="      ")}
    </div>
  </div>
</section>

{intro_band(("    <h2>%s</h2>" + chr(10) + "%s") % (esc(about_lead['title']), nodes_html(about_lead['nodes'], "    ")), "Introduction")}

<section class="section" aria-labelledby="about-heading">
  <div class="container">
    <h2 id="about-heading" class="visually-hidden">About {BUSINESS}</h2>
    <div class="layout-split">
      <div class="prose">
{"".join(mid_blocks)}      </div>
{SIDEBAR}
    </div>
  </div>
</section>

<section class="cta-band" aria-labelledby="about-close-heading">
  <div class="container">
    <h2 id="about-close-heading">{esc(about_close['title'])}</h2>
{nodes_html(about_close['nodes'], "    ")}
    <div class="btn-row is-centered">
      <a class="btn btn--primary btn--lg" href="#quote">Book Your Consultation</a>
      <a class="btn btn--ghost btn--lg" href="tel:{PHONE_HREF}">Call Now: {PHONE_DISPLAY}</a>
    </div>
  </div>
</section>

{services_grid(heading="Everything We Insulate", intro=f"{NUM_WORDS.get(N_SERVICES, str(N_SERVICES))} spray foam insulation services for {CITY} homes, garages and new builds.")}

{contact_form("About")}
</main>
"""
about += footer()
write("about.html", about)

# ============================================================================
#  CONTACT PAGE
# ============================================================================
ch1, csecs = CONTACT
crumbs, crumb_ld = breadcrumbs([("Home", "index.html"), ("Contact", None)])
c_by = {s["title"]: s for s in csecs}
info_sec = c_by["Contact Information"]
other = [s for s in csecs if s["title"] != "Contact Information"]
lead_sec = other[0]
rest = other[1:]

# "Contact Information" arrives as a single paragraph of label: value pairs
info_pairs = []
for k, t in info_sec["nodes"]:
    for part in re.split(r'\s(?=(?:Company|Phone|Location|Services):)', t):
        if ":" in part:
            lab, val = part.split(":", 1)
            info_pairs.append((lab.strip(), val.strip()))
info_html = "\n".join(
    f'        <div><dt style="font-weight:800;color:var(--color-heading);">{esc(l)}</dt>'
    f'<dd style="margin:0 0 var(--space-3);">'
    + (f'<a href="tel:{PHONE_HREF}">{esc(v)}</a>' if l.lower() == "phone" else esc(v))
    + '</dd></div>'
    for l, v in info_pairs)

rest_blocks = "".join(content_block(s) for s in rest)

contact_page = head(seo["Contact Page"]["title"], seo["Contact Page"]["meta"], "contact.html", crumb_ld)
contact_page += header("contact.html")
contact_page += crumbs
contact_page += f"""
<main id="main">

<section class="hero hero--page" aria-labelledby="hero-heading">
  <div class="container hero__inner">
    <div class="hero__intro">
      <span class="eyebrow" style="color:var(--color-accent-light);">Contact</span>
      <h1 id="hero-heading">{esc(ch1)}</h1>
      <div class="btn-row">
        <a class="btn btn--primary btn--lg" href="tel:{PHONE_HREF}">Call Now: {PHONE_DISPLAY}</a>
        <a class="btn btn--ghost btn--lg" href="#quote">Request an Estimate</a>
      </div>
    </div>
  </div>
</section>

{intro_band(("    <h2>%s</h2>" + chr(10) + "%s") % (esc(lead_sec['title']), nodes_html(lead_sec['nodes'], "    ")), "Introduction")}

<section class="section" aria-labelledby="contact-detail-heading">
  <div class="container">
    <h2 id="contact-detail-heading" class="visually-hidden">Contact details and what to expect</h2>
    <div class="layout-split">
      <div class="prose">
{rest_blocks}      </div>

      <aside class="sidebar" aria-labelledby="info-heading">
        <div class="card">
          <h3 id="info-heading">{esc(info_sec['title'])}</h3>
          <dl style="margin:0;">
{info_html}
          </dl>
          <!-- PLACEHOLDER: add email address, street address and Google Maps embed when available -->
          <div class="btn-row">
            <a class="btn btn--primary btn--block" href="tel:{PHONE_HREF}">Call Now</a>
            <a class="btn btn--outline btn--block" href="#quote">Get a Free Quote</a>
          </div>
        </div>
        <div class="panel" style="margin-top:var(--space-5);">
          <h3>Spray Foam Insulation Services</h3>
          <ul class="footer-list" style="padding:0;">
            {"".join(f'<li><a href="{s}" style="color:var(--color-primary-light);">{esc(t)}</a></li>' for s, t, _ in SERVICE_PAGES)}
          </ul>
        </div>
      </aside>
    </div>
  </div>
</section>

{cta_band(sc("Contact Page CTA Heading"), sc("Contact Page CTA Text"), 2)}

{contact_form("Contact")}
</main>
"""
contact_page += footer()
write("contact.html", contact_page)

# ============================================================================
#  FAQ PAGE
# ============================================================================
fh1, fsecs = FAQPAGE
crumbs, crumb_ld = breadcrumbs([("Home", "index.html"), ("FAQ", None)])
faq_body, faq_ld2 = faq_accordion(fsecs[0], "faq-page")
faq_page = head(seo["FAQ Page"]["title"], seo["FAQ Page"]["meta"], "faq.html", crumb_ld + faq_ld2)
faq_page += header("faq.html")
faq_page += crumbs
faq_page += f"""
<main id="main">

<section class="hero hero--page" aria-labelledby="hero-heading">
  <div class="container hero__inner">
    <div class="hero__intro">
      <span class="eyebrow" style="color:var(--color-accent-light);">Answers</span>
      <h1 id="hero-heading">{esc(sc("FAQ Page Heading"))}</h1>
      <div class="btn-row">
        <a class="btn btn--primary btn--lg" href="#quote">Get a Free Quote</a>
        <a class="btn btn--ghost btn--lg" href="tel:{PHONE_HREF}">Call Now: {PHONE_DISPLAY}</a>
      </div>
    </div>
  </div>
</section>

{intro_band("    <p>%s</p>" % esc(sc("FAQ Page Intro")), "Introduction")}

{cta_band(sc("FAQ Page CTA Heading"), sc("FAQ Page CTA Text"), 1)}

{faq_body}

{services_grid(heading="Every System We Offer", intro=f"Each page below covers cost, cure times and upkeep for that system in {CITY}.")}

{contact_form("FAQ")}
</main>
"""
faq_page += footer()
write("faq.html", faq_page)

# ============================================================================
#  PRIVACY POLICY  &  TERMS  (clearly labelled placeholder legal pages)
# ============================================================================
def legal_page(slug, title, meta, h1, eyebrow, crumb_label, sections):
    crumbs, crumb_ld = breadcrumbs([("Home", "index.html"), (crumb_label, None)])
    body = "".join(f"""      <section class="content-block">
        <h2>{esc(t)}</h2>
{chr(10).join(f'        <p>{esc(p)}</p>' for p in ps)}
      </section>
""" for t, ps in sections)
    page = head(title, meta, slug, crumb_ld)
    # Privacy and terms are boilerplate by nature and carry no ranking value.
    # Keeping them out of the index means they cannot count against a network
    # of city sites for near-duplicate content.
    page = page.replace('<meta name="robots" content="index, follow, max-image-preview:large">',
                        '<meta name="robots" content="noindex, follow">')
    page += header(slug) + crumbs + f"""
<main id="main">

<section class="hero hero--page" aria-labelledby="hero-heading">
  <div class="container hero__inner">
    <div class="hero__intro">
      <span class="eyebrow" style="color:var(--color-accent-light);">{esc(eyebrow)}</span>
      <h1 id="hero-heading">{esc(h1)}</h1>
    </div>
  </div>
</section>

{intro_band("    <p>PLACEHOLDER DOCUMENT. This page is a working template for %s and should be reviewed by a legal professional before the site goes live.</p>" % BUSINESS, "Introduction")}

<section class="section">
  <div class="container container--narrow prose">
{body}    </div>
  </div>
</section>

{cta_band("Questions About Your Floor Or Your Information?", f"Call {BUSINESS} and speak with a local installer.", 1)}

{contact_form(h1)}
</main>
""" + footer()
    write(slug, page)

legal_page(
    "privacy-policy.html",
    f"Privacy Policy | {CITY_PROV}",
    f"Privacy policy for {BUSINESS} covering how estimate requests are handled. Call us at {PHONE_DISPLAY} with any questions.",
    "Privacy Policy", "Legal", "Privacy Policy",
    sections=[
        ("Information We Collect", [
            "When you submit an estimate request on this website we collect the name, email address, phone number, city, service of interest and message that you provide.",
            "We do not collect payment information through this website."]),
        ("How We Use Your Information", [
            "Your details are used to respond to your estimate request, arrange a site visit, and provide a written quote.",
            "We do not sell, rent or trade your information to third parties."]),
        ("Cookies And Analytics", [
            "PLACEHOLDER: list any analytics or advertising tools installed on the site, such as Google Analytics or Meta Pixel, along with how visitors can opt out.",
            "This website does not set marketing cookies in its current form."]),
        ("Data Retention", [
            "Estimate requests are retained only as long as needed to serve the customer and meet record keeping requirements."]),
        ("Your Choices", [
            "You may ask us to correct or delete the information you have submitted at any time by calling " + PHONE_DISPLAY + "."]),
        ("Contact Us About Privacy", [
            "Questions about this policy can be directed to %s, %s, at %s." % (BUSINESS, CITY_PROV, PHONE_DISPLAY)]),
    ])

legal_page(
    "terms.html",
    f"Terms & Conditions | {CITY_PROV}",
    f"Terms and conditions placeholder for the {BUSINESS} website. Call us at {PHONE_DISPLAY} for estimate and warranty details.",
    "Terms & Conditions", "Legal", "Terms",
    sections=[
        ("Use Of This Website", [
            "The content on this website is provided for general information about spray foam insulation and air sealing services in %s." % CITY_PROV]),
        ("Estimates And Pricing", [
            "Prices described on this website are general ranges only. A binding price is provided in a written estimate after an on-site measurement and slab assessment."]),
        ("Workmanship And Warranty", [
            "Installations include a written warranty. PLACEHOLDER: insert the exact warranty term, coverage and exclusions supplied by %s." % BUSINESS]),
        ("Cure Times And Site Conditions", [
            "Stated cure times are typical and depend on slab temperature, humidity and the system installed. Written cure times are supplied at the end of every job."]),
        ("Limitation Of Liability", [
            "PLACEHOLDER: insert the limitation of liability wording reviewed by your legal advisor."]),
        ("Changes To These Terms", [
            "These terms may be updated from time to time. Questions can be directed to " + PHONE_DISPLAY + "."]),
    ])

# ============================================================================
#  PLACEHOLDER IMAGES  (lightweight inline SVG so the site is never broken)
# ============================================================================
# Logo, favicon and social images are all real artwork now, produced from
# Logo.png by tools/make-logo.py. Nothing here generates placeholders.

# ============================================================================
#  SITEMAP + ROBOTS + PROJECT README
# ============================================================================
# privacy-policy and terms are noindex, so they are deliberately absent here
all_pages = ["index.html", "services.html"] + [s for s, _, _ in SERVICE_PAGES] + \
            ["about.html", "faq.html", "contact.html"]
urls = "\n".join(
    f"""  <url>
    <loc>{DOMAIN}{public_url(p)}</loc>
    <changefreq>monthly</changefreq>
    <priority>{'1.0' if p == 'index.html' else ('0.9' if p in [s for s,_,_ in SERVICE_PAGES] else '0.7')}</priority>
  </url>""" for p in all_pages)
open(os.path.join(OUT, "sitemap.xml"), "w", encoding="utf-8").write(
f"""<?xml version="1.0" encoding="UTF-8"?>
<!-- PLACEHOLDER DOMAIN: replace {DOMAIN} with the live domain before submitting to Google Search Console -->
<urlset xmlns="http://www.sitemap.org/schemas/sitemap/0.9">
{urls}
</urlset>
""".replace("www.sitemap.org", "www.sitemaps.org"))

# Search and answer-engine crawlers are allowed explicitly. Naming them is
# not strictly required when User-agent: * already allows everything, but it
# is what AEO checkers look for and it documents the intent.
AI_CRAWLERS = ["OAI-SearchBot", "ChatGPT-User", "PerplexityBot",
               "Google-Extended", "ClaudeBot", "Claude-SearchBot", "Bingbot"]

open(os.path.join(OUT, "robots.txt"), "w", encoding="utf-8").write(
"User-agent: *\nAllow: /\n\n"
+ "".join("User-agent: %s\nAllow: /\n\n" % b for b in AI_CRAWLERS)
+ "Sitemap: %s/sitemap.xml\n" % DOMAIN)

# ---------------------------------------------------------------------------
#  WEB APP MANIFEST
#  Every page carries <link rel="manifest" href="site.webmanifest">, but the
#  inherited generator never wrote the file, so all 14 pages 404'd on it. Same
#  fault exists on the Halifax build it came from. Generated here so it cannot
#  go missing and theme_color cannot drift from THEME_COLOR.
# ---------------------------------------------------------------------------
open(os.path.join(OUT, "site.webmanifest"), "w", encoding="utf-8").write(
    json.dumps({
        "name": BUSINESS,
        "short_name": "%s Spray Foam" % CITY,
        "description": "Spray foam insulation in %s." % CITY_PROV,
        "start_url": "/",
        "display": "browser",
        "background_color": "#ffffff",
        "theme_color": THEME_COLOR,
        "icons": [
            {"src": "images/icon-192.png", "sizes": "192x192", "type": "image/png"},
            {"src": "images/icon-512.png", "sizes": "512x512", "type": "image/png"},
            {"src": "images/icon-512.png", "sizes": "512x512",
             "type": "image/png", "purpose": "maskable"},
        ],
    }, indent=2))

# ---------------------------------------------------------------------------
#  llms.txt - a plain-text map of the site for answer engines. Everything is
#  derived from CONFIG and SERVICE_PAGES, so it cannot drift out of step with
#  the pages that actually exist.
# ---------------------------------------------------------------------------
_llms = ["# %s" % BUSINESS, ""]
_llms.append("> Spray foam insulation for attics, garages, basements, crawl "
             "spaces, rim joists and new construction in %s and across %s."
             % (CITY_PROV, REGION))
_llms.append("")
_llms.append("Phone: %s" % PHONE_DISPLAY)
_llms.append("Service area: %s" % ", ".join(SERVICE_AREA))
_llms.append("Hours: %s" % HOURS_TEXT)
_llms.append("")
_llms.append("## Pages")
_llms.append("- [Home](%s/): spray foam insulation across %s." % (DOMAIN, REGION))
_llms.append("- [Services](%s/services): every insulation service we install."
             % DOMAIN)
for _slug, _title, _short in SERVICE_PAGES:
    _llms.append("- [%s](%s/%s): %s in %s."
                 % (_title, DOMAIN, _slug[:-5], _title.lower(), CITY_PROV))
_llms.append("- [About](%s/%s): who we are and how we quote."
             % (DOMAIN, SLUG_ALIAS.get("about.html", "about.html")[:-5]))
_llms.append("- [FAQ](%s/faq): costs, timelines and product questions." % DOMAIN)
_llms.append("- [Contact](%s/%s): free written quotes."
             % (DOMAIN, SLUG_ALIAS.get("contact.html", "contact.html")[:-5]))
_llms.append("")
open(os.path.join(OUT, "llms.txt"), "w", encoding="utf-8").write(
    "\n".join(_llms))


# ============================================================================
#  CLOUDFLARE: CACHE HEADERS + 404 PAGE
# ============================================================================
open(os.path.join(OUT, "_headers"), "w", encoding="utf-8").write(
"""# Cloudflare edge headers.
# Images, CSS and JS are content-addressed by name, so they can cache hard.
/images/*
  Cache-Control: public, max-age=31536000, immutable

# Fingerprinted in the HTML as style.css?v=<hash>, so these can cache hard.
# The hash changes whenever the file changes, which busts the cache instantly.
/style.css
  Cache-Control: public, max-age=86400, must-revalidate
/script.js
  Cache-Control: public, max-age=86400, must-revalidate

# HTML should revalidate so copy changes go live immediately
/*.html
  Cache-Control: public, max-age=0, must-revalidate

/*
  X-Content-Type-Options: nosniff
  Referrer-Policy: strict-origin-when-cross-origin
  X-Frame-Options: SAMEORIGIN
  Permissions-Policy: geolocation=(), microphone=(), camera=()
""")

notfound = head(f"Page Not Found | {BUSINESS}",
                f"That page could not be found. Browse our spray foam insulation services in {CITY_PROV}, or call {PHONE_DISPLAY}.",
                "404.html")
notfound = notfound.replace('<meta name="robots" content="index, follow, max-image-preview:large">',
                            '<meta name="robots" content="noindex, follow">')
notfound += header("404.html")
notfound += f'''
<main id="main">

<section class="hero hero--page" aria-labelledby="hero-heading">
  <div class="container hero__inner">
    <div class="hero__intro">
      <span class="eyebrow" style="color:var(--color-accent-light);">Error 404</span>
      <h1 id="hero-heading">{esc(sc("Not Found Heading"))}</h1>
      <div class="btn-row">
        <a class="btn btn--primary btn--lg" href="index.html">Back To The Home Page</a>
        <a class="btn btn--ghost btn--lg" href="tel:{PHONE_HREF}">Call Now: {PHONE_DISPLAY}</a>
      </div>
    </div>
  </div>
</section>

{intro_band("    <p>%s</p>" % esc(sc("Not Found Text")), "Page not found")}

{services_grid(heading="Our Services", intro=f"Spray foam insulation installed across {CITY} and {REGION}.")}

{contact_form("404")}
</main>
'''
notfound += footer()
write("404.html", notfound)

# all_pages is the sitemap list, which excludes the noindexed legal pages,
# so count the files actually written instead.
print("PAGES: %d written, %d in sitemap" % (
    len([f for f in os.listdir(OUT) if f.endswith(".html")]), len(all_pages)))
