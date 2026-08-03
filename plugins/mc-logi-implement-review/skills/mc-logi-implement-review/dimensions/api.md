# API Conformance Dimension

**경계 계약 4종**(`api_endpoint`(REST) · `service_interface`(비-HTTP 서비스: MCP 도구·CLI) · `module_api`(in-process 모듈 API) · `library_api`(라이브러리 공개 API))이 실제 코드와 정합하는지 검토. 키트가 진실원 — 코드가 키트 계약을 위반하면 `code_drift`, 키트 ITEM 에 대응 구현이 없으면 `coverage_gap`, 키트에 없는 구현은 `extra_code`. REST(`api_endpoint`)가 주 대상이고, 키트에 SVC/IAPI/LIB 이 존재하면 아래 §비-HTTP 경계 계약 룰(API-CONF-007~009)도 함께 수행한다.

REST 대상: 컨트롤러가 키트 `api_endpoint` 와 **path·method·request·response·envelope·상태코드** 차원에서 정합하는지.

코드 측 = 컨트롤러 (`@RestController` / `@RequestMapping` / `@GetMapping` / `@PostMapping` / `@PutMapping` / `@DeleteMapping` / `@PatchMapping` + 요청 DTO + 예외 advice).
키트 측 = `api_endpoint` ITEM 의 `path` / `method` / `request_schema` / `response_schema` / `envelope`(ADR-072 공통 응답) / `error`(상태코드 표).

핵심 관계:
- `api_endpoint.path + .method` ↔ 컨트롤러 매핑 애너테이션 값
- `api_endpoint.request_schema` ↔ 요청 DTO 필드·필수여부(`@NotNull`/`required`)
- `api_endpoint.response_schema + envelope(ADR-072)` ↔ 응답 본문 형식
- `api_endpoint.error` 상태코드(409/410/413/422 등) ↔ 예외 advice(`@ExceptionHandler` / `@ControllerAdvice` / `ResponseStatus`)

## 입력 보강 (STEP 0 — 검사의 전제)

키트 측 적재:
- 키트 `api_endpoint/*.md` + `_raw/*.json` 에서 각 ITEM 의 `path` · `method` · `request_schema`(필드·필수여부) · `response_schema` · `envelope` 정책(ADR-072 공통 envelope) · `error`(상태코드 표) 를 전수 적재.
- ADR-072 envelope 형식(공통 응답 wrapper 구조)을 별도 적재 — 모든 응답 검증의 기준선.

코드 측 인벤토리:
- serena `find_symbol`(컨트롤러 클래스, `depth=1`)로 핸들러 메서드 목록 + 매핑 애너테이션 수집.
- Grep `@(Get|Post|Put|Delete|Patch|Request)Mapping` 으로 엔드포인트 전수 인벤토리 구성(클래스 레벨 `@RequestMapping` prefix + 메서드 레벨 path 합성).
- 요청 DTO 는 핸들러 시그니처(`@RequestBody`/`@RequestParam`)에서 역추적, 예외 advice 는 `@ControllerAdvice`/`@ExceptionHandler` Grep 으로 상태코드 매핑 수집.

⚠️ 키트 `api_endpoint` 후보가 0건이고 코드 컨트롤러도 0건이면 **전 룰 skip** + `notes_for_main.unable_to_verify` 에 "도메인 API 계약·컨트롤러 부재 — 검증 불가" 명시.

> confidence 등급(3중 추적 2+ 일치 = high)·반증 우선(단정 전 "다르게 구현됐을 가능성" 배제)·evidence 규약(kit_item + code_ref 필수)·read-only 보장은 모두 `checklist.md` 를 따른다 — 여기서 재서술하지 않는다.

## 검토 룰

### 커버리지 (API-CONF-001)

#### API-CONF-001: 엔드포인트 미구현
- 키트 `api_endpoint` 의 `path` + `method` 조합에 대응하는 컨트롤러 핸들러가 없음 → **P1**
- **finding_type**: `coverage_gap` / **bucket**: `code_fix`
- **검출**: 키트 path 문자열 grep + 매핑 애너테이션 인벤토리 대조 → 핸들러 매핑 부재 확인. 반증(다른 컨트롤러·다른 path 표기로 구현됐을 가능성) 배제 후 단정.

