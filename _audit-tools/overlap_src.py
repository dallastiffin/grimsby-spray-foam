# -*- coding: utf-8 -*-
"""Map every shared run back to the SENTENCE in the markdown that produced it,
so a rewrite pass can work from source text rather than from lowercased,
punctuation-stripped fragments."""
import sys, os, glob, re
sys.path.insert(0, os.path.expanduser("~/tt/build"))
from audit import paras_of, words

def grams(site):
    out = set()
    for p in glob.glob(os.path.join(site, "*.html")):
        if os.path.basename(p) in ("privacy-policy.html","terms.html","404.html"): continue
        for para in paras_of(open(p, encoding="utf-8").read()):
            w = words(para)
            for i in range(len(w)-5): out.add(" ".join(w[i:i+6]))
    return out

mine_site, md = sys.argv[1], sys.argv[2]
theirs = set()
for d in sys.argv[3:]: theirs |= grams(d)

runs = {}
for p in glob.glob(os.path.join(mine_site, "*.html")):
    if os.path.basename(p) in ("privacy-policy.html","terms.html","404.html"): continue
    for para in paras_of(open(p, encoding="utf-8").read()):
        w = words(para)
        mark = [False]*len(w)
        for i in range(len(w)-5):
            if " ".join(w[i:i+6]) in theirs:
                for j in range(i, i+6): mark[j] = True
        i = 0
        while i < len(mark):
            if mark[i]:
                j = i
                while j < len(mark) and mark[j]: j += 1
                if j-i >= 6: runs[" ".join(w[i:j])] = j-i
                i = j
            else: i += 1

# find the source sentence in the markdown for each run
src = open(md, encoding="utf-8").read()
sentences = re.split(r'(?<=[.?!])\s+', src)
norm = lambda t: " ".join(words(t))
out = []
seen = set()
for run, ln in sorted(runs.items(), key=lambda kv: -kv[1]):
    key = run[:40]
    for sent in sentences:
        n = norm(sent)
        if run in n and sent.strip() not in seen and len(sent.strip()) > 30:
            seen.add(sent.strip())
            out.append((ln, sent.strip().replace("\n", " ")))
            break
print("%d distinct source sentences carry a shared run of 8+ words\n" % len(out))
for ln, sent in out:
    print("[%2d] %s" % (ln, sent[:250]))
    print()
