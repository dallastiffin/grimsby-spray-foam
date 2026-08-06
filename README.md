# Grimsby Epoxy Floors — Website

Static site for **Grimsby Epoxy Floors**, Grimsby, Ontario. No framework, no build server, no monthly hosting cost.

```
Grimsby-Epoxy-Floors-Website-Content.md   <- all copy lives here (source of truth)
build.py                                  <- turns the markdown into the site
wrangler.toml                             <- Cloudflare deploy config
site/                                     <- generated output, THIS is what deploys
*.png                                     <- original photos (tracked, never served)
```

---

## Do these three things before you go live

### 1. Set your real domain

Open `build.py` and find this line near the top:

```python
DOMAIN = "https://www.grimsbyepoxyfloors.ca"
```

Change it to your actual domain, then run `python build.py`. This feeds canonical
tags, Open Graph tags, `sitemap.xml` and the schema markup. Getting it wrong will
hurt indexing.

### 2. Deliver leads to a Google Sheet

Every page has an estimate form. **It validates and shows a success message, but
nothing is delivered until you complete this setup.**

Leads go straight into a Google Sheet you own, via a Google Apps Script web app.
No third-party form service, no monthly fee, no row limits.

**Create the sheet and script**

1. Go to <https://sheets.new>. That URL always creates a *native* Google Sheet.

   > Do not upload an Excel file and use that. Uploaded `.xlsx` files open in a
   > compatibility mode with **no Extensions menu**, and Apps Script cannot read
   > them at all. If you see a small `.XLSX` badge beside the filename, you are
   > in the wrong kind of file — start again at sheets.new.

2. Name it *Grimsby Epoxy Floors — Leads*.
3. In that sheet: **Extensions → Apps Script**.
4. Delete the placeholder `function myFunction() {}`, then open
   `google-apps-script.gs` from this repo, copy the whole file, and paste it in.
5. Optional — for email alerts on every lead, set:

   ```js
   var NOTIFY_EMAIL = 'tiffindevelopments@gmail.com';
   ```

   Leave it as `''` to skip alerts and just collect rows.
6. Save (the disk icon).

**Check it works before touching the website**

In the Apps Script editor, choose `testWrite` from the function dropdown and
click **Run**. Google will ask for permission the first time — you'll see an
"unverified app" warning, which is expected for your own script. Click
**Advanced → Go to (project name)** and allow it.

Switch back to the sheet. A **Leads** tab should exist with a header row and one
test row. Delete the test row.

**Deploy it**

1. **Deploy → New deployment**
2. Click the gear next to "Select type" → **Web app**
3. Set:

   | Field | Value |
   |---|---|
   | Execute as | **Me** |
   | Who has access | **Anyone** |

   "Anyone" is required — visitors submitting the form are not signed in to
   Google. They can only POST data in; they cannot read your sheet.
4. **Deploy**, then copy the **Web app URL**. It ends in `/exec`.

**Connect the website**

Open `site/script.js` and paste the URL:

```js
var SHEET_ENDPOINT = 'https://script.google.com/macros/s/AKfy.../exec';
```

Then rebuild so the cache fingerprint updates:

```bash
python build.py
```

All 14 pages share the same script, so this one edit switches on every form.

**Test on the live site.** Submit a real entry and confirm the row appears. If
the form shows an error but rows still land in the sheet, it's a CORS quirk —
set `SHEET_USE_NO_CORS = true` in `site/script.js`, rebuild, and push.

> **Whenever you edit `google-apps-script.gs`**, you must redeploy for the change
> to take effect: **Deploy → Manage deployments → pencil icon → Version: New
> version → Deploy**. Editing and saving alone does nothing to the live endpoint.

### 3. Add the real logo

`site/images/logo.svg` and `site/images/favicon.svg` are the last placeholders on
the site. Everything else is your own photography. Replace both files, keeping
the same names, and nothing else needs to change.

---

## Uploading to GitHub

The repo is already connected to <https://github.com/dallastiffin/grimsby-epoxy-flooring>.
This commit **replaces** the previous version of the site, so expect a large diff:
the old `site/assets/` tree is deleted and the new `site/` tree is added.

Open a terminal in this folder and run:

```bash
git add -A
git status              # look it over before committing
git commit -m "Rebuild site: new copy, real photography, project gallery"
git push origin main
```

