# -*- coding: utf-8 -*-
"""
전체 강좌 검색용 색인 생성기
- 강좌/<과목slug>/*.html (밑줄로 시작하는 파일 제외)을 스캔
- 각 파일에서 <section id="..."> 단위(없으면 id 부여된 heading)로
  { id, title, text } 를 추출
- 결과를 8. 학습사이트/search-index.js 로 저장 (window.SEARCH_INDEX = {...})
  → <script src>로 로드되므로 file:// 로컬에서도 CORS 없이 동작

사용법:  python3 _build_search_index.py
새 강좌 HTML을 추가/갱신할 때마다 다시 실행하면 됨.
"""
import os, re, json, datetime, glob

BASE = os.path.dirname(os.path.abspath(__file__))          # .../8. 학습사이트/강좌
SITE = os.path.dirname(BASE)                                # .../8. 학습사이트
OUT  = os.path.join(SITE, "search-index.js")

from bs4 import BeautifulSoup

HEADING_TAGS = ["h1", "h2", "h3", "h4"]


def collapse(s):
    return re.sub(r"\s+", " ", (s or "")).strip()


def section_title(sec):
    for h in sec.find_all(HEADING_TAGS, recursive=True):
        t = collapse(h.get_text())
        if t:
            return t
    return collapse(sec.get("data-title") or sec.get("id") or "")


def extract_sections(soup):
    root = soup.find(id="content-area") or soup.body or soup
    out = []
    secs = root.find_all("section", id=True)
    if secs:
        for sec in secs:
            sid = sec.get("id")
            title = section_title(sec)
            text = collapse(sec.get_text(separator=" "))
            if text:
                out.append({"id": sid, "title": title or sid, "text": text[:1600]})
    else:
        # section이 없으면 id가 부여된 heading 단위로 대체
        for h in root.find_all(HEADING_TAGS, id=True):
            sid = h.get("id")
            title = collapse(h.get_text())
            parts = [title]
            for sib in h.find_all_next():
                if sib.name in HEADING_TAGS:
                    break
                if sib.name in ("p", "li", "td", "th", "span", "div"):
                    parts.append(collapse(sib.get_text()))
                if sum(len(x) for x in parts) > 1600:
                    break
            text = collapse(" ".join(parts))
            if text:
                out.append({"id": sid, "title": title or sid, "text": text[:1600]})
    return out


def main():
    docs = []
    for slug in sorted(os.listdir(BASE)):
        sub = os.path.join(BASE, slug)
        if not os.path.isdir(sub):
            continue
        for path in sorted(glob.glob(os.path.join(sub, "*.html"))):
            fname = os.path.basename(path)
            if fname.startswith("_"):
                continue
            with open(path, encoding="utf-8") as f:
                soup = BeautifulSoup(f.read(), "html.parser")
            sections = extract_sections(soup)
            if sections:
                docs.append({"slug": slug, "file": fname, "sections": sections})
                print(f"  [OK] {slug}/{fname}  →  섹션 {len(sections)}개")
            else:
                print(f"  [!!] {slug}/{fname}  →  추출된 섹션 없음(건너뜀)")

    payload = {"generated": datetime.date.today().isoformat(), "docs": docs}
    js = "window.SEARCH_INDEX = " + json.dumps(payload, ensure_ascii=False) + ";\n"
    with open(OUT, "w", encoding="utf-8") as f:
        f.write(js)
    total_sec = sum(len(d["sections"]) for d in docs)
    print(f"\n생성 완료: {OUT}")
    print(f"문서 {len(docs)}개 · 섹션 {total_sec}개 · 크기 {len(js):,} bytes")


if __name__ == "__main__":
    main()
