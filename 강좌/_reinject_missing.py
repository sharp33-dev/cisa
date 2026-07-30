# -*- coding: utf-8 -*-
import fitz, os, re
ROOT=os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
MAP={
 "M02":("1-1 정보화법_제도_감리/1.2 감리 법 지침_V1.0_20190328_최종본.pdf","감리및사업관리/M02_감리법지침.html"),
 "M03":("1-1 정보화법_제도_감리/2. 감리 및 사업관리(25)_V1.3_2장 지침_5월 8일_최종본.pdf","감리및사업관리/M03_감리지침_2장.html"),
 "M04":("1-1 정보화법_제도_감리/2. 정보시스템 감리 점검 해설서 v3 요약정리.pdf","감리및사업관리/M04_감리점검해설서.html"),
 "M05":("1-1 정보화법_제도_감리/3. 감리 및 사업관리(25)_V1.1_3장 감리총론.pdf","감리및사업관리/M05_감리총론_3장.html"),
 "M06":("1-1 정보화법_제도_감리/서브노트(감리)_190106.pdf","감리및사업관리/M06_서브노트_감리.html"),
 "M07":("1-2 사업관리/1. 정보시스템감리사_사업관리_V5.4_1장_4장_통합관리.pdf","감리및사업관리/M07_통합관리_1_4장.html"),
 "M08":("1-2 사업관리/1.1 사업관리 특강 및 출제 예상_V1.2_20190328_최종본.pdf","감리및사업관리/M08_사업관리특강.html"),
 "M09":("1-2 사업관리/2. 정보시스템감리사_사업관리_V5.4_5장 범위관리 6장 시간관리.pdf","감리및사업관리/M09_범위시간관리_5_6장.html"),
 "M10":("1-2 사업관리/3. 정보시스템감리사_사업관리_V5.4_7장 원가관리_8장 품질관리.pdf","감리및사업관리/M10_원가품질관리_7_8장.html"),
 "M11":("1-2 사업관리/4. 정보시스템감리사_V5.5_9장 인적자원관리_11장 위험관리.pdf","감리및사업관리/M11_인적자원위험관리.html"),
 "M12":("1-2 사업관리/5. 정보시스템감리사_V5.4_12장 조달관리_13장 이해관계자관리.pdf","감리및사업관리/M12_조달이해관계자관리.html"),
}
ITO=re.compile(r'(입력물.*산출물|산출물.*입력물|도구\s*및\s*기법)',re.S)
def flagged(pdf):
    d=fitz.open(os.path.join(ROOT,pdf)); out=[]
    for i in range(d.page_count):
        t=d[i].get_text(); clean=re.sub(r'감리사 합격을 위한 사업관리 총정리|\s','',t); imgs=len(d[i].get_images())
        if (len(clean)<90 and imgs>=1) or ITO.search(t) or (imgs>=4 and len(clean)<500): out.append(i+1)
    return out, d.page_count
for c,(pdf,htmlrel) in MAP.items():
    hp=os.path.abspath(htmlrel); s=open(hp,encoding="utf-8").read()
    # 기존 전체첨부/보완 섹션 및 사이드바 제거
    s=re.sub(r'\n*<section id="origslides".*?</section>\n*','\n',s,flags=re.S)
    s=re.sub(r'\n*<li data-os="1">.*?</li>','',s,flags=re.S)
    pages,tot=flagged(pdf)
    slugdir="assets/%sslides"%c
    # 렌더 이미지가 실제 있는지 확인(없으면 스킵)
    absdir=os.path.join(os.path.dirname(hp),slugdir)
    avail=[p for p in pages if os.path.exists(os.path.join(absdir,"p%03d.jpg"%p))]
    if not avail: print(f"{c}: 이미지 없음 skip"); continue
    imgs="".join('<figure style="margin:0 0 16px;"><img loading="lazy" src="%s/p%03d.jpg" alt="원본 p.%d" style="width:100%%;border:1px solid var(--border-color);border-radius:4px;"><figcaption style="font-size:0.8rem;color:#94a3b8;">원본 p.%d</figcaption></figure>'%(slugdir,p,p,p) for p in avail)
    sec=('\n    <section id="origslides" class="section">\n'
         '      <h2>📄 원본 보완 – 도표·ITO 등 추출이 어려운 페이지 (%d개)</h2>\n'
         '      <p>요약·해설로 옮기기 어려운 <strong>ITO 표·다이어그램·매트릭스</strong> 등은 텍스트 추출 시 구조가 손실되므로, 해당 페이지의 <strong>원본 이미지</strong>를 그대로 수록해 내용 누락을 방지했습니다. (전체 %dp 중 추출 곤란 %dp)</p>\n'
         '      <div>%s</div>\n    </section>\n'%(len(avail),tot,len(avail),imgs))
    s=s.replace("  </main>",sec+"  </main>",1)
    li='      <li data-os="1" style="margin-top:6px;"><a href="#origslides" style="font-weight:700;color:#0e7490;">📄 원본 보완 (추출곤란 %d)</a></li>\n    </ul>'%len(avail)
    s=s.replace("\n    </ul>","\n"+li,1)
    open(hp,"w",encoding="utf-8").write(s)
    print(f"{c}: 추출곤란 {len(avail)}/{tot}p 삽입")
