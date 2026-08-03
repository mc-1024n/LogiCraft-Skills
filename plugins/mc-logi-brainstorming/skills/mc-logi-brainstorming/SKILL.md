---
name: mc-logi-brainstorming
description: 대화형 브레인스토밍으로 시나리오를 발굴해 흐름으로 정리하고, mc-logi-scene-sketch로 등록한 뒤, 기존 logicraft ITEM과 대조해 필요 산출물(ADR/ERD/경계 계약 4종 API·SVC·IAPI·LIB/SCREEN/UC/domain_event/NFR/migration/integration/infra/data_pipeline/desktop PMAN·SETT/AI 6종)을 Gap 책정하는 얇은 오케스트레이터 스킬. 사용자가 "시나리오 발굴하고 산출물 책정해줘" / "브레인스토밍해서 로지크래프트 책정까지" / "/mc-logi-brainstorming" 호출 시 트리거. 산출물 책정은 조회+리포트만 (AI 임의 등록 안 함).
metadata:
  version: 0.2.0
  author: mc.claude.dev@gmail.com
  category: logicraft
---

# mc-logi-brainstorming — 시나리오 발굴 + 산출물 책정 오케스트레이터

## 목적
대화형 브레인스토밍 → 시나리오 흐름화 → scene-sketch 등록 → 산출물 Gap 책정을
하나의 연속 파이프라인으로 묶는다. scene-sketch 등록은 mc-logi-scene-sketch를 재사용하고,
산출물 책정(Phase D)은 조회+리포트만 수행한다(실제 ITEM 생성은 사용자가 mc-logi-update로).

## 트리거
- 슬래시: `/mc-logi-brainstorming`
- 자연어: "시나리오 발굴하고 산출물 책정해줘" / "브레인스토밍해서 로지크래프트 책정까지" /
  "아이디어 정리해서 scene-sketch + 산출물 잡아줘"

## 작업 정책
1. **AI 임의 등록 금지** — Phase D는 조회 + 책정 리포트 산출만. 실제 create_item 은 사용자 몫.
2. **쓰기는 Phase C 뿐** — scenario_sketch 등록만 쓰기 작업이며, 반드시 확인 게이트 후 수행.
3. **중복 0** — scene-sketch 로직 재구현 금지, mc-logi-scene-sketch 호출/재사용.
4. **브레인스토밍 원칙 차용, HARD-GATE 미상속** — 종착점은 writing-plans 가 아니라 Phase D.

## 4-Phase 워크플로

### Phase A: 경량 브레인스토밍
참조: `references/phase_a_brainstorming.md`
1. 컨텍스트 선탐색: `mcp__logicraft__list_projects` → project_id 확정, 도메인 추정,
   `list_items`/`find_*`로 기존 ITEM 가볍게 정찰
2. **한 번에 하나씩** 질문 (AskUserQuestion 객관식 우선) — purpose/제약/성공기준
3. 2~3개 접근법 제안 + 추천안
4. 합의되면 Phase B로 (★ writing-plans 호출하지 않음)

### Phase B: 시나리오 흐름 정리
참조: `../mc-logi-scene-sketch/references/event_storming_kinds.md`,
      `../mc-logi-scene-sketch/references/decomposition_rules.md`
1. 발굴 아이디어를 actor / step(시간순 + kind) / hotspot(결정포인트)로 정리
2. 다중 독립 흐름이면 분해 (decomposition_rules 정합)
3. 흐름 요약을 사용자에게 제시 → 합의

### Phase C: scene-sketch 등록 (재사용 + 확인 게이트)
1. **확인 게이트(필수)**: .md 미리보기 + 핵심 요약 제시 →
   AskUserQuestion(그대로 등록 / 수정 후 / 일부만 / 폐기)
2. 게이트 통과 시 `mc-logi-scene-sketch` 호출(또는 동등 로직):
   `create_item(type='scenario_sketch', ...)` + `./docs/scene-sketch/SK-{nnn}_{slug}.md`
3. 등록 결과(SKETCH-NNN, .md 경로) 확보

### Phase D: 산출물 Gap 책정 (조회 + 리포트만)
참조: `references/budget_mapping.md`, `references/gap_analysis.md`,
      `references/budget_report_template.md`
1. **매핑**: 시나리오 step kind/신호 → 산출물 타입 (budget_mapping.md)
2. **Gap 분석**: `list_items`/`find_*`로 기존 ITEM 대조 → 신규/재사용/갱신 분류 (gap_analysis.md)
3. **리포트 산출**: `./docs/discovery/{slug}_budget.md` (budget_report_template.md 골격)
4. **종료**: 책정표 + 결정대기 hotspot 요약 + 다음 액션(mc-logi-update 안내) 보고

## 도구 사용 가이드
- 조회(자동 OK): `list_projects`, `list_items`, `find_module`/`find_constant`/`find_navigation`,
  `get_item`, `get_related`/`get_neighbors`(cascade 규모 추정), `get_item_schema`
- 쓰기(Phase C 게이트 후만): `create_item(type='scenario_sketch')`, 등록 후 .md frontmatter 백필
- 대화: `AskUserQuestion`(Phase A 질문, Phase C 확인 게이트)
- 파일: `Read`/`Write`/`Bash`(mkdir/ls)
- 연계 스킬: `mc-logi-scene-sketch`(Phase C), `mc-logi-update`(Phase D 후속 안내)

## 에러 처리
- project_id 미명시 → `list_projects` 결과로 AskUserQuestion
- scene-sketch 등록 E_VALIDATION → 에러 메시지 그대로 노출 + .md 수정 제안
- 책정 시 후보 타입 0건 → "해당 신호 없음"으로 책정표에서 제외(정상)
- 기존 ITEM 정찰 결과 과다 → 도메인 필터(domain_id)로 범위 축소

## 후속 액션 (안내만, 자동 진입 X)
- hotspot 결정 수집 → mc-logi-update 로 정책/이벤트 승급
- 책정표 신규 N건 → mc-logi-update 로 실제 ITEM 생성
- scene-sketch status 승급: draft → reviewed → promoted

## 참고
- Phase A 원칙: `references/phase_a_brainstorming.md`
- 책정 매핑: `references/budget_mapping.md`
- Gap 분석: `references/gap_analysis.md`
- 리포트 템플릿: `references/budget_report_template.md`
- 예시: `examples/example-budget-report.md`
