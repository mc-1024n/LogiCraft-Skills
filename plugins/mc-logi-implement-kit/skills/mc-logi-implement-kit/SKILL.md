---
name: mc-logi-implement-kit
description: Logicraft 특정 프로젝트의 특정 도메인을 로컬에서 바이브코딩으로 구현할 수 있도록 구현 핵심 ITEM 세트를 ./docs/design/{도메인}-{ID}/{타입}/{ITEM} 구조로 다운로드+구현지향 요약하고, 각 ITEM 상단에 logicraft current_version 을 박아 재실행 시 버전 차이를 감지·표기·갱신하는 구현 준비 스킬. 사용자가 "D002 구현 키트 만들어줘", "DOMAIN-002 다운받아 구현 준비해줘", "logicraft 도메인 로컬로 내려받아줘", "구현 키트 동기화해줘" 등을 요청할 때 실행. 결정적 다운로더(bin/download-kit.mjs)가 배치 export(API-152)를 호출해 서버 verbatim 스켈레톤 + 원본 JSON 을 받아 기록 — LLM 0·초 단위·content-hash 무열화(ADR-026, 옛 logi-implement-fetcher LLM 요약 폐기). ITEM 수정 안 함 — read-only 다운로드.
license: MIT
allowed-tools: Read, Write, Edit, Grep, Glob, Bash, Agent, ToolSearch, AskUserQuestion, TaskCreate, TaskUpdate, TaskList
metadata:
  version: "1.4.0"
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
- 도메인 정합 갭 검출 (mc-logi-domain-review)
- 단일 ITEM 조회 (logicraft MCP 직접)
- 실제 코드 작성 (본 스킬은 키트만 생성 — 구현은 키트 기반 별도 진행)

## 핵심 원칙 (사용자 결정 반영)

1. ✅ **이름**: `mc-logi-implement-kit`
2. ✅ **ITEM 범위**: 구현 핵심 세트 고정 (`core-item-set.md` 의 Tier 1~3 결정 규칙)
3. ✅ **산출물**: 서버 결정적 스켈레톤(.md, verbatim·무열화) + 원본 raw JSON(.json) **둘 다**
4. ✅ **실행**: **결정적 다운로더 `bin/download-kit.mjs`** (배치 export API-152 호출, LLM 0·초 단위·content-hash 무열화). 옛 `logi-implement-fetcher`(LLM 요약)는 폐기·폴백용(ADR-026)
5. ✅ **버전 추적**: 다운로더가 `.kit-manifest.json`(id→version/hash)으로 델타 자동 산출 + `version-master.md` 생성 + frontmatter 에 version/status/prev_version. 재실행 시 변경분만
6. ✅ **read-only**: logicraft 쓰기 도구 호출 금지. 로컬 파일만 생성/갱신
7. ✅ **삭제 안 함**: RETIRED ITEM 도 `_retired/` 로 이동만, 물리 삭제 금지
8. ⚠️ **배포**: `publish_skill`/플러그인 배포 시 **`download-kit-src.md`(소스 캐리어)를 files[] 에 반드시 포함**한다 — 이게 있으면 `bin/download-kit.mjs` 가 없어도 Phase 3 가용성 게이트가 캐리어 코드블록에서 재생성한다(설치본은 첫 실행 시 사용자 확인 후 생성). `bin/download-kit.mjs` 자체는 배포 안 해도 됨(생성물). 또한 배치 export 엔드포인트(API-152)가 **대상 LogiCraft 서버에 배포**돼 있어야 다운로더가 동작(미배포 서버는 404→exit 4→fetcher 폴백).

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
├── adr/  nfr/  implementation_guideline/  feature/
│                                 (code_module 은 다운로드 안 함 — core-item-set.md 제외 규칙)
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

#### ★ DFEAT 부재 게이트 (구현 착수 전 필수 노티)

