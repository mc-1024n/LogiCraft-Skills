# Role Conformance Dimension

권한 가드(코드 측)가 키트의 역할 제한 요구(설계 측)를 **빠짐없이·정확히** 강제하는지 검토. 코드 ↔ 키트 ↔ IMPREC 3방향 대조로 보안 드리프트(공개 누출·역할 어긋남·스텁 가드)를 검출한다.

핵심 대조 축:
- **코드 측** = 권한 가드: `@PreAuthorize`/`@Secured`/`@RolesAllowed` 애너테이션, `AccessGuard`/인터셉터/필터 클래스, Spring Security 설정(`SecurityFilterChain`/`http.authorizeHttpRequests`).
- **키트 측** = `permission_role` ITEM 의 `required_roles` + API ITEM 의 `required_roles` 링크(엔드포인트 ↔ 역할 매핑).
- **IMPREC 측** = 가드 구현 주장(구현 심볼·커밋)이 실제 코드와 일치하는지.

이 차원은 두 방향을 본다:
1. **누락·불일치 (키트가 옳음)**: 키트가 요구한 역할 제한이 코드에 없거나(공개), 강제 역할이 키트와 다름.
2. **표류·과잉 (코드가 앞섬/과함)**: 가드가 스텁/TODO 라 실제론 무력하거나, 키트에 없는 역할을 코드가 강제.

> 룰 ID 형식·finding_type 5종·bucket·confidence·severity·evidence·반증 우선·출력 YAML 스키마는 **`../checklist.md` 공유 계약을 그대로 따른다** (이 차원에서 재정의하지 않음). 룰 ID prefix 는 `ROLE-CONF-NNN`, `dimension:` 값은 `role`.

## STEP 0 — 입력 보강 (검사의 전제)

검사 시작 전 다음을 적재한다 (없으면 보고 불가 → `notes_for_main.unable_to_verify`).

**키트 측 (설계 진실원):**
1. 키트 `permission_role/*.md` 전건 — 각 역할의 정의 + 보호 대상(어떤 API/엔드포인트에 어떤 `required_roles` 가 걸리는지).
2. 각 API ITEM 의 권한 요구 — `required_roles` 필드(없으면 `get_item(API)` 로 보강). 비어있으면 "역할 제한 없음(공개 의도)" 로 간주 — 가드 부재가 gap 아님.
3. 키트 보존/예외 정책(`_domain.md`/`IMPLEMENTATION.md` §주의) — 가드가 의도적으로 단일 교체점(예: `AccessGuard` TODO)으로 남겨진 경우 등을 확인 (의도된 상태는 gap 아님).

**코드 측 (실제):**
- Grep 권한 애너테이션: `@PreAuthorize`, `@Secured`, `@RolesAllowed`, `hasRole`, `hasAuthority`.
- 가드 클래스: `AccessGuard`, `*Interceptor`, `*Filter`, `HandlerInterceptor` 구현체.
- 시큐리티 설정: `SecurityFilterChain`, `authorizeHttpRequests`, `requestMatchers(...).hasRole(...)`, `.permitAll()`.
- 각 핸들러(컨트롤러 메서드)별로 엔드포인트 경로 ↔ 강제 역할을 매핑한다.

→ 키트 `permission_role` 도 0건이고 `required_roles` 보유 API 도 0건이면 **전 룰 skip** + `notes_for_main.unable_to_verify` 에 "역할 제한 요구 키트 ITEM 없음 — 검증 불가" 명시. (억지 finding 금지.)

## 검토 룰

각 룰: 조건 → severity → finding_type(→ bucket 자동) → 검출.

### ROLE-CONF-001: 권한 가드 미적용 (공개 누출)

- 키트가 역할 제한(`required_roles` ≠ ∅)을 요구한 엔드포인트인데, 대응 핸들러에 **어떤 가드도 없음**(애너테이션·인터셉터·시큐리티 매처 전부 부재 → 사실상 공개됨) → **P0 (보안)**.
- `finding_type: code_drift` → `bucket: code_fix` (키트가 옳음, 코드가 가드를 빠뜨림).
- **검출**: 키트 `required_roles` 보유 API 의 엔드포인트 경로 ↔ 코드 핸들러 매핑 후, 그 핸들러(또는 상위 클래스·시큐리티 매처)에 권한 강제 지점이 하나도 없음을 확인.
- ★ **반증 먼저** (checklist §5): 가드가 (a) 클래스 레벨 애너테이션, (b) 부모 인터셉터/필터 체인, (c) 시큐리티 설정의 path 매처 중 **다른 계층**에 있을 가능성을 배제한 뒤에만 단정. 배제 못 하면 `needs_human: true` + P2 강등.

**예시**: "API-2xx `required_roles=[ROLE-DATA-ADMIN]` 인데 핸들러 `XxxController.create():42` 에 `@PreAuthorize` 없음 + 시큐리티 매처 `.permitAll()` → 무인증 공개"

### ROLE-CONF-002: 역할 불일치

