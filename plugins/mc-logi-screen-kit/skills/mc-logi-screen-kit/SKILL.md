---
name: mc-logi-screen-kit
description: Logicraft 특정 프로젝트의 특정 화면(screen_spec)과 그 화면이 의존하는 디자인 ITEM 세트(design_system / ui_component / app_shell / navigation_tree / api_endpoint / constant / permission_role / implementation_guideline + 화면별 use_case / acceptance / wireframe / 디자인 렌더)를 ./docs/screen-design/{도메인슬러그}-{DOMAIN-ID}/ 화면 중심 구조로 다운로드 + 버전 추적하는 화면 특화 키트 다운로더. 사용자가 "SCREEN-011 화면 키트 만들어줘", "D002 화면 다운로드", "화면 키트 준비해줘", "logicraft 화면 로컬로 내려받아줘", "화면 키트 동기화해줘" 등을 요청할 때 실행. 결정적 다운로더(bin/download-kit.mjs, 배치 export API-152)로 서버 verbatim 스켈레톤 + 원본 JSON + 렌더 정적파일을 받고, arranger(bin/arrange-screen-kit.mjs)가 화면 중심 레이아웃 + 인덱스로 정리 — LLM 0·초 단위·content-hash 무열화(ADR-026, 옛 logi-implement-fetcher LLM 요약 폐기). ITEM 수정 안 함 — read-only 다운로드.
license: MIT
allowed-tools: Read, Write, Edit, Grep, Glob, Bash, Agent, ToolSearch, AskUserQuestion, TaskCreate, TaskUpdate, TaskList
metadata:
  version: "1.2.0"
  domain: logicraft-orchestration
  triggers: 화면 키트, screen kit, 화면 다운로드, 화면 구현 준비, 화면 키트 동기화, SCREEN-NNN 키트, SCREEN-NNN 다운로드, 화면 로컬 다운, 화면 구현 준비해줘, logicraft 화면 로컬로 내려받아, screen-design 동기화, D001 화면 키트, D002 화면 다운로드
  role: orchestrator-readonly
  scope: logicraft-screen-implementation-prep
  output-format: docs/screen-design/{도메인슬러그}-{DOMAIN-ID}/ 트리 (SCREENS.md + version-master.md + _shared/ + screens/)
  related-skills: mc-logi-screen-implement, mc-logi-implement-kit, mc-logi-update, mc-logi-domain-review
---

# mc-logi-screen-kit — Logicraft Screen Kit Downloader

Logicraft 특정 프로젝트의 화면(screen_spec)과 그 화면이 의존하는 디자인 ITEM 세트를,
**로컬에서 프론트엔드 화면 구현이 바로 가능**하도록 다운로드 + 구현지향 요약 + 버전 추적한다.
**read-only** — logicraft ITEM 절대 수정 안 함.

기존 `mc-logi-implement-kit`(도메인 단위 백+프론트)의 화면(프론트) 특화 버전이다.

## When to Use

- 사용자가 특정 화면 또는 도메인 화면 전체 구현 착수 전 로컬 키트 요청
  (예: "SCREEN-011 화면 키트 만들어줘", "D002 화면 다운로드해줘")
- 이미 받은 화면 키트의 logicraft 변경분 재동기화 (예: "화면 키트 최신화")
- 설계가 logicraft 에서 cascade 된 후 코드 반영 전 변경분 파악 (화면 단위)
- mc-logi-screen-implement 에 줄 "화면 구현 컨텍스트 번들" 생성

## When NOT to Use

- logicraft ITEM 수정 (mc-logi-update)
- 화면 정합 갭 검출 (mc-logi-domain-review)
- 단일 ITEM 조회 (logicraft MCP 직접)
- 실제 코드 작성 (본 스킬은 키트만 생성 — 구현은 mc-logi-screen-implement)
- 도메인 단위 백+프론트 전체 키트 (mc-logi-implement-kit)

## 핵심 원칙

1. ✅ **ITEM 범위**: 화면 핵심 세트 고정 (`core-item-set.md` 공유 ITEM + 화면별 ITEM). Phase 2 가 화면+의존 id 집합을 산출해 다운로더에 `--ids` 로 전달
2. ✅ **산출물**: 서버 verbatim 스켈레톤(.md) + 원본 raw JSON(.json) **둘 다** (요약/의역 0 = 무열화)
3. ✅ **실행**: **결정적 2-스크립트** — `bin/download-kit.mjs`(배치 export API-152, 무열화 전송) + `bin/arrange-screen-kit.mjs`(화면 중심 레이아웃·인덱스 정리, 네트워크 0). 옛 `logi-implement-fetcher`(LLM 요약)는 폐기·폴백용(ADR-026)
4. ✅ **버전 추적**: 각 ITEM 헤더에 `current_version`·`content_hash` + `version-master.md` 마스터 + 재실행 시 NEW/CHANGED/UNCHANGED/RETIRED 판정(다운로더 델타 + run-report)
5. ✅ **read-only**: logicraft 쓰기 도구 호출 금지. 로컬 파일만 생성/갱신
6. ✅ **삭제 안 함**: RETIRED ITEM 도 `_retired/` 로 이동만, 물리 삭제 금지
7. ✅ **ui_component 카탈로그 감지**: 0건이면 SCREENS.md 헤더에 경고 플래그 기록 (arranger 자동)
8. ⚠️ **배포**: `publish_skill`/플러그인 배포 시 **소스 캐리어 `download-kit-src.md`·`arrange-screen-kit-src.md` 를 files[] 에 반드시 포함** — bin/ 이 없어도 Phase 3 가용성 게이트가 캐리어에서 재생성. 배치 export 엔드포인트(API-152)가 대상 서버에 배포돼 있어야 동작(미배포=404→exit 4→fetcher 폴백)

## 디렉터리 구조 (산출물)

