# -*- coding: utf-8 -*-
"""Line-level view: for each markdown line, how many of its words sit inside a
6-gram shared with the comparison sites. Rewriting works on lines, not on
lowercased fragments."""
import sys, os, glob
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from audit import paras_of, words
SKIP={"privacy-policy.html","terms.html","404.html"}
def grams(site):
    out=set()
    for p in glob.glob(os.path.join(site,"*.html")):
        if os.path.basename(p) in SKIP: continue
        for para in paras_of(open(p,encoding="utf-8").read()):
            w=words(para)
            for i in range(len(w)-5): out.add(" ".join(w[i:i+6]))
    return out
md=sys.argv[1]; theirs=set()
for d in sys.argv[2:]: theirs|=grams(d)
rows=[]
for ln,line in enumerate(open(md,encoding="utf-8"),1):
    s=line.rstrip("\n")
    if not s.strip(): continue
    w=words(s)
    if len(w)<6: continue
    mark=[False]*len(w)
    for i in range(len(w)-5):
        if " ".join(w[i:i+6]) in theirs:
            for j in range(i,i+6): mark[j]=True
    h=sum(mark)
    if h: rows.append((h,ln,s))
rows.sort(key=lambda r:-r[0])
print("%d lines carry shared words; %d shared words total\n"%(len(rows),sum(r[0] for r in rows)))
for h,ln,s in rows:
    print("L%-5d %3dw  %s"%(ln,h,s[:200]))
