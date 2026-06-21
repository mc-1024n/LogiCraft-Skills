# Schema Conformance Dimension

JPA 엔티티 + Flyway 마이그레이션(실제 코드)이 키트 `erd` ITEM(설계 진실원)의 테이블/컬럼/타입/제약/인덱스와 정합하는지 검토. 런타임 스키마 표류(컬럼 누락·타입 불일치·제약/인덱스 누락) 검출 + 키트에 없는 코드 객체(extra_code) 식별.

핵심 관계:
- `키트 ERD 테이블/컬럼/타입/제약/인덱스` ↔ `마이그레이션 SQL CREATE/ALTER` ↔ `@Entity/@Table/@Column 엔티티`
- **마이그레이션 SQL = 런타임 스키마의 적재 진실원** — 엔티티 매핑과 SQL 이 충돌하면 **SQL 기준**(실제 DB 에 적용되는 것은 마이그레이션). 엔티티는 보조 증거(매핑 의도)로만 본다.

이 차원은 두 축을 본다:
1. **정합 (drift)**: 키트가 정의한 테이블/컬럼/타입/제약/인덱스가 마이그레이션·엔티티에 빠짐없이·올바르게 반영됐는가
2. **역방향 (extra)**: 마이그레이션·엔티티에 있으나 키트 ERD 에 없는 객체가 있는가 (단 1차 보존 스키마는 정상 — 제외)

## 입력 보강 (STEP 0 — 검사의 전제)

**키트 측 적재:**
- 키트 `erd/*.md`(구현지향 요약) + `erd/_raw/*.json`(원본) 의 테이블 정의 적재 — 테이블명·컬럼명·타입·길이·nullable·PK/FK·CHECK/UNIQUE·인덱스(특히 부분 UNIQUE).
- 보존 정책 식별용: 키트 `_domain.md` / `IMPLEMENTATION.md` 의 "보존 영역"·"1차 보존 테이블"·"기존 스키마" 단락. (extra_code 오탐 제외 기준 — SCH-CONF-006)

**코드 측 적재 (마이그레이션이 진실원):**
- Glob `src/main/resources/db/migration/V*.sql` **전수** Read → CREATE TABLE / ALTER TABLE / CREATE INDEX / CONSTRAINT 전부 인벤토리화. (Flyway 는 누적 적용이므로 **모든 V 파일을 합산**한 최종 스키마가 런타임 상태 — 한 파일만 보지 말 것.)
- serena `get_symbols_overview` / `find_symbol` 로 `@Entity`/`@Table`/`@Column` 엔티티 심볼 적재 (보조 증거).
- ⚠️ **충돌 시 SQL = 기준**: 엔티티 `@Column(length=N)` 과 SQL `varchar(M)` 이 다르면 런타임은 SQL(M). finding 은 SQL 값으로 기술하고 엔티티 불일치는 별도 코드 표류로 본다.

→ 키트 ERD 테이블이 0건이고 마이그레이션 SQL 도 0건이면 **전 룰 skip** + `notes_for_main.unable_to_verify` 에 "도메인 ERD/마이그레이션 부재 — 검증 불가" 명시. (억지 finding 생성 금지)

## 검토 룰

각 룰: 조건 → severity → `finding_type` → `bucket` → 검출 → gap 예시. confidence 등급·반증 우선·evidence(kit_item+code_ref) 규약은 **`checklist.md` §3~§5 인용** (변형 금지).

### 정합 — 누락/표류 (SCH-CONF-001 ~ SCH-CONF-005)

#### SCH-CONF-001: 테이블 미생성
- 키트 ERD 가 정의한 테이블이 **어떤 마이그레이션 SQL 에도 CREATE TABLE 없음** → **P1**
- `finding_type: coverage_gap` → `bucket: code_fix`
- **검출**: 키트 테이블명을 마이그레이션 SQL 전수에서 `CREATE TABLE` grep → 매칭 0건. (스키마 prefix·따옴표·대소문자 변형 모두 시도해 반증부터 — 명명만 다른 경우 배제)
- **gap 예시**: "ERD-010 테이블 `dataset_artifact_upload_session` — V1~V18 마이그레이션 어디에도 CREATE TABLE 없음 (미구현)"

