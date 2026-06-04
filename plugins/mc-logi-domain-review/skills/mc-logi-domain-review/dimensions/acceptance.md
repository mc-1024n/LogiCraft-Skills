# Acceptance Dimension

AC(인수기준)가 도메인의 UC/DFEAT/REQ 를 **빠짐없이·올바르게** 검증하는지 검토. 추적성 종착점(REQ/UC → AC) 무결성 + AC 본문의 **현행성**(폐기·구 모델 검증 여부).

핵심 관계 체인:
- `REQ → (verifies) ← AC`
- `UC → (covered_by_acceptances) → AC`
- `DFEAT → (verifies, DFEAT→AC) → AC` (또는 UC 경유 간접)
- `AC.scenario(given/when/then) ↔ 현행 API/테이블/UC.main_flow`

두 축: 1.커버리지(누락) 2.현행성(stale).

## 입력 보강 (STEP 0)
AC 는 domain_id 직접 안 가질 수 있음(project-level). 귀속 식별: 1.UC.covered_by_acceptances 역추적 2.AC.notes/statement 인용 3.AC.verifies 의 REQ 도메인 귀속. ★ derived_from_use_cases(AC→UC)와 UC.covered_by_acceptances(UC→AC) 양방향 모두 확인(비대칭 ACC-007 흔함). deprecated 대조용 include_retired=true. → 도메인 UC 0건+AC 후보 0건이면 전 룰 skip + unable_to_verify.

## 검토 룰
### 커버리지 — 누락 (ACC-001~003)
- **ACC-001**: 활성 UC covered_by_acceptances 비어있음 → P1 (must/critical → P0), happy만+negative 없음 P2
- **ACC-002**: 활성 DFEAT 검증 AC 부재 (realize UC 경유·직접 verifies 둘 다 0) → P1
- **ACC-003**: 도메인 REQ 검증 AC 부재 (귀속 명확할 때만) → P1, 모호하면 skip

### 현행성 — stale (ACC-004~006)
- **ACC-004**: AC scenario 가 deprecated/폐기 ITEM 인용 → P0 (include_retired 대조)
- **ACC-005**: AC 가 deprecated DFEAT/UC 검증 → P0
- **ACC-006**: AC scenario 가 현행 모델과 불일치 (옇 endpoint/필드) → P1. ★ 이중 인용 의무(AC.when + UC.main_flow 현행 줄 동시).

### 추적성 링크 (ACC-007)
- **ACC-007**: 완전 고립 AC(verifies·covered_by·derived_from_use_cases 모두 비었) → P1 / 단방향 UC 누락 → P1 / 역방향 비대칭(derived_from_use_cases 비었으나 UC.covered_by에 등록) → P2. derived_domain_ids 는 자동계산 — derived_from_use_cases만 채움.

### 품질 (ACC-008)
- **ACC-008**: scenario 부재/빈약 (statement만, given/when/then 없음) → P2, verification_method 미지정 P2

## Gap 분류 코드
- `D<NNN>-ACC-001`~`008` (YAML dimension=acceptance, prefix ACC)

## auto_fixable 정책
- ACC-001/002/003 → `false` / ACC-004/006 → `false` / ACC-005 → `false`
- ACC-007 forward 등록 누락(UC.covered_by에 추가) → `true` / 역방향 비대칭(AC.derived_from_use_cases에 추가) → `true` / 완전 고립 → `false`
- ACC-008 → `false`

## cross-dimension hint
- ACC-004/005 ↔ STL-009 / ACC-002 ↔ COV-002.
