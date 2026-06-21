# mc-logi-brainstorming

대화형 브레인스토밍으로 시나리오를 발굴해 흐름으로 정리하고, mc-logi-scene-sketch로 등록한 뒤, 기존 설계와 대조해 필요 산출물을 Gap 책정하는 얇은 오케스트레이터. "무엇을 만들지" 발굴부터 책정까지 한 흐름으로 묶는다.

## 무엇을 하나
- **Phase A — 경량 브레인스토밍**: `list_projects`로 컨텍스트 선탐색 → 한 번에 하나씩 질문(purpose·제약·성공기준) → 2~3개 접근법 제안.
- **Phase B — 시나리오 흐름화**: 발굴 아이디어를 actor / step(시간순+kind) / hotspot(결정포인트)로 구조화, 다중 흐름 자동 분해.
- **Phase C — scene-sketch 등록**: 확인 게이트(미리보기 → 그대로/수정/일부/폐기) 후 mc-logi-scene-sketch 재사용해 `scenario_sketch`(SKETCH-NNN) + .md 등록.
- **Phase D — 산출물 Gap 책정**: step 신호 → 산출물 타입 매핑 → 기존 ITEM 대조(신규/재사용/갱신 분류) → `docs/discovery/{slug}_budget.md` 리포트.

## 어떤 효과
- 발굴~책정이 한 파이프라인 — "아이디어"에서 "무엇을 만들지 목록"까지 끊김 없이.
- **AI 임의 등록 안 함** — Phase D는 책정 리포트만 산출, 실제 `create_item`은 사용자가 mc-logi-update로.
- 중복 0 — scene-sketch 로직을 재구현하지 않고 호출·재사용(쓰기는 Phase C 한 곳뿐).

## 사용 예
- "시나리오 발굴하고 산출물 책정해줘"
- "브레인스토밍해서 로지크래프트 책정까지"
- `/mc-logi-brainstorming`

## 요구 사항
- **LogiCraft MCP**: `list_projects` / `list_items` / `find_*` / `get_item` / `get_related` (조회)
- **연계 스킬**: mc-logi-scene-sketch(Phase C 등록), mc-logi-update(Phase D 후속 ITEM 생성)

## 구성
- `SKILL.md` — 4-Phase 절차·작업 정책
- `references/phase_a_brainstorming.md` — Phase A 질문 원칙
- `references/budget_mapping.md` — step kind → 산출물 타입 매핑
- `references/gap_analysis.md` — 기존 ITEM 대조 규칙
- `references/budget_report_template.md` — 책정 리포트 골격
- `examples/example-budget-report.md` — 책정 리포트 예시

## 한계
- 산출물 책정은 **리포트만** — 실제 ITEM 생성은 mc-logi-update 별도 호출.
- Phase C 등록은 mc-logi-scene-sketch에 의존(미설치 시 등록 불가).
