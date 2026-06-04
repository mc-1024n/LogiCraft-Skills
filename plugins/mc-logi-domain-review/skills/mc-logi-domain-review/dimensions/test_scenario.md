# Test Scenario Dimension (통합/시스템 시험 시나리오)

통합(integration)·시스템(system) 시험 시나리오(`test_scenario`, TEST-NNN)가 도메인의 핵심 흐름(cross-UC end-to-end)·책임 요구사항(REQ)·NFR 을 **빠짐없이·올바르게** 검증하는지 + `steps[]` 본문의 **현행성**(폐기·옛 흐름 검증 여부)을 검토.

> AC(acceptance 차원)가 **단위/인수기준** 레벨이면, 이 차원은 **통합·시스템 시험** 레벨 — 여러 UC 를 잇는 end-to-end(integration), REQ/NFR 검증(system). 둘은 짝(검증 산출물 커버리지+현행성).

핵심 관계 체인:
- TEST(integration) → `covers_use_cases` → UC (cross-UC end-to-end 흐름)
- TEST → `exercises_screens` / `steps[].screen_ref` → SCREEN
- TEST(system) → `verifies_requirements` → REQ / `verifies_nfrs` → NFR
- TEST → `related_apis` → API
- TEST.`steps`(action/test_item/input_data/expected/screen_ref) ↔ 현행 UC.main_flow / SCREEN.sections / API 계약

두 축:
1. **커버리지(누락)**: 도메인 핵심 end-to-end 흐름·책임 REQ/NFR 가 시험 시나리오로 검증되는가
2. **현행성(stale)**: TEST steps 가 폐기 ITEM·옛 흐름/화면/API 를 검증하고 있지 않은가

## 입력 보강 (STEP 0 — 검사의 전제)

TEST 는 **project-level**(domain_id 없음, `related_domains[]` 로 도메인 횡단). 도메인 귀속 식별:
1. `list_items(type=test_scenario)` → 다음 중 하나로 도메인 귀속: `related_domains` 에 도메인 포함 / `covers_use_cases` ∩ 도메인 활성 UC ≠ ∅ / `exercises_screens` ∩ 도메인 SCREEN / `verifies_requirements`·`verifies_nfrs` ∩ 도메인 REQ/NFR.
2. 후보 TEST 의 `steps`·`covers_use_cases`·`exercises_screens`·`verifies_*`·`related_apis`·`related_domains`·`status` 본문 `get_item`(도메인 귀속분만, 전수 fetch 금지).
3. deprecated 대조용 `list_items(type=use_case|screen_spec|api_endpoint, include_retired=true)`.

→ 도메인 귀속 TEST 0건이면:
- (a) 도메인이 아직 **통합/시스템 시험 산출물 단계 전**이면 → 전 룰 SKIP + `notes_for_main` 에 "통합/시스템 시험 시나리오 미작성(산출물 단계 전) — 검증 불가/해당없음" 1건(P2).
- (b) 이미 시험 시나리오를 작성한 프로젝트인데 이 도메인만 0건이면 → **TST-001**(P1).

## 검토 룰

### 커버리지 — 누락 (TST-001 ~ TST-002)

#### TST-001: 도메인 핵심 흐름 통합시험 부재
- 도메인의 핵심 **cross-UC end-to-end 흐름**(예: 수신→승인→전달)이 어떤 integration TEST 의 `covers_use_cases` 로도 안 엮임 → **P1** (must/critical 통합 지점이면 **P0**).
- ⚠️ TEST 는 cross-UC end-to-end 라 **모든 UC 가 개별 커버될 필요 없음** — 도메인 주요 사용자 여정/통합 지점 위주. 억지 1:1 금지.
- **검출**: 도메인 활성 must UC 들이 어떤 TEST.covers_use_cases 에도 미등장.

**gap 예시**: "D002 통합시험 부재 — must UC [UC-039 통계수집, UC-004 승인] 을 잇는 integration test_scenario 0건 (covers_use_cases 미등장)"

#### TST-002: 도메인 책임 REQ/NFR 시스템시험 부재
- 도메인 책임 REQ/NFR 가 어떤 system TEST 의 `verifies_requirements`/`verifies_nfrs` 에도 없음 → **P1** (REQ/NFR 귀속 명확할 때만).
- ⚠️ REQ/NFR 전역이라 귀속 모호하면 **skip**.

### 현행성 — stale (TST-003 ~ TST-005)

#### TST-003: steps 가 deprecated/폐기 ITEM 인용 → **P0**
- `steps[].screen_ref` 가 deprecated SCREEN / `related_apis` 가 deprecated API / `steps.action`·`expected` 가 폐기 endpoint·흐름 인용.
- **검출**: `include_retired=true` 목록 대조 + 폐기 경로 패턴.

