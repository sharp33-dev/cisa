# -*- coding: utf-8 -*-
import fitz, os, re, sys, html
from PIL import Image
ROOT=os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
MAP={
 "M02":("1-1 정보화법_제도_감리/1.2 감리 법 지침_V1.0_20190328_최종본.pdf","감리및사업관리/M02_감리법지침.html"),
 "M03":("1-1 정보화법_제도_감리/2. 감리 및 사업관리(25)_V1.3_2장 지침_5월 8일_최종본.pdf","감리및사업관리/M03_감리지침_2장.html"),
 "M04":("1-1 정보화법_제도_감리/2. 정보시스템 감리 점검 해설서 v3 요약정리.pdf","감리및사업관리/M04_감리점검해설서.html"),
 "M06":("1-1 정보화법_제도_감리/서브노트(감리)_190106.pdf","감리및사업관리/M06_서브노트_감리.html"),
 "M05":("1-1 정보화법_제도_감리/3. 감리 및 사업관리(25)_V1.1_3장 감리총론.pdf","감리및사업관리/M05_감리총론_3장.html"),
 "M07":("1-2 사업관리/1. 정보시스템감리사_사업관리_V5.4_1장_4장_통합관리.pdf","감리및사업관리/M07_통합관리_1_4장.html"),
 "M08":("1-2 사업관리/1.1 사업관리 특강 및 출제 예상_V1.2_20190328_최종본.pdf","감리및사업관리/M08_사업관리특강.html"),
 "M09":("1-2 사업관리/2. 정보시스템감리사_사업관리_V5.4_5장 범위관리 6장 시간관리.pdf","감리및사업관리/M09_범위시간관리_5_6장.html"),
 "M10":("1-2 사업관리/3. 정보시스템감리사_사업관리_V5.4_7장 원가관리_8장 품질관리.pdf","감리및사업관리/M10_원가품질관리_7_8장.html"),
 "M11":("1-2 사업관리/4. 정보시스템감리사_V5.5_9장 인적자원관리_11장 위험관리.pdf","감리및사업관리/M11_인적자원위험관리.html"),
 "M12":("1-2 사업관리/5. 정보시스템감리사_V5.4_12장 조달관리_13장 이해관계자관리.pdf","감리및사업관리/M12_조달이해관계자관리.html"),
}
def render(code,p0,p1):
    pdf,_=MAP[code]; d=fitz.open(os.path.join(ROOT,pdf))
    outdir=os.path.join("감리및사업관리","assets",code+"slides"); os.makedirs(outdir,exist_ok=True)
    mat=fitz.Matrix(1.35,1.35)
    for i in range(p0,min(p1,d.page_count)):
        fn=os.path.join(outdir,"p%03d.jpg"%(i+1))
        pix=d[i].get_pixmap(matrix=mat)
        im=Image.frombytes("RGB",[pix.width,pix.height],pix.samples)
        im.save(fn,"JPEG",quality=70,optimize=True)
    return d.page_count
def inject(code):
    pdf,htmlrel=MAP[code]; d=fitz.open(os.path.join(ROOT,pdf)); npages=d.page_count
    hp=os.path.abspath(htmlrel); s=open(hp,encoding="utf-8").read()
    s=re.sub(r'\n*<section id="origslides".*?</section>\n*','\n',s,flags=re.S)
    s=re.sub(r'\n*<li data-os="1">.*?</li>','',s,flags=re.S)
    imgs="".join('<img loading="lazy" src="assets/%sslides/p%03d.jpg" alt="원본 p.%d" style="width:100%%;margin:8px 0;border:1px solid var(--border-color);border-radius:4px;">'%(code,i+1,i+1) for i in range(npages))
    sec=('\n    <section id="origslides" class="section">\n'
         '      <h2>📄 원본 강의 슬라이드 (전체 %d페이지)</h2>\n'
         '      <p>위 요약·해설에서 옮기기 어려운 <strong>ITO 표·다이어그램 등 원본 내용을 누락 없이</strong> 확인할 수 있도록 원본 강의 슬라이드 전체를 수록했습니다.</p>\n'
         '      <div style="max-height:none;">%s</div>\n    </section>\n'%(npages,imgs))
    s=s.replace("  </main>",sec+"  </main>",1)
    li='      <li data-os="1" style="margin-top:6px;"><a href="#origslides" style="font-weight:700;color:#0e7490;">📄 원본 슬라이드 전체 (%d)</a></li>\n    </ul>'%npages
    s=s.replace("\n    </ul>","\n"+li,1)
    open(hp,"w",encoding="utf-8").write(s)
    return npages
if __name__=="__main__":
    code=sys.argv[1]; 
    if len(sys.argv)>=4 and sys.argv[2]=="render":
        n=render(code,int(sys.argv[3]),int(sys.argv[4])); print(f"{code} render {sys.argv[3]}~{sys.argv[4]} / total {n}")
    elif len(sys.argv)>=3 and sys.argv[2]=="inject":
        print(f"{code} inject: {inject(code)}p")
