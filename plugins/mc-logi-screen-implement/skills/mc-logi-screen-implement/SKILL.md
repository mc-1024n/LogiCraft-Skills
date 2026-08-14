---
name: mc-logi-screen-implement
description: mc-logi-screen-kit 이 만든 로컬 화면 키트(./docs/screen-design/{도메인슬러그}-{DOMAIN-ID}/)를 단일 진실원으로 삼아, 프론트엔드 화면 구현을 공유자산 셋업→스펙→플랜→화면별 구현→반영·추적까지 phase 게이트로 완주하는 오케스트레이터 스킬. 사용자가 "SCREEN-011 구현해줘", "화면 구현해줘", "키트대로 화면 구현", "D002 화면 구현 시작", "/mc-logi-screen-implement" 등 화면 프론트엔드 구현을 요청할 때 실행. 키트가 없으면 mc-logi-screen-kit 을 먼저 호출하고, 키트가 stale 이면 SYNC 재실행을 먼저 한다. 도메인 규칙·디자인 토큰·컴포넌트 카탈로그·빌드 순서는 이 스킬에 하드코딩하지 않고 전부 키트에서 읽는다. phase 인자로 중단 지점부터 재개 가능 ("공유자산부터", "구현만", "추적만").
license: MIT
allowed-tools: Read, Write, Edit, Grep, Glob, Bash, Agent, ToolSearch, AskUserQuestion, TaskCreate, TaskUpdate, TaskList
metadata:
  version: "1.1.1"
  domain: logicraft-orchestration
  triggers: 화면 구현, 화면 구현해줘, 키트대로 화면 구현, 화면 구현 시작, SCREEN-NNN 구현, D001 화면 구현, 화면 구현 계획, 화면 구현 추적, screen implement, 화면 구현 오케스트레이터
  role: orchestrator
  scope: logicraft-screen-frontend-implementation
  output-format: feature 브랜치 프론트 코드 + 스펙·플랜 문서 + IMPREC + ui_component 역링크 + 키트 현황 갱신
  related-skills: mc-logi-screen-kit, mc-logi-update, mc-logi-implement-review, mc-logi-domain-review, mc-logi-implement
---

# mc-logi-screen-implement — 화면 키트 기반 구현 오케스트레이터

mc-logi-screen-kit 이 만든 로컬 화면 키트를 읽고, **공유 자산 셋업 → 스펙 → 플랜 → 화면별 구현 → 반영 → logicraft 추적**을
phase 게이트로 완주한다. 이 스킬은 **절차만** 안다 — 무엇을 어떤 토큰으로 색칠하고, 어떤 컴포넌트를 어느 순서로 쌓고,
어떤 API 를 연동할지는 전부 키트가 말한다.

## 핵심 원칙

1. **키트가 단일 진실원** — 도메인 규칙·디자인 토큰·컴포넌트 카탈로그·빌드 순서를 이 스킬에 하드코딩하지 않는다.
   `kit-contract.md` 의 매핑대로 키트 파일에서 읽어 각 phase 에 주입한다. 키트에 없는 도메인 지식을
   임의로 지어내지 않는다 (모르면 사용자에게).
2. **mc-logi-screen-kit 선행 종속** — 키트가 없으면 그 스킬을 먼저 실행하고, 키트가 오래됐으면
   SYNC 재실행을 먼저 한다. 키트의 version-master 가 CHANGED 를 보고하면 변경분 검토 없이
   구현을 진행하지 않는다.
3. **phase 게이트** — 카탈로그 시드 승인(게이트 0.5) / 스펙 승인(게이트 1) / 플랜 승인(게이트 2) /
   머지 방식(게이트 3), 네 지점에서 사용자 확인을 받는다. 그 사이는 자율 진행 (subagent-driven 연속 실행).
   게이트 상세는 `phase-gates.md` 참조.
