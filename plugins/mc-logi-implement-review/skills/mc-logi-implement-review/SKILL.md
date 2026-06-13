---
name: mc-logi-implement-review
description: 현재 구현된 코드가 로컬 구현 키트(docs/design/{slug}-{DOMAIN-ID}/)와 정합하는지 6차원(api/schema/policy/coverage/acceptance/role) 병렬 점검하는 read-only 스킬. 사용자가 "구현이 키트랑 맞는지 확인", "코드 정합 점검", "D004 구현 검토", "키트 대비 코드 표류 찾아줘", "구현 정합성 감사", "/mc-logi-implement-review" 를 요청하면 logi-implement-auditor 에이전트 6건을 병렬 실행해 키트(설계)·코드(실제)·IMPREC(주장) 3방향 삼각 대조로 불일치를 검출. 5종 분류(code_drift/design_stale/coverage_gap/extra_code/imprec_mismatch) 후 코드수정/설계갱신 2버킷으로 핸드오프. ITEM·코드 수정 안 함 — 검출만. 후속 수정은 mc-logi-implement(코드)/mc-logi-update(설계) 별도 호출.
license: MIT
allowed-tools: Read, Write, Edit, Grep, Glob, Bash, Agent, ToolSearch, AskUserQuestion, TaskCreate, TaskUpdate, TaskList
metadata:
  version: "1.0.0"
  domain: logicraft-orchestration
  triggers: 구현 정합, 코드 정합 점검, 키트 대비 코드, 구현 검토, 코드 표류, 구현 정합성 감사, conformance review, 키트 정합, D004 구현 검토, implement review
  role: orchestrator-readonly
  scope: code-kit-conformance
  output-format: 정합 리포트 (Markdown 표 + YAML 원본)
  related-skills: mc-logi-implement, mc-logi-implement-kit, mc-logi-update, mc-logi-domain-review
---

# mc-logi-implement-review — Code ↔ Kit Conformance Auditor

현재 구현된 코드가 로컬 구현 키트(`docs/design/{slug}-{DOMAIN-ID}/`, 설계 진실원)와 정합하는지 **6차원 병렬 감사**해 불일치를 검출. **read-only** — 코드·logicraft·키트 아무것도 수정하지 않음. 후속 수정은 코드=`mc-logi-implement` / 설계=`mc-logi-update` 별도 호출.

> 키트 패밀리(implement-kit → implement → **implement-review**)의 빈 칸인 **코드 ↔ 키트 정합 점검** 칸을 채운다. 키트(설계)·코드(실제)·logicraft IMPREC(구현 주장) 3방향 삼각 대조로 표류를 잡는다.

## 생태계 위치

키트 패밀리·리뷰 스킬 4개 중 본 스킬은 **코드 ↔ 키트 정합 점검**을 담당한다 (다른 셋이 비워둔 칸).

| 스킬 | 비교 축 | 코드 | logicraft |
|---|---|---|---|
| mc-logi-domain-review | 설계 ITEM ↔ 설계 ITEM | 안 봄 | read-only |
| mc-code-reviewer | 코드 ↔ best-practice | 봄 | 안 봄 |
| mc-logi-implement (Phase 5) | (구현 후 IMPREC **쓰기**) | 봄 | **쓰기** |
| **mc-logi-implement-review (본 스킬)** | **코드 ↔ 키트** | **봄** | **read-only** |

## When to Use

- 사용자가 구현 정합 점검 요청 (예: "D004 구현이 키트랑 맞는지 확인", "키트 대비 코드 표류 찾아줘")
- 구현(mc-logi-implement) 완료 후 코드↔키트 정합 검증
- 키트 SYNC 직후 — 설계 변경분이 코드에 반영됐는지 확인
- 현재 브랜치 diff 의 구현 부분이 키트 계약을 지키는지 집중 점검
- 정기 구현 정합 audit (cron + /loop 활용 가능)

## When NOT to Use

- 코드 수정 → `mc-logi-implement` (또는 수동)
- 설계 ITEM 수정 → `mc-logi-update`
- 코드 품질·버그·보안 리뷰 → `mc-code-reviewer`
- 설계 ITEM ↔ 설계 ITEM 정합 (코드 안 봄) → `mc-logi-domain-review`
- 키트 생성·SYNC → `mc-logi-implement-kit` (본 스킬은 권고만, 자동 SYNC 안 함)

