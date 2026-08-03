# Policy Conformance Dimension

코드 패턴(구조·패턴) ↔ ADR 결정 준수 정합 검토. **코드 측 = 구조·패턴**(트리거 모델·컨트롤러 경계·버전 계보·참조 모델 등). **키트 측 = ADR 결정 + `IMPLEMENTATION.md` "구현 함정" 단락**(메인이 `adr_policies` 로 주입).

> **정책은 키트가 진실원** — 본 차원의 룰은 "**주입된 정책 X 를 코드에서 검증**" 하는 *절차*를 기술하고, 구체 정책 값(어떤 트리거 모델인지·어떤 컨트롤러 경계인지 등)은 **하드코딩하지 않는다**(도메인마다 다름). 정책 값은 STEP 0 에서 메인이 주입한 `adr_policies` + 키트 함정 목록으로부터 받는다. 따라서 아래 룰은 **메타룰** — 정책의 *형태*(비동기 트리거·컨트롤러 경계·버전 계보·참조/보존·일반 ADR)별로 코드 검증 절차를 정의한다.

## 핵심 관계

| 측 | 무엇 | 어디서 |
|---|---|---|
| 키트(설계 진실원) | ADR 결정(ADR ID → 한 줄) + `IMPLEMENTATION.md` "구현 함정" 단락 | 메인 주입 `adr_policies` + 키트 `IMPLEMENTATION.md` |
| 코드(실제) | 구조·패턴(애너테이션·클래스 인벤토리·컬럼 분기·업데이트 방식 등) | `code_root` Grep/serena 심볼 |
| IMPREC(주장) | (본 차원은 직접 대조 안 함 — coverage 차원이 담당) | — |

## STEP 0 — 입력 보강 (auditor 가 1회 수행)

1. **메인이 주입한 `adr_policies` 사용** — `{ ADR-ID: "결정 한 줄" }` 형태. 이게 점검 대상 정책의 1차 원천이다. AI 가 ADR 본문을 임의 해석해 정책을 *추가 발명하지 말 것* — 주입된 결정만 검증한다.
2. **키트 명시 함정 목록을 점검 대상 정책으로 변환** — `IMPLEMENTATION.md` 의 "구현 함정"(또는 "§주의"·"운영 전 확인") 단락에서 "코드가 위반하기 쉬운 패턴"을 추출해 정책 항목으로 추가한다. 예: "in-place update 금지·v+1 계보 필수", "deploy_type 분기로 datasets 보존(수정 금지)", "PortalDispatcher 는 Stub" 등.
3. 각 정책 항목을 아래 5종 룰의 **형태**(트리거·경계·계보·참조보존·일반) 중 하나로 분류해, 해당 룰의 검출 절차를 적용한다. 어느 형태에도 안 맞으면 POL-CONF-005(일반 ADR 결정)로 검증한다.
4. **정책 원천이 비어 있으면**(`adr_policies` 미주입 + 키트 함정 단락 부재): 정책 검증 불가 → `notes_for_main.unable_to_verify` 에 "정책 원천 부재 — adr_policies/IMPLEMENTATION.md 함정 단락 없음" 명시하고 finding 0건. **억지 finding 생성 금지.**

## 검토 룰

> 각 룰: 조건 → severity → `finding_type` → `bucket` → 검출 절차. `finding_type`·`bucket` 은 checklist.md §1 enum 고정값. `confidence` 등급·반증 우선·evidence(kit_item+code_ref) 규약은 **checklist.md §3~§5 인용** — 본 파일에서 재정의하지 않는다.

### POL-CONF-001 — 비동기 트리거 모델 위반
- **조건**: 주입 정책이 **특정 비동기 트리거 모델**을 정했는데(예: cron 폴링) 코드에 **반대 모델**의 잔재가 있음 — cron 폴링 결정인데 `LISTEN`/`NOTIFY`·이벤트 리스너 잔재(또는 반대로 이벤트 결정인데 `@Scheduled`/Quartz cron 잔재).
- **severity**: P0
- **finding_type**: `code_drift` → **bucket**: `code_fix`
- **검출**: 정책이 명시한 트리거 모델을 확정 → 반대 모델 키워드 grep:
  - cron/폴링 측: `@Scheduled`, Quartz `JobDetail`/`CronTrigger`/`@DisallowConcurrentExecution`, `cron(`
  - LISTEN/NOTIFY·이벤트 측: `LISTEN`, `NOTIFY`, `@EventListener`, `@TransactionalEventListener`, 메시지 리스너 애너테이션
  - 정책 모델과 **다른** 측 키워드가 활성 코드에 잡히면 위반 후보. (주석·비활성·테스트 픽스처는 반증으로 배제 — checklist.md §5)

