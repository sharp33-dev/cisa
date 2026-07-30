# -*- coding: utf-8 -*-
"""
페이지-덤프형 강좌 HTML(<section id="pN"> 1장=1섹션)을 감리 강좌 수준의
주제별 <h2> 섹션 구조로 전면 재구성한다. PDF에서 직접 재추출하며,
표는 표로, 본문은 문단으로, 다이어그램/저텍스트 페이지는 원본 페이지를
렌더링한 이미지로 삽입한다. 마지막에 전체 기출·예상문제 뱅크를 주입한다.
"""
import fitz, re, os, sys, io, html as htmlmod
from PIL import Image

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))  # CISA
LEC = os.path.join(ROOT, "8. 학습사이트", "강좌")

# ---------- 공통 유틸 ----------
def esc(x): return (x or "").replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")

def mlines(t):
    ls = [re.sub(r"\s+", " ", x).strip() for x in t.split("\n")]
    return [x for x in ls if x and not re.fullmatch(r"[\d\s]+", x)]

def ns(x): return re.sub(r'\s', '', x or '')

def has_marker(x):
    # 일부 PDF는 텍스트 추출 시 한글 단어 사이 공백이 사라짐(예: "토픽핵심요약정리") -> 공백 무시 비교
    return '토픽핵심요약정리' in ns(x)

COVERMARK = re.compile(r'(\[Module|Module\s*0?\d|도메인|이론과\s*전략|수석감리원|기술사|PMP|시험\s*소개|'
                        r'시험\s*로드맵|로드맵|출제\s*빈도|출제빈도|출제분야|세부\s*출제\s*내용|합격\s*단계|'
                        r'강의\s*Roadmap|Overview|Contents|^목차$|Chapter\s*[IVXⅠ-Ⅹ0-9]|Phase\s*[0-9]|'
                        r'IT\s*Leaders|Coursework)')

NOISE = re.compile(r'^\s*\d+\s*$|itpe|ITPE')

def is_cover(t, allow_topic=True):
    ml = mlines(t); text = " ".join(ml)
    if allow_topic and len(ml) >= 2 and has_marker(ml[1]):
        return False
    core = text
    if len(re.sub(r"\s", "", core)) < 5:
        return True
    if COVERMARK.search(text):
        return True
    return False

# ---------- 표/텍스트 복원 (감리 _tableize.py 로직 재사용) ----------
def clean_cell(c, split_items=False):
    if not c:
        return ""
    lines = [l.strip() for l in c.split("\n") if l.strip() and not NOISE.search(l)]
    txt = " ".join(lines); txt = esc(txt)
    if split_items:
        txt = re.sub(r'(\))\s+(?=[가-힣])', r'\1<br>', txt)
        txt = re.sub(r'(★+)\s+(?=[가-힣])', r'\1<br>', txt)
        txt = re.sub(r'\s+(?=\d+\.\s)', r'<br>', txt)
        txt = re.sub(r'\s+(?=[①-⑩])', r'<br>', txt)
    return txt.strip()

def page_title(pg):
    lines = [l.strip() for l in pg.get_text().split("\n") if l.strip() and not NOISE.search(l)]
    return lines[0][:60] if lines else ""

def good_tables(pg):
    try:
        tabs = pg.find_tables().tables
    except Exception:
        return []
    res = []
    for tb in tabs:
        rows = tb.extract()
        if not rows:
            continue
        ncol = max(len(r) for r in rows)
        rows = [r + [""] * (ncol - len(r)) for r in rows]
        keep = [j for j in range(ncol) if any((rows[i][j] or "").strip() for i in range(len(rows)))]
        rows = [[r[j] for j in keep] for r in rows]
        rows = [r for r in rows if any((c or "").strip() for c in r)]
        if len(rows) >= 2 and len(rows[0]) >= 2:
            res.append(rows)
    return res

