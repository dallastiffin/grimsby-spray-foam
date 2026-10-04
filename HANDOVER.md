# Grimsby Spray Foam Insulation — v2 rebuild handover

Rebuilt 3 October 2026 from the Halifax Industrial Coatings generator under
`new-city-trade-site-v2`. This replaces the site that was migrated off
SitePanda earlier the same day.

**Rollback point: git tag `pre-v2-rebuild` (commit `02a718b`).**
`git reset --hard pre-v2-rebuild` returns the previous site exactly.

---

## Do these three things, in this order

### 1. Register the site with the Lead Router — BEFORE the site goes live

The form now posts to the shared Lead Router with `SITE_KEY = grimsby-spray-foam`.
**The site has never been registered**, so until you run this, leads land in the
router's "Unrouted Leads" sheet with `[UNROUTED: site=grimsby-spray-foam]`
prefixed to the message. They are not lost — the router still emails
`tiffindevelopments@gmail.com` — but they will not reach the Grimsby sheet.

```powershell
cd "C:\Users\Lenovo\Documents\Tiffin Developments Lead Generation\Spray Foam Content\Grimsby Spray Foam Insulation"
powershell -ExecutionPolicy Bypass -File .\register-lead-router.ps1
```

It reads `LEAD_ROUTER_ENDPOINT` and `LEAD_ROUTER_SECRET` straight out of
`_credentials\secrets.env`, so neither value is ever typed into a chat window.
It pings the router, registers the site, then sends one test lead.

A wrong secret still returns HTTP 200, so the script checks the response body
and exits non-zero on `success:false`. If that happens, **do not ship** — the
secret in `secrets.env` does not match the router's script properties.

Afterwards, look in Drive for **"Grimsby Spray Foam Insulation - Website
Leads"**. One test row, which you can delete. A row reading `[UNROUTED: ...]`
means registration did not take.

`register-lead-router.ps1` is gitignored. It must stay that way.

### 2. Push

```powershell
git push
```

Cloudflare Workers Builds deploys from this repo automatically. Purge the
Cloudflare cache afterwards — HTML went stale on the last cutover for exactly
this reason.

### 3. Add the 301s for five retired URLs

These were in the submitted sitemap and will 404 after the push. Their content
moved into body copy on the main pages. Cloudflare → the zone → **Rules →
Redirect Rules → Create rule**, expression:

```
(http.request.uri.path in {"/spray-foam-performance-across-climate-zones" "/heating-season-pricing-timelines" "/property-overhaul-planning" "/protecting-fresh-insulation-during-exterior-work" "/insulation-home-envelope-partners"})
```

Then a **dynamic** redirect, status **301**, preserve query string:

```
concat("https://www.grimsbysprayfoaminsulation.com",
  lookup_json_string(
    "{\"/spray-foam-performance-across-climate-zones\":\"/close-and-open-cell-spray-foam\",\"/heating-season-pricing-timelines\":\"/\",\"/property-overhaul-planning\":\"/new-construction-insulation\",\"/protecting-fresh-insulation-during-exterior-work\":\"/\",\"/insulation-home-envelope-partners\":\"/about-us\"}",
    http.request.uri.path))
```

If that expression is rejected on the free plan, five separate single-path
rules do the same job.

---

## What changed

| | Before | After |
|---|---|---|
| Generator | Windsor-derived | Halifax, with `intro_band()`, `rich()`, `_init_photos()` |
| Palette | charcoal + rust | spruce `#17382C`, cured-foam cream, bronze |
| Body type | sans | Georgia serif, condensed display |
| Pages | 16 | 14 (5 retired, FAQ kept) |
| Head-term density | 2.25% site-wide | **4.18%**, all 11 indexed pages in band |
| Lead form | per-city Apps Script | shared Lead Router |
| Worker name | grimsby-spray-foam | unchanged |

### Audit results

`audit.py` with `grimsby-spray-foam-config.json`: **No failures.**

- Head-term density: all 11 indexed pages inside 3.9–4.4%, site-wide 4.18%
- Overlap vs Windsor **2.52%**, vs Chatham **0.77%** (rule is under 3%)
- Certification claims: **0** across all ten banned patterns
- `britcheck.py`: **0 hits**
- 717 internal links and 363 image references checked, 0 dead, 0 carrying `.html`
- 14/14 unique titles and descriptions
- 18 contrast pairs computed, 0 failures, lowest 3.82:1 on `--color-border-strong`
- 0 hero prose violations, 0 hero bullet markers
- Initial page weight 238 KB

