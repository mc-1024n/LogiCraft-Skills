# version-tracking.md — 버전 마스터 포맷 + 차이 감지 알고리즘 (화면 키트용)

logicraft 의 각 ITEM 은 `current_version`(정수, 단조 증가) + `last_updated_at`(ISO) +
`change_summary`(변경 서술) + `stale`(bool) 을 제공한다. **별도 해시 불필요** —
`current_version` 정수 비교만으로 변경 감지가 정확하다.

## version-master.md 포맷

경로: `./docs/screen-design/{slug}-{DOMAIN-ID}/version-master.md`

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
| DS-001 | design_system | {디자인시스템명} | 3 | 2026-05-10T09:00Z | false | _shared/design-system.md | UNCHANGED |
| UI-012 | ui_component | {컴포넌트명} | 7 | 2026-05-12T14:00Z | false | _shared/ui-catalog.md | CHANGED |
| SHELL-001 | app_shell | {앱셸명} | 2 | 2026-04-20T10:00Z | false | _shared/shell-nav.md | UNCHANGED |
| NAV-001 | navigation_tree | {내비게이션명} | 5 | 2026-05-01T08:00Z | false | _shared/shell-nav.md | UNCHANGED |
| API-100 | api_endpoint | GET /example | 4 | 2026-05-15T09:00Z | false | _shared/api/API-100.md | NEW |
| CONST-010 | constant | {상수명} | 2 | 2026-04-30T00:00Z | false | _shared/constant/CONST-010.md | UNCHANGED |
| ROLE-001 | permission_role | {역할명} | 1 | 2026-04-01T00:00Z | false | _shared/role/ROLE-001.md | UNCHANGED |
| GUIDE-003 | implementation_guideline | {가이드명} | 6 | 2026-05-16T00:00Z | false | _shared/guideline/GUIDE-003.md | UNCHANGED |
| SCREEN-011 | screen_spec | {화면명} | 12 | 2026-05-16T23:35Z | false | screens/SCREEN-011/SCREEN-011.md | CHANGED |
| SCREEN-012 | screen_spec | {화면명} | 4 | 2026-05-10T10:00Z | false | screens/SCREEN-012/SCREEN-012.md | UNCHANGED |
| UC-031 | use_case | {시나리오명} | 3 | 2026-05-16T23:35Z | false | screens/SCREEN-011/uc/UC-031.md | NEW |
| AC-055 | acceptance | {수용기준명} | 2 | 2026-05-14T09:00Z | true | _retired/AC-055.md | RETIRED |
| ... | | | | | | | |

## Changelog — {YYYY-MM-DDTHH:MMZ} (session {n}, {INITIAL|SYNC})

### NEW ({n})
- API-100 v4 — GET /example 신규 엔드포인트
- UC-031 v3 — {화면명} 시나리오 신규 추가
- ...

### CHANGED ({n})  ← 코드 재반영 필요
- SCREEN-011 **v11 → v12** — <logicraft change_summary 원문>
- UI-012 **v6 → v7** — <change_summary>
- ...

### RETIRED ({n})  ← _retired/ 이동, 코드 제거 검토
- AC-055 (deprecated) — {사유}
- ...

### UNCHANGED ({n})
표 참조 (다운로드 skip, 파일 유지)

## 이전 Changelog 이력
<직전 run 의 Changelog 블록들을 아래로 누적 보존 (append-only)>
```

> Changelog 는 **append-only** — 매 run 새 블록을 "이번 run" 으로 추가하고, 직전 것은
> "이전 Changelog 이력" 으로 내림. git 과 함께 변경 히스토리 추적 가능.

---

## 차이 감지 알고리즘 (INITIAL / SYNC 공통)

```
입력:
  current_catalog = { ITEM_ID: {version, last_updated_at, stale, type, title, status_active} }
                    (fetch 단계에서 get_neighbors + list_items 로 수집)
  local_catalog   = { ITEM_ID: {version, local_file} }
                    (기존 version-master.md "ITEM 버전 표" 파싱)