```
docs/screen-design/{도메인슬러그}-{DOMAIN-ID}/
├── SCREENS.md                  ← 진입점 (화면 목록 + 공유자산 인덱스 + 빌드 순서 + 카탈로그 상태 플래그 + 변경 알림)
├── version-master.md           ← 버전 마스터 (전 ITEM 버전 표 + run changelog)
├── _shared/
│   ├── design-system.md        ← get_design_md 결과(design.md 형식 원문) + _raw/DS-NNN.json
│   ├── ui-catalog.md           ← ui_component 전체 카탈로그 요약 1파일 (개별 파일 금지)
│   ├── shell-nav.md            ← app_shell + navigation_tree 요약 (화면-셸 경계 명시)
│   ├── api/                    ← api_endpoint 개별 파일 (API-NNN.md + _raw/)
│   ├── constant/               ← constant 개별 파일 (CONST-NNN.md + _raw/)
│   ├── role/                   ← permission_role 개별 파일 (ROLE-NNN.md + _raw/)
│   ├── guideline/              ← implementation_guideline 개별 파일 (GUIDE-NNN.md + _raw/)
│   └── _raw/                   ← DS / UI 원본 JSON (design_system·ui_component 공용)
├── screens/
│   └── SCREEN-NNN/
│       ├── SCREEN-NNN.md       ← screen_spec 구현지향 요약 (frontmatter + 변경 배너)
│       ├── wireframe.html      ← get_static_render 결과 HTML (복수면 wireframe-{render_id}.html / 없으면 _no-wireframe.md)
│       ├── wireframe.css       ← 공통 wireframe.css (get_wireframe_css 결과 — css 없는 와이어프레임 render 용)
│       ├── {render_id}.css     ← per-render 디자인 시안 CSS (get_static_render 의 css 본문 — 해당 render 만; 시안 render 마다 1개)
│       ├── design/              ← screen_design(SD-NNN) 고충실 디자인 렌더 (logicraft 에 SD 있을 때만) — get_design_render 결과
│       │   ├── design-{render_id}.html + design-{render_id}.css   (render_id=와이어프레임과 동일, wireframe.css 미주입)
│       │   └── _sd-meta.md      ← SD-NNN id·version·status·designer·render 목록 (design/ 유무 = SD 존재 여부; implement 가 판단)
│       ├── _raw/SCREEN-NNN.json
│       ├── uc/                 ← 이 화면의 UC-NNN.md
│       └── ac/                 ← 이 화면의 AC-NNN.md
└── _retired/                   ← deprecated/superseded ITEM 이동 (삭제 금지)
    └── {type}/{ID}.md
```

- 폴더명 `{도메인슬러그}-{DOMAIN-ID}`: logicraft `slug` 필드 사용.
  slug 없으면 도메인 title sanitize(공백→`-`, `·/\:*?"<>|` 제거) + `-DOMAIN-XXX` 접미.
- `docs/screen-design/`는 기존 도메인 키트(`docs/design/`)와 분리된 별도 디렉토리.
  같은 레포에 두 키트가 공존 가능.

## 각 ITEM 파일 헤더 (버전 감지 핵심)

모든 요약 `.md` 최상단에 YAML frontmatter (+ CHANGED 시 배너):

```markdown
---
logicraft_item: SCREEN-011
type: screen_spec
version: 12
last_updated_at: 2026-05-16T23:35:04Z
domain: DOMAIN-002
project_id: 95f00d2e-30e8-4426-bc37-9bd85aa969e9
synced_at: 2026-06-20T14:30Z
sync_session: 3
stale: false
status: CHANGED          # synced | NEW | CHANGED | RETIRED
prev_version: 11         # CHANGED 일 때만, 아니면 null
raw: ./_raw/SCREEN-011.json
wireframe: ./wireframe.html
links:
  consumes_apis: [API-100, API-101]
  required_roles: [ROLE-001]
  realizes_use_cases: [UC-031]
  acceptance: [AC-055]
---
```

CHANGED 일 때 frontmatter 직후 배너:

```markdown
> ⚠️ **버전 변경 감지 — logicraft v11 → v12** (2026-05-16T23:35Z)
> change_summary: <logicraft change_summary 원문 그대로>
> ↳ 요약/구현 노트 재검토 후 작성된 코드에 반영. 직전 요약은 git diff 확인.
```

---

## 워크플로우

### Phase 1 — 진입 + 대상 식별

1. **사용자 입력 파싱** (`core-item-set.md` 입력 모드 참조):
   - `DOMAIN-NNN` 명시 → 그 도메인의 활성 screen_spec 전체 다운로드
   - `SCREEN-NNN` 또는 `SCREEN-NNN,SCREEN-MMM,...` 명시 → 지정 화면만 + 공유 의존
   - 도메인명 명시 (예: `영상 관제`) → `list_items(type=domain)` 로 매핑
   - 아무것도 없으면 `AskUserQuestion` 으로 확정:
     ```
     "화면 키트를 생성할 대상을 알려주세요:
      - 도메인 전체: DOMAIN-NNN (예: D002)
      - 특정 화면: SCREEN-NNN (예: SCREEN-011) 또는 복수 (SCREEN-011,SCREEN-012)"
     ```

2. **project_id 식별**:
   - `~/.claude/projects/*/memory/MEMORY.md` 에서 현재 프로젝트 확인
   - 없으면 `list_projects` 결과를 사용자에게 제시해 선택

3. **출력 루트 결정**: `<cwd>/docs/screen-design/` (없으면 생성). cwd 가 코드 레포 루트인지 확인.

4. **재실행 여부 판정**:
   - `docs/screen-design/{slug}-{ID}/version-master.md` 존재 → **SYNC 모드**
   - 없으면 **INITIAL 모드**

5. **진입 멘트 출력** (아래 §진입 멘트 참조)

---

### Phase 2 — 화면 집합 결정 + 카탈로그 수집

#### 2-1. 화면 집합 확정

```python
# DOMAIN-NNN 모드: 도메인 소속 활성 screen_spec 전수
get_item(project_id, DOMAIN-NNN)               # 도메인 본체 (slug·title·도메인명)
get_neighbors(project_id, DOMAIN-NNN)          # backward 링크 = 도메인 소속 ITEM ID 전부
get_related(project_id, DOMAIN-NNN, depth=2, direction="both")  # 2레벨 의존 전개

# 위 결과에서 type=screen_spec 인 것만 추출 → 화면 집합

# SCREEN-NNN[,...] 모드: 사용자 지정 화면만 (이미 확정)
# 공유 의존 범위: 각 화면의 consumes_apis / required_roles 합집합 산출
```