def tableize(pg, pnum):
    try:
        tabs = pg.find_tables().tables
    except Exception:
        tabs = []
    if not tabs:
        return None
    out = []
    for tb in tabs:
        rows = tb.extract()
        if not rows:
            continue
        ncol = max(len(r) for r in rows)
        rows = [r + [""] * (ncol - len(r)) for r in rows]
        keep = [j for j in range(ncol) if any((rows[i][j] or "").strip() for i in range(len(rows)))]
        rows = [[r[j] for j in keep] for r in rows]
        rows = [r for r in rows if any((c or "").strip() for c in r)]
        if not rows:
            continue
        hdr = " ".join((c or "") for c in rows[0])
        ito = ("입력물" in hdr and "산출물" in hdr)
        thtml = '<table>\n'
        if ito and len(rows) >= 2:
            thtml += '  <tr>' + "".join(f'<th>{clean_cell(c)}</th>' for c in rows[0]) + '</tr>\n'
            merged = []
            for j in range(len(rows[0])):
                col = " ".join((rows[i][j] or "").replace("\n", " ") for i in range(1, len(rows)) if j < len(rows[i]))
                merged.append(clean_cell(col, split_items=True))
            thtml += '  <tr>' + "".join(f'<td style="vertical-align:top;">{m}</td>' for m in merged) + '</tr>\n'
        else:
            for i, r in enumerate(rows):
                tag = "th" if i == 0 else "td"
                cells = "".join(f'<{tag}>{clean_cell(c, split_items=(i > 0))}</{tag}>' for c in r)
                thtml += f'  <tr>{cells}</tr>\n'
        thtml += '</table>'
        out.append(thtml)
    if not out:
        return None
    title = esc(re.sub(r'^\d+\.\s*', '', page_title(pg)))
    cap = f'<p style="font-size:0.8rem;color:#64748b;margin:10px 0 6px;">▸ 원본 p.{pnum} 표: {title}</p>'
    return cap + "\n" + "\n".join(out)

def textize(pg, pnum, with_caption=True):
    lines = [l.strip() for l in pg.get_text().split("\n") if l.strip() and not NOISE.search(l)]
    drop = {"출제 예상문제", "출제예상문제", "해설", "출제 예상문제 & 기출 문제", "문제 풀이",
            "(정답) 강의 해설 참조", "핵심 기출 & 출제 예상문제", "토픽 핵심 요약정리", "끝"}
    lines = [l for l in lines if l not in drop and not re.fullmatch(r'\(정답\).{0,3}', l)]
    if not lines:
        return None
    title = esc(re.sub(r'^\d+\.\s*', '', lines[0][:60]))
    rest = lines[1:] if with_caption else lines
    paras = []; cur = ""
    for l in rest:
        if re.match(r'^([①-⑩]|\d+[\.\)]|[가-힣]\.|[IVXⅠ-Ⅹ]+\s*\.\s?)', l):
            if cur:
                paras.append(cur)
            cur = l
        else:
            cur = (cur + " " + l).strip()
    if cur:
        paras.append(cur)
    ps = "".join(f'<p>{esc(x)}</p>' for x in paras)
    if with_caption:
        cap = f'<p style="font-size:0.8rem;color:#64748b;margin:10px 0 6px;">▸ 원본 p.{pnum}: {title}</p>'
        return cap + "\n" + ps
    return ps

def classify(pg):
    t = pg.get_text(); tl = len(re.sub(r'\s', '', t))
    gt = good_tables(pg)
    bigimg = any((im[2] or 0) * (im[3] or 0) > 200000 for im in pg.get_images())
    ttext = sum(len(re.sub(r'\s', '', (c or ""))) for rows in gt for r in rows for c in r)
    if gt and ttext >= 0.45 * max(tl, 1) and ttext >= 80:
        return "TABLE"
    # 객관식 문제(①②③④) 페이지는 보기 텍스트가 짧아도 반드시 텍스트로 보존(퀴즈 뱅크와 별개로 본문에도)
    if '①' in t and '②' in t and tl >= 40:
        return "TEXT"
    # 다이어그램(도형+라벨) 페이지는 문장이 아니라 짧은 라벨 조각들이 많음 -> 평균 줄 길이로 구분
    lines = [l for l in t.split('\n') if l.strip()]
    avglen = sum(len(l) for l in lines) / max(len(lines), 1)
    if tl >= 220 and not bigimg and avglen >= 14:
        return "TEXT"
    return "DIAGRAM"

