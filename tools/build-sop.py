# -*- coding: utf-8 -*-
"""Printable SOP for launching a new city site."""
from reportlab.lib.pagesizes import letter
from reportlab.lib.units import mm
from reportlab.lib import colors
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.enums import TA_LEFT
from reportlab.platypus import (SimpleDocTemplate, Paragraph, Spacer, Table,
                                TableStyle, PageBreak, KeepTogether, ListFlowable,
                                ListItem, HRFlowable)

GREEN = colors.HexColor("#0B4D25")
GREEN_D = colors.HexColor("#07351A")
ORANGE = colors.HexColor("#C24C0C")
GREY = colors.HexColor("#5F605F")
LIGHT = colors.HexColor("#F1F4F1")
BORDER = colors.HexColor("#CBD5CB")
INK = colors.HexColor("#10241A")

OUT = "/tmp/sop/New-City-Site-SOP.pdf"

ss = getSampleStyleSheet()
def S(name, **kw):
    base = dict(fontName="Helvetica", fontSize=9.5, leading=13.5,
                textColor=INK, alignment=TA_LEFT, spaceAfter=5)
    base.update(kw)
    return ParagraphStyle(name, **base)

st = {
 "title":    S("title", fontName="Helvetica-Bold", fontSize=22, leading=25,
               textColor=GREEN, spaceAfter=3),
 "sub":      S("sub", fontSize=10.5, leading=14, textColor=GREY, spaceAfter=14),
 "h1":       S("h1", fontName="Helvetica-Bold", fontSize=13.5, leading=17,
               textColor=colors.white, spaceBefore=2, spaceAfter=2),
 "h2":       S("h2", fontName="Helvetica-Bold", fontSize=11, leading=14,
               textColor=GREEN, spaceBefore=10, spaceAfter=4),
 "body":     S("body"),
 "small":    S("small", fontSize=8.5, leading=11.5, textColor=GREY),
 "cmd":      S("cmd", fontName="Courier-Bold", fontSize=8.8, leading=12,
               textColor=GREEN_D, spaceAfter=0),
 "cmdc":     S("cmdc", fontName="Courier", fontSize=8.3, leading=11,
               textColor=INK, spaceAfter=0),
 "warn":     S("warn", fontSize=9, leading=12.5, textColor=colors.HexColor("#8A2B00")),
 "cell":     S("cell", fontSize=8.6, leading=11.5),
 "cellb":    S("cellb", fontName="Helvetica-Bold", fontSize=8.6, leading=11.5),
 "check":    S("check", fontSize=9.3, leading=14),
}

def band(text, n=None):
    """Section header bar."""
    label = ("STEP %s   " % n if n else "") + text
    t = Table([[Paragraph(label, st["h1"])]], colWidths=[170*mm])
    t.setStyle(TableStyle([
        ("BACKGROUND", (0,0), (-1,-1), GREEN),
        ("LEFTPADDING", (0,0), (-1,-1), 8), ("RIGHTPADDING", (0,0), (-1,-1), 8),
        ("TOPPADDING", (0,0), (-1,-1), 5), ("BOTTOMPADDING", (0,0), (-1,-1), 5),
    ]))
    return [Spacer(1, 9), t, Spacer(1, 7)]

def cmd(lines, where="PowerShell"):
    rows = [[Paragraph(where.upper(), st["small"])]]
    for l in lines:
        rows.append([Paragraph(l.replace("&","&amp;").replace("<","&lt;"), st["cmd"])])
    t = Table(rows, colWidths=[170*mm])
    t.setStyle(TableStyle([
        ("BACKGROUND", (0,0), (-1,-1), LIGHT),
        ("BOX", (0,0), (-1,-1), 0.6, BORDER),
        ("LINEBELOW", (0,0), (0,0), 0.4, BORDER),
        ("LEFTPADDING", (0,0), (-1,-1), 8), ("RIGHTPADDING", (0,0), (-1,-1), 8),
        ("TOPPADDING", (0,0), (-1,-1), 3), ("BOTTOMPADDING", (0,0), (-1,-1), 3),
    ]))
    return [t, Spacer(1, 6)]

def note(text, kind="note"):
    col = colors.HexColor("#FDF1E9") if kind=="warn" else LIGHT
    edge = ORANGE if kind=="warn" else GREEN
    label = "WATCH OUT" if kind=="warn" else "NOTE"
    t = Table([[Paragraph("<b>%s</b>  %s" % (label, text), st["warn" if kind=="warn" else "body"])]],
              colWidths=[170*mm])
    t.setStyle(TableStyle([
        ("BACKGROUND", (0,0), (-1,-1), col),
        ("LINEBEFORE", (0,0), (0,-1), 2.5, edge),
        ("LEFTPADDING", (0,0), (-1,-1), 8), ("RIGHTPADDING", (0,0), (-1,-1), 8),
        ("TOPPADDING", (0,0), (-1,-1), 5), ("BOTTOMPADDING", (0,0), (-1,-1), 5),
    ]))
    return [t, Spacer(1, 6)]

