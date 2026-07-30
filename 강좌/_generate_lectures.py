# -*- coding: utf-8 -*-
"""
강좌 PDF → 표준 양식 HTML 자동 생성기 (하이브리드: 텍스트 본문 + 다이어그램 이미지)

- 각 슬라이드(page)를 <section id="pN"> 로 만들고, 제목/본문(문단·불릿) + 그 슬라이드의
  다이어그램 이미지를 함께 배치.
- 로고 등 여러 페이지에 반복되는 보일러플레이트 이미지는 자동 제외(dedup).
- 좌측 학습목차(챕터/구분 슬라이드 자동 감지), 헤더(☰목차·페이지이동·본문검색),
  임베드 대응 CSS/JS(폰트통일·헤더컴팩트·목차좌측·'본문 넓게' 스위치 연동),
  전역검색 진입(externalGoto/hash/postMessage) 을 모두 포함 → 랜딩페이지와 완전 연동.
- 생성 후 매니페스트(_lectures_manifest.json) 에 {slug,file,title,code,pages} 기록.

실행:  python3 _generate_lectures.py            (전체)
       python3 _generate_lectures.py M02        (특정 code 만)
"""
import os, re, sys, json, html, hashlib, io
import fitz  # PyMuPDF
from PIL import Image

BASE = os.path.dirname(os.path.abspath(__file__))          # .../8. 학습사이트/강좌
ROOT = os.path.dirname(os.path.dirname(BASE))              # .../CISA
MANIFEST = os.path.join(BASE, "_lectures_manifest.json")

