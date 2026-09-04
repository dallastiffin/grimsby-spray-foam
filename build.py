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
import os, re, json, html, sys, hashlib

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
PROVINCE      = "Ontario"
PROVINCE_CODE = "ON"
REGION        = "Niagara Region"
CITY_PROV     = "%s, %s" % (CITY, PROVINCE)

# Format matches the number already printed on the live site and in existing
# citations. Do not "normalise" this to +1 289-672-4160 - NAP consistency with
# the directory listings matters more than matching the Windsor build's style.
#
# The old SitePanda site had CTA buttons that displayed (289) 672-4160 but
# linked to tel:2262426614. 289-672-4160 is the correct number; that second
# number does not appear anywhere in this build.
PHONE_DISPLAY = "(289) 672-4160"
PHONE_HREF    = "+12896724160"
EMAIL         = "tiffindevelopments@gmail.com"

# --- industry layer -------------------------------------------------------
# Everything above is per-city. Everything here is per-INDUSTRY, and is the
# only part that changes when this template is reused for a different trade.
# See INDUSTRY.md in this folder for the researched facts behind the copy.
#
# SCHEMA_TYPE: the schema.org business type. HomeAndConstructionBusiness suits
# insulation, roofing, concrete and most trades. A non-construction local
# service would use LocalBusiness or a more specific subtype.
SCHEMA_TYPE   = "HomeAndConstructionBusiness"
OFFER_CATALOG = "Spray Foam Insulation Services"

# Industry wording used in schema, meta and page furniture. The old template
# had all of this hardcoded to epoxy flooring, which leaked "epoxy" onto a
# spray foam site in the business description, og:image:alt, the hidden detail
# heading, the services page title, the terms page and the 404.
INDUSTRY_NOUN   = "spray foam insulation"
# Carried over from Windsor this said "homes, garages and commercial
# buildings". This site has no commercial page, so that was a claim with
# nothing behind it. It also feeds the services page meta description, which
# came out at 119 characters - just under the 120 minimum.
INDUSTRY_BLURB  = ("Spray foam insulation for attics, garages, basements "
                   "and crawl spaces")
SERVICES_PAGE_H = "Spray Foam Insulation Services"

# Browser UI colour. Must match --color-primary in site/style.css and
# theme_color in site/site.webmanifest. It was hardcoded to the epoxy green
# in three separate places, so a rebrand silently left the old colour in the
# mobile browser chrome.
# Warm charcoal. Deliberately unlike Windsor's navy (#1b2e3e) and the epoxy
# sites' dark green - these are separate domains in the same trade and should
# not look like one network. Must stay in sync with --color-primary in
# site/style.css and theme_color in site/site.webmanifest.
THEME_COLOR = "#2E2A26"

# The service pages this industry runs: (slug, full title, short nav label).
# Order here drives the nav, the block order in the content markdown, and the
# "## " heading order in the SEO block. Use "and", not "&" - these strings
# flow into HTML attributes, JSON-LD and form <option> values.
# MIGRATION CONSTRAINT: these six slugs are already indexed by Google on the
# old SitePanda site and are being carried over byte-for-byte so that no page
# needs a 301. Do not "tidy" them.
#
#   close-and-open-cell-spray-foam    <- yes, "close", not "closed". That is
#                                        what is live and indexed. Leave it.
#   basement-insulation               <- kept separate from crawl space, even
#   crawl-space-insulation               though the Windsor build merges them,
#                                        because both rank independently.
#
# Nav order matches the old site's dropdown so returning visitors find the
# same thing in the same place.
SERVICE_PAGE_DEFS = [
    ("attic-insulation.html",             "Attic Insulation",     "Attic"),
    ("garage-insulation.html",            "Garage Insulation",    "Garage"),
    ("basement-insulation.html",          "Basement Insulation",  "Basement"),
    ("crawl-space-insulation.html",       "Crawl Space Insulation", "Crawl Space"),
    ("new-construction-insulation.html",  "New Construction Insulation",
     "New Construction"),
    ("close-and-open-cell-spray-foam.html",
     "Closed Cell and Open Cell Spray Foam", "Closed and Open Cell"),
]

# The contact form asks for a broad category, not a page name. A select
# listing every service page was unusable on a phone, and the exact system is
# worked out on the call anyway. The header dropdown still carries the full
# list, since those links are what carry the content.
FORM_SERVICE_OPTIONS = [
    "Attic",
    "Basement or Crawl Space",
    "Garage",
    "New Construction",
    "Whole Home",
    "Other",
]

# CITY_SLUG feeds the hero, about and services-page image basenames, so those
# are derived rather than hardcoded to whichever city built the template.
CITY_SLUG     = re.sub(r"[^a-z0-9]+", "-", CITY.lower()).strip("-")
HERO_IMG      = "hero-%s" % CITY_SLUG
ABOUT_IMG     = "about-%s" % CITY_SLUG
SERVICES_IMG  = "services-%s" % CITY_SLUG

# CANONICAL DOMAIN. Feeds canonical tags, Open Graph, sitemap.xml and schema.
# Must match the hostname the site actually serves, with no redirect in
# between, or Google indexes a URL that bounces.
# NOTE THE www. The old site is indexed on the www host and its canonical tags
# point there. Dropping it would point every canonical at a hostname Google has
# not seen. Cloudflare will 301 the apex to www.
DOMAIN = "https://www.grimsbysprayfoaminsulation.com"

