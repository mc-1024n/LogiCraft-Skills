# core-item-set.md — 화면 키트 핵심 세트 (고정) + 빌드 순서

logicraft ITEM 타입(**서버 진실원 = `ITEM_TYPES`, 2026-08 기준 57종 — 계속 늘어남**) 중
**화면(프론트엔드) 구현에 필요한** 타입만 결정 규칙으로 다운로드한다.
이 스킬(mc-logi-screen-kit)은 **read-only** — logicraft 조회 도구만 사용. 쓰기 도구는 호출하지 않는다.

## 입력 모드

| 모드 | 형식 | 동작 |
|---|---|---|
| 도메인 전체 | `DOMAIN-NNN` | 그 도메인의 활성 screen_spec 전체 + 공유 의존 ITEM |
| 화면 좁히기 | `SCREEN-NNN` 또는 `SCREEN-NNN,SCREEN-MMM,...` | 지정 화면만 + 그 화면들의 공유 의존 |
| 미지정 | — | 사용자에게 입력 방식 질문 |

### 화면 집합 확정 후 공유 ITEM 범위 산출

지정 화면들의 다음 링크 **합집합**으로 공유 범위를 결정한다:
- `consumes_apis` → 다운로드할 `api_endpoint` 목록
- `required_roles` → 다운로드할 `permission_role` 목록
- `domain_id` → 공유 ITEM 귀속 도메인

### 도메인 미소속 화면 처리 (공통 화면)

`screen_spec` 의 `domain_id` 가 비어있거나 없는 경우(공통/시스템 화면 등):
1. `get_neighbors(SCREEN-NNN)` 로 의존 링크를 역추적한다.
2. 역추적 결과의 `domain_id` 또는 `belongs_to_domain` 링크로 공유 ITEM 귀속 도메인을 추론한다.
3. 추론 불가 시 프로젝트 레벨(project-wide)로 처리하고 사용자에게 알린다.

### ★ 도메인 스코프 정책 (다운로더 자동 — 조용한 유실 방지)

`--domain` 으로 받을 때 서버 필터는 **`items.domain_id` 컬럼 정확 일치**만 본다. 그것만 쓰면
설계에 있어도 키트에 안 내려온다(2026-08 NexusSystem 48% 유실 사고). 그래서
`bin/download-kit.mjs` 는 **그래프 스코프**를 적용한다 — 옛 LLM fetcher 가 그래프를 따라가던
것을 결정적으로 재현한 것이다(실측 재현율 90%):

```
ITEM 의 소속 도메인 = {자기 domain_id} ∪ {1-hop 이웃들의 domain_id}
```

전역 수집(그래프로 소속을 못 정하는 타입): `nfr`, `implementation_guideline`, `permission_role`.

화면 키트에서 특히 중요하다 — `permission_role`(authz)·`constant`(매직값)·`acceptance`(테스트
근거)는 화면 구현의 필수 입력인데 도메인 귀속이 잘 안 채워지는 타입이다.
스코프 밖으로 빠진 핵심 타입은 실행 로그와 `version-master.md` 에 🚨 경고로 남는다 — **보고에 전재할 것.**

> `--screens`(ids 스코프)로 받을 때는 대상이 ID 로 확정되므로 이 정책도, `.kit-scope.json` pin 도
> 적용되지 않는다. 화면 키트는 Phase 2 가 화면+의존 id 집합을 직접 산출해 `--ids` 로 넘기므로
> **이미 LLM 이 스코프를 정하는 구조**이고, pin 은 도메인 키트(mc-logi-implement-kit)용이다.

---

## 공유 ITEM 세트 (도메인/프로젝트 레벨, 1벌)

화면 집합 전체가 공통으로 의존하는 자산. 도메인당 1벌만 받는다.

