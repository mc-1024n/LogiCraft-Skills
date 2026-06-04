---
name: mc-logi-update
description: Logicraft ITEM 수정을 가이드대로 정확히 수행하고 cascade 영향을 재귀적으로 추적해 처리하는 오케스트레이터 스킬. 사용자가 logicraft ITEM 수정·갱신·정합을 요청하면(예 "SEQ-020 수정해줘", "DFEAT-064 정합해줘", "ADR 추가하고 cascade 해줘") logi-update-specialist 에이전트를 띄워 1 ITEM씩 처리하고 분석된 cascade 후보를 재귀 처리. 일괄 일관성 보장 + AI 추정 금지 정책 + brownfield 메타 자동 추정 + 종료 시 메모리 저장 문의.
license: MIT
allowed-tools: Read, Write, Edit, Grep, Glob, Bash, Agent, ToolSearch, AskUserQuestion, TaskCreate, TaskUpdate, TaskList
metadata:
  version: "1.3.0"
  domain: logicraft-orchestration
  triggers: logicraft 수정, logicraft cascade, ITEM 수정, ITEM 정합, SEQ 수정, DFEAT 수정, API 정합, SCREEN 수정, ERD 정합, ADR 추가, cascade 처리, 영향 추적
  role: orchestrator
  scope: logicraft-item-edit
  output-format: 변경 요약 표 + cascade 라운드 로그
  related-skills: skill-creator
---

# mc-logi-update — Logicraft Update Orchestrator

Logicraft ITEM 수정을 가이드대로 정확히 수행하고 cascade 영향을 재귀적으로 추적·처리하는 오케스트레이터.

## When to Use

- 사용자가 특정 logicraft ITEM 수정 요청 (예: "SEQ-020을 1차 패턴으로 재작성")
- 새 ADR/결정 후 영향 받는 ITEM cascade 정합 필요
- 1차 소스 검증 결과 잘못된 설계 발견 → 일괄 수정
- 명칭·path·테이블 변경 cascade
- stale ITEM 일괄 해소

## When NOT to Use

- 신규 ITEM 단독 생성 (cascade 불필요) — logicraft MCP 직접 호출
- 단순 조회·검색 — `list_items` / `get_item` 직접 호출
- 코드 리팩토링 (mc-code-refactorer)
- 코드 리뷰 (mc-code-reviewer)

## 핵심 원칙 (사용자 결정 반영)

1. **단일 specialist 에이전트 + item_type 파라미터** — 35 타입을 한 에이전트가 schema 동적 로드로 처리
2. **batch 모드 기본** — 자동 진행. 라운드별 사용자 승인 생략
3. **MVP 8 타입**: api_endpoint, screen_spec, diagram_sequence, use_case, domain_feature, erd, adr, navigation_tree
4. **자동 추정 후 보고** — brownfield 메타·외부 식별자는 specialist가 자동 추정, 실패 항목만 종료 시 보고
5. **종료 시 메모리 저장 문의** — 작업 완료 후 사용자에게 메모리 저장 여부 확인

## 워크플로우

### Phase 1 — 진입 + 대상 식별

1. 사용자 요청 파싱:
   - 명시적 ITEM ID 있으면 채택
   - 모호하면 `AskUserQuestion`으로 확정 (대상 ITEM ID + 의도 1줄)
2. 의도 확정:
   - 단순 명칭 변경 / 의미 변경 / 신규 추가 / 잔재 정리 등 분류
3. project_id 식별:
   - `~/.claude/projects/*/memory/MEMORY.md`에서 현재 프로젝트 확인
   - 메모리 없으면 사용자에게 묻기

### Phase 2 — 큐 초기화

```yaml
queue: [<primary_target_id>]
processed: []
edit_logs: []
depth: 0
MAX_DEPTH: 3
```

`TaskCreate`로 라운드별 가시화 — 큐의 각 ITEM당 task.

### Phase 2.5 — 스키마 캐시 워밍 (★ NEW — 토큰 절약 + 가이드 완독 보장)

**문제**: `get_item_schema(type)` 응답은 크다 (예: screen_spec ≈ 71KB → persisted-output 분할). specialist 매 호출마다 MCP 왕복하면 라운드당 수십만 토큰 낭비 + 첫 청크만 읽고 워크플로 후반(신규 섹션)을 놓칠 위험.

**해결**: 메인이 라운드 진입 전 타입별 schema를 로컬 캐시에 1회 워밍. specialist는 **캐시 파일 read-only** (직접 `get_item_schema` 호출 안 함).

