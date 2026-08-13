# summary-templates.md — 화면 키트 타입별 구현지향 요약 포맷

목표: 요약만 읽고 **바로 프론트엔드 코드 작성**이 가능해야 함. 추상 설명 X, 구현 결정 O.
원본 JSON 은 `_raw/` 에 보존되므로 요약은 "구현자가 알아야 할 것"에 집중.

기반: `mc-logi-implement-kit/summary-templates.md` 의 공통 frontmatter·골격·작성 원칙을 차용하고
화면(프론트엔드) 특화 타입 섹션을 확장한다.

---

## 공통 frontmatter (모든 타입 .md 최상단)

```yaml
---
logicraft_item: <ID>
type: <type code>
version: <current_version 정수>
last_updated_at: <ISO>
domain: <DOMAIN-ID>
project_id: <uuid>
synced_at: <ISO>
sync_session: <n>
stale: <bool>
status: <synced|NEW|CHANGED|RETIRED>
prev_version: <CHANGED 일 때만, 아니면 null>
raw: ./_raw/<ID>.json
links:                      # get_neighbors 핵심 링크만 (구현 의존 파악용)
  <link_type>: ["[[<ID>]]", ...]
---
```

> 링크 값은 **Obsidian wikilink** 로 쓴다 — 키트 루트를 볼트로 열면 화면↔API↔UC↔AC 그래프가
> 그대로 보인다. YAML flow sequence 안의 `[[ID]]` 는 **반드시 큰따옴표**로 감싼다
> (안 그러면 중첩 배열로 파싱되어 링크가 깨진다).

CHANGED 면 frontmatter 직후 변경 배너 삽입:

```markdown
> ⚠️ **CHANGED** v{prev} → v{cur} | {last_updated_at}
> change_summary: {logicraft change_summary 원문}
> 영향: 이 변경이 코드에 미치는 범위를 구현자가 직접 파악할 것 (analyze_impact 결과 있으면 인용)
```

---

## 공통 본문 골격

```markdown
# <ID> — <title>

**한 줄**: <이 ITEM 이 프론트엔드 코드로 무엇이 되는가 1줄>

## 구현 요지
<구현자가 만들 것: 컴포넌트/훅/타입/API클라이언트/라우트 단위로 구체적으로>

## 의존 (먼저/함께 구현)
<links 기반: 이 ITEM 구현에 필요한 다른 ITEM ID + 한 줄 이유>

## 구속 제약
<적용 GUIDE/CONST/ROLE — 코드가 반드시 지킬 것. ID 로 명시>

## (타입별 상세 — 아래 섹션)

## 구현 체크리스트
- [ ] <검증 가능한 구현 단위>
```

---

## design_system (DS)

저장 경로: `_shared/design-system.md`

> ★ `get_design_md(DS-NNN)` 결과를 **원문 그대로** 이 파일에 저장한다.
> 토큰 이름·값 의역·재명명 금지. design.md 형식 원문이 진실원이다.
> 요약 보충 섹션은 원문 뒤에 `---` 구분선 후 추가한다.

```markdown
---
logicraft_item: DS-NNN
type: design_system
version: <n>
last_updated_at: <ISO>
domain: <DOMAIN-ID>
project_id: <uuid>
synced_at: <ISO>
sync_session: <n>
stale: <bool>
status: <synced|NEW|CHANGED|RETIRED>
prev_version: <null|n>
raw: ./_raw/DS-NNN.json
links:
  project: ["[[<PROJECT-ID>]]"]
---

<!-- CHANGED 면 변경 배너 삽입 -->

{get_design_md 결과 원문 전체 — design.md 형식 그대로}

---

## 구현 참조 (보충)

### 토큰 요약표

> 아래 값은 get_design_md 원문에서 추출. 의역·보정 금지.

#### 컬러 토큰
| 토큰명 | 값 | 사용 맥락 |
|---|---|---|
| <token-name> | <value> | <의미> |

#### 타이포그래피 토큰
| 토큰명 | 값 | 사용 맥락 |
|---|---|---|
| <token-name> | <value> | <의미> |

#### 스페이싱 토큰
| 토큰명 | 값 | 사용 맥락 |
|---|---|---|
| <token-name> | <value> | <의미> |

#### 보더/라디우스 토큰
| 토큰명 | 값 | 사용 맥락 |
|---|---|---|
| <token-name> | <value> | <의미> |

### 구현 규칙 (예방)

- 색·간격·타이포·라디우스는 **이 파일의 토큰명만** 사용. 임의 hex / px 하드코딩 금지.
- 토큰 이름이 위 표에 없으면 `⚠️ 미정 (get_design_md 미기재)` 로 남기고 임의 추정 금지.
- 이 규칙은 mc-logi-screen-implement Phase 4 의 디자인 검증 grep 체크 대상이다.

### 구현 체크리스트
- [ ] get_design_md 원문 전체 저장 완료 (의역 없음)
- [ ] 컬러 토큰 표 추출 완료 (토큰명·값 원문 그대로)
- [ ] 스페이싱·타이포·라디우스 토큰 표 추출 완료
- [ ] 화면 구현 코드에서 이 파일 토큰 이외의 하드코딩 값 없음
```

