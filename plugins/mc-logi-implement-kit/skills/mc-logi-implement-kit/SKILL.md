---
name: mc-logi-implement-kit
description: Logicraft 특정 프로젝트의 특정 도메인을 로컬에서 바이브코딩으로 구현할 수 있도록 구현 핵심 ITEM 세트를 ./docs/design/{도메인}-{ID}/{타입}/{ITEM} 구조로 다운로드+구현지향 요약하고, 각 ITEM 상단에 logicraft current_version 을 박아 재실행 시 버전 차이를 감지·표기·갱신하는 구현 준비 스킬. 사용자가 "D002 구현 키트 만들어줘", "DOMAIN-002 다운받아 구현 준비해줘", "logicraft 도메인 로컬로 내려받아줘", "구현 키트 동기화해줘" 등을 요청할 때 실행. logi-implement-fetcher 에이전트를 타입별 병렬 실행. 요약 + 원본 JSON 둘 다 보존. ITEM 수정 안 함 — read-only 다운로드.
license: MIT
allowed-tools: Read, Write, Edit, Grep, Glob, Bash, Agent, ToolSearch, AskUserQuestion, TaskCreate, TaskUpdate, TaskList
metadata:
  version: "1.0.0"
  domain: logicraft-orchestration
  triggers: 구현 키트, implement kit, 도메인 다운로드, 구현 준비, 구현 키트 동기화, 버전 동기화, D001 구현 키트, D002 다운로드, DOMAIN-XXX 구현 준비, logicraft 로컬 다운, 바이브코딩 준비, spec 다운로드
  role: orchestrator-readonly
  scope: logicraft-domain-implementation-prep
  output-format: docs/design/{도메인}-{ID}/ 트리 (요약 .md + 원본 .json + version-master.md + IMPLEMENTATION.md)
  related-skills: mc-logi-domain-review, mc-logi-update, skill-creator
---

# mc-logi-implement-kit — Logicraft Domain Implementation Kit Downloader

Logicraft 특정 프로젝트의 특정 도메인을, **로컬에서 바이브코딩으로 그대로 구현 가능**하도록
구현 핵심 ITEM 을 다운로드 + 구현지향 요약 + 버전 추적한다. **read-only** — logicraft ITEM 절대 수정 안 함.

## When to Use

- 사용자가 특정 도메인 구현 착수 전 로컬 키트 요청 (예: "D002 구현 키트 만들어줘")
- 이미 받은 키트의 logicraft 변경분 재동기화 (예: "구현 키트 최신화")
- 설계가 logicraft 에서 cascade 된 후 코드 반영 전 변경분 파악
- 바이브코딩 에이전트에게 줄 "구현 컨텍스트 번들" 생성

## When NOT to Use

- logicraft ITEM 수정 (mc-logi-update)
- 도메인 정합 갑 검출 (mc-logi-domain-review)
- 단일 ITEM 조회 (logicraft MCP 직접)
- 실제 코드 작성 (본 스킬은 키트만 생성 — 구현은 키트 기반 별도 진행)

## 핵심 원칙 (사용자 결정 반영)

1. ✅ **이름**: `mc-logi-implement-kit`
2. ✅ **ITEM 범위**: 구현 핵심 세트 고정 (`core-item-set.md` 의 Tier 1~3 결정 규칙)
3. ✅ **산출물**: 구현지향 요약(.md) + 원본 raw JSON(.json) **둘 다**
4. ✅ **실행**: ITEM 타입별 `logi-implement-fetcher` 병렬 에이전트
5. ✅ **버전 추적**: 각 ITEM 헤더에 `current_version` 박음 + `version-master.md` 마스터 + 재실행 시 정수 비교로 NEW/CHANGED/UNCHANGED/RETIRED 판정
6. ✅ **read-only**: logicraft 쓰기 도구 호출 금지. 로컬 파일만 생성/갱신
7. ✅ **삭제 안 함**: RETIRED ITEM 도 `_retired/` 로 이동만, 물리 삭제 금지

