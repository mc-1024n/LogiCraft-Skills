# core-item-set.md — 구현 핵심 세트 + 빌드 순서

logicraft ITEM 타입(**서버 진실원 = `packages/schemas` `ITEM_TYPES`, 2026-08 기준 57종 — 계속 늘어남**) 중
**코드로 구현되는** 타입만 결정 규칙으로 다운로드한다. Tier 규칙은 결정적(deterministic) — 매 실행 동일.

> ★ **신규 타입 기본 정책 (fail-open)**: 이 문서의 Tier 표에 **없는 미지의 타입**을 서버가 반환하면
> "제외"가 아니라 **"포함"이 기본**이다 — 다운로더를 `--types`(포함 목록) 대신
> **`--exclude-types`(아래 제외 목록 CSV)** 로 호출하면 서버에 타입이 새로 추가되어도 키트에 자동 포함된다.
> 설계에 존재하는데 키트에 안 내려와 구현이 설계를 못 보는 사고(2026-08 신규 6종 누락 사례)를 막는 구조.
> 미지의 타입을 발견하면 보고에 "⚠️ Tier 미분류 신규 타입 N종 포함됨 — core-item-set.md 갱신 권장" 을 남긴다.

## Tier 1 — 항상 다운로드 (구현 본체)

| type code | 약칭 | 구현상 의미 |
|---|---|---|
| `domain` | DOMAIN | bounded context 본체 (`_domain.md`) — 1건 |
| `domain_feature` | DFEAT | 도메인 기능 = 비즈니스 로직 단위. **구현의 진실원 — 0건이면 SKILL Phase 2 DFEAT 부재 게이트로 사용자 노티 필수** |
| `api_endpoint` | API | 엔드포인트 계약 (method/path/req/res/auth/error) |
| `erd` | ERD | 데이터 모델 (논리+물리 둘 다 — 물리는 DDL 직결) |
| `diagram_sequence` | SEQ | 호출 흐름 = 코드 시퀀스 |
| `screen_spec` | SCREEN | 화면 (sections/components/consumes_apis/roles) |
| `use_case` | UC | 동작 시나리오 = 통합 테스트 근거 |
| `domain_event` | EVT | 이벤트 계약 (payload/emitter/consumer) |
| `acceptance` | AC | 수용 기준 = 테스트 케이스 근거 |
| `permission_role` | ROLE | 역할-권한 매트릭스 = authz 코드 |
| `service_interface` | SVC | **비-HTTP 서비스 계약**(MCP 도구·CLI·데몬 등) — api_endpoint 와 동급 경계 계약. core capability(프로파일 무관 항상 노출, ADR-016) |
| `module_api` | IAPI | **in-process 앱 모듈 공개 API** — local-first(모바일/데스크톱) 앱의 4번째 경계 타입. DFEAT 가 implements 로 실현, persists_in 으로 ERD 연결 |
| `library_api` | LIB | **라이브러리 공개 API** 계약(함수/클래스 시그니처) — 라이브러리성 코드의 경계. core capability(ADR-017) |
| `data_pipeline` | DP | **배치/파이프라인** — reads_from/writes_to(ERD·EXTSYS)·emits(EVT)·implemented_by(MOD). 도메인에 없으면 0건으로 무해 |
| `constant` | CONST | 코드/설정에 박을 실제 상수값. 설계 ITEM(API/SCREEN/ERD/DFEAT)이 `uses_constant` 로 참조 → 역참조를 따라 "이 API/화면 구현 시 박을 enum/range/default/임계치"를 코드에 정확히 반영. enum/range 는 인라인 중복 말고 CONST 단일 진실원 사용 |

## Tier 2 — 항상 다운로드 (구속 제약·기존 구현 컨텍스트)

