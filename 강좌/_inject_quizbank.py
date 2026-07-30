# -*- coding: utf-8 -*-
import fitz, re, os, html
def norm(s): return re.sub(r'\s+',' ',s).strip()
HDR=re.compile(r'(감리사 합격을 위한 사업관리 총정리|출제 예상문제 & 기출 문제|출제 예상문제|기출 문제|토픽 핵심 요약정리|핵심 기출\([0-9]+\)[^\n]*|핵심 기출|해설|끝)')
CUE=['것은?','것은','무엇','고르','옳은','틀린','적절','거리가 먼','아닌 것','맞는','모두 고','바르게','설명으로','계산','구하','얼마','짝지']
SKIP=re.compile(r'^\s*(제\s?\d+조|[IVX]+\.|\[|\(원본\)|단원|부록|별표|Chapter|Phase|Contents)')
def extract(path):
    d=fitz.open(path); P=[d[i].get_text() for i in range(d.page_count)]
    out=[]
    for i,t in enumerate(P):
        if '①' not in t or '②' not in t: continue
        Jn="\n".join(norm(x) for x in t.split('\n') if norm(x))
        k=Jn.find('①'); qraw=HDR.sub('',Jn[:k]).strip(); qraw=re.sub(r'^\s*\d+\s*','',qraw); q=norm(qraw)
        if SKIP.match(q): continue
        if not (('출제 예상문제' in t) or ('기출' in t) or any(c in q for c in CUE)): continue
        Js=norm(t)  # 전체 spaced (옵션 전체 캡처)
        Js2=HDR.sub(' ',Js)
        opts=re.findall(r'[①②③④⑤][^①②③④⑤]{1,220}', Js2)
        opts=[re.split(r'\(정답\)|해설|문제 풀이', o)[0] for o in opts]
        if len(opts)<3 or len(q)<10: continue
        ans=""
        for j in (i,i+1,i+2):
            if j>=len(P): break
            m=re.search(r'\(정답\)\s*(.{0,240})', norm(P[j]))
            if m: ans=re.split(r'해설|문제 풀이',norm(m.group(1)))[0].strip(); break
        out.append({"page":i+1,"q":q[:500],"opts":[norm(o)[:200] for o in opts[:5]],"ans":ans[:260]})
    seen=set(); uq=[]
    for x in out:
        kk=x["q"][:26]
        if kk in seen: continue
        seen.add(kk); uq.append(x)
    return uq

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
ROOT=os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))  # CISA
def esc(s): return html.escape(s,quote=True)
for code,(pdf,htmlrel) in MAP.items():
    qs=extract(os.path.join(ROOT,pdf))
    if not qs: print(code,"문항 0 - skip"); continue
    hp=os.path.abspath(htmlrel)
    s=open(hp,encoding="utf-8").read()
    # 기존 주입 제거
    s=re.sub(r'\n*<section id="allquiz".*?</section>\n*', '\n', s, flags=re.S)
    s=re.sub(r'\n*<li data-qb="1">.*?</li>', '', s, flags=re.S)
    # 문제 HTML 생성
    items=[]
    for idx,q in enumerate(qs,1):
        opts="".join("<li>%s</li>"%esc(re.sub(r'^[①②③④⑤]\s*','',o)) for o in q["opts"])
        ansdisp = esc(q["ans"]) if q["ans"] else "원문 강의자료 해설 참조"
        items.append(
          '<div class="quiz-container"><div class="quiz-header"></div>'
          '<div class="quiz-question">Q%d. %s <span style="font-weight:400;color:#94a3b8;font-size:0.8rem;">(원본 p.%d)</span></div>'
          '<ol class="quiz-options">%s</ol>'
          '<div class="quiz-explanation"><strong>정답</strong> %s</div></div>'
          %(idx, esc(q["q"]), q["page"], opts, ansdisp))
    sec=('\n    <section id="allquiz" class="section">\n'
         '      <h2>📚 전체 기출·예상문제 (%d문항) — 원문 수록</h2>\n'
         '      <p>본 강좌 원본 PDF에 수록된 기출·예상문제를 <strong>빠짐없이 원문 그대로</strong> 정리했습니다. 정답·해설은 강의 원문 기준입니다.</p>\n'
         '      %s\n    </section>\n'
         %(len(qs), "\n      ".join(items)))
    s=s.replace("  </main>", sec+"  </main>",1)
    # 사이드바 항목 추가(첫 </ul> 앞)
    li='      <li data-qb="1" style="margin-top:8px;"><a href="#allquiz" style="font-weight:700;color:#b91c1c;">📚 전체 기출·예상문제 (%d)</a></li>\n    </ul>'%len(qs)
    s=s.replace("\n    </ul>", "\n"+li, 1)
    open(hp,"w",encoding="utf-8").write(s)
    print(f"{code}: {len(qs)}문항 주입 · {os.path.basename(hp)}")