#### 2-2. 공유 ITEM 카탈로그 수집

화면 집합 확정 후 공유 ITEM 범위 산출 (`core-item-set.md` 규칙):

```python
# 공유 ITEM 전수 수집
find_app_shell(project_id)                     # SHELL
find_navigation(project_id)                    # NAV
list_items(type=design_system)                 # DS (프로젝트/도메인 소속)
list_items(type=ui_component, limit=500)       # UI 카탈로그 전체
list_items(type=implementation_guideline)      # GUIDE (applies_to_types 매칭분)

# 화면들의 consumes_apis 합집합 → API 목록
# 화면들의 required_roles 합집합 → ROLE 목록
# 화면/API 의 uses_constant 링크 합집합 + 도메인 소속 CONST → CONST 목록

# ★ 화면별 UC/AC/SD 수집 (다운로더 --ids 에 반드시 포함 — 다른 도메인일 수 있음):
#   get_related(SCREEN, depth=2, direction="both") 로 화면당:
#     - UC = 화면에 references/realizes 로 연결된 use_case
#     - AC = 그 UC 들의 covered_by acceptance (depth-2 — AC 는 화면에 직접 안 붙음)
#     - SD = 화면을 designs 하는 screen_design (고충실 디자인)
#   (UC/AC 는 DOMAIN 경계를 넘을 수 있으므로 domain 스코프가 아니라 id 로 명시 수집)

# 각 ITEM 의 id / type / current_version / last_updated_at / stale / change_summary / slug 수집
# → current_catalog 완성
# → ★ id_set = 위 전부의 id CSV (SCREEN + API + ROLE + CONST + GUIDE + UC + AC + SD + DS + UI + SHELL + NAV)
#    = Phase 3 다운로더 --ids 인자. screen_ids = 피벗 SCREEN CSV = arranger --screens 인자.
```

`ui_component` **0건 감지**:
- `catalog_empty_flag = True` 로 기록
- Phase 4 SCREENS.md 헤더에 경고 플래그 + DS archetype 기재 (core-item-set.md §카탈로그 감지)

큰 응답(>30KB)은 `Bash` + `python -c "import json,sys; data=json.load(sys.stdin); ..."` (encoding='utf-8') 파싱.

---

### Phase 2.5 — 버전 차이 산출 (SYNC 모드만)

1. 기존 `version-master.md` 파싱 → **로컬 카탈로그(local_catalog)**: ITEM ID → version
2. `current_catalog` 와 비교해 상태 분류 (`version-tracking.md` 알고리즘):

| 상태 | 조건 | 처리 |
|---|---|---|
| **NEW** | current 에 있고 local 에 없음 | 신규 다운로드 |
| **CHANGED** | 양쪽 존재, `current_version` 다름 | 재다운로드 + 변경 배너 + prev_version 기록 |
| **UNCHANGED** | 양쪽 존재, version 동일 | 다운로드 skip — 파일 존재만 검증 |
| **RETIRED** | local 에 있고 current 활성 목록에 없음/deprecated | `_retired/{type}/` 이동 + version-master 표기 (삭제 X) |

3. INITIAL 모드는 전부 NEW 취급.
4. stale=true 토글만 발생한 ITEM: UNCHANGED 로 두되 version-master 표의 stale 컬럼만 갱신 + SCREENS.md "변경 알림"에 "stale 전파" 1줄.
5. RETIRED ITEM 이동 (`version-tracking.md` §RETIRED 처리 규칙):
   - `_shared/{type}/{ID}.md` → `_retired/{type}/{ID}.md`
   - `screens/{SCREEN-NNN}/{ID}.md` → `_retired/{type}/{ID}.md`
   - 이동 후 frontmatter 에 `status: RETIRED + retired_at + 사유` 추가

---

### Phase 3 — 결정적 다운로드 + 정리(arrange) (LLM 0)  ★ ADR-026

옛 `logi-implement-fetcher`(LLM 요약, 30~40% 열화) 병렬 방식을 **결정적 2-스크립트**로 대체한다:
1. **`bin/download-kit.mjs`** — 배치 export(API-152)로 원본 JSON + 서버 verbatim 스켈레톤 + content_hash + 그래프 links + **렌더 정적파일**(와이어프레임·SD 디자인, css self-contain)을 받아 **평평한 스테이징**(`<kit>/.staging/{type}/…`)에 기록. 델타(version/hash)로 변경분만.
2. **`bin/arrange-screen-kit.mjs`** — 네트워크 0·순수 로컬. 스테이징을 **screen-implement 가 기대하는 화면 중심 레이아웃**(`screens/SCREEN-NNN/…` + `_shared/…`)으로 재배치하고, `SCREENS.md`·`version-master.md`·`_shared/ui-catalog.md`·`_shared/shell-nav.md`·`_shared/design-system.md` 를 결정적 합성. 본문은 verbatim(요약/변형 0 → 열화 원천 차단).