## 디렉터리 구조 (산출물)

```
./docs/design/{도메인슬러그}-{DOMAIN-ID}/
├── version-master.md            ← 버전 마스터 (모든 ITEM 버전 표 + 이번 run changelog)
├── IMPLEMENTATION.md            ← 바이브코딩 진입점 (빌드 순서·의존 그래프·제약·시작점)
├── _domain.md                   ← 도메인 ITEM 자체 요약
├── _raw/_domain.json            ← 도메인 원본
├── domain_feature/
│   ├── DFEAT-064.md             ← 구현지향 요약 (헤더에 version)
│   └── _raw/DFEAT-064.json      ← logicraft 원본 그대로
├── api_endpoint/
│   ├── API-273.md
│   └── _raw/API-273.json
├── erd/  diagram_sequence/  screen_spec/  use_case/
├── domain_event/  acceptance/  permission_role/  constant/
├── adr/  nfr/  implementation_guideline/  code_module/  feature/
├── (조건부) class_diagram/ diagram_state/ integration_point/ external_system/ ...
└── _retired/                    ← logicraft 에서 deprecated/제거된 ITEM (삭제 안 함)
    └── api_endpoint/API-191.md
```

- 폴더명 `{도메인슬러그}-{DOMAIN-ID}`: logicraft `slug` 필드 사용(파일시스템 안전).
  slug 없으면 도메인 title 을 sanitize(공백→`-`, `·/\:*?"<>|` 제거) + `-DOMAIN-XXX` 접미.
- `{ITEM 종류 명}` = logicraft type code 그대로 (`domain_feature`, `api_endpoint` …).
- 원본 JSON 은 각 타입 폴더 하위 `_raw/` 에 동일 ID 로 보존.

## 각 ITEM 파일 헤더 (버전 감지 핵심)

모든 요약 `.md` 최상단에 YAML frontmatter + (변경 시) 배너:

```markdown
---
logicraft_item: DFEAT-064
type: domain_feature
version: 12                       # logicraft current_version (정수)
last_updated_at: 2026-05-16T23:35:04Z
domain: DOMAIN-002
project_id: 95f00d2e-30e8-4426-bc37-9bd85aa969e9
synced_at: 2026-05-18T14:30Z
sync_session: 5
stale: false                      # logicraft 가 자체 표기한 stale 플래그
status: synced                    # synced | NEW | CHANGED | RETIRED
prev_version: null                # CHANGED 일 때만 직전 로컬 버전
raw: ./_raw/DFEAT-064.json
---
```

CHANGED 일 때 frontmatter 바로 아래 배너 삽입:

```markdown
> ⚠️ **버전 변경 감지 — logicraft v11 → v12** (2026-05-16T23:35Z)
> change_summary: <logicraft change_summary 원문 그대로>
> ↳ 아래 요약/구현 노트를 재검토하고 이미 작성된 코드에 반영 필요.
> ↳ 직전 버전 요약은 git diff 로 확인 (이 파일 이전 커밋).
```

## 워크플로우

### Phase 1 — 진입 + 대상 식별

1. 사용자 입력 파싱:
   - 도메인 ID 명시 (예 `D002`, `DOMAIN-002`) → 채택
   - 도메인명 명시 (예 `영상·메타 수집`) → `list_items(type=domain)` 로 매핑
   - 둘 다 없으면 `AskUserQuestion` 으로 확정
2. project_id 식별:
   - `~/.claude/projects/*/memory/MEMORY.md` 에서 현재 프로젝트 확인
   - 없으면 `list_projects` 결과를 사용자에게 제시해 선택
3. 출력 루트 결정: `<cwd>/docs/design/` (없으면 생성). cwd 가 코드 레포 루트인지 확인.
4. 재실행 여부 판정: `docs/design/{slug}-{ID}/version-master.md` 존재 → **SYNC 모드**, 없으면 **INITIAL 모드**

### Phase 2 — 도메인 ITEM 카탈로그 수집 (메인 1회)

