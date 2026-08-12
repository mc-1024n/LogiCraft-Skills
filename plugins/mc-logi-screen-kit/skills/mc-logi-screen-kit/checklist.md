# checklist.md — 화면 키트 fetcher 공통 하드룰 (예외 없음)

## READ-ONLY (절대)
- [ ] logicraft **조회 도구만** 사용: `get_item`, `list_items`, `get_neighbors`, `get_related`,
      `analyze_impact`, `get_item_schema`, `get_implementation_coverage`, `list_unimplemented`,
      `get_design_md`, `list_static_renders`, `get_static_render`, `get_wireframe_css`,
      `find_app_shell`, `find_navigation`, `find_constant`,
      `find_ui_component`, `get_logicraft_guide`
- [ ] 쓰기 도구 호출 **금지**: `create_item` / `update_item` / `register_*` / `propose_change` /
      `mark_implementation` / `upload_static_render` / `create_implementation_record` / 기타 모든 변경 도구
- [ ] 로컬 파일 시스템만 변경 (Write/Bash mkdir/mv). logicraft 상태 불변

## 다운로드 정확성
- [ ] **deferred 도구 선로드**: fetcher 세션에서 logicraft MCP 도구가 미로드(deferred)일 수 있다.
      `get_item` 외에 `get_design_md` (design.md 원문) / `list_static_renders` (목록 확인) / `get_static_render` (HTML 취득) / `get_wireframe_css` (CSS 취득) / `find_app_shell` / `find_navigation` 등을
      쓰기 전, 호출이 "도구 없음 / InputValidationError" 로 실패하면
      `ToolSearch("select:mcp__logicraft__<도구명>")` 로 먼저 로드한 뒤 호출한다.
      ★ 도구가 없다고 단정해 `get_item` 토큰 등으로 임의 대체하지 말 것 (원문 진실원을 잃는다).
- [ ] 각 ITEM 은 `get_item(project_id, ID)` 로 **전체 원본** 취득
- [ ] 원본을 가공 없이 `_raw/<ID>.json` 으로 저장: **item 객체 1개를 표준 JSON 으로** 저장
      (Bash python 이면 `json.dump`, Write 면 직렬화된 단일 JSON 문자열). MCP 래퍼
      (`[{"type":"text","text":...}]`)·persisted-output 텍스트·여러 객체를 한 파일에 이어붙이지 말 것
      — `Extra data` / `delimiter` 파싱 깨짐의 원인. **한 파일 = 단일 JSON 객체** (UTF-8, logicraft 응답 그대로)
- [ ] 응답 >30KB → Bash `python -c "import json,sys; ..."` (encoding='utf-8') 파싱,
      메인 컨텍스트로 거대 JSON 끌어오지 말 것
- [ ] 요약 .md 는 해당 타입 섹션 포맷 그대로 (ITEM 타입별 요약 구조 준수)
- [ ] frontmatter 의 version = 응답 `current_version` (정수) 정확히 기입
- [ ] last_updated_at / stale / slug 등 메타 원본값 그대로

## 버전 상태 처리
- [ ] status=NEW: 신규 생성, prev_version=null
- [ ] status=CHANGED: 재작성 + prev_version=입력값 + 변경 배너 삽입(version-tracking.md 포맷)
- [ ] status=UNCHANGED: 파일 존재 검증만. 없으면 NEW 로 격상해 생성. 있으면 건드리지 말 것
      (frontmatter synced_at 갱신도 안 함 — git diff 노이즈 방지)
- [ ] status=RETIRED: 메인이 처리(이동). fetcher 는 RETIRED 안 받음

## 요약 품질 (빈 요약 금지)
- [ ] "구현 요지" 가 코드 단위로 구체적 (클래스/함수/컴포넌트/엔드포인트)
- [ ] logicraft 값/이름/경로/타입 의역·추정 **금지**. 모르면 `⚠️ 미정 (logicraft 미기재)`
- [ ] 의존 ITEM 은 ID 로 표기 (SCREENS.md 그래프 연결용)
- [ ] 적용 ADR/NFR/CONST/GUIDE 를 "구속 제약" 에 ID 로 명시
- [ ] **상수 값 인라인**: API/SCREEN/UC/AC 요약이면 `uses_constant` 링크를 따라 해당 CONST 의
      **실제 값**을 `CONST-NNN(name=value unit)` 형태로 "적용 상수" 줄에 인라인. enum/range/default/
      임계치/토큰 같은 매직값을 **상상해서 채우지 말 것** — logicraft CONST value 원문 그대로.
      uses_constant 역링크가 없으면 "⚠️ uses_constant 미연결 — 도메인 CONST 표 확인" 으로 남김.