**★ 가용성 게이트 (Phase 3 진입 시 먼저 판정)**:
1. **스크립트 탐색 + (없으면) 재생성 문의**: `Glob("**/mc-logi-screen-kit/bin/download-kit.mjs")` 와 `Glob("**/mc-logi-screen-kit/bin/arrange-screen-kit.mjs")`.
   - 둘 다 있으면 결정적 경로로 진행.
   - 하나라도 없으면 `AskUserQuestion`: ① **지금 생성하고 결정적 다운로드로 진행 (권장)** — 빠르고 무열화 / ② **옛 fetcher 방식** — 느리고 30~40% 열화.
     - **①(생성) 선택 시**: 없는 스크립트마다 `Glob("**/mc-logi-screen-kit/download-kit-src.md")`·`Glob("**/mc-logi-screen-kit/arrange-screen-kit-src.md")` → Read → 그 안의 ```js 코드블록 **전체를 한 글자도 바꾸지 말고** `<스킬 디렉터리>/bin/<파일>` 로 Write(부모 dir 생성) → `node --check` 로 문법 확인 → 정상이면 진행. (download-kit.mjs 는 `**/mc-logi-implement-kit/bin/download-kit.mjs` 에 있으면 그걸 써도 됨 — 동일 파일.)
     - **②(옛 방식) 선택 시**: 이 Phase 아래 옛 fetcher 절차로 폴백.
     - 캐리어마저 없으면 → 생성 불가 → 옛 fetcher 폴백 + "다운로더/arranger·소스 캐리어 미배포" 보고.
2. **환경**: node 미가용 → 폴백. `LOGICRAFT_API_KEY`(lc_ 키, MCP 와 동일) 미설정 → 사용자에게 설정 요청. base 는 개발기 `LOGICRAFT_API_BASE`(기본 `http://localhost:14000/api`), 상용은 해당 서버.

**실행** (Phase 2 에서 확정한 **화면+공유 의존 ITEM id 집합**을 `--ids` 로 전달 — 화면 집합만 정확히 받도록):

```bash
KIT=<cwd>/docs/screen-design/{slug}-{DOMAIN}
IDS=<Phase2 가 산출한 id CSV: SCREEN들 + consumes_apis/required_roles/uses_constant + guideline + UC(references/realizes) + AC(UC covered_by, depth-2) + SD(designs) + DS + UI + SHELL + NAV>
SCREENS=<피벗 SCREEN id CSV>

# 1) 다운로드 → 평평한 스테이징 (+ run-report)
LOGICRAFT_API_KEY=<lc_ 키> LOGICRAFT_API_BASE=<base> \
  node <download-kit.mjs> --project <uuid> --out "$KIT/.staging" --ids "$IDS" --report "$KIT/.staging/.run-report.json"

# 2) 정리(arrange) → 화면 키트 레이아웃 + 인덱스 (네트워크 0)
node <arrange-screen-kit.mjs> --staging "$KIT/.staging" --out "$KIT" \
  --report "$KIT/.staging/.run-report.json" --project <uuid> \
  --domain <DOMAIN-NNN> --domain-name "<도메인명>" --slug <slug> --sync-session <n> --screens "$SCREENS"
```

**종료코드 분기** (다운로더): **0**=성공(이어서 arrange) · **4**=엔드포인트 미배포(구버전 서버, `/kit-export` 없음) → **옛 fetcher 폴백** · **2**=네트워크/인증 오류 → **사용자 보고 + 수정 요청**(자동 폴백 금지 — 고칠 설정 문제를 느린·열화 폴백으로 숨기지 말 것) · **1/3**=인자/무결성 오류 → stderr 확인. arranger 성공 출력은 `✅ arrange 완료 — 화면 N …`.

- `--ids` 집합이 커도 다운로더가 40개씩 청크로 나눠 호출(414 회피). UNCHANGED 는 스테이징에 유지되어 재다운로드 skip.
- 렌더 css: 와이어프레임의 공통 `/api/static/wireframe/wireframe.css` 는 다운로더가 self-contain(상대 `wireframe.css`)하고, SD 디자인 css_url 은 함께 받아 `design-{rid}.css` 로 arranger 가 상대화 → **오프라인 렌더 가능**.
- `_no-wireframe.md`·`_sd-meta.md`·orphan 처리는 arranger 가 결정적 수행. UC/AC 는 screen→UC(직접)·screen→UC→AC(depth-2)로 화면 아래 중첩.

> ⚠️ **옛 `logi-implement-fetcher`(LLM 요약) 방식은 폐기(ADR-026).** ITEM 본문 "요약"은 서버 결정적 스켈레톤이 대체(의역 0). 아래 fetcher 절차는 **다운로더/arranger 미배포·실패 시 폴백 참고용**으로만 남긴다. 폴백 사용 시 Phase 5 보고에 "⚠️ 다운로더 미가용 — fetcher 폴백(느리고 30~40% 열화)" 명시.

---

#### (폴백 참고) 옛 타입별 병렬 fetcher

다운로드 필요 타입별로 **한 메시지에 병렬 Agent** (다운로더/arranger 미가용 시에만):

```python
Agent(subagent_type="logi-implement-fetcher",
      description="Fetch DOMAIN-002 screen_spec kit (SCREEN-011, SCREEN-012)", prompt=...)
# ... 타입 수만큼 (상한 8 병렬, 초과 시 배치 분할)
```

#### ★ Agent 이름 해석 + 등록 fallback

`logi-implement-fetcher` 에이전트는 **설치 방식에 따라 등록 이름이 다르다**:
- **플러그인 설치** (`/plugin install mc-logi-implement-kit@logicraft`): 에이전트가 `agents/logi-implement-fetcher.md` 로 동봉되어 **scoped name `mc-logi-implement-kit:logi-implement-fetcher`** 로 자동 등록
- **user/project scope** (개발 환경, `~/.claude/agents/`): bare name `logi-implement-fetcher`

다음 순서로 시도 (절대경로 하드코딩 금지 — 설치 위치 무관):

**Case 1 — 전용 에이전트 호출** (첫 성공 채택):
1. `subagent_type="mc-logi-implement-kit:logi-implement-fetcher"` (플러그인 scope)
2. 실패 시 `subagent_type="logi-implement-fetcher"` (user/project scope)

**Case 2 — 둘 다 `Agent type ... not found`** → general-purpose 로 fallback + 에이전트 정의를 **동적 탐색**해 인라인:

