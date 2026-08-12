# mc-logi-scene-sketch

사용자의 **자연어 시나리오**를 두 곳에 동시 생성하는 스킬:
1. **로컬 `.md` 진실원** (`./docs/scene-sketch/`) — 사용자 원문 verbatim 보존 + AI 정제 + 추가 고려사항·선행작업
2. **Logicraft `scenario_sketch` ITEM** (SKETCH-NNN) — actors + chapters[].steps (Event Storming) + hotspot

정형 ITEM(UC/SEQ/FEAT/ADR) 설계 **전 단계**의 캐주얼 입력 계층 (Logicraft Phase 12).

## 무엇을 해주나

- **자동 등록** — 사용자 검토 게이트 없이 .md + Logicraft 동시 생성 (필요 시만 질문)
- **다중 시나리오 자동 분해** — 독립 흐름이면 SKETCH N건 분리 + linked_items 상호 참조. 선행+본은 chapters=[prerequisite, main] 통합
- **Event Storming 분류** — 각 step 을 command/event/policy/read_model/hotspot/note 로 자동 색칠
- **결정 hotspot 추출** — 미해결 의사결정을 D-1, D-2... 로 번호 매겨 `context` 챕터에 모아 후속 cascade 트리거
- **원문 보존** — narrative_text 는 절대 가공 안 함 (정제본은 .md 별도 섹션)

## 사용법

```
/mc-logi-scene-sketch {시나리오 자연어}
```
또는 자연어 트리거: "이 흐름 시나리오 스케치로 만들어줘", "logicraft 에 등록해줘"

## 8 Phase 워크플로

1. 입력 수집 (project_id 미명시 시 질문)
2. 다중 시나리오 분해
3. AI 정제 (actors·steps·assumptions·outcomes)
4. 추가 고려사항·선행작업·cascade 규모 산정
5. .md 파일 생성
6. (조건부) 사용자 검토 게이트
7. Logicraft scenario_sketch 등록
8. 결과 보고 + 다음 액션 안내

## 효과

- 기획 단계의 자연어 아이디어를 즉시 추적 가능한 설계 자산으로 전환
- 등록 후 mc-logi-update cascade 진입으로 UC/API/ERD/SCREEN 전개 가능
- backref 로 어느 ITEM 에서든 원 시나리오 추적

## 참고 자료 (references/)

- `scenario_sketch_schema.md` — ITEM 스키마·chapter role enum·payload 템플릿
- `md_template.md` — 로컬 .md 표준 (10 섹션)
- `event_storming_kinds.md` — step kind 분류 결정 트리
- `decomposition_rules.md` — 다중 시나리오 분해 매트릭스
- `examples/sk-001-example.md` — 실제 사례 (배경이미지 요청 → ~50 ITEM cascade)

## 의존성
- Logicraft MCP (create_item / list_projects / get_item_schema)
- scenario_sketch ITEM 타입 지원 (Logicraft Phase 12)