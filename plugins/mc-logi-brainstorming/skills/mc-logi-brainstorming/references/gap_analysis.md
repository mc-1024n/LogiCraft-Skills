# Phase D Gap 분석 절차

매핑(budget_mapping.md)으로 얻은 산출물 후보를 기존 logicraft ITEM 과 대조해 분류한다.

## 절차
1. 후보 타입별로 기존 ITEM 정찰:
   - `list_items(type=..., domain_id=...)` — 타입+도메인 범위 조회
   - `find_module`/`find_constant`/`find_navigation` — 이름/식별자 매칭
   - `get_item` — 후보와 의미 비교
2. 각 후보를 분류:
   - **신규**: 의미상 동일/유사한 기존 ITEM 없음 → 새로 책정
   - **재사용**: 동일 의미 ITEM 존재 → 기존 ID 참조 (신규 생성 불필요)
   - **갱신**: 유사 ITEM 존재하나 시나리오로 인해 변경 필요 → 갱신 대상 ID + 변경 요지
3. 갱신/신규 후보는 `get_related`/`get_neighbors`로 예상 cascade 규모(연결 ITEM 수) 추정

## 분류 판단 기준
- 제목·식별자·도메인이 일치 → 재사용 우선 검토
- 일치하나 시나리오가 새 필드/상태/엔드포인트를 요구 → 갱신
- 정찰 결과 0건 → 신규 (단 도메인 필터 누락으로 0건일 수 있으니 광역 재확인)

## 출력
각 후보 = { 타입, 상태(신규/재사용/갱신), 후보ID(재사용/갱신 시), 근거 step, 예상 cascade }
→ budget_report_template.md 의 책정표 행으로 전달
