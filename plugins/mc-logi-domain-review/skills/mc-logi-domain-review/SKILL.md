---
name: mc-logi-domain-review
description: Logicraft 도메인을 10 차원(coverage/links/schema/stale/policy/acceptance/requirement/content/diagram/test_scenario) 병렬 감사해 갑을 검출하는 read-only 스킬. 사용자가 도메인 검토를 요청하면(예 "D002 검토해줘", "DOMAIN-001 갑 찾아줘", "도메인 정합 확인", "D001 인수기준 검토", "요구사항 RFP 정합 확인", "설명이 제목과 맞는지·장황하지 않은지 검토", "다이어그램 반영 확인", "통합/시스템 시험 시나리오 검토") logi-domain-auditor 에이전트 10건을 병렬 실행해 갑 리포트를 우선순위(P0/P1/P2)별로 생성. requirement 차원은 RFP(원천)↔REQ↔도메인(현재) 정합·stale·추적성 검토, content 차원은 제목↔본문 의미 일치·서술 명료성 검토, diagram 차원은 다이어그램(CDIAG·C4)이 활성 DFEAT 를 빠짐없이 그리는지(정형 depicts) + 본문(컴포넌트/클래스 description)이 구 모델로 표류 안 했는지(DIAG-005 stale body) 검토, test_scenario 차원은 통합/시스템 시험 시나리오(TEST)가 도메인 핵심 흐름(cross-UC)·책임 REQ/NFR 를 검증하는지(커버리지) + steps 본문 현행성(폐기·옇 흐름 검증) 검토(AC 와 짝, 통합/시스템 레벨). ITEM 수정 안 함 — 검출만. 후속 수정은 사용자가 mc-logi-update 별도 호출.
license: MIT
allowed-tools: Read, Write, Edit, Grep, Glob, Bash, Agent, ToolSearch, AskUserQuestion, TaskCreate, TaskUpdate, TaskList
metadata:
  version: "1.3.1"
  domain: logicraft-orchestration
  triggers: 도메인 검토, 도메인 감사, 갑 검출, 도메인 정합, ITEM 갑, 도메인 review, gap analysis, D001 검토, D002 검토, DOMAIN-XXX 검토, 도메인 audit
  role: orchestrator-readonly
  scope: logicraft-domain-audit
  output-format: 갑 리포트 (Markdown 표 + YAML 원본)
  related-skills: mc-logi-update, skill-creator
---

# mc-logi-domain-review — Logicraft Domain Auditor

Logicraft 도메인을 10 차원 병렬 감사해 갑을 검출. **read-only** — ITEM 수정은 mc-logi-update 별도 호출.

