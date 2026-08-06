# Grimsby Spray Foam — SitePanda to Cloudflare Migration Runbook

Everything that can be done without your accounts is done. This file covers
the rest, in the order it has to happen.

**Do not cancel SitePanda until step 6 is verified.**

---

## Where things stand

| Item | Status |
|---|---|
| Site built from the Windsor generator | Done — 14 pages in `site/` |
| All 10 indexed URLs preserved | Done — verified, zero redirects needed |
| Copy rewritten and Grimsby-specific | Done — 9,100 words, 0.98% prose overlap with Windsor |
| Photos reassigned so no slot matches Windsor | Done |
| New brand: warm rust and charcoal | Done — 19 contrast pairs, all pass AA |
| Logo, favicon, app icons | Done — generated, no file was supplied |
| Contact form wired to a live endpoint | **Not done — step 1 below** |
| Deployed | **Not done — steps 3 to 5** |
| DNS moved | **Not done — step 6** |

---

## Step 1 — Google Sheet and Apps Script

Do this signed in as the Google account that should **send** the notification
emails. Apps Script sends as whoever authorises it, regardless of what
`NOTIFY_EMAIL` says.

1. Go to <https://sheets.google.com> and create a **blank spreadsheet**. Name it
   `Grimsby Spray Foam Leads`.
   - It must be a native Google Sheet. An uploaded `.xlsx` has no Extensions
     menu and Apps Script cannot read it.
2. **Extensions → Apps Script.**
3. Delete whatever is in `Code.gs`. Open `google-apps-script.gs` from this
   folder, copy all of it, paste it in.
4. `NOTIFY_EMAIL` is already set to `tiffindevelopments@gmail.com`. Change it
   only if you want a different inbox.
5. **Deploy → New deployment.** Gear icon → **Web app**.
   - Description: `Grimsby leads`
   - Execute as: **Me**
   - Who has access: **Anyone**
   - Deploy, then authorise when prompted. Google will warn about an
     unverified app — that is expected for your own script. Advanced → Go to
     project.
6. Copy the **Web app URL**. It ends in `/exec`.

Send me that URL and I will paste it in and rebuild. Or do it yourself:
open `site\script.js`, find `SHEET_ENDPOINT`, replace
`'YOUR-APPS-SCRIPT-EXEC-URL'` with the `/exec` URL, save, then **rerun
`python build.py`**. The rebuild is not optional — the cache fingerprint has to
change or nobody's browser will pick up the new file.

> Any later edit to the `.gs` file needs **Deploy → Manage deployments → edit →
> Version: New version → Deploy.** Saving alone leaves the live site on old code.

---

## Step 2 — Look at the site before it goes anywhere

In File Explorer, open:

```
C:\Users\Lenovo\Documents\Tiffin Developments Lead Generation\Spray Foam Content\Grimsby Spray Foam Insulation\site\index.html
```

Double-click it. It opens in your browser from disk — no server needed.

Click through the nav to every page. What I could not check myself is how it
*looks*, so this is the part I need your eyes on. Send me a screenshot if
anything is off, and batch the feedback into one list rather than one item at
a time — each round is a rebuild.

---

## Step 3 — Git repository

In PowerShell, one line at a time:

```powershell
cd "C:\Users\Lenovo\Documents\Tiffin Developments Lead Generation\Spray Foam Content\Grimsby Spray Foam Insulation"
git init
git add .
git commit -m "Grimsby Spray Foam Insulation - migrated from SitePanda"
git branch -M main
```

Then create an empty repo at <https://github.com/new> named
`grimsby-spray-foam`. Set it to **Private**. **No README, no .gitignore, no
licence** — it must be empty.

Private matters here: `build.py` and `google-apps-script.gs` both carry
`tiffindevelopments@gmail.com`, and there is no upside to publishing it.
Cloudflare connects to private repos without any extra setup.

`git add .` picks up everything that needs to go — including the master `*.png`
photos, which `.gitignore` tracks **on purpose** because `build.py --images`
regenerates `site/images/` from them, and including `site/` itself, which is
the directory Cloudflare actually serves. Nothing needs adding by hand.

```powershell
git remote add origin https://github.com/dallastiffin/grimsby-spray-foam.git
git push -u origin main
```

You should see it count objects and finish with `main -> main`.

> If Cloudflare later fails at "Cloning repository", the repo is empty — the
> push did not work. Check for a `.git` folder before debugging anything else.

---

## Step 4 — Cloudflare Worker

1. Cloudflare dashboard → **Compute (Workers)** → **Create** → **Import a
   repository**.
2. Pick `grimsby-spray-foam`.
3. Settings:
   - **Worker name:** `grimsby-spray-foam` — this must match `name` in
     `wrangler.toml` exactly or the deploy fails.
   - **Build command:** leave empty.
   - **Deploy command:** `npx wrangler deploy`
