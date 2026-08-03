# Acceptance Conformance Dimension

> ⚠️ **domain-review 의 acceptance 차원(AC↔UC/DFEAT 설계 정합)과 다름** — 여기는 **AC↔테스트 코드** 정합이다. 설계 그래프 추적성(REQ/UC→AC) 이 아니라, 키트가 명시한 인수기준(AC)의 Given/When/Then 시나리오를 **실제 JUnit 테스트가 검증하고 있는지**(코드 측 실증)를 본다.

코드 측 = JUnit 테스트(`@Test`/`@ParameterizedTest`). 키트 측 = `acceptance` ITEM 의 `scenario`(Given/When/Then). AC 가 정한 시나리오가 테스트로 **실증(검증)** 되는지, 테스트가 **다른 동작을 단언**하지 않는지, **폐기된 시나리오 검증 테스트가 잔존**하지 않는지 3축으로 검토한다.

핵심 대조 체인:
- `AC.scenario(given/when/then)` ↔ 테스트 메서드의 `assertion`(상태코드·반환값·예외·상태변화)
- `AC.scenario.then(기대결과)` ↔ `assertThat`/`assertEquals`/`status().is*()`/`assertThrows` 단언 대상
- AC 의 negative/edge 분기(실패·권한·경계) ↔ 그 분기를 단독 검증하는 테스트 메서드 존재

이 차원은 세 축을 본다:
1. **커버리지 (테스트 부재/미커버)**: 키트 AC 가 대응 테스트로 검증되는가 (happy + negative/edge)
2. **표류 (drift)**: 테스트가 있으나 AC 와 **다른 결과**를 단언하는가
3. **현행성 (stale)**: 폐기된 AC 시나리오를 검증하는 테스트가 잔존하는가

## 입력 보강 (STEP 0 — 검사의 전제)

키트 측 적재:
- 도메인 귀속 AC 의 `scenario`(given/when/then)·`statement`·`verification_method`·`is_negative`·`notes` 적재.
  - 적재원: 키트 `acceptance/*.md` 요약 + `acceptance/_raw/*.json` 원본. ★ 시나리오의 **핵심 동작(상태코드·HTTP 메서드·예외·상태 전이·반환 필드)** 을 grep 키로 추출해 둔다.
- 폐기 대조용: 키트에서 **삭제·deprecated 된 AC**(version-master 의 제거 이력, 또는 logicraft `list_items(type=acceptance, include_retired=true)`) — ACC-CONF-004 용. degraded 면 키트 측 흔적만으로 판정.

코드 측 적재:
- Glob `src/test/**`(또는 프로젝트 테스트 루트) 로 테스트 파일 인벤토리 구성.
- Grep `@Test`/`@ParameterizedTest`/`@DisplayName`·`assert*`·`status().is*`·`assertThrows`·`verify(` 로 테스트 메서드·assertion 수집. serena `get_symbols_overview`(테스트 클래스) 로 메서드 목록 확보.
- 키트 AC ↔ 테스트 매핑은 **checklist.md 의 3중 추적**(① IMPLEMENTATION.md 의존맵 ② IMPREC 커밋/심볼 ③ 계약 문자열 grep — 여기선 AC 의 endpoint·예외명·상태코드·`@DisplayName`/메서드명 키워드 grep)으로 교차 검증한다.

→ 도메인 귀속 AC 가 0건이거나 코드 측 테스트 디렉터리가 0건이면 **전 룰 skip** + `notes_for_main.unable_to_verify` 에 "도메인 AC 후보 없음 / 테스트 인벤토리 없음 — 검증 불가" 명시 (억지 finding 금지).

## 검토 룰

각 룰: 조건 → severity → `finding_type` → `bucket` → 검출. `confidence` 등급·반증 우선·evidence(kit_item+code_ref) 규약은 **checklist.md** 를 그대로 따른다(여기서 재정의하지 않음).