4. **추적 역동기화 의무** — 구현이 끝나면 logicraft `create_implementation_record` 로 화면별 IMPREC 를 남기고,
   `register_module` + `link_ui_component_to_module` 로 부품↔코드 역링크를 완성하며, 키트 현황을 갱신한다.
   이 스킬은 logicraft 에 **구현 기록 쓰기만** 한다 (설계 ITEM data 수정은 mc-logi-update).
5. **superpowers 재사용** — 스펙은 `superpowers:brainstorming`, 플랜은 `superpowers:writing-plans`,
   구현은 `superpowers:subagent-driven-development` 를 그대로 쓴다. 이 스킬은 그 사이에
   "키트 컨텍스트 주입"과 "logicraft 왕복"을 접착한다.
6. **디자인 룰 (D6)** — 색·간격은 `_shared/design-system.md` 의 `get_design_md` 토큰명만 사용한다.
   임의 hex(#RRGGBB)·px 하드코딩은 금지다. 예방은 구현자 프롬프트 주입, 검출은 생성 파일 raw hex grep 체크로 한다.
   KRDS 를 특별취급하지 않는다 — KRDS 도 디자인시스템 하나일 뿐이다.

## Phase 개요

```
Phase 0    키트 게이트       키트 존재/신선도 확인 → 없으면 screen-kit 호출, stale 이면 SYNC.
                             CHANGED/RETIRED 있으면 영향 정리 후 진행. kit-contract Phase 0 적재.
Phase 0.5  카탈로그 시드     SCREENS.md 카탈로그 플래그 확인. 비었으면 3출처로 ui_component 시드:
                             A) 레포 컴포넌트 코드 있음 → 파일 읽어 추출 → register_ui_components
                             B) 라이브러리 정함(shadcn 등) → 표준 지식으로 register_ui_components
                             C) 코드/라이브러리 없음 → apply_design_preset(seed_components=true)
                             → [게이트 0.5: 시드 dry 제시 + 사용자 승인]
Phase 1    공유 자산 셋업    레포 Explore 실측 → 도메인 apiClient(3파일)·queryKeys·types(snake_case)·
                             zod schema + 라우팅/셸 결선. _shared/api·constant·role·guideline 주입.
Phase 2    스펙              superpowers:brainstorming + 화면별 키트 주입(screen_spec/wireframe/AC/
                             ui-catalog 룩업). 키트 ITEM ID·경로 인용. → [게이트 1: 승인]
Phase 3    플랜              superpowers:writing-plans. 태스크=공유자산 Task 0 → 화면별 Task 점진.
                             각 태스크에 키트 화면 요약·AC 경로 명시. → [게이트 2: 승인]
Phase 4    화면별 구현       feature 브랜치 + superpowers:subagent-driven-development. 화면 하나씩:
                             screen_spec.sections → find_ui_component 카탈로그 룩업 → 컴포넌트 조립
                             → react-query 연동(consumes_apis) → react-hook-form+zod 검증
                             → AC(Given/When/Then) 충족.
                             ★ 디자인 규칙 주입: 색·간격은 get_design_md 토큰만, 임의 hex 금지(D6 예방).
                             ★ 가벼운 검출: 생성 파일 raw hex grep 체크(D6 검출).
                             태스크별 스펙리뷰→품질리뷰 + 최종 전체 리뷰.
Phase 5    반영·추적         lint+build 그린 → [게이트 3: 머지 방식] → 머지.
                             IMPREC: create_implementation_record (화면별).
                             역링크: register_module(code_module) + link_ui_component_to_module
                                     (이 화면이 쓴 ui_component ↔ 실제 .tsx) → 다음 세션 중복 방지.
                             키트 현황(SCREENS.md)·프로젝트 CLAUDE.md 블록 갱신.
                             mc-logi-update 권고(구현 중 발견 설계 불일치) + 메모리 저장 문의.
```

재개: 사용자가 phase 를 지정하면 ("공유자산부터", "구현만", "추적만", "Phase N 부터") 해당 phase 의
선행 산출물(SCREENS.md / 스펙/플랜 문서 / git 상태) 존재를 확인하고 그 지점부터 진행한다.
선행 산출물이 없으면 어느 phase 부터 시작할지 보고 후 확인. Phase 0 (키트 게이트)는 재개 시에도 생략하지 않는다.
재개 선행 산출물 목록과 컨텍스트 복원 절차는 `phase-gates.md` §재개 참조.

---

## Phase 0 — 키트 게이트 (선행 종속)

1. **대상 식별**: 화면/도메인 ID (SCREEN-NNN / DOMAIN-NNN / D002 등) 와 프로젝트를 인자·대화·메모리에서 확정.
   불명확하면 질문.
2. **키트 탐색**: `docs/screen-design/*-{DOMAIN-ID}/SCREENS.md` 존재 확인.
   - **없음** → `Skill(mc-logi-screen-kit)` 를 먼저 실행해 키트 생성 (사용자에게 선행 실행을 알리고 진행).
     생성 후 본 스킬 계속.
   - **있음** → `version-master.md` 의 last sync 시각 확인. logicraft 접근이 가능하고
     ① 마지막 sync 가 오래됐거나 ② 사용자가 "최신으로" 류 요청을 했으면 screen-kit 을
     SYNC 모드로 재실행 권고 (간단 확인 후 실행). SYNC 결과 **CHANGED/RETIRED 가 있으면
     그 목록을 사용자에게 보여주고 구현 범위에 미치는 영향을 정리한 뒤** 진행.
     RETIRED 화면은 구현 대상 제외 + 코드 제거 검토 대상 알림.
3. **키트 컨텍스트 적재**: `kit-contract.md` 의 "Phase 0 적재 목록"을 읽는다 —
   `SCREENS.md` 전체(화면 목록·공유자산 인덱스·빌드 순서·카탈로그 상태 플래그·변경 알림) 와
   `version-master.md` 헤더(last sync·sync_session·Domain·화면 집합) + 직전 changelog 의 CHANGED/RETIRED 건.
   여기서 얻는 것: 구현 대상 화면 집합 / 공유 ITEM 목록 / 빌드 순서 / RETIRED 화면 / 카탈로그 상태.
4. **Phase 0 보고**: `phase-gates.md` §Phase 0 키트 게이트 보고 포맷으로 출력 후 Phase 0.5 또는 Phase 1 진입.

## Phase 0.5 — 카탈로그 시드 (logicraft 쓰기 발생)

`SCREENS.md` 에서 `ui_component 카탈로그` 상태 플래그를 확인한다.
- **populated N건** → Phase 0.5 skip, Phase 1 진입.
- **⚠️ 비어있음** → 시드 절차 진행.

**시드 출처 판단 순서**:
1. 레포 `src/` (또는 프로젝트 컴포넌트 루트) 를 Explore 해 컴포넌트 코드 존재 여부 확인.
   - **A) 코드 있음** → 파일 읽어 컴포넌트 목록(이름·category·props·variants) 추출 → `register_ui_components` 대상 목록 구성.
   - **B) 라이브러리 명시** (shadcn, MUI, Ant Design 등) → 표준 지식으로 컴포넌트 목록 구성 → `register_ui_components` 대상.
   - **C) 코드/라이브러리 없음** → `_shared/design-system.md` 의 DS archetype 확인 → `apply_design_preset(seed_components=true)` 대상.