**gap 예시**: "TEST-012.steps[3].screen_ref=SCREEN-005(deprecated, clip 1차 흡수) / steps[3].action 'GET /api/.../heatmap-points'(API-231 재정의로 폐기 path)"

#### TST-004: covers/exercises/verifies 대상이 deprecated → **P0/P1**
- `covers_use_cases` UC / `exercises_screens` SCREEN / `related_apis` API / `verifies_*` REQ·NFR 가 deprecated (죽은 대상 검증).

#### TST-005: steps 가 현행 모델과 불일치 (옛 흐름/화면/API) → **P1**
- 대상 UC/SCREEN/API 는 **활성**이나 `steps.action`/`expected`/`screen_ref` 가 현행 UC.main_flow·SCREEN.sections·API 계약과 어긋남.
- ★ **이중 인용 의무**: step quote + 현행 UC.main_flow/SCREEN/API 줄 quote 를 **동시에** 제시(false positive 억제).

**gap 예시**: "TEST-008.steps[1] expected '200 {batch_id, replay} — Idempotency-Key 검증' ↔ UC-039 현행 main_flow 'body.batch_id 멱등(Idempotency-Key 폐기)' — 옛 멱등 모델 검증"

### 추적성·품질 (TST-006 ~ TST-007)

#### TST-006: 고립 / 추적 단절 → **P1**
- `covers_use_cases`·`verifies_requirements`·`verifies_nfrs`·`exercises_screens` **전부 비어있음**(무엇을 검증하는지 추적 불가) → P1.
- `related_domains` 미지정(도메인 횡단 추적 단절) → **P2**.

#### TST-007: kind 대비 필수 link/steps 빈약 → **P2**
- kind=integration 인데 `covers_use_cases` 빔 / kind=system 인데 `verifies_requirements`·`verifies_nfrs` **둘 다** 빔 / `steps[].expected` 부재 / `objective` 빈약.

## Gap 분류 코드
- `D<NNN>-TST-001`: 핵심 흐름 통합시험 부재
- `D<NNN>-TST-002`: 책임 REQ/NFR 시스템시험 부재
- `D<NNN>-TST-003`: steps deprecated 인용 (stale)
- `D<NNN>-TST-004`: covers/verifies 대상 deprecated
- `D<NNN>-TST-005`: steps 현행 모델 불일치
- `D<NNN>-TST-006`: 고립 / 추적 단절
- `D<NNN>-TST-007`: kind 대비 필수 link/steps 빈약

(YAML 출력의 `dimension:` 값은 `test_scenario`, gap prefix 는 `TST`)

## auto_fixable 정책
- TST-001/002 부재 → `false` (시나리오 작성 = 사용자)
- TST-003/004/005 stale → `false` (재작성 = 의미 변경)
- TST-006 **link 보강**(covers_use_cases·related_domains 에 명백한 대상 추가) → `true` / 완전 고립 → `false`
- TST-007 → `false`

## Evidence 인용 룰
- 커버리지: `list_items(type=test_scenario) → D002 related/covers 기준 0건; 도메인 must UC=[UC-039,UC-004]`
- stale 대조: `TEST-008.steps[1].expected ↔ UC-039.main_flow 현행 줄` (코드 블록 동시 quote)
- deprecated 대조: `list_items(include_retired=true) → SCREEN-005 retired, TEST-012.steps[3].screen_ref=SCREEN-005`

## cross-dimension hint
- TST-003/004(stale) ↔ `STL-009`(stale 차원 deprecated 참조) 연동.
- TST-001(통합시험 부재) ↔ `ACC-001`(AC 부재) — 검증 산출물 동시 누락이면 함께 보고(`cross_dimension_hint` 에 `D<NNN>-TST-001 ↔ D<NNN>-ACC-001`).

## 주의
- **read-only** — 검출·초안 제안만. 수정은 mc-logi-update (cascade-patterns.md `test_scenario` 섹션과 짝).
- TEST 는 **project-level·cross-domain** — 다른 도메인 위주 TEST(related_domains 에 이 도메인 없음)를 그 도메인 누락으로 보지 말 것.
- 도메인이 아직 시험 시나리오 산출물 단계 전이면 **과잉 TST-001 금지**(SKIP + 안내 1건).
- AC(acceptance 차원)와 짝 — AC=단위/인수기준 레벨, TEST=통합/시스템 레벨. 같은 "검증 산출물 커버리지+현행성" 패밀리.
