---
name: mc-logi-domain-review
description: Logicraft 도메인을 10 차원(coverage/links/schema/stale/policy/acceptance/requirement/content/diagram/test_scenario) 병렬 감사해 갑을 검출하는 read-only 스킬. 사용자가 도메인 검토를 요청하면(예 "D002 검토해줘", "DOMAIN-001 갑 찾아줘", "도메인 정합 확인", "D001 인수기준 검토", "요구사항 RFP 정합 확인", "설명이 제목과 맞는지·장황하지 않은지 검토", "다이어그램 반영 확인", "통합/시스템 시험 시나리오 검토") logi-domain-auditor 에이전트 10건을 병렬 실행해 갑 리포트를 우선순위(P0/P1/P2)별로 생성. requirement 차원은 RFP(원천)↔REQ↔도메인(현재) 정합·stale·추적성 검토, content 차원은 제목↔본문 의미 일치·서술 명료성 검토, diagram 차원은 다이어그램(CDIAG·C4)이 활성 DFEAT 를 빠짐없이 그리는지(정형 depicts) + 본문(컴포넌트/클래스 description)이 구 모델로 표류 안 했는지(DIAG-005 stale body) 검토, test_scenario 차원은 통합/시스템 시험 시나리오(TEST)가 도메인 핵심 흐름(cross-UC)·책임 REQ/NFR 를 검증하는지(커버리지) + steps 본문 현행성(폐기·옇 흐름 검증) 검토(AC 와 짝, 통합/시스템 레벨). ITEM 수정 안 함 — 검출만. 후속 수정은 사용자가 mc-logi-update 별도 호출.
license: MIT
allowed-tools: Read, Write, Edit, Grep, Glob, Bash, Agent, ToolSearch, AskUserQuestion, TaskCreate, TaskUpdate, TaskList
metadata:
  version: "1.3.2"
  domain: logicraft-orchestration
  triggers: 도메인 검토, 도메인 감사, 갑 검출, 도메인 정합, ITEM 갑, 도메인 review, gap analysis, D001 검토, D002 검토, DOMAIN-XXX 검토, 도메인 audit
  role: orchestrator-readonly
  scope: logicraft-domain-audit
  output-format: 갑 리포트 (Markdown 표 + YAML 원본)
  related-skills: mc-logi-update, skill-creator
---

# mc-logi-domain-review — Logicraft Domain Auditor

Logicraft 도메인을 10 차원 병렬 감사해 갑을 검출. **read-only** — ITEM 수정은 mc-logi-update 별도 호출.

> 10 차원 = coverage · links · schema · stale · policy · acceptance · requirement · **content**(제목↔본문 의미 일치·서술 명료성·장황함·핵심 매몰 — Session 121 신설) · **diagram**(다이어그램 CDIAG·C4 가 활성 DFEAT 를 정형 depicts 로 빠짐없이 그리는지 + 본문이 구 모델로 표류 안 했는지 DIAG-005 stale body — system-feedback 05bcc047 신설, DIAG-005 는 D002 CMP-002 실증으로 보강) · **test_scenario**(통합/시스템 시험 시나리오 TEST 가 도메인 핵심 흐름 cross-UC·책임 REQ/NFR 를 검증하는지 커버리지 + steps 본문 현행성 — AC 와 짝, 통합/시스템 레벨).

## When to Use

- 사용자가 도메인 검토 요청 (예: "D002 검토해줘", "DOMAIN-001 갑 찾아줘")
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

1. ✅ **10 dimension 분리**: coverage / links / schema / stale / policy / acceptance / requirement / content / diagram / test_scenario
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
   - 검토 차원 (기본 10 차원 전체 / 부분 선택 — 예 "AC만"·"인수기준만" → acceptance 단독, "요구사항만"·"RFP 정합" → requirement 단독, "설명이 제목과 맞는지"·"장황한지"·"내용 검토" → content 단독, "다이어그램 반영"·"클래스다이어그램 정합"·"C4 반영" → diagram 단독, "통합시험"·"시스템시험"·"시험 시나리오 검토"·"TEST 정합" → test_scenario 단독)
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
  ADR-051: "2차 8대 이벤트 한정 — 쓰러짐·폭력·화재·교통사고·유구·침수·산불·산사태"
  # ... (메인이 동적 추출)