---

## ui_component (UI) — 카탈로그 1파일

저장 경로: `_shared/ui-catalog.md`

> ★ **개별 UI-NNN.md 파일 생성 금지.** 모든 컴포넌트를 이 1파일에 집약.
> mc-logi-screen-implement Phase 4 에서 `find_ui_component` 룩업 인덱스로 사용한다.
> 원본 raw 는 컴포넌트별로 `_shared/_raw/UI-NNN.json` 에 개별 저장.

```markdown
---
type: ui_component_catalog
domain: <DOMAIN-ID>
project_id: <uuid>
synced_at: <ISO>
sync_session: <n>
catalog_count: <n>          # 0 이면 Phase 0.5 시드 필요
status: <populated|empty>
---

<!-- catalog_count=0 이면 아래 경고 블록 삽입 -->
> ⚠️ **ui_component 카탈로그 비어있음** — mc-logi-screen-implement Phase 0.5 에서 시드 필요
> DS archetype: {design_system 이름 또는 "미확인"}
> 시드 출처 후보: A) 레포 컴포넌트 코드 추출 / B) 라이브러리 표준 / C) apply_design_preset(seed_components=true)

---

# UI 컴포넌트 카탈로그

> 이 파일은 mc-logi-screen-implement Phase 4 화면 구현 시
> `find_ui_component` 룩업 인덱스로 사용한다.
> 각 섹션의 `implements_in_module_ids` 는 구현 완료 후 Phase 5 역링크에서 채운다.

## 카탈로그 인덱스

| ID | 이름 | category | variants | 비고 |
|---|---|---|---|---|
| UI-NNN | <name> | <category> | <variants 목록> | |

---

## UI-NNN {이름}

**category**: <category>
**한 줄**: <이 컴포넌트가 화면에서 하는 일 1줄>

### Props
| prop명 | 타입 | 필수 | 기본값 | 설명 |
|---|---|---|---|---|
| <prop> | <type> | <Y/N> | <default> | <설명> |

### Variants
| variant | 설명 | 시각 차이 |
|---|---|---|
| <variant> | <설명> | <diff> |

### 접근성 핵심 (a11y)
- <WCAG 항목 또는 role/aria 요약>

### code_snippet 요약
```<언어>
<logicraft code_snippet 원문 또는 핵심 발췌. 없으면 "⚠️ 미기재">
```

### 구현 역링크
- **implements_in_module_ids**: [] ← Phase 5 에서 채움 (link_ui_component_to_module 대상)

### 원본
- raw: `./_raw/UI-NNN.json`

---

<!-- 컴포넌트 수만큼 위 섹션 반복 -->
```

---

## screen_spec (SCREEN)

저장 경로: `screens/SCREEN-NNN/SCREEN-NNN.md`

> ★ **spec 텍스트 정제 규칙 (반드시 준수)**:
> - 식별 기호 `①` `②` `[Modal]` `★` `"그룹 N"` `※ 참고` 등을 요약 본문에 그대로 박지 말 것.
>   구현 의도를 자연스러운 문장으로 풀어 기술할 것.
> - 섹션 번호·메타 설명("이 컴포넌트는 ~ 을 표시합니다")을 첫 문장에 복붙하지 말 것.
> - API ID 접미사(예: `조회 (GET-/clip/list)`)를 화면 설명 인라인에 넣지 말 것 —
>   `consumes_apis` 필드에 별도 기재.
> 이 규칙을 어기면 개발자용 메타 텍스트가 UI 에 노출될 위험이 있다.