# ---- 매핑: (과목 slug, code, 출력 파일명, 원본 PDF 상대경로, 기본 라벨) ----
S_GAM = "감리및사업관리"; S_SW = "소프트웨어공학"; S_DB = "데이터베이스"; S_SA = "시스템구조"; S_SEC = "보안"
MAP = [
  # 감리 및 사업관리 (M01 은 기존 Gemini 폴리시본 유지 → 제외)
  (S_GAM,"M02","M02_감리법지침.html","1-1 정보화법_제도_감리/1.2 감리 법 지침_V1.0_20190328_최종본.pdf","감리 법·지침"),
  (S_GAM,"M03","M03_감리지침_2장.html","1-1 정보화법_제도_감리/2. 감리 및 사업관리(25)_V1.3_2장 지침_5월 8일_최종본.pdf","감리지침 (2장)"),
  (S_GAM,"M04","M04_감리점검해설서.html","1-1 정보화법_제도_감리/2. 정보시스템 감리 점검 해설서 v3 요약정리.pdf","감리 점검 해설서"),
  (S_GAM,"M05","M05_감리총론_3장.html","1-1 정보화법_제도_감리/3. 감리 및 사업관리(25)_V1.1_3장 감리총론.pdf","감리총론 (3장)"),
  (S_GAM,"M06","M06_서브노트_감리.html","1-1 정보화법_제도_감리/서브노트(감리)_190106.pdf","서브노트 (감리)"),
  (S_GAM,"M07","M07_통합관리_1_4장.html","1-2 사업관리/1. 정보시스템감리사_사업관리_V5.4_1장_4장_통합관리.pdf","통합관리 (1~4장)"),
  (S_GAM,"M08","M08_사업관리특강.html","1-2 사업관리/1.1 사업관리 특강 및 출제 예상_V1.2_20190328_최종본.pdf","사업관리 특강·출제예상"),
  (S_GAM,"M09","M09_범위시간관리_5_6장.html","1-2 사업관리/2. 정보시스템감리사_사업관리_V5.4_5장 범위관리 6장 시간관리.pdf","범위·시간관리 (5~6장)"),
  (S_GAM,"M10","M10_원가품질관리_7_8장.html","1-2 사업관리/3. 정보시스템감리사_사업관리_V5.4_7장 원가관리_8장 품질관리.pdf","원가·품질관리 (7~8장)"),
  (S_GAM,"M11","M11_인적자원위험관리.html","1-2 사업관리/4. 정보시스템감리사_V5.5_9장 인적자원관리_11장 위험관리.pdf","인적자원·위험관리 (9,11장)"),
  (S_GAM,"M12","M12_조달이해관계자관리.html","1-2 사업관리/5. 정보시스템감리사_V5.4_12장 조달관리_13장 이해관계자관리.pdf","조달·이해관계자관리 (12~13장)"),
  # 소프트웨어공학 (9)
  (S_SW,"SE01","SE01_PartI_기초.html","2 소프트웨어공학/1. 소프트웨어공학_Part I_V1.2_강의최종본.pdf","Part I · SW공학 기초"),
  (S_SW,"SE02","SE02_PartI_아키텍처1.html","2 소프트웨어공학/1.2 소프트웨어공학_Part I_V1.1_아키텍처까지 강의.pdf","Part I · 아키텍처(1)"),
  (S_SW,"SE03","SE03_PartI_아키텍처2.html","2 소프트웨어공학/1.3 소프트웨어공학_Part I_V1.0_SW 아키텍처 외 완료.pdf","Part I · 아키텍처(2)"),
  (S_SW,"SE04","SE04_PartII_디자인UML.html","2 소프트웨어공학/2.1 소프트웨어공학_Part II_V1.1_디자인_UML.pdf","Part II · 디자인·UML"),
  (S_SW,"SE05","SE05_PartII_디자인패턴.html","2 소프트웨어공학/2.2 디자인 패턴_Part II_V1.1.pdf","Part II · 디자인 패턴"),
  (S_SW,"SE06","SE06_PartII_SW개발.html","2 소프트웨어공학/2.3 소프트웨어공학_Part II_SW 개발_V1.3.pdf","Part II · SW 개발"),
  (S_SW,"SE07","SE07_PartIII_테스트유지관리.html","2 소프트웨어공학/3.1 소프트웨어공학_Part III_V1.0_테스트_유지관리.pdf","Part III · 테스트·유지관리"),
  (S_SW,"SE08","SE08_PartIII_품질비용산정.html","2 소프트웨어공학/3.2 소프트웨어공학_Part III_V1.0_품질관리_비용산정.pdf","Part III · 품질관리·비용산정"),
  (S_SW,"SE09","SE09_SW공학개론.html","2 소프트웨어공학/[1]1. SW 공학_V1.1.pdf","SW 공학 개론"),
  # 데이터베이스 (8)
  (S_DB,"DB00","DB00_특강출제예상.html","3 데이터베이스/3. 데이터베이스 특강 및 출제 예상_V1.0_20190327.pdf","특강·출제예상"),
  (S_DB,"DB01","DB01_Ch1_개요.html","3 데이터베이스/3.데이터베이스_구환회기술사_Chapter1(36p)_개요.pdf","Ch1 · 개요"),
  (S_DB,"DB02","DB02_Ch2_트랜잭션.html","3 데이터베이스/3.데이터베이스_구환회기술사_Chapter2(69p)_트랜잭션.pdf","Ch2 · 트랜잭션"),
  (S_DB,"DB03","DB03_Ch3_모델링.html","3 데이터베이스/3.데이터베이스_구환회기술사_Chapter3(98p)_모델링.pdf","Ch3 · 모델링"),
  (S_DB,"DB04","DB04_Ch4_SQL.html","3 데이터베이스/3.데이터베이스_구환회기술사_Chapter4(134p)_SQL.pdf","Ch4 · SQL"),
  (S_DB,"DB05","DB05_Ch5_유형.html","3 데이터베이스/3.데이터베이스_구환회기술사_Chapter5(34p)_유형.pdf","Ch5 · 유형"),
  (S_DB,"DB06","DB06_Ch6_분석.html","3 데이터베이스/3.데이터베이스_구환회기술사_Chapter6(55p)_분석.pdf","Ch6 · 분석"),
  (S_DB,"DB07","DB07_Ch7_빅데이터.html","3 데이터베이스/3.데이터베이스_구환회기술사_Chapter7(19p)_빅데이터_기타.pdf","Ch7 · 빅데이터·기타"),
  # 시스템구조 (2)
  (S_SA,"SA01","SA01_Module04_시스템구조.html","4 시스템 구조/Module_04_시스템구조.pdf","Module 04 · 시스템구조"),
  (S_SA,"SA02","SA02_시스템구조_강의자료.html","4 시스템 구조/[1]시스템 구조 감리사 강의자료.pdf","시스템 구조 강의자료"),
  # 보안 (10)
  (S_SEC,"SEC00","SEC00_특강출제예상.html","5 보안도메인_PDF/1.5 보안 특강 및 출제 예상_V1.0_20190410_final.pdf","특강·출제예상"),
  (S_SEC,"SEC01","SEC01_Ch1.html","5 보안도메인_PDF/5.보안(170319)_이아람기술사_Chapter1.pdf","Chapter 1"),
  (S_SEC,"SEC02","SEC02_Ch2.html","5 보안도메인_PDF/5.보안(170319)_이아람기술사_Chapter2_20170320(최종).pdf","Chapter 2"),
  (S_SEC,"SEC03","SEC03_Ch3_1.html","5 보안도메인_PDF/5.보안(170319)_이아람기술사_Chapter3-1_20170320(최종).pdf","Chapter 3-1"),
  (S_SEC,"SEC04","SEC04_Ch3_2.html","5 보안도메인_PDF/5.보안(170319)_이아람기술사_Chapter3-2_20170320(최종).pdf","Chapter 3-2"),
  (S_SEC,"SEC05","SEC05_Ch4_1.html","5 보안도메인_PDF/5.보안(170319)_이아람기술사_Chapter4-1.pdf","Chapter 4-1"),
  (S_SEC,"SEC06","SEC06_Ch4_2.html","5 보안도메인_PDF/5.보안(170319)_이아람기술사_Chapter4-2.pdf","Chapter 4-2"),
  (S_SEC,"SEC07","SEC07_Ch4_3.html","5 보안도메인_PDF/5.보안(170319)_이아람기술사_Chapter4-3.pdf","Chapter 4-3"),
  (S_SEC,"SEC08","SEC08_Ch5_1.html","5 보안도메인_PDF/5.보안(170319)_이아람기술사_Chapter5-1(수정본).pdf","Chapter 5-1"),
  (S_SEC,"SEC09","SEC09_Ch5_2.html","5 보안도메인_PDF/5.보안(170319)_이아람기술사_Chapter5-2(수정본).pdf","Chapter 5-2"),
]