def _box():
    """Empty square drawn with a border. The Unicode ballot-box glyph is absent
    from the built-in fonts and renders as a solid black block."""
    b = Table([[""]], colWidths=[3.4*mm], rowHeights=[3.4*mm])
    b.setStyle(TableStyle([("BOX", (0,0), (-1,-1), 0.7, GREY),
                           ("LEFTPADDING",(0,0),(-1,-1),0),
                           ("RIGHTPADDING",(0,0),(-1,-1),0),
                           ("TOPPADDING",(0,0),(-1,-1),0),
                           ("BOTTOMPADDING",(0,0),(-1,-1),0)]))
    return b


def checklist(items):
    rows = [[_box(), Paragraph(i, st["check"])] for i in items]
    t = Table(rows, colWidths=[7*mm, 163*mm])
    t.setStyle(TableStyle([
        ("VALIGN", (0,0), (-1,-1), "TOP"),
        ("TOPPADDING", (0,0), (0,-1), 3),
        ("LEFTPADDING", (0,0), (-1,-1), 0), ("RIGHTPADDING", (0,0), (-1,-1), 2),
        ("TOPPADDING", (0,0), (-1,-1), 1.5), ("BOTTOMPADDING", (0,0), (-1,-1), 1.5),
    ]))
    return [t, Spacer(1, 5)]

def table(header, rows, widths):
    hdr = ParagraphStyle("hdr", parent=st["cellb"], textColor=colors.white)
    data = [[Paragraph(h, hdr) for h in header]]
    for r in rows:
        data.append([Paragraph(str(c), st["cell"]) for c in r])
    t = Table(data, colWidths=widths, repeatRows=1)
    t.setStyle(TableStyle([
        ("BACKGROUND", (0,0), (-1,0), GREEN),
        ("TEXTCOLOR", (0,0), (-1,0), colors.white),
        ("GRID", (0,0), (-1,-1), 0.4, BORDER),
        ("VALIGN", (0,0), (-1,-1), "TOP"),
        ("ROWBACKGROUNDS", (0,1), (-1,-1), [colors.white, LIGHT]),
        ("LEFTPADDING", (0,0), (-1,-1), 5), ("RIGHTPADDING", (0,0), (-1,-1), 5),
        ("TOPPADDING", (0,0), (-1,-1), 4), ("BOTTOMPADDING", (0,0), (-1,-1), 4),
    ]))
    return [t, Spacer(1, 7)]

def P(text): return Paragraph(text, st["body"])
def H2(text): return Paragraph(text, st["h2"])

def footer(canvas, doc):
    canvas.saveState()
    canvas.setStrokeColor(BORDER); canvas.setLineWidth(0.5)
    canvas.line(20*mm, 14*mm, 190*mm, 14*mm)
    canvas.setFont("Helvetica", 7.5); canvas.setFillColor(GREY)
    canvas.drawString(20*mm, 9.5*mm, "New City Site — Standard Operating Procedure")
    canvas.drawRightString(190*mm, 9.5*mm, "Page %d" % doc.page)
    canvas.restoreState()

story = []

# ---------------------------------------------------------------- cover
story.append(Paragraph("Launching a New City Website", st["title"]))
story.append(Paragraph("Standard operating procedure &nbsp;•&nbsp; Tiffin Developments &nbsp;•&nbsp; local trade sites",
                       st["sub"]))
story.append(HRFlowable(width="100%", thickness=2, color=GREEN, spaceAfter=10))

story.append(P("Every city site is built from one template rather than from scratch. The template lives in the "
   "<b>Grimsby Epoxy Flooring</b> folder. A Python script generates all 14 pages from a single markdown "
   "file, so the only things that change per city are the copy, the photos and a short config block."))
story.append(Spacer(1, 4))
story.append(P("<b>Your time: roughly 35 minutes</b> of actual work, spread across the steps below, plus a DNS wait "
   "that can be anywhere from 10 minutes to a few hours. Claude does the writing and the code."))

story += note("Work through this in order. Steps 6 to 9 each depend on the one before, and step 9 cannot start "
              "until the domain is registered.")