카탈로그 확정 직후, **`domain_feature`(DFEAT) 건수를 센다.** DFEAT = 도메인 비즈니스 로직 단위이자
빌드 순서 step 4 의 서비스 계층 설계 근거(API·EVT·테이블을 오케스트레이션). **DFEAT 가 0건이면
"무엇을 구현해야 하는지"의 진실원이 비어있는 상태** — API/ERD 만으로 구현하면 비즈니스 로직을
구현자가 임의 추정하게 되어 설계 이탈이 발생한다. 따라서 다운로드 착수 전 아래 게이트를 통과해야 한다:

- **DFEAT 0건 감지 → 진행 전 `AskUserQuestion` 으로 반드시 노티**하고 사용자 결정을 받는다:
  - 질문 예: "`DOMAIN-XXX <도메인명>` 에 domain_feature(DFEAT) 가 **0건**입니다. DFEAT 는 비즈니스 로직
    구현의 진실원인데, 없는 상태로 키트를 만들면 구현자가 로직을 임의 추정하게 됩니다. 어떻게 진행할까요?"
  - 선택지:
    1. **DFEAT 먼저 설계** (권장) — 키트 생성 중단. mc-logi-brainstorming/mc-logi-update 로 DFEAT 설계 후 재실행
    2. **DFEAT 없이 진행** — API/ERD/SCREEN 만으로 키트 생성 (구현 시 로직 추정 리스크 감수 — 명시 동의)
    3. **도메인 ID 재확인** — 도메인을 잘못 지정했을 가능성 (의도한 도메인엔 DFEAT 존재)
  - 사용자가 **"DFEAT 없이 진행"** 을 명시 선택한 경우에만 Phase 2.5 로 계속. 그 외엔 중단 또는 도메인 재확인.
- **DFEAT 는 있으나 이를 실현할 계약(API) 또는 데이터 모델(ERD)이 0건**인 경우(예: DFEAT 8 / API 0)도
  같은 방식으로 부분 노티 — "구현 계약(API)·데이터 모델(ERD) 부재" 경고를 표시하고 진행 여부 확인.
- 검사 결과(DFEAT/API/ERD 건수, 노티 발생 여부, 사용자 결정)를 기록해 Phase 4 IMPLEMENTATION.md 상단
  경고 블록과 Phase 5 보고에 반영한다.

### Phase 2.5 — 버전 차이 산출 → **Phase 3 다운로더가 자동 처리**

버전 diff(NEW/CHANGED/UNCHANGED/RETIRED)는 이제 **별도 단계가 아니다** — Phase 3 의 결정적 다운로더가 `.kit-manifest.json`(id→version/hash)과 서버 export 를 비교해 자동 산출한다. UNCHANGED 는 페치·재렌더 skip, RETIRED 는 `_retired/` 이동, 변경분만 다운로드. 상태 분류표는 `version-tracking.md` 참고(개념 동일). 메인은 버전 카탈로그를 손으로 파싱하지 않는다.

### Phase 3 — 결정적 다운로드 (download-kit.mjs · LLM 0)  ★ ADR-026

