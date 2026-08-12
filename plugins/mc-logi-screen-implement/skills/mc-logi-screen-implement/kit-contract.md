# kit-contract.md — 키트 ↔ phase 데이터 계약

이 스킬이 도메인 지식을 얻는 **유일한** 출처는 mc-logi-screen-kit 산출물이다.
키트 구조(screen-kit 의 산출 규약)와 각 파일에서 무엇을 읽어 어느 Phase 에 주입하는지를 정의한다.
키트 포맷이 바뀌면 이 파일만 갱신하면 된다.

## 키트 구조 (입력 계약)

```
docs/screen-design/{도메인슬러그}-{DOMAIN-ID}/
├── SCREENS.md                  ← 진입점 (화면 목록 + 공유자산 인덱스 + 빌드 순서 + 카탈로그 상태 플래그 + 변경 알림)
├── version-master.md           ← 버전 마스터 (전 ITEM 버전 표 + run changelog: NEW/CHANGED/RETIRED)
├── _shared/
│   ├── design-system.md        ← get_design_md 결과(design.md 형식 원문) + _raw/DS-NNN.json
│   ├── ui-catalog.md           ← ui_component 전체 카탈로그 요약 1파일 (find_ui_component 룩업 인덱스)
│   ├── shell-nav.md            ← app_shell + navigation_tree 요약 (화면-셸 경계 명시)
│   ├── api/                    ← api_endpoint 개별 파일 (API-NNN.md + _raw/)
│   ├── constant/               ← constant 개별 파일 (CONST-NNN.md + _raw/)
│   ├── role/                   ← permission_role 개별 파일 (ROLE-NNN.md + _raw/)
│   ├── guideline/              ← implementation_guideline 개별 파일 (GUIDE-NNN.md + _raw/)
│   ├── settings_schema/        ← (desktop 프로파일 시) SETT-NNN.md — 설정 화면이 렌더할 키·default
│   ├── permission_manifest/    ← (desktop 프로파일 시) PMAN-NNN.md — 권한 요청/안내 UI 참조
│   └── _raw/                   ← DS / UI 원본 JSON (design_system·ui_component 공용)
├── screens/
│   └── SCREEN-NNN/
│       ├── SCREEN-NNN.md       ← screen_spec 구현지향 요약 (frontmatter + 변경 배너)
│       ├── wireframe.html      ← static_render 와이어프레임 HTML (없으면 _no-wireframe.md)
│       ├── _raw/SCREEN-NNN.json
│       ├── uc/                 ← 이 화면의 UC-NNN.md
│       └── ac/                 ← 이 화면의 AC-NNN.md
└── _retired/                   ← deprecated/superseded ITEM 이동 (삭제 금지)
```

- 키트 루트: `docs/screen-design/{도메인슬러그}-{DOMAIN-ID}/`
  (기존 도메인 키트 `docs/design/` 와 분리·공존. 같은 도메인에 두 키트가 공존 가능)

---

## Phase 0 — 키트 게이트 적재 목록 (메인 컨텍스트로 읽음)

| 키트 파일 | 읽는 것 | 쓰이는 곳 |
|---|---|---|
| `SCREENS.md` | 전체 — 화면 목록 표 / 공유자산 인덱스 / 빌드 순서 / 카탈로그 상태 플래그(⚠️ ui_component 비어있음 여부) / 변경 알림(CHANGED/RETIRED) / last sync | 모든 Phase 의 골격. Phase 0.5 시드 필요 여부 판단. RETIRED 영향 정리 |
| `version-master.md` | 헤더(last sync·sync_session·Domain·화면 집합) + 직전 changelog 의 CHANGED/RETIRED 건 | 신선도 게이트 (stale 판단 + screen-kit 재실행 필요 여부) |

**Phase 0 게이트 결정 로직**:
- `SCREENS.md` 없음 → Skill(mc-logi-screen-kit) 실행 후 재진입
- `version-master.md` last sync 가 설정 임계치(예: 7일) 초과 또는 사용자 SYNC 요청 → screen-kit 재실행 제안
- CHANGED / RETIRED 있으면 영향 정리 후 진행(RETIRED 화면은 구현 대상 제외 + 코드 제거 검토 대상 알림)

---

## Phase 0.5 — 카탈로그 시드 입력