story.append(H2("What you need before you start"))
story += checklist([
  "City name, and the list of towns to name as the service area",
  "Domain registered at Namecheap — <b>do this first</b>, the DNS wait is the long pole",
  "A phone number for that city (separate numbers per city are better for local search)",
  "Decision on photos: new ones for this city, or reuse the existing set",
  "A logo, or reuse the existing one",
])

story.append(H2("The five things that change per city"))
story += table(["What", "Where"], [
  ["City, phone, domain, region, service area", "CONFIG block at the top of build.py — the scaffolder writes this for you"],
  ["All page copy", "the markdown content file"],
  ["Photos, and their alt text", "project root folder, plus the two photo tables in build.py"],
  ["Logo", "Logo.png, then run tools/make-logo.py"],
  ["Lead destination", "SHEET_ENDPOINT in site/script.js"],
], [58*mm, 112*mm])

story.append(Paragraph("Everything else — layout, SEO, schema, forms, gallery, accessibility, caching, "
    "Cloudflare config — carries over untouched and does not need looking at.", st["small"]))

story.append(PageBreak())

# ---------------------------------------------------------------- 1
story += band("Start a new Claude project", 1)
story.append(P("Open a new project in Claude Cowork. Connect it to the <b>parent</b> folder, not a city folder:"))
story += cmd(["C:\\Users\\Lenovo\\Documents\\Tiffin Developments Lead Generation\\Epoxy Flooring Content"],
             "Folder to connect")
story += note("If you connect only the new city's folder, Claude cannot read the Grimsby template and the process "
              "will not work. The parent folder gives access to the template and every city.", "warn")
story.append(P("Then send this as your first message, filling in the blanks:"))
story += cmd([
  "/new-city-trade-site",
  "",
  "City: ______________, Ontario",
  "Region: ______________",
  "Business: ______________ Epoxy Floors",
  "Phone: +1 ___-___-____",
  "Domain: https://______________.com",
  "Service area: ______________________________________",
  "Photos: reusing the existing set  /  new ones are in the folder",
], "Paste into Claude")

# ---------------------------------------------------------------- 2
story += band("Scaffold the project folder", 2)
story.append(P("In PowerShell, from the Grimsby folder:"))
story += cmd([
  'cd "C:\\Users\\Lenovo\\Documents\\Tiffin Developments Lead Generation\\Epoxy Flooring Content\\Grimsby Epoxy Flooring"',
  "python tools/new-city.py",
])
story.append(P("Answer the prompts. Press Enter to accept anything shown in brackets. It asks whether to reuse the "
   "existing photos — answer <b>y</b> unless you have new ones."))
story.append(P("It creates a sibling folder with the config, Worker name and web manifest already rewritten, and "
   "the previous city's form endpoint cleared. Paste the output back to Claude."))
story.append(Paragraph("Get latitude and longitude from Google Maps: right-click the city centre and the first menu "
   "item is the coordinates. Leave blank if you don't have them.", st["small"]))

# ---------------------------------------------------------------- 3
story += band("Claude writes the copy", 3)
story.append(P("Claude produces roughly 7,900 words across 12 blocks and saves it into the content file the "
   "scaffolder created. This is the part that determines whether the site ranks, so it gets real effort."))
story.append(H2("What to check before moving on"))
story += checklist([
  "The wording is genuinely different from other cities, not the same text with the city name swapped",
  "Local detail is actually true for this city — roads, geography, climate, nearby towns",
  "Section order and FAQ questions differ from the other sites",
  "The service area list matches what you actually cover",
])
story += note("Ask Claude: <i>“what percentage of the rendered text comes from this city's markdown, and does any "
              "sentence appear on a site we already launched?”</i> It can measure both.")

# ---------------------------------------------------------------- 4
story += band("Photos and logo", 4)
story.append(P("Reusing the same photos and logo? Skip to step 5."))
story.append(P("Otherwise put the photos in the project root, tell Claude the filenames, and it will update the two "
   "photo tables. Replace Logo.png if the logo is different."))
story += note("Check every photo for another company's logo, watermark or branding before using it. This has "
              "already happened once — a competitor's name on a crew shirt reached a live page.", "warn")
story.append(Paragraph("Different photos per city is the single strongest way to keep the sites distinct. Identical "
   "imagery across domains is easier to spot than identical wording.", st["small"]))

# ---------------------------------------------------------------- 5
story += band("Build the site", 5)
story += cmd([
  'cd "C:\\...\\Epoxy Flooring Content\\[NEW CITY] Epoxy Flooring"',
  "python tools/make-logo.py",
  "python build.py --images",
])
story.append(P("<b>--images</b> re-exports every photo and is slow. After the first run, plain "
   "<font face='Courier'>python build.py</font> is enough — use that whenever copy, CSS or JavaScript changes."))