```python
# 1. 도메인 본체
get_item(project_id, DOMAIN-XXX)            # description / ubiquitous_language / brownfield

# 2. 도메인 소속 ITEM 전수 (★ list_items 는 domain_id 필터 미지원 — 우회)
get_related(project_id, DOMAIN-XXX, depth=2, direction="both")
get_neighbors(project_id, DOMAIN-XXX)       # backward = 도메인 소속 ITEM ID 전부

# 3. 타입별 보강 (get_neighbors 가 누락한 타입)
list_items(type=adr, limit=200)             # 도메인 참조 ADR 수동 필터
list_items(type=implementation_guideline)   # applies_to_types 매칭
list_items(type=<core type>, include_retired=true)   # RETIRED 식별
```

- `core-item-set.md` 의 Tier 1~3 규칙으로 다운로드 대상 타입 확정
- 각 ITEM 의 `id / type / current_version / last_updated_at / stale / change_summary / slug` 수집
  → **현재 카탈로그(current_catalog)**
- 큰 응답(>30KB)은 Bash + `python -c "import json"` (encoding='utf-8') 파싱

### Phase 2.5 — 버전 차이 산출 (SYNC 모드만)

1. 기존 `version-master.md` 파싱 → **로컬 카탈로그(local_catalog)**: ITEM ID → version
2. current_catalog 와 비교해 상태 분류 (`version-tracking.md` 알고리즘):

| 상태 | 조건 | 처리 |
|---|---|---|
| **NEW** | current 에 있고 local 에 없음 | 신규 다운로드 |
| **CHANGED** | 양쪽 존재, `current_version` 다름 | 재다운로드 + 변경 배너 + prev_version 기록 |
| **UNCHANGED** | 양쪽 존재, version 동일 | 다운로드 skip (토큰 절약) — 파일 존재만 검증 |
| **RETIRED** | local 에 있고 current 활성 목록에 없음/deprecated | `_retired/` 이동 + version-master 표기 (삭제 X) |

3. INITIAL 모드는 전부 NEW 취급

### Phase 3 — 타입별 병렬 fetch (logi-implement-fetcher)

다운로드 필요 타입(NEW/CHANGED 가 1건 이상인 타입)별로 한 메시지에 병렬 Agent:

```python
Agent(subagent_type="logi-implement-fetcher",
      description="Fetch D002 domain_feature kit",
      prompt=<아래 호출 패턴>)
Agent(subagent_type="logi-implement-fetcher",
      description="Fetch D002 api_endpoint kit", prompt=...)
# ... 타입 수만큼 (상한 8 병렬, 초과 시 배치 분할)
```

#### ★ Agent 등록 timing fallback (mc-logi-domain-review 와 동일)

`logi-implement-fetcher` 정의 세션에서는 호출 불가. 에러 시 자동 fallback:

```python
# Case 1: 호출 성공 → 정상
# Case 2: "Agent type 'logi-implement-fetcher' not found" → general-purpose 전환
Agent(
  subagent_type="general-purpose",
  description="Fetch D002 <type> kit (fallback)",
  prompt=f"""당신은 logi-implement-fetcher 역할입니다. 먼저 아래 파일을 Read 로 정독하고 그대로 따르세요:

1. C:\\Users\\lumie\\.claude\\agents\\logi-implement-fetcher.md (시스템 프롬프트)
2. C:\\Users\\lumie\\.claude\\skills\\mc-logi-implement-kit\\summary-templates.md (타입별 요약 포맷)
3. C:\\Users\\lumie\\.claude\\skills\\mc-logi-implement-kit\\checklist.md (hard rules)

# 입력
{입력 yaml}

# 출력
fetcher 파일의 STEP 출력 규약대로 파일 생성 후 YAML 결과 블록 1개만 출력하고 종료.
""")
```

각 fetcher prompt 에 포함:
- project_id, domain_id, domain_slug, output_root
- 이번 타입에서 처리할 ITEM 목록 + 각 상태(NEW/CHANGED/UNCHANGED) + prev_version
- `summary-templates.md` 의 해당 타입 섹션 본문
- `checklist.md` 본문

