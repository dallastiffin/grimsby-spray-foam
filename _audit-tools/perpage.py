import sys, os, glob
sys.path.insert(0,"/root/tt/build")
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
mine=sys.argv[1]; theirs=set()
for d in sys.argv[2:]: theirs|=grams(d)
T=H=0; rows=[]
for p in sorted(glob.glob(os.path.join(mine,"*.html"))):
    if os.path.basename(p) in SKIP: continue
    t=h=0
    for para in paras_of(open(p,encoding="utf-8").read()):
        w=words(para); t+=len(w); mark=[False]*len(w)
        for i in range(len(w)-5):
            if " ".join(w[i:i+6]) in theirs:
                for j in range(i,i+6): mark[j]=True
        h+=sum(mark)
    T+=t; H+=h
    rows.append((100.0*h/max(t,1), h, t, os.path.basename(p)))
for pc,h,t,n in sorted(rows, reverse=True):
    print("%6.2f%%  %4d/%-5d %s" % (pc,h,t,n))
print("\nTOTAL %.2f%%  (%d/%d)" % (100.0*H/max(T,1),H,T))