### 커버리지 — 테스트 부재/미커버 (ACC-CONF-001 ~ ACC-CONF-002)

#### ACC-CONF-001: AC 검증 테스트 부재
- **조건**: 키트 AC 에 대응하는 테스트가 어디에도 없음 (해당 시나리오의 핵심 동작을 단언하는 테스트 메서드 0건).
- **severity**: **P1**
- **finding_type**: `coverage_gap` → **bucket**: `code_fix`
- **검출**: AC.scenario 의 핵심 동작(상태코드·HTTP 메서드+경로·예외·상태 전이) 을 grep 키로 추출 → 테스트 측 assertion(`status().is4xx`, `assertThrows`, `assertThat(...).isEqualTo`, `verify(...)`)·`@DisplayName`·메서드명 grep 매핑이 **전부 실패**.
- **반증 우선**(checklist.md §5): 단정 전 "다른 클래스/다른 명명으로 검증 중일 가능성"(통합테스트 vs 슬라이스테스트, AC 문구 ≠ 메서드명) 을 먼저 배제. 배제 못 하면 `needs_human: true` + **P2 강등**.

**gap 예시**: "AC-051(artifact 업로드 세션 만료 시 410 반환) — 410 단언 테스트 부재. `assertThat(...status).isEqualTo(410)`·`status().isGone()` grep 0건 (ArtifactUploadSessionTest happy 만)"

#### ACC-CONF-002: 시나리오 미커버 (negative/edge 분기 누락)
- **조건**: AC 의 negative/edge 분기(실패·권한 거부·경계값·동시성 충돌)를 단독 검증하는 테스트가 없음. happy path 만 검증됨.
- **severity**: **P2**
- **finding_type**: `coverage_gap` → **bucket**: `code_fix`
- **검출**: AC 가 `is_negative=true` 이거나 scenario 에 실패/권한/경계 분기를 명시 → 그 분기의 기대결과(예 4xx/예외/롤백) 를 단언하는 테스트 grep 실패. happy assertion 만 존재.

**gap 예시**: "AC-052(동시 TUS 업로드 시 부분 UNIQUE 위반 409) — happy 적재 테스트만 존재, 409/`DataIntegrityViolation` 동시성 분기 단언 테스트 없음"

### 표류 — drift (ACC-CONF-003)

#### ACC-CONF-003: 테스트가 다른 동작 검증 (assertion 표류)
- **조건**: 대응 테스트는 존재하나, 그 assertion 이 AC 의 Given/When/Then 과 **다른 결과**를 단언한다 (예: AC 는 409 인데 테스트는 400 단언, AC 는 예외 발생인데 테스트는 정상 반환 단언, AC 의 then 필드 ≠ 단언 필드).
- **severity**: **P1** (불확실 시 **P2** 강등)
- **finding_type**: `code_drift` → **bucket**: `code_fix`
- **검출**: AC.scenario 와 매핑된 테스트의 assertion 을 **동시 인용** — AC.then 의 기대결과 quote + 테스트 assertion 줄 quote 를 나란히 제시해 불일치를 입증. 한쪽만이면 보고 금지(false positive 억제).
- **needs_human 빈번**: AC 문구와 코드 의미의 미묘한 차이는 사람 판단 필요 → 확신 못 하면 `needs_human: true` + **P2 강등** (checklist.md §5 반증 우선).

**gap 예시**: "AC-053.then '만료 세션 재개 요청은 410 Gone' ↔ ArtifactUploadSessionTest.resumeExpired `status().isNotFound()` (404) — 키트 410 vs 코드 404 단언"

### 현행성 — stale (ACC-CONF-004)