`git add -A` matters here — plain `git add .` will not stage the deleted files
from the old structure.

If `git push` asks for a password, GitHub no longer accepts account passwords.
Either install [GitHub CLI](https://cli.github.com) and run `gh auth login`, or
create a personal access token at **GitHub → Settings → Developer settings →
Personal access tokens** and paste that in place of the password.

---

## Deploying on Cloudflare

The repo already contains `wrangler.toml`, so Cloudflare knows to serve the
`site/` folder. There are two ways to deploy — pick one.

### Option A — connect the repo (recommended)

Every push to `main` rebuilds and deploys automatically.

1. Go to the [Cloudflare dashboard](https://dash.cloudflare.com) → **Compute (Workers)**
2. **Create** → **Import a repository**
3. Authorise GitHub and pick `dallastiffin/grimsby-epoxy-flooring`
4. Set the build settings:

   | Setting | Value |
   |---|---|
   | Build command | *(leave empty)* |
   | Deploy command | `npx wrangler deploy` |
   | Root directory | `/` |

   Leave the build command empty. The HTML is already generated and committed —
   there is nothing to compile. `wrangler.toml` tells the deploy step that
   `./site` is the folder to publish.

5. **Save and Deploy**

You get a `*.workers.dev` URL within about a minute. After that, every
`git push origin main` redeploys on its own, and pull requests get their own
preview URL.

### Option B — deploy from your machine

Useful for a one-off or for testing before wiring up Git.

```bash
npm install -g wrangler
wrangler login
wrangler deploy
```

---

## Pointing your domain at it

1. In the Cloudflare dashboard, open the Worker → **Settings** → **Domains & Routes**
2. **Add** → **Custom domain**
3. Enter `grimsbyepoxyfloors.ca` and add `www.grimsbyepoxyfloors.ca` as a second one

If the domain is already on Cloudflare, DNS records are created for you and the
certificate is issued automatically — usually a few minutes. If the domain is
registered elsewhere, first add the site to Cloudflare and update the
nameservers at your registrar, which can take a few hours to propagate.

Whichever hostname you settle on — with or without `www` — make sure `DOMAIN` in
`build.py` matches it exactly, then rebuild and push. Canonical tags pointing at
a hostname that redirects will confuse Google.

---

## After launch

- Submit `https://yourdomain.ca/sitemap.xml` in [Google Search Console](https://search.google.com/search-console)
- Create the Google Business Profile listing — the FAQ answers in the markdown
  are written to be pasted straight into it
- Run the live URL through [PageSpeed Insights](https://pagespeed.web.dev)

---

## Editing the site later

**Copy changes:** edit `Grimsby-Epoxy-Floors-Website-Content.md`, then:

```bash
python build.py
```

Every page is rebuilt with consistent navigation, schema, CTAs and forms.
**Do not hand-edit the HTML in `site/`** — it gets overwritten on the next build.

**Photos:** drop new PNGs in the root folder, update the `PAGE_PHOTOS` or
`GALLERY_PHOTOS` table in `build.py`, then:

```bash
python build.py --images      # needs Pillow: pip install pillow
```

This crops, resizes and exports every photo as WebP plus a JPG fallback at two
widths. See `site/images/README.txt` for which source photo feeds which slot.

**Design and behaviour:** `site/style.css` and `site/script.js` are hand-written
and never regenerated. Edit them directly.

---

## What is in the site

14 pages: home, services index, 6 service pages, about, FAQ, contact, privacy
policy, terms, and a 404 page.

Each page carries a unique title and meta description, Open Graph tags, canonical
tag, LocalBusiness schema, breadcrumbs where relevant, multiple CTAs, and the
estimate form. The home page also has FAQ schema and a 12-photo project gallery
with a keyboard-accessible lightbox.

Initial load for the home page is about 208 KB — one eager image, everything
else lazy-loaded.

### One note on photography

`warehouse grey epoxy.png` was **deliberately left out of the site**. It has
another company's branding visible on the crew shirt and the resin pail. It is
still in the repo as a master file, but nothing references it. If you get a
commercial warehouse photo of your own, add it to `PAGE_PHOTOS` in `build.py`
as `service-commercial-epoxy-flooring` — that card currently uses a large open
grey floor as a stand-in.