story += note("Always run build.py after editing CSS or JavaScript. It refreshes the cache fingerprint; without it, "
              "visitors keep the old file and your changes appear not to work.", "warn")

# ---------------------------------------------------------------- 6
story += band("Set up the Google Sheet for leads", 6)
story.append(P("One sheet per city, so leads never mix."))
story += checklist([
  "Go to <b>sheets.new</b> — this must be a native Google Sheet, never an uploaded Excel file",
  "Name it <i>[City] Epoxy Floors — Leads</i>",
  "<b>Extensions → Apps Script</b>. Delete the placeholder code",
  "Paste in the whole of <i>google-apps-script.gs</i> from the project folder",
  "Set NOTIFY_EMAIL to the address that should receive alerts, then save",
  "Choose <b>testWrite</b> from the function dropdown and click <b>Run</b>",
  "Approve the permissions prompt: Advanced → Go to (project) → Allow",
  "Check the sheet: a <b>Leads</b> tab with a header row and one test row. Delete the test row",
  "<b>Deploy → New deployment</b>, gear icon → <b>Web app</b>",
  "Execute as <b>Me</b>, Who has access <b>Anyone</b>, then <b>Deploy</b>",
  "Copy the URL ending in <b>/exec</b> and give it to Claude to paste into script.js",
  "Run <font face='Courier'>python build.py</font> again",
])
story += note("If there is no Extensions menu, the file is an uploaded .xlsx. Apps Script cannot read those at all. "
              "Start again at sheets.new.", "warn")
story.append(Paragraph("After any later edit to the Apps Script, you must redeploy: Deploy → Manage deployments → "
   "pencil → Version: New version → Deploy. Saving alone changes nothing.", st["small"]))

# ---------------------------------------------------------------- 7
story += band("Push to GitHub", 7)
story += cmd([
  "git init",
  "git add -A",
  'git commit -m "Initial site"',
])
story.append(P("Create an empty repository on GitHub named after the city, then:"))
story += cmd([
  "git remote add origin https://github.com/dallastiffin/[REPO-NAME].git",
  "git branch -M main",
  "git push -u origin main",
])
story.append(Paragraph("A browser window opens for GitHub sign-in the first time. Credentials are saved afterwards.",
   st["small"]))

story.append(PageBreak())

# ---------------------------------------------------------------- 8
story += band("Deploy on Cloudflare", 8)
story.append(P("Dashboard → <b>Workers &amp; Pages</b> → <b>Create application</b> → "
   "<b>Import a repository</b> → pick the new repo. Then:"))
story += table(["Field", "Value"], [
  ["Worker name", "<b>must exactly match the</b> name <b>line in wrangler.toml</b>"],
  ["Build command", "leave completely empty"],
  ["Deploy command", "npx wrangler deploy"],
  ["Root directory", "/"],
], [45*mm, 125*mm])
story += note("A Worker name that does not match wrangler.toml is the most common reason the deploy fails. The "
              "scaffolder printed the correct name — use it exactly.", "warn")
story.append(P("The build command stays empty on purpose: the HTML is already generated and committed, so there is "
   "nothing to compile. Click <b>Save and Deploy</b>. You get a workers.dev URL in a minute or two, and every "
   "later push redeploys automatically."))

# ---------------------------------------------------------------- 9
story += band("Connect the domain", 9)
story += checklist([
  "Cloudflare → <b>Add a domain</b> → enter it → choose the <b>Free</b> plan",
  "Copy the two nameservers Cloudflare shows you",
  "Namecheap → <b>Domain List</b> → <b>Manage</b> → Nameservers → <b>Custom DNS</b>",
  "Paste both nameservers, then <b>click the green checkmark to save</b>",
  "Wait for Cloudflare to email that the domain is Active",
  "<b>DNS → Records:</b> delete any leftover A record pointing at 192.64.x.x",
  "Worker → <b>Settings → Domains &amp; Routes → Add → Custom domain</b>. Add the bare domain and the www version",
  "Pick one as canonical. <b>Rules → Redirect Rules</b>: hostname equals the other one, dynamic redirect, 301",
  "Confirm DOMAIN in build.py matches the canonical hostname exactly, then rebuild and push",
])
story += note("Do not delete the MX or TXT records. Those are the domain's email forwarding and SPF record. "
              "Only the parking A record goes.", "warn")

story.append(PageBreak())