## 핵심 원칙

1. ✅ **read-only 검출 전용** — 코드·logicraft·키트 아무것도 수정하지 않는다 (IMPREC 도 읽기만). domain-review 와 동일 철학.
2. ✅ **후속 처리는 두 갈래 핸드오프** — 검출 결과를 두 버킷으로 분류해 사용자에게 제시:
   - **코드 수정 후보** → `mc-logi-implement` (또는 수동 수정)
   - **설계 갱신 후보** → `mc-logi-update`
   메인이 직접 이 스킬들을 호출하지 않는다 (입력 포맷만 미리 변환해 제공).
3. ✅ **키트가 점검 기준** — "무엇이 옳은가"의 1차 기준은 키트(설계 진실원). 단 코드가 키트보다 앞선 경우(구현 중 확정)는 설계 stale 로 분류해 mc-logi-update 로 넘긴다 (3방향 판정, 아래 판정 모델).
4. ✅ **거짓양성 방어 의무** — 정합 매핑은 본질적으로 휴리스틱이므로 모든 finding 에 evidence + confidence 를 필수화하고 불확실 시 반증을 우선한다 (checklist.md 강제).

## 판정 모델 — 3방향 삼각 대조

```
        키트 (설계 진실원)
         /          \
   코드 (실제) ——— IMPREC (구현 주장)
```

각 불일치를 5종으로 분류한다:

| 유형 | 의미 | 버킷 |
|---|---|---|
| `code_drift` | 코드가 키트 계약을 위반 (키트가 옳음) | `code_fix` (코드 수정) |
| `design_stale` | 코드가 키트보다 앞섬 (구현 중 확정·설계 미반영) | `design_update` (설계 갱신) |
| `coverage_gap` | 키트 ITEM 에 대응 코드 없음 (미구현) | `code_fix` (코드 수정) |
| `extra_code` | 코드에 있는데 키트에 없음 | `design_update` (설계 갱신 or 의도 확인) |
| `imprec_mismatch` | IMPREC 는 구현됐다는데 코드 없음 / 버전 어긋남 | `imprec_fix` (추적 정정) |

**logicraft degrade**: logicraft 접근 불가 시 **2방향(키트 ↔ 코드)** 으로 자동 축소 — `imprec_mismatch` 차원만 SKIP 하고 나머지 4종 분류는 그대로 수행. 리포트에 degrade 사실 명시.

## 아키텍처 — 6차원 병렬 auditor

신규 에이전트 **`logi-implement-auditor`** 1종 + `dimension` 파라미터. `logi-domain-auditor` 와 달리 **키트 파일(md/json) + 실코드(grep/serena 심볼/Read) + logicraft IMPREC** 셋을 동시에 판독한다 (도구 세트가 달라 신규 에이전트 불가피). 네이밍은 `mc-logi-domain-review` ↔ `logi-domain-auditor` 와 대칭 (패밀리 규칙 `logi-{축}-auditor`).

| 차원 | 코드 측 점검 대상 | 키트 측 기준 | 주요 finding |
|---|---|---|---|
| `api` | 컨트롤러 path/method/요청·응답/envelope | API ITEM 계약 (ADR-072 envelope) | 엔드포인트 누락·경로불일치·응답형식 표류 |
| `schema` | 엔티티 + Flyway 마이그레이션 | ERD ITEM 테이블/컬럼/제약/인덱스 | 누락 컬럼·타입 불일치·CHECK/UNIQUE 누락 |
| `policy` | 코드 패턴·구조 | ADR 결정 (키트 "구현 함정" 단락) | cron 폴링 vs LISTEN/NOTIFY·단일 컨트롤러/BFF·v+1 계보 위반 |
| `coverage` | 키트 ITEM → 코드 심볼 매핑 + 역방향 표류 | 키트 ITEM 전수 ↔ IMPREC | 미구현 ITEM·키트에 없는 엔드포인트/테이블/클래스 |
| `acceptance` | JUnit 테스트 | AC Given/When/Then | AC 가 검증하는 테스트 부재·시나리오 미커버 |
| `role` | @PreAuthorize / AccessGuard / 인터셉터 | ROLE required_roles | 권한 가드 미적용·역할 불일치 (D004 AccessGuard TODO 류) |