- [ ] CONST 요약이면 value 는 **의역·반올림·단위변환 금지**(원문 그대로). env_var+is_secret 은 값 대신 placeholder.
- [ ] 추상 일반론·마케팅 문구 금지. 구현 결정만

## 파일 경로 규약
- [ ] 요약 · 산출물 루트: `docs/screen-design/{slug}-{DOMAIN-ID}/`
- [ ] 공유 ITEM: `_shared/{type}/{ID}.md` / `_shared/{type}/_raw/{ID}.json`
- [ ] ui_component 카탈로그: `_shared/ui-catalog.md` (개별 파일 아님 — 아래 화면 특화 룰 참조)
- [ ] design_system: `_shared/design-system.md` + `_shared/_raw/DS-{ID}.json`
- [ ] app_shell + navigation_tree: `_shared/shell-nav.md`
- [ ] 화면별: `screens/{SCREEN-NNN}/{SCREEN-NNN}.md` / `screens/{SCREEN-NNN}/_raw/{SCREEN-NNN}.json`
- [ ] UC/AC: `screens/{SCREEN-NNN}/uc/{UC-NNN}.md` / `screens/{SCREEN-NNN}/ac/{AC-NNN}.md`
- [ ] RETIRED: `_retired/` 이동 (물리 삭제 절대 금지)
- [ ] mkdir -p 로 필요한 폴더 선생성
- [ ] 절대 경로 사용. 기존 파일 덮어쓰기 전 상태 확인(CHANGED 만 덮어씀)

## 화면 특화 룰 (화면 키트 고유)

### screen_spec — 와이어프레임 처리 (get_static_render + get_wireframe_css)
- [ ] `get_static_render(project_id, SCREEN-NNN)` 호출 → `renders[]` 취득
      (deferred 면 `ToolSearch("select:mcp__logicraft__get_static_render")` 선로드)
- [ ] renders 가 비어있으면(count 0): `screens/{SCREEN-NNN}/_no-wireframe.md` 플래그 파일 생성 → 3~5 건너뜀
- [ ] renders 있으면: 각 render 의 html 저장
      - surface 1개: `screens/{SCREEN-NNN}/wireframe.html`
      - 복수: `screens/{SCREEN-NNN}/wireframe-{render_id}.html`
      - html 이 null(`error: file_missing`)인 항목은 건너뛰고 SCREENS.md 에 "파일 누락" 표기
- [ ] `get_wireframe_css()` 1회 호출 → `screens/{SCREEN-NNN}/wireframe.css` 저장
      (deferred 면 `ToolSearch("select:mcp__logicraft__get_wireframe_css")` 선로드)
- [ ] 저장한 각 `wireframe*.html` 에서 `'/api/static/wireframe/wireframe.css'` → 상대 `'wireframe.css'` 치환
- [ ] 와이어프레임 HTML 의 **개발자 주석·spec 메타 텍스트는 제거하지 않는다**
      (원본 HTML 그대로 저장)

### design_system — design.md 형식 저장
- [ ] `get_design_md(DS-NNN)` 결과를 `_shared/design-system.md` 에 저장
      (design.md 형식 그대로 — 컬러·스페이싱·타이포 토큰이 포함된 포맷).
      ★ `get_design_md` 가 deferred 면 `ToolSearch("select:mcp__logicraft__get_design_md")` 로 먼저 로드.
      도구 없다고 단정해 `get_item` 토큰으로 대체하지 말 것 — design.md 원문이 토큰 진실원이다.
- [ ] raw JSON 도 병행 저장: `_shared/_raw/DS-{ID}.json`
- [ ] 토큰 이름·값 의역·재명명 금지 (get_design_md 원문 그대로)

### ui_component — 카탈로그 1파일 집약 (개별 파일 금지)
- [ ] `list_items(type=ui_component)` 전체 목록 취득 후 각 `get_item(UI-NNN)` 으로 상세 취득
- [ ] 개별 `UI-NNN.md` 파일 생성 **금지** — 반드시 `_shared/ui-catalog.md` 1파일에 집약
- [ ] ui-catalog.md 포맷: 컴포넌트 1건 = 섹션 1개 (`## UI-NNN {이름}`)
      - category / props 요약 / variants / a11y 키 포인트 / code_snippet 요약
      - 원본 raw: `_shared/_raw/{UI-NNN}.json` (개별 저장)