```
캐시 디렉토리: ~/.claude/cache/logicraft-schema/{item_type}.json
캐시 구조:
  { "_cache_meta": { "fetched_at": "<ISO8601>", "schema_version": <int>, "source": "get_item_schema" },
    ... (get_item_schema 응답 본문 그대로) }
```

**워밍 절차** (Phase 3 라운드 LOOP 진입 직전 + 각 라운드 시작 시 distinct type 대상):

```python
import os, json, datetime
CACHE_DIR = os.path.expanduser("~/.claude/cache/logicraft-schema")
os.makedirs(CACHE_DIR, exist_ok=True)
TTL_HOURS = 24

for t in distinct_item_types(current_round):           # 이번 라운드 큐의 고유 타입만
    path = f"{CACHE_DIR}/{t}.json"
    stale = True
    if os.path.exists(path):
        meta = json.load(open(path, encoding="utf-8")).get("_cache_meta", {})
        age_h = (datetime.datetime.now(datetime.timezone.utc)
                 - datetime.datetime.fromisoformat(meta["fetched_at"])).total_seconds() / 3600
        stale = age_h > TTL_HOURS
    if stale or force_refresh:                          # force_refresh = 사용자가 "배포됐다" 알린 경우
        resp = get_item_schema(type=t)                  # MCP 1회 (persisted-output 가능 → 파일로 받음)
        body = json.loads(resp_text)                    # persisted 파일이면 읽어서 파싱
        body["_cache_meta"] = {
            "fetched_at": datetime.datetime.now(datetime.timezone.utc).isoformat(),
            "schema_version": body.get("schema_version"),
            "source": "get_item_schema",
        }
        json.dump(body, open(path, "w", encoding="utf-8"), ensure_ascii=False)
    # specialist prompt 엔 schema_cache_path = path 만 전달
```

**무효화 정책 (3중)**:
1. mtime/`fetched_at` 기준 24h 초과 → 자동 refresh
2. 사용자가 "가이드 배포됐다 / schema 바뀌었다" 알림 → `force_refresh=true` 로 전체 무효화
3. specialist가 캐시의 `_cache_meta.schema_version` 과 실제 ITEM `get_item` 응답의 `schema_version` 불일치 감지 시 → notes_for_main 에 `schema_cache_stale: <type>` 보고 → 메인이 다음 라운드에서 강제 refresh

**동시성 안전**: 캐시 write 는 **메인 단독**. 병렬 specialist 는 read-only → race condition 없음.

### Phase 3 — 라운드 처리 LOOP

```
while queue not empty AND depth < MAX_DEPTH:
  current_round = queue 전체 복사
  queue = []
  depth += 1

  # 토폴로지 의존 처리
  current_round를 cascade-patterns.md 순위표대로 정렬
  의존성 있는 ITEM은 직렬, 독립은 병렬 그룹화

  # 병렬 그룹 처리
  for group in parallel_groups:
    # 한 메시지에 multiple Agent tool uses
    spawn specialist agents (subagent_type=logi-update-specialist)
    각 prompt에 target_id, item_type, edit_intent, edit_context, cascade_origin, project_id 포함
    cascade-patterns.md + checklist.md 본문 첨부

    wait all completions

    for each specialist report (YAML):
      validate YAML 형식
      processed.add(report.edited.id)
      edit_logs.append(report)

      for candidate in report.cascade_candidates:
        if candidate.id in processed: skip (cycle 방지)
        if candidate.auto_propagate == false:
          → pending_user_decisions에 보류 (라운드 종료 시 일괄 보고)
        else:
          queue.append(candidate) with edit_intent=candidate.suggested_edit_intent

  # 라운드 종료 — batch 모드는 자동 진행
  # depth 증가 후 다음 라운드
```

### Phase 4 — 종료

종료 조건:
- queue 비었음 (자연 종료)
- depth ≥ MAX_DEPTH (보호 종료, 보고 시 사용자에게 알림)
- specialist 3회 retry 실패 (사용자 개입)
- pending_user_decisions 발생 시 일괄 확인

### Phase 4.5 — Post-edit Verification (NEW)

라운드별 specialist 완료 후 메인이 random sample 1~2건 verify:

