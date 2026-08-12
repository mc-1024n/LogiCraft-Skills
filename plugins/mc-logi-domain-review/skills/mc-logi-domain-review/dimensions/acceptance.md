# Acceptance Dimension

AC(인수기준)가 도메인의 UC/DFEAT/REQ 를 **빠짐없이·올바르게** 검증하는지 검토. 추적성 종착점(REQ/UC → AC) 무결성 + AC 본문의 **현행성**(폐기·구 모델 검증 여부).

핵심 관계 체인:
- `REQ → (verifies) ← AC`
- `UC → (covered_by_acceptances) → AC`
- `DFEAT → (verifies, DFEAT→AC) → AC` (또는 UC 경유 간접)
- `AC.scenario(given/when/then) ↔ 현행 API/테이블/UC.main_flow`

이 차원은 두 축을 본다:
1. **커버리지 (누락)**: 활성 UC/DFEAT/REQ 가 검증 AC 를 가졌는가
2. **현행성 (stale)**: AC 가 폐기됐거나 옛 모델을 검증하고 있지 않은가

## 입력 보강 (STEP 0 — 검사의 전제)

AC 는 `domain_id` 를 직접 안 가질 수 있다(project-level ITEM). 도메인 귀속 식별:
1. 도메인 활성 UC 의 `covered_by_acceptances` 역추적 (1차)
2. AC.notes / AC.statement 의 UC·DFEAT 인용 (예 "UC-026 happy_path", "verifies DFEAT-029")
3. AC.verifies 의 REQ 가 도메인 책임 REQ 인지

⚠️ 검사 전 보강 필요(item_catalog 에 없으면 get_item):
- 활성 UC 의 `covered_by_acceptances` 필드 (UC 측 forward 등록 확인용)
- 후보 AC 의 `scenario`·`verifies`·`derived_from_use_cases`·`notes` 본문 (전수 fetch 금지 — 도메인 귀속 AC 만). ★ `derived_from_use_cases`(AC→UC) 와 UC.covered_by_acceptances(UC→AC) **양방향 모두** 확인 — 한쪽만 등록된 비대칭(ACC-007)이 흔함(schema 가 UC쪽만 등록해도 OK 라 안내하기 때문).
- deprecated 대조용 `list_items(type=use_case|domain_feature|api_endpoint, include_retired=true)`

→ 도메인 활성 UC 가 0건이고 AC 후보도 0건이면 **전 룰 skip** + `notes_for_main.unable_to_verify` 에 "도메인 AC 후보 없음 — 검증 불가" 명시.

## 검토 룰

### 커버리지 — 누락 (ACC-001 ~ ACC-003)

#### ACC-001: 활성 UC 검증 AC 부재
- 활성 UC 의 `covered_by_acceptances` 가 비어있음 → **P1** (priority=must/critical UC 면 **P0**)
- happy AC 만 있고 핵심 분기(탈취·권한·실패)의 negative AC 없음 → **P2**
- **검출**: UC.covered_by_acceptances 길이 = 0, 또는 happy 만 존재(is_negative=true AC 0건)

**gap 예시**: "UC-053(중계서버 장비설정, priority=should) covered_by_acceptances=[] — DFEAT-070 검증 AC 전무"

#### ACC-002: 활성 DFEAT 검증 AC 부재
- 활성 DFEAT 가 (a) realize UC 경유 AC, (b) 직접 verifies AC 어디로도 검증 안 됨 → **P1**
- **검출**: DFEAT 를 realize 하는 활성 UC 들의 covered_by_acceptances 합집합 = 0 **AND** DFEAT→AC verifies = 0

**gap 예시**: "DFEAT-070 — realize UC(UC-053) covered_by_acceptances 비어있고 직접 verifies AC 도 없음"

#### ACC-003: 도메인 REQ 검증 AC 부재 (REQ 귀속 명확할 때만)
- 도메인 책임 REQ 가 어떤 AC 의 verifies 에도 없음 → **P1**
- ⚠️ REQ 는 전역이라 도메인 귀속 모호하면 **skip** (억지 gap 금지)

### 현행성 — stale (ACC-004 ~ ACC-006)

#### ACC-004: AC scenario 가 deprecated/폐기 ITEM 인용
- given/when/then/statement 가 **deprecated API·테이블·UC·폐기 endpoint 경로** 인용 → **P0**
- **검출**: scenario 텍스트에서 ITEM ID·endpoint path 추출 → `include_retired=true` 목록 대조 + 폐기 경로 패턴(예 옛 `/api/ruleset/v2/*`)

**gap 예시**: "AC-036 when '5분마다 trigger PULL job, GET /agent/v1/logs/list' — 폐기 batch PULL 모델 (현재 DFEAT-051 pull-through proxy API-221/222)"

#### ACC-005: AC 가 deprecated DFEAT/UC 를 검증
- AC.notes/statement 가 검증 대상으로 인용한 DFEAT/UC 가 **deprecated** → **P0** (죽은 feature 검증)
- **검출**: AC.notes "verifies DFEAT-XXX" / "UC-XXX" 인용 대상의 status

**gap 예시**: "AC-019 notes 'verifies DFEAT-029' — DFEAT-029 deprecated(DFEAT-051 흡수)"