- 가드는 **있으나**, 코드가 강제하는 역할 ≠ 키트 `required_roles` (더 약한 역할 허용·다른 역할명·일부 누락 등) → **P1**.
- `finding_type: code_drift` → `bucket: code_fix`.
- **검출**: 핸들러의 `hasRole(...)`/`@Secured(...)` 역할 집합 ↔ 키트 API `required_roles` 집합 비교. 차집합이 비지 않음(코드가 키트보다 느슨하거나 다른 역할).
- ★ **반증**: 역할명 매핑 차이(키트 논리명 `ROLE-DATA-ADMIN` ↔ 코드 물리 권한 `ROLE_DATA_ADMIN`/`DATA_ADMIN`)를 **명명 차이일 뿐 동등**으로 먼저 배제. 동등 매핑이면 gap 아님. 불확실 시 `needs_human: true`.

**예시**: "키트 API-2xx `required_roles=[ROLE-DATA-ADMIN]` ↔ 코드 `@PreAuthorize(\"hasRole('USER')\")`:88 — USER 가 관리자 전용 엔드포인트 호출 가능"

### ROLE-CONF-003: 가드 스텁/TODO

- `AccessGuard`(또는 인터셉터·필터)가 **TODO·항상-허용 스텁**(예: `return true;` // TODO, `// 인증 검증 미구현`)인데, 키트는 그 엔드포인트에 역할 강제를 요구 → **P1**.
- `finding_type: imprec_mismatch` → `bucket: imprec_fix`. (IMPREC 는 가드 구현됐다 주장하나 실제론 무력 — 추적 정정 대상. logicraft 미대조(`degraded: true`)면 `design_stale` → `design_update` 로 분류하고 코드↔키트 표류로 보고.)
- **검출**: 가드 클래스 본문에 무조건 통과 로직 + `TODO`/`FIXME`/`미구현` 주석 동반. 동시에 그 가드가 보호해야 할 엔드포인트가 키트에서 `required_roles` 를 가짐.
- ★ **실증 사례**: D004 의 `AccessGuard` 가 단일 교체점으로 TODO 스텁 상태이며 전체 JWT 검증/ROLE-002 403 이 미구현(운영 전 확인 항목)이다. 단, 키트 `IMPLEMENTATION.md §주의`/`_domain.md` 가 이를 **의도된 단일 교체점**으로 명시한 경우 — finding 으로 보고하되 `needs_human: true` + reason 에 "키트 명시된 의도된 미구현(운영 전 확인 항목)" 을 달아 거짓 P0 승격을 막는다.

**예시**: "`AccessGuard.check():17` `return true; // TODO ROLE-002 검증` ↔ 키트 API 전건 `required_roles` 보유 + IMPLEMENTATION.md §주의 'AccessGuard 단일 교체점·TODO'"

### ROLE-CONF-004: 키트에 없는 권한 강제

- 코드가 **키트에 없는 역할 제한**을 강제(키트 `required_roles` 가 비었거나 그 역할이 `permission_role` 에 정의되지 않음)하는데, 의도된 공개 엔드포인트를 코드가 잠그고 있음 → **P2**.
- `finding_type: extra_code` → `bucket: design_update` (설계 보강 or 의도 확인).
- **검출**: 코드 핸들러의 강제 역할 ↔ 키트 매핑 시, 키트 측에 해당 엔드포인트의 `required_roles` 부재 또는 그 역할이 어떤 `permission_role` ITEM 에도 정의 안 됨.
- ★ **반증**: 키트가 "공개 의도" 로 명시했는지(보존/예외 정책) 먼저 확인. 키트가 단지 `required_roles` 를 **미기재**한 것뿐이면 → 설계 누락(보강 대상)으로 보고하되, 진짜 공개 의도면 코드 측 과잉 잠금 — 어느 쪽인지 모호하면 `needs_human: true`.

**예시**: "코드 `@Secured(\"ROLE_AUDITOR\")`:55 ↔ 키트 API-2xx `required_roles=[]` + `permission_role` 에 ROLE-AUDITOR 정의 없음 → 설계 보강 또는 의도 확인 필요"

## confidence · 반증 · evidence (공유 계약 인용)

- **confidence 판정**: `../checklist.md §4` 의 3중 추적(① IMPLEMENTATION.md 의존맵 ② IMPREC 커밋/심볼 ③ 계약 문자열 grep). `high` 는 2개 이상 일치 시에만. 코드 가드를 직접 grep·심볼로 확인 못 하고 키트만 보고 추정하면 `low` → P2 강등 + `needs_human: true`.
- **반증 우선**: `../checklist.md §5` — "가드가 다른 계층에 있을 가능성"·"역할명 명명 차이일 뿐 동등"·"키트가 의도한 공개/단일 교체점" 을 단정 전에 배제. 배제 못 하면 P2 강등·`needs_human: true`. 의도된 상태(키트 명시)는 gap 아님.
- **evidence 필수**: 모든 finding 에 `kit_item`(API/permission_role ID) + `code_ref`(`relative/path.java:line`, 가드 부재 시 `code_ref: "<부재>"`). 추적 실패 finding 은 보고 금지(`../checklist.md §3`).
- **출력**: `../checklist.md §6` 의 YAML 스키마 한 블록만. `dimension: role`, id `ROLE-CONF-NNN`. `degraded: true`(logicraft 미대조) 면 `imprec_mismatch`(ROLE-CONF-003 의 imprec 경로) 0건 — 대신 `design_stale` 로 분류.