### POL-CONF-002 — 컨트롤러 경계 위반
- **조건**: 주입 정책이 **컨트롤러 경계**를 정했는데(예: 단일 컨트롤러로 통합·BFF/aggregation 컨트롤러 금지) 코드가 **다중 컨트롤러** 또는 **BFF/aggregation 패턴**으로 구현됨(또는 반대로 분리 정책인데 단일 거대 컨트롤러).
- **severity**: P0
- **finding_type**: `code_drift` → **bucket**: `code_fix`
- **검출**: 컨트롤러 인벤토리 구성 후 정책과 대조:
  - serena `get_symbols_overview` 또는 Grep `@RestController`/`@Controller`/`@RequestMapping` 으로 컨트롤러 클래스 전수 수집.
  - BFF/aggregation 금지 정책이면 `*Bff*`/`*Aggregat*`/`*Facade*` 명명·여러 도메인 서비스를 합치는 핸들러 패턴 탐지.
  - 단일 경계 정책이면 동일 책임을 가진 컨트롤러가 2개 이상으로 쪼개졌는지 대조.

### POL-CONF-003 — 버전 계보 위반
- **조건**: 주입 정책이 **불변 버전 계보**(예: 신규 행 v+1 + `parent_version_id` 로 계보 연결)를 정했는데 코드가 **in-place update**(기존 행 수정) 또는 **계보 미기록**(parent 링크 누락)으로 구현됨.
- **severity**: P0
- **finding_type**: `code_drift` → **bucket**: `code_fix`
- **검출**:
  - 계보 컬럼(예 `parent_version_id`/`version`/`lineage`) 의 엔티티·마이그레이션 존재 확인.
  - 등록/갱신 서비스에서 `save(new ...)`(신규 행) vs `findById(...).setXxx(...)`(in-place) 패턴 대조 — 정책이 v+1 인데 in-place update 면 위반.
  - 신규 행 생성 시 `parentVersionId` 세팅 누락(계보 미기록)이면 위반. (Registrar/Builder 류 클래스의 계보 세팅 라인 grep)

### POL-CONF-004 — polymorphic 참조 / 보존 위반
- **조건**: 신규 모델이 **기존 보존 테이블/모델을 변형**함 — 정책상 분기(예: `deploy_type` 같은 polymorphic 구분 컬럼으로 분기)해야 하는데 보존 테이블(예 `datasets`)을 직접 수정/확장.
- **severity**: P0
- **finding_type**: `code_drift` → **bucket**: `code_fix`
- **검출**:
  - 키트 보존 정책(`_domain.md`/`IMPLEMENTATION.md` "보존 영역")에서 보존 대상 테이블/모델 식별.
  - 보존 테이블에 신규 컬럼 추가·구조 변경하는 마이그레이션(`ALTER TABLE <보존테이블>`)이 있는지 grep.
  - 정책이 요구한 분기 메커니즘(구분 컬럼·별도 테이블·다형 참조)이 실제 코드에 있는지 확인 — 분기 대신 보존 테이블 변형이면 위반.

### POL-CONF-005 — 일반 ADR 결정 미준수
- **조건**: 주입된 **임의 ADR 결정**(위 4종 형태에 안 맞는 일반 정책)이 코드 패턴으로 **확인되지 않음**. (예: "outbound HTTPS 필수", "특정 헤더 통일", "특정 코드값 사용", "특정 envelope 형식" 등 도메인별 임의 결정.)
- **severity**:
  - **명확 위반**(정책이 코드에서 반대로 구현됨이 grep 으로 확정) → **P1**
  - **불확실**(코드 측을 grep/심볼로 직접 확인 못 함 — 키트 측만 보고 추정) → **P2 + `needs_human: true`** (checklist.md §5 반증 우선·강등 규약)