**병렬 정책**: 한 메시지에 6 Agent 동시 호출. rate limit 시 **3+3 배치**(`api`/`schema`/`policy` → `coverage`/`acceptance`/`role`).

## Phase 흐름

```
Phase 0  진입 + 키트 게이트
Phase 1  데이터 수집 (메인 1회)
Phase 2  6차원 병렬 auditor
Phase 3  합산 + 5종 분류 + 우선순위
Phase 4  정합 리포트 출력
Phase 5  메모리 저장 문의
```

### Phase 0 — 진입 + 키트 게이트

1. **대상·범위 확정**: 도메인 ID(D004/DOMAIN-004)·프로젝트를 인자/대화/메모리에서 확정. 불명확하면 `AskUserQuestion`.
2. **범위 단위 결정** (둘 다 지원):
   - **기본**: 도메인 키트 전체 정합 스캔.
   - **타겟**: 인자로 특정 ITEM 목록 · 현재 브랜치 diff(`git diff`) · 구현 영역 지정 시 그 부분만 집중.
3. **키트 신선도 게이트 (권고만 — 자동 SYNC 안 함)**:
   - 키트 없음 → 안내: "키트가 없습니다. `mc-logi-implement-kit` 먼저 생성 필요." 후 중단.
   - 키트 stale (`version-master.md` last sync 오래됨) → **권고만**:
     "⚠️ 키트 last sync N일 전 — 그 이후 logicraft 설계 변경분 미반영. `mc-logi-implement-kit` SYNC 권장. 그대로 진행할까요?" 사용자 선택. **자동 SYNC 하지 않는다** (점검은 read-only·가벼움 원칙).
   - 진행 시 stale 사실을 **Phase 4 리포트 상단 경고 배너**로 항상 명시.

### Phase 1 — 데이터 수집 (메인 1회)

메인이 모든 auditor 공통 입력을 1회 수집한다 (중복 fetch 방지):

1. **키트 카탈로그 로드**: `IMPLEMENTATION.md`(빌드순서·의존맵·구현현황·구현함정), `version-master.md`(ITEM 버전 표·last sync), 차원별 ITEM 요약 `.md` + `_raw/*.json` 경로 인덱스.
2. **코드 루트 식별**: 빌드 도구(gradle/maven)·소스 루트·계층 구조·테스트 인프라를 serena `get_symbols_overview` / Explore 로 실측. 컨트롤러·엔티티·마이그레이션·테스트 디렉터리 위치.
3. **IMPREC·coverage 수집** (logicraft 가용 시): `get_implementation_coverage(scope=domain)`, ITEM 별 implementation record(status·progress·커밋·구현노트). 불가 시 2방향 degrade 표시.
4. **ADR 정책 추출**: 키트 ADR 요약 + `IMPLEMENTATION.md` 구현 함정 단락에서 정책 목록 구성(policy auditor 입력). 메모리 grep 보조.
5. **타겟 범위 산출**: Phase 0 결정에 따라 점검 대상 ITEM 집합 확정.

### Phase 2 — 6차원 병렬 auditor

한 메시지에 6 `logi-implement-auditor` 호출. 각 prompt 에 주입:
- 입력 yaml: `domain_id`, `dimension`, `kit_root`, `code_root`, `item_catalog`(해당 차원), `imprec_data`(또는 degrade 플래그), `adr_policies`(policy 차원), `target_scope`.
- `dimensions/{dimension}.md` 본문 (차원 룰).
- `checklist.md` 본문 (evidence/confidence 규약 + read-only 보장 + 출력 YAML 스키마).

에이전트 책무: 키트 계약 판독 → 대응 코드 휴리스틱 추적(IMPLEMENTATION.md 의존맵 + IMPREC 커밋/심볼 + 계약 문자열 grep) → 5종 분류 finding 작성(evidence + confidence) → 구조화 YAML 반환.

