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
def _mlines(t):
    ls=[re.sub(r"\s+"," ",x).strip() for x in t.split("\n")]
    return [x for x in ls if x and not re.fullmatch(r"[\d\s]+",x) and "감리사 합격" not in x and "itpe" not in x.lower() and "ITPE" not in x]
def is_cover(t):
    lines=_mlines(t); text=" ".join(lines)
    core=re.sub(r"토픽 핵심 요약정리|출제 예상문제 & 기출 문제|기출문제|핵심 요약정리|핵심 정리","",text).strip()
    if len(re.sub(r"\s","",core))<5: return True          # 빈 페이지
    if COVERMARK.search(text): return True                 # 표지/구분/로드맵 마커
    # 토픽 구분 표지: '토픽 핵심 요약정리' 있고 잔여(제목·날짜·법인용 제외) 거의 없음
    if "토픽 핵심 요약정리" in text or "핵심 요약정리" in text:
        resid=re.sub(r"토픽 핵심 요약정리|핵심 요약정리","",text)
        resid=re.sub(r"\[?시행[^\]]*\]?|\d{4}[.\-]\s*\d{1,2}[.\-]?\s*\d{0,2}|제정|개정|최종본|V\d",""," "+resid)
        # 제목 1줄 정도만 남으면 표지
        if len(re.sub(r"\s","",resid))<24: return True
    return False

STOP=set("및 등 것 수 는 은 이 가 을 를 에 의 로 와 과 그 이런 또는 관한 관련 대한 대해 있다 한다 하는 위한 위해 통해".split())
def toks(t):
    t=re.sub(r'[^0-9A-Za-z가-힣\s]',' ',t)
    return set(w for w in t.split() if len(w)>=2 and w not in STOP)
def flagged(d):
    out=[]
    for i in range(d.page_count):
        t=d[i].get_text(); clean=re.sub(r'감리사 합격을 위한 사업관리 총정리|\s','',t); imgs=len(d[i].get_images())
        if (len(clean)<90 and imgs>=1) or ITO.search(t) or (imgs>=4 and len(clean)<500): out.append(i+1)
    return out
def sections(html):
    secs=[]
    for m in re.finditer(r'<section id="([^"]+)"[^>]*>(.*?)</section>', html, re.S):
        sid=m.group(1); body=m.group(2)
        if sid in ('allquiz','origslides'): continue
        txt=re.sub(r'<[^>]+>',' ',body)
        secs.append((sid, toks(txt), m.start(), m.end()))
    return secs
def run(code):
    pdf,htmlrel=MAP[code]; hp=os.path.abspath(htmlrel)
    d=fitz.open(os.path.join(ROOT,pdf))
    s=open(hp,encoding="utf-8").read()
    # 하단 모음/기존 인라인 제거
    s=re.sub(r'\n*<section id="origslides".*?</section>\n*','\n',s,flags=re.S)
    s=re.sub(r'\n*<li data-os="1"[^>]*>.*?</li>','',s,flags=re.S)
    s=re.sub(r'\s*<figure class="origpg"[^>]*>.*?</figure>','',s,flags=re.S)
    secs=sections(s)
    if not secs: print(code,"no sections"); return
    slug="assets/%sslides"%code
    absdir=os.path.join(os.path.dirname(hp),slug)
    allf=[p for p in flagged(d) if os.path.exists(os.path.join(absdir,"p%03d.jpg"%p))]
    pages=[p for p in allf if not is_cover(d[p-1].get_text())]
    covers=[p for p in allf if is_cover(d[p-1].get_text())]
    print(f'  {code} 표지제외 {len(covers)}p: {covers}')
    # 각 페이지를 최적 섹션에 배정
    assign={}
    prev_sid=secs[0][0]
    for p in pages:
        pt=toks(d[p-1].get_text())
        best=None; bscore=-1
        for sid,stoks,a,b in secs:
            sc=len(pt & stoks)
            if sc>bscore: bscore=sc; best=sid
        if bscore<=0: best=prev_sid   # 매칭 약하면 직전 섹션에 이어붙임(문서 순서상 인접)
        assign.setdefault(best,[]).append(p); prev_sid=best
    # 섹션별 이미지 HTML 만들어 </section> 앞에 삽입
    def block(ps):
        figs="".join('<figure class="origpg" style="margin:14px 0;"><img loading="lazy" src="%s/p%03d.jpg" alt="원본 p.%d" style="width:100%%;border:1px solid var(--border-color);border-radius:5px;box-shadow:0 2px 6px rgba(0,0,0,0.06);"><figcaption style="font-size:0.8rem;color:#64748b;margin-top:4px;">📄 원본 슬라이드 p.%d (도표·ITO 등 추출 곤란 원본)</figcaption></figure>'%(slug,p,p,p) for p in ps)
        return '\n      <div class="origpg-wrap" style="margin-top:16px;">'+figs+'</div>\n    '
    # 뒤에서부터 삽입(인덱스 안정)
    for sid in list(assign.keys()):
        pat=re.compile(r'(<section id="'+re.escape(sid)+r'"[^>]*>.*?)(</section>)', re.S)
        m=pat.search(s)
        if not m: continue
        s=s[:m.end(1)]+block(sorted(assign[sid]))+s[m.end(1):]
    open(hp,"w",encoding="utf-8").write(s)
    print(f"{code}: {len(pages)}p → {len(assign)}개 섹션에 인라인 배치 "+str({k:len(v) for k,v in assign.items()}))
if __name__=="__main__":
    run(sys.argv[1])