```markdown
---
logicraft_item: SCREEN-NNN
type: screen_spec
version: <n>
last_updated_at: <ISO>
domain: <DOMAIN-ID>
project_id: <uuid>
synced_at: <ISO>
sync_session: <n>
stale: <bool>
status: <synced|NEW|CHANGED>
prev_version: <null|n>
raw: ./_raw/SCREEN-NNN.json
wireframe: ./wireframe.html          # 복수면 wireframe-{render_id}.html / static_render 0건일 때만 ./_no-wireframe.md
links:
  consumes_apis: ["[[<API-NNN>]]", ...]
  required_roles: ["[[<ROLE-NNN>]]", ...]
  realizes_use_cases: ["[[<UC-NNN>]]", ...]
  acceptance: ["[[<AC-NNN>]]", ...]
---

<!-- CHANGED 면 변경 배너 삽입 -->

# SCREEN-NNN — <title>

**한 줄**: <이 화면이 사용자에게 하는 일 1줄 — 개발자 메타 아닌 기능 서술>

## 구현 요지
- 라우트 경로: <ROUTE_PATH.XXX 상수 또는 NAV 참조값. 미정이면 "⚠️ NAV 참조 필요">
- 진입 조건: required_roles=[<ROLE-NNN>...] → 권한 가드 처리 대상
- 컴포넌트 파일: `src/pages/<domain>/<ScreenName>Page.tsx` (Router.tsx lazy 등록 필요)
- 공유 자산 의존: api_endpoint=[<API-NNN>...] / constant=[<CONST-NNN>...] / role=[<ROLE-NNN>...]

## 의존 (먼저/함께 구현)
- <ITEM-ID>: <한 줄 이유>

## 구속 제약
- 적용 GUIDE: [<GUIDE-NNN>...] — <요지>
- 적용 CONST: [<CONST-NNN(name=value unit)>...] — 입력 검증·셀렉트 옵션·레이블에 사용
- 역할 가드: required_roles=[<ROLE-NNN>...] — <역할명> 만 접근 허용

## 화면 구조 (role=main 본문)

> 셸(헤더·사이드바·푸터)은 app_shell 소관 — 이 섹션에 포함하지 않는다.
> shell-nav.md 경계 참조.

| sections[] | layout | 포함 컴포넌트 (UI 카탈로그 ID) | 주요 동작 |
|---|---|---|---|
| <section name> | <grid/flex/...> | <UI-NNN (컴포넌트명)> | <트리거·바인딩 요약> |

### 섹션별 상세

#### <section name>

| 컴포넌트 | type | label | 입력/출력 | 검증 규칙 | 트리거 API |
|---|---|---|---|---|---|
| <component> | <type> | <label> | <io> | <validation> | <API-NNN> |

<!-- section 수만큼 반복 -->

## API 연동 (consumes_apis)

| API-ID | method/path | 용도 (화면 관점) | 바인딩 필드 |
|---|---|---|---|
| <API-NNN> | <METHOD /path> | <fetch/submit/...> | <UI ↔ response 필드 매핑> |

- 에러 응답 처리: <errorManager.showError 또는 인라인 처리 여부>
- 적용 상수: <CONST-NNN(name=value unit) — req/res enum·range>

## 역할/접근 제어 (required_roles)

| ROLE-ID | 역할명 | 이 화면의 노출 조건 |
|---|---|---|
| <ROLE-NNN> | <역할명> | <조건> |

## 관련 UC/AC

- 실현 유스케이스: [<UC-NNN>...] → `uc/` 폴더 참조
- 수용 기준: [<AC-NNN>...] → `ac/` 폴더 참조 (구현 완료 판단 기준)

## 와이어프레임

- 경로: `./wireframe.html` (복수면 `wireframe-{render_id}.html` / 없으면 `_no-wireframe.md` 참조)
- CSS: render 별 2-갈래 — 공통 `./wireframe.css`(get_wireframe_css, css 없는 와이어프레임용) + per-render `./{render_id}.css`(get_static_render 의 css 본문, 디자인 시안용)
- 취득 절차: fetcher 가 `get_static_render(project_id, SCREEN-NNN)` 호출 → renders[] 전체 취득 (각 render = `html` + 옵션 `css`/`css_url`).
  count 0 이면 `_no-wireframe.md` 생성. html 이 null 인 항목은 건너뛰고 "파일 누락" 표기.
  · render 에 `css` 있으면 → `{render_id}.css` 로 저장 (html 링크 이미 상대 `{render_id}.css` — 치환 불필요)
  · `css` 없으면 → 공통 css 사용: `get_wireframe_css()` 1회로 `wireframe.css` 저장 후 html 의 `/api/static/wireframe/wireframe.css` → `wireframe.css` 치환
  (공통 css render 가 하나도 없으면 `get_wireframe_css()` 생략 가능.)

> ★ brownfield 보존 메모:
> 이 화면이 1차(기존) 페이지의 **redesign/modified** 이면:
> - 1차 UI 를 보존하고 cascade 변경분만 얹는다.
> - 기존 컴포넌트를 무시하고 신규로 그리지 않는다.
> - 변경 범위: <CHANGED 배너의 change_summary 요약 또는 "⚠️ brownfield 여부 미기재">

## 구현 체크리스트
- [ ] Router.tsx 에 lazy() import + Route 추가
- [ ] ROUTE_PATH 상수 등록 (하드코딩 금지)
- [ ] required_roles 권한 가드 결선
- [ ] 각 section 컴포넌트 → ui-catalog.md 룩업 후 조립
- [ ] consumes_apis 각각 react-query 훅 연동 (response.data.error === 0 체크)
- [ ] CONST 값 사용 — 인라인 magic number 없음
- [ ] DS 토큰만 사용 — 임의 hex/px 없음
- [ ] AC 기준 충족 확인 (ac/ 폴더 참조)
- [ ] 셸 영역(헤더·사이드·푸터) 미포함 확인
```