| type code | 약칭 | 구현상 의미 |
|---|---|---|
| `adr` | ADR | 코드가 **반드시** 지켜야 할 결정·제약 (도메인 참조분만) |
| `nfr` | NFR | 성능/보안/가용성 예산 = 비기능 구속 |
| `implementation_guideline` | GUIDE | 프로젝트 공통 코딩 규칙 (applies_to 매칭분) |
| `feature` | FEAT | DFEAT 의 상위 FEAT (specializes_feature 대상만 — 컨텍스트) |

### ADR 필터 규칙 (전역 ADR 중 도메인 관련만)
1. `get_related(DOMAIN-XXX, depth=2)` 결과에 등장한 ADR
2. 도메인 소속 ITEM 의 `brownfield.decided_by` 에 등장한 ADR
3. 도메인 `change_summary` / description 본문에 `ADR-\d+` 로 인용된 ADR
→ 위 합집합만 다운로드. 무관 ADR 제외.

### GUIDE 매칭 규칙
- `applies_to_types` 비어있음 → project-wide → 항상 포함
- `applies_to_types` 채워짐 → 다운로드 대상 타입과 교집합 있으면 포함

## Tier 3 — 조건부 (링크 존재 & 관련 시에만)

| type code | 포함 조건 |
|---|---|
| `class_diagram` | 도메인에 링크된 class_diagram 존재 시 (코드 구조 직결) |
| `diagram_state` | 도메인에 상태머신 존재 시 |
| `integration_point` / `external_system` / `integration_spec` | 도메인이 `uses_integrations` 보유 시 (외부 연동 구현 필요) |
| `ai_policy` / `model_usage` / `guardrail` / `prompt_template` / `ai_eval` / `ai_dataset` | 도메인이 AI 도메인일 때 (예: D007 생성형 AI). 도메인 description 에 LLM/VLM/생성형/prompt 키워드 또는 위 타입 링크 존재 |
| `ui_component` / `design_system` | SCREEN 이 3건 이상이고 design_system/ui_component 링크 존재 시 |
| `diagram_c4_container` / `diagram_c4_component` | 도메인 전용 C4 컨테이너/컴포넌트 다이어그램 링크 존재 시 |
| `migration_plan` | 도메인 ERD 가 brownfield migration 대상일 때 (brownfield_migration 링크) |
| `permission_manifest` / `settings_schema` | **프로젝트 프로파일이 desktop**(capability `desktop_ui`)일 때 (ADR-021 — OS 권한 매니페스트·환경설정 스키마). 프로파일은 프로젝트 profile/capabilities 로 판정(`packages/schemas` profiles.ts 매핑이 진실원) — 웹 전용 프로젝트면 자동 0건 |

### 제외 (구현 무관 — 다운로드 안 함)
`code_module`(★ **이미 구현된** 코드 모듈의 역참조 매핑(file_path→설계) — **구현의 입력 스펙이 아니라 구현 결과의 사후 추적 문서**다. 무엇을 구현할지는 DFEAT/API/ERD 로 충분하고, 코드↔설계 접합은 소스의 `@DesignRef` 코드주석이 담당하므로 키트에 불필요. 매 SYNC 마다 대량 신규로 떠서 노이즈만 됨),
`rfp_item`, `requirement`(상위 추상 — FEAT 로 충분), `glossary`(도메인 ubiquitous_language 로 흡수),
`risk`, `slo`, `runbook`, `incident`, `postmortem`, `monitor_alert`, `navigation_tree`,
`app_shell`, `diagram_c4_context`, `diagram_deployment`, `implementation_record`.

> 단, 사용자가 "전부 받아줘" 명시 시 Tier 제한 해제하고 도메인 연결 전체 다운로드.

## 빌드 순서 (IMPLEMENTATION.md 에 기재 — 바이브코딩 진행 순서)

제약을 먼저 읽고, 데이터→계약→로직→UI→검증 순으로 쌓는다.

