#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Post-build audit for one city site. Reports NUMBERS, not reassurances.

    python3 audit.py <site-dir> [--head "tree trimming"] [--compare other/site ...]

Covers everything Phase 6 of the runbook asks for: link and image integrity,
heading structure, duplicate ids, alt text, meta uniqueness and length,
head-term density per page, place-name density, outbound links, the owner's
internal-linking requirements, page weight, certification claims, and verbatim
overlap against sibling cities measured on paragraph text.
"""
import os, re, sys, json, html, glob, collections

# ---------------------------------------------------------------- tiny HTML
TAG = re.compile(r"<[^>]+>")
SCRIPTSTYLE = re.compile(r"<(script|style)\b.*?</\1>", re.S | re.I)


def text_of(frag):
    frag = SCRIPTSTYLE.sub(" ", frag)
    frag = re.sub(r"<!--.*?-->", " ", frag, flags=re.S)
    t = TAG.sub(" ", frag)
    return re.sub(r"\s+", " ", html.unescape(t)).strip()


def main_of(doc):
    m = re.search(r'<main\b[^>]*>(.*?)</main>', doc, re.S | re.I)
    return m.group(1) if m else ""


def paras_of(doc):
    """<p> text inside <main> only. Whole-page overlap is dominated by nav,
    footer and the service-card grid, which are interface and must not vary."""
    return [text_of(m.group(1))
            for m in re.finditer(r'<p\b[^>]*>(.*?)</p>', main_of(doc), re.S | re.I)]


def words(s):
    return re.findall(r"[A-Za-z']+", s.lower())


def phrase_count(text, phrase):
    p = r"\b" + r"[\s\-]+".join(re.escape(w) for w in phrase.split()) + r"\b"
    return len(re.findall(p, text, re.I))


# ---------------------------------------------------------------- the audit
def audit(site, head_terms, other_terms, place_names, compare_dirs, label, aliases=None):
    # aliases: {"about.html": "about-us.html", ...} for cities that keep
    # legacy indexed slugs (Brantford). Defaults to the template names.
    aliases = aliases or {}
    ABOUT = aliases.get("about.html", "about.html")
    CONTACT = aliases.get("contact.html", "contact.html")
    pages = sorted(glob.glob(os.path.join(site, "*.html")))
    docs = {os.path.basename(p): open(p, encoding="utf-8").read() for p in pages}
    fails, warns = [], []

    def fail(m): fails.append(m)
    def warn(m): warns.append(m)

    print("=" * 78)
    print("AUDIT: %s   (%d pages)" % (label, len(docs)))
    print("=" * 78)

    # ---------------- 1. links and images resolve --------------------------
    print("\n1. LINK AND IMAGE INTEGRITY")
    have = set(docs) | {os.path.basename(f) for f in
                        glob.glob(os.path.join(site, "**", "*"), recursive=True)}
    rel = {os.path.relpath(f, site).replace("\\", "/")
           for f in glob.glob(os.path.join(site, "**", "*"), recursive=True)}
    slugs = {n[:-5] for n in docs}
    n_int = n_img = 0
    for name, doc in docs.items():
        for href in re.findall(r'href="([^"]+)"', doc):
            if href.startswith(("http", "mailto:", "tel:", "#", "data:")):
                continue
            n_int += 1
            if href.endswith(".html"):
                fail("%s: internal link still carries .html -> %s" % (name, href))
                continue
            t = href.split("#")[0].split("?")[0].lstrip("/")
            if t in ("", "/"):
                continue
            if t not in slugs and t not in rel:
                fail("%s: dead internal link -> %s" % (name, href))
        # Only <img>/<source> assets. Matching every src= also caught
        # <script src="script.js?v=hash">, which reported the cache
        # fingerprint as a missing image on all 15 pages.
        for tag in re.findall(r'<(?:img|source)\b[^>]*>', doc, re.I):
            for attr in re.findall(r'(?:src|srcset)="([^"]+)"', tag):
                for cand in attr.split(","):
                    u = cand.strip().split(" ")[0].split("?")[0]
                    if not u or u.startswith(("http", "data:")):
                        continue
                    n_img += 1
                    if u.lstrip("/") not in rel:
                        fail("%s: missing image file -> %s" % (name, u))
    print("   %d internal links checked, %d image references checked" % (n_int, n_img))
    print("   internal links carrying .html: %d" %
          sum(1 for f in fails if "carries .html" in f))

    # ---------------- 2. structure ----------------------------------------
    print("\n2. HEADING STRUCTURE, ALT TEXT, DUPLICATE IDS")
    for name, doc in docs.items():
        h1 = re.findall(r"<h1\b", doc, re.I)
        if len(h1) != 1:
            fail("%s: %d <h1> elements (want exactly 1)" % (name, len(h1)))
        for img in re.findall(r"<img\b[^>]*>", doc, re.I):
            if 'alt=' not in img:
                fail("%s: <img> with no alt attribute" % name)
        ids = re.findall(r'\sid="([^"]+)"', doc)
        dup = [i for i, c in collections.Counter(ids).items() if c > 1]
        if dup:
            fail("%s: duplicate element id(s): %s" % (name, ", ".join(dup)))
    print("   exactly one h1 per page: %s" %
          ("YES" if not any("<h1>" in f for f in fails) else "NO"))
    print("   images without alt: %d" % sum(1 for f in fails if "no alt" in f))
    print("   pages with duplicate ids: %d" % sum(1 for f in fails if "duplicate element" in f))
    empties = sum(doc.count('alt=""') for doc in docs.values())
    print("   empty alt=\"\" instances: %d  (hero background + lightbox placeholder"
          " are correct; they are decorative)" % empties)

    # ---------------- 3. alt-text uniqueness ------------------------------
    print("\n3. ALT TEXT")
    alts = collections.Counter()
    for doc in docs.values():
        for a in re.findall(r'<img\b[^>]*\salt="([^"]*)"', doc, re.I):
            if a.strip():
                alts[a.strip()] += 1
    print("   %d distinct non-empty alt strings" % len(alts))
    generic = [a for a in alts if len(a.split()) < 4]
    if generic:
        warn("short alt text: %s" % generic)
    print("   shortest: %r" % (min(alts, key=len) if alts else None))

    # ---------------- 4. meta ---------------------------------------------
    print("\n4. META TITLES AND DESCRIPTIONS")
    titles, descs = {}, {}
    for name, doc in docs.items():
        t = re.search(r"<title>(.*?)</title>", doc, re.S | re.I)
        d = re.search(r'<meta name="description" content="([^"]*)"', doc, re.I)
        c = re.search(r'<link rel="canonical" href="([^"]*)"', doc, re.I)
        og = re.findall(r'<meta property="og:([a-z:]+)"', doc, re.I)
        if not t: fail("%s: no <title>" % name)
        if not d: fail("%s: no meta description" % name)
        if not c: fail("%s: no canonical" % name)
        for need in ("title", "description", "url", "image"):
            if need not in og:
                fail("%s: missing og:%s" % (name, need))
        titles[name] = html.unescape(t.group(1).strip()) if t else ""
        descs[name] = html.unescape(d.group(1).strip()) if d else ""
    for bag, what in ((titles, "title"), (descs, "description")):
        dup = [v for v, c in collections.Counter(bag.values()).items() if c > 1]
        if dup:
            fail("duplicate %s within site: %s" % (what, dup))
    bad_len = {n: len(v) for n, v in descs.items() if not (120 <= len(v) <= 160)}
    print("   unique titles: %d/%d   unique descriptions: %d/%d"
          % (len(set(titles.values())), len(titles),
             len(set(descs.values())), len(descs)))
    print("   descriptions outside 120-160 chars: %d %s"
          % (len(bad_len), bad_len if bad_len else ""))

    # ---------------- 5. certification claims ------------------------------
    print("\n5. CERTIFICATION AND ACCREDITATION CLAIMS  (must be zero)")
    banned = ["certif", "accredit", r"\bISA\b", r"\bTCIA\b", "CAN/ULC", "CUFCA",
              "qualified arborist", r"\bWSIB\b", "licensed arborist", "award-winning"]
    total_banned = 0
    for pat in banned:
        hits = []
        for name, doc in docs.items():
            body = text_of(main_of(doc)) + " " + titles.get(name, "") + " " + descs.get(name, "")
            n = len(re.findall(pat, body, re.I))
            if n: hits.append("%s x%d" % (name, n))
        total_banned += len(hits)
        print("   %-22s %s" % (pat, ", ".join(hits) if hits else "0"))
        if hits:
            fail("banned claim %r appears: %s" % (pat, hits))
    print("   TOTAL pages carrying a banned claim: %d" % total_banned)

    # ---------------- 6. head-term density ---------------------------------
    print("\n6. HEAD-TERM DENSITY  (main text + title + meta; target 4.0%%)")
    print("   %-42s %6s %7s %7s" % ("page", "words", "head%", "all-kw%"))
    site_kw = site_words = 0
    rows = []
    for name in sorted(docs):
        doc = docs[name]
        body = text_of(main_of(doc)) + " " + titles[name] + " " + descs[name]
        w = len(words(body))
        if not w: continue
        head = head_terms.get(name, head_terms["*"])
        hk = phrase_count(body, head) * len(head.split())
        allk = hk + sum(phrase_count(body, t) * len(t.split())
                        for t in other_terms if t != head)
        rows.append((name, w, 100.0 * hk / w, 100.0 * allk / w, head))
        site_kw += hk; site_words += w
    for name, w, hp, ap, head in rows:
        flag = "" if 3.9 <= hp <= 4.4 else "  <-- outside 3.9-4.4"
        print("   %-42s %6d %6.2f%% %6.2f%%%s" % (name, w, hp, ap, flag))
    print("   %-42s %6d %6.2f%%" % ("SITE-WIDE (head term)", site_words,
                                    100.0 * site_kw / max(site_words, 1)))
    for name, w, hp, ap, head in rows:
        if not (3.8 <= hp <= 4.5):
            warn("%s head-term density %.2f%% (target 4.0)" % (name, hp))

    # ---------------- 7. place-name density --------------------------------
    print("\n7. PLACE-NAME DENSITY  (<p> text in main; ~1%% on service pages,"
          " 5-7%% on contact)")
    for name in sorted(docs):
        body = " ".join(paras_of(docs[name]))
        w = len(words(body))
        if not w: continue
        pn = sum(phrase_count(body, p) * len(p.split()) for p in place_names)
        print("   %-42s %6d %6.2f%%" % (name, w, 100.0 * pn / w))

    # ---------------- 8. internal linking requirements ---------------------
    print("\n8. INTERNAL LINKING (the owner's stated requirements)")
    def links_in_main(doc):
        return set(re.findall(r'<a\b[^>]*href="([^"]+)"', main_of(doc)))
    def body_links(doc):
        """Links inside <p> only - i.e. links written into the copy, not the
        service-card grid or the CTA buttons the template emits everywhere."""
        out = set()
        for m in re.finditer(r'<p\b[^>]*>(.*?)</p>', main_of(doc), re.S | re.I):
            out |= set(re.findall(r'href="([^"]+)"', m.group(1)))
        return out
    home = docs.get("index.html", "")
    hb = body_links(home)
    ok_about = any(l.rstrip("/").endswith("/" + ABOUT[:-5]) for l in hb)
    ok_contact = any(l.rstrip("/").endswith("/" + CONTACT[:-5]) for l in hb)
    print("   home body copy links to /about   : %s" % ("YES" if ok_about else "NO"))
    print("   home body copy links to /contact : %s" % ("YES" if ok_contact else "NO"))
    if not ok_about: fail("home page body copy does not link to /about")
    if not ok_contact: fail("home page body copy does not link to /contact")

    service_pages = [n for n in docs if n not in
                     ("index.html", "services.html", ABOUT, CONTACT,
                      "faq.html", "privacy-policy.html", "terms.html", "404.html")]
    for n in sorted(service_pages) + [ABOUT, CONTACT]:
        bl = body_links(docs[n])
        ok = any(l == "/" for l in bl)
        print("   %-42s links back to / in body copy: %s" % (n, "YES" if ok else "NO"))
        if not ok: fail("%s body copy has no link back to the home page" % n)

    # every service listed on the home page, each with a link
    print("   services listed on the home page with a link:")
    hl = links_in_main(home)
    for n in sorted(service_pages):
        present = ("/" + n[:-5]) in hl
        print("      %-44s %s" % (n[:-5], "YES" if present else "NO"))
        if not present: fail("home page does not link to /%s" % n[:-5])

    # ---------------- 9. outbound links ------------------------------------
    print("\n9. OUTBOUND LINKS")
    hosts = collections.Counter()
    for doc in docs.values():
        for h in re.findall(r'href="https?://([^/"]+)', doc):
            hosts[h] += 1
    if hosts:
        for h, c in hosts.most_common():
            print("   %-46s x%d" % (h, c))
    else:
        print("   none")
    # The site's own canonical host is not a cross-link. Only a link to a
    # DIFFERENT tree-trimming domain in the network is the doorway signal.
    self_host = ""
    m = re.search(r'<link rel="canonical" href="https?://([^/"]+)', home)
    if m: self_host = m.group(1).lower()
    own = [h for h in hosts
           if "treetrimming" in h.replace("-", "").lower()
           and h.lower().lstrip("www.") != self_host.lstrip("www.")]
    print("   own canonical host (not a cross-link): %s" % (self_host or "unknown"))
    print("   links to the owner's OTHER city sites: %d %s"
          % (len(own), own if own else "(must be zero)"))
    if own: fail("cross-links to sibling city sites: %s" % own)

    # ---------------- 10. page weight --------------------------------------
    print("\n10. PAGE WEIGHT (index.html)")
    def kb(p): return os.path.getsize(p) / 1024.0
    css = sum(kb(f) for f in glob.glob(os.path.join(site, "*.css")))
    js = sum(kb(f) for f in glob.glob(os.path.join(site, "*.js")))
    himg = glob.glob(os.path.join(site, "images", "hero-*-1200.webp"))
    hero = kb(himg[0]) if himg else 0
    lazy = sum(kb(f) for f in glob.glob(os.path.join(site, "images", "*.webp"))) - hero
    print("   html %.0f KB + css %.0f KB + js %.0f KB + hero %.0f KB = %.0f KB initial"
          % (kb(os.path.join(site, "index.html")), css, js, hero,
             kb(os.path.join(site, "index.html")) + css + js + hero))
    print("   lazy-loaded imagery (all other webp): %.0f KB" % lazy)

    # ---------------- 11. sitemap and canonicals ---------------------------
    print("\n11. SITEMAP AND CANONICAL HOST")
    sm = os.path.join(site, "sitemap.xml")
    if os.path.exists(sm):
        s = open(sm, encoding="utf-8").read()
        locs = re.findall(r"<loc>([^<]+)</loc>", s)
        host = collections.Counter(re.match(r"https?://([^/]+)", l).group(1) for l in locs)
        print("   %d URLs, host(s): %s" % (len(locs), dict(host)))
        for bad in ("privacy-policy", "terms", "404"):
            if any(bad in l for l in locs):
                fail("sitemap contains %s (should be excluded, noindex)" % bad)
        print("   privacy/terms/404 excluded: %s"
              % ("YES" if not any(b in l for l in locs
                                  for b in ("privacy-policy", "terms", "404")) else "NO"))
        if any(l.endswith(".html") for l in locs):
            fail("sitemap contains .html URLs")
    for n in ("privacy-policy.html", "terms.html"):
        if n in docs and "noindex" not in docs[n]:
            fail("%s is not noindex" % n)
    print("   privacy and terms carry noindex: %s"
          % ("YES" if all("noindex" in docs.get(n, "noindex")
                          for n in ("privacy-policy.html", "terms.html")) else "NO"))

    # ---------------- 12. cross-site verbatim overlap ----------------------
    if compare_dirs:
        print("\n12. VERBATIM OVERLAP vs SIBLING CITIES  (6+ word runs, <p> text"
              " in main, excluding privacy/terms/404)")
        SKIP = {"privacy-policy.html", "terms.html", "404.html"}

        def grams(d):
            """Every 6-gram in a site's paragraph text."""
            out = set()
            for n, doc in d.items():
                if n in SKIP:
                    continue
                for p in paras_of(doc):
                    w = words(p)
                    for i in range(len(w) - 5):
                        out.add(" ".join(w[i:i + 6]))
            return out

        def covered(d, theirs):
            """Share of MY words that sit inside a run shared with them.

            The first version of this counted matching 6-grams and multiplied by
            six, which is nonsense: a shared run of N words contains N-5
            overlapping 6-grams, so every long match was counted about six times
            over. St. George came out at 239% against Paris. This marks word
            POSITIONS instead, so a word inside three overlapping shared grams is
            still one word, and the figure is a real percentage.
            """
            total = hits = 0
            longest = {}
            for n, doc in d.items():
                if n in SKIP:
                    continue
                for p in paras_of(doc):
                    w = words(p)
                    total += len(w)
                    mark = [False] * len(w)
                    for i in range(len(w) - 5):
                        g = " ".join(w[i:i + 6])
                        if g in theirs:
                            for j in range(i, i + 6):
                                mark[j] = True
                    # pull the actual shared runs out for reporting
                    i = 0
                    while i < len(mark):
                        if mark[i]:
                            j = i
                            while j < len(mark) and mark[j]:
                                j += 1
                            run = " ".join(w[i:j])
                            longest[run] = max(longest.get(run, 0), j - i)
                            i = j
                        else:
                            i += 1
                    hits += sum(mark)
            return hits, total, longest

        mine_grams = grams(docs)
        for cd in compare_dirs:
            od = {os.path.basename(p): open(p, encoding="utf-8").read()
                  for p in glob.glob(os.path.join(cd, "*.html"))}
            if not od:
                print("   %-40s (no built pages found)" % cd)
                continue
            label_o = os.path.basename(os.path.dirname(cd)) or cd
            hits, total, longest = covered(docs, grams(od))
            pct = 100.0 * hits / max(total, 1)
            print("   %-42s %5.2f%%  (%d of %d paragraph words)"
                  % (label_o, pct, hits, total))
            if pct > 3.0:
                fail("overlap with %s is %.2f%% (>3%%)" % (label_o, pct))
            for run in sorted(longest, key=lambda r: -longest[r])[:10]:
                print("        %2d words  %r" % (longest[run], run[:96]))

    # ---------------- verdict ---------------------------------------------
    print("\n" + "=" * 78)
    if fails:
        print("FAILURES (%d):" % len(fails))
        for f in fails: print("  * " + f)
    else:
        print("No failures.")
    if warns:
        print("\nWarnings (%d):" % len(warns))
        for w in warns: print("  - " + w)
    print("=" * 78)
    return len(fails)


if __name__ == "__main__":
    cfg = json.load(open(sys.argv[1]))
    sys.exit(audit(cfg["site"], cfg["head_terms"], cfg["other_terms"],
                   cfg["place_names"], cfg.get("compare", []), cfg["label"],
                   cfg.get("aliases")))
