# -*- coding: utf-8 -*-
"""For each markdown line, print the exact maximal shared spans (>=6 words)."""
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
    if not any(mark): continue
    spans=[];i=0
    while i<len(w):
        if mark[i]:
            j=i
            while j<len(w) and mark[j]: j+=1
            spans.append(" ".join(w[i:j])); i=j
        else: i+=1
    rows.append((sum(mark),ln,spans))
rows.sort(reverse=True)
for h,ln,spans in rows:
    print("L%-6d %3dw" % (ln,h))
    for sp in spans: print("        | "+sp)
print("\n%d lines, %d shared words"%(len(rows),sum(r[0] for r in rows)))