| 키트 파일 | 읽는 것 | 쓰이는 곳 |
|---|---|---|
| `SCREENS.md` | `ui_component 카탈로그` 상태 플래그 (`⚠️ 비어있음` 또는 `populated N건`) | 시드 필요 여부 판단 게이트. 비었으면 시드 진행, populated 면 Phase 0.5 skip |
| `_shared/design-system.md` | DS archetype 이름 (헤더 또는 frontmatter 의 logicraft_item 필드) / 디자인 시스템 계열 정보 | 시드 출처 C 판단 (`apply_design_preset(seed_components=true)`) 시 어느 DS 에 연동할지 확인 |

**Phase 0.5 시드 출처 판단 (SCREENS.md ⚠️ 플래그 확인 후)**:
- A) 레포에 컴포넌트 코드 있음 → AI 가 파일 읽어 추출 → `register_ui_components`
- B) 라이브러리 정함(shadcn 등) → 표준 지식으로 `register_ui_components`
- C) 코드/라이브러리 없음 → `_shared/design-system.md` 의 DS archetype 확인 → `apply_design_preset(seed_components=true)`
- logicraft 쓰기 발생 지점 — dry 제시 후 사용자 승인 필수 (logicraft 정책 준수)

---

## Phase 1 — 공유 자산 셋업 입력

| 키트 파일 | 읽는 것 | 쓰이는 곳 |
|---|---|---|
| `_shared/api/API-NNN.md` (건수만큼) | method/path/req/res/auth/에러 envelope 계약 / consumed_by_screens 역참조 | apiClient 3파일 세트(axiosInstance 호출·normalizeResponse 체이닝·react-query 훅) 생성 |
| `_shared/constant/CONST-NNN.md` (건수만큼) | 상수명·값·unit·kind / used_in_screens·used_in_apis 링크 | 상수 정의 파일 (`src/define/` 또는 프로젝트 경로) 에 등록 |
| `_shared/role/ROLE-NNN.md` (건수만큼) | role key / 접근 허용 매트릭스 / required_by_screens 링크 | Router 레벨 가드 + userMenus.ts / menuStructure.ts 권한 결선 |
| `_shared/guideline/GUIDE-NNN.md` (건수만큼) | rule 원문 / applies_to_types 범위 / category | 구현 전 코딩 규칙 내재화. linter 규칙화 가능 항목 확인 |
| `_shared/shell-nav.md` | 슬롯 정의(header·sidebar·main·footer) / NAV 트리 구조 / 라우트 매핑 표 | Router.tsx Route 경로 결선 / menuStructure.ts 항목 추가 / 화면-셸 경계 확인 |
| `SCREENS.md` 의 도메인 슬러그 | `{도메인슬러그}-{DOMAIN-ID}` 형식에서 추출 | 공유 자산 폴더 네이밍 / API·queryKeys 도메인 키 결정 |

**Phase 1 범위**: 도메인 `apiClient`(3파일 세트)·`queryKeys`·`types`(snake_case 보존)·`zod schema` + 라우팅/셸 결선.
레포 컨벤션은 Explore 실측 우선 (키트가 없는 프로젝트별 규칙은 키트에 넣을 일이지 스킬에 하드코딩 금지).

---

## Phase 2 — 스펙 입력 (화면별)

화면마다 아래 파일 세트를 적재하여 superpowers:brainstorming 스펙 작성에 주입.

| 키트 파일 | 읽는 것 | 쓰이는 곳 |
|---|---|---|
| `screens/SCREEN-NNN/SCREEN-NNN.md` | sections[] / components[] / consumes_apis / required_roles / realizes_use_cases / acceptance 링크 / brownfield 보존 메모 / 라우트 경로 / 구현 요지 | 화면 스펙 기술: 컴포넌트 조립 계획·API 연동 계획·권한 가드 계획 |
| `screens/SCREEN-NNN/wireframe.html` | 와이어프레임 HTML (없으면 `_no-wireframe.md` 확인) | 섹션/컴포넌트 배치·레이아웃 이해 (스펙 보조 근거) |
| `screens/SCREEN-NNN/design/` (있으면) | `design-{surface}.html`(고충실도 레이아웃·비주얼) + `design-notes.md`(디자인 결정 + 컴포넌트/토큰 매핑) | ★ 있으면 `wireframe.html` 보다 **우선** 하는 레이아웃·비주얼 근거. 없으면 wireframe 사용. (mc-logi-screen-design 산출) |
| `screens/SCREEN-NNN/uc/UC-NNN.md` (건수만큼) | Actor / 사전·사후 조건 / 주 흐름 단계 / 대안·예외 흐름 / Given/When/Then | 화면 동작 시나리오 → 컴포넌트 상태 흐름 설계 |
| `screens/SCREEN-NNN/ac/AC-NNN.md` (건수만큼) | Given/When/Then 수용 기준 표 / 구현 완료 판단 항목 | 스펙에서 "이 화면이 무엇을 만족해야 하는가" 기준 설정 |
| `_shared/ui-catalog.md` | 카탈로그 인덱스 표 (ID·이름·category·variants) / 각 UI-NNN 섹션 props·code_snippet | `find_ui_component` 룩업 인덱스 — screen_spec sections[] 의 컴포넌트를 UI-NNN 으로 매핑 |