def render_page(pg, pnum, figdir, code):
    cls = classify(pg)
    if cls == "TABLE":
        blk = tableize(pg, pnum)
        if blk:
            return blk
    if cls == "TEXT":
        blk = textize(pg, pnum)
        if blk:
            return blk
    # DIAGRAM(또는 표/텍스트 추출 실패) -> 원본 페이지 렌더링
    os.makedirs(figdir, exist_ok=True)
    fn = "p%03d.jpg" % pnum
    fpath = os.path.join(figdir, fn)
    if not os.path.exists(fpath):
        pix = pg.get_pixmap(dpi=150)
        im = Image.open(io.BytesIO(pix.tobytes("png"))).convert("RGB")
        im.thumbnail((1400, 2000))
        im.save(fpath, "JPEG", quality=82)
    rel = "assets/%sfig/%s" % (code, fn)
    return ('<figure class="fig"><img loading="lazy" src="%s" alt="원본 p.%d">'
            '<figcaption>📄 원본 슬라이드 p.%d</figcaption></figure>' % (rel, pnum, pnum))

NUMPAT = re.compile(r'^(\d{1,2})\.\s*(\S.{0,26})$')

# ---------- 주제 경계 분할 ----------
def build_sections(pdf_path, code, figdir, skip_pages=()):
    d = fitz.open(pdf_path)
    sections = []
    cur = None
    for i in range(d.page_count):
        pno = i + 1
        if pno in skip_pages:
            continue
        pg = d[i]; t = pg.get_text()
        ml = mlines(t)
        if not ml:
            continue
        # '토픽 핵심 요약정리' 표지가 제목 앞/뒤 어느 쪽에도 올 수 있어 앞 3줄 안에서 탐색
        newtopic = False; topic_title = None; subhead = None
        for j in range(min(3, len(ml))):
            if has_marker(ml[j]):
                newtopic = True
                if j - 1 >= 0 and not has_marker(ml[j - 1]):
                    topic_title = ml[j - 1]
                elif j + 1 < len(ml) and not has_marker(ml[j + 1]):
                    topic_title = ml[j + 1]
                if j + 1 < len(ml) and ml[j + 1] != topic_title:
                    cand = ml[j + 1]
                    if re.match(r'^\s*(\[참고\]|[IVXⅠ-Ⅹ]+\s*\.\s?|\d+\s*\.\s?)', cand):
                        subhead = cand[:70]
                break
        # '토픽 핵심 요약정리' 표지가 없는 강좌(소프트웨어공학 등)는 "N. 토픽명" 형태의
        # 반복되는 러닝헤더로 주제 경계를 판단(퀴즈 문항 첫 줄과 헷갈리지 않도록 문장부호 제외)
        if not newtopic:
            for j in range(min(2, len(ml))):
                m = NUMPAT.match(ml[j])
                if (m and not re.search(r'[?".,]', m.group(2))
                        and not re.fullmatch(r'[A-Z]{2,6}', m.group(2))):  # "4. BAM" 같은 워터마크성 표기 제외
                    newtopic = True; topic_title = m.group(0)[:60]
                    break
        if is_cover(t) and not newtopic:
            continue
        if newtopic and topic_title:
            tnorm = re.sub(r'\s', '', topic_title)
            prev_tnorm = re.sub(r'\s', '', cur["title"]) if cur else None
            if cur is not None and tnorm == prev_tnorm:
                pass  # 같은 주제가 이어짐(중간에 기출/해설 페이지가 끼어든 경우) -> 새 섹션 만들지 않고 이어붙임
            else:
                cur = {"title": topic_title[:60], "pages": [], "subs": {}}
                sections.append(cur)
        if cur is None:
            cur = {"title": ml[0][:60], "pages": [], "subs": {}}
            sections.append(cur)
        cur["pages"].append(pno)
        if subhead:
            cur["subs"][pno] = subhead
    out = []
    for sec in sections:
        blocks = []
        last_sub = None
        for p in sec["pages"]:
            sh = sec["subs"].get(p)
            if sh and sh != last_sub:
                blocks.append('<h3>%s</h3>' % esc(re.sub(r'^\s*\d+\s*\.\s*', '', sh)))
                last_sub = sh
            blk = render_page(d[p - 1], p, figdir, code)
            if blk:
                blocks.append(blk)
        if blocks:
            out.append({"title": sec["title"], "pages": sec["pages"], "blocks": blocks})
    return out, d.page_count

# ---------- 퀴즈뱅크 추출 (감리 _inject_quizbank.py 로직 재사용) ----------
HDR = re.compile(r'(감리사 합격을 위한 사업관리 총정리|출제 예상문제 & 기출 문제|출제 예상문제|기출 문제|'
                  r'토픽 핵심 요약정리|핵심 기출\([0-9]+\)[^\n]*|핵심 기출|해설|끝)')
