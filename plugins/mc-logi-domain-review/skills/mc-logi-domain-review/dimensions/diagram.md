# Dimension: Diagram (다이어그램 정형 반영)

> 도메인의 다이어그램(CDIAG·C4 CTX/CNT/CMP)이 그 도메인의 **활성 DFEAT 를 빠짐없이·
> 올바르게 그리는가**. 신규 DFEAT 가 다이어그램에 미반영되거나, 폐기·없는 DFEAT 를
> 아직 그리고 있는 사각지대를 찾는다.
> 다른 차원은 "DFEAT→UC→SEQ backing" 은 보지만 "DFEAT→다이어그램 반영" 을 안 봤다
> (system-feedback 05bcc047 — S122~126 D003 통합관제센터 클래스/C4 통째 누락이 이
> 차원 부재로 수동 6라운드에야 발견된 실증).

## 검출 원천 — `list_diagram_coverage` MCP 도구 (1차)

먼저 `list_diagram_coverage(project_id, domain_id)` 를 호출한다. (deferred 면 ToolSearch
로 로드). 반환:
- `per_domain[]`: { domain_id, active_dfeats, depicted_dfeats, coverage_pct, missing_dfeats[] }
- `deprecated_refs[]`: 폐기 DFEAT 를 depicts 하는 활성 다이어그램
- `dangling_refs[]`: 존재하지 않는 DFEAT 를 depicts
- `undepicted_diagrams[]`: depicts 가 하나도 없는 활성 다이어그램

도구가 없거나(서버 미반영) 실패하면 **수동 fallback**: 도메인의 active DFEAT 목록과
4종 다이어그램의 `depicts_dfeats[]` + 노드 `dfeat_ref` 를 get_item 으로 모아 직접 차집합.

## 갭 유형

| 유형 | 정의 | severity |
|---|---|---|
| DIAG-001 | **미반영(missing)** — 도메인 활성 DFEAT 인데 그 도메인 어느 다이어그램도 depicts 안 함. 신규 기능군이 다이어그램에 안 들어옴 | P1 |
| DIAG-002 | **폐기 참조** — 활성 다이어그램이 deprecated/superseded DFEAT 를 아직 depicts (구 모델 잔존) | P1 |
| DIAG-003 | **dangling 참조** — 다이어그램이 존재하지 않는 DFEAT id 를 depicts (오타·삭제됨) | P0 |
| DIAG-004 | **미선언 다이어그램** — 활성 다이어그램인데 depicts_dfeats·dfeat_ref 가 모두 비어 그래프에서 무엇을 그리는지 추적 불가 | P2 |
| DIAG-005 | **본문 구 모델(stale body)** — depicts_dfeats 는 활성 DFEAT 정상인데 `components[].description`·`classes[].description`·`relationships` 본문이 폐기 테이블/엔티티·deprecated API·구 식별자·superseded ADR·폐기 흐름(cron/pull/batch)을 참조 (모델 대전환 미cascade). ★ list_diagram_coverage 로 안 잡힘 | P1 |

> severity 조정: 도메인 핵심 DFEAT(다수 UC/API 보유) 가 missing 이면 P0 로 승격.
> coverage_pct 가 현저히 낮은(<50%) 도메인은 요약에 강조.

## 작업 절차

1. `list_diagram_coverage(project_id, domain_id)` 호출 (또는 수동 fallback).
2. `per_domain.missing_dfeats` → DIAG-001 (각 missing DFEAT 가 어느 다이어그램에
   들어가야 자연스러운지 fix_hint 에. 보통 CDIAG(클래스) 또는 도메인의 CMP).
3. `deprecated_refs` → DIAG-002, `dangling_refs` → DIAG-003, `undepicted_diagrams`
   → DIAG-004 각각 gap entry.
4. 본문 클래스/컴포넌트는 있는데 depicts 만 비었는지(=정형 link 누락, DIAG-001/004) vs
   본문 자체가 구 모델인지(DIAG-005) 구분 — 전자는 depicts_dfeats 채움(저비용), 후자는 본문 재작성.