# ---------------------------------------------------------------- 10
story += band("Verify before you call it done", 10)
story.append(P("Ask Claude to check the build first — links, duplicate IDs, heading structure, contrast and page "
   "weight take it seconds and catch things you will not see. Then, on the live site:"))
story += checklist([
  "Bare domain loads with a padlock",
  "The other hostname (www or not) redirects to the canonical one",
  "A deep link such as /garage-floor-coating loads with no redirect flash",
  "/nope shows the styled 404 page, not a Cloudflare error",
  "On a narrow window: hamburger menu opens, services dropdown expands, sticky call bar appears",
  "Submit a real form entry — the row appears in the Sheet and the email arrives",
  "/sitemap.xml lists the correct domain",
  "Submit the sitemap in Google Search Console",
])
story += note("Test the form on the live domain, not a preview URL. Do it before you spend anything on advertising.")

# ---------------------------------------------------------------- troubleshooting
story += band("If something goes wrong")
story += table(["Symptom", "Cause and fix"], [
  ["Site root shows the 404 page",
   "html_handling is set to \"none\" in wrangler.toml. With that value, / does not map to index.html. Use auto-trailing-slash."],
  ["Your changes do not appear",
   "Stale cache. Run python build.py to refresh the fingerprint, then hard refresh with Ctrl+F5."],
  ["Cloudflare build fails immediately",
   "Worker name does not match the name line in wrangler.toml."],
  ["DNS_PROBE_FINISHED_NXDOMAIN",
   "No DNS record exists for that hostname. The custom domain was never added to the Worker, or a parking A record is blocking it."],
  ["Certificate warning on first load",
   "The certificate is still being issued. Wait five minutes."],
  ["Form shows success but no row in the Sheet",
   "Endpoint not set, or build.py not rerun after setting it. Press F12, open Console, submit again, read the error."],
  ["Form errors but rows do arrive",
   "A CORS quirk. Set SHEET_USE_NO_CORS = true in script.js, rebuild, push."],
  ["No Extensions menu in Google Sheets",
   "The file is an uploaded .xlsx. Create a fresh sheet at sheets.new."],
  ["Favicon still shows the old icon",
   "Browsers cache favicons very aggressively. Open /favicon.ico directly, then hard refresh. Or check in a private window."],
  ["git push asks for a password",
   "GitHub no longer accepts account passwords. Install GitHub CLI and run gh auth login."],
], [52*mm, 118*mm])

# ---------------------------------------------------------------- reference
story += band("Reference")
story.append(H2("Commands you will actually use"))
story += table(["Command", "What it does"], [
  ["python tools/new-city.py", "Scaffold a new city folder from the template"],
  ["python tools/make-logo.py", "Rebuild every logo and favicon size from Logo.png"],
  ["python build.py", "Rebuild all pages. Run after any copy, CSS or JS change"],
  ["python build.py --images", "As above, plus re-export every photo. Slow, first run only"],
  ["git add -A", "Stage everything, including deletions"],
  ["git status", "See what changed before committing"],
  ["git push origin main", "Send it up. Cloudflare redeploys automatically"],
  ["ipconfig /flushdns", "Clear cached DNS after a domain change"],
], [58*mm, 112*mm])

story.append(H2("Where things live"))
story += table(["File", "Purpose"], [
  ["build.py", "Generates every page. CONFIG block at the top holds all city-specific values"],
  ["[City]-...-Website-Content.md", "All copy, in 12 blocks separated by ---"],
  ["site/", "The folder that deploys. Never hand-edit the HTML in here"],
  ["site/style.css, site/script.js", "Hand-written, never generated"],
  ["tools/new-city.py", "The scaffolder"],
  ["tools/make-logo.py", "Logo and favicon pipeline"],
  ["google-apps-script.gs", "Paste into Apps Script to receive leads"],
  ["wrangler.toml", "Cloudflare config. The name line must match the Worker name"],
  ["NEW-CITY.md", "Longer version of this document, kept with the project"],
  ["AVOIDING-DUPLICATE-SITES.md", "What must be original per city, and why"],
], [58*mm, 112*mm])

story.append(Spacer(1, 6))
story.append(Paragraph("Reviewed against the Grimsby build. If any step here stops matching what you see on screen, "
   "tell Claude and it will correct the runbook in the project folder.", st["small"]))

doc = SimpleDocTemplate(OUT, pagesize=letter,
                        leftMargin=20*mm, rightMargin=20*mm,
                        topMargin=16*mm, bottomMargin=20*mm,
                        title="New City Site - Standard Operating Procedure",
                        author="Tiffin Developments")
doc.build(story, onFirstPage=footer, onLaterPages=footer)
print("built:", OUT)
