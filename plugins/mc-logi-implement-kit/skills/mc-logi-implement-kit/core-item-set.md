# core-item-set.md — 구현 핵심 세트 (고정) + 빌드 순서

logicraft 35 타입 중 **코드로 구현되는** 타입만 결정 규칙으로 다운로드한다.
사용자 결정: "구현 핵심 세트 고정". Tier 규칙은 결정적(deterministic) — 매 실행 동일.

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
| `constant` | CONST | 코드/설정에 박을 실제 상수값. 설계 ITEM(API/SCREEN/ERD/DFEAT)이 `uses_constant` 로 참조 → 역참조를 따라 "이 API/화면 구현 시 박을 enum/range/default/임계치"를 코드에 정확히 반영. enum/range 는 인라인 중복 말고 CONST 단일 진실원 사용 |

## Tier 2 — 항상 다운로드 (구속 제약·기존 구현 컨텍스트)

| type code | 약칭 | 구현상 의미 |
|---|---|---|
| `adr` | ADR | 코드가 **반드시** 지켜야 할 결정·제약 (도메인 참조분만) |
| `nfr` | NFR | 성능/보안/가용성 예산 = 비기능 구속 |
| `implementation_guideline` | GUIDE | 프로젝트 공통 코딩 규칙 (applies_to 매칭분) |
| `code_module` | MOD | **이미 구현된** 코드 모듈 (재구현 방지 — realizes 링크) |
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

### 제외 (구현 무관 — 다운로드 안 함)
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
3. API 계약       API        → 컨트롤러 시그니처/DTO/에러 응답
4. 비즈니스 로직   DFEAT      → 서비스 계층 (API·EVT·테이블 오케스트레이션)
5. 흐름 배선       SEQ        → DFEAT 내부 호출 순서·외부 연동 와이어링
6. 인가 계층       ROLE       → 엔드포인트/리소스 권한 가드
7. 화면           SCREEN     → 컴포넌트 + consumes_apis 바인딩
8. 검증           UC + AC    → 통합 테스트·수용 테스트
조건부: INT/EXTSYS(외부 연동 어댑터), class_diagram(클래스 구조), AI 거버넌스
참고: MOD(이미 구현된 모듈 — 건드리지 말고 재사용), 구현 현황표(어디부터)
```

## 의존 그래프 (IMPLEMENTATION.md 에 기재)

`get_related(DOMAIN-XXX, depth=2, both)` 결과에서 다음 링크를 추출해 표/머메이드로:
- DFEAT `--implemented_by_endpoints-->` API
- DFEAT `--triggers-->` EVT, DFEAT `--consumes-->` EVT
- DFEAT `--persists_in_tables-->` ERD(물리 테이블)
- API `--realized_by-->` SEQ
- SCREEN `--consumes_apis-->` API, SCREEN `--required_roles-->` ROLE
- UC `--verified_by-->` AC, FEAT `--specialized_by-->` DFEAT
- API/SCREEN/ERD/DFEAT `--uses_constant-->` CONST (설계가 쓰는 상수 — 코드에 박을 실제 enum/range/default/임계치)
  · 커버리지 방어: uses_constant 미연결 CONST 도 도메인 소속(belongs_to_domain)으로 키트에 이미 포함됨

이 그래프가 "무엇부터, 무엇과 함께 구현해야 하는지"의 핵심 — 바이브코딩 에이전트가 컨텍스트로 사용.