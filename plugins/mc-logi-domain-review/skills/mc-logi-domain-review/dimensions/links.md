# Links Dimension

forward/backward link 무결성 검토. analyze_impact + get_neighbors 활용.

## 검토 룰

### LINK-1: DFEAT.implemented_by_endpoints 정합
- DFEAT description에 명시된 API endpoint vs implemented_by_endpoints[] 일치
- description에 "API-XXX" 인용했는데 implemented_by_endpoints에 없음 → P0

### LINK-2: API.implements_features 역방향
- API가 어떤 DFEAT.implemented_by_endpoints에 포함되면, API.implements_features에 그 DFEAT의 specializes_feature(FEAT-XXX) 또는 DFEAT 자체 인용 필요
- 빈 implements_features + DFEAT 매핑 있음 → P1

### LINK-3: SEQ.invokes_apis 정합
- SEQ messages[].item_ref가 가리키는 API + SEQ description에 인용된 API → invokes_apis[]에 모두 포함되어야 함
- 누락 → P1

### LINK-4: SEQ.realizes_use_cases 정합
- SEQ title·description에 "UC-XXX" 인용 → realizes_use_cases[]에 포함되어야 함
- 누락 → P0 (UC 추적성 끊김)

### LINK-5: SCREEN.consumes_apis 정합
- SCREEN sections[].references_apis 합집합 vs consumes_apis[] 일치
- sections에 있는데 consumes_apis에 없음 → P1
- consumes_apis에 있는데 sections에 사용 안 함 → P2 (잔재 가능성)

### LINK-6: SCREEN.realizes_use_cases / required_roles
- SCREEN backing UC 명시 (realizes_use_cases) 권장
- required_roles 비어있음 → P1 (보안 정책 미정의)

### LINK-7: ERD persists 양방향
- DFEAT.persists_in_tables 테이블이 도메인 ERD에 존재하는지 (텍스트 매칭)
- ERD 테이블인데 어떤 DFEAT도 persists_in_tables에 포함 안 함 → P1 (테이블 책임 DFEAT 없음)

### LINK-8: unresolved_links 확인
- 도메인 ITEM 중 unresolved_links > 0 → P0/P1 (severity는 unresolved 대상에 따라)
- get_neighbors로 확인

### LINK-9: deprecated ITEM 참조 잔재
- description / sections / messages에 deprecated 상태 ITEM 인용 검색
- 발견 시 P0 (cascade 누락)

### LINK-10: UC.realizes_dfeats 정합 (도메인 직접 매핑)
- UC가 realizes_features=[FEAT-X] 만 있고 realizes_dfeats 비어있음
- 그런데 도메인 안에 `DFEAT WHERE specializes_feature=FEAT-X AND domain_id=UC.domain_id` 가 존재
- → P1: FEAT 1개 ↔ DFEAT 다수 specialize 케이스에서 UC가 어느 DFEAT 를 실현하는지 모호.
       도메인 안의 실제 구현 단위 (DFEAT) 와 직접 매핑 누락.
- 후보 1건 → 사용자에게 매핑 제안 (auto_fixable=true)
- 후보 N건 → 사용자 선택 필요 (auto_fixable=false)

### LINK-11: UC.realizes_dfeats 와 DFEAT 도메인 일치
- UC.realizes_dfeats=[DFEAT-Y] 인데 DFEAT-Y.domain_id ≠ UC.domain_id
- → P1: cross-domain 매핑은 가능하지만 보통 실수. description 으로 의도 명시 권장.

## Gap 분류 코드
- `D<NNN>-LINK-001`: implemented_by_endpoints 누락
- `D<NNN>-LINK-002`: implements_features 역방향 누락
- `D<NNN>-LINK-003`: invokes_apis 누락
- `D<NNN>-LINK-004`: realizes_use_cases 누락
- `D<NNN>-LINK-005`: consumes_apis 누락 / 잔재
- `D<NNN>-LINK-006`: realizes_use_cases / required_roles 비어있음
- `D<NNN>-LINK-007`: persists_in_tables ↔ ERD 불일치
- `D<NNN>-LINK-008`: unresolved_links 존재
- `D<NNN>-LINK-009`: deprecated 참조 잔재
- `D<NNN>-LINK-010`: UC.realizes_dfeats 비어있음 (도메인 DFEAT 존재)
- `D<NNN>-LINK-011`: UC.realizes_dfeats 의 DFEAT 도메인 불일치

## auto_fixable 정책
- LINK-001/002/003/004/005/006: 단순 link 필드 보강 → `true`
- LINK-007: ERD 테이블 추가/제거 판단 필요 → `false`
- LINK-008: 원인 분석 필요 → `false`
- LINK-009: 단순 청소 → `true` (deprecated ID 텍스트만 제거)
- LINK-010: 도메인 안 specialize DFEAT 후보 1건이면 → `true`, N건이면 → `false`
- LINK-011: 의도 확인 필요 → `false`

## Evidence 인용 룰
- get_neighbors 응답 인용: `forward[]에 API-273 없음, but DFEAT-064.description에 "API-273 신규 단건" 명시`
- description에서 ITEM ID 인용 직접 quote
- analyze_impact.severity_score 인용