**gap 예시**: "API-332 POST /datasets/{id}/artifacts (TUS 생성) — 대응 핸들러 없음 (path grep·매핑 인벤토리 모두 부재)"

### 표류 — code_drift (API-CONF-002 ~ API-CONF-005)

#### API-CONF-002: 경로/메서드 불일치
- 핸들러는 존재하나 매핑된 `path` 또는 HTTP `method` 가 키트와 다름 → **P0**
- **finding_type**: `code_drift` / **bucket**: `code_fix`
- **검출**: 매핑 애너테이션 값(클래스 prefix + 메서드 path, HTTP verb) ↔ 키트 `path`/`method` 직접 비교.

**gap 예시**: "API-335 키트 PATCH /datasets/{id}/artifacts/{aid} vs 코드 @PutMapping(\"/datasets/{id}/artifacts/{aid}\") — method PUT≠PATCH"

#### API-CONF-003: 요청 계약 표류
- 요청 DTO 의 필드 또는 필수여부(`@NotNull`/`required`)가 키트 `request_schema` 와 불일치(필드 누락·필수→선택 완화 등) → **P1**
- **finding_type**: `code_drift` / **bucket**: `code_fix`
- **검출**: 키트 `request_schema` 필드·required 표 ↔ DTO 필드·검증 애너테이션 대조.

**gap 예시**: "API-333 request_schema 필수 'model_version' vs 코드 DTO 에 model_version 필드 없음"

#### API-CONF-004: 응답/envelope 불일치
- 응답 본문이 키트 `response_schema` 와 다르거나 ADR-072 공통 envelope 형식을 따르지 않음(envelope 미적용·필드 누락) → **P0**
- **finding_type**: `code_drift` / **bucket**: `code_fix`
- **검출**: 핸들러 반환 타입·DTO 구조 ↔ 키트 `response_schema`, 그리고 ADR-072 envelope wrapper 적용 여부 대조.

**gap 예시**: "API-334 응답이 raw ModelDto 직반환 — ADR-072 공통 envelope(result/data/meta) 미적용"

#### API-CONF-005: 상태코드 불일치
- 키트가 명시한 에러 상태코드(409 충돌 / 410 만료 / 413 용량초과 / 422 검증 등)를 코드가 다르게 반환 → **P1**
- **finding_type**: `code_drift` / **bucket**: `code_fix`
- **검출**: 키트 `error` 상태코드 표 ↔ 예외 advice(`@ExceptionHandler`/`@ResponseStatus`/`ResponseEntity.status(...)`) 매핑 비교.

**gap 예시**: "API-337 키트 업로드 세션 만료=410 Gone vs 코드 @ResponseStatus(HttpStatus.NOT_FOUND) — 410≠404"

### 키트 외 코드 (API-CONF-006)

#### API-CONF-006: 키트에 없는 엔드포인트
- 컨트롤러 핸들러가 어떤 `api_endpoint` ITEM 에도 추적되지 않음 → **P1**
- **finding_type**: `extra_code` / **bucket**: `design_update`
- **검출**: 코드 엔드포인트 인벤토리 ↔ 키트 `api_endpoint` 전수 대조 → 미추적 핸들러 식별.
- ⚠️ **반증 우선**: path·method 가 미세하게 달라 "명명만 다른 같은 엔드포인트"일 가능성을 먼저 배제. 배제 못 하면 단정 금지 → `needs_human: true` + **P2 로 강등**(checklist §5).

**gap 예시**: "GET /datasets/{id}/artifacts/{aid}/download (DatasetArtifactController:142) — 대응 api_endpoint ITEM 없음 (명명 차이 배제됨)"

### 비-HTTP 경계 계약 — SVC/IAPI/LIB (API-CONF-007 ~ API-CONF-009, 키트에 해당 타입 존재 시)