- **finding_type**: `code_drift` → **bucket**: `code_fix`
- **검출**: 정책별로 검증 가능한 키워드/구조를 도출해 grep:
  - 통신 방향·프로토콜 정책 → `http://`/`https://` 리터럴·클라이언트 설정 grep
  - 헤더·토큰 정책 → 헤더 상수명·`Authorization`/`x-access-token` 등 grep
  - 코드값·상수 정책 → 해당 상수/리터럴 grep (정정 전 잔재값 탐지)
  - envelope·응답 형식 정책 → 공통 래퍼 클래스 적용 여부 grep
  - **정책을 코드로 환원할 grep 단서를 못 만들면** → finding 으로 단정하지 말고 `notes_for_main.unable_to_verify` 에 "정책 X 는 코드 패턴으로 검증 불가(구조 미특정)" 로 보고.

## 거짓양성 방어 (checklist.md §5 인용)

1. **단정 전 반증 먼저** — `code_drift` 단정 전 "**다르게 구현됐을 가능성**"(다른 클래스·다른 계층·다른 명명으로 정책을 *충족*하고 있을 가능성)을 먼저 배제한다. 예: cron 잔재처럼 보이는 `@Scheduled` 가 실제로는 정책이 허용한 **별개 워커**(만료 워커 등)일 수 있음 — 정책이 금지한 트리거 경로인지 확인 후 단정.
2. **불확실 시 강등** — 배제 못 하면 `needs_human: true` + severity **P2 강등**. 단정 보고 금지.
3. **의도된 상태는 위반 아님** — 키트가 명시적으로 Stub/TODO/단계적 미구현으로 둔 정책 항목(예: PortalDispatcher Stub, AccessGuard TODO)은 정책 *위반*이 아니라 *coverage/role 차원의 부분구현* 사안이다. 본 차원에서 위반으로 보고하지 말고 `notes_for_main.cross_dimension_hint` 로 넘긴다.

## confidence 판정 (checklist.md §4 인용)

코드 측 매핑은 휴리스틱이므로 3중 추적(① IMPLEMENTATION.md 의존맵 ② IMPREC 커밋/심볼 ③ 계약·정책 문자열 grep)으로 교차 검증한다. 본 차원은 주로 **③ 정책 키워드 grep** 으로 검출하므로:
- `high` — 정책 키워드 grep 위반 라인 확정 **+** IMPLEMENTATION.md 함정 단락이 동일 패턴을 함정으로 명시(2개 일치).
- `medium` — 정책 키워드 grep 으로만 1경로 확인.
- `low` — 코드를 직접 grep 하지 못하고 키트 정책만 보고 추정 → **P2 강등 + `needs_human: true`** 권장.

## evidence 인용 룰 (checklist.md §3 인용)

- **정책(키트) 인용**: `adr_policies` 의 `ADR-ID: "결정 한 줄"` 또는 `IMPLEMENTATION.md` "구현 함정" 해당 줄 quote. `kit_item` = ADR ITEM ID(예 `ADR-081`).
- **코드 인용**: `relative/path.java:line` + 위반 핵심 줄 quote(예 `@Scheduled(cron = ...)`, `ALTER TABLE datasets ...`). `code_ref` 필수.
- **정책은 있으나 코드 위치를 못 잡은 경우**: 단정 finding 금지(추적 실패 = 무근거, checklist.md §3) → `notes_for_main.unable_to_verify` 로 강등 보고.

## Cross-dimension hint

- 컨트롤러 경계 위반(POL-CONF-002) ↔ api 차원 extra/누락 엔드포인트와 겹칠 수 있음 → `cross_dimension_hint`.
- 보존 테이블 변형(POL-CONF-004) ↔ schema 차원 SCH-CONF-006(키트에 없는 테이블/컬럼)과 겹침 → `cross_dimension_hint`.
- 정책상 Stub/TODO 항목 ↔ coverage(COV-005 부분구현)·role(ROLE-CONF-003 가드 스텁) 차원으로 핸드오프 → `cross_dimension_hint`.

## 출력

checklist.md §6 출력 YAML 스키마 한 블록만 반환한다(자유 텍스트 금지). `id` 형식 `POL-CONF-NNN`, 순번 1부터. `finding_type` → `bucket` 매핑은 checklist.md §1 표대로(본 차원 5종 모두 `code_drift` → `code_fix`).
