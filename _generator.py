#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import re, sys, html
import markdown

MD_EXT = ['tables', 'nl2br', 'fenced_code', 'sane_lists']
AREA1 = ['문제', '보기', '정답', '핵심 키워드', '문제 정보']
AREA2 = ['정답 해설', '오답 분석', '관련 이론 정리', '실무 적용 사례', '감리사 시험 출제 포인트']
AREA3 = ['매칭 강의자료', '출제패턴 분석', '유사문제', '빈출도 분석', '암기 포인트']
KNOWN = set(AREA1 + AREA2 + AREA3)

def md2html(text):
    return markdown.markdown(text.strip(), extensions=MD_EXT)

def parse_md(md_text):
    lines = md_text.split('\n')
    q_indices = [i for i, l in enumerate(lines) if re.match(r'^#\s+문항\s+\d+', l)]
    intro = '\n'.join(lines[:q_indices[0]]).strip() if q_indices else md_text
    questions = []
    for idx, start in enumerate(q_indices):
        end = q_indices[idx + 1] if idx + 1 < len(q_indices) else len(lines)
        block = lines[start:end]
        num = int(re.match(r'^#\s+문항\s+(\d+)', block[0]).group(1))
        sections, cur_title, cur_buf = [], None, []
        for l in block[1:]:
            m = re.match(r'^##\s+(.+?)\s*$', l)
            if m:
                if cur_title is not None:
                    sections.append((cur_title, '\n'.join(cur_buf).strip()))
                cur_title, cur_buf = m.group(1).strip(), []
            else:
                cur_buf.append(l)
        if cur_title is not None:
            sections.append((cur_title, '\n'.join(cur_buf).strip()))
        sec_map, extra = {}, []
        for t, c in sections:
            if t in KNOWN:
                sec_map[t] = c
            else:
                extra.append((t, c))
        questions.append({'num': num, 'sec': sec_map, 'extra': extra})
    return intro, questions

def render_section(title, content):
    if content is None:
        return ''
    return ('<div class="content-section"><div class="section-label">'
            + html.escape(title) + '</div><div class="section-text">'
            + md2html(content) + '</div></div>')

def render_options_section(content):
    body = md2html(content)
    return ('<div class="content-section"><div class="section-label">보기'
            '<label class="ans-switch" title="정답 보기">'
            '<input type="checkbox" onchange="toggleAns(this)">'
            '<span class="track"></span><span class="switch-text">정답 보기</span></label>'
            '</div><div class="section-text opts">' + body + '</div></div>')

def render_answer_section(content):
    body = md2html(content)
    return ('<div class="content-section answer-box"><div class="section-label">정답</div>'
            '<div class="section-text">' + body + '</div></div>')

def build_area(order, sec_map, extra=None):
    parts = []
    for n in order:
        if n not in sec_map:
            continue
        if n == '보기':
            parts.append(render_options_section(sec_map[n]))
        elif n == '정답':
            parts.append(render_answer_section(sec_map[n]))
        else:
            parts.append(render_section(n, sec_map[n]))
    if extra:
        parts += [render_section(t, c) for t, c in extra]
    return '\n'.join(parts)

def build_question_html(q):
    a1 = build_area(AREA1, q['sec'])
    a2 = build_area(AREA2, q['sec'], q['extra'])
    a3 = build_area(AREA3, q['sec'])
    num = q['num']
    left = ('<div class="merge-divider"></div>'.join([a1, a3]) if a3 else a1)
    return (
        '\n    <div class="question-view" data-num="' + str(num) + '" style="display:none;">'
        '\n      <div class="content-workspace">'
        '\n        <div class="area-card area-left"><div class="area-header">영역 1 · 문제 / 보기 / 정답 · 강의 연계 / 빈출도 / 암기</div><div class="area-body">' + left + '</div></div>'
        '\n        <div class="area-card area-2"><div class="area-header">영역 2 · 정답 해설 / 오답 분석 / 이론</div><div class="area-body">' + a2 + '</div></div>'
        '\n      </div>\n    </div>')