1. **무작위 sample**: 라운드 변경 ITEM 중 1~2건 선택
2. **재 fetch**: `get_item(sample_id)` → 변경 적용 확인
   - `current_version` 증가 확인
   - 변경한 필드 값이 의도와 일치 확인
   - `warnings` 잔존 확인
   - `stale` 플래그 정합 확인
3. **discrepancy 발견 시**:
   - specialist YAML 재검토
   - 같은 ITEM 다시 처리 또는 사용자 보고
4. **모두 정합 시**: 다음 라운드 진행

verify 결과 Phase 5 보고에 포함 (`verified: N/M samples checked`).

### Phase 5 — 보고

변경 요약 표 (사용자에게):

```
| # | ITEM | Type | Before → After | 변경 요약 | warnings |
|---|------|------|----------------|-----------|----------|
| 1 | SEQ-020 | diagram_sequence | v10 → v13 | LS_DATA_RAW INSERT 패턴 복귀 | - |
| 2 | UC-020 | use_case | v9 → v10 | main_flow 재작성 | - |
| ...

## 자동 추정 실패 항목 (사용자 검토 필요)
- ERD-022 brownfield.legacy_source.identifier: 추정 불가
- ADR-051 references[].url: 인용 ITEM URL 불명

## Cascade 미처리 (사용자 결정 필요)
- SCREEN-022 HTML 재업로드 (multi-surface)
- ADR-036 본문 정정 (인용 정합)
```

### Phase 6 — 자동 메모리 저장 (사용자 결정 #5 — 자동, 묻지 않음)

**자동 진행** — 사용자 확인 묻지 않음. Phase 5 보고 후 즉시 저장.

1. **타임스탬프 수집**: `Bash date +%Y%m%d_%H%M` 실행 (실제 현재 시각, 임의 생성 금지)
2. **파일명 자동 생성**: `session_{NN}_{topic}_cascade_{YYYYMMDD}_{HHMM}.md`
   - 예: `session_33_d002_cascade_20260514_1248.md`
   - session 번호: MEMORY.md 최근 entry에서 자동 추출
   - topic: 대상 ITEM ID 또는 도메인 ID (예: seq_020, d002)
3. **메모리 파일 작성**: 변경 ITEM 표 + warnings + 잔여 작업 + 노하우
4. **MEMORY.md 인덱스 자동 추가**: 최상단
   - 형식: `- **★★★★ [Session NN <topic> cascade (mc-logi-update, YYYY-MM-DD HH:MM)](filename)** — N건 처리 ... 핵심 변경 ...`

저장 완료 후 사용자에게 파일명만 보고. 별도 확인 묻지 않음.

**예외**: 사용자가 명시적으로 "메모리 저장하지 마"라고 했을 때만 skip.

## ★ Trivial 직접 처리 가이드 (specialist 우회)

다음 경우 specialist 호출 대신 메인이 직접 `update_item` patch 실행 (검증 완료, Session 33 D002 cascade):

### 직접 처리 케이스 (트리비얼)
- 단일 필드 set/remove (예: `implements_features=[FEAT-007]`)
- 배열 항목 1~2건 add/remove (예: `realizes_use_cases=[UC-019, UC-020]`)
- enum 값 변경 (예: `status: "approved"`)
- brownfield.notes 텍스트 추가 (1~2 줄)
- change_summary 정합 (의미 보강)
- stale 해소 (description 라이트 터치)

### Specialist 호출 케이스 (복잡)
- description 통째 재작성 (Session 33 v3 SEQ-020 같은 case)
- main_flow / sections / messages 다단계 편집
- 의미 변경 + 다른 ITEM cascade 발생 가능성
- 새 enum 값 도입 / schema 검증 필요
- 1차 소스 검증 필요

### 효율 비교 (실측)
- Specialist 1건 호출: 평균 100~130초, 150~200K 토큰
- 직접 patch 1건: 1~3초, ~2K 토큰
- 18건 trivial 모두 specialist 호출 시: ~30분 + 3M 토큰 → 비효율

### 운영 가이드
- Phase 3 라운드 진입 전 각 ITEM의 fix_intent 분류
- trivial → 메인이 직접 update_item 병렬 batch (4~5건 parallel)
- 복잡 → specialist 호출
- 혼합 시 직접 처리부터 batch → specialist 그룹

## Specialist 호출 패턴 (Agent tool 사용)

#### ★ Agent 이름 해석 + 등록 fallback (중요)

