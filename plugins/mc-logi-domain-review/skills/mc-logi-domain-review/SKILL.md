---
name: mc-logi-domain-review
description: Logicraft 도메인을 7 차원(coverage/links/schema/stale/policy/acceptance/requirement) 병렬 감사해 갭을 검출하는 read-only 스킬. 사용자가 도메인 검토를 요청하면(예 "D002 검토해줘", "DOMAIN-001 갭 찾아줘", "도메인 정합 확인", "D001 인수기준 검토", "요구사항 RFP 정합 확인") logi-domain-auditor 에이전트 7건을 병렬 실행해 갭 리포트를 우선순위(P0/P1/P2)별로 생성. requirement 차원은 RFP(원천)↔REQ↔도메인(현재) 정합·stale·추적성 검토. ITEM 수정 안 함 — 검출만. 후속 수정은 사용자가 mc-logi-update 별도 호출.
license: MIT
allowed-tools: Read, Write, Edit, Grep, Glob, Bash, Agent, ToolSearch, AskUserQuestion, TaskCreate, TaskUpdate, TaskList
metadata:
  version: "1.1.1"
  domain: logicraft-orchestration
  triggers: 도메인 검토, 도메인 감사, 갭 검출, 도메인 정합, ITEM 갭, 도메인 review, gap analysis, D001 검토, D002 검토, DOMAIN-XXX 검토, 도메인 audit
  role: orchestrator-readonly
  scope: logicraft-domain-audit
  output-format: 갭 리포트 (Markdown 표 + YAML 원본)
  related-skills: mc-logi-update, skill-creator
---

# mc-logi-domain-review — Logicraft Domain Auditor

Logicraft 도메인을 7 차원 병렬 감사해 갭을 검출. **read-only** — ITEM 수정은 mc-logi-update 별도 호출.

## When to Use

- 사용자가 도메인 검토 요청 (예: "D002 검토해줘", "DOMAIN-001 갭 찾아줘")
- 도메인 작업 완료 후 정합성 확인
- 다른 도메인 cascade 후 영향 확인
- 신규 ITEM 다수 추가 후 무결성 검증
- 정기 도메인 audit (cron + /loop 활용 가능)

## When NOT to Use

- ITEM 수정 (mc-logi-update)
- 단일 ITEM 조회 (logicraft MCP 직접)
- 코드 리뷰 (mc-code-reviewer)
- 코드 중복 검출 (mc-code-hunter)

## 핵심 원칙 (사용자 결정 반영)

1. ✅ **7 dimension 분리**: coverage / links / schema / stale / policy / acceptance / requirement
2. ✅ **검출만, 자동 수정 없음**: 수정은 mc-logi-update 사용자 별도 호출
3. ✅ **legacy grep 기본 OFF**: 1차 소스 검증은 옵션 (D001~D008에서만 활성화 권장)
4. ✅ **정책 추출 = 메모리 + ADR**: Phase 2에서 자동 추출
5. ✅ **메모리 저장은 종료 시 사용자 문의**

## 워크플로우

### Phase 1 — 진입
1. 사용자 입력 파싱:
   - 도메인 ID 명시 (예 `D002`, `DOMAIN-002`)
   - 도메인명 명시 (예 `영상·메타 수집`) → list_items로 매핑
   - 없으면 `AskUserQuestion`으로 확정
2. 옵션 확인:
   - 검토 차원 (기본 7 차원 전체 / 부분 선택 — 예 "AC만"·"인수기준만" → acceptance 단독, "요구사항만"·"RFP 정합" → requirement 단독)
   - legacy grep (기본 OFF)