**한 메시지에 6 Agent calls** (병렬 실행):
```python
Agent(subagent_type="logi-implement-auditor", description="Conform D004 api", prompt=...)
Agent(subagent_type="logi-implement-auditor", description="Conform D004 schema", prompt=...)
Agent(subagent_type="logi-implement-auditor", description="Conform D004 policy", prompt=...)
Agent(subagent_type="logi-implement-auditor", description="Conform D004 coverage", prompt=...)
Agent(subagent_type="logi-implement-auditor", description="Conform D004 acceptance", prompt=...)
Agent(subagent_type="logi-implement-auditor", description="Conform D004 role", prompt=...)
```

6 auditor 모두 완료 대기.

#### ★ Agent 이름 해석 + 등록 fallback (중요)

`logi-implement-auditor` 에이전트는 **설치 방식에 따라 등록 이름이 다르다**:
- **플러그인 설치** (`/plugin install mc-logi-implement-review@logicraft`): 에이전트가 `agents/logi-implement-auditor.md` 로 동봉되어 **scoped name `mc-logi-implement-review:logi-implement-auditor`** 로 자동 등록 (fresh 세션에서 즉시 사용 가능 — "not found" 없음)
- **user/project scope** (개발 환경, `~/.claude/agents/`): bare name `logi-implement-auditor`

따라서 다음 순서로 시도 (절대경로 하드코딩 금지 — 설치 위치 무관):

**Case 1 — 전용 에이전트 호출** (첫 성공 채택):
1. `subagent_type="mc-logi-implement-review:logi-implement-auditor"` (플러그인 scope, 배포 환경 기본)
2. 실패 시 `subagent_type="logi-implement-auditor"` (user/project scope, 개발 환경)

**Case 2 — 둘 다 `Agent type ... not found`** → general-purpose 로 fallback + 에이전트 정의를 **동적 탐색**해 인라인:
```python
# 1) 에이전트 정의 파일을 Glob 으로 탐색 (설치 위치 무관, 절대경로 박지 말 것)
#    Glob("**/agents/logi-implement-auditor.md") → 첫 결과를 Read → agent_md_content
# 2) dimension 룰·checklist 는 메인이 이미 읽어둔 내용(dimension_rules_content,
#    checklist_content; 스킬 디렉터리 상대 — dimensions/<dim>.md, checklist.md)을 그대로 인라인
Agent(
  subagent_type="general-purpose",
  description="Conform D004 <dim> (fallback)",
  prompt=f"""당신은 logi-implement-auditor 역할입니다. 아래 system prompt 를 그대로 따르세요:

# logi-implement-auditor 시스템 프롬프트
{agent_md_content}

# 이번 차원 룰 (dimensions/<dim>.md)
{dimension_rules_content}

# 공통 체크리스트 (checklist.md)
{checklist_content}

# 입력
{입력 yaml}

# 출력
YAML 한 블록만 출력하고 종료. 자유 텍스트 금지.
"""
)
```

플러그인 배포 시 Case 1-1(plugin scope)으로 정상 동작, Case 2 는 안전망.

### Phase 3 — 합산 + 분류 + 우선순위

1. 6 auditor YAML 파싱 (실패 시 1회 재시도 → 해당 차원 skip + 보고).
2. **중복 finding 병합**: 같은 `code_ref` + 유사 reason / cross-dimension 매칭 통합.
3. **5종 유형별 분류** → 2버킷 매핑 (판정 모델 표):
   - `code_drift` / `coverage_gap` → `code_fix`
   - `design_stale` / `extra_code` → `design_update`
   - `imprec_mismatch` → `imprec_fix`
4. **우선순위 정렬** (아래 우선순위 매김 표).

### Phase 4 — 정합 리포트 출력

Markdown 표 (사용자 노출):
- 상단 **경고 배너** (키트 stale / logicraft degrade 발생 시).
- **커버리지 요약**: 점검 ITEM 수 / 정합 / 불일치(P0·P1·P2) / degrade 여부.
- **P0/P1/P2 finding 표** (dimension · 유형 · affected(키트 ID + `file:line`) · reason · confidence).
- **[코드 수정 버킷]** — mc-logi-implement / 수동 입력 포맷.
- **[설계 갱신 버킷]** — mc-logi-update 입력 포맷.
- **[추적 정정]** — imprec_mismatch 목록.