```python
# 1) 에이전트 정의 파일을 Glob 으로 탐색 (설치 위치 무관, 절대경로 박지 말 것)
#    Glob("**/agents/logi-implement-fetcher.md") → 첫 결과를 Read → agent_md_content
# 2) summary-templates·checklist 는 메인이 이미 읽어둔 내용을 인라인
#    (스킬 디렉토리 상대: summary-templates.md, checklist.md)
Agent(
  subagent_type="general-purpose",
  description="Fetch DOMAIN-002 <type> kit (fallback)",
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

각 fetcher prompt 에 포함 (`summary-templates.md` 의 해당 타입 섹션 + `checklist.md` 주입):

```yaml
# fetcher 입력 YAML 구조
project_id: {uuid}
domain_id: {DOMAIN-NNN}
domain_slug: {slug}
output_root: {cwd}/docs/screen-design/{slug}-{DOMAIN-NNN}
sync_session: {n}
synced_at: {ISO now}
kit_type: screen   # implement-kit 과 구분용 메타
```

★ **타입별 에이전트 선택 (allowed-tools 제약 — 반드시 준수)**: `logi-implement-fetcher` 의 allowed-tools 는 `get_item`/`list_items`/`get_neighbors`/`get_related`/`analyze_impact`/`get_item_schema`/`get_implementation_coverage`/`get_logicraft_guide` 9개 조회 도구뿐이다. **디자인·와이어프레임 전용 도구가 필요한 타입은 이 에이전트로 불가**(allowed-tools 화이트리스트는 ToolSearch 로도 못 넘는다 — checklist 의 'deferred 선로드' 룰은 ToolSearch 로 풀리는 deferred 한정):

- **`design_system`** (`get_design_md` 필요) · **`screen_spec`** (`get_static_render`·`get_wireframe_css` + SD 탐색 `list_items`·`get_item` 필요; SD 본문은 `get_design_render` **있으면**) → ★ **`general-purpose` 로 디스패치**. 프롬프트 0단계에서 `ToolSearch("select:mcp__logicraft__get_design_md")` 또는 `ToolSearch("select:mcp__logicraft__get_static_render,mcp__logicraft__get_wireframe_css,mcp__logicraft__list_items,mcp__logicraft__get_item,mcp__logicraft__get_design_render")` 로 로드(★ `get_design_render` 는 미배포일 수 있음 — 로드 실패 시 (B)의 미배포 fallback 적용).
- **그 외** (`ui_component`·`app_shell`·`navigation_tree`·`api_endpoint`·`constant`·`permission_role`·`use_case`·`acceptance`) → `get_item`/`list_items` 만으로 충분 → `logi-implement-fetcher` 재사용. (app_shell/navigation_tree 는 메인이 Phase 2 에서 `find_app_shell`/`find_navigation` 으로 확보한 SHELL/NAV id 를 fetcher 에 넘기고, fetcher 는 `get_item(SHELL-NNN/NAV-NNN)` 으로 받는다 — fetcher 는 find_* 권한이 없다.)

타입별 **화면 키트 전용 지시** (★ 공통: fetcher 가 쓸 logicraft 도구가 deferred 면 먼저 `ToolSearch("select:mcp__logicraft__<도구명>")` 로 로드 — 도구 없다고 단정해 다른 도구로 대체 금지. `_raw` JSON 은 item 객체 1개를 단일 JSON 으로 저장(MCP 래퍼·복수 객체 이어붙이기 금지)):

| 타입 | fetcher 추가 지시 |
|---|---|
| `screen_spec` | **(A) 와이어프레임**: `get_static_render(project_id, SCREEN-NNN)`(deferred 면 ToolSearch 선로드) → renders[] 취득. **각 render = `html` + (옵션) `css`(본문)·`css_url`**. count 0 이면 `_no-wireframe.md` 생성. html 있는 항목만 `wireframe.html`(단수) 또는 `wireframe-{render_id}.html`(복수) 저장. html null 항목은 건너뛰고 SCREENS.md 에 "파일 누락" 표기. **★ CSS 는 render 별 2-갈래로 판정**: ① render 에 `css` 필드 있음 = per-render 디자인 시안 → 그 `css` 본문을 `{render_id}.css` 로 저장(html 의 링크가 이미 상대 `{render_id}.css` 라 **치환 불필요**). ② `css` 없음 = 공통 wireframe.css 사용(와이어프레임) → 그 html 의 `/api/static/wireframe/wireframe.css` 를 상대 `wireframe.css` 로 치환. **②가 1건이라도 있을 때만** `get_wireframe_css()`(deferred 면 ToolSearch 선로드) 1회로 `wireframe.css` 저장(전부 ①이면 생략). spec 텍스트 정제 룰 적용. (sanitize 가 `<script>` 제거 → 시안은 무 JS·CSS-only 전제.) **(B) ★ SD 고충실 디자인(있으면)**: 이 SCREEN 을 `designs` 하는 `screen_design`(SD-NNN) 을 찾는다 — `list_items(type=screen_design, project_id)` 에서 `data.designs_screen==SCREEN-NNN` (또는 `get_neighbors(SCREEN-NNN)` backward `designs`). **SD 없거나 renders 0건이면 `design/` 폴더 생성 안 함**(implement 가 부재로 감지해 가이드). **SD 있으면**: ① **메타** = `get_item(SD-NNN).data.renders[]`(id·surface·label·url·css_url) + current_version·status·designer → `_sd-meta.md` 작성(항상). ② **본문(html/css) 다운로드**: `get_design_render` 가 **있으면**(`ToolSearch("select:mcp__logicraft__get_design_render")` 로 선로드 시도) render 별 html+css 취득 → `design/design-{render_id}.html` + `design-{render_id}.css` 저장(css link 상대화). ★ **`get_design_render` 미배포면**(현재 logicraft 는 `upload_design_render`(쓰기)만 있고 SD 읽기 도구 미제공일 수 있음) → **로컬 `design/` 에 파일이 이미 있으면**(= mc-logi-screen-design 산출 = SD 업로드 원본, 동일) **그대로 두고** `_sd-meta.md` 에 'SD 본문 다운로드 도구 미배포 — 로컬 design 스킬 산출물 사용' 명시, **없으면** url 만 `_sd-meta.md` 에 기록하고 본문은 비움(도구 배포 후 재SYNC). SD 의 current_version 을 version-master 표에 기록해 재SYNC 시 디자인 변경 감지. |
| `design_system` | `get_design_md(DS-NNN)`(deferred 면 ToolSearch 선로드 — get_item 토큰으로 대체 금지) 결과를 design-system.md 에 원문 그대로 저장. 의역 금지. |
| `ui_component` | 카탈로그 1파일(ui-catalog.md)에 집약. 개별 파일 금지. 0건이면 catalog_empty 상태 YAML 반환. |
| `app_shell` | `find_app_shell` 결과. `navigation_tree` 와 합산해 shell-nav.md 1파일. |
| `navigation_tree` | `find_navigation` 결과. shell-nav.md 에 NAV 섹션으로 합산. |
| `use_case`, `acceptance` | 해당 화면의 `screens/{SCREEN-NNN}/uc/` 또는 `ac/` 에 저장. |

fetcher 책무: ITEM 별 `get_item` → 원본 `_raw/<ID>.json` 저장 → 해당 타입 템플릿으로 구현지향 `.md` 요약 작성(frontmatter + 변경 배너 포함) → STEP-OUT YAML 반환.

---

### Phase 4 — SCREENS.md + version-master.md + 산출물 (★ arranger 가 자동 생성)

> **결정적 경로에서는 `SCREENS.md`·`version-master.md`·`_shared/{ui-catalog,shell-nav,design-system}.md` 를 `arrange-screen-kit.mjs` 가 이미 생성한다** — 메인은 재작성하지 않고 **존재·건수만 검증**하고 Phase 5 로 보고한다. 아래 4-1/4-2 템플릿은 **arranger 산출 형식의 참고**이자 **폴백(옛 fetcher) 경로에서 메인이 직접 작성할 때의 규격**이다.

#### 4-1. version-master.md 형식 (`version-tracking.md` 포맷 — 폴백 시 메인 작성)

```markdown
# Version Master — {도메인명} ({DOMAIN-ID}) — 화면 키트

