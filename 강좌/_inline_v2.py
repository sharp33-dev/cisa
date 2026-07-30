# -*- coding: utf-8 -*-
import fitz, os, re, sys
ROOT=os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
MAP={
 "M02":("1-1 정보화법_제도_감리/1.2 감리 법 지침_V1.0_20190328_최종본.pdf","감리및사업관리/M02_감리법지침.html"),
 "M03":("1-1 정보화법_제도_감리/2. 감리 및 사업관리(25)_V1.3_2장 지침_5월 8일_최종본.pdf","감리및사업관리/M03_감리지침_2장.html"),
 "M05":("1-1 정보화법_제도_감리/3. 감리 및 사업관리(25)_V1.1_3장 감리총론.pdf","감리및사업관리/M05_감리총론_3장.html"),
 "M07":("1-2 사업관리/1. 정보시스템감리사_사업관리_V5.4_1장_4장_통합관리.pdf","감리및사업관리/M07_통합관리_1_4장.html"),
 "M08":("1-2 사업관리/1.1 사업관리 특강 및 출제 예상_V1.2_20190328_최종본.pdf","감리및사업관리/M08_사업관리특강.html"),
 "M09":("1-2 사업관리/2. 정보시스템감리사_사업관리_V5.4_5장 범위관리 6장 시간관리.pdf","감리및사업관리/M09_범위시간관리_5_6장.html"),
 "M10":("1-2 사업관리/3. 정보시스템감리사_사업관리_V5.4_7장 원가관리_8장 품질관리.pdf","감리및사업관리/M10_원가품질관리_7_8장.html"),
 "M11":("1-2 사업관리/4. 정보시스템감리사_V5.5_9장 인적자원관리_11장 위험관리.pdf","감리및사업관리/M11_인적자원위험관리.html"),
 "M12":("1-2 사업관리/5. 정보시스템감리사_V5.4_12장 조달관리_13장 이해관계자관리.pdf","감리및사업관리/M12_조달이해관계자관리.html"),
}
ITO=re.compile(r'(입력물.*산출물|산출물.*입력물|도구\s*및\s*기법)',re.S)
COVERMARK=re.compile(r'(\[Module|Module\s*0?\d|도메인|이론과\s*전략|수석감리원|기술사|PMP|시험\s*소개|시험\s*로드맵|로드맵|출제\s*빈도|출제빈도|출제분야|세부 출제 내용|합격\s*단계|강의\s*Roadmap|Overview|Contents|^목차$|Chapter\s*[IVX0-9]|Phase\s*[0-9])')
def mlines(t):
    ls=[re.sub(r"\s+"," ",x).strip() for x in t.split("\n")]
    return [x for x in ls if x and not re.fullmatch(r"[\d\s]+",x) and "감리사 합격" not in x and "itpe" not in x.lower() and "ITPE" not in x]
def is_cover(t):
    lines=mlines(t); text=" ".join(lines)
    core=re.sub(r"토픽 핵심 요약정리|출제 예상문제 & 기출 문제|기출문제|핵심 요약정리|핵심 정리","",text).strip()
    if len(re.sub(r"\s","",core))<5: return True
    if COVERMARK.search(text): return True
    if "토픽 핵심 요약정리" in text or "핵심 요약정리" in text:
        resid=re.sub(r"토픽 핵심 요약정리|핵심 요약정리","",text)
        resid=re.sub(r"\[?시행[^\]]*\]?|\d{4}[.\-]\s*\d{1,2}[.\-]?\s*\d{0,2}|제정|개정|최종본|V\d"," "+"",resid)
        if len(re.sub(r"\s","",resid))<24: return True
    return False
def flagged(d):
    out=[]
    for i in range(d.page_count):
        t=d[i].get_text(); clean=re.sub(r'감리사 합격을 위한 사업관리 총정리|\s','',t); imgs=len(d[i].get_images())
        f=(len(clean)<90 and imgs>=1) or ITO.search(t) or (imgs>=4 and len(clean)<500)
        if f and not is_cover(t): out.append(i+1)
    return out
