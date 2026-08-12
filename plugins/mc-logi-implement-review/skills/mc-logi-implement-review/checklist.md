# Implement-Review Auditor 공통 체크리스트 (공유 계약)

> 이 파일은 6개 dimension 파일(`dimensions/{api,schema,policy,coverage,acceptance,role}.md`)과 `logi-implement-auditor` 에이전트가 **그대로 참조하는 공유 계약**이다. 아래 enum·스키마 값은 절대 변형 금지 — dimension 룰과 에이전트 출력이 모두 이 값으로 통일된다.

## 1. 5종 분류 정의 (finding_type ↔ bucket)

키트(설계 진실원)·코드(실제)·IMPREC(구현 주장) 3방향 삼각 대조의 불일치를 다음 5종으로 분류한다.

| `finding_type` | 의미 | `bucket` (자동 매핑) | 후속 핸드오프 |
|---|---|---|---|
| `code_drift` | 코드가 키트 계약을 위반 (키트가 옳음) | `code_fix` | mc-logi-implement / 수동 |
| `design_stale` | 코드가 키트보다 앞섬 (구현 중 확정·설계 미반영) | `design_update` | mc-logi-update |
| `coverage_gap` | 키트 ITEM 에 대응 코드 없음 (미구현) | `code_fix` | mc-logi-implement / 수동 |
| `extra_code` | 코드에 있는데 키트에 없음 | `design_update` | mc-logi-update (or 의도 확인) |
| `imprec_mismatch` | IMPREC 는 구현됐다는데 코드 없음 / 버전 어긋남 | `imprec_fix` | mc-logi-implement Phase 5 (추적 정정) |

**5종 분류 → 버킷 매핑 (고정 — 에이전트는 finding_type 만 정하면 bucket 은 이 표대로):**
- `code_drift` → `code_fix`
- `coverage_gap` → `code_fix`
- `design_stale` → `design_update`
- `extra_code` → `design_update`
- `imprec_mismatch` → `imprec_fix`

## 2. enum 카탈로그 (절대 변형 금지)

```yaml
finding_type: [code_drift, design_stale, coverage_gap, extra_code, imprec_mismatch]   # 5종
bucket:       [code_fix, design_update, imprec_fix]                                    # 3종
confidence:   [high, medium, low]                                                      # 3등급
severity:     [P0, P1, P2]
needs_human:  <boolean: true | false>
```

## 3. evidence 규약 (모든 finding 필수)

- **모든 finding 은 `kit_item`(키트 ITEM ID) + `code_ref`(`relative/path.java:line` 또는 코드 부재 시 명시 문자열) 를 반드시 동반**한다.
- 키트 ITEM 도 코드 위치도 추적하지 못한 finding 은 **보고 금지** (추적 실패 = 무근거 → 폐기).
- 인용 형식:
  - 키트 계약: 키트 ITEM ID + 요약 `.md` 또는 `_raw/*.json` 의 해당 필드 quote
  - 코드: `relative/path.ext:line` + 핵심 줄 quote (`@GetMapping("/x")` 등)
  - 코드 부재: `code_ref: "<부재>"` 로 명시 (절대 빈 문자열로 두지 말 것)
  - IMPREC: implementation record 의 status·version·commit quote

## 4. confidence 등급 + 3중 추적 방법

코드 측 매핑은 본질적으로 **휴리스틱**이므로 다음 3중 추적으로 교차 검증한다:

| ① IMPLEMENTATION.md 의존맵 | ② IMPREC 커밋/심볼 | ③ 계약 문자열 grep |
|---|---|---|
| 키트 IMPLEMENTATION.md 의 빌드순서·의존맵에서 ITEM↔파일/클래스 매핑 | logicraft implementation record 의 커밋 해시·구현 심볼 노트 | path·테이블명·클래스명 등 계약 문자열을 코드에서 직접 grep |

**confidence 판정 (★ 2개 이상 일치해야 `high`):**
- `high` — 3중 추적 중 **2개 이상** 일치 (예: ② IMPREC 커밋 + ③ 계약 문자열 grep 모두 코드 위치 확정)
- `medium` — 1개만 일치 (한 경로로만 추적됨)
- `low` — 코드 측을 grep·심볼로 직접 확인하지 못함 (키트 측만 보고 추정)

> `low` finding 은 우선순위 매김에서 P2 로 강등하고 `needs_human: true` 를 권장한다.

## 5. 반증 우선 규약 (거짓양성 방어)