```

**RFP 원천 수집 (requirement 차원용 — Phase 2 에서 1회)**
```python
list_items(type=rfp_item, limit=100)   # RFP-001~018 (=SFR-01~18) title·workstream·keyword
# → requirement auditor 입력에 rfp_catalog 로 전달. REQ↔RFP 매핑이 명시(derived_from_rfp) 없으면
#   auditor 가 title/workstream 으로 추정 (예 학습데이터 REQ ↔ RFP-013/015/016/017)
```
→ `rfp_catalog`(RFP id·title·workstream 목록)을 requirement auditor prompt 에 adr_policies 와 함께 첨부.

### Phase 3 — 10 dimension 병렬 감사

> ⚠️ 10 auditor 동시 실행 시 일시적 서버 rate limit 가능 — 그 경우 **5+5 배치**(예 coverage/links/schema/content/diagram → stale/policy/acceptance/requirement/test_scenario)로 나눠 재실행하면 안정적. (Session 68 D004 실측 — 당시 7 dim, content·diagram·test_scenario 추가로 5+5)

**한 메시지에 10 Agent calls**:
```python
# 모두 한 메시지에 (병렬 실행)
Agent(subagent_type="logi-domain-auditor", description="Audit D002 coverage", prompt=...)
Agent(subagent_type="logi-domain-auditor", description="Audit D002 links", prompt=...)
Agent(subagent_type="logi-domain-auditor", description="Audit D002 schema", prompt=...)
Agent(subagent_type="logi-domain-auditor", description="Audit D002 stale", prompt=...)
Agent(subagent_type="logi-domain-auditor", description="Audit D002 policy", prompt=...)
Agent(subagent_type="logi-domain-auditor", description="Audit D002 acceptance", prompt=...)
Agent(subagent_type="logi-domain-auditor", description="Audit D002 requirement", prompt=...)
Agent(subagent_type="logi-domain-auditor", description="Audit D002 content", prompt=...)
Agent(subagent_type="logi-domain-auditor", description="Audit D002 diagram", prompt=...)
Agent(subagent_type="logi-domain-auditor", description="Audit D002 test_scenario", prompt=...)
```

> `diagram` 차원 = 도메인 다이어그램(CDIAG·C4 CTX/CNT/CMP)이 활성 DFEAT 를 빠짐없이·올바르게 그리는지 (정형 depicts 기준). `list_diagram_coverage(project_id, domain_id)` MCP 도구로 미반영(missing)·폐기 참조·dangling 참조·미선언 다이어그램 검출. dimensions/diagram.md 룰. 사용자가 "다이어그램 검토"·"클래스다이어그램 정합"·"C4 반영"을 요청하면 단독 실행 가능. (system-feedback 05bcc047 — 신규 DFEAT 가 다이어그램에 자동 미반영되던 사각지대 차원화.)

> `acceptance` 차원 = AC(인수기준)가 도메인의 UC/DFEAT/REQ 를 빠짐없이·올바르게 검증하는지 + AC 본문의 현행성(폐기·구 모델 검증 여부) 검토. dimensions/acceptance.md 룰 적용. 사용자가 "인수기준만"·"AC 검토"를 요청하면 이 차원 단독 실행도 가능.
>
> `requirement` 차원 = 요구사항(REQ)이 상위 진실원천 **RFP(rfp_item)** 와 하위 현재설계(도메인)의 사이에서 **최신·정합·추적가능**한지 검토 (도메인 기준 반복 수정으로 REQ 가 가장 stale 해지는 역전 구조 포착). RFP↔REQ 미연결(derived_from_rfp 부재)·REQ 가 폐기 모델 서술(도메인보다 stale)·RFP divergence 미명시·**RFP 비책임 부분 미명시(RQ-006 advisory — "이 부분은 우리 영역 아닌 것으로 보임")**. dimensions/requirement.md 룰. 정책: RFP 원천=rfp_item, 충돌 시 도메인 우선+RFP 배경. 사용자가 "요구사항만"·"RFP 정합"을 요청하면 단독 실행 가능. **★ requirement auditor 입력에는 후보 rfp_item(RFP-NNN) 목록도 adr_policies 와 함께 제공**(메인이 Phase 2 에서 list_items(type=rfp_item) 1회 수집). **★ 검증 모드 3단계(가용 입력별 자동)**: REQ 0건→차원 SKIP / REQ+RFP없음→domain↔REQ 대조만(RQ-002/005) / REQ+RFP+도메인→전체(RQ-001~006). dimensions/requirement.md "검증 모드" 참조.

> `test_scenario` 차원 = 통합(integration, cross-UC end-to-end)·시스템(system, REQ/NFR 검증) 시험 시나리오(`test_scenario`, TEST-NNN)가 도메인 핵심 흐름·책임 REQ/NFR 를 빠짐없이 검증하는지(커버리지 TST-001/002) + `steps` 본문이 폐기 ITEM·옇 흐름/화면/API 를 검증하지 않는지(현행성 TST-003~005) + 추적성·품질(TST-006/007) 검토. **AC(acceptance)와 짝** — AC=단위/인수기준, TEST=통합/시스템 레벨. dimensions/test_scenario.md 룰. ★ TEST 는 **project-level·cross-domain**(`related_domains[]`) — `list_items(type=test_scenario)` 후 related_domains/covers_use_cases/verifies_* ∩ 도메인으로 귀속 식별. 도메인이 아직 시험 시나리오 산출물 단계 전이면 SKIP+안내 1건(과잉 금지). 사용자가 "통합시험"·"시스템시험"·"시험 시나리오 검토"·"TEST 정합"을 요청하면 단독 실행 가능.

#### ★ Agent 이름 해석 + 등록 fallback (중요)

`logi-domain-auditor` 에이전트는 **설치 방식에 따라 등록 이름이 다르다**:
- **플러그인 설치** (`/plugin install mc-logi-domain-review@logicraft`): 에이전트가 `agents/logi-domain-auditor.md` 로 동봉되어 **scoped name `mc-logi-domain-review:logi-domain-auditor`** 로 자동 등록 (fresh 세션에서 즉시 사용 가능 — "not found" 없음)
- **user/project scope** (개발 환경, `~/.claude/agents/`): bare name `logi-domain-auditor`

따라서 다음 순서로 시도 (절대경로 하드코딩 금지 — 설치 위치 무관):

**Case 1 — 전용 에이전트 호출** (첫 성공 채택):
1. `subagent_type="mc-logi-domain-review:logi-domain-auditor"` (플러그인 scope, 배포 환경 기본)
2. 실패 시 `subagent_type="logi-domain-auditor"` (user/project scope, 개발 환경)

**Case 2 — 둘 다 `Agent type ... not found`** → general-purpose 로 fallback + 에이전트 정의를 **동적 탐색**해 인라인:
```python
# 1) 에이전트 정의 파일을 Glob 으로 탐색 (설치 위치 무관, 절대경로 박지 말 것)
#    Glob("**/agents/logi-domain-auditor.md") → 첫 결과를 Read → agent_md_content
# 2) dimension 룰·checklist 는 메인이 이미 읽어둔 내용(dimension_rules_content,
#    checklist_content; 스킬 디렉터리 상대 — dimensions/<dim>.md, checklist.md)을 그대로 인라인
Agent(
  subagent_type="general-purpose",
  description="Audit D002 <dim> (fallback)",
  prompt=f"""당신은 logi-domain-auditor 역할입니다. 아래 system prompt 를 그대로 따르세요:

# logi-domain-auditor 시스템 프롬프트
{agent_md_content}

# 이번 차원 룰 (dimensions/<dim>.md)
{dimension_rules_content}

# 공통 체크리스트 (checklist.md)
{checklist_content}

# 입력
{입력 yaml}

# 출력
STEP F YAML 한 블록만 출력하고 종료. 자유 텍스트 금지.
"""
)
```

검증 완료 (Session 33 D002/D003 audit). 플러그인 배포 시 Case 1-1(plugin scope)으로 정상 동작, Case 2 는 안전망.

각 prompt에 포함:
- 입력 yaml (domain_id, dimension, item_catalog, domain_context, adr_policies, legacy_grep_enabled)
- 해당 dimension의 `dimensions/<name>.md` 본문
- 공통 `checklist.md` 본문

10 auditor 모두 완료 대기.

> `content` 차원 = ITEM 본문(description·goal·user_story)이 **제목·구조 필드가 말하는 그 ITEM 을 정확·명료하게** 서술하는지 검토. 제목↔본문 의미 불일치(CNT-001)·형제 ITEM rotation 오염(CNT-002, D006 DFEAT-025/073/074 실증)·과잉 장황(CNT-003)·핵심 매몰(CNT-004)·변경이력 본문 혼입(CNT-005)·중복/빈약(CNT-006/007). 구조(링크·필드)는 멀줦한데 자연어 본문이 틀리거나 장황한 **다른 차원들의 사각지대**를 잡는다. dimensions/content.md 룰. 사용자가 "설명이 제목과 맞는지"·"장황하지 않은지"·"내용 검토"를 요청하면 단독 실행 가능. **read-only — 명료화 초안만 제시, 실제 재작성은 mc-logi-update.**

### Phase 4 — 결과 합산

1. **YAML 파싱**: 10 auditor 출력 YAML 모두 파싱 (실패 시 1회 재시도)
2. **중복 gap 병합**:
   - `affected_items` + 유사 reason으로 중복 식별
   - cross_dimension_hint 매칭 항목 통합
3. **우선순위 정렬**: P0 → P1 → P2
4. **mc-logi-update 후보 분류**:
   - auto_fixable=true → "자동 수정 후보"
   - auto_fixable=false → "사용자 결정 필요"

### Phase 5 — 갑 리포트 출력

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
   - 형식: `- **★★★★ [Session NN D<NNN> 도메인 감사 (mc-logi-domain-review, YYYY-MM-DD HH:MM)](filename)** — 10 차원 ... P0/P1/P2 ... 핵심 ...`

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

- 8 dimension은 한 메시지에 동시 호출 (resource 충분, rate limit 시 4+4 배치)
- 같은 도메인 단일 audit: 10 auditor 병렬
- 여러 도메인 동시 audit: 도메인별 순차 권장 (8×N auditor 동시 = rate limit 위험)
- 상한 초과·rate limit 시 배치 분할

## 갑 우선순위 매김 (Phase 4)

| Severity | 조건 |
|---|---|
| P0 | 시스템 동작 불가 / link 깨짐 / schema 불일치 / ADR 정책 위반 / deprecated 활성 참조 / AC 가 폐기·deprecated 모델 검증 (ACC-004/005) / must REQ 가 폐기 모델 서술 (RQ-002 must) / **제목↔본문 다른 기능 서술 (CNT-001) / 형제 ITEM rotation 오염 (CNT-002)** |
| P1 | stale / coverage 갑 / link 단방향 / brownfield 메타 누락 / required_roles 비어있음 / 활성 UC·DFEAT 검증 AC 부재 (ACC-001/002) / AC scenario 현행 불일치 (ACC-006) / 완전 고립 AC·UC forward 등록 누락 (ACC-007) / REQ 가 도메인보다 stale (RQ-002) / REQ↔RFP 미연결 (RQ-001) / RFP divergence 미명시 (RQ-003) / **본문 과잉 장황 (CNT-003) / 핵심 매몰 (CNT-004) / 변경이력 본문 혼입 (CNT-005)** |
| P2 | description 부족 / prominent 필드 비어있음 / 정보 풍부화 권장 / AC scenario 부재 (ACC-008) / negative AC 부재 / AC→UC 역방향 link 비대칭 (ACC-007, derived_from_use_cases 비→파생 UC/도메인 빈칸) / RFP 핵심요구 도메인 REQ 미하향 (RQ-004) / REQ acceptance_criteria 빈약 (RQ-005) / RFP 비책임 부분 미명시 advisory (RQ-006) / **본문 중복 서술 (CNT-006) / 빈약·일반론 (CNT-007)** |

## TaskList 관리

- audit 진입 시 `TaskCreate` × 8 (dimension별)
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

검출된 갑은:
1. Markdown 표 + YAML 원본으로 사용자에게 보고
2. auto_fixable=true 항목은 별도 섹션으로 분리 + mc-logi-update 입력 포맷 미리 변환
3. 사용자가 별도로 `/mc-logi-update` 호출 시 위 입력 그대로 사용

(메인이 직접 mc-logi-update 호출 안 함 — 결정사항 #2 (a) 반영)

## 호출 예시

### 예시 1: D002 전체 감사
```
사용자: "D002 검토해줘"
→ Phase 1: domain_id=DOMAIN-002, 8 dim, legacy_grep=OFF
→ Phase 2: list_items × 7 types + ADR 추출
→ Phase 3: 10 auditor 병렬 (한 메시지)
→ Phase 4: 18 gaps 합산, P0:3 / P1:9 / P2:6
→ Phase 5: Markdown 표 + mc-logi-update 후보 11건 분리 보고
→ Phase 6: 메모리 저장 Y → session_XX_d002_audit.md
```

### 예시 2: D001 policy 차원만
```
사용자: "D001 정책 위반만 확인해줘"
→ Phase 1: dimension=policy 단일
→ Phase 3: auditor 1건만 호출
→ Phase 5: policy 갑 리포트만
```

### 예시 2b: D001 인수기준(AC) 차원만
```
사용자: "D001 인수기준 검토해줘" / "D001 AC 빠진 거 찾아줘"
→ Phase 1: dimension=acceptance 단일
→ Phase 3: auditor 1건만 호출 (acceptance)
→ Phase 5: AC 커버리지 누락(ACC-001/002) + stale AC(ACC-004/005/006) 갑 리포트
```

### 예시 3: 여러 도메인 동시
```
사용자: "D001, D002 갑 검출"
→ Phase 1: 2 도메인 × 8 dim = 16 auditor
→ Phase 3: 도메인별 8 병렬 (도메인 간 순차)
→ Phase 5: 도메인별 섹션 분리 리포트
```

## 진입 멘트

"mc-logi-domain-review 시작합니다.

대상: `<DOMAIN-ID>` / 차원: `<8 dim 또는 선택>`
모드: read-only (수정 없음, 검출만)
legacy grep: `<ON/OFF>`

데이터 수집 후 10 auditor 병렬 실행합니다. 계속할까요?"
