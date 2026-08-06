# Building the next site faster

Notes from the Grimsby build, written down so the next one takes a fraction of
the time. Two parts: the fastest path (reuse this repo), and a prompt template
for when you do want a fresh build.

---

## Part 1 — The real speedup: reuse this repo

You are building city sites for the same business type. Rewriting from scratch
each time is the slow path. This repo is already 90% a template.

For a new city, only these change:

| What | Where |
|---|---|
| City, phone, business name, domain | config block at the top of `build.py` |
| All copy | the markdown file |
| Service list and URLs | `SERVICE_PAGES` in `build.py` |
| Photos | root folder + `PAGE_PHOTOS` / `GALLERY_PHOTOS` tables |
| Logo | `Logo.png`, then `python tools/make-logo.py` |
| Brand colours | four CSS variables at the top of `style.css` |
| Sheet endpoint | one line in `script.js` |

Everything else — layout, SEO scaffolding, schema, forms, gallery, lightbox,
accessibility, cache headers, Cloudflare config — carries over untouched.

**Ask for this first:** *"Extract every city-specific value in build.py into a
single CONFIG block at the top, so a new city only needs that block, a new
markdown file, and new photos."* That one refactor is worth more than any
prompt improvement.

Then per city: copy the folder, edit CONFIG, drop in copy and photos, run
`python tools/make-logo.py && python build.py`, push.

---

## Part 2 — What actually cost time this round

Not theory. These are the specific things that caused rework, in rough order of
cost. Each one is now a line you can put in the brief.

### 1. Stale CSS cache hid every change I made

I set a 7-day cache on `style.css` with no cache-busting. You spent several
rounds looking at an old stylesheet while I insisted the layout was correct.
Worst single time sink in the project.

> **Add:** "Fingerprint CSS and JS filenames or query strings with a content
> hash at build time, so edits are never masked by browser or edge caching."

### 2. The site root returned 404 after deploy

I set `html_handling = "none"` in `wrangler.toml` to avoid redirect hops. With
that value, `/` does not map to `index.html`, so the home page 404'd.

> **Add:** "URLs must be extensionless (`/about`, not `/about.html`). The site
> root must serve the home page. Internal links, canonical tags, Open Graph
> URLs and the sitemap must all use the exact final URL form — no redirects."

### 3. I made placeholder images while real photos sat in the folder

Twelve project photos were already there. I generated grey SVG placeholders and
you had to tell me to use the real ones.

> **Add:** "Photos are already in the project folder. Use them. Resize and
> compress to responsive WebP with JPG fallback, lazy-load everything below the
> fold, and set width/height on every image."

### 4. Logo and brand colours arrived last

The site was built navy, the logo turned out dark green, and every colour had to
be redone. Also the palette I chose had a button contrast failure I only caught
when re-checking.

> **Add:** "Brand colours are `#______` and `#______`; the logo is `Logo.png` in
> the project folder. Use these from the start. All text must meet WCAG AA
> (4.5:1 normal, 3:1 large) — verify numerically, do not eyeball it."

### 5. The contact form was rebuilt three times

Placeholder, then a third-party email service, then Google Sheets. Each pass
touched every page.

> **Add:** "Form submissions go to a Google Sheet via Apps Script, and also
> email `______`. Build this in from the first pass, not as a placeholder."

### 6. The domain placeholder was wrong

I guessed `.ca`. The real domain is `.com`. That value was baked into canonical
tags, Open Graph, schema and the sitemap on every page.

> **Add:** "The live domain is `https://______`. Use it everywhere from the
> start. Pick www or non-www and be consistent."

### 7. I did not know a repo and a previous version already existed

The folder was already a git repo with a deployed site and a `site/` output
structure, and I only found out when we went to deploy. The previous build also
had notes I should have read first.

> **Add:** "This folder is an existing git repo connected to `______`, deployed
> on Cloudflare from the `site/` folder. Read the existing README and
> `wrangler.toml` before changing any structure."

### 8. The hero was redesigned five times

Image right, then form right, then a copy panel, then a lighter panel, then no
panel, then a masthead. All avoidable with one description upfront.

> **Add:** "Hero layout: business name as a large masthead across the top,
> headline and copy on the left, estimate form on the right, background photo at
> full colour with contrast handled behind the text only."

### 9. One supplied photo had a competitor's branding in it

`warehouse grey epoxy.png` has another company's name on the crew shirt and
resin pail. It went live on a service card before I caught it.

> **Add:** "Check every supplied photo for third-party logos, watermarks or
> branding, and flag anything you find rather than publishing it."

### 10. Content and build were two separate prompts

The copy was written first, then converted. That meant a second pass over
structure. Worth combining, or at least writing the copy against the known page
structure.

---

## Part 3 — Prompt template

Fill in the blanks. Everything below is either a fact I cannot guess or a
decision that caused rework this time.

```
Build a static website for [BUSINESS], a [TRADE] company in [CITY], [PROVINCE].

FACTS
  Business name:      
  Phone:              
  Live domain:        https://            (use exactly this, www or not)
  Brand colours:      #          primary, #          accent
  Logo:               Logo.png in this folder
  Photos:             in this folder - use them, do not make placeholders
  Service pages:      [list, in nav order]
  Leads go to:        Google Sheet via Apps Script + email to ____
  Existing repo:      [URL, or "none"]
  Hosting:            Cloudflare Workers, deploys from site/

STRUCTURE
  Copy lives in one markdown file as the single source of truth.
  One Python generator script builds every page from it. Never hand-edit
  generated HTML. Shared header, footer, CTAs and forms come from the
  generator so they cannot drift.

TECHNICAL - these caused rework last time, do them from the start
  - Extensionless URLs. Root serves the home page. No redirect on any
    internal link or canonical tag.
  - Fingerprint CSS/JS with a content hash so caching never hides an edit.
  - Responsive WebP with JPG fallback, two widths, lazy below the fold,
    width/height on every image to prevent layout shift.
  - Every page: unique title and meta description, canonical, Open Graph,
    LocalBusiness schema, breadcrumbs, exactly one h1.
  - Lead form on every page: name, email, phone, city, service, message,
    honeypot, client-side validation, success state. Working delivery, not
    a placeholder.
  - WCAG AA verified numerically for every text-on-background pair.
  - Cloudflare: wrangler.toml with assets directory, _headers, 404 page,
    sitemap.xml, robots.txt.

DELIVERABLES
  Working site, generator script, logo pipeline script, and a README with
  exact PowerShell and Cloudflare steps for deploying and for adding a new
  city later.

VERIFY BEFORE HANDING OVER
  No broken links or image references. One h1 per page. No duplicate element
  IDs. Contrast ratios pass. Report page weight. Confirm the root URL and a
  deep link both resolve without redirects.
```

---

## Part 4 — How to work with me more efficiently

- **Tell me the constraint, not the fix.** "Body copy must stay readable on the
  photo" gets a better result than "make the overlay 50%", which I implemented
  three times before we found a value that passed contrast.
- **Screenshots are worth more than descriptions.** "The photo is above the
  copy" took several rounds to diagnose; the screenshot solved it immediately.
- **Say when something is already deployed.** I nearly restructured a live
  repo without knowing it was live.
- **Batch the visual feedback.** Five separate hero tweaks meant five rebuilds
  and five pushes. One list would have been one pass.
- **Let me verify before you push.** I can check links, contrast, duplicate IDs
  and page weight in seconds. Cheaper than finding it on the live site.