BULLET = "•·▪◦‣∙-–▶►■□◆●○*"
def esc(s): return html.escape(s, quote=True)

def clean_lines(raw):
    out = []
    for ln in raw.split("\n"):
        t = ln.strip().strip(" ").strip()
        if not t: continue
        if re.fullmatch(r"[\d]{1,4}", t): continue          # 페이지 번호
        if re.fullmatch(r"[%s\s]+" % re.escape(BULLET), t): continue
        out.append(t)
    return out

def slide_title(lines):
    for t in lines:
        core = t.lstrip("".join(["\\", *list(BULLET)])).strip()
        if 2 <= len(core) <= 60 and not core[0].isdigit():
            return core
    return lines[0][:60] if lines else ""

def is_bullet(t):
    return len(t) > 0 and t[0] in BULLET

def body_html(lines, title):
    parts, ul = [], []
    def flush():
        if ul:
            parts.append("<ul>" + "".join("<li>%s</li>" % esc(x) for x in ul) + "</ul>")
            ul.clear()
    skipped = False
    for t in lines:
        if not skipped and t == title:   # 제목 1회 제거
            skipped = True; continue
        core = t.lstrip("".join(list(BULLET))).strip()
        if not core: continue
        if is_bullet(t):
            ul.append(core)
        else:
            flush()
            parts.append("<p>%s</p>" % esc(core))
    flush()
    return "\n".join(parts)