"명명만 다른데 missing 으로 오판" 하는 거짓양성이 가장 큰 위험이다. 따라서:

1. **단정 전 반증 먼저** — `code_drift`/`coverage_gap` 으로 단정하기 전에 "**다르게 구현됐을 가능성**"(명명 차이·다른 클래스·다른 계층 구현)을 먼저 배제한다.
2. **불확실 시 강등** — 배제하지 못하면 `needs_human: true` + severity 를 **P2 로 강등**한다. 단정 보고 금지.
3. **의도된 상태는 gap 아님** — 키트가 의도적으로 그 상태인 경우(예: 1차 보존 테이블, 백엔드 전용 DFEAT 의 SCREEN 부재, Stub 명시) 는 finding 아님. 키트 보존 정책(`_domain.md`/`IMPLEMENTATION.md`)으로 확인.

## 6. 출력 YAML 스키마 (6 dimension 공통 — 에이전트 반환 형식)

에이전트는 STEP 완료 후 **이 스키마의 YAML 한 블록만** 출력한다 (자유 텍스트 절대 금지).

```yaml
dimension: <api|schema|policy|coverage|acceptance|role>
domain_id: DOMAIN-XXX
degraded: <true|false>   # logicraft 불가로 imprec 대조 생략 시 true
findings:
  - id: <DIM>-CONF-NNN          # 예: API-CONF-001, SCH-CONF-004, COV-002, ROLE-CONF-001
    finding_type: <code_drift|design_stale|coverage_gap|extra_code|imprec_mismatch>
    severity: <P0|P1|P2>
    kit_item: <ITEM-ID 또는 "->코드에만 존재">
    code_ref: "<relative/path.java:line 또는 <부재>>"
    reason: <한 줄>
    confidence: <high|medium|low>
    needs_human: <true|false>
    fix_hint: <코드수정 또는 설계갱신 방향 한 줄>
    bucket: <code_fix|design_update|imprec_fix>
summary: { checked: N, findings: M, p0: a, p1: b, p2: c }
notes_for_main: { unable_to_verify: <...>, cross_dimension_hint: <...> }
```

- `id` 형식: `<DIM>-CONF-NNN` (coverage 차원만 `COV-NNN`). 순번 1부터.
- `summary.findings` = `findings[]` 길이와 일치해야 함. p0+p1+p2 = findings.
- 다른 차원이 함께 봐야 할 단서는 `notes_for_main.cross_dimension_hint` 에 (gap 직접 보고 금지).
- 기준 부재로 검사 불가한 항목은 `notes_for_main.unable_to_verify` 에 명시 (억지 finding 생성 금지).

## 7. read-only 보장 (절대 금지)

본 에이전트는 **검출만** 한다. 다음은 **절대 금지**:

- [ ] **logicraft 쓰기 도구 호출 금지** — `create_item` / `update_item` / `register_*` / `mark_implementation` / `propose_change` / `create_implementation_record` 등 일체. logicraft 는 **조회만**(`get_item`/`list_items`/`get_implementation_coverage`/`get_neighbors`/`get_related`/`get_item_schema`).
- [ ] **코드 수정 금지** — `Edit` / `Write` 로 소스·테스트·마이그레이션 파일 변경 금지. 코드는 **Read/Grep/serena 심볼 조회만**.
- [ ] **키트 수정 금지** — `docs/design/{slug}-{DOMAIN-ID}/` 의 `.md`·`_raw/*.json`·`version-master.md` 등 키트 산출물 변경 금지 (read-only 산출물).
- [ ] **Agent 도구 호출 금지** (재귀 방지) / 사용자 직접 질문 금지 / 자유 텍스트 보고 금지 / 다른 dimension 룰 침범 금지.

## 8. 자가 검증 (보고 직전)

1. dimension 이 입력값과 일치하는가?
2. 모든 finding 에 `kit_item` + `code_ref` 인용이 있는가? (추적 실패 finding 폐기했는가?)
3. `finding_type` → `bucket` 매핑이 §1 표대로인가?
4. `summary` 카운트 = `findings[]` 길이 인가? (p0+p1+p2 = findings)
5. `confidence` 가 `high` 인 finding 은 3중 추적 2+ 일치 근거가 있는가?
6. 불확실한 finding 은 `needs_human: true` + P2 로 강등됐는가?
7. `degraded: true` 면 `imprec_mismatch` finding 이 0건인가? (logicraft 미대조)
8. read-only 위반(쓰기 도구·Edit/Write) 이 없었는가?
