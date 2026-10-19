# 강좌 교재 HTML 표준 양식 가이드 (양산용)

이 문서는 강좌 PDF를 HTML로 변환해 **학습사이트 랜딩페이지(index.html)의 콘텐츠 iframe**에 연결하기 위한 표준 규칙입니다.
샘플 `IS_Auditor_Study_Material_Interactive_Final.html` 을 기준으로 하며, 나머지 PDF도 **아래 규칙만 지키면** 그대로 연결됩니다.

---

## 1. 폴더·파일 배치 규칙

```
3. 학습사이트/
├─ index.html                 ← 랜딩페이지(수정 완료)
└─ 강좌/
   ├─ 감리및사업관리/
   │   ├─ M01_정보화법제도_전자정부법.html   ← 변환 완료(샘플)
   │   ├─ M02_감리법지침.html
   │   └─ ...
   ├─ 소프트웨어공학/   (SE01_... ~ SE07_...)
   ├─ 데이터베이스/     (DB00_... ~ DB07_...)
   ├─ 시스템구조/       (SA01_..., SA02_...)
   └─ 보안/             (SEC00_... ~ SEC09_...)
```

- 폴더명 = 과목 slug(공백 없음): `감리및사업관리 / 소프트웨어공학 / 데이터베이스 / 시스템구조 / 보안`
- 파일명 = index.html의 `courses[].lectures[].file` 값과 **정확히 일치**해야 함(대소문자·언더스코어 포함).
- 파일명 목록은 index.html `<script>` 의 `lectures` 배열에 이미 정의되어 있음. 새 강좌를 추가할 때는 그 배열에 항목을 넣고 `ready: true` 로 바꾸면 즉시 "열람"으로 표시됨.

---

## 2. HTML 필수 요건 (Gemini/변환 도구에 지시할 사항)

### (필수 A) 자체 완결형(self-contained) 1개 파일
- 모든 CSS·JS를 **파일 내부에 인라인**으로 둘 것. 외부 CDN·별도 .css/.js 로드 금지(오프라인·GitHub Pages·iframe 모두에서 안정적으로 동작).
- 문자 인코딩: `<meta charset="UTF-8">`, `<html lang="ko">`.

### (필수 B) 임베드(iframe) 대응 2줄 — **가장 중요**
샘플에는 상단에 GitHub Pages로 가는 `top-nav`(외부 링크)가 있음. 랜딩페이지 iframe 안에서 열릴 때는 **랜딩페이지가 이미 내비게이션을 제공**하므로 이 상단바를 숨겨야 함. 아래를 그대로 포함하면 **단독 실행 시엔 상단바 표시, iframe 임베드 시엔 자동 숨김**이 되어 두 상황 모두 지원됨.