```
0. 제약 흡수      ADR + NFR + CONST + GUIDE
                  → 코드 전반에 적용될 불변 규칙·예산·금지사항 먼저 내재화
                  → 각 설계 ITEM(API/SCREEN/ERD/DFEAT)의 uses_constant 를 따라가
                    "이 단계에서 코드에 박을 실제 상수값"을 CONST 에서 확인 (인라인 추정 금지)
1. 데이터 계층     ERD(물리)  → 마이그레이션/스키마/엔티티
2. 이벤트 계약     EVT        → 이벤트 페이로드 타입/발행·구독 인터페이스
3. 경계 계약       API + SVC + IAPI + LIB
                  → REST 는 컨트롤러 시그니처/DTO/에러 응답 (API)
                  → 비-HTTP 서비스(MCP 도구·CLI)는 SVC 계약의 request/response_schema
                  → in-process 모듈 공개 API 는 IAPI 시그니처 (owner_module·language 명시)
                  → 라이브러리 공개 API 는 LIB 시그니처
                  ※ 프로젝트 성격에 따라 넷 중 존재하는 것만 — 전부 "외부에서 호출되는 계약" 동급
4. 비즈니스 로직   DFEAT      → 서비스 계층 (경계 계약·EVT·테이블 오케스트레이션)
                  + DP        → 배치/파이프라인 구현 (reads/writes 테이블·외부시스템, 존재 시)
5. 흐름 배선       SEQ        → DFEAT 내부 호출 순서·외부 연동 와이어링
6. 인가 계층       ROLE       → 엔드포인트/리소스 권한 가드
7. 화면           SCREEN     → 컴포넌트 + consumes_apis 바인딩
8. 검증           UC + AC    → 통합 테스트·수용 테스트
조건부: INT/EXTSYS(외부 연동 어댑터), class_diagram(클래스 구조), AI 거버넌스,
        PMAN/SETT(desktop 프로파일 — OS 권한 매니페스트·설정 스키마는 화면(7) 전에 셸/부트스트랩 단계에서)
참고: 구현 현황표(어디부터 — get_implementation_coverage / list_unimplemented)
      · code_module(MOD)은 키트에 다운로드하지 않는다(구현 결과 추적 문서 — 위 제외 규칙).
        기구현 재사용 범위 판단은 구현 현황표와 소스의 @DesignRef 태그로 확인
```

## 의존 그래프 (IMPLEMENTATION.md 에 기재)

`get_related(DOMAIN-XXX, depth=2, both)` 결과에서 다음 링크를 추출해 표/머메이드로:
- DFEAT `--implemented_by_endpoints-->` API
- DFEAT `--implements-->` SVC / IAPI (비-HTTP·in-process 경계 계약의 실현 — 존재 시)
- SVC/IAPI/LIB `--implements-->` FEAT, `--verifies-->` AC, `--uses_constant-->` CONST (경계 계약 공통)
- IAPI `--persists_in-->` ERD, SVC/IAPI `--triggers-->` EVT
- DP `--reads_from/writes_to-->` ERD·EXTSYS, DP `--emits-->` EVT (파이프라인 존재 시)
- DFEAT `--triggers-->` EVT, DFEAT `--consumes-->` EVT
- DFEAT `--persists_in_tables-->` ERD(물리 테이블)
- API `--realized_by-->` SEQ
- SCREEN `--consumes_apis-->` API, SCREEN `--required_roles-->` ROLE
- UC `--verified_by-->` AC, FEAT `--specialized_by-->` DFEAT
- API/SCREEN/ERD/DFEAT `--uses_constant-->` CONST (설계가 쓰는 상수 — 코드에 박을 실제 enum/range/default/임계치)
  · 커버리지 방어: uses_constant 미연결 CONST 도 도메인 소속(belongs_to_domain)으로 키트에 이미 포함됨

이 그래프가 "무엇부터, 무엇과 함께 구현해야 하는지"의 핵심 — 바이브코딩 에이전트가 컨텍스트로 사용.
