# mc-logi-update — Logicraft Update Orchestrator

Logicraft ITEM 수정을 가이드대로 정확히 수행하고, 그 수정이 일으키는 **cascade 영향을 재귀적으로 추적·정합**하는 오케스트레이터 스킬입니다. 한 ITEM만 고치고 끝나는 게 아니라 연결된 ITEM까지 일괄 일관성을 맞춥니다.

## 무엇을 하나

대상 ITEM을 식별 → 큐 초기화 → 라운드별로 처리하며, 각 처리 후 `analyze_impact`로 cascade 후보를 찾아 큐에 넣고 `MAX_DEPTH`까지 반복합니다.

- **trivial 변경**(단일 필드 set/remove, enum 변경, stale 라이트터치 등)은 메인이 **직접 `update_item` patch** — 1~3초/~2K 토큰
- **복잡 변경**(description 재작성, 다단계 편집, 의미 변경)은 **`logi-update-specialist` 에이전트** 호출
- 토폴로지 순서(adr→erd→api→dfeat→uc/nav→seq/screen)대로 정렬, 독립 ITEM은 병렬 그룹

## 언제 쓰나

- 특정 ITEM 수정 + 그 여파 정합 (예: "SEQ-020 재작성", "DFEAT-064 정합")
- 새 ADR/결정 후 영향 ITEM cascade
- 1차 소스 검증 결과 잘못된 설계 일괄 수정
- 명칭/path/테이블 변경 cascade, stale 일괄 해소

## 언제 쓰지 않나

- 신규 ITEM 단독 생성(cascade 불필요) → logicraft MCP 직접
- 단순 조회 → `get_item`/`list_items` 직접
- 코드 리팩터/리뷰 → `mc-code-refactorer`/`mc-code-reviewer`

## 효과 / 받는 것

- **일괄 일관성** — 한 변경의 모든 파급을 재귀 추적해 끊긴 link/모순 제거
- **AI 추정 금지 정책** 준수 + brownfield 메타 자동 추정(실패분만 보고)
- 변경 요약 표 + cascade 라운드 로그 + post-edit 무작위 검증
- 스키마 캐시 워밍으로 토큰 절약, 종료 시 메모리 자동 저장

## 사용 예

```
"SEQ-020 title에 BFF 잔재 있어. 정합해줘"
→ specialist(SEQ-020) → cascade 0 → 1 ITEM 변경 보고

"1차 소스 따라 SEQ-020 재작성"
→ cascade[UC-020, DFEAT-064, API-188, ERD-021/022, SCREEN-022]
→ 토폴로지 정렬 병렬 처리 → 7 ITEM 변경 + HTML 재업로드 보류 보고
```

## 한계 / 보안

- ITEM 삭제·소프트삭제 안 함, 다른 프로젝트 영향 없음(project_id 고정)
- 1차 소스 코드는 읽기만, MAX_DEPTH(기본 3) 도달 시 미처리 큐 보고

## 관련 스킬

`mc-logi-domain-review`(갭 검출 → 본 스킬로 수정) · `skill-creator`

> 미검증 마켓플레이스 항목 — 설치 전 SKILL.md 원문도 함께 확인하세요.
