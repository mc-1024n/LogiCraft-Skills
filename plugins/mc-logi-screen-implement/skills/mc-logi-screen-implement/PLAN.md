# mc-logi-screen-kit / mc-logi-screen-implement 구현 계획

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Logicraft 화면(screen_spec)과 의존 디자인 ITEM 세트를 로컬 키트로 받아 풀 프론트엔드 화면을 구현하는 user-level 스킬 2종(`mc-logi-screen-kit` 다운로더 + `mc-logi-screen-implement` 오케스트레이터)을 작성한다.

**Architecture:** 기존 `mc-logi-implement-kit`/`mc-logi-implement`(도메인 단위) 골격을 화면(프론트) 특화로 변형. 산출물은 마크다운 스킬 정의 파일(SKILL.md + 동일 디렉토리의 참조 `.md`). 구현 대상 코드가 아니라 "절차 문서"이므로 각 태스크의 검증은 테스트 실행이 아니라 **구조 대조 + 참조 일관성 점검**이다.

**Tech Stack:** Markdown 스킬 정의(YAML frontmatter), logicraft MCP 도구, superpowers 스킬 재사용(brainstorming/writing-plans/subagent-driven-development), `logi-implement-fetcher` 에이전트 재사용.

## Global Constraints

- 출력 경로: `~/.claude/skills/mc-logi-screen-kit/` 및 `~/.claude/skills/mc-logi-screen-implement/` (KLID 레포 밖, user scope). 절대경로 하드코딩 금지 — 스킬 내부 참조는 디렉토리 상대.
- 설계 근거: `mc-logi-screen-implement/DESIGN.md` 의 결정 D1~D6 을 그대로 따른다. 충돌 시 DESIGN.md 우선.
- D1: 스킬 2개. D2: 풀 프론트 구현. D3: 키트=도메인(+`SCREEN-NNN` 좁히기). D4: 구현=화면 점진. D5: 빈 카탈로그→implement Phase 0.5 시드. D6: KRDS 특별취급 금지, 디자인 검증=범용 토큰 룰(예방+가벼운 검출), 전용 정적분석기 안 만듦.
- 산출물 디렉토리명 확정(DESIGN §8-④ 해소): 키트는 `docs/screen-design/{slug}-{ID}/` 에 생성한다 (기존 도메인 키트 `docs/design/` 와 물리 분리·공존).
- fetcher 결정 확정(DESIGN §8-① 해소): **기존 `logi-implement-fetcher` 재사용**. 화면 특화 처리(static_render→wireframe.html 다운로드, ui_component 카탈로그 요약, get_design_md→design.md)는 신규 에이전트 없이 `summary-templates.md` 화면 섹션 + fetcher 호출 프롬프트 지시로 주입. 에이전트 이름 해석/fallback 은 기존 implement-kit SKILL.md "Agent 이름 해석 + 등록 fallback" 절차를 그대로 복제.
- read-only 경계: `mc-logi-screen-kit` 은 logicraft 조회 도구만. `mc-logi-screen-implement` 은 Phase 0.5(register_ui_components / apply_design_preset) 와 Phase 5(create_implementation_record / register_module / link_ui_component_to_module) 에서만 logicraft 쓰기. 그 외 쓰기 금지.
- logicraft 정책 준수: Phase 0.5 시드는 사용자 확정 데이터만 등록(AI 임의 추정 금지), 등록 전 dry 제시 + 게이트.
- 커밋: 사용자가 직접 수행. 각 태스크는 커밋 step 대신 "변경 파일 + 요약 보고" 로 종료.
- 기존 톤/형식 차용: frontmatter 필드(name/description/license/allowed-tools/metadata), 진입 멘트, phase 표, 에러 표, 호출 예시 등 기존 두 스킬의 형식을 그대로 따른다.

---

## 파일 구조 (생성 대상)

```
~/.claude/skills/mc-logi-screen-kit/
├── SKILL.md                 다운로더 오케스트레이션 (Task 4)
├── core-item-set.md         화면 키트 ITEM 세트 = 공유/화면별 2층 결정 규칙 (Task 1)
├── summary-templates.md     타입별 요약 템플릿 — 화면 특화 타입 포함 (Task 3)
├── version-tracking.md      버전 비교 알고리즘 + version-master 포맷 (Task 2, 거의 차용)
├── checklist.md             fetcher hard rules (Task 2, 거의 차용)
└── claude-md-block.md       프로젝트 CLAUDE.md 블록 규약 (Task 2, 경로만 변형)

~/.claude/skills/mc-logi-screen-implement/
├── SKILL.md                 구현 오케스트레이션 Phase 0~5 (Task 7)
├── kit-contract.md          키트 파일 ↔ phase 데이터 계약 (Task 5)
├── phase-gates.md           phase별 게이트·재개·보고 포맷 (Task 6)
├── DESIGN.md                (이미 존재)
└── PLAN.md                  (이 문서)
```