**Phase 2 원칙**: SCREEN-NNN.md 와 wireframe.html 을 1차 사실로 사용. UI 카탈로그 룩업은 `_shared/ui-catalog.md` 로만 (logicraft MCP 재조회 불필요). ITEM ID (SCREEN-NNN, API-NNN 등) 를 스펙에 인용.

---

## Phase 3 — 플랜 (Phase 2 산출물 기반, 키트 직접 입력 없음)

Phase 2 스펙 결과를 기반으로 superpowers:writing-plans 실행. 키트 파일을 직접 새로 읽지 않으나,
플랜의 각 태스크에 **키트 파일 경로를 명시**한다:

| 플랜 태스크 | 명시할 키트 경로 |
|---|---|
| 공유자산 Task 0 | `_shared/api/`, `_shared/constant/`, `_shared/role/`, `_shared/guideline/`, `_shared/design-system.md` |
| 화면별 Task (SCREEN-NNN) | `screens/SCREEN-NNN/SCREEN-NNN.md`, `screens/SCREEN-NNN/wireframe.html`, `screens/SCREEN-NNN/uc/`, `screens/SCREEN-NNN/ac/` |

---

## Phase 4 — 화면별 구현 입력

Phase 2 에서 적재한 화면별 파일 세트를 그대로 구현자 프롬프트에 전달. 추가로 디자인 토큰 규칙 적용.

| 키트 파일 | 읽는 것 | 쓰이는 곳 |
|---|---|---|
| `screens/SCREEN-NNN/SCREEN-NNN.md` | (Phase 2 와 동일 + 구현 체크리스트) | subagent-driven-development 구현자 프롬프트에 화면 스펙 전달 |
| `screens/SCREEN-NNN/wireframe.html` | 섹션·컴포넌트 배치 | 컴포넌트 조립 시 레이아웃 기준 (design/ 없을 때) |
| `screens/SCREEN-NNN/design/` (있으면) | `design-{surface}.html` 고충실도 레이아웃·비주얼 + `design-notes.md` 컴포넌트/토큰 매핑 | ★ 있으면 wireframe 대신 **레이아웃·비주얼 기준**. design-notes.md 매핑을 구현 가이드로. raw hex 금지(D6) 동일 적용 |
| `screens/SCREEN-NNN/uc/UC-NNN.md` | Given/When/Then 흐름 | 상태 관리 구현 + 에러 핸들링 패턴 |
| `screens/SCREEN-NNN/ac/AC-NNN.md` | 수용 기준 항목 | 구현 완료 체크 기준 (화면별 AC 충족 확인) |
| `_shared/ui-catalog.md` | UI-NNN props·variants·a11y·code_snippet | `find_ui_component` 결과 기반 컴포넌트 조립 (카탈로그 외 컴포넌트 추정 금지) |
| `_shared/design-system.md` | 컬러·스페이싱·타이포·라디우스 **토큰명** (get_design_md 원문 기반) | ★ D6 디자인 규칙 주입: 색·간격은 이 파일의 토큰명만. 임의 hex·px 하드코딩 금지. 생성 파일 raw hex grep 체크 (가벼운 검출) |

**Phase 4 핵심 흐름 (화면 하나씩)**:
`SCREEN-NNN.md` sections[] 순회 → `_shared/ui-catalog.md` 로 컴포넌트 룩업 → 컴포넌트 조립
→ `_shared/api/API-NNN.md` react-query 연동 → react-hook-form + zod 검증
→ `screens/SCREEN-NNN/ac/` Given/When/Then 충족 확인

