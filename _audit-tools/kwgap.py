import json,sys,glob,os,re
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from audit import text_of, main_of, phrase_count, words
cfg=json.load(open(sys.argv[1])); ht=cfg['head_terms']
for p in sorted(glob.glob(os.path.join(cfg['site'],'*.html'))):
    n=os.path.basename(p)
    if n in ('privacy-policy.html','terms.html','404.html'): continue
    doc=open(p,encoding='utf-8').read(); term=ht.get(n,ht['*'])
    ttl=re.search(r'<title>(.*?)</title>',doc,re.S); md=re.search(r'name="description" content="(.*?)"',doc,re.S)
    full=text_of(main_of(doc))+" "+(ttl.group(1) if ttl else "")+" "+(md.group(1) if md else "")
    W=len(words(full)); c=phrase_count(full,term); tw=len(term.split())
    print("%-44s %-32s n=%2d  %.2f%%  need +%d"%(n,term,c,100.0*c*tw/W,int(round((0.040*W-c*tw)/tw))))