#### SCH-CONF-002: 컬럼 누락
- 키트 테이블의 컬럼이 마이그레이션(CREATE/ALTER) 및 엔티티에 **없음** → **P1** (해당 컬럼이 **PK/FK 면 P0** — 무결성·관계 단절)
- `finding_type: code_drift` → `bucket: code_fix`
- **검출**: 키트 컬럼 목록 ↔ 마이그레이션 합산 컬럼(CREATE + 후속 ALTER ADD COLUMN) ↔ 엔티티 `@Column`. 3측 모두 부재여야 단정.
- **gap 예시**: "ERD-010 `external_training_dataset.parent_version_id`(FK→self) — V12 CREATE 및 엔티티에 없음 (계보 FK 누락, PK/FK ∴ P0)"

#### SCH-CONF-003: 타입 불일치
- 컬럼 타입이 키트 정의와 다름 (varchar 길이·`uuid` vs `bigint`·`timestamptz` vs `timestamp`·numeric precision 등) → **P1**
- `finding_type: code_drift` → `bucket: code_fix`
- **검출**: 키트 컬럼 타입 ↔ 마이그레이션 SQL 컬럼 타입(진실원). 엔티티와 SQL 이 다르면 SQL 채택 + 엔티티 표류 병기.
- **gap 예시**: "ERD-010 `dataset_id` 키트=`uuid` ↔ V11 SQL `bigint` — 식별자 타입 불일치 (런타임=bigint)"

#### SCH-CONF-004: 제약 누락
- 키트가 명시한 **CHECK / UNIQUE / FK / NOT NULL** 제약이 마이그레이션에 없음 → **P0** (데이터 무결성 직결)
- `finding_type: code_drift` → `bucket: code_fix`
- **검출**: 키트 제약 명세 ↔ 마이그레이션 SQL 에서 `CONSTRAINT` / `CHECK` / `UNIQUE` / `REFERENCES` / `NOT NULL` grep. 인라인(컬럼 정의 내)·테이블레벨·후속 `ALTER TABLE ADD CONSTRAINT` 모두 합산해 확인 (한 형태만 보고 누락 단정 금지).
- **gap 예시**: "ERD-010 `deploy_type` CHECK IN ('internal','datamart','ai_model') — V11 CREATE 에 CHECK 제약 없음 (불법 값 허용, 무결성 ∴ P0)"

#### SCH-CONF-005: 인덱스 누락
- 키트가 명시한 인덱스(특히 **부분 UNIQUE 인덱스** — 동시성·중복 방지 핵심)가 마이그레이션에 부재 → **P1**
- `finding_type: code_drift` → `bucket: code_fix`
- **검출**: 키트 인덱스 명세 ↔ 마이그레이션 `CREATE [UNIQUE] INDEX` grep. 부분 인덱스면 `WHERE` 절 조건까지 일치 확인 (full UNIQUE 로 대체돼 있으면 의미 다름 — 별도 표류).
- **gap 예시**: "ERD-010 부분 UNIQUE `uq_active_session (dataset_id) WHERE status='active'` — V17 에 부재 (동시 업로드 세션 중복 차단 인덱스 누락)"

### 역방향 — extra (SCH-CONF-006)