---

## app_shell + navigation_tree (SHELL + NAV)

저장 경로: `_shared/shell-nav.md`

> ★ **화면-셸 경계 규칙**:
> - 화면(screen_spec) 은 `role=main` 본문만 담당한다.
> - 글로벌 헤더·사이드바·푸터는 app_shell 소관이므로 screen_spec 요약에 중복 기술 금지.
> - navigation_tree 의 라우팅 구조는 화면 라우트 결선 시 참조 진실원이다.

```markdown
---
logicraft_item:
  shell: SHELL-NNN
  nav: NAV-NNN
type: app_shell+navigation_tree
version:
  shell: <n>
  nav: <n>
last_updated_at:
  shell: <ISO>
  nav: <ISO>
domain: <DOMAIN-ID>
project_id: <uuid>
synced_at: <ISO>
sync_session: <n>
stale:
  shell: <bool>
  nav: <bool>
status:
  shell: <synced|NEW|CHANGED>
  nav: <synced|NEW|CHANGED>
raw:
  shell: ./_raw/SHELL-NNN.json
  nav: ./_raw/NAV-NNN.json
---

<!-- CHANGED 있으면 해당 ITEM 변경 배너 삽입 -->
<!-- 버전 추적 규칙:
     - frontmatter 의 version/status 는 SHELL-NNN, NAV-NNN 각각의 키로 분리 표기(위 구조 유지).
     - version-master 표와 fetcher STEP-OUT YAML(processed.new/changed 등)에는
       SHELL-NNN, NAV-NNN 을 각각 독립 ITEM 행으로 보고한다 — 1파일에 합산됐어도 버전 추적은 ITEM 단위.
     - 둘 중 하나라도 CHANGED 이면 그 ITEM 의 변경 배너를 파일 내 해당 블록(셸 섹션 또는 NAV 섹션) 위에 삽입.
     - checklist.md 의 STEP-OUT YAML processed.new / processed.changed 에 SHELL-NNN, NAV-NNN 이 각각 등재됨.
-->

# 앱 셸 + 내비게이션 (SHELL-NNN + NAV-NNN)

**한 줄**: 앱 껍데기(헤더·사이드·레이아웃 컨테이너) + 메뉴 트리·라우팅 구조 진실원.

> ★ 화면-셸 경계:
> - 이 파일이 정의하는 영역(헤더·사이드바·푸터·레이아웃 컨테이너)은 screen_spec 구현 범위 밖이다.
> - 화면 구현 시 `role=main` 영역만 담당한다. 셸 영역을 중복 구현하지 않는다.

## 앱 셸 구조 (SHELL-NNN)

### 슬롯 정의

| 슬롯 | 컴포넌트 경로(추정 또는 실측) | 설명 |
|---|---|---|
| header | <컴포넌트 경로> | 글로벌 헤더 — 로고·사용자 정보·전역 액션 |
| left / sidebar | <컴포넌트 경로> | 사이드 내비게이션 — NAV 트리 렌더 |
| main | {children} | 화면(screen_spec) 이 채우는 영역 |
| footer | <컴포넌트 경로> | 글로벌 푸터 (없으면 "없음") |

### 레이아웃 컨테이너
- 파일: <추정 경로 또는 "⚠️ 미기재">
- CSS 전략: <토큰 기반 grid/flex — DS 토큰 참조>

## 내비게이션 트리 (NAV-NNN)

### 메뉴 구조

```
<트리 형태로 메뉴 항목 열거>
예:
├── 메뉴 그룹 A
│   ├── 메뉴 항목 A-1 → ROUTE_PATH.XXX
│   └── 메뉴 항목 A-2 → ROUTE_PATH.YYY
└── 메뉴 그룹 B
    └── ...
