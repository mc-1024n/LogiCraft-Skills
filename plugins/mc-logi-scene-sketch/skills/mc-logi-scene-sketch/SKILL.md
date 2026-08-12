---
name: mc-logi-scene-sketch
description: 사용자 자연어 시나리오를 ./docs/scene-sketch/ .md 파일(진실원)로 정제 + Logicraft scenario_sketch ITEM으로 자동 등록하는 스킬. 다중 시나리오는 자동 분해해 독립 SKETCH N건으로 분리 등록. SK-001 (배경이미지 요청) 작업 패턴 표준화. 사용자가 "시나리오 스케치 만들어줘" / "이 흐름 logicraft 에 등록해줘" / "기획안 sketch 로 만들어" / "/mc-logi-scene-sketch" 호출 시 트리거.
metadata:
  version: 0.1.0
  author: mc.claude.dev@gmail.com
  category: logicraft
---

# mc-logi-scene-sketch — 시나리오 스케치 자동 등록 스킬

## 목적
사용자 자연어 시나리오 → **로컬 .md 진실원** + **Logicraft scenario_sketch ITEM** 동시 생성.
다중 시나리오는 자동 분해해 독립 SKETCH 로 분리 등록. 사용자 검토 게이트 최소화 (꼭 필요할 때만).

## 트리거
- 슬래시: `/mc-logi-scene-sketch`
- 자연어: "시나리오 스케치 만들어줘" / "이 흐름 logicraft 에 등록해줘" / "기획안 sketch 로" / "scene sketch"
- 자동 감지: 사용자가 다단계 흐름 + actor + 결정 포인트를 묘사하면 제안

## 작업 정책
1. **자동 등록 기본** — 사용자 검토 없이 .md + Logicraft 동시 생성. 사용자가 명시적으로 "검토하고 등록" 요청 시만 Phase 6 게이트 활성화
2. **AskUserQuestion 최소** — 다음 3가지 경우만:
   - project_id 미명시
   - 동일 제목 SKETCH 이미 존재 (신규 vs 덮어쓰기)
   - 시나리오 너무 짧음 (< 50자, 보강 요청)
3. **독립 흐름 자동 분리** — 명백히 독립이면 SKETCH N건 분리 + linked_items 상호 참조
4. **narrative_text verbatim 보존** — AI 가 원문을 절대 가공·축약하지 않음

## 8-Phase 워크플로

### Phase 1: 입력 수집
- raw_prompt 캡처 (사용자 자연어 시나리오 원문)
- project_id 확인:
  - 명시되어 있으면 그대로 사용
  - 미명시 시 `mcp__logicraft__list_projects` → AskUserQuestion 으로 선택
- domain_id 추정 (선택, cross-domain 이면 비움)

### Phase 2: 다중 시나리오 분해
참조: `references/decomposition_rules.md`

raw_prompt 분석 → scenes[] 산출:
- **단일 흐름** → 1개 SKETCH (챕터 = main)
- **선행+본** → 1개 SKETCH (챕터 = prerequisite + main, SK-001 패턴)
- **독립 흐름 2개+** → SKETCH N건 분리 (linked_items 상호 참조)
- **결정 미정 항목** → hotspot step + decisions 챕터(context role)

분해 신호 키워드 (decomposition_rules.md 참조).

### Phase 3: 각 scene AI 정제
참조: `references/scenario_sketch_schema.md`, `references/event_storming_kinds.md`

각 scene 마다:
- `narrative_text`: 원문 verbatim (★ 가공 금지 — 정제본은 별도 .md 섹션)
- `actors[]`: 자동 추출 (kind: human/our_system/external_system/ui/data_store/other)
- `steps[]`: 시간순 + Event Storming kind (command/event/policy/read_model/hotspot/note)
- `assumptions[]`: AI 가 추정·전제한 부분 명시
- `outcomes[]`: 기대 결과
- `chapters[]`: setup(prerequisite) / main / decisions(context) / alternative / followup / error_handling

### Phase 4: 추가 고려사항·선행작업 산정
- 누락 결정 포인트 → D-1, D-2... 번호 부여 → hotspot step + decisions 챕터
- 선행 작업 (기존 ITEM rename·신규 ADR·다른 SKETCH 선행 등)
- 영향 도메인·예상 cascade 규모 추정
- 기존 ITEM 정찰 (선택, `mcp__logicraft__list_items` / `find_*` 도구)

### Phase 5: .md 파일 생성
참조: `references/md_template.md`