def choose_title(doc, default):
    # 큐레이션 라벨에 한글 토픽이 있으면 그대로 사용(감리/SW/DB 등)
    if re.search(r"[가-힣]", default):
        return default
    # 토픽 없는 라벨(보안 'Chapter N') → PDF에서 'Chapter N. 한글토픽' 추출
    pat = re.compile(r"Chapter\s+([IVXLC0-9]+)\s*[.\-]?\s*([가-힣][^\n]{0,18})")
    for i in range(min(8, doc.page_count)):
        for ln in doc[i].get_text().split("\n"):
            m = pat.search(ln)
            if m:
                topic = re.sub(r"\s+", " ", m.group(2)).strip(" .")
                return "Chapter %s. %s" % (m.group(1), topic)
    return default

def extract_images(doc, page_index, out_dir, xref_count, saved, npages):
    """페이지의 다이어그램 이미지를 저장, 파일명 리스트 반환(보일러플레이트 제외).
       dedup·보일러플레이트 판정은 xref(추출 1회) 기반으로 빠르게 처리."""
    figs = []
    page = doc[page_index]
    try:
        imlist = page.get_images(full=True)
    except Exception:
        return figs
    boiler_thr = max(6, int(npages * 0.25))
    seen_here = set()
    for img in imlist:
        xref = img[0]
        if xref in seen_here: continue
        seen_here.add(xref)
        if xref_count.get(xref, 0) >= boiler_thr:  # 여러 페이지 반복 = 로고류 제외
            continue
        if xref in saved:                           # 동일 이미지 재사용
            figs.append(saved[xref]); continue
        try:
            base = doc.extract_image(xref)
        except Exception:
            continue
        data = base.get("image")
        if not data: continue
        try:
            im = Image.open(io.BytesIO(data))
            w, k = im.size
            if min(w, k) < 90:                    # 너무 작은 아이콘 제외
                continue
            if im.mode in ("RGBA", "P", "LA"):
                bg = Image.new("RGB", im.size, (255, 255, 255))
                im = im.convert("RGBA"); bg.paste(im, mask=im.split()[-1]); im = bg
            else:
                im = im.convert("RGB")
            longest = max(im.size)
            if longest > 1100:
                r = 1100 / longest
                im = im.resize((int(im.size[0]*r), int(im.size[1]*r)))
            fn = "img%03d.jpg" % (len(saved) + 1)
            im.save(os.path.join(out_dir, fn), "JPEG", quality=72, optimize=True)
            saved[xref] = fn
            figs.append(fn)
        except Exception:
            continue
    return figs

def count_xrefs(doc):
    """이미지 xref 별 등장 페이지 수(추출 없이 빠르게)."""
    xc = {}
    for i in range(doc.page_count):
        try: imlist = doc[i].get_images(full=True)
        except Exception: imlist = []
        for xref in set(img[0] for img in imlist):
            xc[xref] = xc.get(xref, 0) + 1
    return xc

TEMPLATE = None  # 아래 build_html 에서 f-string 사용