```

### 라우트 매핑

| 메뉴 항목 | 라우트 경로 | SCREEN-ID | 역할 제한 |
|---|---|---|---|
| <메뉴명> | <path> | <SCREEN-NNN> | <ROLE-NNN 또는 "없음"> |

### 구현 결선 포인트
- Router.tsx 의 Route 경로는 이 NAV 트리의 경로와 일치해야 함.
- menuStructure.ts 에 추가할 항목: <목록>
- userMenus.ts 권한별 노출: ROLE → 메뉴 매핑 확인 필요

## 구현 체크리스트
- [ ] 셸 컴포넌트 파일 확인 (src/components/layout/ 또는 해당 프로젝트 경로)
- [ ] 화면 구현 시 role=main 영역만 담당 (헤더·사이드·푸터 중복 구현 없음)
- [ ] NAV 트리 라우트 → Router.tsx 경로 일치 확인
- [ ] 메뉴 항목 → menuStructure.ts / userMenus.ts 추가 확인
```

---

## api_endpoint (API)

저장 경로: `_shared/api/API-NNN.md`

> 화면 구현 관점: axios 호출 계약 + 에러 응답 포맷 + 소비 화면 역참조.
> 기반: implement-kit api_endpoint 섹션 차용 + 프론트 소비처 필드 추가.

```markdown
---
logicraft_item: API-NNN
type: api_endpoint
version: <n>
last_updated_at: <ISO>
domain: <DOMAIN-ID>
project_id: <uuid>
synced_at: <ISO>
sync_session: <n>
stale: <bool>
status: <synced|NEW|CHANGED>
prev_version: <null|n>
raw: ./_raw/API-NNN.json
links:
  required_roles: ["[[<ROLE-NNN>]]", ...]
  uses_constant: ["[[<CONST-NNN>]]", ...]
  consumed_by_screens: ["[[<SCREEN-NNN>]]", ...]
---

<!-- CHANGED 면 변경 배너 삽입 -->

# API-NNN — <title>

**한 줄**: <이 API 가 화면에서 무엇을 하는가 — 데이터 fetch 또는 mutation>

## 구현 요지 (프론트 관점)
- axios 호출 파일: `src/apis/<domain>/<feature>/<feature>Api.ts`
- react-query 훅: `use<Feature>Query` / `use<Feature>Mutation`
- normalizeResponse<T> 체이닝 필수 (응답 타입 추론용)
- 성공 판단: `response.data.error === 0` (HTTP 200 으로 판단 금지)

## 의존 (먼저/함께 구현)
- <ITEM-ID>: <한 줄 이유>

## 구속 제약
- 인증 헤더: <x-access-token 또는 GUIDE 참조값>
- 적용 CONST: [<CONST-NNN(name=value unit)>...] ← req/res enum·range·임계치. 값 추정 금지.
- 적용 ROLE: [<ROLE-NNN>...]

## 엔드포인트 계약

- `<METHOD> <path>`
- 인증: <헤더/토큰 — 인증 ADR 반영>
- Path params: <name: type — 설명>
- Query params: <name: type — 설명>
- Request body:

```json
{
  "<field>": "<type>  // <설명, 필수 여부, 검증 규칙>"
}
```

- Response 200:

```json
{
  "error": 0,
  "data": { "<field>": "<type>" }
}
```

- 에러 응답 envelope:

| HTTP 상태 | error 코드 | 조건/메시지 |
|---|---|---|
| <status> | <code> | <조건/메시지> |

## 프론트 소비처

| SCREEN-ID | 용도 | 바인딩 필드 |
|---|---|---|
| <SCREEN-NNN> | <fetch/submit/...> | <응답 필드 → UI 필드 매핑> |

## 구현 체크리스트
- [ ] API_ENDPOINTS 에 경로 상수 등록 (인라인 URL 금지)
- [ ] axiosInstance.get/post().then(normalizeResponse<T>) 체이닝
- [ ] react-query queryKeys 표준 등록 (로컬 keys 패턴 금지)
- [ ] 성공 시 response.data.error === 0 체크
- [ ] CONST 값 사용 (추정·하드코딩 없음)
- [ ] 에러 응답 → errorManager.showError 처리
```

