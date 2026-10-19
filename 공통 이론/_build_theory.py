# -*- coding: utf-8 -*-
# 공통 이론 MD -> 스타일 HTML 변환.  사용: python3 _build_theory.py "<파일.md>"
import sys, os, re, html as _html
import markdown

TEMPLATE = '''<!DOCTYPE html>
<html lang="ko">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>__TITLE__</title>
<style>
  :root{ --primary:#1e3a8a; --primary-dark:#0f172a; --accent:#0ea5e9; --bg:#f8fafc; --card:#fff; --border:#cbd5e1; --text:#334155; --text-dark:#0f172a; }
  *{box-sizing:border-box;margin:0;padding:0;font-family:'Pretendard',-apple-system,BlinkMacSystemFont,sans-serif;}
  body{background:var(--bg);color:var(--text);line-height:1.65;}
  .topbar{position:sticky;top:0;z-index:50;background:var(--primary-dark);color:#fff;padding:.6rem 1rem;box-shadow:0 2px 8px rgba(0,0,0,.15);display:flex;align-items:center;gap:.6rem;flex-wrap:wrap;}
  .topbar .back{font-size:.8rem;font-weight:700;color:#cbd5e1;background:#1e293b;border:1px solid #334155;border-radius:20px;padding:.3rem .8rem;text-decoration:none;white-space:nowrap;}
  .topbar .back:hover{background:#334155;color:#fff;}
  .topbar h1{font-size:1rem;font-weight:800;}
  .wrap{max-width:1180px;margin:0 auto;padding:1.3rem 1.1rem 4rem;}
  .content h1{display:none;}
  .content h2{font-size:1.12rem;color:var(--primary);font-weight:800;margin:2rem 0 .7rem;padding:.45rem .7rem;background:linear-gradient(90deg,#e0e7ff,transparent);border-left:5px solid var(--primary);border-radius:4px;}
  .content h2:first-child{margin-top:.3rem;}
  .content h3{font-size:.98rem;color:var(--text-dark);font-weight:800;margin:1.3rem 0 .45rem;padding-left:.6rem;border-left:3px solid var(--accent);}
  .content p{margin:.55rem 0;font-size:.9rem;}
  .content ul,.content ol{margin:.4rem 0 .9rem 1.3rem;font-size:.89rem;}
  .content li{margin:.28rem 0;}
  .content strong{color:var(--text-dark);font-weight:700;}
  .content blockquote{background:var(--card);border:1px solid var(--border);border-left:4px solid var(--accent);border-radius:8px;padding:.7rem 1rem;margin:.6rem 0 1rem;font-size:.86rem;color:#475569;}
  .content blockquote p{margin:.2rem 0;}
  .content code{background:#eef2ff;color:#1e3a8a;font-family:Consolas,monospace;font-size:.86em;padding:.08rem .35rem;border-radius:5px;font-weight:600;}
  .tbl-scroll{overflow-x:auto;margin:.5rem 0 1rem;border:1px solid var(--border);border-radius:10px;}
  table{border-collapse:collapse;width:100%;font-size:.82rem;background:var(--card);}
  th{background:#e2e8f0;color:#1e293b;font-weight:700;padding:.5rem .55rem;text-align:left;white-space:nowrap;border-bottom:1px solid #cbd5e1;}
  td{padding:.45rem .55rem;border-top:1px solid #e2e8f0;vertical-align:top;}
  tr:hover td{background:#f1f5f9;}
  .content a{color:var(--accent);font-weight:700;text-decoration:none;border-bottom:1px dotted var(--accent);}
  .content a:hover{background:#e0f2fe;}
  /* 기출문항 링크(새 탭) 버튼화 */
  a.examlink{display:inline-block;background:#e2e8f0;color:#1e293b;border:1px solid #cbd5e1;border-bottom:1px solid #cbd5e1;border-radius:6px;padding:.1rem .45rem;font-size:.76rem;font-weight:700;margin:.1rem .12rem 0 0;white-space:nowrap;}
  a.examlink:hover{background:#dbeafe;border-color:#93c5fd;}
  hr{border:none;border-top:1px solid var(--border);margin:1.4rem 0;}
  @media (max-width:768px){ .wrap{padding:1rem .7rem 3rem;} .content h2{font-size:1rem;} table{font-size:.78rem;} }
</style>
</head>
<body>
<div class="topbar">
  <a class="back" href="공통이론.html">← 공통 이론 목록</a>
  <h1>__TITLE__</h1>
</div>
<div class="wrap"><div class="content">
__BODY__
</div></div>
</body>
</html>
'''

def build(md_path):
    md_text = open(md_path, encoding='utf-8').read()
    # 제목: 첫 # 헤딩
    m = re.search(r'^#\s+(.+)$', md_text, re.M)
    title = m.group(1).strip() if m else os.path.splitext(os.path.basename(md_path))[0]
    body = markdown.markdown(md_text, extensions=['tables', 'fenced_code', 'sane_lists'])
    # 표를 스크롤 컨테이너로 감싸기
    body = body.replace('<table>', '<div class="tbl-scroll"><table>').replace('</table>', '</table></div>')
    # 기출문항 링크(../과목/...html#q..) 새 탭 + 버튼 클래스
    body = re.sub(r'<a href="(\.\./[^"]+\.html#q\d+)">', r'<a class="examlink" href="\1" target="_blank" rel="noopener">', body)
    out = TEMPLATE.replace('__TITLE__', _html.escape(title)).replace('__BODY__', body)
    out_path = os.path.splitext(md_path)[0] + '.html'
    open(out_path, 'w', encoding='utf-8').write(out)
    print('OK', out_path, '(title:', title, ')')
    return out_path

if __name__ == '__main__':
    for p in sys.argv[1:]:
        build(p)
