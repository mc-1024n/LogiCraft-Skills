# Policy Dimension

ADR 정책 위반·사용자 정책 위반 검토. 메모리 + ADR 본문에서 정책 자동 추출.

## 정책 추출 절차 (auditor STEP B에서 1회)
1. 메인이 `adr_policies` 첨부
2. 메모리 키워드도 정책으로 간주: "1차 그대로"/"preserved", "BFF 사용 안 함"(ADR-045), "8대 이벤트"(ADR-051), "data scope"(ADR-028), "x-access-token"(ADR-027), "outbound HTTPS"(ADR-036), "EV08000101 이그노어"(ADR-038)

## 검토 룰
- **POL-1**: 1차 보존 위반 → P0
- **POL-2**: BFF 제거 위반 (ADR-045) — tags 'bff' 또는 description "BFF 패턴" → P0
- **POL-3**: 8대 이벤트 범위 위반 (ADR-051) → P1 (쓰러짐·폭력·화재·교통사고·유구·침수·산불·산사태)
- **POL-4**: data scope 위반 (ADR-028) → 지자체 필터 미명시 P0/P1
- **POL-5**: JWT 헤더 통일 위반 (ADR-027) → P1, 인증 토큰 없음 P0
- **POL-6**: outbound/inbound 통신 방향 위반 (ADR-036) → inbound HTTP P0
- **POL-7**: 이그노어 코드값 정합 (ADR-038) — EV99999999 잔재 → P0
- **POL-8**: ADR 인용 누락 → P2, brownfield.decided_by 비어있음+modified P1
- **POL-9**: 자동 추정 brownfield 메타 누락 → STL-004와 중복 (cross_dimension_hint)

## Gap 분류 코드
- `D<NNN>-POL-001`~`009` (위 순서)

## auto_fixable 정책
- POL-002 BFF tags 청소 → `true`
- POL-007 EV99999999→EV08000101 → `true`
- POL-005 헤더 보강 → `true`
- POL-008 ADR 인용 추가 → `true`
- POL-001/003/004/006 → `false`

## Cross-dimension hint
- POL-009 ↔ STL-004 / POL-007 ↔ STL-002.