각 태스크의 표준 step 형(문서 작성용):
1. 대응하는 기존 파일을 Read (차용 기반)
2. 화면 버전 작성 (아래 "변경점" 적용)
3. 검증: DESIGN.md 결정과 대조 + 참조 ID/경로/도구명 일관성 grep
4. 변경 파일 + 요약 보고 (커밋은 사용자)

---

## Task 1: screen-kit `core-item-set.md` (화면 ITEM 세트 결정 규칙)

**Files:**
- Create: `~/.claude/skills/mc-logi-screen-kit/core-item-set.md`
- Read 기반: `~/.claude/skills/mc-logi-implement-kit/core-item-set.md`

**Interfaces:**
- Produces: 키트가 다운로드할 ITEM 타입 목록 + "공유 vs 화면별" 분류 + 빌드 순서. Task 3(summary-templates 타입 목록)·Task 4(kit SKILL Phase 2 수집)·Task 5(kit-contract)이 이 분류를 참조.

- [ ] **Step 1:** 기존 `core-item-set.md` Read — Tier 1~3 결정 규칙·build order 형식 파악.
- [ ] **Step 2:** 화면 버전 작성. 변경점:
  - ITEM 세트를 **2층으로 재정의** (DESIGN §4.2):
    - 공유(도메인/프로젝트, 1벌): `design_system`, `ui_component`(전체 카탈로그), `app_shell`, `navigation_tree`, `api_endpoint`(화면 consumes), `constant`, `permission_role`, `implementation_guideline`
    - 화면별(SCREEN마다): `screen_spec`(+static_render), `use_case`, `acceptance`
  - 입력 모드 명시: `DOMAIN-NNN`(도메인 화면 전체) / `SCREEN-NNN[,...]`(좁히기) → 화면 집합 결정 후, 그 화면들의 consumes_apis/required_roles 합집합으로 공유 ITEM 범위 산출.
  - 빌드 순서(implement Phase 매핑): 공유[DS → ui_component → SHELL/NAV → API/CONST/ROLE/GUIDE] → 화면별[screen_spec → UC/AC].
  - 화면이 도메인에 속하지 않을 수 있음(공통 화면) → domain_id 없으면 `get_neighbors(SCREEN-NNN)` 로 의존 역추적.
- [ ] **Step 3:** 검증 — DESIGN §4.2/§3(D3) 와 ITEM 목록 일치 확인. logicraft 타입명이 실제 enum(`design_system`,`ui_component`,`app_shell`,`navigation_tree`,`screen_spec`,`use_case`,`acceptance`,`api_endpoint`,`constant`,`permission_role`,`implementation_guideline`)과 정확히 일치하는지 점검.
- [ ] **Step 4:** 변경 보고.

---

## Task 2: screen-kit `version-tracking.md` + `checklist.md` + `claude-md-block.md` (차용 3종)

**Files:**
- Create: `~/.claude/skills/mc-logi-screen-kit/version-tracking.md`
- Create: `~/.claude/skills/mc-logi-screen-kit/checklist.md`
- Create: `~/.claude/skills/mc-logi-screen-kit/claude-md-block.md`
- Read 기반: 동명의 `mc-logi-implement-kit/` 3파일

**Interfaces:**
- Produces: NEW/CHANGED/UNCHANGED/RETIRED 판정 알고리즘 + version-master.md 포맷(version-tracking); fetcher hard rules(checklist); CLAUDE.md `<!-- mc-logi-screen-kit:start/end -->` 블록 규약(claude-md-block). Task 4·Task 7 이 참조.