def sec_core(h2):
    x=re.sub(r'<[^>]+>','',h2); x=re.sub(r'^\s*〔[^〕]*〕\s*','',x); x=re.sub(r'^\s*\d+\.\s*','',x)
    x=re.sub(r'[★]|\([^)]*\)|–.*$|-\s.*$|·.*$','',x).strip()
    return x
def keywords(core):
    # 공백 제거 핵심어 + 2어절 토큰
    kw=[core.replace(' ','')]
    for w in core.split():
        if len(w)>=2: kw.append(w)
    return [k for k in kw if len(k)>=2]
def title_of(d,i):
    return " ".join(mlines(d[i].get_text()))[:80]
def anchors(d, secs):
    # secs: [(sid, core)] 순서대로. 각 섹션의 앵커 PDF 페이지(단조 증가)
    res=[]; prev=0
    for sid,core in secs:
        kws=keywords(core); found=None
        for i in range(prev, d.page_count):
            title=re.sub(r'\s','',title_of(d,i))
            body=re.sub(r'\s','',d[i].get_text()[:400])
            if any(k in title for k in kws) or (kws and kws[0] in body):
                found=i; break
        if found is None: found=prev
        res.append((sid,found)); prev=found
    return res
def run(code):
    pdf,htmlrel=MAP[code]; hp=os.path.abspath(htmlrel); d=fitz.open(os.path.join(ROOT,pdf))
    s=open(hp,encoding="utf-8").read()
    s=re.sub(r'\n*<section id="origslides".*?</section>\n*','\n',s,flags=re.S)
    s=re.sub(r'\n*<li data-os="1"[^>]*>.*?</li>','',s,flags=re.S)
    s=re.sub(r'\s*<div class="origpg-wrap"[^>]*>.*?</div>\s*(?=</section>)','',s,flags=re.S)
    s=re.sub(r'\s*<figure class="origpg"[^>]*>.*?</figure>','',s,flags=re.S)
    # 섹션(순서) + h2
    sm=[(m.group(1), sec_core(re.search(r'<h2>(.*?)</h2>',m.group(2),re.S).group(1)), m.start(), m.end())
        for m in re.finditer(r'<section id="([^"]+)"[^>]*>(.*?)</section>', s, re.S)
        if m.group(1) not in ('allquiz','origslides') and re.search(r'<h2>',m.group(2))]
    order=[(sid,core) for sid,core,a,b in sm]
    anc=anchors(d, order)   # [(sid, pageidx0)]
    # 큐레이션 fig 페이지(중복 제거용)
    curated=set(int(x) for x in re.findall(r'assets/M\d+fig/p(\d+)\.jpg', s))
    slug="assets/%sslides"%code; absdir=os.path.join(os.path.dirname(hp),slug)
    pages=[p for p in flagged(d) if os.path.exists(os.path.join(absdir,"p%03d.jpg"%p)) and p not in curated]
    # 페이지 → 섹션: 앵커 이하 최대값
    assign={}
    for p in pages:
        best=order[0][0]
        for sid,pi in anc:
            if pi < p: best=sid   # pi는 0-index, p는 1-index → pi< p 이면 그 섹션 시작 이후
        assign.setdefault(best,[]).append(p)
    def block(ps):
        figs="".join('<figure class="origpg" style="margin:14px 0;"><img loading="lazy" src="%s/p%03d.jpg" alt="원본 p.%d" style="width:100%%;border:1px solid var(--border-color);border-radius:5px;box-shadow:0 2px 6px rgba(0,0,0,0.06);"><figcaption style="font-size:0.8rem;color:#64748b;margin-top:4px;">📄 원본 슬라이드 p.%d (추출 곤란 도표·ITO)</figcaption></figure>'%(slug,p,p,p) for p in ps)
        return '\n      <div class="origpg-wrap" style="margin-top:16px;">'+figs+'</div>\n    '
    for sid in list(assign.keys()):
        pat=re.compile(r'(<section id="'+re.escape(sid)+r'"[^>]*>.*?)(</section>)', re.S)
        m=pat.search(s)
        if m: s=s[:m.end(1)]+block(sorted(assign[sid]))+s[m.end(1):]
    open(hp,"w",encoding="utf-8").write(s)
    print(f"{code}: 배치 "+str({k:sorted(v) for k,v in assign.items()}))
if __name__=="__main__":
    run(sys.argv[1])
