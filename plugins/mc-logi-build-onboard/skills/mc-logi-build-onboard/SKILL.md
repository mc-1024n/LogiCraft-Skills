---
name: mc-logi-build-onboard
description: 현재 프로젝트에 맞는 "구현 오케스트레이션 세트"(수정 dispatch + 설계 backfill + (greenfield 시) build 스킬 + (앱 표면 있으면) E2E 시나리오 저작·실행·정합점검 3종 + 도메인별 implementer·독립 qa-verifier 에이전트)를 빌드/온보딩하는 메타 스킬. KLID(brownfield-submodule)·Graph-RAG(greenfield-monolith)에서 교차 추출한 불변 뼈대(templates/_invariant)에, 프로젝트 구조를 판정한 13개 스위치(toggles.md)로 조각(templates/_switched)을 조립하고 슬롯을 채워 방출한다. 아키타입 2종(프리셋)을 기본으로, 프리셋 밖 구조는 스위치를 개별 판정해 조합. Discovery(LogiCraft project_id + repo 스캔) → 스위치 확정 게이트 → 슬롯 인터뷰 → 조립 → 도메인 지침 초안(설계 정독·근거첨부) → 검증 게이트 순. 사용자가 "이 프로젝트 온보딩해줘", "구현 세트 만들어줘", "dispatch/build 스킬 세팅", "/mc-logi-build-onboard" 라고 하면 실행. AI 임의 추정 금지 — 설계·repo 근거 없는 값은 비우고 보고, 게이트에서 사용자 확정.
metadata:
  version: 1.0.0
---

# mc-logi-build-onboard — 구현 오케스트레이션 세트 온보딩

프로젝트마다 손으로 dispatch/build/backfill 스킬 + 도메인 에이전트를 포팅하면 매번 미묘하게 달라진다(드리프트). 이 스킬이 그걸 접는다 — **불변 뼈대 + 스위치 조각 + 슬롯**을 조립해 **일관된 세트**를 방출한다.

## 진실원 파일 (이 스킬이 참조)

| 파일 | 역할 |
|---|---|
| `toggles.md` | ★ 두뇌 — 13개 스위치 정의·판정신호·프리셋 2종·프리셋 밖 조합규칙·슬롯 목록 |
| `templates/_TEMPLATING.md` | 치환 문법(`{{slot}}`·`<!-- IF -->`·`<!-- INSERT -->`)·슬롯 카탈로그·방출 위치·검증 규칙 |
| `templates/_invariant/*` | 🟩 항상 생성 (dispatch·backfill·implementer·qa-verifier) |
| `templates/_switched/*` | 🟨 스위치 on 일 때만 (build·conventions·work_claim·phase0·layers·e2e 4종) |

**시작 전 반드시 `toggles.md` 와 `templates/_TEMPLATING.md` 를 정독한다.** 스위치 판정·조립 규칙이 거기 있다.

## 원칙 (전 파이프라인 관통)

- **AI 임의 추정 금지** — 스위치·슬롯 값은 repo/LogiCraft 근거 또는 인터뷰로만 확정. 근거 없으면 비우고 "정보부족" 보고(placeholder·가짜 ID 금지).
- **게이트 우선** — 스위치 확정·슬롯·도메인 지침·최종 검증 4지점에서 사용자 확인. 나머지 자동.
- **기존 세트 존중** — 이미 `{{prefix}}-dispatch` 등이 있으면 덮어쓰기 전 diff 보고 후 확인(재온보딩=업그레이드 모드).
- **방출만, 실행 안 함** — 이 스킬은 세트를 만들 뿐 구현을 돌리지 않는다. 구현은 만들어진 build/dispatch 로.

---

## 파이프라인

### Phase 0 — Discovery (자동 수집)
스위치 판정신호와 슬롯 값을 모은다. **repo 스캔 + LogiCraft 이중**.

**A. repo 스캔**
- 코드 루트에 실제 소스가 있나 / README·빈 폴더뿐인가 → `has_build` 신호.
- `.gitmodules` 존재 / 코드 루트가 서브모듈 폴더들인가 → `commit_strategy`·`code_boundary` 신호.
- 빌드 파일(pyproject/build.gradle/package.json/Makefile) → `{{build_cmds}}`·`{{tech_stack_table}}`·`{{package_layout}}` 원자료.
- `frontend/`·`package.json` → 프론트 트랙 유무 → `{{frontend_stack_block}}`.
- `CLAUDE.md` → `{{project_id}}`·도메인 표·주의사항.
- **E2E 신호** → `e2e_track`: 브라우저로 조작 가능한 앱 표면(프론트 앱·라우트·dev 스크립트)이 있나 · 기존 `playwright.config.*`/`cypress.config.*`/spec 폴더 · `grep -r "data-testid"` 건수(→ `e2e_selector`) · 인증 라우트 유무(→ `e2e_auth`).

