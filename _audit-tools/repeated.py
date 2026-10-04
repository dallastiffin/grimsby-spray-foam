# -*- coding: utf-8 -*-
"""List shared runs by how many PAGES carry them. A run on twelve pages is a
site-wide block (a CTA, a form intro, a service-card excerpt) and one edit to
its source fixes twelve pages; a run on one page is worth one edit. Sorting by
page count puts the cheap wins first."""
import sys, os, glob, collections
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from audit import paras_of, words
def grams(site):
    out=set()
    for p in glob.glob(os.path.join(site,"*.html")):
        if os.path.basename(p) in ("privacy-policy.html","terms.html","404.html"): continue
        for para in paras_of(open(p,encoding="utf-8").read()):
            w=words(para)
            for i in range(len(w)-5): out.add(" ".join(w[i:i+6]))
    return out
mine=sys.argv[1]; theirs=set()
for d in sys.argv[2:]: theirs |= grams(d)
runs=collections.Counter()
for p in glob.glob(os.path.join(mine,"*.html")):
    if os.path.basename(p) in ("privacy-policy.html","terms.html","404.html"): continue
    for para in paras_of(open(p,encoding="utf-8").read()):
        w=words(para); mark=[False]*len(w)
        for i in range(len(w)-5):
            if " ".join(w[i:i+6]) in theirs:
                for j in range(i,i+6): mark[j]=True
        i=0
        while i<len(mark):
            if mark[i]:
                j=i
                while j<len(mark) and mark[j]: j+=1
                runs[" ".join(w[i:j])]+=1; i=j
            else: i+=1
for r,c in sorted(runs.items(), key=lambda kv:(-kv[1]*len(kv[0].split()), -len(kv[0].split())))[:60]:
    print("x%-3d %3dw  %s" % (c, len(r.split()), r[:130]))