```markdown
# DOMAIN-004 학습데이터 구현 정합 점검 결과

> ⚠️ 키트 last sync 6일 전 (s6) — 그 이후 설계 변경분 미반영 가능. logicraft: 가용 (3방향).

## 요약
- 점검 ITEM: 84건 (API 40 + ERD 6 + AC 18 + ROLE 4 + ...)
- 불일치: 12건 (P0: 3 / P1: 6 / P2: 3) / degrade: 없음
- 코드 수정: 5건 / 설계 갱신: 4건 / 추적 정정: 3건

## P0 (계약 위반·런타임 깨짐)
| id | dimension | 유형 | affected | reason | conf |
|---|---|---|---|---|---|
| ROLE-CONF-001 | role | code_drift | API-332 / TusController.java:88 | 키트 required_roles=ROLE-002 인데 가드 부재(공개) | high |
| SCH-CONF-004 | schema | code_drift | ERD-010 ai_model / V18__*.sql | 키트 부분 UNIQUE 제약 미반영 | high |

## P1 (커버리지·표류) ...
## P2 (경미·needs_human) ...

## [코드 수정 버킷] (mc-logi-implement / 수동)
- ROLE-CONF-001: TusController API-332 핸들러에 ROLE-002 가드 적용
- ...

## [설계 갱신 버킷] (mc-logi-update)
- COV-002: ArtifactRegistrar 클래스 키트 ITEM 부재 — DFEAT 보강 결정 필요
- ...

## [추적 정정] (imprec_mismatch)
- COV-005: PortalDispatcher Stub 인데 IMPREC=implemented — in_progress 정정 권고
```

### Phase 5 — 메모리 저장 문의

종료 시 사용자에게 메모리 저장 여부 **문의** (domain-review Phase 6 규약 — 단 자동 아닌 문의형으로, 점검 결과는 휘발 가능성 높음). 저장 시:
1. `Bash date +%Y%m%d_%H%M` 로 실제 타임스탬프 수집.
2. `session_NN_{domain}_conformance_{YYYYMMDD}_HHMM.md` 작성 (~/.claude/projects/<project>/memory/).
3. MEMORY.md 인덱스 1줄 추가.

## Auditor 호출 패턴

```python
Agent(
  subagent_type="logi-implement-auditor",
  description=f"Conform {domain_id} {dimension}",
  prompt=f"""
당신은 logi-implement-auditor입니다. 다음 도메인의 {dimension} 차원 코드↔키트 정합을 감사하세요.

# 입력
domain_id: {domain_id}
dimension: {dimension}
kit_root: {kit_root}
code_root: {code_root}
target_scope: {target_scope}
degraded: {degraded}   # logicraft 불가 시 true → imprec 룰 SKIP

# item_catalog (해당 차원 키트 ITEM 요약 + _raw 경로)
{item_catalog_yaml}

# imprec_data (logicraft get_implementation_coverage 결과; degraded 면 빈값)
{imprec_data_yaml}

# adr_policies (policy 차원용; ADR ID → 결정 한 줄)
{adr_policies_yaml}

# Dimension 룰 (dimensions/{dimension}.md)
{dimension_rules_content}

# 공통 체크리스트 (checklist.md)
{checklist_content}

# 출력
STEP 0~6 완료 후 checklist.md 출력 YAML 스키마 한 블록만 출력하고 종료.
""",
)
```

각 prompt 에 포함:
- 입력 yaml (domain_id, dimension, kit_root, code_root, item_catalog, imprec_data/degraded, adr_policies, target_scope)
- 해당 dimension 의 `dimensions/<name>.md` 본문
- 공통 `checklist.md` 본문

## 우선순위 매김 (Phase 3)