---

## constant (CONST)

저장 경로: `_shared/constant/CONST-NNN.md`

> CONST = 화면·API·폼 검증에 **그대로 박을 실제 값** (enum·range·default·임계치·토큰).
> 의역·반올림·단위변환 절대 금지 — logicraft 원문 그대로.

```markdown
---
logicraft_item: CONST-NNN
type: constant
version: <n>
last_updated_at: <ISO>
domain: <DOMAIN-ID>
project_id: <uuid>
synced_at: <ISO>
sync_session: <n>
stale: <bool>
status: <synced|NEW|CHANGED>
prev_version: <null|n>
raw: ./_raw/CONST-NNN.json
links:
  used_in_screens: ["[[<SCREEN-NNN>]]", ...]
  used_in_apis: ["[[<API-NNN>]]", ...]
---

<!-- CHANGED 면 변경 배너 삽입 -->

# CONST-NNN — <name>

**한 줄**: <이 값이 화면/API 코드에서 무엇으로 쓰이는가 1줄>

## 상수 값 (코드/설정에 그대로 박을 값)

- **name**: `<name>`
- **value**: `<value>` ← logicraft 원문 그대로. 객체/배열이면 JSON 그대로
- **kind**: <token|enum|config|env_var|magic_value>
- **unit**: <ms·px·count·... / 없으면 "-">
- **의미/결정 근거**: <description 요지>
- **사용 화면**: used_in_screens=[<SCREEN-NNN>...] — 이 값이 박히는 화면
- **사용 API**: used_in_apis=[<API-NNN>...] — 이 값이 req/res 에 쓰이는 API
- **역링크 경고**: uses_constant 역링크 없으면 `⚠️ uses_constant 미연결 — 도메인 CONST 표 수동 확인`
- **env_var 주의**: kind=env_var 이고 is_secret=true 면 값은 placeholder — 실제 시크릿 코드에 박지 말 것

## 화면 구현 사용처

| 사용 위치 | 용도 | 코드 형태 |
|---|---|---|
| <SCREEN-NNN 또는 API-NNN> | <폼 검증 범위·셀렉트 옵션·레이블·enum 등> | `<name>` 상수 참조 |

> enum/range/default 를 추정·하드코딩하지 말 것 — 이 CONST 를 단일 진실원으로 참조.

## 구현 체크리스트
- [ ] 상수 파일 (`src/define/` 또는 프로젝트 constants 경로) 에 등록
- [ ] 사용 화면·API 에서 인라인 값 없이 상수명으로 참조
- [ ] env_var+is_secret 은 .env 파일에만, 코드에 값 노출 없음
```

---

## permission_role (ROLE)

저장 경로: `_shared/role/ROLE-NNN.md`

> 화면 구현 관점: 화면 접근 가드·메뉴 노출·UI 조건부 렌더 결선용.