5. ★ **본문 구모델 점검 (DIAG-005) — `list_diagram_coverage` 로 안 잡힘, 본문 정독 필수**:
   depicts_dfeats 가 활성 DFEAT 정상인 다이어그램도 `components[].description`·`classes[].description`·
   `relationships` 를 정독해 도메인의 **폐기 ITEM·구 모델 어휘**를 참조하는지 대조. 검출 신호:
   (a) 폐기 테이블/엔티티명 (b) deprecated API id (c) 구 식별자/계약 (d) superseded ADR 인용
   (e) 폐기 흐름(cron→push·pull→push·batch 등). 진실원 = 도메인 description·활성 ERD/API·
   `brownfield.decided_by` ADR. ★ 그 도메인에 최근 **모델 대전환 ADR**(change_kind 에
   model-change/data-model-redesign/semantic-redefinition)이 있었으면 C4/CDIAG 본문을 **우선 정독**
   (표류 가능성 높음 — D002 CMP-002 실증).

## fix_hint 작성 규칙 (mc-logi-update 입력용)

- DIAG-001: `<CDIAG/CMP-id>.depicts_dfeats 에 <DFEAT-id> 추가 (+ 해당 클래스/컴포넌트 노드에 dfeat_ref). 본문 클래스가 없으면 클래스 N개 신규 작성 필요`
- DIAG-002: `<diagram-id>.depicts_dfeats 에서 폐기 <DFEAT-id> 제거, 대체 활성 DFEAT(<신규-id>)로 교체 + 본문 노드 갱신`
- DIAG-003: `<diagram-id>.depicts_dfeats 의 <id> 오타/삭제 — 올바른 DFEAT id 로 교정 또는 제거`
- DIAG-004: `<diagram-id> 에 depicts_dfeats 선언 — 이 다이어그램이 그리는 도메인 기능 명시`
- DIAG-005: `<CMP/CDIAG-id> 본문의 폐기 <테이블/API/식별자/흐름> 인용을 현행 모델로 재작성 — components/classes description·relationships·external_dependencies 전면 대조. ★부분 수정 금지(모델 대전환 잔재 일괄), update_item patch op set 통째 교체. 어긋난 인용: <구 모델 어휘> → <현행 ADR/ERD 기준>`

## 주의

- **read-only** — depicts 를 직접 채우지 않는다. 검출·초안 제안만. 수정은 mc-logi-update.
- ★ **DIAG-005(본문 구모델)는 `list_diagram_coverage`(depicts 레벨)로 검출 불가** — 본문 정독 필수. depicts 정상이라고 통과시키지 말 것 (D002 CMP-002 실증: DFEAT-060~066 정상 depicts였으나 본문이 batches·썸네일·8:30 cron·API-009/010 구모델로 표류, 모델 대전환 ADR-078/055/075/278 미cascade). cascade 측은 mc-logi-update/cascade-patterns.md 의 `diagram_c4_component`/`class_diagram` 전용 섹션과 짝.
- 폐기 다이어그램(deprecated/superseded)은 검출 대상 아님 (도구가 이미 제외).
- 도메인에 다이어그램이 0개면 차원 SKIP (또는 "다이어그램 미작성" 1건만 보고).
- cross-domain depicts(다른 도메인 DFEAT 를 그림)는 정상 — missing 으로 보지 않는다.
- evidence 에 반드시 `list_diagram_coverage` 결과(coverage_pct, missing 목록) 인용.

## gap 예시

```yaml
- id: D003-DIAG-001
  severity: P0
  type: DIAG-001
  affected_items: [CDIAG-003, DFEAT-075, DFEAT-076]
  reason: 통합관제센터(DFEAT-075)·외부OpenAPI(DFEAT-076) 가 D003 활성 기능인데 어느 다이어그램도 depicts 안 함
  evidence: |
    list_diagram_coverage(D003): active_dfeats=12, depicted=10, coverage_pct=83,
    missing_dfeats=[DFEAT-075, DFEAT-076]. CDIAG-003.depicts_dfeats=[] (클래스 본문도 누락).
  suggested_fix: CDIAG-003 에 통합관제센터/외부OpenAPI 클래스 작성 + depicts_dfeats=[DFEAT-075, DFEAT-076]
  auto_fixable: false
  fix_intent: |
    CDIAG-003.depicts_dfeats 에 DFEAT-075, DFEAT-076 추가. 본문 classes 가 비어 있으면
    각 DFEAT 의 persists_in_tables·implemented_by_endpoints 기준 클래스 노드 신규 작성 후
    해당 노드에 dfeat_ref 연결.
```