**B. LogiCraft 조회** (project_id 확보 후)
- `project_id` 없으면 `list_projects({q})` 로 검색·사용자 확정.
- 도메인 목록·이름 → 매핑표 골격. `get_project_kickoff` → 기술스택·아키텍처 결정.
- ADR(진실원·정책) → 도메인 지침 초안 근거(Phase 4).
- 로컬 키트 `docs/design/*/IMPLEMENTATION.md` 존재·last sync → `has_build` 보강, `{{domain_kit_root}}`.

**C. E2E 실측** (`e2e_track` 후보가 on 일 때만 — toggles.md §5.2)
E2E 슬롯은 **읽어서 얻은 값이 실제와 다른 경우가 흔하다.** 조립 전에 직접 확인한다:
- 앱을 실제로 띄워본다 → `{{e2e_service_up}}`·`{{e2e_base_url}}`·`{{e2e_api_base}}` 확정. (문서와 다른 기동 명령, 죽은 프로세스가 잡은 포트 등이 여기서 드러난다.)
- 인증 우회를 실제로 태워 세션이 발급되는지 본다 → `{{e2e_auth_bypass}}`. 우회가 특정 환경설정에 의존하면(예: 실서비스 IdP 를 가리키면 우회 불가) 그 조건을 `{{e2e_env_caveat}}` 에 적는다.
- 테스트 데이터 삭제 API 를 실제로 호출해본다 → `{{e2e_cleanup}}`. 오삭제 방지 장치(확인 문구 일치·권한·2단계)는 **문서에 없고 400 응답으로만 드러나는** 경우가 많다.
- **권한을 실제로 써본다** → `{{e2e_roles}}`·`{{e2e_fixture_setup}}`. 우회로 얻은 계정이 관리·승인 API 를 **실제로 호출할 수 있는지** 확인한다. 권한 부족은 **403 으로만 드러나며**, 그때 "미커버"로 넘기면 그 역할의 시나리오가 통째로 빠진다. 권한 부여가 필요하면 **되돌리는 방법까지 함께 확정**한다.
- 확인 못 한 값은 **비우고 "정보부족"으로 표시**한다(추정 금지 — 추정값을 넣으면 3종 스킬 전체가 그 위에서 깨진다).

산출: **스위치별 추정값(신호 근거 포함) + 슬롯 원자료**. 자동판정 불가분(work_claim·계층내용·E2E 우회수단)은 "인터뷰 필요"로 표시.

### Phase 1 — 아키타입/스위치 확정  🚦게이트①
1. Discovery 신호로 **가까운 프리셋(P1 greenfield-monolith / P2 brownfield-submodule)** 선택.
2. `toggles.md §4` 조합규칙으로 프리셋과 다른 스위치를 **오버라이드** 계산(프리셋 밖 구조도 여기서 흡수).
3. 스위치 표를 사용자에게 제시 — 각 행에 `값 · 근거(신호) · ⚠️override 여부 · 인터뷰필요`:
```
스위치               값        근거
has_build            off       코드 루트에 기존 소스 존재
code_boundary        package   단일 repo, 서브모듈 없음
conventions_location shared ⚠️  monolith 균일 스택 → override(P2 는 embedded)
work_claim           ?         인터뷰 필요 (팀 작업 여부)
...
프리셋: P2(brownfield) 기반 + monolith 오버라이드(package/single/shared)
```
사용자 확인·수정 후 스위치 확정. (프리셋 밖 새 조합이 반복되면 toggles.md 에 P3 로 승격 제안.)

### Phase 2 — 슬롯 인터뷰  🚦게이트②
자동판정 불가한 슬롯만 확정:
- `{{prefix}}` (에이전트·스킬 접두사) — 프로젝트 약칭.
- `work_claim` on/off (팀 구성 질문).
- `{{layer_rounds}}` (dependency_layers=on 시) — 계약 의존 근거로 계층 순서. LogiCraft 계약 의존 참고해 초안 제시 후 확정.
- `{{commit_forbidden}}` — 커밋금지 파일(secrets·설정).
- 매핑표의 code_root·에이전트명 최종 확인.
- **E2E 계정 전략** (`e2e_track=on` 이고 `e2e_auth != none` 일 때 — toggles.md §5.3). **자동판정 불가 — 반드시 묻는다.** 안 물으면 권한 필요한 시나리오가 403 으로 조용히 빠지거나, 급한 대로 자격증명이 spec 에 하드코딩돼 저장소에 커밋된다.
  - `{{e2e_roles}}` — 시나리오에 필요한 역할과 **각 역할의 획득 방법**(가입만/승인필요/역할부여필요). 부여가 필요하면 되돌리는 방법도.
  - `e2e_account_strategy` — 자급자족으로 만들 수 있나, 받아야 하나. **"데이터가 쌓여 있어야만 검증되는 시나리오(대량 목록·통계·이력)가 있습니까?"** 를 물어 판정한다. 있으면 `seed`/`mixed`.
  - `{{e2e_seed_accounts}}` — `seed`/`mixed` 면 **어떤 env 키로 주입할지와 용도**(자격증명 값 자체는 받지 않는다).
  - `{{e2e_groups}}` — 그룹 태그 체계. 기본 `@provisioning`/`@smoke`/`@regression` 제시 후 확정.