```markdown
---
logicraft_item: ROLE-NNN
type: permission_role
version: <n>
last_updated_at: <ISO>
domain: <DOMAIN-ID>
project_id: <uuid>
synced_at: <ISO>
sync_session: <n>
stale: <bool>
status: <synced|NEW|CHANGED>
prev_version: <null|n>
raw: ./_raw/ROLE-NNN.json
links:
  required_by_screens: ["[[<SCREEN-NNN>]]", ...]
---

<!-- CHANGED 면 변경 배너 삽입 -->

# ROLE-NNN — <role name>

**한 줄**: <이 역할이 화면에서 어떤 접근 범위를 허용하는가 1줄>

## 구현 요지 (프론트 관점)
- 화면 접근 가드: Router 레벨 또는 페이지 컴포넌트 내 역할 체크
- 메뉴 노출 조건: userMenus.ts / menuStructure.ts 참조
- UI 조건부 렌더: 특정 역할만 보이는 버튼·영역 처리

## 구속 제약
- 데이터 스코프: <본인 지자체 한정 / 전체 / 조건부 — ADR/GUIDE 반영>

## 역할-권한 (화면 접근 매트릭스)

| SCREEN-ID | 화면명 | 접근 허용 | 조건(데이터 스코프) |
|---|---|---|---|
| <SCREEN-NNN> | <화면명> | <허용/제한> | <조건> |

## 역할 속성

- role key: `<key>`
- 표시명: `<한글명>`
- 상위 역할: <상위 ROLE-ID 또는 "없음">
- 권한 매트릭스 요약:

| 리소스/액션 | 허용 | 조건 |
|---|---|---|
| <resource> | <Y/N> | <조건> |

## 구현 체크리스트
- [ ] 화면 Router 레벨 가드 적용 (required_roles 연결 화면)
- [ ] userMenus.ts 역할별 메뉴 노출 설정 확인
- [ ] 조건부 렌더 처리 (역할에 따라 달라지는 UI 요소)
- [ ] 데이터 스코프 규칙 준수 (API 요청 시 스코프 파라미터)
```

---

## use_case (UC)

저장 경로: `screens/SCREEN-NNN/uc/UC-NNN.md`

> 화면 구현 관점: 사용자 시나리오 → 컴포넌트 상태 흐름 + AC 연결.

```markdown
---
logicraft_item: UC-NNN
type: use_case
version: <n>
last_updated_at: <ISO>
domain: <DOMAIN-ID>
project_id: <uuid>
synced_at: <ISO>
sync_session: <n>
stale: <bool>
status: <synced|NEW|CHANGED>
prev_version: <null|n>
raw: ./_raw/UC-NNN.json
links:
  realized_by_screens: ["[[<SCREEN-NNN>]]", ...]
  verified_by: ["[[<AC-NNN>]]", ...]
  consumes_apis: ["[[<API-NNN>]]", ...]
---

<!-- CHANGED 면 변경 배너 삽입 -->

# UC-NNN — <title>

**한 줄**: <이 유스케이스가 화면에서 사용자가 하는 일 1줄>

## 구현 요지
- 이 UC 를 구현하는 화면: [<SCREEN-NNN>...]
- 검증 기준 (AC): [<AC-NNN>...] → `../ac/` 폴더 참조

## 의존
- <ITEM-ID>: <한 줄 이유>

## 유스케이스 흐름

- **Actor**: <사용자 역할>
- **사전 조건**: <진입 시 필요한 상태>
- **사후 조건**: <완료 시 시스템 상태>

### 주 흐름
1. <단계 1 — 사용자 행위>
2. <단계 2 — 시스템 반응·화면 상태 변화>
3. ...

### 대안/예외 흐름
- **대안 A**: <분기 조건> → <대안 처리>
- **예외 E1**: <에러 조건> → <화면 에러 처리>

## Given/When/Then (구현 검증)

| # | Given | When | Then |
|---|---|---|---|
| 1 | <사전 상태> | <사용자 행위> | <기대 결과> |

> 각 행 = 1 테스트 케이스 (AC 의 기준과 대응)

## 구현 체크리스트
- [ ] 주 흐름 단계가 화면 컴포넌트 상태로 구현됨
- [ ] 예외 흐름 에러 처리 구현 (errorManager 또는 인라인 피드백)
- [ ] Given/When/Then 각 항목 충족 확인 (AC 기준과 정합)
```

---

## acceptance (AC)

저장 경로: `screens/SCREEN-NNN/ac/AC-NNN.md`

> 화면 구현 관점: 구현 완료 판단 기준 — mc-logi-screen-implement Phase 4 각 화면 구현 후 체크.