- [ ] **Step 1:** 기존 3파일 Read.
- [ ] **Step 2:** `version-tracking.md` 작성 — 알고리즘은 그대로 차용. 변경점: version-master 표에 화면 키트 헤더(domain/screens 집합), 산출 경로 `docs/screen-design/`.
- [ ] **Step 3:** `checklist.md` 작성 — fetcher hard rules 차용. 추가 룰: static_render URL 있으면 wireframe.html 저장 / get_design_md 는 design.md 로 저장 / ui_component 는 카탈로그 1파일로 집약 / spec 텍스트(식별기호·API ID 접미사)를 요약 본문에 그대로 박지 말 것.
- [ ] **Step 4:** `claude-md-block.md` 작성 — 마커명을 `mc-logi-screen-kit` 로, 표 컬럼을 화면 키트용(도메인/화면 수/카탈로그 상태/last sync)으로. 기존 도메인 키트 블록과 공존(다른 마커라 충돌 없음) 명시.
- [ ] **Step 5:** 검증 — 마커명·경로·도구명 일관성 grep. 변경 보고.

---

## Task 3: screen-kit `summary-templates.md` (화면 타입별 요약 템플릿)

**Files:**
- Create: `~/.claude/skills/mc-logi-screen-kit/summary-templates.md`
- Read 기반: `~/.claude/skills/mc-logi-implement-kit/summary-templates.md`

**Interfaces:**
- Consumes: Task 1 의 타입 목록.
- Produces: 각 타입의 구현지향 요약 포맷. fetcher 가 이 섹션을 주입받아 `.md` 생성. Task 4(kit SKILL fetcher 호출)·Task 5(kit-contract 가 "어느 파일에서 무엇을 읽나" 매핑)가 참조.

- [ ] **Step 1:** 기존 `summary-templates.md` Read — 타입별 섹션 형식(frontmatter+배너+본문) 파악.
- [ ] **Step 2:** 화면 특화 타입 섹션 작성/추가:
  - `design_system` → **design.md 원문 보존**(get_design_md 결과) + 토큰 표 요약. 구현 시 "이 토큰만 사용" 근거가 됨.
  - `ui_component` → **카탈로그 1파일**(`ui-catalog.md`): 표로 name/category/props/variants/a11y/code_snippet/implements_in_module_ids. find_ui_component 룩업 인덱스.
  - `screen_spec` → sections[].components[](type·label·triggers_api·io/validation) 표 + consumes_apis/required_roles/realizes_use_cases + wireframe.html 경로 + brownfield 보존 메모. **spec 텍스트 식별기호 UI 금지** 룰 명시.
  - `app_shell`/`navigation_tree` → 슬롯/메뉴 트리 요약(화면이 본문만 담당하는 경계 명시).
  - `api_endpoint`/`constant`/`permission_role`/`use_case`/`acceptance` → 기존 implement-kit 템플릿 차용(프론트 관점 요약: API는 요청/응답 계약·에러 envelope, CONST는 값 표, AC는 Given/When/Then).
- [ ] **Step 3:** 검증 — Task 1 타입 목록과 1:1 대응 확인(누락 타입 없음). DESIGN §4.3 산출물 트리(`_shared/`, `screens/SCREEN-NNN/`)와 파일명 일치.
- [ ] **Step 4:** 변경 보고.

---

## Task 4: screen-kit `SKILL.md` (다운로더 오케스트레이션)

**Files:**
- Create: `~/.claude/skills/mc-logi-screen-kit/SKILL.md`
- Read 기반: `~/.claude/skills/mc-logi-implement-kit/SKILL.md`

**Interfaces:**
- Consumes: Task 1~3 참조 파일.
- Produces: `docs/screen-design/{slug}-{ID}/` 산출물(SCREENS.md/version-master.md/_shared/screens/). Task 5(kit-contract)·Task 7(implement Phase 0)이 이 산출물 계약에 의존.