Warnings are `404`, `privacy-policy` and `terms` sitting outside the density
band. All three are `noindex` and excluded from the sitemap, so the band does
not apply.

### v2 layer

- `site/llms.txt` generated from CONFIG and `SERVICE_PAGES`
- `robots.txt` names seven AI crawlers explicitly
- JSON-LD validated: `HomeAndConstructionBusiness`, `FAQPage`,
  `BreadcrumbList`, per-service `Service`. 12 `areaServed` entries.
- `CLARITY_ID = ""` — set it when you create the Clarity project; the snippet
  is omitted entirely while it is empty

---

## Three inherited bugs fixed here that are STILL LIVE on Halifax

1. **`site.webmanifest` was referenced on every page and never generated.**
   14 dead links per build. Now generated in `build.py`.
2. **`script.js` hardcoded the source city's phone number** in the
   form-failure fallback. A failed submission on Grimsby was telling visitors
   to call Halifax. Now carries the Grimsby number.
3. **`.ext-link` is emitted by `build.py` with no matching CSS rule**, so every
   outbound link fell back to a default blue anchor. Now styled.

Also fixed here, and worth fixing on Halifax: the LocalBusiness schema always
emitted a `PostalAddress`, so every page published
`"streetAddress": "PLACEHOLDER - add street address"` to Google. The address
block is now conditional — locality, region and country only, until
`STREET_ADDRESS` and `POSTAL_CODE` hold real values.

---

## October 2026 — agricultural and commercial pages added

Eight services now, up from six. The owner pointed out that the first build
researched Grimsby's residential geography thoroughly and never touched
agriculture, despite the site already claiming Lincoln and West Lincoln as
service area. Both new pages carry new slugs — no legacy constraint.

- `/agricultural-insulation` — barns, machinery sheds, livestock housing,
  greenhouse service rooms, cold storage, farm shops
- `/commercial-insulation` — warehouses, fabrication shops, service garages,
  food and beverage, small units

Research is in `INDUSTRY.md` under "Agriculture — the Niagara fruit belt" and
"Commercial and industrial — west Niagara". Three things recorded there that
must not drift:

1. **Do not name the South Service Road development or its owner.** Naming a
   specific developer's project on a contractor site implies an association
   that does not exist. The copy refers to the corridor and the clear heights.
2. **Do not claim foam is a rodent barrier or resists chewing.** Competitor
   sites claim both; neither is true. The page says it gives rodents nothing
   to nest in, and says explicitly that this is not the same thing.
3. **Verify every "Grimsby business" fact is Ontario.** Grimsby *and* Lincoln
   both exist in North East Lincolnshire, England, and UK results dominate
   those searches.

**Gallery retitled.** It read "Recent Work" over a photo set that
`generated-industrial-agricultural-prompts.txt` documents as *"AI-generated
spray foam project illustrations; not photographs of completed customer
projects."* It now reads "What Spray Foam Insulation Looks Like Installed",
which sells the finish without asserting authorship. **The same heading is
still live on Halifax, Windsor, Chatham and the other siblings.**

### Audit after the change

`_audit-tools/` now exists in this folder with a Grimsby config — per-page head
terms, local place names, and four sibling sites in `compare`.

- Both new pages inside the density band; 0 British spellings; 0 certification
  claims; 0 images without alt; 16/16 unique titles and descriptions; both
  pages linked from the home page and linking back; initial weight 245 KB
- Sitemap 13 URLs, `llms.txt` and the `Service` schema both picked the pages up

### One failure, pre-existing, NOT introduced here

**Overlap with Leamington Spray Foam Insulation is 3.74%, against a 3% rule.**

This was never measured before — Leamington was not in the original compare
list, which only held Windsor and Chatham. Every one of the ten
highest-scoring matched phrases comes from pages that existed before this
change (crawl space headroom, the rebate "not the program administrator"
line, ducting and air handlers, foundation walls and rim joists, the written
spec sentence). None come from the agricultural or commercial copy.

So the two new pages are clean and the overlap is older than they are. It is
a real duplicate-content risk between two same-trade sibling sites and it
wants its own pass — rewriting shared boilerplate touches six already-indexed
pages, which is not something to fold into an additive change.

## Accepted deviations from the skill

**Cross-links to the owner's other sites — kept at the owner's instruction.**
The site links out to Hamilton, Barrie and Newmarket cabinet painting, Aurora
and Sarnia tree service, Caledon epoxy, and Milton, Windsor, Leamington and
Saint John spray foam. They now sit in body copy rather than on dedicated
resource pages, as instructed.