| 항목 | 값 |
|---|---|
| Project | {프로젝트명} |
| project_id | {UUID} |
| Domain | {DOMAIN-ID} {도메인명} |
| 다운로드 화면 | {SCREEN-NNN, SCREEN-MMM, ...} 또는 "도메인 전체" |
| Last sync | {YYYY-MM-DDTHH:MMZ} (session {n}) |
| sync_session | {n} |
| Mode (this run) | INITIAL | SYNC |
| 출력 루트 | ./docs/screen-design/{slug}-{DOMAIN-ID}/ |

## ITEM 버전 표
| ITEM ID | type | title | version | last_updated_at | stale | local file | status |
|---|---|---|---|---|---|---|---|
| DS-NNN | design_system | ... | n | ... | false | _shared/design-system.md | ... |
| ...    |               |     |   |     |       |                          |     |

## Changelog — {ISO} (session {n}, {INITIAL|SYNC})
### NEW ({n})
### CHANGED ({n})  ← 코드 재반영 필요
### RETIRED ({n})  ← _retired/ 이동, 코드 제거 검토
### UNCHANGED ({n}) — 표 참조
## 이전 Changelog 이력
```

Changelog 는 **append-only** — 매 run 새 블록 추가, 기존은 "이전 Changelog 이력" 으로 내림.

`ui-catalog.md` 버전 집약 규칙: 버전 표에는 각 UI-NNN 을 개별 행으로 기록하되 local file 은 모두 `_shared/ui-catalog.md`. 어느 한 UI-NNN 이라도 CHANGED/NEW 이면 카탈로그 전체 재생성.

#### 4-2. SCREENS.md 형식 (바이브코딩 진입점 — arranger 자동 생성; 폴백 시 메인 작성)

`mc-logi-implement-kit` 의 `IMPLEMENTATION.md` 에 대응하는 화면 키트 진입점.

```markdown
# {도메인명} 화면 키트 — SCREENS.md

> 이 파일이 화면 구현의 진입점이다. mc-logi-screen-implement 는 이 파일부터 읽는다.
> 키트는 read-only 산출물 — **직접 수정 금지**. 갱신은 mc-logi-screen-kit 재실행.

## 키트 현황

| 항목 | 값 |
|---|---|
| Domain | {DOMAIN-ID} {도메인명} |
| last sync | {YYYY-MM-DD} (session {n}) |
| 화면 수 | {n}개 |
| ui_component 카탈로그 | {populated N건 | ⚠️ 비어있음 — implement Phase 0.5 에서 시드 필요} |
| 출력 루트 | ./docs/screen-design/{slug}-{DOMAIN-ID}/ |

<!-- ui_component 0건이면 아래 경고 블록 삽입 -->
> ⚠️ **ui_component 카탈로그 비어있음** — mc-logi-screen-implement Phase 0.5 에서 시드 필요
> DS archetype: {design_system 이름 또는 "미확인"}
> 시드 출처 후보: A) 레포 컴포넌트 코드 추출 / B) 라이브러리 표준 / C) apply_design_preset(seed_components=true)

## 화면 목록

| SCREEN-ID | 화면명 | 상태 | 와이어프레임 | consumes_apis | required_roles | 비고 |
|---|---|---|---|---|---|---|
| SCREEN-NNN | {화면명} | NEW\|CHANGED\|UNCHANGED | ✅\|⚠️없음 | API-NNN, ... | ROLE-NNN | |

## 공유 자산 인덱스

| type | 파일 | 건수 | 상태 |
|---|---|---|---|
| design_system | _shared/design-system.md | 1 | {status} |
| ui_component | _shared/ui-catalog.md | {n} | {populated\|empty} |
| app_shell + nav | _shared/shell-nav.md | 1+1 | {status} |
| api_endpoint | _shared/api/ | {n} | {status} |
| constant | _shared/constant/ | {n} | {status} |
| permission_role | _shared/role/ | {n} | {status} |
| implementation_guideline | _shared/guideline/ | {n} | {status} |

## 빌드 순서 (mc-logi-screen-implement 참조)

> "공유 자산 먼저, 화면 단위 점진" 원칙 (`core-item-set.md` §빌드 순서 참조)

### Phase 1 — 공유 자산 셋업