def build_html(code, subtitle, sections_html, toc_html, npages):
    title_full = "[%s] %s" % (code, subtitle)
    return f"""<!DOCTYPE html>
<html lang="ko">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>{esc(title_full)}</title>
<style>
:root {{ --primary:#1e3a8a; --secondary:#3b82f6; --accent:#0ea5e9; --border-color:#cbd5e1;
  --bg-main:#f8fafc; --text-main:#334155; --text-dark:#0f172a; --table-header:#e0e7ff; }}
* {{ box-sizing:border-box; margin:0; padding:0; }}
body {{ font-family:'Pretendard',-apple-system,'Malgun Gothic',sans-serif; color:var(--text-main); background:var(--bg-main); line-height:1.7; }}
.top-nav {{ background:#0f172a; padding:12px 20px; position:sticky; top:0; z-index:1000; }}
.top-nav a {{ color:#fff; text-decoration:none; font-weight:bold; font-size:0.95rem; }}
.top-nav a:hover {{ color:#93c5fd; }}
.header {{ background:var(--primary); color:#fff; padding:15px 20px; display:flex; flex-wrap:wrap; align-items:center; justify-content:space-between; gap:15px; box-shadow:0 4px 6px rgba(0,0,0,0.1); position:sticky; top:45px; z-index:999; }}
.header-left {{ display:flex; align-items:center; gap:15px; }}
.toggle-btn {{ background:#fff; color:var(--primary); border:none; padding:6px 12px; border-radius:4px; font-weight:bold; cursor:pointer; font-size:0.95rem; display:flex; align-items:center; gap:5px; }}
.toggle-btn:hover {{ background:var(--table-header); }}
.header-title {{ font-size:1.2rem; font-weight:bold; }}
.header-controls {{ display:flex; gap:12px; flex-wrap:wrap; align-items:center; }}
.control-group {{ display:flex; align-items:center; gap:8px; background:rgba(255,255,255,0.1); padding:6px 12px; border-radius:6px; font-size:0.9rem; }}
.control-group input {{ padding:5px 8px; border:1px solid #ccc; border-radius:4px; font-size:0.85rem; outline:none; }}
.control-group input[type=number] {{ width:80px; }}
.control-group input[type=text] {{ width:140px; }}
.control-group button {{ padding:5px 12px; background:var(--secondary); color:#fff; border:none; border-radius:4px; cursor:pointer; font-weight:bold; }}
.container {{ max-width:1400px; margin:30px auto; padding:0 20px; display:flex; gap:40px; align-items:flex-start; }}
.sidebar {{ flex:0 0 300px; background:#fff; padding:20px; border-radius:8px; border:1px solid var(--border-color); position:sticky; top:130px; max-height:calc(100vh - 150px); overflow-y:auto; transition:all 0.3s ease; }}
.sidebar.hidden {{ width:0; padding:0; border:none; opacity:0; overflow:hidden; transform:translateX(-20px); flex:0 0 0px; margin:0; }}
.sidebar h3 {{ margin-bottom:12px; color:var(--primary); border-bottom:2px solid var(--primary); padding-bottom:10px; font-size:1rem; }}
.sidebar ul {{ list-style:none; }}
.sidebar li {{ margin-bottom:6px; font-size:0.9rem; }}
.sidebar a {{ text-decoration:none; color:var(--text-main); display:block; padding:4px 6px; border-radius:4px; }}
.sidebar a:hover {{ color:var(--secondary); background:#f1f5f9; }}
.content {{ flex:1; min-width:0; }}
.slide {{ background:#fff; border:1px solid var(--border-color); border-radius:8px; padding:22px 26px; margin-bottom:18px; scroll-margin-top:120px; }}
.slide-title {{ font-size:1.15rem; color:var(--primary); font-weight:bold; border-left:5px solid var(--secondary); padding-left:12px; margin-bottom:14px; }}
.slide-num {{ float:right; font-size:0.75rem; color:#94a3b8; font-weight:normal; }}
.slide p {{ margin:6px 0; }}
.slide ul {{ margin:8px 0 8px 22px; }}
.slide li {{ margin:3px 0; }}
.figs {{ display:flex; flex-wrap:wrap; gap:12px; margin-top:14px; }}
.figs img {{ max-width:100%; border:1px solid var(--border-color); border-radius:6px; background:#fff; }}
mark.search-highlight {{ background:#fde68a; padding:0 1px; border-radius:2px; }}
mark.search-highlight.active {{ background:#f59e0b; color:#fff; }}
@media (max-width:992px) {{
  .container {{ flex-direction:column; }}
  .sidebar {{ position:static; width:100%; max-height:none; margin-bottom:20px; }}
  .header {{ justify-content:center; text-align:center; }}
}}
/* === 임베드(iframe) 대응 === */
html.embedded {{ font-size:14.5px; }}
html.embedded .top-nav {{ display:none !important; }}
html.embedded .header {{ top:0 !important; padding:5px 12px; gap:8px; box-shadow:0 2px 4px rgba(0,0,0,0.08); }}
html.embedded .header-title {{ font-size:0.92rem; }}
html.embedded .toggle-btn {{ padding:3px 8px; font-size:0.78rem; }}
html.embedded .control-group {{ padding:3px 8px; font-size:0.78rem; gap:5px; }}
html.embedded .control-group input {{ padding:2px 6px; font-size:0.76rem; }}
html.embedded .control-group input[type=number] {{ width:58px; }}
html.embedded .control-group input[type=text] {{ width:108px; }}
html.embedded .control-group button {{ padding:2px 8px; }}
html.embedded .sidebar {{ top:var(--embed-hdr,92px); max-height:calc(100vh - var(--embed-hdr,92px) - 20px); position:sticky; margin-bottom:0; }}
html.embedded .container {{ flex-direction:row; gap:20px; margin:16px auto; padding:0 16px; }}
html.embedded .sidebar:not(.hidden) {{ width:auto; flex:0 0 210px; }}
html.embedded.chrome-hidden .header {{ display:none !important; }}
@media (max-width:640px) {{
  html.embedded .container {{ flex-direction:column; }}
  html.embedded .sidebar:not(.hidden) {{ position:static; width:100%; flex:none; max-height:none; margin-bottom:16px; }}
}}
</style>
</head>
<body>
<div class="top-nav"><a href="../../index.html">← 학습 사이트 메인으로</a></div>
<div class="header">
  <div class="header-left">
    <button id="toggle-sidebar-btn" class="toggle-btn"><span>☰</span> 목차</button>
    <div class="header-title">{esc(title_full)}</div>
  </div>
  <div class="header-controls">
    <div class="control-group"><span id="page-display">1/{npages}</span>
      <input type="number" id="page-input" placeholder="페이지" min="1">
      <button type="button" id="page-move-btn">이동</button></div>
    <div class="control-group"><input type="text" id="search-input" placeholder="본문 검색">
      <button type="button" id="search-btn">검색</button></div>
  </div>
</div>
<div class="container">
  <aside class="sidebar" id="sidebar">
    <h3>📑 학습 목차</h3>
    <ul>{toc_html}</ul>
  </aside>
  <main class="content" id="content-area">
{sections_html}
  </main>
</div>
<script>
document.addEventListener('DOMContentLoaded', function () {{
  var sidebar=document.getElementById('sidebar');
  document.getElementById('toggle-sidebar-btn').addEventListener('click',function(){{ sidebar.classList.toggle('hidden'); }});
  var pageDisplay=document.getElementById('page-display'), pageInput=document.getElementById('page-input'), pageMoveBtn=document.getElementById('page-move-btn');
  function calc(){{ var ph=window.innerHeight, tot=document.documentElement.scrollHeight; var tp=Math.max(1,Math.ceil(tot/ph)); var cp=Math.min(tp,Math.floor(window.scrollY/ph)+1); pageDisplay.textContent=cp+'/'+tp; pageInput.max=tp; return {{ph:ph,tp:tp}}; }}
  window.addEventListener('scroll',function(){{ requestAnimationFrame(calc); }}); window.addEventListener('resize',calc); calc();
  pageMoveBtn.addEventListener('click',function(){{ var t=parseInt(pageInput.value,10); var c=calc(); if(t>0&&t<=c.tp){{ window.scrollTo({{top:(t-1)*c.ph,behavior:'smooth'}}); }} else if(t>c.tp){{ window.scrollTo({{top:document.documentElement.scrollHeight,behavior:'smooth'}}); }} }});
  pageInput.addEventListener('keypress',function(e){{ if(e.key==='Enter') pageMoveBtn.click(); }});

  var searchInput=document.getElementById('search-input'), searchBtn=document.getElementById('search-btn'), contentArea=document.getElementById('content-area');
  var matches=[], mi=-1;
  function clearHi(){{ contentArea.querySelectorAll('mark.search-highlight').forEach(function(m){{ var p=m.parentNode; p.replaceChild(document.createTextNode(m.textContent),m); p.normalize(); }}); matches=[]; mi=-1; }}
  function doHighlight(term){{ clearHi(); if(!term){{ searchInput.dataset.last=''; return 0; }} searchInput.dataset.last=term;
    var esc=term.replace(/[.*+?^${{}}()|[\\]\\\\]/g,'\\\\$&');
    var w=document.createTreeWalker(contentArea,NodeFilter.SHOW_TEXT,null,false), nodes=[], n;
    while(n=w.nextNode()){{ if(n.parentElement.tagName!=='SCRIPT'&&n.parentElement.tagName!=='STYLE'&&n.nodeValue.toLowerCase().includes(term.toLowerCase())) nodes.push(n); }}
    nodes.forEach(function(tn){{ var rx=new RegExp('('+esc+')','gi'), fr=document.createDocumentFragment(), li=0;
      tn.nodeValue.replace(rx,function(mt,p1,off){{ fr.appendChild(document.createTextNode(tn.nodeValue.slice(li,off))); var mk=document.createElement('mark'); mk.className='search-highlight'; mk.textContent=mt; fr.appendChild(mk); li=off+mt.length; }});
      fr.appendChild(document.createTextNode(tn.nodeValue.slice(li))); tn.parentNode.replaceChild(fr,tn); }});
    matches=contentArea.querySelectorAll('mark.search-highlight'); return matches.length; }}
  function scrollToEl(el,off){{ if(!el) return; var r=el.getBoundingClientRect(); window.scrollTo({{top:window.pageYOffset+r.top-(off||120),behavior:'smooth'}}); }}
  function performSearch(){{ var term=searchInput.value.trim();
    if(term&&term===searchInput.dataset.last&&matches.length){{ matches[mi].classList.remove('active'); mi=(mi+1)%matches.length; matches[mi].classList.add('active'); scrollToEl(matches[mi]); return; }}
    var c=doHighlight(term); if(!term) return; if(c===0){{ alert('검색 결과가 없습니다.'); return; }} mi=0; matches[0].classList.add('active'); scrollToEl(matches[0]); }}
  searchBtn.addEventListener('click',performSearch);
  searchInput.addEventListener('keypress',function(e){{ if(e.key==='Enter') performSearch(); }});
  searchInput.addEventListener('input',function(e){{ if(e.target.value.trim()===''){{ clearHi(); searchInput.dataset.last=''; }} }});

  function externalGoto(id,term){{ if(term){{ var c=doHighlight(term); if(c>0){{ mi=0; matches[0].classList.add('active'); }} }}
    var el=id?document.getElementById(id):null; var target=el||(matches&&matches[0])||null;
    var off=document.documentElement.classList.contains('embedded')?70:120; if(target) setTimeout(function(){{ scrollToEl(target,off); }},40); }}
  function parseNavHash(){{ var h=(location.hash||'').replace(/^#/,''); if(!h) return null; var p=new URLSearchParams(h); if(p.has('sec')||p.has('q')) return {{id:p.get('sec')||'',q:p.get('q')||''}}; return {{id:h,q:''}}; }}
  var nav=parseNavHash(); if(nav) setTimeout(function(){{ externalGoto(nav.id,nav.q); }},80);
  window.addEventListener('hashchange',function(){{ var n=parseNavHash(); if(n) externalGoto(n.id,n.q); }});
  window.addEventListener('message',function(e){{ var d=e.data||{{}}; if(d&&d.type==='lecture-goto') externalGoto(d.id||'',d.q||''); }});
}});
</script>
<script>
if (window.self !== window.top) {{
  document.documentElement.classList.add('embedded');
  var syncHeaderOffset=function(){{ var hdr=document.querySelector('.header'); if(!hdr) return; var h=Math.ceil(hdr.getBoundingClientRect().height); document.documentElement.style.setProperty('--embed-hdr',(h+8)+'px'); }};
  window.addEventListener('load',syncHeaderOffset); window.addEventListener('resize',syncHeaderOffset); syncHeaderOffset();
  window.addEventListener('message',function(e){{ var d=e.data||{{}}; if(d&&d.type==='lecture-chrome'){{ document.documentElement.classList.toggle('chrome-hidden',d.show===false); setTimeout(syncHeaderOffset,40); }} }});
}}
</script>
</body>
</html>"""