> 10 차원 = coverage · links · schema · stale · policy · acceptance · requirement · **content** · **diagram** · **test_scenario**. 상세 룰은 각 dimensions/<name>.md 본문. content=제목↔본문 의미 일치·명료성(Session 121 신설), diagram=CDIAG·C4 가 활성 DFEAT 를 정형 depicts 로 그리는지 + 본문 stale body DIAG-005(D002 CMP-002 실증), test_scenario=통합/시스템 시험 TEST 의 커버리지+현행성(AC 와 짝).

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
get_item(DOMAIN-XXX)
get_neighbors(DOMAIN-XXX)   # backward 배열에 도메인 소속 ITEM ID 포함
list_items(type=domain_feature, limit=200)
list_items(type=api_endpoint, limit=200)
list_items(type=domain_feature, include_retired=true)   # deprecated ITEM 식별
```

**우선 전략**: get_neighbors(1차) → 부족 타입 list_items+수동필터(2차) → 큰 응답은 Bash python json.load.

**ADR 정책 자동 추출**: 메모리 grep + list_items(type=adr) → `adr_policies` 객체 구성 (ADR-027 x-access-token, ADR-028 본인 지자체, ADR-045 BFF 회피, ADR-051 8대 이벤트 등).

**RFP 원천 수집 (requirement 차원용)**: `list_items(type=rfp_item, limit=100)` → `rfp_catalog`(RFP id·title·workstream)을 requirement auditor prompt 에 첨부.

### Phase 3 — 10 dimension 병렬 감사

> ⚠️ 10 auditor 동시 실행 시 rate limit 가능 — **5+5 배치**(coverage/links/schema/content/diagram → stale/policy/acceptance/requirement/test_scenario)로 나눠 재실행.

**한 메시지에 10 Agent calls** (subagent_type="logi-domain-auditor", 각 dimension).

> `diagram` = CDIAG·C4 CTX/CNT/CMP 가 활성 DFEAT 를 정형 depicts 로 그리는지. `list_diagram_coverage(project_id, domain_id)` MCP 로 missing·폐기참조·dangling·미선언 검출 + DIAG-005 본문 구모델. dimensions/diagram.md.

> `acceptance` = AC 가 UC/DFEAT/REQ 를 검증하는지 커버리지 + AC 본문 현행성. dimensions/acceptance.md.
>
> `requirement` = REQ 가 RFP↔도메인 사이에서 최신·정합·추적가능한지. ★ 검증 모드 3단계(REQ 0건→SKIP / REQ+RFP없음→domain↔REQ만 / 전체). ★ rfp_catalog 제공. dimensions/requirement.md.

> `test_scenario` = 통합/시스템 시험 TEST 가 핵심 흐름·책임 REQ/NFR 를 검증하는지(TST-001/002) + steps 현행성(TST-003~005). AC 와 짝. ★ project-level·cross-domain(related_domains) — list_items(type=test_scenario) 후 귀속 식별. 산출물 단계 전이면 SKIP+안내 1건. dimensions/test_scenario.md.

#### ★ Agent 이름 해석 + 등록 fallback
`logi-domain-auditor` 는 설치 방식별 이름 상이:
- 플러그인: `mc-logi-domain-review:logi-domain-auditor` (agents/ 동봉 자동등록)
- user/project: bare `logi-domain-auditor`

Case 1(전용 호출 — plugin scope 먼저, 실패 시 bare) → Case 2(둘 다 not found 면 general-purpose + Glob("**/agents/logi-domain-auditor.md") Read 해 인라인). 절대경로 하드코딩 금지.

각 prompt에 입력 yaml + dimensions/<name>.md + checklist.md 본문 포함. 10 auditor 완료 대기.

> `content` = ITEM 본문(description·goal·user_story)이 제목·구조 필드를 정확·명료하게 서술하는지. CNT-001 제목↔본문 불일치·CNT-002 rotation 오염·CNT-003 장황·CNT-004 핵심 매몰·CNT-005 이력 혼입. dimensions/content.md. read-only.

### Phase 4 — 결과 합산
1. 10 auditor YAML 파싱 (실패 1회 재시도)
2. 중복 gap 병합 (affected_items + cross_dimension_hint)
3. P0 → P1 → P2 정렬
4. mc-logi-update 후보 분류 (auto_fixable true/false)

### Phase 5 — 갑 리포트 출력
Markdown 표: 요약 + P0/P1/P2 갑 + mc-logi-update 자동수정 후보 분리 + 사용자 결정 필요 항목.

### Phase 6 — 자동 메모리 저장 (자동, 묻지 않음)
Bash date → `session_{NN}_d{NNN}_audit_{YYYYMMDD}_{HHMM}.md` 작성 + MEMORY.md 인덱스 추가. 예외: "메모리 저장하지 마".

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
- 10 dimension 한 메시지 동시 호출 (rate limit 시 5+5 배치)
- 여러 도메인 동시 audit는 도메인별 순차 권장

## 갑 우선순위 (Phase 4)

| Severity | 조건 |
|---|---|
| P0 | 시스템 동작 불가 / link 깨짐 / schema 불일치 / ADR 정책 위반 / deprecated 활성 참조 / AC 폐기·deprecated 모델 검증(ACC-004/005) / must REQ 폐기 모델(RQ-002 must) / 제목↔본문 불일치(CNT-001) / rotation 오염(CNT-002) / 다이어그램 dangling(DIAG-003) / TEST steps deprecated 인용(TST-003) |
| P1 | stale / coverage 갑 / link 단방향 / brownfield 메타 누락 / AC 부재(ACC-001/002) / REQ stale(RQ-002) / RFP 미연결(RQ-001) / 장황·핵심매몰(CNT-003/004) / 다이어그램 missing·폐기참조·본문구모델(DIAG-001/002/005) / TEST 커버리지·불일치(TST-001/002/005) |
| P2 | description 부족 / prominent 비어있음 / 정보 풍부화 / negative AC 부재(ACC-008) / RFP 미하향(RQ-004) / RQ-006 advisory / 중복·빈약(CNT-006/007) / 다이어그램 미선언(DIAG-004) |

## 에러 처리
| 에러 | 대응 |
|---|---|
| auditor YAML 파싱 실패 | 1회 재시도 → skip + 보고 |
| list_items 큼 (>30KB) | persisted-output Bash python 파싱 |
| ADR 정책 0건 | 정책 차원 skip |
| 도메인 ID 잘못 | AskUserQuestion 재확인 |
| MCP 다운 | ToolSearch 재시도 → 부분 보고 |

## mc-logi-update와의 분리
본 스킬은 read-only. 검출된 갑은 Markdown+YAML 보고, auto_fixable=true 항목은 별도 섹션으로 mc-logi-update 입력 포맷 변환. 메인이 직접 mc-logi-update 호출 안 함.

## 진입 멘트
"mc-logi-domain-review 시작합니다. 대상: <DOMAIN-ID> / 차원: <10 dim 또는 선택> / 모드: read-only. 데이터 수집 후 10 auditor 병렬 실행합니다. 계속할까요?"