1. 제약 흡수: guideline/ → constant/ → design-system.md 순
2. 디자인 시스템 (DS): _shared/design-system.md
3. UI 컴포넌트 카탈로그: _shared/ui-catalog.md (0건이면 Phase 0.5 선행)
4. 앱 셸 / 내비게이션: _shared/shell-nav.md
5. API 계약 / 상수 / 역할: _shared/api/ + _shared/constant/ + _shared/role/

### Phase 4 — 화면별 점진

화면 하나씩 아래 순서로 처리:

| 순서 | 화면 | screen_spec | 와이어프레임 | UC | AC |
|---|---|---|---|---|---|
| 1 | SCREEN-NNN — {화면명} | screens/SCREEN-NNN/SCREEN-NNN.md | wireframe.html | uc/ | ac/ |
| 2 | SCREEN-MMM — {화면명} | ... | | | |

## 변경 알림 (SYNC 모드 — 코드 재반영 필요)

<!-- CHANGED/RETIRED ITEM 이 있을 때만 이 섹션 존재 -->
| ITEM | type | v | change_summary |
|---|---|---|---|
| SCREEN-NNN | screen_spec | v11→v12 | {change_summary 원문} |
| API-NNN | api_endpoint | v4→v5 | {change_summary 원문} |

## RETIRED (logicraft 에서 폐기 — _retired/ 이동)

- {ID} ({type}) — {사유} — 코드 제거 검토 필요

## git 권장

`docs/screen-design/` 를 git 으로 함께 버전관리 권장.
CHANGED ITEM 의 직전 요약은 git history 로 자연 보존.
```

---

### Phase 4.5 — 프로젝트 CLAUDE.md 화면 키트 블록 등록 (`claude-md-block.md` 규약)

키트는 `docs/screen-design/` 에만 있으면 후속 세션이 존재를 모른다 — 레포 루트 `CLAUDE.md` 의
`<!-- mc-logi-screen-kit:start/end -->` 마커 구간에 키트 표·작업 규칙·도메인별 주의 포인터를 작성/갱신.

1. `claude-md-block.md` (스킬 디렉토리 상대) 를 읽고 템플릿·필드 추출 출처·병합 규칙을 따른다.
2. CLAUDE.md 없으면 생성, 있으면 **마커 구간만** 교체 (사용자 작성 내용 불가침).
3. 멀티 도메인 레포면 기존 블록의 타 도메인 행 보존 + 이번 도메인 행 추가/갱신.
4. 기존 `<!-- mc-logi-kit:start/end -->` (도메인 키트 블록)와 **충돌 없이 공존** — 서로의 마커 구간 절대 건드리지 않음.
5. SYNC 에서 CHANGED/RETIRED 가 있었으면 해당 도메인 행 "도메인별 주의" 칸에 `⚠️ 변경 N건 코드 재반영 필요` 표식.

---

### Phase 5 — 결과 보고

Markdown 표로 사용자에게 (CLAUDE.md 블록 등록/갱신 여부 1줄 포함):

```markdown
# {DOMAIN-ID} {도메인명} 화면 키트 ({INITIAL | SYNC} 모드)

## 요약
- 출력: ./docs/screen-design/{slug}-{DOMAIN-ID}/
- 화면: {n}건 (SCREEN-NNN, SCREEN-MMM, ...)
- 공유 ITEM: DS 1 / UI {n} / SHELL 1 / NAV 1 / API {n} / CONST {n} / ROLE {n} / GUIDE {n}
- 화면별 ITEM: screen_spec {n} / UC {n} / AC {n} / wireframe {n}
- 이번 run: NEW {n} / CHANGED {n} / UNCHANGED {n} / RETIRED {n}
- ui_component 카탈로그: {populated N건 | ⚠️ 비어있음 — Phase 0.5 시드 필요}
- CLAUDE.md 블록: {신규 등록 | 갱신 완료}
- 진입점: SCREENS.md (빌드 순서 + 공유자산 인덱스 + 카탈로그 상태)

## 변경 감지 (코드 재반영 필요)
| ITEM | type | v | change_summary |
|---|---|---|---|
| ... | ... | ...→... | ... |

## RETIRED (logicraft 에서 폐기 — _retired/ 이동)
- {ID} ({type}) — 코드 제거 검토