> 코드 측 앵커는 프로젝트마다 다르다 — MCP 도구는 도구 등록부·입력 zod/JSON schema, in-process API 는
> `module_api.owner_module`(MOD)의 공개 시그니처, 라이브러리는 export 심볼. 키트 ITEM 의
> `signature`/`methods`/`exports` 와 소스의 `@design <ID>` 태그(있으면)를 1차 앵커로 쓰고,
> 없으면 이름·경로 grep 으로 추적한다. 검출이 불확실하면 checklist 보수 룰(단정 금지·P 강등)을 따른다.

#### API-CONF-007: 경계 계약 미구현 (coverage_gap → code_fix)
- 키트 `service_interface`/`module_api`/`library_api` ITEM 에 대응하는 코드(도구 핸들러·모듈 공개 메서드·export)가 없음 → **P1**

#### API-CONF-008: 경계 계약 표류 (code_drift → code_fix)
- SVC: 코드의 입력/출력 스키마·에러 코드(E_* 등)가 키트 `request_schema`/`response_schema`/`error_model` 과 불일치 → **P1**
- IAPI: 코드 공개 메서드 시그니처(파라미터·반환·에러)가 키트 `methods` 와 불일치 → **P1**
- LIB: 공개 심볼이 키트 `exports` 와 불일치(제거·시그니처 변경) → **P1**

#### API-CONF-009: 키트에 없는 경계 구현 (extra_code → design_update)
- 코드에 존재하는 MCP 도구/모듈 공개 API/export 가 어떤 SVC/IAPI/LIB ITEM 에도 추적 안 됨 → **P2**
  (⚠️ REST 의 API-CONF-006 보다 한 단계 낮게 — 경계 타입 도입 이전 코드가 다수 존재할 수 있어
  전부 gap 으로 올리면 노이즈. 신규·최근 변경 코드 위주로 보고)

## Gap 분류 코드
- `API-CONF-001`: 엔드포인트 미구현 (coverage_gap → code_fix)
- `API-CONF-002`: 경로/메서드 불일치 (code_drift → code_fix)
- `API-CONF-003`: 요청 계약 표류 (code_drift → code_fix)
- `API-CONF-004`: 응답/envelope 불일치 (code_drift → code_fix)
- `API-CONF-005`: 상태코드 불일치 (code_drift → code_fix)
- `API-CONF-006`: 키트에 없는 엔드포인트 (extra_code → design_update)
- `API-CONF-007`: 경계 계약(SVC/IAPI/LIB) 미구현 (coverage_gap → code_fix)
- `API-CONF-008`: 경계 계약 표류 (code_drift → code_fix)
- `API-CONF-009`: 키트에 없는 경계 구현 (extra_code → design_update)

(YAML 출력의 `dimension:` 값은 `api`, finding `id` prefix 는 `API-CONF`)

## Evidence 인용 룰 (checklist §3 준수)
- 키트 계약: `API-332._raw.json "method":"POST","path":"/datasets/{id}/artifacts"` 또는 요약 `.md` 해당 줄 quote
- 코드: `relative/path.java:line` + 매핑 애너테이션 quote (예 `@PostMapping("/datasets/{id}/artifacts")`)
- 코드 부재: `code_ref: "<부재>"` 명시 (빈 문자열 금지)
- envelope 대조: 키트 ADR-072 envelope 구조 quote ↔ 핸들러 반환 타입 quote 동시 제시

## cross-dimension hint
- API-CONF-001(미구현) ↔ `COV-001`(미구현 ITEM) 연동 — 동일 ITEM 이 양 차원에서 잡히면 `notes_for_main.cross_dimension_hint` 에 `API-CONF-001 ↔ COV-001`
- API-CONF-006(키트 외 엔드포인트) ↔ `COV-002`(키트 외 코드) 연동 — 컨트롤러 추적 실패 시 두 차원 동시 단서
- 권한 가드 부재(키트 required_roles 보유 엔드포인트)는 본 차원이 아니라 `role` 차원(ROLE-CONF-001) 소관 → 발견 시 `cross_dimension_hint` 로만 전달
