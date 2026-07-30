# -*- coding: utf-8 -*-
import fitz, os, re, sys
ROOT=os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from _inline_v2 import MAP, ITO, COVERMARK, mlines, is_cover, flagged
def lcs(a,b):
    if not a or not b: return 0
    m=[[0]*(len(b)+1) for _ in range(len(a)+1)]; best=0
    for i in range(1,len(a)+1):
        for j in range(1,len(b)+1):
            if a[i-1]==b[j-1]:
                m[i][j]=m[i-1][j-1]+1; best=max(best,m[i][j])
    return best
def ns(x): return re.sub(r'\s','',x)
def title_prefix(d,i):
    t=" ".join(mlines(d[i].get_text()))
    t=re.sub(r'^\s*\d+\.\s*','',t)         # leading "N. "
    t=re.split(r'\(|ITO|입력물|도구 및', t)[0]
    return t[:26].strip()
def h2full(body):
    m=re.search(r'<h2>(.*?)</h2>',body,re.S)
    return re.sub(r'<[^>]+>','',m.group(1)) if m else ''
def run(code):
    pdf,htmlrel=MAP[code]; hp=os.path.abspath(htmlrel); d=fitz.open(os.path.join(ROOT,pdf))
    s=open(hp,encoding="utf-8").read()
    s=re.sub(r'\n*<section id="origslides".*?</section>\n*','\n',s,flags=re.S)
    s=re.sub(r'\n*<li data-os="1"[^>]*>.*?</li>','',s,flags=re.S)
    s=re.sub(r'\s*<div class="origpg-wrap"[^>]*>.*?</div>\s*(?=</section>)','',s,flags=re.S)
    s=re.sub(r'\s*<figure class="origpg"[^>]*>.*?</figure>','',s,flags=re.S)
    secs=[(m.group(1), h2full(m.group(2))) for m in re.finditer(r'<section id="([^"]+)"[^>]*>(.*?)</section>', s, re.S)
          if m.group(1) not in ('allquiz','origslides') and re.search(r'<h2>',m.group(2))]
    order=[sid for sid,_ in secs]; h2map={sid:ns(re.sub(r'^\s*\d+\.\s*','',h)) for sid,h in secs}
    curated=set(int(x) for x in re.findall(r'assets/M\d+fig/p(\d+)\.jpg', s))
    slug="assets/%sslides"%code; absdir=os.path.join(os.path.dirname(hp),slug)
    pages=[p for p in flagged(d) if os.path.exists(os.path.join(absdir,"p%03d.jpg"%p)) and p not in curated]
    assign={}; prev=order[0]; previ=0
    for p in pages:
        tp=ns(title_prefix(d,p-1))
        sc=[(lcs(tp,h2map[sid]),i,sid) for i,sid in enumerate(order)]
        S=max(x[0] for x in sc)
        cand=[(abs(i-previ),i,sid) for s0,i,sid in sc if s0==S]  # 동점→직전과 가까운 섹션
        cand.sort(); _,bi,bsid=cand[0]
        if S<3:
            tgt=prev                       # 약한 매칭 → 문서순서상 직전 섹션
        elif bi<previ and S<6:
            tgt=prev                       # 약한 역방향 점프 차단
        else:
            tgt=bsid; previ=bi
        prev=tgt
        assign.setdefault(tgt,[]).append(p)
    def block(ps):
        figs="".join('<figure class="origpg" style="margin:14px auto;max-width:600px;text-align:center;"><img loading="lazy" src="%s/p%03d.jpg" alt="원본 p.%d" style="width:100%%;max-width:600px;display:block;margin:0 auto;border:1px solid var(--border-color);border-radius:5px;box-shadow:0 2px 6px rgba(0,0,0,0.06);"><figcaption style="font-size:0.8rem;color:#64748b;margin-top:4px;">📄 원본 슬라이드 p.%d (추출 곤란 도표·ITO)</figcaption></figure>'%(slug,p,p,p) for p in ps)
        return '\n      <div class="origpg-wrap" style="margin-top:16px;">'+figs+'</div>\n    '
    for sid in assign:
        pat=re.compile(r'(<section id="'+re.escape(sid)+r'"[^>]*>.*?)(</section>)', re.S)
        m=pat.search(s)
        if m: s=s[:m.end(1)]+block(sorted(assign[sid]))+s[m.end(1):]
    open(hp,"w",encoding="utf-8").write(s)
    print(f"{code}: "+str({k:sorted(v) for k,v in assign.items()}))
if __name__=="__main__": run(sys.argv[1])
