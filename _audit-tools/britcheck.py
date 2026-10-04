# -*- coding: utf-8 -*-
"""North American English check. The owner reads this copy as a Paris, Ontario
homeowner would; British register reads as imported and, in one case ('kerb'),
as a spelling mistake. Run on the markdown, not the build, so a hit points at a
line you can edit."""
import sys, re
BRIT = {
 r"\bkerbs?\b":"curb", r"\bpavements?\b":"sidewalk", r"\bautumn\b":"fall",
 r"\bgardens?\b(?! Avenue| Street| Road| Lane)":"yard",
 r"\bring (?:us|me|\(|the|on)\b":"call", r"\bRing (?:us|me|\(|the|on)\b":"Call",
 r"\bwhilst\b":"while", r"\bamongst\b":"among", r"\bstorey(s)?\b":"story",
 r"\btyres?\b":"tire", r"\bboot of\b":"trunk of",
 r"\bpetrol\b":"gas", r"\blorry|lorries\b":"truck", r"\bironmongery\b":"hardware",
 r"\bfortnight\b":"two weeks", r"\bpost code\b":"postal code",
 r"\bcar park\b":"parking lot", r"\bhire\b":"rent", r"\bgarden(er|ing)\b":"yard",
 r"\bspecialis(e|ed|ing|ation)\b":"specialize", r"\bstabilis(e|ed|ing)\b":"stabilize",
 r"\brecognis(e|ed|ing)\b":"recognize", r"\borganis(e|ed|ing)\b":"organize",
 r"\bapologis(e|ed|ing)\b":"apologize", r"\banalys(e|ed|ing)\b":"analyze",
 r"\bpractis(e|ed|ing)\b":"practice", r"\bmanoeuvr":"maneuver",
 r"\benquir(e|y|ies|ing)\b":"inquiry",
 r"\bmum\b":"mom", r"\bqueue\b":"line",
 r"\bmotorway\b":"highway", r"\bverge\b":"boulevard/shoulder",
 r"\bcopse\b":"stand", r"\bcouncil\b":"municipality/township",
}
tot=0
for path in sys.argv[1:]:
    txt=open(path,encoding="utf-8").read()
    lines=txt.split("\n")
    for pat,fix in BRIT.items():
        for i,l in enumerate(lines,1):
            for m in re.finditer(pat,l,re.I):
                tot+=1
                print("%-14s L%-5d %-22s -> %-18s  %s"%(path.split('/')[-1][:14],i,m.group(0),fix,l[:90]))
print("\n%d hits"%tot)