2. **[게이트 0.5]** dry 제시 후 사용자 승인 대기 (logicraft 쓰기 전 절대 실행 금지).
   승인 후 실행 → 결과 보고. 게이트 포맷은 `phase-gates.md` §게이트 0.5 참조.
3. 시드 완료 후 `SCREENS.md` 카탈로그 상태 플래그 갱신 (populated N건으로).

**logicraft 쓰기 경계**: 이 스킬에서 logicraft 쓰기는 Phase 0.5 와 Phase 5 에서만 발생한다.
Phase 0·1·2·3·4 는 logicraft read(get_*, find_*, list_*) 또는 레포 코드 작업만.

## Phase 1 — 공유 자산 셋업

`kit-contract.md` 의 "Phase 1 — 공유 자산 셋업 입력" 표에 따라 키트 파일을 읽어 구현에 주입한다.

1. **레포 Explore 실측**: 빌드 도구·디렉토리 계층·기존 apiClient 패턴·import 컨벤션·타입 래퍼·응답 포맷을 실측한다.
   프로젝트별 규칙은 스킬에 하드코딩 않고 Explore 로 읽는다 (예: axios 인스턴스 경로, normalizeResponse 체이닝 방식).
2. **API 계약 흡수**: `_shared/api/API-NNN.md` 각 파일 읽기 → 도메인 `apiClient` 3파일 세트
   (axiosInstance 호출·normalizeResponse 체이닝·react-query 훅) 생성.
   `queryKeys` 표준 계층 구조 등록, `types` 파일(snake_case 보존, camelCase 변환 금지).