`</style>` 바로 앞에 삽입:
```css
        /* === 임베드(iframe) 대응 === */
        html.embedded { font-size: 14.5px; }                 /* 기출 해설집과 본문 크기 통일 */
        html.embedded .top-nav { display: none !important; }
        html.embedded .header { top: 0 !important; }
        /* 사이드바 sticky 오프셋은 헤더 실측 높이로 JS가 동적 설정(--embed-hdr) */
        html.embedded .sidebar { top: var(--embed-hdr, 92px); max-height: calc(100vh - var(--embed-hdr, 92px) - 20px); }
        /* 헤더 한 줄 컴팩트(타이틀·버튼 축소) */
        html.embedded .header { padding: 5px 12px; gap: 8px; }
        html.embedded .header-title { font-size: 0.92rem; }
        html.embedded .toggle-btn { padding: 3px 8px; font-size: 0.78rem; }
        html.embedded .control-group { padding: 3px 8px; font-size: 0.78rem; gap: 5px; }
        html.embedded .control-group input { padding: 2px 6px; font-size: 0.76rem; }
        html.embedded .control-group input[type="number"] { width: 58px; }
        html.embedded .control-group input[type="text"] { width: 108px; }
        html.embedded .control-group button { padding: 2px 8px; }
        /* 목차를 본문 좌측에 고정(상단 적층 방지), 매우 좁을 때만 상단으로 */
        html.embedded .container { flex-direction: row; gap: 20px; margin: 16px auto; padding: 0 16px; }
        html.embedded .sidebar { position: sticky; margin-bottom: 0; }
        /* 폭·flex 는 '접히지 않은' 경우에만 → ☰ 목차 접으면 본문이 넓어짐 */
        html.embedded .sidebar:not(.hidden) { width: auto; flex: 0 0 210px; }
        html.embedded.chrome-hidden .header { display: none !important; }   /* '본문 넓게' 스위치 ON */
        @media (max-width: 640px) {
            html.embedded .container { flex-direction: column; }
            html.embedded .sidebar:not(.hidden) { position: static; width: 100%; flex: none; max-height: none; margin-bottom: 16px; }
        }
```
> 랜딩페이지 상단의 **‘본문 넓게’ 스위치**가 `postMessage({type:'lecture-chrome', show:false})` 를 보내면 강좌는 `chrome-hidden` 클래스로 헤더를 접어 본문을 넓힌다. 아래 스크립트가 이 메시지를 처리한다.
> - `font-size: 14.5px` : 기출 해설집(본문 ≈14.4px)과 강좌 본문 크기를 통일. 강좌 원본이 다른 기본 크기를 쓰면 이 값으로 root를 맞춰 시각적 통일성 확보.
> - `.sidebar { top: var(--embed-hdr) }` : sticky 헤더는 좁은 iframe 폭에서 **줄바꿈되며 높이가 달라진다.** 고정값을 주면 헤더가 그보다 커질 때 목차 상단을 덮으므로, 아래 스크립트가 헤더 실측 높이를 측정해 `--embed-hdr` 변수로 오프셋을 자동 설정한다(겹침 방지).

`</body>` 바로 앞에 삽입:
```html
    <script>
        if (window.self !== window.top) {
            document.documentElement.classList.add('embedded');
            // 헤더 줄바꿈으로 높이가 달라져도 목차가 헤더에 가리지 않도록 오프셋을 실측·동기화
            var syncHeaderOffset = function () {
                var hdr = document.querySelector('.header');
                if (!hdr) return;
                var h = Math.ceil(hdr.getBoundingClientRect().height);
                document.documentElement.style.setProperty('--embed-hdr', (h + 8) + 'px');
            };
            window.addEventListener('load', syncHeaderOffset);
            window.addEventListener('resize', syncHeaderOffset);
            syncHeaderOffset();
            // 랜딩페이지 '본문 넓게' 스위치 → 헤더 접기/펴기
            window.addEventListener('message', function (e) {
                var d = e.data || {};
                if (d && d.type === 'lecture-chrome') {
                    document.documentElement.classList.toggle('chrome-hidden', d.show === false);
                    setTimeout(syncHeaderOffset, 40);
                }
            });
        }
    </script>
```

> 참고: `.header { top: 45px }` 처럼 상단바 높이만큼 오프셋을 준 sticky 헤더가 있으면, 위의 `html.embedded .header { top:0 }` 이 그 오프셋을 제거해 준다. 다른 sticky 오프셋이 있으면 동일 패턴으로 `html.embedded ...` 규칙을 추가.

### (필수 C) 상단바 링크는 상대경로 권장
`top-nav` 를 유지한다면 외부 절대 URL 대신 랜딩페이지 상대경로(`../../index.html`)로 두는 것을 권장(임베드 시엔 어차피 숨겨지지만 단독 실행 시 안전).

### (필수 D) 전역 검색·이동 연동 — **모든 `<section>` 에 고유 id**
랜딩페이지 상단의 **전체 강좌 검색**은 각 강좌를 미리 스캔한 색인(`search-index.js`)을 사용한다. 검색 결과를 클릭하면 해당 강좌를 iframe 으로 열면서 **정확한 섹션으로 스크롤 + 키워드 하이라이트**한다. 이를 위해 다음 두 가지가 반드시 지켜져야 한다.

