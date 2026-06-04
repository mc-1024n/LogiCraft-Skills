# Schema Dimension

데이터 일관성 검토. DFEAT.persists ↔ ERD / API request/response ↔ ERD / SCREEN sections ↔ API schema.

## 검토 룰
- **SCH-1**: DFEAT.persists_in_tables ↔ ERD 테이블 존재 → 없으면 P0 (가공의 테이블)
- **SCH-2**: ERD 논리·물리 페어 정합 → 한쪽만 P1, 테이블 수 다름 P0
- **SCH-3**: ERD 컬럼 description 충실 → 빈 description P1, placeholder P0
- **SCH-4**: API request/response schema vs ERD 컬럼 → 불일치 P1, ERD에 없는 컬럼 P0
- **SCH-5**: SEQ messages DB 동작 vs ERD → 없으면 P1
- **SCH-6**: brownfield.legacy_source.type 유효 (api/table/column/screen/role/module/other) → 위반 P0
- **SCH-7**: 1차 보존 테이블 명시 (1차 그대로 DFEAT → 1차 테이블만) → v2_* 포함 P0
- **SCH-8**: api_endpoint 필드 정합 (path / → 시작, parameters.in enum, responses code 문자열)
- **SCH-9**: SCREEN sections components 일관성 (type enum, triggers_api 실존 API)

## Gap 분류 코드
- `D<NNN>-SCH-001`~`009` (위 순서)

## auto_fixable 정책
- SCH-003 컬럼 description 누락 → `false`
- SCH-006 enum 위반 → `true`
- SCH-008/009 형식 위반 → `true`
- 나머지 → `false`

## Evidence 인용 룰
- ERD tables[] 인용·API schema 직접 quote·1차 테이블명 prefix 확인(TB_*, MNG_*).