```markdown
---
logicraft_item: AC-NNN
type: acceptance
version: <n>
last_updated_at: <ISO>
domain: <DOMAIN-ID>
project_id: <uuid>
synced_at: <ISO>
sync_session: <n>
stale: <bool>
status: <synced|NEW|CHANGED>
prev_version: <null|n>
raw: ./_raw/AC-NNN.json
links:
  verifies: ["[[<UC-NNN>]]", ...]
  related_screens: ["[[<SCREEN-NNN>]]", ...]
---

<!-- CHANGED 면 변경 배너 삽입 -->

# AC-NNN — <title>

**한 줄**: <이 수용 기준이 검증하는 화면 동작 1줄>

## 구현 요지
- 검증 대상 화면: [<SCREEN-NNN>...]
- 검증 대상 UC: [<UC-NNN>...]
- Phase 4 구현 후 이 기준 충족 여부를 구현자가 직접 확인

## 수용 기준 (Given/When/Then)

| # | Given | When | Then |
|---|---|---|---|
| 1 | <사전 상태> | <사용자 행위 또는 API 응답> | <기대 화면 상태·메시지·데이터> |
| 2 | ... | ... | ... |

> 각 행 = 구현자가 브라우저에서 수동 확인하거나 자동화 테스트로 단언하는 1 케이스.

## last_run 기록
- last_run: <있으면 "날짜 — passed/failed" / 없으면 "미실행">

## 구현 체크리스트
- [ ] 모든 Given/When/Then 항목을 브라우저(또는 자동화 테스트)로 확인
- [ ] 실패 항목 있으면 Phase 4 로 되돌아가 수정 후 재확인
- [ ] 통과 시 SCREENS.md 화면 상태 업데이트 (Phase 5 에서 create_implementation_record)
```

---

## implementation_guideline (GUIDE)

저장 경로: `_shared/guideline/GUIDE-NNN.md`

> 화면 구현 관점: 프로젝트 공통 코딩 규칙 — 이 스킬이 받는 GUIDE 는 applies_to_types 매칭분.

```markdown
---
logicraft_item: GUIDE-NNN
type: implementation_guideline
version: <n>
last_updated_at: <ISO>
domain: <DOMAIN-ID>
project_id: <uuid>
synced_at: <ISO>
sync_session: <n>
stale: <bool>
status: <synced|NEW|CHANGED>
prev_version: <null|n>
raw: ./_raw/GUIDE-NNN.json
links:
  applies_to_types: ["[[<type code>]]", ...]
---

<!-- CHANGED 면 변경 배너 삽입 -->

# GUIDE-NNN — <title>

**한 줄**: <이 가이드라인이 화면 코드에 강제하는 것 1줄>

## 구현 요지
- 적용 범위: applies_to_types=[<type list>] (비어있으면 project-wide)
- 이 GUIDE 를 위반하면 pre-commit lint 또는 코드리뷰에서 차단됨.

## 구속 제약
- category: <category>
- rule 원문: <logicraft rule 필드 원문 그대로>
- applies_to_types: [<type code>...]

## 공통 코딩 규칙 (화면 구현 적용)

| category | rule (원문) | 위반 예 | 준수 예 |
|---|---|---|---|
| <category> | <rule> | <violation> | <correct> |

## 구현 체크리스트
- [ ] 이 GUIDE 의 rule 을 모든 관련 타입 코드에 적용
- [ ] 위반 예와 비교하여 기존 코드 점검
- [ ] linter 규칙화 가능한 항목은 ESLint config 에 반영 여부 확인
```

---

## 작성 원칙 (fetcher 준수)

1. **구현 결정만** — "사용자가 X 할 수 있다" 같은 일반론 금지. 컴포넌트·훅·타입·경로 수준으로 구체화.
2. **logicraft 데이터 충실** — 값/이름/타입/경로 의역·추정 금지. 모르면 `⚠️ 미정 (logicraft 미기재)` 명시.
3. **링크는 ID 로** — 의존 ITEM 은 ITEM-ID 로 적어 SCREENS.md 그래프와 연결.
4. **상수 값 인라인** — API/SCREEN/UC/AC 요약이면 `uses_constant` 링크를 따라 `CONST-NNN(name=value unit)` 형태로 인라인. 값 추정 금지.
5. **spec 텍스트 정제** — screen_spec 요약 시 식별 기호·메타 설명·API ID 접미사를 본문에 그대로 박지 말 것.
6. **화면-셸 경계 유지** — screen_spec 요약에 셸(헤더·사이드·푸터) 영역 기술 금지. shell-nav.md 로 위임.
7. **read-only 전제** — 이 요약 템플릿을 사용하는 fetcher 는 logicraft 쓰기 도구를 호출하지 않는다.
8. **불확실은 표기** — logicraft 에 없는 정보는 채우지 말고 `⚠️ 미정 (logicraft 미기재)` 로 남김.
