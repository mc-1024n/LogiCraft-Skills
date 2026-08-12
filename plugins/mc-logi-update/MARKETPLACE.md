# mc-logi-update — Logicraft Update Orchestrator

Logicraft ITEM 수정을 **가이드대로 정확히** 수행하고, 변경이 일으키는 **cascade 영향을 재귀적으로 추적·정합**하는 오케스트레이터 스킬.

## 무엇을 하나
- 사용자가 ITEM 수정을 요청하면("SEQ-020 재작성", "ADR 추가 후 cascade", "명칭/path/테이블 변경 정합")
- 토폴로지 의존 순서(adr→erd→api→dfeat→uc/nav→seq/screen)로 정렬해 라운드 단위로 처리
- **trivial**(단일 필드·link 보강·stale-ack)은 메인이 직접 `update_item` patch (1~3초)
- **복잡**(description 통째 재작성·다단계 편집·의미 변경)은 `logi-update-specialist` 에이전트 위임
- 각 변경 후 `analyze_impact` 로 cascade 후보를 큐에 추가, MAX_DEPTH까지 재귀

## 핵심 특징
- **AI 추정 금지** — brownfield 메타·외부 식별자는 1차 소스/edit_context 근거로만 자동 추정, 실패 시 보고
- **스키마 캐시 워밍** — 타입별 schema를 24h TTL 로컬 캐시(토큰 절약 + workflow_notes 완독 보장)
- **상류 requirement sync** — 도메인/DFEAT 의미 변경 시 부모 REQ를 RFP+도메인 재대조로 refresh
- **post-edit 검증** — 라운드별 random sample re-fetch 로 적용 확인
- 종료 시 메모리 자동 저장

## 1.3.0 변경 (C4·test_scenario 약-link cascade 보강)
- **diagram_c4_component / class_diagram 전용 섹션**: C4 컴포넌트·클래스 다이어그램은 `depicts_dfeats`(DFEAT 레벨)로만 연결돼, 필드 레벨 모델 대전환(배치/썸네일 제거·push 전환·식별자 변경·cron→push)이 일어나도 link 무변 → `analyze_impact` 가 dependent로 안 띄우는 사각지대. 모델 대전환 ADR cascade 시 해당 도메인 CMP/CDIAG를 **수동 큐잉** + 본문(description·relationships) **전면 refresh**(부분 수정 금지). D002 CMP-002 실증.
- **test_scenario 검증 산출물 섹션**: 통합/시스템 시험 시나리오(TEST)는 covers_use_cases·exercises_screens·verifies_requirements/nfrs·related_apis로 추적하나 약-link라 analyze_impact에 안 뜰 수 있음 → UC/SCREEN/API/REQ/NFR/ERD 의미 변경 시 `list_items(type=test_scenario)` 교차 수동 점검. AC(acceptance)와 동일 패턴.

## 함께 쓰는 스킬
- **mc-logi-domain-review** — 갭 검출(read-only). 검출 후 그 입력으로 이 스킬 호출
- **mc-logi-implement-kit** — 정합 완료 설계를 로컬 구현 키트로 다운로드