`logi-update-specialist` 에이전트는 **설치 방식에 따라 등록 이름이 다르다**:
- **플러그인 설치** (`/plugin install mc-logi-update@logicraft`): 에이전트가 `agents/logi-update-specialist.md` 로 동봉되어 **scoped name `mc-logi-update:logi-update-specialist`** 로 자동 등록 (fresh 세션에서 즉시 사용 가능 — "not found" 없음)
- **user/project scope** (개발 환경, `~/.claude/agents/`): bare name `logi-update-specialist`

따라서 다음 순서로 시도 (절대경로 하드코딩 금지 — 설치 위치 무관):

**Case 1 — 전용 에이전트 호출** (첫 성공 채택):
1. `subagent_type="mc-logi-update:logi-update-specialist"` (플러그인 scope, 배포 환경 기본)
2. 실패 시 `subagent_type="logi-update-specialist"` (user/project scope, 개발 환경)

**Case 2 — 둘 다 `Agent type ... not found`** → general-purpose 로 fallback + 에이전트 정의를 **동적 탐색**해 인라인:
```python
# 1) 에이전트 정의 파일을 Glob 으로 탐색 (설치 위치 무관, 절대경로 박지 말 것)
#    Glob("**/agents/logi-update-specialist.md") → 첫 결과를 Read → agent_md_content
# 2) cascade-patterns·checklist 는 메인이 이미 읽어둔 내용(cascade_patterns_content,
#    checklist_content; 스킬 디렉터리 상대 — cascade-patterns.md, checklist.md)을 그대로 인라인
Agent(
  subagent_type="general-purpose",
  description="Update <ITEM-ID> (fallback)",
  prompt=f"""당신은 logi-update-specialist 역할입니다. 아래 system prompt 를 그대로 따르세요:

# logi-update-specialist 시스템 프롬프트
{agent_md_content}

## cascade-patterns.md
{cascade_patterns_content}

## checklist.md
{checklist_content}

# 입력
{입력 yaml}

# 출력
STEP H YAML 한 블록만 출력하고 종료. 자유 텍스트 금지.
"""
)
```

검증 완료 (Session 33 D002 cascade). 플러그인 배포 시 Case 1-1(plugin scope)으로 정상 동작, Case 2 는 안전망.

```python
# 정식 호출 패턴
Agent(
  subagent_type="logi-update-specialist",
  description="Update <ITEM-ID>",
  prompt=f"""
당신은 logi-update-specialist입니다. 다음 ITEM을 가이드대로 수정하세요.

# 입력
target_id: {target_id}
item_type: {item_type}
edit_intent: {edit_intent}
edit_context: |
  {edit_context}
cascade_origin: {cascade_origin}
project_id: {project_id}
schema_cache_path: {schema_cache_path}   # ★ Phase 2.5 워밍된 로컬 캐시. get_item_schema 직접 호출 금지, 이 파일을 Grep/Read 로 정독.

# 참조
다음 두 문서를 반드시 따르세요:

## cascade-patterns.md
{cascade_patterns_content}

## checklist.md
{checklist_content}

# 출력
STEP A~G 완료 후 YAML 한 블록만 출력하고 종료.
""",
)
```

## 토폴로지 정렬 룰

cascade-patterns.md의 우선순위표 참조:
1. adr → 2. erd → 3. api_endpoint → 4. domain_feature → 5. use_case / navigation_tree → 6. diagram_sequence / screen_spec

같은 순위라도 `depends_on_completion`에 명시된 ITEM은 선행 처리.

### ★ 상류(upstream) requirement sync (cascade-patterns.md "상류 cascade" 섹션)
도메인 계층 ITEM(DFEAT/domain/ERD)을 **의미(모델·범위·계약) 변경**하면 부모 `requirement`(REQ)가 stale 해진다(도메인이 REQ 보다 최신 — Session 71 D004 실증). specialist 가 의미 변경 시 부모 REQ 를 cascade_candidate(`auto_propagate: true`)로 보고하면 메인이 자동 큐잉 → REQ 를 **RFP(rfp_item, 불변 원천)+도메인(현재) 재대조**로 refresh(도메인 우선+RFP 배경·`derived_from_rfp` link 보강).
- ★ 가드: trivial(stale-ack·오타·field-count·HTML 재업로드)은 상류 트리거 안 함. 의미 변경만.
- ★ REQ 는 catch-up 종착 → REQ 처리 후 그 **하위는 재큐 금지**(무한루프 방지).
- ★ Phase 5 보고에 REQ 변경 **명시**(요구사항 변경은 사용자 가시화 필요).
- ★ `rfp_item`(RFP-NNN)은 **읽기 전용** — 재대조 입력으로만, 절대 수정 안 함.