### Phase 3 — 조립 (assembler)
`_TEMPLATING.md` 규약대로 **결정적 치환**한다(외부 엔진 없음 — 이 스킬이 직접):
1. **방출 목록 결정** (스위치 기준):
   - 항상: `{{prefix}}-dispatch/SKILL.md`, `{{prefix}}-design-backfill/SKILL.md`, `{{prefix}}-qa-verifier.md`, 도메인마다 `{{domain_agent_name}}.md`.
   - `has_build=on`: `{{prefix}}-build/SKILL.md`.
   - `conventions_location==shared`: `.claude/conventions.md`.
   - **프론트 트랙 있으면**(repo `frontend/`·`package.json` 또는 키트에 `screen_spec` 존재): `_switched/web-implementer.tmpl.md` → `{{prefix}}-web-implementer.md`. 없으면 생성 안 함.
   - `e2e_track=on`: `.claude/e2e-conventions.md` + E2E 스킬 3종(`{{prefix}}-e2e-author`/`-run`/`-verify`). 규약 파일을 먼저 만들고 3종이 그것을 참조하게 한다(슬롯 값은 규약 한 곳에만 — 3종에 중복 박지 않는다).
2. **각 파일**: 해당 템플릿 Read → `<!-- INSERT ... IF sw -->`(on 이면 조각 삽입, off 삭제) → `<!-- IF sw -->/<!-- ELSE -->/<!-- ENDIF -->` 해소 → `{{slot}}` 치환 → 방출 경로에 Write.
3. **implementer 는 도메인마다 1회** 인스턴스화(도메인별 슬롯). `{{domain_guidance}}` 는 Phase 4 에서 채우므로 여기선 골격 표시로 두고 Phase 4 후 갱신.

### Phase 4 — 도메인 지침 초안 (설계 정독)  🚦게이트③
`toggles.md §5.1` 대로, 도메인마다 특화지침(책임·경계 / 진실원·엔티티 / 함정 top / 정책·제약 / 코드 레이아웃)을 **근거 ITEM ID 붙여** 초안한다.

**진실원 결정 (★ 로컬 키트는 LogiCraft 의 스냅샷 — 궁극 진실원은 LogiCraft):**
1. **신선도 먼저 판정** — 키트 `version-master`/last sync 와 `_raw` 의 `current_version` 을 LogiCraft 와 대조해 **fresh / stale / 없음** 을 도메인별로 판별.
2. **fresh 면 로컬 키트가 진실원** — `IMPLEMENTATION.md` + 타입별 요약(ADR/ERD/DFEAT/CONST/policy) + `_raw/*.json`. 이미 구현지향 정제돼 함정·CONST·진실원 뽑기 좋음. (묻지 않고 진행)
3. **★ stale 면 사용자에게 3택 확인 (자동 결정 금지)** — 어느 도메인 키트가 stale 이면 게이트에서 묻는다:
   - **(a) 현재 로컬 키트 그대로** — 이 버전 스냅샷 기준으로 초안. 빠르나 최신 아닐 수 있음(선택 사실을 지침에 명기).
   - **(b) 키트 업데이트 먼저** — `/mc-logi-implement-kit` SYNC 로 해당 도메인 재동기화 후, 갱신된 키트로 초안. (권장 — 이후 build/구현도 최신 키트 사용)
   - **(c) LogiCraft(live) 직접** — 키트 무시하고 `get_item`/`list_items` 로 라이브 설계에서 추출. 키트 SYNC 없이 최신 반영.
   - drift 요지(무엇이 몇 버전 차이)를 함께 제시해 사용자가 판단하게 한다.