| Severity | 조건 |
|---|---|
| **P0** | 계약 위반 런타임 깨짐 / envelope 불일치 / ERD 제약(CHECK·FK·UNIQUE) 코드 누락 / ADR 정책 정면 위반 / `imprec_mismatch`(구현됨 주장인데 코드 부재) / 권한 가드 미적용(엔드포인트 공개) |
| **P1** | `coverage_gap`(미구현 ITEM) / `extra_code`(키트에 없는 엔드포인트·테이블) / 버전 stale(키트가 코드 이후 변경) / 요청·응답 계약 표류 / 역할 불일치 / 가드 스텁 |
| **P2** | 명명·구조 경미 차이 / `confidence: low` 또는 `needs_human: true` / 정보 풍부화 권장 / negative AC 테스트 부재 |

## TaskList 관리

- audit 진입 시 `TaskCreate` × 6 (dimension별)
- 각 auditor 시작 시 in_progress
- 완료 시 completed
- Phase 3~4 종료 시 cleanup

## 에러·degrade 처리

| 상황 | 대응 |
|---|---|
| 키트 없음 | 안내 후 중단 (implement-kit 선행 필요) |
| 키트 stale | 권고만 + 진행 시 경고 배너 (자동 SYNC 안 함) |
| logicraft 불가 | 2방향 degrade (imprec_mismatch SKIP) + 리포트 명시 |
| auditor YAML 파싱 실패 | 1회 재시도 → 실패 시 해당 차원 skip + 보고 |
| 큰 응답(>30KB) | persisted-output Bash python 파싱 |
| 코드 루트 식별 실패 | 사용자에게 소스 루트 확인 요청 |
| 6 auditor rate limit | 3+3 배치 분할 |
| 도메인 ID 잘못됨 | AskUserQuestion 으로 재확인 |

## mc-logi-implement / mc-logi-update 와의 분리

본 스킬은 **read-only**. 수정은 절대 수행 안 함.

검출된 불일치는:
1. Markdown 표 + YAML 원본으로 사용자에게 보고
2. 버킷별 분리 + 후속 스킬 입력 포맷 미리 변환 (코드 수정 → mc-logi-implement / 설계 갱신 → mc-logi-update / 추적 정정 → mc-logi-implement Phase 5)
3. 사용자가 별도로 후속 스킬 호출 시 위 입력 그대로 사용

(메인이 직접 mc-logi-implement / mc-logi-update 호출 안 함)

## 호출 예시

### 예시 1: D004 전체 정합 점검
```
사용자: "D004 구현이 키트랑 맞는지 확인해줘"
→ Phase 0: domain_id=DOMAIN-004, 전체 키트, 키트 게이트(s6 신선도 판정)
→ Phase 1: 키트 카탈로그 + 코드 루트 + IMPREC + ADR 정책 1회 수집
→ Phase 2: 6 auditor 병렬 (한 메시지)
→ Phase 3: 12 불일치 합산, P0:3 / P1:6 / P2:3, 2버킷 분류
→ Phase 4: Markdown 표 + 코드수정 5 / 설계갱신 4 / 추적정정 3 분리 보고
→ Phase 5: 메모리 저장 문의 → session_XX_d004_conformance.md
```

### 예시 2: D004 schema 차원만
```
사용자: "D004 ERD 대비 마이그레이션 표류 확인"
→ Phase 0: dimension=schema 단일
→ Phase 2: auditor 1건만 호출 (schema)
→ Phase 4: 컬럼 누락·제약 미반영(SCH-CONF-002/004) 리포트만
```

### 예시 3: 현재 브랜치 diff 만
```
사용자: "지금 브랜치 구현분이 키트 지키는지 점검"
→ Phase 0: 타겟 = git diff 변경 파일 → 관련 키트 ITEM 집합으로 역산
→ Phase 2: 6 auditor (target_scope 한정)
→ Phase 4: diff 범위 내 불일치만
```

## 진입 멘트

"mc-logi-implement-review 시작합니다.

대상: `<DOMAIN-ID>` `<도메인명>` / 범위: `<전체 키트 | 타겟>`
키트: `<경로>` (last sync `<시각>`, `<신선 | ⚠️stale N일>`)
모드: read-only (코드·설계 수정 없음, 검출만) / 판정: 3방향 (logicraft `<가용 | degrade>`)

데이터 수집 후 6 auditor 병렬 실행합니다. 계속할까요?"