3. **상수·역할·가이드라인 흡수**: `_shared/constant/CONST-NNN.md` → 상수 정의. `_shared/role/ROLE-NNN.md` → Router 가드 + userMenus 권한 결선. `_shared/guideline/GUIDE-NNN.md` → 코딩 규칙 내재화.
4. **셸·내비 결선**: `_shared/shell-nav.md` 의 슬롯 정의·NAV 트리·라우트 매핑 → Router.tsx Route 경로 결선 / menuStructure 항목 추가 / 화면-셸 경계 확인.
5. **디자인 시스템 내재화**: `_shared/design-system.md` 를 읽고 컬러·스페이싱·타이포 **토큰명** 목록을 Phase 4 주입용으로 추출 (D6 예방).
6. 공유 자산 작업은 `feature/{slug}` 브랜치에서 진행 + 커밋.

## Phase 2 — 스펙 (brainstorming 위임 + 키트 주입)

`superpowers:brainstorming` 을 호출하되, `kit-contract.md` "Phase 2 — 스펙 입력" 표에 따라 화면별 파일 세트를 출발점으로 주입한다:

- **화면별 주입 세트**: `screens/SCREEN-NNN/SCREEN-NNN.md` (sections·components·consumes_apis·required_roles·accepts 링크) + `wireframe.html` (없으면 `_no-wireframe.md` 확인) + `uc/UC-NNN.md` 전체 + `ac/AC-NNN.md` 전체.
- **★ design/ 우선 + 부재 시 가이드**: 화면에 `screens/SCREEN-NNN/design/`(고충실 디자인)가 있으면 `wireframe-*.html` 보다 **우선**하여 `design-{render_id}.html`(=`design-{surface}.html`) 을 레이아웃·비주얼 근거로, `design-notes.md` 의 컴포넌트/토큰 매핑을 가이드로 주입한다.
  **design/ 가 없으면(부재) — 와이어프레임으로 하위호환 진행하되, 착수 전 사용자에게 1줄 안내한다** (디자인은 선택 단계라 강제 아님):
  - ① **logicraft 에 디자인(SD)이 이미 있을 수 있음** → `mc-logi-screen-kit` **SYNC** 로 로컬 `design/` 를 받아오면 고충실 디자인 기준으로 구현 가능. (screen-kit 이 SCREEN 을 `designs` 하는 `screen_design` SD 를 받아 `design/` 에 떨군다.)
  - ② **logicraft 에도 SD 가 없으면** → `mc-logi-screen-design` 으로 **디자인을 새로 생성**(SD ITEM 생성 + 디자인 작성·역등록)한 뒤 다시 SYNC.
  - 사용자가 "그냥 와이어프레임으로" 선택 시 기존 흐름 그대로 진행.
