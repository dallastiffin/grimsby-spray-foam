# Launching a new city

The repeatable process. Grimsby is the template; every city after it follows
these steps. Budget an hour or so, most of it waiting on DNS.

Before you start, have ready:

- City name, region, and the towns you'll service
- Phone number for that city
- Domain, registered (Namecheap or wherever)
- Logo (or reuse the same one)

---

## Step 1 — Scaffold the project

In PowerShell, from the Grimsby folder:

```powershell
cd "C:\Users\Lenovo\Documents\Tiffin Developments Lead Generation\Epoxy Flooring Content\Grimsby Epoxy Flooring"
python tools/new-city.py
```

It asks for city, province, region, business name, phone, domain, service area,
latitude/longitude, and where to create the folder. Press Enter to accept any
default in brackets.

It creates a sibling folder with everything already rewritten: `CONFIG` in
`build.py`, the Worker name in `wrangler.toml`, the web manifest, and a cleared
form endpoint in `script.js`.

It does **not** copy the Grimsby copy, the git history, or the generated HTML.

> Get the lat/long from Google Maps: right-click the city centre, and the first
> item in the menu is the coordinates. Leave blank if you don't have them.

---

## Step 2 — Write the copy

The scaffolder left a stub markdown file. Replace it entirely.

Paste this to me, filling in the blanks:

```
Write website content for [BUSINESS NAME], an epoxy flooring company in
[CITY], [PROVINCE]. Phone [PHONE].

Match the exact structure of the Grimsby content file:
  - Home page, ~2000 words, 15+ question or statement headers, plus a
    "## Frequently Asked Questions" section with 5 "### " questions
  - 6 service pages, ~600 words each: Flake Epoxy Flooring, Garage Floor
    Coating, Polyaspartic Floor Coating, Commercial Epoxy Flooring,
    Basement Floor Coating, Concrete Floor Coating
  - About ~700 words, Contact ~300 words, standalone FAQ, SEO titles and
    meta descriptions
  - A final "# SITE COPY" block containing every reusable string: hero
    badges, all CTA headings and text, form headings and intros, sidebar
    text, gallery intro, services page copy, FAQ page copy, 404 wording,
    and a "## Photo Alt Text" section with one "slug: description" line
    per image. Copy the section names exactly from the Grimsby file.
  - "---" between blocks, page markers "# HOME PAGE", "# SERVICE PAGE 1..6",
    "# ABOUT PAGE", "# CONTACT PAGE", "# FAQ SECTION",
    "# SEO TITLES AND META DESCRIPTIONS", "# SITE COPY"

The home page must have one section starting "Why Choose" and one starting
"Serving" - build.py finds those by prefix.

Do not reuse Grimsby's wording. Different section order, different examples,
different FAQ questions, and local specifics that only apply to this city.

Local specifics: [CLIMATE NOTES], nearby towns [LIST], local landmarks or
roads worth naming [LIST].

Same rules as Grimsby: grade 6-8 reading level, short paragraphs, no AI
filler phrases, keyword targets on epoxy flooring / garage floor coating /
garage flooring / epoxy floor coating / polyaspartic floor coating / best
garage flooring. SEO titles "[page] | City, Province". Meta descriptions
120-160 chars including "call us at [PHONE]".
```

Save the result over the stub file, keeping the filename the scaffolder chose.

**Do not rename the file** unless you also update `CONTENT_FILE` in `build.py`.

---

## Step 3 — Photos

If you reused the Grimsby photos, skip to Step 4.

Otherwise put the new photos in the project root, then open `build.py` and
update two tables to match your filenames:

- `PAGE_PHOTOS` — hero, service cards, about and services page images
- `GALLERY_PHOTOS` — the home page gallery

Alt text in those tables is templated, so `{CITY}` and `{BUSINESS}` fill
themselves in.

**Check every photo for other companies' branding** before using it. One of the
Grimsby photos had a competitor's name on a crew shirt and resin pail, and it
went live before anyone noticed.

---

## Step 4 — Logo and colours

Reusing the same logo, same brand colours? Just run:

```powershell
python tools/make-logo.py
```

For a different logo: replace `Logo.png` first. The script expects the same
layout as the Grimsby master — stacked wordmark on the left, rounded app icon
on the right. If the new file is laid out differently, adjust `ARTWORK`,
`SPLIT_END` and `ICON_START` at the top of `tools/make-logo.py`.

For different brand colours, edit four variables at the top of
`site/style.css`:

```css
--color-primary:        #0b4d25;
--color-primary-dark:   #07351a;
--color-primary-light:  #146632;
--color-accent:         #c24c0c;
```

Ask me to check contrast if you change these. White text on the old orange was
failing WCAG at 3.52:1 and nobody spotted it until I ran the numbers.

---

## Step 5 — Build

```powershell
cd "C:\path\to\the\new\city folder"
python tools/make-logo.py
python build.py --images
```

`--images` re-exports every photo and is slow. After the first run, plain
`python build.py` is enough — use it any time you change copy, CSS or JS.

If the content file isn't finished you'll get a clear message saying so.

---

## Step 6 — Google Sheet for leads

Per city, so leads don't mix.

1. [sheets.new](https://sheets.new) — must be a native Google Sheet, not an
   uploaded `.xlsx` (those have no Extensions menu)
2. Name it `[City] Epoxy Floors - Leads`
3. **Extensions → Apps Script**, delete the placeholder, paste in
   `google-apps-script.gs`
4. Set `NOTIFY_EMAIL` to where you want alerts
5. Run `testWrite`, approve the permissions prompt, confirm a row appears,
   delete the test row
6. **Deploy → New deployment → Web app**, Execute as **Me**, Who has access
   **Anyone**
7. Copy the `/exec` URL into `SHEET_ENDPOINT` in `site/script.js`
8. `python build.py` again so the cache fingerprint updates

---

## Step 7 — GitHub

```powershell
git init
git add -A
git commit -m "Initial site"
```

Create an empty repo on GitHub named after the city, then:

```powershell
git remote add origin https://github.com/dallastiffin/[REPO-NAME].git
git branch -M main
git push -u origin main
```

---

## Step 8 — Cloudflare

1. Dashboard → **Workers & Pages** → **Create application** → **Import a
   repository**
2. Pick the new repo
3. Settings:

   | Field | Value |
   |---|---|
   | Worker name | **must exactly match `name` in `wrangler.toml`** |
   | Build command | leave empty |
   | Deploy command | `npx wrangler deploy` |
   | Root directory | `/` |

4. **Save and Deploy**

A name mismatch is the most common failure. The scaffolder set `name` in
`wrangler.toml` for you — copy it exactly.

---

## Step 9 — Domain

1. Cloudflare → **Add a domain** → enter it → **Free** plan
2. Copy the two nameservers it gives you
3. Namecheap → **Domain List** → **Manage** → Nameservers → **Custom DNS** →
   paste both → **click the green checkmark to save**
4. Wait for Cloudflare to email that the domain is Active (10 min to a few hours)
5. **DNS → Records:** delete any leftover **A** record pointing at a Namecheap
   parking IP (`192.64.x.x`). **Keep the MX and TXT records** — those are email
   forwarding.
6. Worker → **Settings → Domains & Routes → Add → Custom domain**, add both the
   bare domain and the `www` version
7. Pick one as canonical and redirect the other: **Rules → Redirect Rules**,
   hostname equals the non-canonical one, dynamic redirect to
   `concat("https://[canonical]", http.request.uri.path)`, 301, preserve query
   string
8. Confirm `DOMAIN` in `build.py` matches the canonical hostname exactly, then
   rebuild and push

---

## Step 10 — Verify

Ask me to check the build before you push — links, duplicate IDs, heading
structure, contrast and page weight take seconds and catch things you won't see.

Then on the live site:

- [ ] Bare domain loads, padlock present
- [ ] The non-canonical hostname 301s to the canonical one
- [ ] A deep link like `/garage-floor-coating` loads with no redirect
- [ ] `/nope` shows the styled 404
- [ ] Mobile: hamburger opens, dropdown expands, sticky call bar shows
- [ ] Submit a real form entry, confirm the row lands in the Sheet and the
      email arrives
- [ ] `/sitemap.xml` shows the correct domain
- [ ] Submit the sitemap in Google Search Console

---

## What carries over untouched

Layout, SEO scaffolding, schema, breadcrumbs, forms, honeypot, validation,
gallery, lightbox, accessibility, cache headers, fingerprinting, 404, redirect
handling, `_headers`, `robots.txt`, sitemap generation.

None of it needs looking at again.

## What changes per city

`CONFIG` in `build.py`, the markdown copy, photos plus the two photo tables,
`Logo.png`, the four colour variables, `SHEET_ENDPOINT`, and the git remote.

That's the whole list.
