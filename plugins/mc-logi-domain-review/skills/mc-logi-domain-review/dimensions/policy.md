# Policy Dimension

ADR 정책 위반·사용자 정책 위반 검토. 메모리 + ADR 본문에서 정책 자동 추출.

## 정책 추출 절차 (auditor STEP B에서 1회 수행)

1. 메인 오케스트레이터가 입력에 `adr_policies` 첨부
2. auditor는 다음 메모리 키워드도 정책으로 간주:
   - "1차 그대로", "1차 보존", "preserved" (1차 시스템 보존)
   - "BFF 사용 안 함", "BFF 제거" (ADR-045)
   - "8대 이벤트" (ADR-051)
   - "data scope", "지자체 사용자 한정" (ADR-028)
   - "x-access-token", "JWT 통일" (ADR-027)
   - "outbound HTTPS", "inbound HTTPS" (ADR-036)
   - "EV08000101 이그노어" (ADR-038)

## 검토 룰

### POL-1: 1차 보존 위반
- DFEAT description에 "1차 그대로" 명시 + persists_in_tables에 v2_* 신규 테이블 포함 → P0
- API path가 1차 패턴과 다른데 brownfield.status=preserved → P0

### POL-2: BFF 제거 위반 (ADR-045)
- 활성 API tags에 "bff" / "bff-host" / "bff-agg" 포함 → P0
- description에 "BFF 패턴" 명시 → P0
- ADR-020 superseded됨, 잔재 정합 필요

### POL-3: 8대 이벤트 범위 위반 (ADR-051)
- 영상 수집·학습·AI 처리 책임 DFEAT (D002/D004/D007 등)에서 8대 외 이벤트 명시 → P1
- 8대: 쓰러짐·폭력·화재·교통사고·유괴·침수·산불·산사태
- 룰셋·필터·드롭다운에 8대 외 active 표시 → P1
- 통계 도메인(DFEAT-061 등)에서 전체 이벤트 처리는 OK

### POL-4: data scope 위반 (ADR-028)
- LOCAL_USER(ROLE-004/005) 접근 가능 SCREEN/API에서 지자체 필터 미명시 → P0
- description에 "지자체 사용자 본인 관할" 표기 없으면 → P1

### POL-5: JWT 헤더 통일 위반 (ADR-027)
- API parameters에 `Authorization` Bearer 사용 (`x-access-token` 아님) → P1
- 인증 필요 API에 어떤 토큰 헤더도 없음 → P0

### POL-6: outbound/inbound 통신 방향 위반 (ADR-036)
- 관제지원 → 중계서버 outbound가 HTTPS 명시 → P1 (정책상 HTTP만)
- 중계서버 → 관제지원 inbound가 HTTP 명시 → P0 (정책상 HTTPS 필수)

### POL-7: 이그노어 코드값 정합 (ADR-038)
- description / sections / messages에 "EV99999999" 잔재 → P0 (정정값 EV08000101)
- 별도 ignore_events 테이블 인용 → P0 (1차 그대로 정책 위반)

### POL-8: ADR 인용 누락
- DFEAT/SCREEN/UC description에 관련 ADR 인용 없음 → P2 (명시 권장)
- brownfield.decided_by 비어있음 + status=modified → P1

### POL-9: 자동 추정 brownfield 메타 누락
- modified/deprecated인데 brownfield.legacy_source.identifier 비어있음 → STL-004와 중복 (cross_dimension_hint)
- 1차 코드 식별자 자동 추정 가능하면 `auto_fixable=true`

## Gap 분류 코드
- `D<NNN>-POL-001`: 1차 보존 위반
- `D<NNN>-POL-002`: BFF 제거 위반
- `D<NNN>-POL-003`: 8대 이벤트 범위 위반
- `D<NNN>-POL-004`: data scope 위반
- `D<NNN>-POL-005`: JWT 헤더 통일 위반
- `D<NNN>-POL-006`: 통신 방향 위반
- `D<NNN>-POL-007`: 이그노어 코드값 잔재
- `D<NNN>-POL-008`: ADR 인용 누락
- `D<NNN>-POL-009`: brownfield 메타 누락

## auto_fixable 정책
- POL-002 BFF tags 청소 → `true` (단순 텍스트 제거)
- POL-007 EV99999999 → EV08000101 정정 → `true`
- POL-005 헤더 보강 → `true` (정형 작업)
- POL-008 ADR 인용 추가 → `true` (description 텍스트 추가)
- POL-001/003/004/006 → `false` (의미 변경, 사용자 결정)

## Evidence 인용 룰
- ADR 인용: `ADR-045 v10 "BFF 사용 안 함" 정책 vs API-188.tags = ['clip', 'send-learning', 'bff']`
- 메모리 인용: 메모리 entry 줄 quote
- description grep: 정책 키워드 위반 라인 직접 인용

## Cross-dimension hint
- POL-009 ↔ STL-004 중복: cross_dimension_hint에 명시
- POL-007 ↔ STL-002 중복: deprecated EV99999999 잔재