- [ ] ui_component 0건: `_shared/ui-catalog.md` 에 "카탈로그 비어있음" 플래그 + SCREENS.md 헤더에
      `⚠️ ui_component 카탈로그 비어있음 — implement Phase 0.5 에서 시드 필요` + DS archetype 기재

### spec 텍스트 정제 규칙 (요약 작성 시)
- [ ] 식별 기호·개발자 메모를 요약 본문에 **그대로 박지 말 것**:
      - `①`, `②`, `[Modal]`, `★`, `"그룹 N"`, `(API-NNN)` 접미사, `※ 참고` 등 — 구현 의도를 자연스러운 문장으로 기술
- [ ] 섹션 번호·메타 설명(예: "이 컴포넌트는 ~ 을 표시합니다")을 요약 첫 문장에 그대로 복붙하지 말 것
- [ ] API ID 접미사(예: `조회 (GET-/clip/list)`)를 화면 설명에 인라인하지 말 것 —
      consumes_apis 필드로 별도 기재
- [ ] 위 처리 룰 상세: krds-component-builder 의 `references/prompt-template.md` 와이어프레임 해석 #21 참조
      (KLID 프로젝트 한정; 다른 프로젝트는 SCREENS.md 내 가이드라인 참조)

### SCREENS.md 카탈로그 상태 플래그 갱신
- [ ] 각 fetch 완료 후 SCREENS.md 헤더 "공유자산 인덱스" 테이블 갱신
- [ ] CHANGED/NEW ITEM 이 있으면 SCREENS.md "변경 알림" 섹션에 ID + change_summary 1줄 추가
- [ ] ui_component 카탈로그 비어있으면 헤더에 플래그 기재 (위 참조)

## 출력 규약 (STEP-OUT)
완료 후 자유 텍스트 없이 YAML 한 블록만:

```yaml
fetcher_result:
  item_type: <type>
  domain_id: <DOMAIN-XXX>
  screens: [<SCREEN-NNN>...]         # screen_spec 처리 시만 — 처리한 화면 ID 목록
  processed:
    new: [<ID>...]
    changed: [{id: <ID>, prev: <n>, cur: <n>}...]
    unchanged_verified: [<ID>...]
    unchanged_recreated: [<ID>...]   # 파일 없어 재생성
  wireframes:
    saved: [<SCREEN-NNN>...]         # wireframe.html 저장 완료
    missing: [<SCREEN-NNN>...]       # static_render 없어 _no-wireframe.md 생성
  ui_catalog:
    count: <n>                       # ui_component 건수 (0 이면 Phase 0.5 시드 필요)
    status: <"populated"|"empty">
  failed: [{id: <ID>, reason: <...>}]
  files_written: <count>
  notes_for_main: <메인이 SCREENS.md/version-master 작성 시 알아야 할 점>
```

## 금지 안티패턴
- ❌ logicraft 쓰기 도구 호출
- ❌ 원본 JSON 의역/축약 저장 (raw 는 무가공)
- ❌ _raw 에 MCP 래퍼·persisted-output 텍스트·복수 객체 이어붙이기 (단일 JSON 객체만 — `Extra data` 깨짐 방지)
- ❌ deferred 도구를 "없음" 으로 단정해 다른 도구로 임의 대체 (먼저 `ToolSearch` 로 로드)
- ❌ UNCHANGED 파일 재작성 (git diff 오염)
- ❌ 거대 JSON 을 메인/에이전트 컨텍스트로 직접 로드 (Bash python 파싱)
- ❌ logicraft 에 없는 값 상상해서 채우기
- ❌ enum/range/default/임계치 매직값을 추정·하드코딩 (반드시 CONST value 인라인 — uses_constant 추적)
- ❌ 파일 물리 삭제 (RETIRED 도 메인이 이동만)
- ❌ \uXXXX escape 로 한글 저장 (UTF-8 그대로)
- ❌ ui_component 를 개별 파일로 분산 저장 (반드시 ui-catalog.md 1파일 집약)
- ❌ spec 텍스트의 식별 기호(① [Modal] ★ "그룹 N")·메타 설명·API ID 접미사를 요약 본문에 그대로 박기
- ❌ get_design_md 결과를 의역·요약 저장 (design.md 형식 원문 그대로)
- ❌ wireframe HTML 을 임의 변환/마크다운 변환하여 저장 (HTML 원본 그대로)