| type code | 약칭 | 구현상 의미 | fetch 방법 |
|---|---|---|---|
| `design_system` | DS | 디자인 토큰·컬러·타이포·스페이싱 계약 — 색·간격은 여기서만 | `get_design_md` 결과(design.md 형식) + raw JSON |
| `ui_component` | UI | 컴포넌트 카탈로그 전체 — 이름·category·props·variants·a11y·code_snippet 요약 | `list_items(type=ui_component)` 전체 + 개별 `get_item` |
| `app_shell` | SHELL | 앱 껍데기(헤더·사이드바·레이아웃 컨테이너) — 화면 조립 시 부모 구조 | `find_app_shell` |
| `navigation_tree` | NAV | 메뉴 트리·라우팅 구조 — 화면 진입점·breadcrumb·링크 결선 | `find_navigation` |
| `api_endpoint` | API | 화면들의 `consumes_apis` 합집합 — method/path/req/res/auth/error 계약 | 화면별 consumes_apis 합집합 ID 로 `get_item` |
| `constant` | CONST | 화면·API 가 `uses_constant` 로 참조하는 상수값 — enum/range/default | 도메인 소속 CONST + 화면/API uses_constant 링크 |
| `permission_role` | ROLE | 화면들의 `required_roles` 합집합 — 역할·권한 매트릭스 | 화면별 required_roles 합집합 ID 로 `get_item` |
| `implementation_guideline` | GUIDE | 프로젝트 공통 코딩 규칙 (`applies_to_types` 매칭분) | 아래 GUIDE 매칭 규칙 참조 |
| `settings_schema` | SETT | (★ **desktop 프로파일 시에만**) 환경설정 스키마 — 설정 화면이 렌더할 설정 키·타입·default·그룹 | `list_items(type=settings_schema)` — 프로젝트 프로파일이 desktop(capability `desktop_ui`)일 때만. 웹 프로젝트는 자연히 0건 |
| `permission_manifest` | PMAN | (★ **desktop 프로파일 시에만**) OS 권한 매니페스트 — 권한 요청/안내 UI 가 참조 | `list_items(type=permission_manifest)` — 동일 조건 |

> ★ **소비 계약 한계(현 스키마 사실)**: `screen_spec.consumes_apis` 는 `^API-\d+$` **REST API 전용**이다.
> local-first(모바일/데스크톱) 화면이 in-process `module_api`(IAPI) 를 데이터 소스로 쓰는 경우
> 화면→IAPI 직접 링크가 스키마에 없으므로, IAPI 계약은 **도메인 구현 키트(mc-logi-implement-kit)** 쪽에서
> 확인해야 한다. 화면 키트에는 자동으로 안 들어옴 — 필요 시 `--types module_api` 로 수동 포함하고
> 보고에 그 사실을 명시한다.

### GUIDE 매칭 규칙
- `applies_to_types` 비어있음 → project-wide → 항상 포함
- `applies_to_types` 채워짐 → 다운로드 대상 타입과 교집합이 있으면 포함 (예: `screen_spec`, `ui_component`, `api_endpoint`)

### 카탈로그 감지 (구현 Phase 0.5 연동)
- `ui_component` 0건 → `SCREENS.md` 헤더에 경고 플래그 기록:
  ```
  ⚠️ ui_component 카탈로그 비어있음 — implement Phase 0.5 에서 시드 필요
  DS archetype: {design_system 이름 또는 "미확인"}
  ```
- 이 플래그는 mc-logi-screen-implement 가 Phase 0.5(카탈로그 시드)를 건너뛸지 여부를 판단하는 데 사용된다.

---

## 화면별 ITEM 세트 (SCREEN 마다)

화면 집합의 각 SCREEN에 대해 개별적으로 받는다.