#### SCH-CONF-006: 키트에 없는 테이블/컬럼
- 마이그레이션·엔티티에 존재하나 키트 ERD 에 **없는** 테이블/컬럼 → **P1**
- `finding_type: extra_code` → `bucket: design_update`
- **검출**: 마이그레이션 CREATE/ALTER 객체 ↔ 키트 ERD 전수 대조 → 키트 미추적 객체.
- ⚠️ **오탐 방지 (의도된 상태는 gap 아님)**: 키트 `_domain.md`/`IMPLEMENTATION.md` **보존 정책**으로 식별되는 **1차 보존 테이블·기존 스키마**는 정상 → **제외**. 키트가 의도적으로 ERD 에 안 그린 보존 영역이므로 finding 으로 보고 금지. (checklist.md §5 "의도된 상태는 gap 아님")
- 명명만 다른 키트 객체와의 매칭 가능성을 먼저 배제 — 배제 못 하면 `needs_human: true` + **P2 강등**.
- **gap 예시**: "마이그레이션 V14 `ai_model_eval_log` 테이블 — 키트 ERD 에 없음. 보존 정책 비대상 ∴ 설계 미반영(extra_code) — ERD 신규 등록 또는 의도 확인 필요"

## confidence · 반증 우선 (checklist.md 인용)

- **confidence 판정** (checklist.md §4): 코드 측 매핑은 휴리스틱 → 3중 추적(① IMPLEMENTATION.md 의존맵 ② IMPREC 커밋/심볼 ③ 계약 문자열 grep — 여기선 **테이블명/컬럼명/제약명 grep** 이 ③) 중 **2개 이상 일치해야 `high`**. SQL grep 으로 직접 확인 1개만이면 `medium`. 키트만 보고 코드 미확인이면 `low`.
- **반증 우선** (checklist.md §5): SCH-CONF-001/002/003 으로 단정 전 "**다르게 명명·다른 마이그레이션 파일·엔티티 매핑 차이로 존재할 가능성**"을 먼저 배제. 배제 못 하면 `needs_human: true` + severity **P2 강등** — 단정 보고 금지. ("명명만 다른데 missing 으로 오판" 이 최대 위험)
- **evidence 의무** (checklist.md §3): 모든 finding 은 `kit_item`(ERD ITEM ID) + `code_ref`(`db/migration/V11__*.sql:line` 또는 코드 부재 시 `"<부재>"`) 필수. 추적 실패 finding 보고 금지.
- **`low` 강등** (checklist.md §4): SQL·심볼로 직접 확인 못 한 finding 은 P2 + `needs_human: true`.

## Gap 분류 코드 (요약)
- `SCH-CONF-001`: 테이블 미생성 (coverage_gap / code_fix / P1)
- `SCH-CONF-002`: 컬럼 누락 (code_drift / code_fix / P1, PK·FK 면 P0)
- `SCH-CONF-003`: 타입 불일치 (code_drift / code_fix / P1)
- `SCH-CONF-004`: 제약 누락 (code_drift / code_fix / P0)
- `SCH-CONF-005`: 인덱스 누락 (code_drift / code_fix / P1)
- `SCH-CONF-006`: 키트에 없는 테이블/컬럼 (extra_code / design_update / P1; 1차 보존 스키마 제외)

(YAML 출력의 `dimension:` 값은 `schema`, gap id prefix 는 `SCH-CONF`)

## Evidence 인용 룰
- 마이그레이션 인용: `db/migration/V11__create_external_training_dataset.sql:42 "deploy_type varchar(20) not null"` (SQL 줄 직접 quote)
- 키트 제약 인용: `ERD-010 deploy_type CHECK IN ('internal','datamart','ai_model')`
- 타입 불일치: `ERD-010 dataset_id = uuid ↔ V11 SQL "dataset_id bigint" (런타임=bigint)` (양측 동시 quote)
- 코드 부재: `code_ref: "<부재>"` 명시 (빈 문자열 금지)

## cross-dimension hint
- SCH-CONF-004/005(제약·인덱스 누락) ↔ policy 차원 `POL-CONF-003/004`(버전 계보·보존 위반)와 연동될 수 있음 → `notes_for_main.cross_dimension_hint` 에 `SCH-CONF-004 ↔ POL-CONF-004`
- SCH-CONF-006(extra 테이블) ↔ coverage 차원 `COV-002`(키트 외 코드)와 동일 객체일 수 있음 → 중복 보고 대신 hint 로 연계