This is a deliberate, recorded exception to three rules in the skill
(`AVOIDING-DUPLICATE-SITES.md`, "Do not cross-link the city sites", and the
v2 guardrail "Internal linking: within one site only"). `audit.py` section 9
reports 0 because its pattern only matches `treetrimming` domains, so the
check passes mechanically rather than genuinely. The same-trade links —
Milton, Windsor, Leamington, Saint John — are the highest-risk of the set.

**Pricing figures omitted at the owner's instruction.** This forfeits
`spray foam insulation cost`, 720/month nationally at SD 11, the
lowest-difficulty term in the keyword set.

---

## Open items

- `STREET_ADDRESS` and `POSTAL_CODE` are still `PLACEHOLDER`. The schema omits
  the address rather than publishing a placeholder. Supply real values and the
  next build picks them up.
- `HOURS_TEXT` is Monday–Saturday 7:00–18:00. Confirm or correct.
- Microsoft Clarity not set up. Create the project, put the ID in
  `CLARITY_ID`, rebuild.
- The v2 SEO gate (`seo-code-audit`, `technical-seo`, `aeotester` score) was
  not run before this cutover. Worth running against the live URL afterwards.
- Phase 8 ranking checks are meaningful about four weeks after launch.

## Rebuilding

```powershell
python build.py            # copy, CSS or JS changes
python build.py --images   # also re-export photos (slower)
python tools/make-logo.py  # after changing Logo.png or Favicon.png
```

Always rerun `build.py` after editing `site/style.css` or `site/script.js` —
the HTML carries a content hash of each, and without a rebuild the change
reaches nobody who has already visited.

Never hand-edit anything in `site/` except `style.css` and `script.js`.

---

## October 3 2026 (evening) — visual redesign, frontend-design pass

The earlier v2 rebuild changed the palette but kept the template's layout, so
the site still read as the old format. This pass replaces the look entirely.
**Copy is unchanged** — every page, slug, paragraph and FAQ comes from the same
markdown. Pushed live 3 Oct 2026 (commit bd60d94) together with the agricultural and commercial pages; Workers Builds succeeded and all 13 sitemap URLs return the new design.

What changed (all in `build.py` templates, `site/style.css`, `tools/make-logo.py`):

- **Palette from the logo**: charcoal `#2E2B27`, rust `#A84A1D`, cured-foam
  `#EBD9A6` on dark grounds only, drywall grey `#EDEDE9` as the alternate
  ground. `THEME_COLOR` now `#2E2B27`. 20 text/background pairs checked, lowest
  body pair 4.89:1 (rust on grey), input borders 3.97:1.
- **One signature device**: the logo's scalloped foam line. It rises behind the
  form at the foot of the home hero (one load animation, off under reduced
  motion), sits under every inner-page hero, and forms the top edge of the
  rust/charcoal call-to-action bands and the footer.
- **Type**: Archivo, self-hosted variable font (`site/fonts/`, SIL OFL, 90 KB),
  expanded width for headings, normal width for reading. No Google Fonts call.
- **Layout**: services shown as a ruled index with photos (not a card grid);
  dark "why choose" section; "What every job gets" as a bordered spec sheet;
  numbered steps only on the install process (the one real sequence); service
  and about pages get a sticky "On this page" contents list beside the copy;
  FAQ and quote form in two-column layouts. Top bar removed.
- **Logo assets fixed**: the old script squashed the whole lockup into a square,
  so the header logo and favicons were unreadable. Now a tight horizontal lockup
  (`lockup-*.png`, plus a light version for the footer) and the house mark alone
  for favicons. Old `wordmark-*.png` names still exist as aliases.
- Hero rule still holds: no paragraphs in any hero.
- `Service` schema `url` now uses the extensionless URL (was `.html`).
- Two epoxy leftovers in the terms page ("slab") reworded.

Audit after the change: 0 dead links, 0 duplicate ids, one h1 per page, 0 banned
claims, 0 British spellings, all JSON-LD parses. Head-term density moved closer
to band on most pages because template labels no longer repeat the head term:
indexed pages in 3.9–4.4% went from 3 to 8 of 13. Still outside: index 4.49%,
about 4.63%, faq 4.50%, services 5.26%, commercial 3.73%.

Rollback for this pass only: `git checkout -- build.py site tools` before
committing (nothing has been committed for it).