| type code | 약칭 | 구현상 의미 | fetch 방법 |
|---|---|---|---|
| `screen_spec` | SCREEN | 화면 정의 본문 — sections/components/consumes_apis/required_roles/layout | `get_item(SCREEN-NNN)` + `get_static_render` / `get_wireframe_css` 로 와이어프레임 취득 |
| `use_case` | UC | 이 화면의 동작 시나리오 — Given/When/Then 흐름 | `get_neighbors(SCREEN-NNN)` 에서 `use_case` 링크 추출 |
| `acceptance` | AC | 이 화면의 수용 기준 — 구현 완료 판단 기준 | `get_neighbors(SCREEN-NNN)` 에서 `acceptance` 링크 추출 |

### static_render (와이어프레임) 처리 — get_static_render + get_wireframe_css (HTTP/DNS 무관)

1. `get_static_render(project_id, SCREEN-NNN)` 호출 → `renders[]` (전체 surface).
2. `renders` 가 비어있으면(count 0) → `_no-wireframe.md` 플래그 파일 생성. (3~5 건너뜀)
3. 각 render 의 html 을 저장:
   - surface 1개면 `wireframe.html`
   - 복수면 `wireframe-{render_id}.html` (예: `wireframe-main.html`, `wireframe-detail.html`)
   - html 이 null(`error: file_missing`)인 항목은 건너뛰고 SCREENS.md 에 "파일 누락" 표기.
4. `get_wireframe_css()` 1회 호출 → css 를 같은 화면 폴더에 `wireframe.css` 로 저장.
5. 저장한 각 `wireframe*.html` 에서 `'/api/static/wireframe/wireframe.css'` 를 상대 `'wireframe.css'` 로 치환
   (sed/replace) → 브라우저로 열면 스타일 그대로 적용.

※ `_no-wireframe.md` 는 "static_render 자체가 0건일 때만". (URL fetch 실패로 만들지 않는다 — 이제 fetch 안 함.)

---

## 빌드 순서 (SCREENS.md 에 기재 — implement 진행 순서)

mc-logi-screen-implement 가 이 키트를 단일 진실원으로 쓸 때의 처리 순서.
"공유 자산 먼저, 화면 단위 점진" 원칙을 따른다.

```
━━━ 공유 자산 (Phase 1 셋업) ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

  0. 제약 흡수
     GUIDE → 프로젝트 코딩 규칙 내재화
     CONST → 화면·API 가 uses_constant 로 참조하는 상수값 확인 (인라인 추정 금지)
     DS    → 디자인 토큰 확인 (색·간격은 get_design_md 토큰만 사용, 임의 hex 금지)

  1. 디자인 시스템
     design_system → 토큰·컬러·타이포·스페이싱 계약 확인

  2. UI 컴포넌트 카탈로그
     ui_component  → 전체 카탈로그 확인 (0건이면 Phase 0.5 시드 선행)

  3. 앱 껍데기 / 내비게이션
     app_shell + navigation_tree → 레이아웃 컨테이너·라우팅 구조 확인

  4. API 계약 / 상수 / 역할
     api_endpoint  → 화면들의 consumes_apis 합집합 (컨트롤러 시그니처·DTO·에러 응답)
     constant      → 화면·API 가 사용하는 상수 (enum/range/default)
     permission_role → 화면들의 required_roles 합집합 (권한 가드 결선)

  5. 구현 가이드라인
     implementation_guideline → 매칭 GUIDE 적용 규칙 확인

━━━ 화면별 점진 (Phase 4 구현) ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

  화면 하나씩, 아래 순서로:

  6. 화면 스펙
     screen_spec   → sections/components/consumes_apis/required_roles + 와이어프레임 HTML

  7. 시나리오 / 수용 기준
     use_case      → 동작 시나리오 확인 (화면 구현 방향 결정)
     acceptance    → 수용 기준 확인 (구현 완료 판단 기준)

  ↑ 6–7 을 화면 수만큼 반복
```

### implement Phase 매핑