각 ITEM_ID 판정:
  if id in current and id not in local:
      status = NEW           # 신규 다운로드
  elif id in current and id in local:
      if current.version != local.version:
          status = CHANGED   # 재다운로드 + 배너 + prev_version=local.version
      else:
          status = UNCHANGED # skip (파일 존재 검증만)
  elif id in local and (id not in current_active OR current.status == deprecated/superseded):
      status = RETIRED       # _retired/<type>/ 이동, 삭제 금지

INITIAL 모드 (version-master.md 없음): 모든 current ITEM = NEW
```

### 판정 세부 규칙

- **version 필드 출처**: `list_items` / `get_item` 응답의 `current_version` (정수).
- **RETIRED 식별**: `list_items(include_retired=true)` 의 `retired_items` 에 등장 OR
  current 활성 목록에서 사라짐. 두 경우 모두 RETIRED.
- **CHANGED 인데 version 동일하나 stale 토글**: logicraft 가 stale=true 로 막 바뀐 경우
  → UNCHANGED 로 두되 version-master 표의 stale 컬럼만 갱신 + SCREENS.md 변경알림에 "stale 전파" 1줄.
- **로컬 파일 누락 + UNCHANGED**: 파일이 실제로 없으면 강제 재다운로드(NEW 취급).
- **version 역행** (current < local, 이론상 발생 X): 경고 로깅 + CHANGED 처리 + 사용자 보고.

### ui-catalog.md 버전 집약 규칙

`ui_component` 는 개별 파일이 아니라 카탈로그 1파일(`_shared/ui-catalog.md`)로 집약된다.
버전 표에는 각 UI-NNN 을 개별 행으로 기록하되, local file 컬럼은 모두 `_shared/ui-catalog.md`
를 가리킨다. ui-catalog.md 전체의 CHANGED 판정은 **어느 한 UI-NNN 이라도 CHANGED/NEW 이면**
카탈로그 파일 전체를 재생성한다.

### CHANGED ITEM 파일 배너 (fetcher 가 삽입)

frontmatter `status: CHANGED`, `prev_version: 11` + 본문 최상단:

```markdown
> ⚠️ **버전 변경 감지 — logicraft v11 → v12** (2026-05-16T23:35Z)
> change_summary: <원문 그대로>
> ↳ 요약/구현 노트 재검토 후 작성된 코드에 반영. 직전 요약은 git diff 확인.
```

SCREENS.md 에도 해당 ITEM ID 와 change_summary 를 "변경 알림" 섹션에 1줄씩 기재한다.

### RETIRED 처리 (삭제 금지)

```
_retired/ 이동 규칙:
  공유 ITEM:
    mv _shared/{type}/{ID}.md        _retired/{type}/{ID}.md
    mv _shared/{type}/_raw/{ID}.json _retired/{type}/{ID}.json  (있으면)
  화면별 ITEM (SCREEN / UC / AC):
    mv screens/{SCREEN-NNN}/{ID}.md  _retired/{type}/{ID}.md
    mv screens/{SCREEN-NNN}/_raw/    _retired/{type}/{ID}.json  (있으면)

→ _retired 파일 frontmatter 에 status: RETIRED + retired_at + 사유(change_summary) 추가
→ version-master 표 local file 컬럼을 _retired 경로로 갱신
```

물리 삭제 절대 금지 (전역 정책: 사용자가 만들지 않은 산출물·구현 흔적 보존).

---

## git 권장

산출물 루트가 코드 레포 안이면 `docs/screen-design/` 를 git 으로 함께 버전관리 권장.
CHANGED ITEM 의 직전 요약은 git history 로 자연 보존되므로 별도 백업 불필요.
(스킬은 git 명령 자동 실행 안 함 — 사용자가 커밋. SCREENS.md 에 안내만 기재.)