**★ 가용성 게이트 (Phase 3 진입 시 먼저 판정 → 폴백 결정)**:
1. **스크립트 탐색 + (없으면) 재생성 문의**: `Glob("**/mc-logi-implement-kit/bin/download-kit.mjs")`.
   - **찾음** → 그대로 사용(→ 2·3단계).
   - **없음**(스킬만 배포되고 `bin/` 누락) → **`AskUserQuestion` 으로 사용자에게 먼저 묻는다**(임의 폴백 금지):
     - 질문 예: "결정적 다운로더 스크립트(`bin/download-kit.mjs`)가 이 환경에 없습니다. 어떻게 진행할까요?"
     - 선택지: ① **지금 생성하고 결정적 다운로드로 진행 (권장)** — 빠르고 무열화 / ② **옛 fetcher 방식으로 진행** — 느리고 30~40% 열화
     - **①(생성) 선택 시**: `Glob("**/mc-logi-implement-kit/download-kit-src.md")` → Read → 그 안의 ```js 코드블록 **전체를 한 글자도 바꾸지 말고** `<스킬 디렉터리>/bin/download-kit.mjs` 로 Write(부모 dir 생성) → `node --check` 로 문법 확인 → 정상이면 2·3단계로 진행(결정적 다운로드).
     - **②(옛 방식) 선택 시**: 이 Phase 아래 옛 fetcher 절차로 폴백.
     - `download-kit-src.md`(캐리어)마저 없으면 → 생성 불가 → 옛 fetcher 폴백 + "다운로더·소스 캐리어 모두 미배포" 보고.
2. **환경**: node 미가용 → 폴백. `LOGICRAFT_API_KEY`(lc_ 키) 미설정 → 사용자에게 설정 요청(MCP 와 동일 키). base 는 개발기 `LOGICRAFT_API_BASE`(기본 :14000/api), 상용은 해당 서버.
3. **다운로더 실행 후 종료코드 분기**:
   - **0** = 성공 → Phase 4.
   - **4** = 엔드포인트 미배포(서버에 `/kit-export` 없음 = 구버전 LogiCraft, 배치 export 미배포) → **폴백**(옛 fetcher, MCP `get_item` 기반).
   - **2** = 네트워크/인증 오류(서버 다운·키/스코프 문제) → **사용자에게 보고 + 수정 요청.** 자동 fetcher 폴백 금지(고칠 수 있는 설정 문제를 느린·열화 폴백으로 숨기지 말 것).
   - **1** = 인자 오류 → 호출 인자 수정.

→ 폴백은 이 Phase 아래 "#### ★ Agent 이름 해석 + 등록 fallback" 이후 옛 fetcher 절차를 그대로 따른다(동일 디렉터리 구조 산출, 단 요약이 LLM 이라 **느리고 30~40% 열화**). 폴백 사용 시 Phase 5 보고에 "⚠️ 다운로더 미가용 — fetcher 폴백 사용(원인: 스크립트 미배포 / 엔드포인트 미배포). 서버·스크립트 배포 확인 권장" 명시.

옛 fetcher(LLM 에이전트) 병렬 방식을 **결정적 노드 다운로더 하나로 대체**한다. 서버(LogiCraft 배치 export `GET /projects/:id/kit-export`, API-152)가 **원본 JSON + 서버 결정적 스켈레톤(verbatim·무열화) + content_hash + 그래프 links** 를 반환하고, 다운로더가 델타(version 비교)로 변경분만 받아 아래를 기록한다:
- `{type}/_raw/{ID}.json` — 원본(기존 `{item:...}` 포맷)
- `{type}/{ID}.md` — 서버 스켈레톤 body(verbatim) + 다운로더 재구성 frontmatter(`logicraft_item·type·version·domain·synced_at·status·prev_version·content_hash·stale·raw·links`)
- `version-master.md` — 다운스트림 신선도 게이트·changelog·ITEM 표
- `.kit-manifest.json` — 델타 판별용(id→version/hash)

**LLM 0 · 초 단위 · 설계 내용 무손실**(옛 fetcher 요약의 30~40% 열화 문제 해소 — content-hash 로 기계 검증).

실행 (스크립트 위치는 설치 무관하게 `Glob("**/mc-logi-implement-kit/bin/download-kit.mjs")` 로 탐색):
```bash
LOGICRAFT_API_KEY=<lc_ 키 — MCP 와 동일한 그 키> \
LOGICRAFT_API_BASE=http://localhost:14000/api \
node <download-kit.mjs> \
  --project <project_id> --out docs/design/{slug}-{DOMAIN-ID} \
  [--domain DOMAIN-NNN] [--types adr,domain_feature,api_endpoint,...] [--dry-run]
```
- **api-key**: MCP 와 동일한 `LOGICRAFT_API_KEY`(lc_) env. 개발기는 `logicraft-dev`(:14000), base 는 `LOGICRAFT_API_BASE`(기본 `http://localhost:14000/api`).
- **--types**: `core-item-set.md` Tier 1~3 규칙으로 확정한 타입 CSV(생략 시 도메인 전체 타입). code_module 제외 등 Tier 규칙은 --types 로 반영.
- **--domain**: 도메인 스코프. **--out**: 키트 루트.
- **델타·RETIRED·무결성**: 재실행 시 변경분만, UNCHANGED skip, 서버에서 사라진 것은 `_retired/` 이동. 쓰기 후 read-back 바이트 검증(무열화).
- 출력이 `📊 … 변경 N` + `✅ SYNC 완료` 이면 성공. 오류 시 종료코드(1 인자/2 HTTP·인증/3 무결성)·stderr 확인.