# The markdown file holding all copy, in this folder.
CONTENT_FILE = "Grimsby-Spray-Foam-Insulation-Website-Content.md"

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
# West Niagara and the Hamilton fringe. Beamsville, Vineland, Jordan and
# Campden are all within the Town of Lincoln, not separate municipalities -
# worth knowing before the copy calls them "nearby towns".
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

# --- footer map ------------------------------------------------------------
# The src of a Google Maps "Embed a map" iframe, centred on the service area.
# Get a new one per city: maps.google.com -> Share -> Embed a map -> copy the
# src value out of the iframe it gives you. Set to "" to drop the map.
#
# Deliberately not the whole <iframe> tag. build.py owns the width, height,
# loading and title attributes so the map stays responsive and accessible
# rather than the 600x450 fixed box Google hands you.
MAP_EMBED_URL = ("https://www.google.com/maps/embed?pb=!1m14!1m12!1m3!1d11634.397796191022"
                 "!2d-79.56173837985783!3d43.19691477956117!2m3!1f0!2f0!3f0!3m2!1i1024!2i768"
                 "!4f13.1!5e0!3m2!1sen!2sca!4v1785984840343!5m2!1sen!2sca")

# ==========================================================================
#  END CONFIG
# ==========================================================================

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


# --- URL aliases (migration) ----------------------------------------------
# This site replaces an existing SitePanda/Duda site whose pages are already
# indexed. Two of them use slugs the template does not: /about-us and
# /contact-us. Rather than 301 them and bleed equity, the pages keep their
# live paths.
#
# build.py refers to these pages internally as about.html and contact.html in
# roughly 25 places. Instead of chasing every string literal, the alias is
# applied at the three choke points every URL passes through:
#
#   public_url()    - canonical, og:url, breadcrumbs, sitemap
#   rewrite_links() - every internal href in the rendered HTML
#   write()         - the filename on disk
#
# Add a mapping here and all three follow. Remove one and the page reverts to
# the template default.
SLUG_ALIAS = {
    "about.html":   "about-us.html",
    "contact.html": "contact-us.html",
}


def alias(slug):
    return SLUG_ALIAS.get(slug, slug)


def public_url(slug):
    """The path Cloudflare actually serves a page at.

    wrangler.toml uses html_handling = "auto-trailing-slash", so about-us.html
    is served at /about-us and index.html at /. Canonical tags, Open Graph
    URLs, breadcrumbs, the sitemap and every internal link all use this form,
    so no link ever hits a redirect.
    """
    slug = alias(slug)
    if slug in ("index.html", ""):
        return "/"
    return "/" + slug[:-5] if slug.endswith(".html") else "/" + slug


def esc(s):
    return html.escape(s, quote=False)

# ---------------------------------------------------------------------------
#  INLINE LINKS IN PROSE
#
#  The markdown parser escapes everything and supports no inline markup, which
#  is deliberate - it means nothing in the copy can inject HTML. Body prose
#  supports exactly one piece of markdown syntax: [text](url). Nothing else.
#  Escaping still happens first, so a stray bracket or ampersand in the copy
#  cannot inject markup.
#
#  External links get target="_blank" plus rel="noopener" - without noopener
#  the opened page gets a handle on this one through window.opener. If any of
#  these turn out to be PAID placements, Google's guidance is that they should
#  carry rel="sponsored" - add "sponsored" to EXTERNAL_REL below and every one
#  of them changes at once.
#
#  Links to the owner's OWN other city sites (bradfordsprayfoaminsulation.com,
#  sprayfoaminsulationwindsor.com, miltonsprayfoaminsulation.com,
#  chathamsprayfoaminsulation.com, leamingtonsprayfoaminsulation.com,
#  capebretonsprayfoaminsulation.com, saintjohnsprayfoaminsulation.com,
#  caledonsprayfoaminsulation.com) must NEVER appear in this markdown. Ten
#  sites linking to each other is the single most recognisable doorway-network
#  pattern there is.
# ---------------------------------------------------------------------------
EXTERNAL_REL = "noopener"

_MD_LINK = re.compile(r'\[([^\]]+)\]\(([^\s)]+?)(?:\s+"([^"]*)")?\)')


def rich(s):
    """Escape prose, then turn [text](url) into a real anchor.

    External (http/https) targets get target="_blank", rel=EXTERNAL_REL and
    the ext-link class. Internal targets (slug.html, index.html) render as a
    plain anchor with no target/rel - rewrite_links() turns the .html
    reference into the extensionless served path and applies SLUG_ALIAS, same
    as every other internal link on the site. This is what lets body copy
    carry the required internal cross-links between services, about and
    contact without a second markup syntax."""
    out = esc(s)
    def repl(m):
        label, url, title = m.group(1), m.group(2), m.group(3)
        if url.startswith("http://") or url.startswith("https://"):
            rel = EXTERNAL_REL if title != "nf" else EXTERNAL_REL + " nofollow"
            return ('<a class="ext-link" href="%s" target="_blank" rel="%s">%s</a>'
                    % (html.escape(url, quote=True), rel, label))
        return '<a href="%s">%s</a>' % (html.escape(url, quote=True), label)
    return _MD_LINK.sub(repl, out)


def plain(s):
    """Strip [text](url) down to text. For meta descriptions and card blurbs,
    where an anchor would be wrong or would leak raw markdown."""
    return esc(_MD_LINK.sub(lambda m: m.group(1), s))

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