> ★ **design/ 우선 규칙 + 부재 가이드**: 화면에 `screens/SCREEN-NNN/design/` 가 있으면 `wireframe.html` 대신
> `design-{render_id}.html` 을 레이아웃·비주얼 기준으로, `design-notes.md` 의 컴포넌트/토큰 매핑을 구현
> 가이드로 쓴다. **design/ 없으면(부재) 와이어프레임 폴백 + 착수 전 사용자 1줄 안내**: ① `mc-logi-screen-kit`
> SYNC 로 logicraft 의 `screen_design`(SD) 디자인을 받아오거나, ② logicraft 에도 SD 가 없으면
> `mc-logi-screen-design` 으로 디자인을 새로 생성한 뒤 SYNC. 디자인은 선택 단계 — 사용자가 와이어프레임 진행을
> 택하면 그대로 진행. 어느 경우든 D6(토큰만·raw hex 금지) 동일 적용.

---

## Phase 5 — 반영·추적 대상

| 키트 파일 | 읽는 것 | 역동기화 행동 |
|---|---|---|
| `_shared/ui-catalog.md` | 카탈로그 인덱스의 각 `UI-NNN` id + `implements_in_module_ids` 현황 | 이 화면 구현에서 쓴 UI-NNN id ↔ 생성된 `.tsx` 파일 경로(code_module·MOD) → `link_ui_component_to_module` 호출 대상 식별. 역링크 완료 후 다음 세션 중복 방지 |
| `SCREENS.md` | 화면 목록 표 / 빌드 순서 | 구현 완료 화면 상태 갱신 + IMPREC 생성(`create_implementation_record`) 후 SCREENS.md 현황 업데이트 |
| `version-master.md` | ITEM 버전 표 (구현한 SCREEN·API·CONST·ROLE 등 ITEM ID 목록) | `create_implementation_record` IMPREC 대상 식별 (구현한 ITEM ID 열거) |

**Phase 5 역동기화 흐름**:
lint + build 그린 → 머지 게이트 → 머지
→ `create_implementation_record` (화면별 IMPREC)
→ `register_module` (생성된 code_module 등록) + `link_ui_component_to_module` (UI-NNN ↔ MOD 역링크)
→ `SCREENS.md` 현황 + 프로젝트 `CLAUDE.md` 블록 갱신
→ `mc-logi-update` 권고 (구현 중 발견한 설계 불일치) + 메모리 저장 문의

---

## 해석 규칙

1. **⚠️ 표기 우선순위**: 키트 파일이 ⚠️ 로 명시한 불일치(예: "ROLE 미기재", "API 계약 변경 필요")는
   그 지시를 그대로 따른다. 키트가 답을 안 줬으면 사용자에게 묻는다.
2. **RETIRED ITEM**: `_retired/` 와 version-master.md RETIRED 항목 — 구현 대상 제외.
   해당 화면(`SCREENS.md` RETIRED 표기) 은 코드 제거 검토 대상 알림. 구현하지 않는다.
3. **요약 vs 원본**: 요약 `.md` 로 부족하면 `_raw/{ID}.json` 을 열어 보완 — 단 거대 JSON 은
   서브에이전트/Bash 파싱으로 (메인 컨텍스트 오염 방지).
4. **키트 ≠ 코드 현실**: 키트는 설계의 스냅샷이다. 레포의 실코드·실 DOM 구조와 다르면 그것은
   오류가 아니라 **발견**이다 — Explore 실측으로 확정하고, 결정을 스펙 "구현 중 확정" 단락과
   IMPREC 노트에 기록하며, `mc-logi-update` 권고 목록에 올린다.
   (설계를 현실에 맞출지 코드를 설계에 맞출지는 사용자/키트 정책의 몫)
5. **스킬에 도메인 지식 금지**: 이 계약 파일을 포함해 스킬 어디에도 특정 프로젝트의 규칙
   (토큰명·역할 코드·라우터 구조 등)을 적지 않는다. 그런 내용이 필요하면 키트(또는 logicraft 설계)에
   넣을 일이지 스킬에 넣을 일이 아니다.
6. **ui_component 추측 금지**: Phase 4 에서 `_shared/ui-catalog.md` 에 없는 컴포넌트 ID 를
   임의로 쓰지 않는다. 카탈로그 외 컴포넌트 필요 시 사용자에게 알리고 Phase 0.5 시드 또는
   `register_ui_components` 추가 등록을 권고한다.
7. **디자인 토큰 추측 금지**: Phase 4 에서 `_shared/design-system.md` 에 없는 토큰·색·간격 값을
   임의 hex/px 로 추정하지 않는다. 없으면 `⚠️ 미정 (design-system.md 미기재)` 로 남긴다.