> ⚠️ **옛 `logi-implement-fetcher`(LLM 요약) 방식은 폐기(ADR-026).** ITEM 본문 "요약"은 서버 결정적 스켈레톤이 대체한다(의역 0). 구현지향 "해석"(MUST/체크리스트)은 버리는 게 아니라 Phase 4 IMPLEMENTATION.md 합성 + 구현 착수 시 지연 생성으로 이동. 아래 fetcher 절차는 **다운로더 미배포/실패 시 폴백 참고용**으로만 남긴다.

#### ★ Agent 이름 해석 + 등록 fallback (mc-logi-domain-review 와 동일)

`logi-implement-fetcher` 에이전트는 **설치 방식에 따라 등록 이름이 다르다**:
- **플러그인 설치** (`/plugin install mc-logi-implement-kit@logicraft`): 에이전트가 `agents/logi-implement-fetcher.md` 로 동봉되어 **scoped name `mc-logi-implement-kit:logi-implement-fetcher`** 로 자동 등록 (fresh 세션에서 즉시 사용 가능 — "not found" 없음)
- **user/project scope** (개발 환경, `~/.claude/agents/`): bare name `logi-implement-fetcher`

따라서 다음 순서로 시도 (절대경로 하드코딩 금지 — 설치 위치 무관):

**Case 1 — 전용 에이전트 호출** (첫 성공 채택):
1. `subagent_type="mc-logi-implement-kit:logi-implement-fetcher"` (플러그인 scope, 배포 환경 기본)
2. 실패 시 `subagent_type="logi-implement-fetcher"` (user/project scope, 개발 환경)