fetcher 책무: ITEM 별 `get_item` → 원본 `_raw/<ID>.json` 저장 → 타입별 템플릿으로 구현지향 `.md` 요약 작성(헤더 frontmatter + 변경 배너 포함) → 결과 YAML 반환.

### Phase 4 — 도메인 본체 + 버전 마스터 + 진입점 작성 (메인)

1. `_domain.md` + `_raw/_domain.json` 작성 (도메인 요약: bounded context / 책임 / ubiquitous language / 외부 의존 / ADR 정책)
2. **`version-master.md` 재작성** (`version-tracking.md` 포맷):
   - 전체 ITEM 버전 표 (ID / type / title / version / last_updated_at / stale / local file / status)
   - 이번 run **Changelog 섹션**: NEW n건 / CHANGED n건(각 prev→cur + change_summary) / RETIRED n건
   - 헤더 메타: project, domain, last sync 시각, sync_session, domain item version
3. **`IMPLEMENTATION.md` 작성/갱신** (바이브코딩 진입점):
   - 도메인 1줄 요약 + bounded context
   - **빌드 순서** (`core-item-set.md` 의 build order: ADR/NFR/CONST/GUIDE → ERD → EVT → API → DFEAT → SEQ → ROLE → SCREEN → UC/AC)
   - **의존 그래프**: DFEAT ↔ API ↔ ERD ↔ EVT ↔ SCREEN 링크 맵 (get_related 결과 기반)
   - **구속 제약 요약**: 적용 ADR 결정 / NFR 예산 / CONST 실제 값 / GUIDE 코딩 규칙
   - **구현 현황**: `get_implementation_coverage(scope=domain)` + `list_unimplemented(domain_id)` → "이미 구현됨 / 미구현 / 어디부터 시작" 표
   - **변경 알림**: 이번 run CHANGED ITEM 목록 → "코드 재반영 필요" 강조
   - 각 ITEM 요약 파일로의 상대경로 링크 인덱스

### Phase 5 — 결과 보고

Markdown 표로 사용자에게:
```markdown
# DOMAIN-002 영상·메타 수집 구현 키트 (SYNC 모드)

## 요약
- 출력: ./docs/design/domain-video-metadata-ingestion-DOMAIN-002/
- 대상 ITEM: 72건 (DFEAT 6 / API 35 / ERD 2 / SEQ 14 / SCREEN 6 / UC 7 / EVT 2 …)
- 이번 run: NEW 4 / CHANGED 9 / UNCHANGED 57 / RETIRED 2
- 진입점: IMPLEMENTATION.md (빌드 순서 + 의존 그래프 + 구현 현황)

## 변경 감지 (코드 재반영 필요)
| ITEM | type | v | change_summary |
|---|---|---|---|
| DFEAT-064 | domain_feature | 11→12 | … |
| SEQ-020 | diagram_sequence | 8→9 | … |
...

## RETIRED (logicraft 에서 폐기 — _retired/ 이동)
- API-191 (deprecated) — 코드에서 제거 검토

→ 바이브코딩: IMPLEMENTATION.md 부터 읽고 빌드 순서대로 구현
→ 재동기화: 이 스킬 재실행 시 변경분만 갱신
```

### Phase 6 — 메모리 저장 (종료 시 사용자 문의)

작업 완료 후 사용자에게 메모리 저장 여부 문의 (mc-logi-update 정책 따름).
저장 시: `~/.claude/projects/<project>/memory/` 에 키트 생성 기록 + MEMORY.md 인덱스 1줄.
사용자가 "저장하지 마" 시 skip.

## logi-implement-fetcher 호출 패턴