1. **본문의 모든 `<section>` 에 고유 `id` 부여** (예: `<section id="ch2-3">`). 색인은 이 `id` 를 스크롤 목표로 사용한다. id 가 없으면 그 섹션은 검색 결과의 정확 위치 이동이 되지 않는다.
2. **샘플의 기능 `<script>` 블록을 그대로 유지.** 이 블록에는 검색어를 하이라이트하는 `doHighlight()` 와, 랜딩페이지에서 넘어온 위치로 이동시키는 `externalGoto()` / `parseNavHash()` / `hashchange` · `message` 리스너가 포함돼 있다. 이 부분을 삭제하면 전역 검색의 "위치 이동"이 작동하지 않는다.

동작 방식(참고): 랜딩페이지는 강좌를 열 때 URL 해시 `#sec=<섹션id>&q=<키워드>` 를 전달하고, 이미 열려 있으면 `postMessage({type:'lecture-goto', id, q})` 를 보낸다. 강좌 스크립트가 이를 받아 스크롤·하이라이트한다.

> ⚠️ 새 강좌를 추가/수정했으면 **반드시 `강좌/_build_search_index.py` 를 다시 실행**해 `search-index.js` 를 갱신해야 검색에 편입된다.

### (권장 D) 문서 자체 기능 유지
샘플이 제공하는 아래 기능은 iframe 안에서도 잘 동작하므로 유지 권장:
- 좌측 **학습 목차(사이드바 TOC)** + `☰ 목차` 토글
- **본문 검색·하이라이트**
- **가상 페이지 이동**(스크롤 기반)

### (권장 E) 콘텐츠 구조
- 섹션은 `<h2>`/`<h3>` 로 나누고, 목차 링크 대상엔 `id` 부여(예: `<h3 id="ch1-1-1">`).
- 표·퀴즈 등은 샘플의 클래스(`.quiz-bg`, 테이블 스타일 등)를 재사용하면 톤이 통일됨.
- 원문(PDF) 내용은 **축약·왜곡 없이** 담되, 학습 편의를 위한 표/강조/퀴즈 가공은 허용.

---

## 3. 랜딩페이지 연결 방식 (이미 구현됨 — 참고용)

`index.html` 의 `courses[].lectures[]` 각 항목:
```js
{ title: "M02. 감리 법·지침 개요", file: "M02_감리법지침.html", ready: false }
```
- `ready: false` → 사이드바에 "준비중" 태그, 클릭 시 안내 화면.
- 변환 완료 후 `ready: true` 로 바꾸면 → "열람" 태그, 클릭 시 `강좌/<slug>/<file>` 을 iframe 에 로드.
- 로더는 기출·강좌 공용 함수 `selectContent()` 사용.

즉 **새 강좌 양산 절차**:
1. 위 규칙(필수 A·B·C·D)대로 HTML 생성 — 특히 모든 `<section>` 에 고유 `id`
2. `강좌/<과목slug>/` 에 정해진 파일명으로 저장
3. index.html 의 해당 `lectures` 항목 `ready` 를 `true` 로 변경
4. `강좌/_build_search_index.py` 실행 → `search-index.js` 갱신(전체 검색 편입)
5. 끝 — 랜딩페이지에서 즉시 열람·검색 가능

---

## 4. 검증 체크리스트

- [ ] 파일이 `강좌/<slug>/<정확한 파일명>` 에 있는가
- [ ] `<meta charset="UTF-8">` 및 한글 정상 표시(UTF-8)
- [ ] `html.embedded` CSS(폰트·상단바·헤더·사이드바) + 감지/오프셋 동기화 스크립트 포함
- [ ] 모든 `<section>` 에 고유 `id` 부여(전역 검색 위치 이동용)
- [ ] 샘플 기능 스크립트(`doHighlight`/`externalGoto`/`hashchange`·`message`) 유지
- [ ] 강좌 추가/수정 후 `_build_search_index.py` 실행하여 `search-index.js` 갱신
- [ ] 외부 CDN·별도 파일 로드 없음(자체 완결형)
- [ ] index.html `lectures[].file` 파일명과 일치, `ready:true`
- [ ] 랜딩페이지에서 클릭 시 iframe 로드되고 상단 외부바가 숨겨지는가