## 병렬 vs 직렬

**병렬 (한 메시지에 multiple Agent calls)**:
- 같은 토폴로지 순위
- 서로 link 없음 (analyze_impact 교차 없음)
- 다른 도메인

**직렬**:
- 다른 토폴로지 순위
- `depends_on_completion` 명시
- 같은 ITEM (base_version 충돌 방지)

병렬 그룹 크기 상한: 5 (resource 관리)

## 에러 처리

| 에러 | 대응 |
|---|---|
| specialist YAML 파싱 실패 | 1회 재시도 (프롬프트에 형식 강조) → 실패 시 사용자 보고 |
| base_version conflict | specialist 내부 retry (최대 2회). 그래도 실패하면 사용자 개입 |
| analyze_impact 응답 없음 | cascade 후보 없음으로 처리 + warning |
| MCP 도구 다운 | ToolSearch 재시도 → 실패 시 작업 중단 + 부분 결과 보고 |
| MAX_DEPTH 도달 | 미처리 큐 사용자에게 보고. 추가 라운드 여부 확인 |

## TaskList 관리

`TaskCreate`로 각 ITEM당 1 task:
- subject: `<ITEM-ID> 수정 (<intent 한 줄>)`
- description: target_id, item_type, edit_intent, cascade_origin

상태:
- pending: 큐 진입 직후
- in_progress: specialist 실행 중
- completed: YAML 보고 받음 + cascade enqueue 완료
- 라운드 종료 시 stale task 제거

## 사용자 결정 정책 (자동 추정 우선)

기본 자동 진행. 다음 경우만 사용자에게 묻기:

1. **진입 시**: 대상 ITEM 모호하거나 의도 불분명
2. **라운드 종료 시**: `auto_propagate=false` cascade 후보 처리 여부 (모드 옵션 — interactive)
3. **종료 시**:
   - 자동 추정 실패 항목 (auto_estimation_failed)
   - MAX_DEPTH 도달 시 추가 라운드 여부
   - 메모리 저장 여부 + 파일명

## 보안·범위

- ITEM 삭제·소프트 삭제 안 함 (specialist 금지)
- 다른 프로젝트 ITEM 영향 안 줌 (project_id 고정)
- 1차 소스 코드 읽기만 (편집 금지)
- **rfp_item(RFP-NNN) 읽기만 — 수정 금지** (불변 발주처 진실원천, 상류 REQ refresh 의 재대조 입력으로만)
- 로컬 파일 변경은 99. screen / 메모리만

## 호출 예시

### 예시 1: 단일 ITEM 명칭 정정 (자명한 cascade)
```
사용자: "SEQ-020 title에 BFF 잔재 있어. 정합해줘"
→ Phase 1: target_id=SEQ-020, intent="BFF 잔재 제거"
→ Phase 3 라운드 1: specialist(SEQ-020) → cascade 0건 (slug 변경은 link 무관)
→ Phase 5: 1 ITEM 변경 보고
→ Phase 6: 메모리 저장? "안 함" → 종료
```

### 예시 2: 의미 변경 + 큰 cascade
```
사용자: "1차 ServiceImplOriginalSendLearning 따라서 SEQ-020 재작성"
→ Phase 1: target_id=SEQ-020, intent="REST 모델 폐기 LS_DATA_RAW INSERT 패턴"
→ Phase 3 라운드 1: specialist(SEQ-020) → cascade[UC-020, DFEAT-064, API-188, ERD-021, ERD-022, SCREEN-022]
→ Phase 3 라운드 2: 토폴로지 정렬 후 병렬 (ERD 페어 → API → DFEAT → UC → SCREEN)
→ Phase 3 라운드 3: SCREEN-022 → cascade[HTML 재업로드] 보류 → pending
→ Phase 5: 7 ITEM 변경 + HTML 보류 보고
→ Phase 6: 메모리 저장? "Y" → session_33_seq_020_redesign.md 자동 생성
```

## 진입 멘트 (메인이 사용자에게 첫 응답)

"mc-logi-update 시작합니다.

대상: `<ITEM-ID>` / 의도: `<요약>`
모드: batch (자동 진행) / MAX_DEPTH: 3

진행할까요?"

사용자 OK 시 Phase 2~5 진행. 종료 후 메모리 저장 문의.