```python
Agent(
  subagent_type="logi-implement-fetcher",
  description=f"Fetch {domain_id} {type} kit",
  prompt=f"""
당신은 logi-implement-fetcher 입니다. 아래 타입의 ITEM 을 구현 키트로 다운로드+요약하세요.

# 입력
project_id: {project_id}
domain_id: {domain_id}
domain_slug: {domain_slug}
item_type: {type}
output_root: {cwd}/docs/design/{domain_slug}-{domain_id}
sync_session: {n}
synced_at: {iso_now}

# 처리 대상 (status 포함)
{items_yaml}   # [{id, status, prev_version, current_version, stale}]

# 타입별 요약 템플릿 (summary-templates.md 의 {type} 섹션)
{template_section}

# 공통 체크리스트
{checklist_content}

# 출력
- 각 NEW/CHANGED ITEM: get_item → _raw/{id}.json + {type}/{id}.md (frontmatter+배너)
- UNCHANGED: 파일 존재 검증만, 없으면 다운로드
- 완료 후 STEP-OUT YAML 1개만 출력하고 종료. 자유 텍스트 금지.
""")
```

## 병렬 실행 정책

- 다운로드 필요 타입은 한 메시지에 동시 호출 (상한 8 병렬)
- 8 초과 시 타입을 2 배치로 분할 순차
- UNCHANGED 만 있는 타입은 fetcher 생략 (메인이 파일 존재만 검증)
- 단일 거대 ITEM(screen_spec 70KB+)은 fetcher 내부에서 Bash python 파싱

## 에러 처리

| 에러 | 대응 |
|---|---|
| fetcher YAML 파싱 실패 | 1회 재시도 → 실패 시 해당 타입 skip + 보고 |
| get_item 응답 큼(>30KB) | fetcher 가 persisted-output Bash python 파싱 |
| version-master.md 파싱 실패 | 백업 후 INITIAL 모드로 폴백 + 사용자 경고 |
| 도메인 ID 잘못 | AskUserQuestion 재확인 |
| cwd 가 레포 아님 | 사용자에게 출력 경로 확인 요청 |
| MCP 도구 다운 | ToolSearch 재시도 → 실패 시 부분 보고 후 중단 |

## read-only 보장

본 스킬은 logicraft **조회 도구만** 사용: `get_item`, `list_items`, `get_neighbors`,
`get_related`, `analyze_impact`, `get_implementation_coverage`, `list_unimplemented`,
`get_item_schema`, `get_logicraft_guide`. **쓰기 도구(create_item/update_item/register_*/
propose_change 등) 절대 호출 금지.** logicraft 변경은 mc-logi-update 별도 사용.

## 호출 예시

### 예시 1: 최초 키트 생성
```
사용자: "D002 구현 키트 만들어줘"
→ Phase 1: DOMAIN-002, project=KLID 2차, INITIAL 모드
→ Phase 2: get_neighbors + list_items → 72 ITEM 카탈로그
→ Phase 3: 11 타입 병렬 fetcher (전부 NEW)
→ Phase 4: version-master.md + IMPLEMENTATION.md 작성
→ Phase 5: 보고 → 사용자는 IMPLEMENTATION.md 부터 바이브코딩
```

### 예시 2: 재동기화 (버전 변경 감지)
```
사용자: "D002 구현 키트 최신화해줘"
→ Phase 1: SYNC 모드 (version-master.md 존재)
→ Phase 2.5: 현재 vs 로컬 카탈로그 diff → NEW 4 / CHANGED 9 / RETIRED 2
→ Phase 3: 변경분 있는 타입만 fetcher → CHANGED 에 v배너 삽입
→ Phase 4: version-master changelog 갱신 + IMPLEMENTATION 변경알림
→ Phase 5: "9건 코드 재반영 필요" 강조 보고
```

## 진입 멘트

"mc-logi-implement-kit 시작합니다.

대상: `<DOMAIN-ID> <도메인명>` / 프로젝트: `<project>`
모드: `<INITIAL | SYNC>` / 출력: `./docs/design/<slug>-<ID>/`
ITEM 범위: 구현 핵심 세트 고정 (Tier 1~3)
모드: read-only (logicraft 수정 없음, 다운로드만)

카탈로그 수집 후 타입별 fetcher 병렬 실행합니다. 계속할까요?"