경로: `./docs/scene-sketch/SK-{nnn}_{slug}.md`
- {nnn} = 003 자리 (해당 폴더 내 다음 번호)
- {slug} = 제목에서 추출 (한글 가능, 공백→underscore)
- 폴더 없으면 mkdir
- 동일 제목 .md 존재 시 사용자 확인 (AskUserQuestion)

다중 scene 일 때 .md 파일 N건 각각 생성.

### Phase 6: 사용자 검토 게이트 (조건부)
**기본: SKIP (자동 등록 모드)**

사용자가 명시적으로 "검토하고 등록", "확인 후 등록", "draft 만 만들고 멈춰" 등 요청 시만 활성:
- .md 경로 + 핵심 요약 제시
- AskUserQuestion: 그대로 등록 / 수정 후 등록 / 일부만 등록 / 폐기

### Phase 7: Logicraft 등록
각 scene 마다 `mcp__logicraft__create_item`:
- type: `scenario_sketch`
- title, date (today), author=claude, narrative_text (원문 verbatim)
- actors, chapters[].steps, assumptions, outcomes
- tags: 도메인 + 자동 태그 (`scenario-sketch`, `decision-pending` if hotspots, `multi-scene` if N>1, `auto-registered`)
- linked_items: Phase 4 후보
- status: `draft`

ID 자동 발급 (SKETCH-NNN). 발급 후 .md 파일 frontmatter 에 ID 백필.

다중 scene 등록 후 linked_items 상호 추가 (cross-reference).

### Phase 8: 결과 보고
사용자에게 보고:
- 생성 ITEM ID 목록 (SKETCH-{nnn} v1, ...)
- .md 파일 경로 목록
- 결정 대기 hotspot 요약 (D-1 ~ D-{m})
- 다음 액션 제안:
  - hotspot 있으면 결정 수집
  - cascade 진입 가능하면 `mc-logi-update` 안내

## 도구 사용 가이드

### 필수 MCP 도구
- `mcp__logicraft__list_projects` — project_id 확인
- `mcp__logicraft__get_item_schema(type='scenario_sketch')` — 스키마 검증 (캐시 가능, references 참조)
- `mcp__logicraft__create_item(type='scenario_sketch', ...)` — 등록
- `mcp__logicraft__list_items` — 기존 ITEM 정찰 (선택)
- `mcp__logicraft__update_item` — 등록 후 linked_items 상호 백필

### 파일 도구
- `Read` / `Write` — .md 파일 생성·읽기
- `Bash` (mkdir / ls) — 폴더 확인·생성

### AskUserQuestion
3가지 경우만:
1. project_id 미명시 → list_projects 결과로 옵션 제시
2. 동일 제목 SKETCH/.md 존재 → 신규 vs 덮어쓰기 vs 취소
3. 시나리오 너무 짧음 → "보강 입력 받기 vs 그대로 등록"

## 에러 처리
참조: `references/error_handling.md` (있다면)

- `E_VALIDATION` (create_item) → 에러 메시지 그대로 사용자에게 + .md 수정 제안
- `chapters[].role` enum 불일치 → references/scenario_sketch_schema.md 의 매핑 표 참조
- `documented_emitters/consumers` pattern 거부 (^[A-Z]+-\d+$ 형식만) → 빈 배열로 등록, 본문 description 에 자유 텍스트로 보존
- 폴더 권한 오류 → 사용자에게 경로 변경 제안

### ★ scenario_sketch enum 차단 시 (MCP 연결 불안정)
Phase 7 진입 전 `get_item_schema('scenario_sketch')` 로 enum 가용성 사전 검증 권장:
- 차단 시 (enum 누락) → MCP 재연결 문제. .md 파일까지만 생성(Phase 5) + frontmatter 에 registration_blocked 명시 + 신규 세션 재시도 안내
- 복구 후 (ToolSearch 재로드 또는 신규 세션) → .md 기반 create_item 등록

## 등록 후 후속 액션 (사용자 안내만, 자동 진입 X)
- 결정 hotspot 수집 → 후속 update_item 으로 hotspot → policy/event 승급
- cascade 시작 → `mc-logi-update` 스킬 안내
- status 승급 → draft → reviewed → promoted → archived

## 참고
- 예시: `examples/sk-001-example.md` (SK-001 배경이미지 요청 cascade)
- ITEM 스키마: `references/scenario_sketch_schema.md`
- .md 템플릿: `references/md_template.md`
- Event Storming: `references/event_storming_kinds.md`
- 분해 규칙: `references/decomposition_rules.md`