CUE = ['것은?', '것은', '무엇', '고르', '옳은', '틀린', '적절', '거리가 먼', '아닌 것', '맞는', '모두 고', '바르게', '설명으로', '계산', '구하', '얼마', '짝지']
SKIP = re.compile(r'^\s*(제\s?\d+조|[IVX]+\.|\[|\(원본\)|단원|부록|별표|Chapter|Phase|Contents)')

def norm(s): return re.sub(r'\s+', ' ', s).strip()

def extract_quiz(path):
    d = fitz.open(path); P = [d[i].get_text() for i in range(d.page_count)]
    out = []
    for i, t in enumerate(P):
        if '①' not in t or '②' not in t:
            continue
        Jn = "\n".join(norm(x) for x in t.split('\n') if norm(x))
        k = Jn.find('①'); qraw = HDR.sub('', Jn[:k]).strip()
        qraw = re.sub(r'^\s*\d+\s*', '', qraw).strip()
        qraw = re.sub(r'^\s*\[[^\]]{0,20}\]\s*', '', qraw)  # "[감리 15회 99번]" 같은 출처 표기는 skip 판정에서 제외
        qraw = re.sub(r'^\s*\d+\s*', '', qraw); q = norm(qraw)
        q = re.sub(r'\s*&\s*$', '', q).strip()  # HDR 치환 잔여 기호 제거
        if SKIP.match(q):
            continue
        if not (('출제 예상문제' in t) or ('기출' in t) or any(c in q for c in CUE)):
            continue
        Js = norm(t)
        Js2 = HDR.sub(' ', Js)
        opts = re.findall(r'[①②③④⑤][^①②③④⑤]{1,220}', Js2)
        opts = [re.split(r'\(정답\)|해설|문제 풀이', o)[0] for o in opts]
        if len(opts) < 3 or len(q) < 10:
            continue
        ans = ""
        for j in (i, i + 1, i + 2):
            if j >= len(P):
                break
            m = re.search(r'\(정답\)\s*(.{0,240})', norm(P[j]))
            if m:
                ans = re.split(r'해설|문제 풀이', norm(m.group(1)))[0].strip(); break
        out.append({"page": i + 1, "q": q[:500], "opts": [norm(o)[:200] for o in opts[:5]], "ans": ans[:260]})
    seen = set(); uq = []
    for x in out:
        kk = x["q"][:26]
        if kk in seen:
            continue
        seen.add(kk); uq.append(x)
    return uq

def quizbank_section(qs):
    if not qs:
        return "", ""
    items = []
    for idx, q in enumerate(qs, 1):
        opts = "".join("<li>%s</li>" % esc(re.sub(r'^[①②③④⑤]\s*', '', o)) for o in q["opts"])
        ansdisp = esc(q["ans"]) if q["ans"] else "원문 강의자료 해설 참조"
        items.append(
            '<div class="quiz-container"><div class="quiz-header"></div>'
            '<div class="quiz-question">Q%d. %s <span style="font-weight:400;color:#94a3b8;font-size:0.8rem;">(원본 p.%d)</span></div>'
            '<ol class="quiz-options">%s</ol>'
            '<div class="quiz-explanation"><strong>정답</strong> %s</div></div>'
            % (idx, esc(q["q"]), q["page"], opts, ansdisp))
    sec = ('    <section id="allquiz" class="section">\n'
           '      <h2>📚 전체 기출·예상문제 (%d문항) — 원문 수록</h2>\n'
           '      <p>본 강좌 원본 PDF에 수록된 기출·예상문제를 <strong>빠짐없이 원문 그대로</strong> 정리했습니다. 정답·해설은 강의 원문 기준입니다.</p>\n'
           '      %s\n    </section>\n' % (len(qs), "\n      ".join(items)))
    li = '      <li data-qb="1" style="margin-top:8px;"><a href="#allquiz" style="font-weight:700;color:#b91c1c;">📚 전체 기출·예상문제 (%d)</a></li>\n' % len(qs)
    return sec, li