4. **키트 없음/부분이면 LogiCraft(live)가 1차** — brownfield 등 키트 미생성 아키타입(`has_build=off`)은 `get_item`/`list_items`(ADR·ERD·DFEAT·CONST) + 코드에서 직접 추출.
- (도메인 많으면 도메인별 Task 에이전트 병렬 가능.)
- **근거 없으면 비우고** "정보부족 — 설계 보완 또는 첫 구현 중 확인"으로 보고. 지어내기 금지.
- 설계가 얇거나 LogiCraft 미등록이면 골격만 + "첫 구현 후 노하우로 축적" 명시.
- 초안을 사용자에게 제시·확정 → `{{domain_guidance}}` 채워 implementer 파일 갱신.
- **프론트 트랙 있으면 `{{web_guidance}}` 도 동일 방식으로 초안** — 단 근거는 `screen_spec`(sections·consumes_apis·required_roles·uses_constant) + 디자인시스템(DS) + 소비 API 계약. 백엔드 ERD/DFEAT 가 아니라 화면·계약 관점. 근거 없으면 비우고 정보부족 보고.
- 노하우 섹션은 온보딩에서 비워둔다(구현하며 축적).

### Phase 5 — 검증 · 완료  🚦게이트④
`_TEMPLATING.md §6` 검증:
- 스킬 본문이 참조하는 **모든 `{{prefix}}-*` 에이전트명**이 `.claude/agents/` 에 실제 존재 (교차검증 — 참조는 있는데 파일 없음 = 실패).
- 매핑표 도메인 수 == 생성된 implementer 수.
- `conventions_location==shared` 면 `.claude/conventions.md` 존재 + 참조 경로 일치.
- `e2e_track=on` 이면 `.claude/e2e-conventions.md` + 스킬 3종 존재 + 3종이 모두 규약 경로를 참조.
- `e2e_auth != none` 이면 **`{{e2e_storage_dir}}` 가 `.gitignore` 에 있는지 확인**한다(로그인 세션 그 자체이므로 커밋되면 안 된다). 없으면 추가하고 보고.
- 남은 `{{...}}`·`<!-- IF/INSERT/ELSE/ENDIF ... -->` 마커 없음(미치환 스캔).
- **비운 E2E 슬롯 목록 보고** — 확인 못 해 비운 것을 "정보부족 — 첫 저작 시 확인"으로 명시(조용히 넘기지 않는다).
- 부트스트랩 파일 생성(아래 §부트스트랩).
- **보고**: 생성 파일 목록 · 스위치 표 · 비운 슬롯(정보부족) · 다음 액션(build 실행 등).

---

## 부트스트랩 파일 (dispatch/build 가 전제하는 것 — 함께 생성)

세트가 동작하려면 아래가 있어야 한다(없으면 dispatch 첫 실행이 깨짐). Phase 5 에서 생성:

- `{{change_orders_path}}_TEMPLATE.md` — CO 골격. 상단 헤더 표(제목·대상 도메인·구현상태·LogiCraft 설계반영<!-- IF work_claim -->·work_claim 행<!-- ENDIF work_claim -->) + §1 배경 · §2 변경 요지 · §3 도메인별 변경 상세(에이전트 구현용) · §4 영향·리스크 · §5 검증 · §6 관련 설계 ITEM(backfill 예정) · §7 구현 로그.
- `{{change_orders_path}}MASTER.md` — CO 추적 표: `CO번호 · 제목 · 대상도메인 · 구현상태 · 설계반영(⏳/🎨/—) · 커밋 · 생성일`. 빈 표 + 컬럼 헤더로 초기화.
<!-- IF has_build -->
- `docs/design/BUILD-MASTER.md` — 도메인별 <!-- IF dependency_layers -->계층·<!-- ENDIF dependency_layers -->구현 상태(⬜/🔨/✅/⚠️) 표.
<!-- ENDIF has_build -->
- (선택) 루트 `CLAUDE.md` 에 세트 사용법 안내 블록 추가 제안(수정·구현·backfill 진입점).

> ⚠️ `_TEMPLATE.md` 의 work_claim 헤더 행은 `work_claim=on` 일 때만. 참고 실물: KLID `.claude/change-orders/_TEMPLATE.md`.

## 게이트 요약
1. Phase 1 — 아키타입/스위치 확정
2. Phase 2 — 슬롯 인터뷰
3. Phase 4 — 도메인 지침 초안 확정 (+ 키트 stale 시 진실원 3택: 현재키트/업데이트/LogiCraft)
4. Phase 5 — 최종 검증
그 외 자동.

## 재온보딩 (업그레이드 모드)
이미 세트가 있는 프로젝트에서 다시 실행하면: 기존 파일과 새 조립 결과를 **diff** 해 보여주고, 스위치 변경(예: 팀 합류 → work_claim on)만 반영. 도메인 지침의 축적된 노하우는 **보존**(덮어쓰지 않음).