**Case 2 — 둘 다 `Agent type ... not found`** → general-purpose 로 fallback + 에이전트 정의를 **동적 탐색**해 인라인:
```python
# 1) 에이전트 정의 파일을 Glob 으로 탐색 (설치 위치 무관, 절대경로 박지 말 것)
#    Glob("**/agents/logi-implement-fetcher.md") → 첫 결과를 Read → agent_md_content
# 2) summary-templates·checklist 는 메인이 이미 읽어둔 내용(template_section, checklist_content;
#    스킬 디렉터리 상대 — summary-templates.md, checklist.md)을 그대로 인라인
Agent(
  subagent_type="general-purpose",
  description="Fetch D002 <type> kit (fallback)",
  prompt=f"""당신은 logi-implement-fetcher 역할입니다. 아래 system prompt 를 그대로 따르세요:

# logi-implement-fetcher 시스템 프롬프트
{agent_md_content}

# 타입별 요약 포맷 (summary-templates.md 해당 섹션)
{template_section}

# hard rules (checklist.md)
{checklist_content}

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
2. **`version-master.md` — 다운로더가 이미 생성**(Phase 3): 헤더 메타(project_id·domain·last sync·mode) + Changelog(NEW/CHANGED/RETIRED) + ITEM 표(ID/type/version/status). 메인은 재작성하지 않는다. 필요 시 도메인 item 버전·sync_session 등 부가 헤더만 보강 가능(선택).
3. **`IMPLEMENTATION.md` 작성/갱신** (바이브코딩 진입점):
   - 도메인 1줄 요약 + bounded context
   - **★ DFEAT 부재 경고 블록 (해당 시 최상단)**: Phase 2 게이트에서 DFEAT 0건(또는 API/ERD 부재)이
     감지됐고 사용자가 "없이 진행" 을 선택한 경우, 문서 최상단에 경고 블록을 박는다:
     `> ⚠️ **이 키트에는 DFEAT(비즈니스 로직 진실원)가 없습니다.** 구현 로직은 API/ERD 계약에서만 유추되므로
     설계 이탈 위험이 있습니다. DFEAT 설계 후 재동기화를 권장합니다.` — DFEAT 가 정상 존재하면 이 블록 생략.
   - **빌드 순서** (`core-item-set.md` 의 build order: ADR/NFR/CONST/GUIDE → ERD → EVT → API → DFEAT → SEQ → ROLE → SCREEN → UC/AC)
   - **의존 그래프**: DFEAT ↔ API ↔ ERD ↔ EVT ↔ SCREEN 링크 맵 (get_related 결과 기반)
     · `uses_constant`(API/SCREEN/ERD/DFEAT → CONST) 링크도 포함 — 어느 설계가 어느 상수를 쓰는지
   - **구속 제약 요약**: 적용 ADR 결정 / NFR 예산 / GUIDE 코딩 규칙
   - **★ 상수 값 표 (CONST 전수 — 매직넘버 단일 진실원)**: 도메인 소속 전 CONST 를 **실제 값과 함께** 한 표에 집계. 구현자가 enum/range/default/임계치/토큰을 추정·하드코딩하지 않고 여기서 lookup.
     | CONST | name | value | unit | kind | 결정 ADR | 사용처(uses_constant 역링크) |
     |---|---|---|---|---|---|---|
     | CONST-012 | MAX_BANDWIDTH_MBPS | 1000 | Mbps | magic_value | ADR-080 | API-259, DFEAT-070 |
     · value 는 logicraft 원문 그대로(의역 금지). 객체/배열이면 JSON 그대로.
     · env_var(is_secret=true)는 값 대신 `<secret — env 주입>` 표기.
     · uses_constant 역링크가 비어도 belongs_to_domain 으로 키트에 포함되니 표에는 반드시 넣고, 사용처는 "⚠️ 미연결" 로 표기.
   - **구현 현황**: `get_implementation_coverage(scope=domain)` + `list_unimplemented(domain_id)` → "이미 구현됨 / 미구현 / 어디부터 시작" 표
   - **변경 알림**: 이번 run CHANGED ITEM 목록 → "코드 재반영 필요" 강조
   - 각 ITEM 요약 파일로의 상대경로 링크 인덱스

### Phase 4.5 — 프로젝트 CLAUDE.md 키트 블록 등록 (`claude-md-block.md` 규약)

키트는 `docs/design/` 에만 있으면 후속 세션이 존재를 모른다 — 레포 루트 `CLAUDE.md` 의
`<!-- mc-logi-kit:start/end -->` 마커 구간에 키트 표·작업 규칙·도메인별 주의 포인터를 작성/갱신한다.

1. `claude-md-block.md` 를 읽고 템플릿·필드 추출 출처·병합 규칙을 따른다.
2. CLAUDE.md 없으면 생성, 있으면 **마커 구간만** 교체 (사용자 작성 내용 불가침).
3. 멀티 도메인 레포면 기존 블록의 타 도메인 행 보존 + 이번 도메인 행 추가/갱신.
4. SYNC 에서 CHANGED/RETIRED 가 있었으면 현황에 `⚠️ 변경 N건 코드 재반영 필요` 표식
   (코드 반영 완료 시 mc-logi-implement Phase 5 가 지움).

### Phase 5 — 결과 보고

Markdown 표로 사용자에게 (CLAUDE.md 블록 등록/갱신 여부 1줄 포함):
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

**★ DFEAT 부재 시 보고 최상단 경고 (Phase 2 게이트 발동분)**: DFEAT 0건(또는 API/ERD 부재)이었고
사용자가 "없이 진행" 을 택했으면 보고 맨 위에 눈에 띄게 표기한다:
```markdown
> ⚠️ **DFEAT(비즈니스 로직 진실원) 0건 — 사용자 동의 하에 없이 진행함.**
> 이 키트로 구현 시 로직이 API/ERD 계약에서만 유추되어 설계 이탈 위험이 있습니다.
> 권장: mc-logi-brainstorming/mc-logi-update 로 DFEAT 설계 → 이 스킬 재실행(SYNC).
```
DFEAT 가 정상 존재하면 이 경고는 출력하지 않는다.

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

카탈로그 수집 후 타입별 fetcher 병렬 실행합니다.
(카탈로그에서 DFEAT 0건이 감지되면 다운로드 전에 별도로 노티하고 진행 여부를 확인합니다.) 계속할까요?"