- [ ] **Step 1:** 기존 implement-kit SKILL.md Read — frontmatter/Phase 1~6/fetcher 호출 패턴/Agent 이름 fallback/진입 멘트 형식.
- [ ] **Step 2:** 화면 버전 작성. 변경점:
  - frontmatter: name=`mc-logi-screen-kit`, description(트리거: "SCREEN-011 화면 키트", "D002 화면 다운로드", "화면 구현 준비", "logicraft 화면 내려받아"), related-skills 에 mc-logi-screen-implement.
  - Phase 1 진입: `DOMAIN-NNN`/`SCREEN-NNN[,...]` 파싱(D3). project_id 식별은 기존과 동일.
  - Phase 2 수집: 화면 집합 결정 → 각 화면 get_neighbors/get_related 로 공유 의존(DS/UI/SHELL/NAV/API/CONST/ROLE/GUIDE) 합집합 산출(core-item-set 규칙). **ui_component 0건이면 카탈로그-빈 플래그 기록**(D5/§4.4).
  - Phase 3 병렬 fetcher: 타입별. screen_spec fetcher 에 static_render 다운로드 지시, design_system fetcher 에 get_design_md 지시. Agent 이름 해석/fallback 절차 복제.
  - Phase 4 산출물: `SCREENS.md`(진입점: 화면 목록·공유자산 인덱스·빌드 순서·**카탈로그 상태 플래그**) + version-master.md + _shared/ + screens/. (도메인 키트의 IMPLEMENTATION.md 대응 = SCREENS.md)
  - Phase 4.5 CLAUDE.md 블록(screen 마커). Phase 5 보고. Phase 6 메모리 문의.
  - read-only 보장 문구.
- [ ] **Step 3:** 검증 — 참조 파일명(core-item-set/summary-templates/version-tracking/checklist/claude-md-block) 정확 인용. 산출물 경로 `docs/screen-design/` 일관. DESIGN §4 전체 대조.
- [ ] **Step 4:** 변경 보고.

---

## Task 5: screen-implement `kit-contract.md` (키트 ↔ phase 데이터 계약)

**Files:**
- Create: `~/.claude/skills/mc-logi-screen-implement/kit-contract.md`
- Read 기반: `~/.claude/skills/mc-logi-implement/kit-contract.md`

**Interfaces:**
- Consumes: Task 4 산출물 구조(SCREENS.md/_shared/screens/).
- Produces: "어느 키트 파일에서 무엇을 읽어 어느 Phase 에 주입하나" 매핑. Task 7(implement SKILL Phase 0 적재)이 참조.

- [ ] **Step 1:** 기존 kit-contract.md Read.
- [ ] **Step 2:** 화면 버전 작성. 매핑:
  - Phase 0 적재: SCREENS.md 전체 + version-master 헤더 + 카탈로그 상태 플래그.
  - Phase 0.5 입력: 카탈로그 플래그 + _shared/design-system.md(archetype, 시드 출처 판단).
  - Phase 1 입력: _shared/api·constant·role + 도메인 슬러그(공유 자산 셋업 대상).
  - Phase 2 입력(화면별): screens/SCREEN-NNN/{SCREEN-NNN.md, wireframe.html, uc/, ac/} + _shared/ui-catalog.md(find_ui_component 룩업).
  - Phase 4 입력: 위 + design-system.md(토큰 룰 D6).
  - Phase 5: 역링크 대상(ui-catalog 의 UI id ↔ 생성 code_module).
- [ ] **Step 3:** 검증 — Task 3/4 의 실제 파일명과 매핑 경로 일치. 변경 보고.

---

## Task 6: screen-implement `phase-gates.md` (phase 게이트·재개·보고)

**Files:**
- Create: `~/.claude/skills/mc-logi-screen-implement/phase-gates.md`
- Read 기반: `~/.claude/skills/mc-logi-implement/phase-gates.md`

**Interfaces:**
- Produces: 각 Phase 산출물·게이트 조건·재개 지점·보고 포맷. Task 7 이 참조.

- [ ] **Step 1:** 기존 phase-gates.md Read.
- [ ] **Step 2:** 화면 버전 작성. 게이트 정의(DESIGN §5):
  - Phase 0.5 게이트(신규): 카탈로그 시드 = logicraft 쓰기 발생 → dry 제시 후 사용자 승인 필수.
  - 게이트 1: 스펙 승인 / 게이트 2: 플랜 승인 / 게이트 3: 머지 방식.
  - 재개 지점: "공유자산부터"/"구현만"/"추적만" → 선행 산출물(스펙/플랜/공유자산 코드) 존재 확인.
  - 보고 포맷: 화면별 구현 현황 표(화면/상태/사용 ui_component/IMPREC).
- [ ] **Step 3:** 검증 — DESIGN §5 phase 와 게이트 수·위치 일치. 변경 보고.

---

## Task 7: screen-implement `SKILL.md` (구현 오케스트레이션)

**Files:**
- Create: `~/.claude/skills/mc-logi-screen-implement/SKILL.md`
- Read 기반: `~/.claude/skills/mc-logi-implement/SKILL.md`

**Interfaces:**
- Consumes: Task 5(kit-contract)·Task 6(phase-gates)·Task 4(kit 산출물)·DESIGN.md.
- Produces: 최종 사용자 진입 스킬.