EXTRA_CSS = """
/* === 주제별 섹션 표준 서식(감리 강좌와 통일) === */
:root{--quiz-bg:#dcfce7;--quiz-border:#4ade80;}
.section{background:#fff;padding:40px;margin-bottom:30px;border-radius:8px;border:1px solid var(--border-color);box-shadow:0 4px 6px rgba(0,0,0,0.05);scroll-margin-top:120px;}
.section h2{color:var(--primary);border-bottom:3px solid var(--secondary);padding-bottom:10px;margin-top:0;font-size:1.45rem;}
.section h3{color:var(--primary);margin-top:28px;border-left:5px solid var(--secondary);padding:8px 12px;font-size:1.1rem;background:#f1f5f9;}
.section p{margin:8px 0;}
.section ul,.section ol{margin:8px 0 8px 22px;}
.section li{margin:4px 0;}
table{width:100%;border-collapse:collapse;margin:14px 0;font-size:0.9rem;line-height:1.5;}
th,td{border:1px solid var(--border-color);padding:9px 12px;vertical-align:top;}
th{background:var(--table-header);color:var(--primary);font-weight:bold;text-align:center;}
.fig{margin:18px 0;text-align:center;}
.fig img{max-width:620px;width:100%;border:1px solid var(--border-color);border-radius:6px;box-shadow:0 2px 6px rgba(0,0,0,0.08);}
.fig figcaption{font-size:0.8rem;color:#64748b;margin-top:6px;}
.quiz-container{border:2px solid var(--quiz-border);border-radius:8px;margin:22px 0;overflow:hidden;}
.quiz-header{background:var(--quiz-bg);padding:12px 18px;font-weight:bold;color:#166534;border-bottom:1px solid var(--quiz-border);}
.quiz-header::before{content:"📝 기출 & 예상문제  ";}
.quiz-question{padding:16px 18px;font-weight:bold;}
.quiz-options{padding:0 18px 14px 40px;}
.quiz-options li{margin-bottom:6px;}
.quiz-explanation{background:#f1f5f9;padding:16px 18px;border-top:1px dashed var(--border-color);font-size:0.92rem;}
.quiz-explanation strong{color:var(--accent);}
"""

def build(code, pdf_rel, html_rel, skip_pages=()):
    pdf_path = os.path.join(ROOT, pdf_rel)
    html_path = os.path.join(LEC, html_rel)
    figdir = os.path.join(os.path.dirname(html_path), "assets", "%sfig" % code)
    subj_dir_name = os.path.basename(os.path.dirname(html_path))

    sections, npages = build_sections(pdf_path, code, figdir, skip_pages=skip_pages)
    qs = extract_quiz(pdf_path)
    quiz_html, quiz_li = quizbank_section(qs)

    s = open(html_path, encoding="utf-8").read()

    # 1) CSS 보강
    s = s.replace("</style>", EXTRA_CSS + "</style>", 1)

    # 2) 사이드바 목차 교체
    li_items = []
    sec_ids = []
    for n, sec in enumerate(sections, 1):
        sid = "%s-t%02d" % (code.lower(), n)
        sec_ids.append(sid)
        p0 = sec["pages"][0]
        li_items.append('<li><a href="#%s"><span style="color:#94a3b8">p.%d</span> %s</a></li>' % (sid, p0, esc(sec["title"])))
    sidebar_html = "<ul>" + "".join(li_items) + quiz_li + "</ul>"
    s = re.sub(r'<h3>📑 학습 목차</h3>\s*<ul>.*?</ul>', lambda m: '<h3>📑 학습 목차</h3>\n    ' + sidebar_html, s, count=1, flags=re.S)

    # 3) 본문 교체
    body_parts = []
    for sid, sec in zip(sec_ids, sections):
        p0, p1 = sec["pages"][0], sec["pages"][-1]
        rng = "p.%d" % p0 if p0 == p1 else "p.%d-%d" % (p0, p1)
        body_parts.append(
            '<section id="%s" class="section">\n  <h2>%s <span style="font-weight:400;color:#94a3b8;font-size:0.8rem;">(원본 %s)</span></h2>\n  %s\n</section>'
            % (sid, esc(sec["title"]), rng, "\n  ".join(sec["blocks"]))
        )
    if quiz_html:
        body_parts.append(quiz_html)
    new_body = "\n".join(body_parts)
    s = re.sub(r'(<main class="content" id="content-area">\n?).*?(\n?\s*</main>)', lambda m: m.group(1) + new_body + m.group(2), s, count=1, flags=re.S)

    open(html_path, "w", encoding="utf-8").write(s)
    print("%s: %d개 주제섹션, %d페이지, 퀴즈 %d문항 -> %s" % (code, len(sections), npages, len(qs), html_rel))
    return len(sections), npages, len(qs)

if __name__ == "__main__":
    pass
