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
