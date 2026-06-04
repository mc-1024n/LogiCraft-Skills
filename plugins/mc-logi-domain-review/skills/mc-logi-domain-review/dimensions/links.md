# Links Dimension

forward/backward link 무결성 검토. analyze_impact + get_neighbors 활용.

## 검토 룰
- **LINK-1**: DFEAT.implemented_by_endpoints 정합 — description 에 "API-XXX" 인용했는데 필드에 없음 → P0
- **LINK-2**: API.implements_features 역방향 — DFEAT 매핑 있는데 빈 implements_features → P1
- **LINK-3**: SEQ.invokes_apis 정합 → 누락 P1
- **LINK-4**: SEQ.realizes_use_cases 정합 → 누락 P0 (UC 추적성 끊김)
- **LINK-5**: SCREEN.consumes_apis 정합 → sections에 있는데 없음 P1, 있는데 안씬 P2
- **LINK-6**: SCREEN.realizes_use_cases / required_roles → required_roles 비어있음 P1
- **LINK-7**: ERD persists 양방향 → 테이블 책임 DFEAT 없음 P1
- **LINK-8**: unresolved_links > 0 → P0/P1
- **LINK-9**: deprecated ITEM 참조 잔재 → P0
- **LINK-10**: UC.realizes_dfeats 비어있음 (도메인 DFEAT 존재) → P1 (후보 1건 auto=true, N건 false)
- **LINK-11**: UC.realizes_dfeats 의 DFEAT 도메인 불일치 → P1

## Gap 분류 코드
- `D<NNN>-LINK-001`~`011` (위 순서)

## auto_fixable 정책
- LINK-001~006: 단순 link 필드 보강 → `true`
- LINK-007: → `false`
- LINK-008: 원인 분석 필요 → `false`
- LINK-009: 단순 청소 → `true`
- LINK-010: 후보 1건이면 `true`, N건 `false`
- LINK-011: → `false`

## Evidence 인용 룰
- get_neighbors 응답 인용·description ITEM ID 직접 quote·analyze_impact.severity_score.
