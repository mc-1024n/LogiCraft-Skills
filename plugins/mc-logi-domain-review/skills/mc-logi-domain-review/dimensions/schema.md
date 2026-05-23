# Schema Dimension

데이터 일관성 검토. DFEAT.persists ↔ ERD / API request/response ↔ ERD / SCREEN sections ↔ API schema.

## 검토 룰

### SCH-1: DFEAT.persists_in_tables ↔ ERD 테이블 존재
- DFEAT.persists_in_tables[] 각 테이블명이 ERD에 등록되어 있는지
- 없으면 → P0 (가공의 테이블 인용)

### SCH-2: ERD 논리·물리 페어 정합
- 같은 도메인에 logical(한글)·physical(영문) ERD 페어 존재
- 한쪽만 있으면 → P1 (페어 누락)
- 페어인데 테이블 수 다름 → P0 (정합 깨짐)

### SCH-3: ERD 컬럼 description 충실
- 모든 컬럼에 description 필수 (메모리 정책)
- 빈 description → P1
- "TODO", "..." 같은 placeholder → P0

### SCH-4: API request/response schema vs ERD
- API request_body.schema.properties / responses[code].schema.properties 컬럼명 vs ERD 컬럼명 매칭
- 불일치 → P1 (snake_case vs camelCase 등 일관성)
- API에 있는데 ERD에 없는 컬럼 → P0 (스키마 검증 불가)

### SCH-5: SEQ messages DB 동작 vs ERD
- SEQ messages 중 "INSERT/UPDATE/SELECT <table>" 인용 테이블이 ERD에 존재하는지
- 없으면 → P1

### SCH-6: brownfield.legacy_source.type 유효
- 모든 ITEM의 brownfield.legacy_source.type이 enum (api/table/column/screen/role/module/other) 준수
- "kind", 임의 문자열 → P0 (validation 깨짐)

### SCH-7: 1차 보존 테이블 명시
- "1차 그대로 운영" DFEAT의 persists_in_tables에는 1차 테이블만 (TB_*, 1차 명명 규칙)
- 신규 v2_* 테이블 포함 → P0 (정책 위반, ADR-041 등 cascade 가능성)

### SCH-8: api_endpoint 필드 정합
- API path가 `/`로 시작하는지 (memory: logicraft API path validation)
- parameters[].in: path / query / header / cookie 유효 enum
- responses[code] code 패턴: "200" 같은 문자열 (정수 거부)

### SCH-9: SCREEN sections components 일관성
- components[].type enum 유효 (memory: value 키 거부)
- triggers_api / references_apis가 실제 존재 API인지

## Gap 분류 코드
- `D<NNN>-SCH-001`: DFEAT 테이블 ERD 부재
- `D<NNN>-SCH-002`: ERD 페어 정합 깨짐
- `D<NNN>-SCH-003`: ERD 컬럼 description 누락
- `D<NNN>-SCH-004`: API ↔ ERD 컬럼 불일치
- `D<NNN>-SCH-005`: SEQ DB 동작 ERD 부재
- `D<NNN>-SCH-006`: brownfield enum 위반
- `D<NNN>-SCH-007`: 1차 보존 + v2_* 테이블 혼재
- `D<NNN>-SCH-008`: api_endpoint 필드 형식 위반
- `D<NNN>-SCH-009`: SCREEN component 형식 위반

## auto_fixable 정책
- SCH-003 컬럼 description 누락 → `false` (실제 정보 필요)
- SCH-006 enum 위반 → `true` (단순 enum 정정)
- SCH-008/009 형식 위반 → `true` (path prefix 추가 등)
- 나머지 → `false` (데이터 구조 결정 필요)

## Evidence 인용 룰
- ERD tables[] 인용: `ERD-022.tables[]: [v2_relay_video_batches, v2_video_assets, ...], DFEAT-064.persists_in_tables에 ls_data_raw 명시했으나 ERD에 없음`
- API schema 직접 quote
- 1차 테이블명 prefix 확인 (TB_*, MNG_*)