PAGE = '''<!DOCTYPE html>
<html lang="ko">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>__TITLE__</title>
<style>
:root {
  --primary-color:#1e3a8a; --accent-color:#0ea5e9; --border-color:#cbd5e1;
  --bg-main:#f8fafc; --text-main:#334155; --text-dark:#0f172a; --area-bg:#ffffff;
  --area-shadow:0 4px 6px -1px rgb(0 0 0 / 0.1);
}
* { box-sizing:border-box; margin:0; padding:0; font-family:'Pretendard',-apple-system,sans-serif; }
html,body { height:100%; }
body { background:var(--bg-main); color:var(--text-main); display:flex; flex-direction:column; height:100vh; overflow:hidden; }

.page-header { background:#fff; border-bottom:1px solid var(--border-color); padding:0.7rem 1.25rem 0.7rem 3.2rem; display:flex; align-items:center; gap:1rem; flex-shrink:0; flex-wrap:wrap; }
.page-title { font-size:1rem; font-weight:800; color:var(--text-dark); }
.page-title small { display:block; font-size:0.72rem; color:#64748b; font-weight:600; margin-top:2px; }
.qnav { display:flex; align-items:center; gap:0.4rem; margin-left:auto; }
.qselect { padding:0.45rem 0.6rem; font-size:0.82rem; font-weight:700; border-radius:6px; border:1px solid var(--border-color); background:#fff; color:var(--text-dark); cursor:pointer; max-width:180px; }
.qnav .btn { padding:0.45rem 0.9rem; font-size:0.82rem; font-weight:700; border-radius:6px; cursor:pointer; border:1px solid var(--border-color); background:#fff; color:var(--text-main); }
.qnav .btn:hover { background:#f1f5f9; }
.qnav .btn-primary { background:var(--primary-color); color:#fff; border-color:var(--primary-color); }

.stage { flex:1; overflow:hidden; padding:1rem; min-height:0; }
.question-view { height:100%; min-height:0; }
.content-workspace { display:grid; grid-template-columns:1fr 1fr; grid-template-rows:1fr; gap:1rem; height:100%; min-height:0; }
.area-card { background:var(--area-bg); border:1px solid var(--border-color); border-radius:8px; box-shadow:var(--area-shadow); display:flex; flex-direction:column; overflow:hidden; min-height:0; }
.area-left { grid-column:1/2; grid-row:1/2; }
.area-2 { grid-column:2/3; grid-row:1/2; }
.area-header { padding:0.55rem 1rem; background:#f8fafc; border-bottom:1px solid var(--border-color); font-size:0.78rem; font-weight:800; color:var(--primary-color); letter-spacing:0.03em; flex-shrink:0; }
.area-body { padding:1.1rem; overflow-y:auto; flex:1; min-height:0; font-size:0.9rem; line-height:1.65; }
.merge-divider { border-top:2px solid var(--border-color); margin:1.1rem 0; }

.overview-view { height:100%; overflow-y:auto; padding:0; }
.overview-card { background:#fff; border:1px solid var(--border-color); border-radius:8px; box-shadow:var(--area-shadow); padding:1.5rem 2rem; max-width:1100px; margin:0 auto; }

.content-section { margin-bottom:1.25rem; border-bottom:1px dashed #e2e8f0; padding-bottom:1rem; }
.content-section:last-child { margin-bottom:0; border-bottom:none; padding-bottom:0; }
.section-label { font-weight:800; font-size:0.88rem; color:var(--text-dark); margin-bottom:0.5rem; display:flex; align-items:center; gap:0.4rem; }
.section-label::before { content:''; display:inline-block; width:3.5px; height:13px; background:var(--accent-color); border-radius:2px; }
.section-text { color:var(--text-main); }
.section-text p { margin:0.4rem 0; }
.section-text ul, .section-text ol { margin:0.4rem 0 0.4rem 1.25rem; }
.section-text li { margin:0.2rem 0; }
.section-text h3 { font-size:0.9rem; color:var(--text-dark); margin:0.7rem 0 0.3rem; }
.section-text pre { background:#f1f5f9; padding:0.6rem; border-radius:5px; overflow-x:auto; font-family:monospace; font-size:0.82rem; }
.section-text code { background:#f1f5f9; padding:0.1rem 0.3rem; border-radius:3px; font-size:0.85em; }
table { width:100%; border-collapse:collapse; margin:0.6rem 0; font-size:0.82rem; }
th,td { border:1px solid var(--border-color); padding:0.45rem 0.65rem; text-align:left; vertical-align:top; }
th { background:#f1f5f9; color:var(--text-dark); font-weight:700; }
strong { color:#0f172a; font-weight:700; }

.ans-switch { margin-left:auto; display:inline-flex; align-items:center; gap:0.4rem; cursor:pointer; font-size:0.72rem; font-weight:700; color:#64748b; user-select:none; }
.ans-switch input { display:none; }
.ans-switch .track { width:34px; height:18px; background:#cbd5e1; border-radius:999px; position:relative; transition:background .2s; flex-shrink:0; }
.ans-switch .track::after { content:''; position:absolute; top:2px; left:2px; width:14px; height:14px; background:#fff; border-radius:50%; transition:transform .2s; }
.ans-switch input:checked + .track { background:var(--accent-color); }
.ans-switch input:checked + .track::after { transform:translateX(16px); }
.ans-switch input:checked ~ .switch-text { color:var(--accent-color); }
.opts strong { font-weight:normal; color:inherit; }
.answer-box { display:none; }
.question-view.show-answer .opts strong { font-weight:700; color:#0f172a; }
.question-view.show-answer .answer-box { display:block; }
</style>
</head>
<body>
  <div class="page-header">
    <div class="page-title">__SUBJECT__ <small>__YEAR__년도 기출해설집 · 총 __COUNT__문항</small></div>
    <div class="qnav">
      <select class="qselect" id="qselect" onchange="jump(this.value)" title="문항 바로가기"></select>
      <button class="btn" onclick="go(-1)">← 이전</button>
      <button class="btn btn-primary" onclick="go(1)">다음 →</button>
    </div>
  </div>
  <div class="stage" id="stage">
    <div class="overview-view question-view" data-num="overview" style="display:none;">
      <div class="overview-card"><div class="section-text">__INTRO__</div></div>
    </div>
__QUESTIONS__
  </div>
<script>
  const views = Array.from(document.querySelectorAll('.question-view'));
  const nums = views.map(function(v){ return v.dataset.num; });
  const select = document.getElementById('qselect');
  let cur = 0;
  views.forEach(function(v, i){
    const o = document.createElement('option');
    o.value = i;
    o.textContent = nums[i] === 'overview' ? '개요·정답표' : (nums[i] + '번');
    select.appendChild(o);
  });
  function show(i){
    if (i < 0 || i >= views.length) return;
    views[cur].style.display = 'none';
    cur = i;
    views[cur].style.display = 'block';
    select.value = i;
    views[cur].querySelectorAll('.area-body, .overview-view').forEach(function(b){ b.scrollTop = 0; });
  }
  function go(d){ show(cur + d); }
  function jump(v){ show(parseInt(v, 10)); }
  function toggleAns(cb){
    const v = cb.closest('.question-view');
    if (v) v.classList.toggle('show-answer', cb.checked);
  }
  show(nums[0] === 'overview' ? 1 : 0);
</script>
</body>
</html>'''

def generate(md_path, subject, year, out_path):
    with open(md_path, encoding='utf-8') as f:
        md_text = f.read()
    intro, questions = parse_md(md_text)
    questions.sort(key=lambda q: q['num'])
    q_html = '\n'.join(build_question_html(q) for q in questions)
    page = (PAGE
            .replace('__TITLE__', html.escape(subject) + ' ' + str(year) + '년도 기출해설집')
            .replace('__SUBJECT__', html.escape(subject))
            .replace('__YEAR__', str(year))
            .replace('__COUNT__', str(len(questions)))
            .replace('__INTRO__', md2html(intro))
            .replace('__QUESTIONS__', q_html))
    with open(out_path, 'w', encoding='utf-8') as f:
        f.write(page)
    print('OK ' + out_path + ' (' + str(len(questions)) + ')')

if __name__ == '__main__':
    generate(sys.argv[1], sys.argv[2], sys.argv[3], sys.argv[4])