- [ ] **Step 1:** 기존 implement SKILL.md Read.
- [ ] **Step 2:** 화면 버전 작성. 변경점:
  - frontmatter: name=`mc-logi-screen-implement`, description(트리거: "SCREEN-011 구현", "화면 구현해줘", "키트대로 화면 구현", "D002 화면 구현"), related-skills 에 mc-logi-screen-kit.
  - 핵심 원칙: 키트=진실원 / screen-kit 선행 종속 / phase 게이트 / 추적 역동기화(IMPREC + link_ui_component_to_module) / superpowers 재사용 / **D6 디자인 룰(토큰만·가벼운 검출)**.
  - Phase 0 키트 게이트(없으면 Skill(mc-logi-screen-kit)) → Phase 0.5 카탈로그 시드(3출처 A/B/C, 게이트) → Phase 1 공유 자산 셋업(apiClient/queryKeys/types/zod, 레포 Explore 실측) → Phase 2 스펙(brainstorming+화면 키트 주입) → Phase 3 플랜(writing-plans, 태스크=화면 점진) → Phase 4 화면별 구현(subagent-driven: sections→find_ui_component→react-query→rhf+zod→AC; 토큰 룰 주입+raw hex grep) → Phase 5 반영·추적(lint+build→머지 게이트→IMPREC+register_module+link_ui_component_to_module→SCREENS.md/CLAUDE.md 갱신→mc-logi-update 권고→메모리).
  - 에러 표·진입 멘트·참조 파일(kit-contract/phase-gates) 인용.
- [ ] **Step 3:** 검증 — 참조 파일명·도구명(register_ui_components/apply_design_preset/find_ui_component/get_design_md/create_implementation_record/register_module/link_ui_component_to_module) 실제 존재 확인. DESIGN §5 전체 대조.
- [ ] **Step 4:** 변경 보고.

---

## Task 8: 통합 검증 (두 스킬 정합)

**Files:**
- Read: 위 모든 생성 파일 + DESIGN.md

- [ ] **Step 1:** 두 SKILL.md description 트리거가 겹치지 않고(kit=다운로드/준비, implement=구현) 명확히 분기되는지 점검.
- [ ] **Step 2:** kit 산출물 경로/파일명(SCREENS.md/_shared/screens/) ↔ implement kit-contract 참조가 정확히 일치하는지 grep 대조.
- [ ] **Step 3:** logicraft 도구명을 실제 스키마와 대조(존재·인자명). 특히 신규 도구 register_ui_components·apply_design_preset(seed_components)·link_ui_component_to_module·get_design_md.
- [ ] **Step 4:** DESIGN §3 결정 D1~D6 각각이 어느 파일에 반영됐는지 1:1 체크(커버리지). 누락 시 해당 태스크로 복귀.
- [ ] **Step 5:** read-only/쓰기 경계 점검 — kit 에 쓰기 도구 인용 없음, implement 쓰기는 Phase 0.5/5 한정.
- [ ] **Step 6:** 전체 변경 보고 + 사용자에게 실제 호출 테스트(예: "D006 화면 키트 만들어줘") 제안.

---

## Self-Review (작성자 체크)

- **Spec coverage:** DESIGN §3 D1~D6 → D1(Task 4·7 두 스킬), D2(Task 7 Phase 4), D3(Task 1·4 입력), D4(Task 1 빌드순서·Task 6·7 phase), D5(Task 4 플래그·Task 7 Phase 0.5), D6(Task 7 토큰룰·Task 8-Step3). §4 screen-kit→Task 1~4. §5 screen-implement→Task 5~7. §8 미해결→Global Constraints 에서 fetcher·디렉토리명 확정, 나머지(참조 분량·시드 절차)는 해당 Task 에 흡수. 갭 없음.
- **Placeholder scan:** 각 Task 에 변경점이 구체값으로 명시됨("적절히"/"TBD" 없음). 스킬 본문 전문은 기존 파일 Read+델타 방식이므로 plan 에 전재하지 않되 델타는 구체적.
- **Type consistency:** 파일명(core-item-set/summary-templates/version-tracking/checklist/claude-md-block/kit-contract/phase-gates), 산출물 경로(docs/screen-design/{slug}-{ID}/, SCREENS.md, _shared/, screens/SCREEN-NNN/), 도구명 전 Task 일관.