3. project_id 식별 (~/.claude/projects/*/memory/MEMORY.md)

### Phase 2 — 데이터·정책 수집 (메인 1회 실행)

**도메인 ITEM 카탈로그**

⚠️ **알려진 한계**: `list_items`는 `domain_id` 필터 미지원 (system_feedback 등록됨). 우회 방법:

```python
# 도메인 description
get_item(DOMAIN-XXX)

# 도메인 직접 link (get_neighbors로 belongs_to_domain 역방향)
get_neighbors(DOMAIN-XXX)
# → backward 배열에 모든 도메인 소속 ITEM ID 포함 (DFEAT/API/UC/SCREEN/SEQ/ERD/NAV 등)

# 타입별 전체 ITEM 목록 (수동 도메인 필터 필요)
list_items(type=domain_feature, limit=200)   # 전체 fetch
list_items(type=api_endpoint, limit=200)     # 30K+ 토큰 시 persisted-output 분할
# ... 메인이 description 본문/get_neighbors 결과로 도메인 ID 필터링

list_items(type=domain_feature, include_retired=true)   # deprecated ITEM 식별
```

**우선 전략**:
1. `get_neighbors(DOMAIN-XXX)` 로 도메인 소속 ITEM ID 목록 수집 (1차)
2. 부족한 타입은 `list_items(type=X)` + 수동 필터 (2차)
3. 큰 응답(30K+)은 Bash + Python json.load(encoding='utf-8')로 파싱

**ADR 정책 자동 추출**
```python
# 메모리 grep
Grep("ADR-\\d+|1차 그대로|BFF|8대 이벤트|data scope|x-access-token", path="~/.claude/projects/.../memory/")

# ADR 본문 fetch (전역)
list_items(type=adr, limit=100)
# 각 ADR.decision.chosen_option + decision.justification 수집
```

→ `adr_policies` 객체 구성:
```yaml
adr_policies:
  ADR-027: "x-access-token 헤더 통일"
  ADR-028: "LOCAL_USER 본인 지자체 한정"
  ADR-036: "관제지원 inbound HTTPS / outbound HTTP"
  ADR-038: "1차 룰셋 그대로 + EV08000101 이그노어 + outbound push"
  ADR-041: "1차 KLID 그대로 운영"
  ADR-045: "BFF 회피 — D002 단일 controller"
  ADR-051: "2차 8대 이벤트 한정 — 쓰러짐·폭력·화재·교통사고·유괴·침수·산불·산사태"
  # ... (메인이 동적 추출)
```

**RFP 원천 수집 (requirement 차원용 — Phase 2 에서 1회)**
```python
list_items(type=rfp_item, limit=100)   # RFP-001~018 (=SFR-01~18) title·workstream·keyword
# → requirement auditor 입력에 rfp_catalog 로 전달. REQ↔RFP 매핑이 명시(derived_from_rfp) 없으면
#   auditor 가 title/workstream 으로 추정 (예 학습데이터 REQ ↔ RFP-013/015/016/017)
```
→ `rfp_catalog`(RFP id·title·workstream 목록)을 requirement auditor prompt 에 adr_policies 와 함께 첨부.

### Phase 3 — 7 dimension 병렬 감사

> ⚠️ 7 auditor 동시 실행 시 일시적 서버 rate limit 가능 — 그 경우 **3+4 배치**(예 coverage/links/schema → stale/policy/acceptance/requirement)로 나눠 재실행하면 안정적. (Session 68 D004 실측)

**한 메시지에 7 Agent calls**:
```python
# 모두 한 메시지에 (병렬 실행)
Agent(subagent_type="logi-domain-auditor", description="Audit D002 coverage", prompt=...)
Agent(subagent_type="logi-domain-auditor", description="Audit D002 links", prompt=...)
Agent(subagent_type="logi-domain-auditor", description="Audit D002 schema", prompt=...)
Agent(subagent_type="logi-domain-auditor", description="Audit D002 stale", prompt=...)
Agent(subagent_type="logi-domain-auditor", description="Audit D002 policy", prompt=...)
Agent(subagent_type="logi-domain-auditor", description="Audit D002 acceptance", prompt=...)
Agent(subagent_type="logi-domain-auditor", description="Audit D002 requirement", prompt=...)
```

> `acceptance` 차원 = AC(인수기준)가 도메인의 UC/DFEAT/REQ 를 빠짐없이·올바르게 검증하는지 + AC 본문의 현행성(폐기·구 모델 검증 여부) 검토. dimensions/acceptance.md 룰 적용. 사용자가 "인수기준만"·"AC 검토"를 요청하면 이 차원 단독 실행도 가능.
>
> `requirement` 차원 = 요구사항(REQ)이 상위 진실원천 **RFP(rfp_item)** 와 하위 현재설계(도메인)의 사이에서 **최신·정합·추적가능**한지 검토 (도메인 기준 반복 수정으로 REQ 가 가장 stale 해지는 역전 구조 포착). RFP↔REQ 미연결(derived_from_rfp 부재)·REQ 가 폐기 모델 서술(도메인보다 stale)·RFP divergence 미명시·RFP 핵심요구 미하향·**RFP 비책임 부분 미명시(RQ-006 advisory — "이 부분은 우리 영역 아닌 것으로 보임")**. dimensions/requirement.md 룰. 정책: RFP 원천=rfp_item, 충돌 시 도메인 우선+RFP 배경. 사용자가 "요구사항만"·"RFP 정합"을 요청하면 단독 실행 가능. **★ requirement auditor 입력에는 후보 rfp_item(RFP-NNN) 목록도 adr_policies 와 함께 제공**(메인이 Phase 2 에서 list_items(type=rfp_item) 1회 수집). **★ 검증 모드 3단계(가용 입력별 자동)**: REQ 0건→차원 SKIP / REQ+RFP없음→domain↔REQ 대조만(RQ-002/005) / REQ+RFP+도메인→전체(RQ-001~006). dimensions/requirement.md "검증 모드" 참조.

#### ★ Agent 등록 timing fallback (중요)
`logi-domain-auditor` agent는 정의된 세션에서는 호출 불가 (Claude Code 한계).
다음 두 케이스 자동 처리:

**Case 1**: agent 호출 성공 → 정상 진행

**Case 2**: `Agent type 'logi-domain-auditor' not found` 에러 → **자동 fallback**:
```python
# general-purpose agent로 전환 + agent 정의 파일을 prompt에 인라인
Agent(
  subagent_type="general-purpose",
  description="Audit D002 <dim> (fallback)",
  prompt=f"""당신은 logi-domain-auditor 역할입니다. 먼저 아래 파일들을 Read로 정독하고 system prompt를 그대로 따르세요:

1. C:\\Users\\lumie\\.claude\\agents\\logi-domain-auditor.md (시스템 프롬프트)
2. C:\\Users\\lumie\\.claude\\skills\\mc-logi-domain-review\\dimensions\\<dim>.md (이번 차원 룰)
3. C:\\Users\\lumie\\.claude\\skills\\mc-logi-domain-review\\checklist.md (공통 hard rules)

# 입력
{입력 yaml}

# 출력
agent 파일의 STEP F YAML 한 블록만 출력하고 종료. 자유 텍스트 금지.
"""
)
```

검증 완료 (Session 33 D002/D003 audit) — fallback 결과 동일.

각 prompt에 포함:
- 입력 yaml (domain_id, dimension, item_catalog, domain_context, adr_policies, legacy_grep_enabled)
- 해당 dimension의 `dimensions/<name>.md` 본문
- 공통 `checklist.md` 본문

7 auditor 모두 완료 대기.

### Phase 4 — 결과 합산

1. **YAML 파싱**: 7 auditor 출력 YAML 모두 파싱 (실패 시 1회 재시도)
2. **중복 gap 병합**:
   - `affected_items` + 유사 reason으로 중복 식별
   - cross_dimension_hint 매칭 항목 통합
3. **우선순위 정렬**: P0 → P1 → P2
4. **mc-logi-update 후보 분류**:
   - auto_fixable=true → "자동 수정 후보"
   - auto_fixable=false → "사용자 결정 필요"

### Phase 5 — 갭 리포트 출력

**Markdown 표 (사용자 노출)**:
```markdown
# DOMAIN-002 영상·메타 수집 감사 결과

## 요약
- 감사 ITEM: 72건 (DFEAT 6 + API 35 + UC 7 + SEQ 14 + SCREEN 6 + ERD 2 + ...)
- 검출 gap: 18건 (P0: 3 / P1: 9 / P2: 6)
- auto_fixable: 11건 / 사용자 결정 필요: 7건

## P0 (즉시 수정 필요)
| gap | dimension | affected | reason | fix |
|---|---|---|---|---|
| D002-LINK-001 | links | DFEAT-064 | API-273 implemented_by_endpoints 누락 | implemented_by_endpoints에 API-273 추가 |
| D002-POL-002 | policy | API-188 | tags에 'bff' 잔재 (ADR-045 위반) | tags에서 'bff' 제거 |
| D002-STL-003 | stale | SCREEN-022 | deprecated API-191 sections 인용 | sections에서 API-191 제거 |

## P1 (정합성 손상)
...

## P2 (개선 권장)
...

## mc-logi-update 자동 수정 가능 (11건)
- D002-LINK-001: DFEAT-064 implemented_by_endpoints에 API-273 추가
- D002-POL-002: API-188 tags 'bff' 제거
- ... (전체 목록)

→ 별도로 `/mc-logi-update` 호출하시면 위 목록을 입력으로 사용 가능

## 사용자 결정 필요 (7건)
- D002-COV-005: API-XXX·API-YYY·API-ZZZ orphan (DFEAT 매핑 부재) — 각 API의 책임 DFEAT 결정 필요
- D002-SCH-001: DFEAT-064 ls_data_raw 테이블이 ERD에 없음 — ERD 추가 결정 필요
- ...
```

### Phase 6 — 자동 메모리 저장 (사용자 결정 #5 — 자동, 묻지 않음)

**자동 진행** — 사용자 확인 묻지 않음. Phase 5 보고 후 즉시 저장.

1. **타임스탬프 수집**: `Bash date +%Y%m%d_%H%M` 실행 (실제 현재 시각, 임의 생성 금지)
2. **파일명 자동 생성**: `session_{NN}_d{NNN}_audit_{YYYYMMDD}_{HHMM}.md`
   - 예: `session_33_d002_audit_20260514_1248.md`
   - session 번호: MEMORY.md 최근 entry에서 자동 추출
3. **메모리 파일 작성**: ~/.claude/projects/<project>/memory/<filename>.md
4. **MEMORY.md 인덱스 자동 추가**: 최상단 (가장 최근 작업)
   - 형식: `- **★★★★ [Session NN D<NNN> 도메인 감사 (mc-logi-domain-review, YYYY-MM-DD HH:MM)](filename)** — 6 차원 ... P0/P1/P2/P3 ... 핵심 ...`

저장 완료 후 사용자에게 파일명만 보고. 별도 확인 묻지 않음.

**예외**: 사용자가 명시적으로 "메모리 저장하지 마"라고 했을 때만 skip.

## Auditor 호출 패턴

```python
Agent(
  subagent_type="logi-domain-auditor",
  description=f"Audit {domain_id} {dimension}",
  prompt=f"""
당신은 logi-domain-auditor입니다. 다음 도메인의 {dimension} 차원을 감사하세요.

# 입력
project_id: {project_id}
domain_id: {domain_id}
dimension: {dimension}
legacy_grep_enabled: {legacy_grep_enabled}

# item_catalog
{item_catalog_yaml}

# domain_context
{domain_description}

# adr_policies
{adr_policies_yaml}

# Dimension 룰 (dimensions/{dimension}.md)
{dimension_rules_content}

# 공통 체크리스트
{checklist_content}

# 출력
STEP A~F 완료 후 YAML 한 블록만 출력하고 종료.
""",
)
```

## 병렬 실행 정책

- 7 dimension은 한 메시지에 동시 호출 (resource 충분, rate limit 시 3+4 배치)
- 같은 도메인 단일 audit: 7 auditor 병렬
- 여러 도메인 동시 audit: 도메인별 순차 권장 (7×N auditor 동시 = rate limit 위험)
- 상한 초과·rate limit 시 배치 분할

## 갭 우선순위 매김 (Phase 4)

| Severity | 조건 |
|---|---|
| P0 | 시스템 동작 불가 / link 깨짐 / schema 불일치 / ADR 정책 위반 / deprecated 활성 참조 / AC 가 폐기·deprecated 모델 검증 (ACC-004/005) / must REQ 가 폐기 모델 서술 (RQ-002 must) |
| P1 | stale / coverage 갭 / link 단방향 / brownfield 메타 누락 / required_roles 비어있음 / 활성 UC·DFEAT 검증 AC 부재 (ACC-001/002) / AC scenario 현행 불일치 (ACC-006) / 완전 고립 AC·UC forward 등록 누락 (ACC-007) / REQ 가 도메인보다 stale (RQ-002) / REQ↔RFP 미연결 (RQ-001) / RFP divergence 미명시 (RQ-003) |
| P2 | description 부족 / prominent 필드 비어있음 / 정보 풍부화 권장 / AC scenario 부재 (ACC-008) / negative AC 부재 / AC→UC 역방향 link 비대칭 (ACC-007, derived_from_use_cases 빔→파생 UC/도메인 빈칸) / RFP 핵심요구 도메인 REQ 미하향 (RQ-004) / REQ acceptance_criteria 빈약 (RQ-005) / RFP 비책임 부분 미명시 advisory (RQ-006) |

## TaskList 관리

- audit 진입 시 `TaskCreate` × 7 (dimension별)
- 각 auditor 시작 시 in_progress
- 완료 시 completed
- Phase 4~5 종료 시 cleanup

## 에러 처리

| 에러 | 대응 |
|---|---|
| auditor YAML 파싱 실패 | 1회 재시도 → 실패 시 해당 dimension skip + 보고 |
| list_items 응답 큼 (>30KB) | persisted-output 파일에서 Bash python 파싱 |
| ADR 정책 추출 0건 | 메모리 / ADR 모두 비어있음 경고, 정책 차원 skip |
| 도메인 ID 잘못됨 | AskUserQuestion으로 재확인 |
| MCP 도구 다운 | ToolSearch 재시도 → 실패 시 작업 중단 + 부분 보고 |

## mc-logi-update와의 분리

본 스킬은 **read-only**. 수정은 절대 수행 안 함.

검출된 갭은:
1. Markdown 표 + YAML 원본으로 사용자에게 보고
2. auto_fixable=true 항목은 별도 섹션으로 분리 + mc-logi-update 입력 포맷 미리 변환
3. 사용자가 별도로 `/mc-logi-update` 호출 시 위 입력 그대로 사용

(메인이 직접 mc-logi-update 호출 안 함 — 결정사항 #2 (a) 반영)

## 호출 예시

### 예시 1: D002 전체 감사
```
사용자: "D002 검토해줘"
→ Phase 1: domain_id=DOMAIN-002, 5 dim, legacy_grep=OFF
→ Phase 2: list_items × 7 types + ADR 추출
→ Phase 3: 6 auditor 병렬 (한 메시지)
→ Phase 4: 18 gaps 합산, P0:3 / P1:9 / P2:6
→ Phase 5: Markdown 표 + mc-logi-update 후보 11건 분리 보고
→ Phase 6: 메모리 저장 Y → session_XX_d002_audit.md
```

### 예시 2: D001 policy 차원만
```
사용자: "D001 정책 위반만 확인해줘"
→ Phase 1: dimension=policy 단일
→ Phase 3: auditor 1건만 호출
→ Phase 5: policy 갭 리포트만
```

### 예시 2b: D001 인수기준(AC) 차원만
```
사용자: "D001 인수기준 검토해줘" / "D001 AC 빠진 거 찾아줘"
→ Phase 1: dimension=acceptance 단일
→ Phase 3: auditor 1건만 호출 (acceptance)
→ Phase 5: AC 커버리지 누락(ACC-001/002) + stale AC(ACC-004/005/006) 갭 리포트
```

### 예시 3: 여러 도메인 동시
```
사용자: "D001, D002 갭 검출"
→ Phase 1: 2 도메인 × 6 dim = 12 auditor
→ Phase 3: 10 병렬 호출
→ Phase 5: 도메인별 섹션 분리 리포트
```

## 진입 멘트

"mc-logi-domain-review 시작합니다.

대상: `<DOMAIN-ID>` / 차원: `<5 dim 또는 선택>`
모드: read-only (수정 없음, 검출만)
legacy grep: `<ON/OFF>`

데이터 수집 후 6 auditor 병렬 실행합니다. 계속할까요?"
