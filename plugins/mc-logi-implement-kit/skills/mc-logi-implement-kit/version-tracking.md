# version-tracking.md — 버전 마스터 포맷 + 차이 감지 알고리즘

logicraft 의 각 ITEM 은 `current_version`(정수, 단조 증가) + `last_updated_at`(ISO) +
`change_summary`(변경 서술) + `stale`(bool) 을 제공한다. **별도 해시 불필요** —
`current_version` 정수 비교만으로 변경 감지가 정확하다.

## version-master.md 포맷

경로: `./docs/design/{slug}-{DOMAIN-ID}/version-master.md`

```markdown
# Version Master — {도메인명} ({DOMAIN-ID})

| 항목 | 값 |
|---|---|
| Project | KLID 2차 - 관제지원시스템 고도화 |
| project_id | 95f00d2e-30e8-4426-bc37-9bd85aa969e9 |
| Domain | DOMAIN-002 영상·메타 수집 |
| Domain item version | 35 |
| Last sync | 2026-05-18T14:30Z (session 5) |
| Mode (this run) | SYNC |
| 출력 루트 | ./docs/design/domain-video-metadata-ingestion-DOMAIN-002/ |

## ITEM 버전 표

| ITEM ID | type | title | version | last_updated_at | stale | local file | status |
|---|---|---|---|---|---|---|---|
| DOMAIN-002 | domain | 영상·메타 수집 | 35 | 2026-05-16T23:35Z | true | _domain.md | UNCHANGED |
| DFEAT-064 | domain_feature | 영상 수집 트리거 | 12 | 2026-05-16T23:35Z | false | domain_feature/DFEAT-064.md | CHANGED |
| API-273 | api_endpoint | POST /ingest | 4 | 2026-05-15T09:00Z | false | api_endpoint/API-273.md | NEW |
| API-191 | api_endpoint | (deprecated) | 6 | 2026-04-30T00:00Z | true | _retired/api_endpoint/API-191.md | RETIRED |
| ... | | | | | | | |

## Changelog — 2026-05-18T14:30Z (session 5, SYNC)

### NEW (4)
- API-273 v4 — POST /ingest 신규 엔드포인트
- ...

### CHANGED (9)  ← 코드 재반영 필요
- DFEAT-064 **v11 → v12** — <logicraft change_summary 원문>
- SEQ-020 **v8 → v9** — <change_summary>
- ...

### RETIRED (2)  ← _retired/ 이동, 코드 제거 검토
- API-191 (deprecated) — Session 21 ADR-035 흡수
- ...

### UNCHANGED (57)
표 참조 (다운로드 skip, 파일 유지)

## 이전 Changelog 이력
<직전 run 의 Changelog 블록들을 아래로 누적 보존 (append-only)>
```

> Changelog 는 **append-only** — 매 run 새 블록을 "이번 run" 으로 추가하고, 직전 것은
> "이전 Changelog 이력" 으로 내림. git 과 함께 변경 히스토리 추적 가능.

## 차이 감지 알고리즘 (Phase 2.5)

```
입력:
  current_catalog = { ITEM_ID: {version, last_updated_at, stale, type, title, status_active} }
                    (Phase 2 에서 get_neighbors + list_items 로 수집)
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
      status = RETIRED       # _retired/ 이동, 삭제 금지

INITIAL 모드 (version-master.md 없음): 모든 current ITEM = NEW
```

### 판정 세부 규칙

- **version 필드 출처**: `list_items` / `get_item` 응답의 `current_version` (정수).
- **RETIRED 식별**: `list_items(include_retired=true)` 의 `retired_items` 에 등장 OR
  current 활성 목록에서 사라짐. 두 경우 모두 RETIRED.
- **CHANGED 인데 version 동일하나 stale 토글**: logicraft 가 stale=true 로 막 바뀐 경우
  → UNCHANGED 로 두되 version-master 표의 stale 컬럼만 갱신 + IMPLEMENTATION 변경알림에 "stale 전파" 1줄.
- **로컬 파일 누락 + UNCHANGED**: 파일이 실제로 없으면 강제 재다운로드(NEW 취급).
- **version 역행** (current < local, 이론상 발생 X): 경고 로깅 + CHANGED 처리 + 사용자 보고.

### CHANGED ITEM 파일 배너 (fetcher 가 삽입)

frontmatter `status: CHANGED`, `prev_version: 11` + 본문 최상단:

```markdown
> ⚠️ **버전 변경 감지 — logicraft v11 → v12** (2026-05-16T23:35Z)
> change_summary: <원문 그대로>
> ↳ 요약/구현 노트 재검토 후 작성된 코드에 반영. 직전 요약은 git diff 확인.
```

### RETIRED 처리 (삭제 금지)

```
mkdir -p _retired/{type}/
mv {type}/{ID}.md          _retired/{type}/{ID}.md
mv {type}/_raw/{ID}.json   _retired/{type}/{ID}.json   (있으면)
→ _retired/{type}/{ID}.md frontmatter 에 status: RETIRED + retired_at + 사유(change_summary) 추가
→ version-master 표 local file 컬럼을 _retired 경로로 갱신
```
물리 삭제 절대 금지 (전역 정책: 사용자가 만들지 않은 산출물·구현 흔적 보존).

## git 권장

산출물 루트가 코드 레포 안이면 `docs/design/` 를 git 으로 함께 버전관리 권장.
CHANGED ITEM 의 직전 요약은 git history 로 자연 보존되므로 별도 백업 불필요.
(스킬은 git 명령 자동 실행 안 함 — 사용자가 커밋. IMPLEMENTATION.md 에 안내만 기재.)