#### ACC-006: AC scenario 가 현행 모델과 불일치 (옛 endpoint/필드)
- 검증 대상 UC/DFEAT 는 **활성**이나, scenario 가 그 ITEM 의 **현재 본문**(API·필드·흐름)과 어긋남 → **P1**
- **검출**: AC 가 검증한다는 UC 의 main_flow API ↔ AC.when 의 API 비교
- ★ **이중 인용 의무**: AC.when 줄 quote + UC.main_flow/DFEAT.description 현행 줄 quote 를 **동시에** 제시해야 gap 인정. 한쪽만이면 보고 금지(false positive 억제).

**gap 예시**: "AC-037 when 'PATCH /relay/v1/admin/event-types/{cd}/clct-yn (API-091)' vs UC-026 현행 main_flow 'API-249 PATCH + API-262 outbound push' — endpoint 불일치"

### 추적성 링크 (ACC-007)

#### ACC-007: unlinked AC / 단방향 link 비대칭
- AC 가 `verifies`(REQ) 비어있음 **AND** 어떤 UC 의 covered_by_acceptances 에도 없음 **AND** `derived_from_use_cases` 비어있음 → **P1** (완전 고립 AC)
- 단방향 (UC쪽 누락): AC.notes 에 "UC-XXX" 인용하나 UC.covered_by_acceptances 에 이 AC 없음 → **P1** (UC forward 등록 누락)
- ★ 역방향 비대칭 (AC쪽 누락): **AC.`derived_from_use_cases` 비어있으나** (a) 어떤 UC 의 covered_by_acceptances 에 이 AC 가 등록돼 있음, 또는 (b) AC.notes/statement 가 "UC-XXX" 인용 → **P2** (AC→UC link 누락). 추적성(UC→AC)은 충족이라 "고립"은 아니지만, **AC 중심 화면의 "파생 UC" 칸·`derived_domain_ids`(자동 계산) 가 빈칸**으로 남고 AC→REQ 간접 추적·그래프뷰가 단절된다.
  - ⚠️ `derived_domain_ids` 는 `derived_from_use_cases` 에서 **서버 자동 계산** — AC→UC 가 비면 도메인도 자동으로 빔. 직접 채우지 말 것(derived_from_use_cases 만 채우면 도메인 자동 복구).
  - **검출**: `get_item(AC).data.derived_from_use_cases == []` 인데 `get_neighbors(AC).backward` 에 `covered_by` UC 존재 OR notes/statement 에 UC-NNN 인용.

### 품질 (ACC-008)

#### ACC-008: scenario 부재 / 빈약
- statement 만 있고 given/when/then 없음 → **P2** (자동화 불가)
- verification_method 미지정 → **P2**

## Gap 분류 코드
- `D<NNN>-ACC-001`: 활성 UC 검증 AC 부재
- `D<NNN>-ACC-002`: 활성 DFEAT 검증 AC 부재
- `D<NNN>-ACC-003`: 도메인 REQ 검증 AC 부재
- `D<NNN>-ACC-004`: AC scenario deprecated 인용 (stale)
- `D<NNN>-ACC-005`: AC 가 deprecated DFEAT/UC 검증
- `D<NNN>-ACC-006`: AC scenario 현행 모델 불일치
- `D<NNN>-ACC-007`: unlinked AC / forward 등록 누락
- `D<NNN>-ACC-008`: scenario 부재 / 빈약

(YAML 출력의 `dimension:` 값은 `acceptance`, gap prefix 는 `ACC`)

## auto_fixable 정책
- ACC-001/002/003 AC 부재 → `false` (신규 AC = 시나리오 확정 = 사용자)
- ACC-004/006 stale scenario → `false` (재작성 = 의미 변경)
- ACC-005 deprecated 검증 → `false` (deprecate 또는 재작성 판단)
- ACC-007 **forward 등록 누락**(UC.covered_by_acceptances 에 기존 AC id 추가) → `true` / **역방향 비대칭**(AC.derived_from_use_cases 에 UC id 추가 — UC.covered_by 또는 notes 역추적으로 확정) → `true` / 완전 고립 AC → `false`
- ACC-008 scenario 부재 → `false` (내용 작성 필요)

→ Acceptance 차원도 대부분 `auto_fixable=false`. 시나리오·의미 판단이 필요하기 때문.

## Evidence 인용 룰
- UC.covered_by_acceptances 인용: `UC-053.covered_by_acceptances = [] (DFEAT-070 realize)`
- stale 대조: `AC-037.when "PATCH .../event-types/{cd}/clct-yn (API-091)" ↔ UC-026.main_flow "API-249 + API-262"` (코드 블록 동시 quote)
- deprecated 대조: `list_items(include_retired=true) → DFEAT-029 retired, AC-019.notes "verifies DFEAT-029"`

## cross-dimension hint
- ACC-004/005(stale) ↔ `STL-009`(stale 차원 deprecated 참조)와 연동 → `cross_dimension_hint` 에 `D<NNN>-ACC-004 ↔ STL-009`
- ACC-002(DFEAT 미검증) ↔ `COV-002`(DFEAT UC backing) 연동 → DFEAT 가 UC backing 도 없으면 두 차원 동시 보고