| 빌드 단계 | mc-logi-screen-implement Phase |
|---|---|
| 제약 흡수 (GUIDE / CONST / DS) | Phase 0 키트 게이트 내 선행 확인 |
| DS → UI → SHELL/NAV → API/CONST/ROLE/GUIDE | Phase 1 공유 자산 셋업 |
| screen_spec → UC/AC (화면별) | Phase 4 화면별 구현 |

---

## 제외 ITEM (이 스킬에서 다운로드하지 않음)

화면(프론트) 구현에 직접 필요하지 않거나 다른 스킬(mc-logi-implement 도메인 버전)이 담당:

- `erd`, `domain_event`, `diagram_sequence` — 백엔드 구현 대상
- `domain`, `domain_feature` — 도메인 단위 스킬(mc-logi-implement-kit) 담당
- `adr`, `nfr` — 백+프론트 공통 제약; 화면 작업 중 관련 ADR이 SCREEN/API에 링크된 경우 사용자에게 알리고 참고 수준으로 메모
- `rfp_item`, `requirement` — 상위 추상
- `glossary` — 도메인 ubiquitous_language 로 흡수
- `risk`, `slo`, `runbook`, `incident`, `postmortem`, `monitor_alert` — 운영 도메인
- `implementation_record`, `code_module`(MOD) — ★ **구현 결과의 사후 추적 문서**(file_path→설계 역참조)지 구현 입력 스펙이 아니다. 무엇을 구현할지는 screen_spec/UC/AC/API 로 충분하고, 코드↔설계 접합은 소스의 `@DesignRef` 주석이 담당하므로 키트에 불필요(매 SYNC 마다 대량 신규로 떠서 노이즈만 됨). 구현 완료 후 mc-logi-screen-implement Phase 5 에서 역동기화만 기록 (mc-logi-implement-kit 과 동일 정책)
- `diagram_c4_*`, `diagram_deployment` — 아키텍처 레벨

> 단, 사용자가 "전부 받아줘" 명시 시 위 제외 ITEM도 화면의 `get_neighbors(depth=2)` 결과 범위에서 추가 다운로드.

---

## 산출물 구조 참조

이 core-item-set 을 기반으로 생성되는 키트 디렉토리 구조:

```
docs/screen-design/{도메인슬러그}-{DOMAIN-ID}/
├── SCREENS.md                  ← 진입점 (화면 목록 + 공유자산 인덱스 + 빌드 순서 + 카탈로그 상태 플래그)
├── version-master.md           ← 버전 마스터 (전 ITEM 버전표 + run changelog)
├── _shared/
│   ├── design-system.md        ← design_system (get_design_md 결과) + _raw/DS-NNN.json
│   ├── ui-catalog.md           ← ui_component 전체 카탈로그 요약 + _raw/UI-NNN.json
│   ├── shell-nav.md            ← app_shell + navigation_tree 요약
│   ├── api/                    ← api_endpoint 개별 파일 (API-NNN.md + _raw/)
│   ├── constant/               ← constant 개별 파일
│   ├── role/                   ← permission_role 개별 파일
│   └── guideline/              ← implementation_guideline 개별 파일
├── screens/
│   └── SCREEN-NNN/
│       ├── SCREEN-NNN.md       ← screen_spec 구현지향 요약 (frontmatter + 변경 배너)
│       ├── wireframe.html      ← get_static_render 결과 HTML (복수면 wireframe-{render_id}.html)
│       ├── wireframe.css       ← get_wireframe_css 결과 CSS
│       ├── _raw/SCREEN-NNN.json
│       └── uc/                 ← use_case 개별 파일 (UC-NNN.md)
│       └── ac/                 ← acceptance 개별 파일 (AC-NNN.md)
└── _retired/                   ← 상태 변경(archived/deprecated)된 ITEM 이동
```

> 이 경로(`docs/screen-design/`)는 기존 도메인 키트(`docs/design/`)와 분리된 별도 디렉토리다.
> 같은 도메인에 두 키트가 공존할 수 있다.