def process(entry):
    slug, code, out, src, deflabel = entry
    pdf_path = os.path.join(ROOT, src)
    if not os.path.exists(pdf_path):
        print("  [MISSING]", src); return None
    doc = fitz.open(pdf_path)
    npages = doc.page_count
    subtitle = choose_title(doc, deflabel)
    out_dir = os.path.join(BASE, slug)
    os.makedirs(out_dir, exist_ok=True)
    asset_dir = os.path.join(out_dir, "assets", code)
    os.makedirs(asset_dir, exist_ok=True)
    hc = count_xrefs(doc)
    saved = {}
    sections, toc, titles = [], [], {}
    chap_pat = re.compile(r"(Chapter\s+[IVXLC0-9]+|\[Module|제?\s*\d+\s*장|Part\s+[IVX0-9]+|Section\s+\d+)", re.I)
    for i in range(npages):
        lines = clean_lines(doc[i].get_text())
        title = slide_title(lines) if lines else ("슬라이드 %d" % (i+1))
        titles[i+1] = title
        body = body_html(lines, title) if lines else ""
        figs = extract_images(doc, i, asset_dir, hc, saved, npages)
        fig_html = ""
        if figs:
            fig_html = '<div class="figs">' + "".join(
                '<img loading="lazy" src="assets/%s/%s" alt="슬라이드 %d 그림">' % (code, f, i+1) for f in figs) + '</div>'
        sec = ('<section id="p%d" class="slide">\n'
               '  <div class="slide-title">%s<span class="slide-num">p.%d</span></div>\n'
               '  %s\n  %s\n</section>') % (i+1, esc(title), i+1, body, fig_html)
        sections.append(sec)
        # 목차 후보: 챕터/구분 슬라이드(제목이 챕터 패턴) 또는 본문이 거의 없는 표지형
        if (chap_pat.search(title) or len(body) < 40) and title and len(title) >= 3:
            toc.append((i+1, title))
    # 챕터 우선 → 부족하면 표지형 포함 → 슬라이드 밀도(약 12p당 1개)로 균등 보강
    chap_only = [(n, t) for (n, t) in toc if chap_pat.search(t)]
    toc_use = chap_only if len(chap_only) >= 3 else list(toc)
    target = min(80, max(8, npages // 12))
    if len(toc_use) < target:
        have = set(n for n, _ in toc_use)
        step = max(1, npages // target)
        for n in range(1, npages + 1, step):
            if n not in have:
                toc_use.append((n, titles.get(n, "슬라이드 %d" % n)))
        toc_use.sort()
    if len(toc_use) > 80:
        toc_use = toc_use[:80]
    if not toc_use:
        toc_use = [(1, subtitle)]
    toc_html = "".join('<li><a href="#p%d"><span style="color:#94a3b8">p.%d</span> %s</a></li>' % (n, n, esc(t[:44])) for (n, t) in toc_use)
    sections_html = "\n".join(sections)
    htmlout = build_html(code, subtitle, sections_html, toc_html, npages)
    with open(os.path.join(out_dir, out), "w", encoding="utf-8") as f:
        f.write(htmlout)
    imgs = len(saved)
    size_kb = (len(htmlout) + sum(os.path.getsize(os.path.join(asset_dir,f)) for f in os.listdir(asset_dir))) // 1024
    print("  [OK] %-9s %-30s p.%-4d img %-4d %6dKB  «%s»" % (code, out, npages, imgs, size_kb, subtitle))
    return {"slug": slug, "file": out, "code": code, "title": "%s. %s" % (code, subtitle), "pages": npages, "images": imgs}

def main():
    only = sys.argv[1:] if len(sys.argv) > 1 else None
    manifest = []
    for e in MAP:
        if only and e[1] not in only: continue
        r = process(e)
        if r: manifest.append(r)
    # 매니페스트 병합 저장(부분 실행도 반영)
    prev = {}
    if os.path.exists(MANIFEST):
        try: prev = {x["code"]: x for x in json.load(open(MANIFEST, encoding="utf-8"))}
        except Exception: prev = {}
    for r in manifest: prev[r["code"]] = r
    allm = [prev[c] for c in [e[1] for e in MAP] if c in prev]
    json.dump(allm, open(MANIFEST, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print("\n매니페스트 저장:", MANIFEST, "| 항목", len(allm))

if __name__ == "__main__":
    main()