4. Deploy. You get a `*.workers.dev` URL.

---

## Step 5 — Test on the workers.dev URL, with the real site still live

This is the whole point of doing it in this order. Check on the temporary URL:

- Home page loads at the root (not a 404)
- All six service pages, About, Contact, FAQ
- `/about-us` and `/contact-us` work — those are the migrated slugs
- `/close-and-open-cell-spray-foam` works — note it is `close`, not `closed`
- Submit the contact form. Confirm a row lands in the Sheet **and** an email
  arrives.
- Open it on your phone.

Do not proceed until the form has actually delivered a test lead.

---

## Step 6 — Domain and DNS (Namecheap)

1. Cloudflare → **Add a site** → `grimsbysprayfoaminsulation.com` → Free plan.
2. Cloudflare scans the existing DNS. **Check the imported records before
   continuing.**
   - **Keep every MX and TXT record.** Those are email forwarding and domain
     verification. Losing them kills your email.
   - **Delete any leftover Namecheap parking A record** (usually `192.64.x.x`).
   - Delete the A/CNAME records pointing at SitePanda.
3. Cloudflare gives you two nameservers. In Namecheap: **Domain List → Manage →
   Nameservers → Custom DNS**, paste both, save.
4. Back in the Worker → **Settings → Domains & Routes → Add custom domain**.
   Add **`www.grimsbysprayfoaminsulation.com`**.
   - www is the canonical host. `DOMAIN` in `build.py` is set to the www form,
     and it feeds every canonical tag, Open Graph URL, the sitemap and the
     schema. Do not add the apex as the primary.
5. Add the apex `grimsbysprayfoaminsulation.com` as well, then create a
   **Redirect Rule**: apex → `https://www.grimsbysprayfoaminsulation.com/$1`,
   301 permanent, preserving the path.

Nameserver propagation is usually under an hour but can take up to 24.

---

## Step 7 — After the domain resolves

1. Visit all ten original URLs on the live domain. Every one should load its
   own page, not a redirect and not a 404:

   ```
   /                                   /crawl-space-insulation
   /services                           /new-construction-insulation
   /attic-insulation                   /close-and-open-cell-spray-foam
   /garage-insulation                  /about-us
   /basement-insulation                /contact-us
   ```

2. Google Search Console → add the property if it is not there → submit
   `https://www.grimsbysprayfoaminsulation.com/sitemap.xml`.
3. Update the website link on the Google Business Profile if it points at a
   SitePanda URL rather than the domain.
4. Submit a real enquiry through the form on the live site.

**Only now cancel SitePanda.** Export anything you want to keep from it first
— once it is gone, the `lirp.cdn-website.com` image URLs die with it. That does
not affect this site, since every image is self-hosted, but any other place you
pasted those URLs will break.

---

## Things that will bite you if you forget them

- **Rerun `python build.py` after editing `style.css` or `script.js`.** The
  HTML carries a content hash of each. Skip the rebuild and your change reaches
  nobody who has already visited.
- **`html_handling` in `wrangler.toml` must stay `auto-trailing-slash`.** Set
  it to `none` and `/` stops mapping to `index.html` and the home page 404s.
- **Never hand-edit anything in `site/`** except `style.css` and `script.js`.
  Everything else is regenerated from the markdown.
- **Do not use `Caledon Storefront.png`.** It is a photograph of another
  company's premises. It came with the shared photo pool.
- **Do not cross-link this site to the Windsor, Chatham or epoxy sites.**

---

## Two things to fix on your other sites

Found while building this one:

1. **`--color-accent-dark` is broken on Windsor and Chatham.** A malformed
   comment in `style.css` closes early, and CSS error recovery swallows the
   next declaration. The token is referenced 10 times and never defined, so
   every hover state built on it computes to nothing. Verified with a CSS
   parser. The fix is in this folder's `style.css` if you want it copied over.

2. **The old Grimsby SitePanda site had CTA buttons dialling the wrong
   number** — displayed `(289) 672-4160`, linked `tel:2262426614`, on the home
   page hero, the garage page and both contact page buttons. Worth checking
   whether the same mistake exists on your other city sites.

---

## Open items

- Business hours are not published anywhere, so `HOURS_TEXT` in `build.py` is
  the template default (Mon–Sat, 7am–6pm). Tell me the real hours and I will
  correct the schema.
- `STREET_ADDRESS` and `POSTAL_CODE` in `build.py` are still `PLACEHOLDER`.
  That is fine for a service-area business with no storefront, but if you have
  a business address you want indexed, it should go in.
- The pricing figures in the FAQ are 2026 Ontario market ranges from research,
  not your prices. Swap in your own numbers when you can.
- The Home Renovation Savings Program details are current as of August 2026 and
  the program runs to November 2026. Worth a diary note to revisit.