#### ACC-CONF-004: 폐기 AC 검증 테스트 잔존
- **조건**: 테스트가 키트에서 **폐기(삭제·deprecated)된 AC 시나리오**(옛 흐름·옛 endpoint·옛 상태코드) 를 여전히 검증하고 있음.
- **severity**: **P2**
- **finding_type**: `design_stale` → **bucket**: `design_update`
- **검출**: 테스트 assertion 이 대조한 시나리오가 `list_items(include_retired=true)` 또는 키트 version-master 제거 이력의 **폐기 AC** 와 일치 → 설계(폐기 의도 재확인) 또는 테스트(정리) 어느 쪽이 옳은지 사람 판단. 폐기 AC 추적 불가(degraded·이력 없음)면 보고 보류 + `notes_for_main` 에 명시.
- **반증 우선**: "폐기된 게 아니라 명명만 바뀐 현행 AC 를 검증 중일 가능성" 을 먼저 배제. 배제 못 하면 `needs_human: true` 유지.

**gap 예시**: "RulesetPullJobTest.scheduled5min — 5분 batch PULL job 단언. 키트에서 해당 AC 폐기(현행 pull-through proxy 모델로 대체) → 테스트가 죽은 시나리오 검증"

## finding_type ↔ bucket 매핑 (checklist.md §1 그대로)
- ACC-CONF-001 / ACC-CONF-002 → `coverage_gap` → `code_fix`
- ACC-CONF-003 → `code_drift` → `code_fix`
- ACC-CONF-004 → `design_stale` → `design_update`

(YAML 출력의 `dimension:` 값은 `acceptance`, finding `id` prefix 는 `ACC-CONF`)

## Evidence 인용 룰 (checklist.md §3 준수)
- 모든 finding 은 `kit_item`(AC ITEM ID) + `code_ref`(`relative/path.java:line` 또는 테스트 부재 시 `"<부재>"`) 필수. 추적 실패 finding 은 **보고 금지**(폐기).
- 부재(ACC-CONF-001/002): `kit_item: AC-051` + `code_ref: "<부재>"` + AC.scenario then 핵심 동작 quote + "grep 키 X 매핑 0건".
- drift(ACC-CONF-003): **이중 인용 의무** — `AC-053.then "..." ↔ ArtifactUploadSessionTest.java:88 "status().isNotFound()"` (AC quote + 테스트 assertion quote 동시).
- stale(ACC-CONF-004): `list_items(include_retired=true) → AC-019 retired` + `RulesetPullJobTest.java:42 "scheduled5min"` (폐기 AC ↔ 잔존 테스트 동시).

## confidence / 반증 우선 (checklist.md 인용 — 재정의 금지)
- **confidence**(checklist.md §4): 3중 추적 2+ 일치 → `high`, 1개만 → `medium`, 코드 측 테스트를 grep·심볼로 직접 확인 못 함 → `low`. `low` finding 은 P2 강등 + `needs_human: true` 권장.
- **반증 우선**(checklist.md §5): "다른 클래스·다른 명명·다른 테스트 계층으로 검증됐을 가능성" 을 단정 전 먼저 배제. 배제 실패 시 단정 보고 금지 → `needs_human: true` + **P2 강등**. 의도된 상태(키트가 자동화 불가로 수동 검증 명시한 AC 등)는 finding 아님.

## cross-dimension hint
- ACC-CONF-001/003 ↔ `API-CONF-005`(상태코드 불일치): AC then 의 상태코드 ≠ 테스트 단언이 컨트롤러 실제 반환과도 어긋나면 api 차원과 연동 → `notes_for_main.cross_dimension_hint` 에 `ACC-CONF-003 ↔ API-CONF-005`.
- ACC-CONF-001 ↔ `COV-001`(미구현 ITEM): AC 가 검증하는 기능 자체가 미구현이면 테스트 부재는 coverage 차원과 동시 보고 → `ACC-CONF-001 ↔ COV-001`.
- ACC-CONF-004 ↔ `COV-002`/`SCH-CONF-006`(키트 외/폐기 잔재): 폐기 시나리오 테스트가 폐기 코드와 짝이면 연동 보고.