- **UI 카탈로그 룩업**: `_shared/ui-catalog.md` 인덱스에서 screen_spec sections[] 의 컴포넌트를 UI-NNN 으로 매핑. 카탈로그 외 컴포넌트가 필요하면 추정 금지 → 사용자에게 register_ui_components 권고.
- **스펙 작성 규칙**: 모든 요구·제약에 **키트 ITEM ID 와 파일 경로를 인용**한다 (예: "로그인 권한 가드 — ROLE-001 / `_shared/role/ROLE-001.md`"). 키트 ⚠️ 불일치는 우선순위 기재 그대로 스펙에 옮긴다. 스킬이 아니라 키트가 근거다.
- **레포 ↔ 키트 불일치 발견**: Explore 실측과 키트 설계가 다르면, 그것을 스펙의 "발견 사항" 단락에 기록한다. Phase 5 mc-logi-update 권고 목록에 적재.
- 스펙 저장: `docs/superpowers/specs/YYYY-MM-DD-{slug}-screen-design.md` + 커밋.

**[게이트 1]** 스펙 검토·승인 후 Phase 3. 게이트 포맷은 `phase-gates.md` §게이트 1 참조.

## Phase 3 — 플랜 (writing-plans 위임)

`superpowers:writing-plans` 를 호출하되:

- **태스크 순서**: 공유 자산 Task 0(apiClient·queryKeys·types·zod schema·라우팅 결선) → 화면 단위 Task 점진 (SCREENS.md 빌드 순서 기본값, 의존 화면 먼저).
- **각 태스크에 키트 참조 명시** (`kit-contract.md` "Phase 3 — 플랜" 표):
  - 공유 자산 Task 0: `_shared/api/`, `_shared/constant/`, `_shared/role/`, `_shared/guideline/`, `_shared/design-system.md`
  - 화면별 Task: `screens/SCREEN-NNN/SCREEN-NNN.md`, `screens/SCREEN-NNN/wireframe.html`, `screens/SCREEN-NNN/uc/`, `screens/SCREEN-NNN/ac/`
- **각 태스크에 AC 경로 명시**: 구현 서브에이전트가 수용 기준 원문을 직접 읽을 수 있어야 한다.
- 플랜 저장: `docs/superpowers/plans/YYYY-MM-DD-{slug}-screen.md` + 커밋.

**[게이트 2]** 플랜 승인 + 실행 방식 선택 후 Phase 4. 게이트 포맷은 `phase-gates.md` §게이트 2 참조.

## Phase 4 — 화면별 구현 (subagent-driven 위임 + 키트 전달)

`superpowers:subagent-driven-development` 로 실행하되:

- main 직접 작업 금지 — `feature/{slug}` 브랜치 (Phase 1 에서 이미 생성).
- **화면 하나씩 점진**: SCREENS.md 빌드 순서대로 화면 1개 완료 → 다음 화면.
- **구현자 프롬프트에 포함할 것** (`kit-contract.md` "Phase 4 — 화면별 구현 입력" 표):
  - 플랜의 해당 태스크 전문 + `screens/SCREEN-NNN/SCREEN-NNN.md` (sections[] 배치 지시) +
    `screens/SCREEN-NNN/wireframe.html` (레이아웃 기준) +
    `screens/SCREEN-NNN/uc/UC-NNN.md` (Given/When/Then 흐름) +
    `screens/SCREEN-NNN/ac/AC-NNN.md` (완료 기준).
  - **★ design/ 우선 (있으면)**: `screens/SCREEN-NNN/design/design-{render_id}.html` 이 있으면 `wireframe.html` 대신 이것을 레이아웃·비주얼 기준으로, `design-notes.md` 의 컴포넌트/토큰 매핑을 구현 가이드로 전달. **없으면 Phase 0 의 design/ 부재 가이드**(① screen-kit SYNC 로 logicraft SD 받기 ② SD 없으면 screen-design 으로 생성) 적용 — 사용자가 와이어프레임 진행 선택 시 와이어프레임 사용. D6(토큰만·raw hex 금지)는 design/ 산출물에도 동일 적용.
  - `_shared/ui-catalog.md` UI-NNN props·variants·code_snippet (카탈로그 외 컴포넌트 추정 금지).
  - **★ 디자인 규칙 주입 (D6 예방)**: "색·간격은 `_shared/design-system.md` 의 토큰명만.
    임의 hex(#RRGGBB)·px 하드코딩 절대 금지. 토큰이 없으면 ⚠️ 미정으로 남기고 주석 처리."
- **★ 구현 흐름 (화면 하나씩)**:
  1. `SCREEN-NNN.md` sections[] 순회
  2. `_shared/ui-catalog.md` 로 컴포넌트 룩업 (find_ui_component 결과 기반)
  3. 컴포넌트 조립 + 디자인 토큰 적용
  4. `_shared/api/API-NNN.md` react-query 연동 (consumes_apis 목록)
  5. react-hook-form + zod 검증 (필드·규칙은 ac/ 기준)
  6. `ac/AC-NNN.md` Given/When/Then 항목별 충족 확인
- **★ D6 검출**: 화면 구현 완료 시마다 생성된 .tsx 파일에 대해 raw hex grep 체크.
  ```bash
  # 생성 파일 내 임의 hex 검출 (토큰명이 아닌 직접 색상값)
  grep -rn "#[0-9a-fA-F]\{3,6\}" src/pages/{domain}/ src/components/{domain}/
  ```
  발견 시 구현자에게 반환 → 디자인 토큰으로 교체.
- **리뷰어 프롬프트에 포함할 것**: 스펙 리뷰어에게는 키트 AC(Given/When/Then) 를 대조 기준으로 제공.
  품질 리뷰어는 통상대로.
- **키트 ↔ 실코드 불일치 발견 시**:
  1. 키트에 ⚠️ 우선순위가 있으면 따른다.
  2. 없으면 중단 + 컨트롤러(메인)가 판단. 레포의 기존 동작을 바꾸는 결정이면 게이트 밖이라도 사용자에게 확인.
  3. 결정을 스펙 "구현 중 확정" 단락에 추가 커밋 + Phase 5 mc-logi-update 권고 목록에 적재.
- **카탈로그 외 컴포넌트 필요 시**: 추정 금지 → 사용자에게 알리고 register_ui_components 추가 등록 권고 (Phase 0.5 재진행 또는 별도 호출).
- 모든 화면 구현 후 **최종 전체 리뷰** 1회 (브랜치 분기점 대비 전체 diff — 스펙 커버리지·AC 충족·역할 가드·raw hex 클린·잔여 표식). Critical/Important 는 수정 후 종료.

## Phase 5 — 반영·추적

1. **lint + build 그린 확인**: 클린 빌드 + 린트 에러 0건 확인.
2. **[게이트 3]** 머지 방식 확인 후 실행. 게이트 포맷은 `phase-gates.md` §게이트 3 참조.
   운영 전 확인 필요 사항(키트 ⚠️ spec-pending·수동 절차)을 머지 보고에 명시.
3. **IMPREC 기록**: 구현 화면별로 `create_implementation_record`
   (status=implemented/in_progress, progress, 커밋 해시, 구현 노트 — 잔여 작업과 "구현 중 확정" 사항 포함).
   부분 구현(stub·명세 대기)은 정직하게 in_progress + 잔여 명시.
4. **역링크**: `register_module` (생성된 .tsx/화면 code_module 등록) +
   `link_ui_component_to_module` (이 화면 구현에서 쓴 UI-NNN id ↔ 생성된 .tsx 파일 경로(MOD)).
   역링크 완료 → 다음 세션에서 중복 구현 방지.
   대상 UI-NNN 은 `_shared/ui-catalog.md` 카탈로그 인덱스의 id 로 식별.
5. **키트 현황 갱신**: `SCREENS.md` 화면별 구현 완료 상태 + "구현 완료 기록" 단락(브랜치/커밋/운영 전 확인 잔여) — 커밋.
   프로젝트 `CLAUDE.md` 의 `mc-logi-screen-kit` 블록도 갱신 (해당 도메인 행 구현 현황 1줄 + ⚠️ 변경 재반영 필요 표식 해제).
6. **mc-logi-update 권고**: Phase 4 에서 적재한 "구현 중 확정/설계 불일치" 목록을 사용자에게 제시.
   logicraft 설계 ITEM 반영은 mc-logi-update 로 별도 진행 (이 스킬이 직접 설계를 수정하지 않는다).
7. `get_implementation_coverage(scope=domain)` 로 도메인 커버리지 보고.
8. 메모리 저장 문의 (구현 중 확정된 프로젝트 사실 — 키트/레포가 기록 못 하는 것만).

---

## 에러·중단 처리

| 상황 | 대응 |
|---|---|
| 키트 없음 + logicraft 도 불가 | 중단 — 키트가 진실원이므로 키트 없이 구현하지 않음 |
| version-master CHANGED 다수 | 변경 요약 제시 → 사용자 확인 후 진행 (코드 재반영 범위에 포함) |
| RETIRED 화면 발견 | 구현 대상 제외 + SCREENS.md RETIRED 표기 + 코드 제거 검토 알림 |
| ui_component 카탈로그 비어있음 | Phase 0.5 시드 게이트 진행 (skip 불가) |
| `design/` 부재 (고충실 디자인 없음) | 와이어프레임 폴백(하위호환) + 착수 전 1줄 안내: ① `mc-logi-screen-kit` SYNC 로 logicraft SD 디자인 받기 ② logicraft 에 SD 없으면 `mc-logi-screen-design` 으로 생성 후 SYNC. 사용자가 와이어프레임 선택 시 그대로 진행(강제 아님) |
| 카탈로그 외 컴포넌트 필요 | 추정 금지 → 사용자 알림 + register_ui_components 권고 |
| raw hex grep 발견 | 구현자에게 반환 → 디자인 토큰으로 교체 후 재grep |
| logicraft 서버 일시 불가 (Phase 5) | 재시도 (ID 조회로 중복 record 확인) → 계속 불가면 기록 내용 보고에 남기고 재실행 안내 |
| 구현 중 키트 자체 모순 발견 | 키트 ⚠️ 우선순위 → 없으면 사용자 → 결정을 스펙 + IMPREC 노트에 기록 |
| 서브에이전트 BLOCKED | subagent-driven 스킬의 에스컬레이션 절차 따름 |

---

## 참조 파일

- `kit-contract.md` — **키트 ↔ phase 데이터 계약** (어느 키트 파일에서 무엇을 읽어 어느 phase 에 주입하는지).
  Phase 0 진입 시 반드시 읽을 것. 키트 포맷이 바뀌면 이 파일만 갱신.
- `phase-gates.md` — **phase 별 산출물·게이트·재개 조건 상세 + 보고 포맷**.
  게이트 0.5 / 1 / 2 / 3 질문 포맷, 보고 포맷, 재개 선행 산출물 표, 이 스킬이 하지 않는 것 목록.

---

## 진입 멘트

"mc-logi-screen-implement 시작합니다.

대상: `<DOMAIN-ID | SCREEN-NNN,...> <도메인명/화면명>` / 프로젝트: `<project>`
키트: `<docs/screen-design/{slug}-{ID}/>` (last sync `<시각>`, 모드 `<신선/SYNC 필요/없음→screen-kit 선행>`)
재개 지점: `<Phase 0~5>`

키트 게이트부터 진행합니다."