→ 화면 구현: mc-logi-screen-implement 로 SCREENS.md 부터 읽고 빌드 순서대로 진행
→ 재동기화: 이 스킬 재실행 시 변경분만 갱신
```

---

### Phase 6 — 메모리 저장 (종료 시 사용자 문의)

작업 완료 후 사용자에게 메모리 저장 여부 문의 (mc-logi-update 정책 따름).
저장 시: `~/.claude/projects/<project>/memory/` 에 키트 생성 기록 + MEMORY.md 인덱스 1줄.
사용자가 "저장하지 마" 시 skip.

---

## logi-implement-fetcher 호출 패턴 (화면 키트 버전)

```python
Agent(
  subagent_type="logi-implement-fetcher",   # 또는 mc-logi-implement-kit:logi-implement-fetcher
  description=f"Fetch {domain_id} {type} kit (screen-kit)",
  prompt=f"""
당신은 logi-implement-fetcher 입니다. 아래 타입의 ITEM 을 화면 키트로 다운로드+요약하세요.

# 입력
project_id: {project_id}
domain_id: {domain_id}
domain_slug: {domain_slug}
item_type: {type}
output_root: {cwd}/docs/screen-design/{domain_slug}-{domain_id}
sync_session: {n}
synced_at: {iso_now}
kit_type: screen

# 처리 대상 (status 포함)
{items_yaml}   # [{id, status, prev_version, current_version, stale}]

# 타입별 요약 포맷 (summary-templates.md 의 {type} 섹션)
{template_section}

# 공통 체크리스트
{checklist_content}

# 화면 키트 추가 지시 (타입별)
{screen_kit_type_instruction}  # 위 Phase 3 표의 "fetcher 추가 지시" 해당분

# 출력
- 각 NEW/CHANGED ITEM: get_item → _raw/{id}.json + 해당 경로의 .md (frontmatter+배너)
- UNCHANGED: 파일 존재 검증만, 없으면 다운로드
- screen_spec: get_static_render + get_wireframe_css 로 wireframe 처리 + (SD 있으면) list_design_renders/get_design_render 로 design/ 다운로드 포함
- design_system: get_design_md 결과 원문 저장
- ui_component: ui-catalog.md 1파일 집약 (개별 파일 금지)
- 완료 후 STEP-OUT YAML 1개만 출력하고 종료. 자유 텍스트 금지.
""")
```

---

## 병렬 실행 정책

- 다운로드 필요 타입은 한 메시지에 동시 호출 (상한 8 병렬)
- 8 초과 시 타입을 2 배치로 분할 순차
- UNCHANGED 만 있는 타입은 fetcher 생략 (메인이 파일 존재만 검증)
- screen_spec 타입은 화면 수에 따라 1 fetcher 에 묶어 처리 (화면별 분할 불필요 — 화면 수 ≤ 10 기준)
- 단일 거대 ITEM(screen_spec/wireframe 70KB+)은 fetcher 내부에서 Bash python 파싱

---

## 에러 처리

| 에러 | 대응 |
|---|---|
| fetcher YAML 파싱 실패 | 1회 재시도 → 실패 시 해당 타입 skip + 보고 |
| get_item 응답 큼(>30KB) | fetcher 가 Bash python 파싱 |
| get_static_render count 0 | `_no-wireframe.md` 플래그 파일 생성 + SCREENS.md "와이어프레임 없음" 표기 |
| get_static_render html null | 해당 항목 건너뜀 + SCREENS.md 에 "파일 누락" 표기 (다른 renders 는 계속 저장) |
| ui_component 0건 | SCREENS.md 헤더에 경고 플래그 기재 (정상 처리 — Phase 0.5 에서 시드 예정) |
| version-master.md 파싱 실패 | 백업 후 INITIAL 모드로 폴백 + 사용자 경고 |
| 도메인/화면 ID 잘못 | AskUserQuestion 재확인 |
| cwd 가 레포 아님 | 사용자에게 출력 경로 확인 요청 |
| SCREEN 의 domain_id 비어있음 | get_neighbors 역추적으로 도메인 추론; 불가 시 프로젝트 레벨 처리 + 사용자 알림 |
| MCP 도구 다운 | ToolSearch 재시도 → 실패 시 부분 보고 후 중단 |

---

## read-only 보장

본 스킬은 logicraft **조회 도구만** 사용:
`get_item`, `list_items`, `get_neighbors`, `get_related`, `get_design_md`,
`list_static_renders`, `get_static_render`, `get_wireframe_css`, `list_design_renders`, `get_design_render`, `find_app_shell`, `find_navigation`, `find_constant`,
`find_ui_component`, `analyze_impact`, `get_implementation_coverage`,
`list_unimplemented`, `get_item_schema`, `get_logicraft_guide`.

**쓰기 도구(create_item / update_item / register_* / propose_change /
mark_implementation / upload_static_render / create_implementation_record /
기타 모든 변경 도구) 절대 호출 금지.**

logicraft 변경은 mc-logi-update 별도 사용.
로컬 파일 시스템만 변경 (Write / Bash mkdir / Bash mv).

---

## 호출 예시

### 예시 1: 최초 화면 키트 생성 (도메인 전체)
```
사용자: "D002 화면 다운로드해줘"
→ Phase 1: DOMAIN-002, project=KLID 2차, INITIAL 모드
→ Phase 2: get_neighbors + find_app_shell/nav + list_items → 화면 6개 + 공유 ITEM 수집
→ Phase 3: 8 타입 병렬 fetcher (전부 NEW)
   - screen_spec: 6화면 + wireframe 처리
   - design_system: get_design_md 원문 저장
   - ui_component: ui-catalog.md 집약
   - api/const/role/guide/shell+nav: 각 fetcher
→ Phase 4: SCREENS.md + version-master.md 작성
→ Phase 4.5: CLAUDE.md 블록 등록
→ Phase 5: 보고 → 사용자는 SCREENS.md 부터 mc-logi-screen-implement 진행
```

### 예시 2: 특정 화면 키트 생성
```
사용자: "SCREEN-011 화면 키트 만들어줘"
→ Phase 1: SCREEN-011, INITIAL 모드
→ Phase 2: SCREEN-011 의 consumes_apis/required_roles 합집합 → 공유 ITEM 범위 산출
→ Phase 3: 병렬 fetcher (SCREEN-011 + 공유 의존 타입)
→ Phase 4: SCREENS.md (화면 1개) + version-master.md 작성
→ Phase 5: 보고
```

### 예시 3: 재동기화 (버전 변경 감지)
```
사용자: "화면 키트 최신화해줘"
→ Phase 1: SYNC 모드 (version-master.md 존재)
→ Phase 2.5: 현재 vs 로컬 카탈로그 diff → CHANGED 3 / NEW 1 / RETIRED 1
→ Phase 3: 변경분 있는 타입만 fetcher → CHANGED 에 변경 배너 삽입
→ Phase 4: version-master changelog 갱신 + SCREENS.md 변경 알림 섹션 추가
→ Phase 4.5: CLAUDE.md 블록에 "⚠️ 변경 N건 코드 재반영 필요" 표식
→ Phase 5: "3건 코드 재반영 필요" 강조 보고
```

---

## 진입 멘트

"mc-logi-screen-kit 시작합니다.

대상: `<DOMAIN-ID | SCREEN-NNN,...>` / 프로젝트: `<project>`
모드: `<INITIAL | SYNC>` / 출력: `./docs/screen-design/<slug>-<ID>/`
ITEM 범위: 화면 핵심 세트 (공유: DS/UI/SHELL/NAV/API/CONST/ROLE/GUIDE + 화면별: SCREEN/UC/AC/wireframe)
모드: read-only (logicraft 수정 없음, 다운로드만)

카탈로그 수집 후 타입별 fetcher 병렬 실행합니다. 계속할까요?"