# Block layout: home, N service pages, about, contact, FAQ, SEO table,
# SITE COPY. Every index is derived from N_SERVICES so the number of service
# pages can change without hunting for hardcoded offsets.
N_SERVICES = len(SERVICE_PAGE_DEFS)
EXPECTED_BLOCKS = N_SERVICES + 6
if len(blocks) < EXPECTED_BLOCKS:
    sys.exit(
        "\nContent file does not have the expected structure.\n"
        "  file:   %s\n"
        "  found:  %d section(s) separated by '---'\n"
        "  needed: %d  (home, %d service pages, about, contact, FAQ, SEO\n"
        "          table, SITE COPY)\n\n"
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
# Block 11 holds every reusable string that used to be hardcoded in this file:
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

# ---------------------------------------------------------------- site map
SERVICE_PAGES = SERVICE_PAGE_DEFS
SERVICE_IMG = {slug: "images/service-%s.jpg" % slug[:-5] for slug, _t, _s in SERVICE_PAGES}


# ---------------------------------------------------------------- partials
def head(title, meta, slug, extra_ld=""):
    url = DOMAIN + public_url(slug)
    ld_local = {
        "@context": "https://schema.org",
        "@type": SCHEMA_TYPE,
        "@id": DOMAIN + "/#business",
        "name": BUSINESS,
        "description": "%s in %s and %s." % (INDUSTRY_BLURB, CITY_PROV, REGION),
        "url": DOMAIN + "/",
        "telephone": PHONE_DISPLAY,
        "email": EMAIL,
        "image": DOMAIN + "/images/og-image.jpg",
        "logo": DOMAIN + "/images/logo.jpg",
        "priceRange": "$$",
        "address": {
            "@type": "PostalAddress",
            "streetAddress": STREET_ADDRESS,
            "addressLocality": CITY,
            "addressRegion": PROVINCE_CODE,
            "postalCode": POSTAL_CODE,
            "addressCountry": COUNTRY
        },
        "geo": {"@type": "GeoCoordinates", "latitude": LATITUDE, "longitude": LONGITUDE},
        "openingHoursSpecification": [{
            "@type": "OpeningHoursSpecification",
            "dayOfWeek": OPENING_DAYS,
            "opens": OPENING_TIME, "closes": CLOSING_TIME
        }],
        "areaServed": [{"@type": "City", "name": n} for n in
            SERVICE_AREA],
        "hasOfferCatalog": {
            "@type": "OfferCatalog", "name": OFFER_CATALOG,
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
<meta property="og:site_name" content="{BUSINESS}">
<meta property="og:locale" content="en_CA">
<meta property="og:title" content="{esc(title)}">
<meta property="og:description" content="{esc(meta)}">
<meta property="og:url" content="{url}">
<meta property="og:image" content="{DOMAIN}/images/og-image.jpg">
<meta property="og:image:width" content="1200">
<meta property="og:image:height" content="630">
<meta property="og:image:type" content="image/jpeg">
<meta property="og:image:alt" content="{BUSINESS} - {INDUSTRY_NOUN} in {CITY_PROV}">
<meta name="twitter:card" content="summary_large_image">
<meta name="twitter:title" content="{esc(title)}">
<meta name="twitter:description" content="{esc(meta)}">
<meta name="twitter:image" content="{DOMAIN}/images/og-image.jpg">

<!-- Fingerprinted. _headers caches /images/* for a year as immutable, and
     unlike the photographs these filenames never change - so without a
     ?v=<hash> a rebranded favicon can never reach anyone who already
     visited. Browsers ignore reloads for immutable assets; only a new URL
     works. -->
<link rel="icon" href="{asset_v('images/favicon.ico')}" sizes="any">
<link rel="icon" type="image/png" sizes="32x32" href="{asset_v('images/icon-32.png')}">
<link rel="icon" type="image/png" sizes="16x16" href="{asset_v('images/icon-16.png')}">
<link rel="apple-touch-icon" sizes="180x180" href="{asset_v('images/icon-180.png')}">
<link rel="manifest" href="site.webmanifest">
<link rel="stylesheet" href="{asset_v("style.css")}">
<script src="{asset_v("script.js")}" defer></script>

<!-- ===== Schema.org: Local Business ===== -->
<script type="application/ld+json">
{json.dumps(ld_local, indent=2)}
</script>{extra_ld}
</head>
<body>
<a class="skip-link" href="#main">Skip to main content</a>
"""

def header(active):
    def cls(page):
        return ' aria-current="page"' if page == active else ''
    # Every service page appears in the dropdown. These links are a large part
    # of how the service pages get discovered and crawled, so the menu carries
    # the full list rather than a trimmed selection.
    sub = "\n".join(
        f'            <li><a href="{slug}"{cls(slug)}>{esc(title)}</a></li>'
        for slug, title, _short in SERVICE_PAGES)
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
    f'            <option value="{esc(o)}">{esc(o)}</option>'
    for o in FORM_SERVICE_OPTIONS)

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
                   data-label="Phone" placeholder="226-000-0000" required>
            <span class="field__error" aria-live="polite"></span>
          </div>

          <div class="field">
            <label for="{pfx}-email">Email <span class="req" aria-hidden="true">*</span></label>
            <input type="email" id="{pfx}-email" name="email" autocomplete="email"
                   data-label="Email" placeholder="you@example.com" required>
            <span class="field__error" aria-live="polite"></span>
          </div>

          <div class="field field--full">
            <label for="{pfx}-service">Service Interested In <span class="req" aria-hidden="true">*</span></label>
            <select id="{pfx}-service" name="service" data-label="Service interested in" required>
            <option value="">Please choose a service</option>
{SERVICE_OPTIONS}
            </select>
            <span class="field__error" aria-live="polite"></span>
          </div>

          <div class="field field--full">
            <label for="{pfx}-message">Message</label>
            <textarea id="{pfx}-message" name="message" data-label="Message"
                      {'rows="3"' if compact else ''}
                      placeholder="Rough size of the space, what it is used for, and whether water has ever come in."></textarea>
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


def quote_band(page_label):
    """Compact estimate form in a full-width band directly beneath the hero.

    This used to sit inside the hero as a card in the right-hand column. The
    hero is now a single centred column, so the form became its own band
    immediately below it - still above the fold on most desktop screens and
    the first thing after the headline on a phone.

    Keeps id="hero-quote" because the hero's "Get a Free Quote" button and any
    existing links point at it. The second, longer form further down the page
    keeps id="quote"; the two must not collide.
    """
    return f"""
<!-- ===================== QUOTE BAND (directly under hero) ===================== -->
<section class="quote-band" id="hero-quote" aria-labelledby="hero-form-heading">
  <div class="container quote-band__inner">

    <div class="quote-band__intro">
      <h2 class="quote-band__title" id="hero-form-heading">{esc(sc("Hero Form Heading"))}</h2>
      <p>{esc(sc("Hero Form Intro"))}</p>
      <p class="quote-band__phone">Or call <a href="tel:{PHONE_HREF}">{PHONE_DISPLAY}</a>.</p>
    </div>

    <div class="quote-band__form">
{success_message('hf')}

      <form class="lead-form" action="#" method="post" novalidate
            data-source="{esc(page_label)} hero band">
        <div class="form-grid">
{form_fields('hf', compact=True)}
          <div class="field field--full">
            <button class="btn btn--primary btn--block" type="submit">{esc(sc("Hero Form Button"))}</button>
            <p class="form-note">{esc(sc("Hero Form Note"))}</p>
          </div>
        </div>
      </form>
    </div>

  </div>
</section>"""


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
        Prefer to talk it through? Call <a href="tel:{PHONE_HREF}">{PHONE_DISPLAY}</a>.</p>
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
            <p class="form-note">Fields marked <span class="req" aria-hidden="true">*</span> are required.
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
          <h3>Our Services</h3>
          <ul class="footer-list" style="padding:0;">
            {"".join(f'<li><a href="{s}" style="color:var(--color-primary-light);">{esc(t)}</a></li>' for s, t, _ in SERVICE_PAGES)}
          </ul>
        </div>
      </aside>
"""

def footer():
    svc = "".join(f'<li><a href="{s}">{esc(t)}</a></li>' for s, t, _ in SERVICE_PAGES)

    # Service-area map. loading="lazy" matters here - this sits on all 14
    # pages, and an eagerly loaded Google Maps frame is a few hundred KB of
    # third-party script on every single one. title= gives the frame an
    # accessible name; without it a screen reader announces "iframe".
    map_block = ""
    if MAP_EMBED_URL:
        map_block = f"""
    <div class="footer-map">
      <h3>Where We Work</h3>
      <div class="footer-map__frame">
        <iframe src="{MAP_EMBED_URL}"
                title="Map of the {BUSINESS} service area around {CITY_PROV}"
                loading="lazy" allowfullscreen
                referrerpolicy="strict-origin-when-cross-origin"></iframe>
      </div>
    </div>"""

    return f"""
<!-- ============================= FOOTER ============================= -->
<footer class="site-footer">
  <div class="container">
    <div class="footer-grid">

      <div class="footer-brand">
        <a class="footer-logo" href="index.html" aria-label="{BUSINESS} home page">
          <img src="images/wordmark-light-300.png"
               alt="{BUSINESS}" width="300" height="310" loading="lazy">
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

      <nav aria-labelledby="footer-guides-heading">
        <h3 id="footer-guides-heading">Guides</h3>
        <ul class="footer-list">
          <li><a href="spray-foam-performance-across-climate-zones.html">Regional Guide</a></li>
          <li><a href="heating-season-pricing-timelines.html">Seasonal Pricing Guide</a></li>
          <li><a href="property-overhaul-planning.html">Property Project Planning</a></li>
          <li><a href="protecting-fresh-insulation-during-exterior-work.html">Protecting Your Insulation</a></li>
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
          <li>Email: <a href="mailto:{EMAIL}">{EMAIL}</a></li>
          <li>Hours: {HOURS_TEXT}</li>
          <li><!-- PLACEHOLDER: add street address once confirmed --></li>
        </ul>
        <div class="btn-row">
          <a class="btn btn--primary btn--sm" href="#quote">Get a Free Quote</a>
        </div>
      </div>

    </div>
{map_block}

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
        body = "\n".join(f"          <p>{rich(a)}</p>" for a in answers)
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
          <p>{plain(blurb)}</p>
          <a class="service-card__link" href="{slug}">View {esc(title)}</a>
        </div>
      </article>""")
    return f"""
<!-- ============================= SERVICES GRID ============================= -->
<section class="section" id="services" aria-labelledby="services-heading">
  <div class="container">
    <div class="section-head is-centered">
      <span class="eyebrow">What We Install</span>
      <h2 id="services-heading">{esc(heading)}</h2>
      <p class="lead">{esc(intro)}</p>
    </div>
    <div class="grid grid--3">
{chr(10).join(cards)}
    </div>
    <div class="btn-row is-centered">
      <a class="btn btn--primary btn--lg" href="#quote">Get a Free Quote</a>
      <a class="btn btn--outline btn--lg" href="services.html">See All Services</a>
    </div>
  </div>
</section>
"""


# ---------------------------------------------------------------- images
# Real project photography, exported as WebP with a JPG fallback at two
# widths each. width/height are always set so the browser reserves space
# and the layout does not shift while images load (CLS).
# Derived from PAGE_PHOTOS further down rather than hand-maintained. The old
# template kept this table in sync by hand, and a missing entry threw KeyError
# from deep inside rendering with no indication of the cause. Real alt text
# still comes from the SITE COPY block; "alt" here is only the fallback.
#
# PAGE_PHOTOS lives with the image pipeline below, so this is populated by
# _init_photos(), called immediately after that table is defined.
PHOTOS = {}

def _init_photos():
    for _src, base, aspect, widths, alt in PAGE_PHOTOS:
        if base == "og-image":
            continue
        w = widths[0]
        PHOTOS[base] = {
            "widths": widths,
            "w": w,
            "h": int(round(w * aspect[1] / float(aspect[0]))),
            "alt": alt,
        }

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
# ---------------------------------------------------------------------------
#  PHOTO SLOT ASSIGNMENT - READ BEFORE CHANGING
#
#  Every photo below is byte-identical to one already deployed on
#  sprayfoaminsulationwindsor.com. That is unavoidable for now: the whole
#  shared pool is on Windsor. What is avoidable is two sites in the same trade
#  showing the same picture in the same position, which is the part that
#  actually looks like a network.
#
#  So every photo here sits in a DIFFERENT slot than it does on Windsor:
#
#    Finished Attic Spray Foam  Windsor: unused          -> Grimsby hero + og
#    Spray Foam on Roof         Windsor: commercial      -> attic
#    Garage Wall with Foam      Windsor: about           -> garage
#    Basement walls getting..   Windsor: services image  -> basement
#    Crawlspace Spray Foam      Windsor: gallery         -> crawl space
#    Two Storey Great Room      Windsor: HERO            -> new construction
#    Spray Foam Close UP        Windsor: unused          -> open/closed cell
#    Crawl Space Installation   Windsor: closed-cell     -> about
#    Basement fully insulated   Windsor: basement svc    -> services image
#
#  Neither hero is reused as a hero. If new photography ever arrives, the two
#  hero slots are the first things to replace.
#
#  DO NOT USE Caledon Storefront.png. It is a photograph of a different
#  company's premises - the sign reads "Caledon Spray Foam Insulation" - and
#  there is a dental practice's signage beside it. It is in the folder because
#  it came with the shared pool.
# ---------------------------------------------------------------------------
PAGE_PHOTOS = [
  ("Finished Attic Spray Foam.png", HERO_IMG, (4,3), [800,1200],
   f"Attic in a {CITY} home finished ridge to eaves in spray foam"),
  ("Finished Attic Spray Foam.png", "og-image", (1200,630), [1200],
   f"{BUSINESS} attic, basement and crawl space insulation"),
  ("Spray Foam on Roof.png", "service-attic-insulation", (16,10), [640,960],
   "Foam going onto the underside of a roof deck between the rafters"),
  ("Garage Wall with Spray Foam Insulation.png", "service-garage-insulation",
   (16,10), [640,960],
   "Attached garage insulated across the wall and up to the ceiling"),
  ("Basement walls getting insulated with spray foam.png",
   "service-basement-insulation", (16,10), [640,960],
   "Installer spraying closed-cell foam along a basement foundation wall"),
  ("Crawlspace Spray Foam.png", "service-crawl-space-insulation", (16,10), [640,960],
   "Crawl space wall being sealed over a taped ground sheet"),
  ("Two Storey Great Room.png", "service-new-construction-insulation",
   (16,10), [640,960],
   "Open stud bays in a new two storey build being filled before drywall"),
  ("Spray Foam Close UP.png", "service-close-and-open-cell-spray-foam",
   (16,10), [640,960],
   "Close up of foam expanding out of the gun into a stud bay"),
  ("Crawl Space Installation.png", ABOUT_IMG, (4,3), [800,1200],
   f"A {BUSINESS} installer working a crawl space in full protective kit"),
  ("Basement fully insulated with spray foam.png", SERVICES_IMG, (4,3), [800,1200],
   "Finished basement with every foundation wall sealed corner to corner"),
]


# Gallery exports at 400 and 1000 wide, so every source here must be at least
# 1000px across or the lightbox upscales it. That rules out Attic Rafters
# Spray, Cutting Foam, Wall Stud Spray Installation, Wall Studs 2 and Subfloor
# Spray, which are all under 600px in the shared pool.
#
# None of these slugs matches a Windsor gallery slot. Windsor's gallery holds
# Basement walls with spray foam, Crawlspace Spray Foam, Attic Insulation,
# garage roof, Shed, Spray Foam Close UP, Subfloor Spray, Man spraying, Wall
# Studs 2 and Garage Wall - deliberately none of those are repeated here.
GALLERY_PHOTOS = [
 ("Finished Attic Spray Foam.png", "attic-finished-ridge-to-eaves",
  "Attic finished from the ridge down to the eaves"),
 ("Basement fully insulated with spray foam.png", "basement-foundation-walls-sealed",
  "Basement with every foundation wall sealed corner to corner"),
 ("Crawlspace Spray Foam 2.png", "crawl-space-sheeted-and-sealed",
  "Crawl space sealed over a taped ground sheet"),
 ("Crawl Space Installation.png", "crawl-space-installer-at-work",
  "Working a crawl space wall in full protective kit"),
 ("Old Wall Re-insulation.png", "century-home-wall-stripped-back",
  "Century home wall stripped back to bare framing before new foam"),
 ("Basement walls getting insulated with spray foam.png", "basement-wall-in-progress",
  "Closed-cell foam going onto a foundation wall"),
 ("Spray Foam on Roof.png", "roof-deck-between-rafters",
  "Roof deck sprayed between the rafters"),
 ("Two Storey Great Room.png", "new-build-stud-bays",
  "Stud bays in a new two-story build filled before drywall"),
]



# og-image is the social share graphic, never rendered as an <img>, so it
# needs no alt text.
_init_photos()

warn_missing_alt([x[1] for x in PAGE_PHOTOS if x[1] != "og-image"]
                 + [x[1] for x in GALLERY_PHOTOS])


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
    items = [GALLERY_ITEM.format(s=g["slug"], c=esc(g["caption"])) for g in GALLERY]
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
        name = alias(name + ".html")[:-5]      # about -> about-us
        target = "/" if name == "index" else "/" + name
        return 'href="%s%s"' % (target, tail)
    return LINK_RE.sub(sub, content)


def write(slug, content):
    content = rewrite_links(content)
    slug = alias(slug)                          # about.html -> about-us.html
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

# Every special home section is matched by PREFIX, never by exact text.
# The old template matched two of these against literal epoxy wording
# ("What Are The Benefits Of Epoxy Flooring?"), which meant the file could
# not be reused for another trade without editing this line. Prefix matching
# lets each industry phrase its own headings:
#   "What Are The Benefits Of Spray Foam Insulation?"
#   "What Happens During A Spray Foam Install?"
def section_starting(prefix, required=True):
    for sec in secs:
        if sec["title"].lower().startswith(prefix.lower()):
            return sec
    if required:
        raise SystemExit(
            "Home page markdown needs a '## ' section starting: " + prefix)
    return None

faq_sec    = section_starting("Frequently Asked Questions")
benefits   = section_starting("What Are The Benefits")
process    = section_starting("What Happens During")
why        = section_starting("Why Choose")
areas      = section_starting("Serving")

special = {hero_sec["title"], faq_sec["title"], benefits["title"],
           process["title"], why["title"], areas["title"]}
body_sections = [s for s in secs if s["title"] not in special]

hero_paras = "\n".join(f"      <p>{rich(t)}</p>" for k, t in hero_sec["nodes"] if k == "p")

# Benefit cards - one card per source paragraph (no text removed)
benefit_cards = "\n".join(f"""      <article class="feature">
        <div class="feature__icon" aria-hidden="true">&#10003;</div>
        <p>{rich(t)}</p>
      </article>""" for k, t in benefits["nodes"] if k == "p")

# Process steps - one step per source paragraph
step_cards = "\n".join(f"""      <li class="step">
        <p>{rich(t)}</p>
      </li>""" for k, t in process["nodes"] if k == "p")

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
    '<link rel="preload" as="image" href="images/%s-1200.jpg"\n' % HERO_IMG +
    '      imagesrcset="images/%s-800.webp 800w, images/%s-1200.webp 1200w"\n' % (HERO_IMG, HERO_IMG) +
    '      imagesizes="100vw" type="image/webp">\n'
    '<link rel="stylesheet" href="%s">' % asset_v("style.css"))
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

  <!-- Single centred column. The estimate form used to sit in the right half
       of this hero; it now lives in the #quote section further down the page,
       which is what the hero buttons point at. One column means the scrim can
       be even rather than weighted to the left, and the headline is not
       competing with a form card for attention above the fold. -->
  <div class="container hero__inner">

    <!-- Business name and service area above the h1. Both are paragraphs, not
         headings, so the page keeps exactly one top-level heading. -->
    <p class="hero__brand">{BUSINESS}</p>
    <p class="hero__eyebrow">{CITY_PROV} &middot; and across {REGION}</p>

    <div class="hero__intro">
      <h1 id="hero-heading">{esc(h1)}</h1>
{hero_paras}
      <ul class="hero__badges">
{chr(10).join('        <li>%s</li>' % esc(b) for b in sc_lines("Hero Badges"))}
      </ul>
      <div class="btn-row">
        <a class="btn btn--primary btn--lg" href="tel:{PHONE_HREF}">Call Now: {PHONE_DISPLAY}</a>
        <a class="btn btn--ghost btn--lg" href="#hero-quote">Get a Free Quote</a>
      </div>
    </div>

  </div>
</section>
{quote_band("Home Page")}

<!-- ============================= TRUST STRIP ============================= -->
<!-- Secondary service navigation. Built from SERVICE_PAGES so the labels and
     targets can never drift apart. -->
<nav class="trust-strip" aria-label="Our services">
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
    <h2 id="detail-heading" class="visually-hidden">{INDUSTRY_NOUN.capitalize()} information for {CITY} property owners</h2>
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

<!-- ============================= SERVICE AREA ============================= -->
<section class="section section--alt" aria-labelledby="areas-heading">
  <div class="container container--narrow prose">
    <span class="eyebrow">Service Area</span>
    <h2 id="areas-heading">{esc(areas['title'])}</h2>
{nodes_html(areas['nodes'], "    ")}
    <div class="btn-row">
      <a class="btn btn--primary" href="#quote">Get a Free Quote</a>
      <a class="btn btn--outline" href="contact.html">Contact Us Today</a>
    </div>
  </div>
</section>

{cta_band(sc("Closing CTA Heading"), sc("Closing CTA Text"))}

{faq_html}
{contact_form("Home Page")}
</main>
"""
home += footer()
write("index.html", home)

# ============================================================================
#  SERVICE PAGES
# ============================================================================
# Must match the "## " headings in the SEO block of the markdown, in order.
SEO_LABELS = [title for _slug, title, _short in SERVICE_PAGES]

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
        "provider": {"@type": SCHEMA_TYPE, "@id": DOMAIN + "/#business",
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
      <span class="eyebrow" style="color:#ffb37a;">{esc(title)}</span>
      <h1 id="hero-heading">{esc(sh1)}</h1>
{over_paras}
      <div class="btn-row">
        <a class="btn btn--primary btn--lg" href="#quote">Get a Free Quote</a>
        <a class="btn btn--ghost btn--lg" href="tel:{PHONE_HREF}">Call Now: {PHONE_DISPLAY}</a>
      </div>
    </div>
  </div>
</section>

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
svc_page = head(f"{SERVICES_PAGE_H} | {CITY_PROV}",
                f"{INDUSTRY_BLURB} in {CITY_PROV}. Call us at {PHONE_DISPLAY} today.",
                "services.html", crumb_ld)
svc_page += header("services.html")
svc_page += crumbs
svc_page += f"""
<main id="main">

<section class="hero hero--page hero--split" aria-labelledby="hero-heading">
  <div class="container hero__inner">
    <div class="hero__intro">
      <span class="eyebrow" style="color:#ffb37a;">Services</span>
      <h1 id="hero-heading">{esc(sc("Services Page Heading"))}</h1>
      <p>{esc(sc("Services Page Intro"))}</p>
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
      <span class="eyebrow" style="color:#ffb37a;">About Us</span>
      <h1 id="hero-heading">{esc(ah1)}</h1>
      <h2 style="color:#fff;font-size:var(--fs-lg);">{esc(about_lead['title'])}</h2>
{nodes_html([n for n in about_lead['nodes']], "      ")}
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

{services_grid(heading="Services We Install", intro=f"Attics, garages and below-grade {INDUSTRY_NOUN} across Grimsby, sprayed by the people who quoted it.")}

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
    for part in re.split(r'\s(?=(?:Company|Phone|Email|Location|Services):)', t):
        if ":" in part:
            lab, val = part.split(":", 1)
            info_pairs.append((lab.strip(), val.strip()))


def _info_value(label, value):
    """Phone and email become links; everything else is plain text."""
    if label.lower() == "phone":
        return f'<a href="tel:{PHONE_HREF}">{esc(value)}</a>'
    if label.lower() == "email":
        return f'<a href="mailto:{esc(value)}">{esc(value)}</a>'
    return esc(value)


info_html = "\n".join(
    f'        <div><dt style="font-weight:800;color:var(--color-heading);">{esc(l)}</dt>'
    f'<dd style="margin:0 0 var(--space-3);">'
    + _info_value(l, v)
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
      <span class="eyebrow" style="color:#ffb37a;">Contact</span>
      <h1 id="hero-heading">{esc(ch1)}</h1>
      <h2 style="color:#fff;font-size:var(--fs-lg);">{esc(lead_sec['title'])}</h2>
{nodes_html(lead_sec['nodes'], "      ")}
      <div class="btn-row">
        <a class="btn btn--primary btn--lg" href="tel:{PHONE_HREF}">Call Now: {PHONE_DISPLAY}</a>
        <a class="btn btn--ghost btn--lg" href="#quote">Request an Estimate</a>
      </div>
    </div>
  </div>
</section>

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
          <h3>Our Services</h3>
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
      <span class="eyebrow" style="color:#ffb37a;">Answers</span>
      <h1 id="hero-heading">{esc(sc("FAQ Page Heading"))}</h1>
      <p>{esc(sc("FAQ Page Intro"))}</p>
      <div class="btn-row">
        <a class="btn btn--primary btn--lg" href="#quote">Get a Free Quote</a>
        <a class="btn btn--ghost btn--lg" href="tel:{PHONE_HREF}">Call Now: {PHONE_DISPLAY}</a>
      </div>
    </div>
  </div>
</section>

{cta_band(sc("FAQ Page CTA Heading"), sc("FAQ Page CTA Text"), 1)}

{faq_body}

{services_grid(heading="Services We Install", intro="Pick a service to see how we approach it, what it costs to do properly, and where it belongs.")}

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
{chr(10).join(f'        <p>{rich(p)}</p>' for p in ps)}
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
      <span class="eyebrow" style="color:#ffb37a;">{esc(eyebrow)}</span>
      <h1 id="hero-heading">{esc(h1)}</h1>
      <p>PLACEHOLDER DOCUMENT. This page is a working template for {BUSINESS} and should be
         reviewed by a legal professional before the site goes live.</p>
    </div>
  </div>
</section>

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
            "The content on this website is provided for general information about %s services in %s." % (INDUSTRY_NOUN, CITY_PROV)]),
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
#  RESOURCE GUIDES  (added for the industry backlink program, Sep 2026)
#  Four extra blocks appended to the end of the content file, after SITE
#  COPY, so the original block indices above are untouched.
# ============================================================================
GUIDE_PAGES = [
    ("spray-foam-performance-across-climate-zones.html", COPY_BLOCK_INDEX + 1, "Regional Guide"),
    ("heating-season-pricing-timelines.html", COPY_BLOCK_INDEX + 2, "Seasonal Pricing Guide"),
    ("property-overhaul-planning.html", COPY_BLOCK_INDEX + 3, "Property Project Planning"),
    ("protecting-fresh-insulation-during-exterior-work.html", COPY_BLOCK_INDEX + 4, "Protecting Your Insulation"),
]

def guide_page(slug, block_index, nav_label):
    h1, secs = parsed[block_index]
    crumbs, crumb_ld = breadcrumbs([("Home", "index.html"), (h1, None)])
    blocks = "".join(content_block(s) for s in secs)
    page = head(h1, f"{h1} - {BUSINESS}, {CITY_PROV}.", slug, crumb_ld)
    page += header(slug)
    page += crumbs
    page += f"""
<main id="main">
<section class="hero hero--page" aria-labelledby="hero-heading">
  <div class="container hero__inner">
    <div class="hero__intro">
      <span class="eyebrow" style="color:#ffb37a;">{esc(nav_label)}</span>
      <h1 id="hero-heading">{esc(h1)}</h1>
    </div>
  </div>
</section>
<section class="section" aria-labelledby="guide-heading">
  <div class="container">
    <h2 id="guide-heading" class="visually-hidden">{esc(h1)}</h2>
    <div class="layout-split">
      <div class="prose">
{blocks}      </div>
{SIDEBAR}
    </div>
  </div>
</section>
{contact_form(h1)}
</main>
"""
    page += footer()
    write(slug, page)

for slug, idx, label in GUIDE_PAGES:
    guide_page(slug, idx, label)

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
            ["about.html", "faq.html", "contact.html"] + [s for s, _, _ in GUIDE_PAGES]
urls = "\n".join(
    f"""  <url>
    <loc>{DOMAIN}{public_url(p)}</loc>
    <changefreq>monthly</changefreq>
    <priority>{'1.0' if p == 'index.html' else ('0.9' if p in [s for s,_,_ in SERVICE_PAGES] else '0.7')}</priority>
  </url>""" for p in all_pages)
open(os.path.join(OUT, "sitemap.xml"), "w", encoding="utf-8").write(
f"""<?xml version="1.0" encoding="UTF-8"?>
<urlset xmlns="http://www.sitemap.org/schemas/sitemap/0.9">
{urls}
</urlset>
""".replace("www.sitemap.org", "www.sitemaps.org"))

open(os.path.join(OUT, "robots.txt"), "w", encoding="utf-8").write(
f"""User-agent: *
Allow: /

Sitemap: {DOMAIN}/sitemap.xml
""")

# ---------------------------------------------------------------------------
#  WEB APP MANIFEST
#
#  Every page carries <link rel="manifest" href="site.webmanifest">, but this
#  file used to be hand-maintained in site/ rather than generated. When this
#  project was copied from the Windsor build only style.css and script.js came
#  across from site/, so the manifest did not - and every page 404'd on it,
#  live, until a network trace caught it.
#
#  Generating it here means it cannot be lost in a copy again, and theme_color
#  cannot drift away from THEME_COLOR and --color-primary.
# ---------------------------------------------------------------------------
_manifest_short = "%s Spray Foam" % CITY
open(os.path.join(OUT, "site.webmanifest"), "w", encoding="utf-8").write(
f"""{{
  "name": "{BUSINESS}",
  "short_name": "{_manifest_short}",
  "description": "{INDUSTRY_BLURB} in {CITY_PROV}.",
  "start_url": "/",
  "display": "browser",
  "background_color": "#ffffff",
  "theme_color": "{THEME_COLOR}",
  "icons": [
    {{ "src": "images/icon-192.png", "sizes": "192x192", "type": "image/png" }},
    {{ "src": "images/icon-512.png", "sizes": "512x512", "type": "image/png" }},
    {{ "src": "images/icon-512.png", "sizes": "512x512", "type": "image/png", "purpose": "maskable" }}
  ]
}}
""")


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
                f"That page could not be found. Browse our {INDUSTRY_NOUN} services in {CITY_PROV} or call us at {PHONE_DISPLAY}.",
                "404.html")
notfound = notfound.replace('<meta name="robots" content="index, follow, max-image-preview:large">',
                            '<meta name="robots" content="noindex, follow">')
notfound += header("404.html")
notfound += f'''
<main id="main">

<section class="hero hero--page" aria-labelledby="hero-heading">
  <div class="container hero__inner">
    <div class="hero__intro">
      <span class="eyebrow" style="color:#ffb37a;">Error 404</span>
      <h1 id="hero-heading">{esc(sc("Not Found Heading"))}</h1>
      <p>{esc(sc("Not Found Text"))}</p>
      <div class="btn-row">
        <a class="btn btn--primary btn--lg" href="index.html">Back To The Home Page</a>
        <a class="btn btn--ghost btn--lg" href="tel:{PHONE_HREF}">Call Now: {PHONE_DISPLAY}</a>
      </div>
    </div>
  </div>
</section>

{services_grid(heading="Our Services", intro=f"{SERVICES_PAGE_H} across {CITY} and {REGION}.")}

{contact_form("404")}
</main>
'''
notfound += footer()
write("404.html", notfound)

# all_pages is the sitemap list, which excludes the noindexed legal pages,
# so count the files actually written instead.
print("PAGES: %d written, %d in sitemap" % (
    len([f for f in os.listdir(OUT) if f.endswith(".html")]), len(all_pages)))
