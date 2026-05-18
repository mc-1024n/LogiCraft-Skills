# Cascade Patterns — MVP 8 타입

logi-update-specialist가 STEP D 검증 + STEP F cascade 후보 분류 시 참조.

## 토폴로지 의존 (선행 처리 우선순위)

낮은 번호 먼저 처리. 같은 번호는 병렬 가능.

| 순위 | 타입 | 사유 |
|---|---|---|
| 1 | `adr` | 다른 ITEM이 description/brownfield.decided_by로 인용 |
| 2 | `erd` | DFEAT.persists_in_tables / SCREEN sections 참조 |
| 3 | `api_endpoint` | DFEAT.implemented_by_endpoints / SEQ.invokes_apis / SCREEN.consumes_apis 참조 |
| 4 | `domain_feature` | UC / SCREEN backing |
| 5 | `use_case` | SEQ.realizes_use_cases |
| 6 | `diagram_sequence` | 잎 노드 (보통 더 이상 cascade 없음) |
| 6 | `screen_spec` | 잎 노드 (단, NAV에 영향 시 5순위) |
| 5 | `navigation_tree` | SCREEN route 변경 cascade |

## 타입별 cascade 패턴

### api_endpoint (API-XXX)

**필수 자체 점검**
- **(2026-05-14~) `data.title` 필드 신설** — patch path `"title"` set 시 outer title 자동 sync. 이전 "outer 매개변수만" 우회 폐기
- path 변경 시 `parameters[]`도 정합 (path id 추가/제거)
- responses schema 변경 시 호출처 검증
- request_body remove op: `request_body.schema.properties.{field}` remove 작동

**cascade 후보**
- DFEAT (implemented_by_endpoints에 본 API 포함)
- SEQ (invokes_apis / messages[].item_ref)
- SCREEN (consumes_apis)
- UC (main_flow의 API 호출 단계)

**auto_propagate=true 케이스**: path 단순 정정 / response 필드명 변경 (의미 동일)
**auto_propagate=false**: method 변경, 신규 필드 추가, 의미 변경

### screen_spec (SCREEN-XXX)

> ★★ 이 섹션은 요약이다. **반드시 schema 캐시의 `workflow_notes` 신규 섹션을 우선 정독**:
> Multi-surface 분할 워크플로 / CSS 변수 카탈로그 / 인라인 스타일 정책 / wf-* 변형·마크업 합성 /
> data.sections vs static_renders.sections 책임분담 / brownfield.legacy_source 5필드 /
> purpose 작성 가이드 / wf-page-header·breadcrumb 예외 / CSS 경로 워크플로.
> 본 문서와 충돌 시 **workflow_notes 가 항상 우선** (2026-05-15 가이드 대폭 보강 반영).

**필수 자체 점검**
- sections[].role enum: header/hero/navigation/filter/main/side/modal/footer
- sections[].layout enum: form/list/detail/dashboard/grid/stack/tabs
- components[].value 키 거부 → label에 통합
- consumes_apis 갱신
- ★ `data.sections[]` = SCREEN 전체 통합 (모든 surface 합집합, 추적성 단일 source) — 항상 채움.
  `static_renders[].sections[]` = 해당 surface 자체 메타 (page 는 보통 비움, modal/toast 는 채우면 정확)
- multi-surface 는 surface 별 별도 render entry. `render_id` 명명: page='main'(1개),
  modal/popover=명사구 슬러그('asset-result'·'background-request'), toast=에러코드('err-403')
- `overlays` = 이 render 가 떠 있는 base render_id (modal→modal 체인 가능)
- `triggered_by[]` = 진입 경로 자연어 배열

**static_render (HTML) — ★ wireframe.css 정책 (구 모순 정정 2026-05-15)**
- ❌ (구 가이드 폐기) "wireframe.css 절대경로 `/api/static/...` 를 본문에 박아라" — **틀림**
- ✅ 업로드 본문에 `<link>`·`<style>`·외부폰트·`<script>`·`on*=` **절대 금지** — 서버 sanitize 가
  wireframe.css 를 자동 주입. 본문은 `<!DOCTYPE><html><body class='wf-app'>...` 만
- ✅ 색상/border/shadow/font 는 `var(--wf-*)` 또는 wf-* 클래스 (hardcode 금지).
  레이아웃 좌표(position/flex/z-index)·미세 간격은 inline 허용
- ✅ 가이드에 없는 클래스(wf-btn-sm·wf-badge-ok 등)는 CSS 정의 없음 → 효과 0, 사용 금지.
  Badge 는 wf-badge-success/-danger/-warning/-primary
- ✅ 로컬 작업 시 wireframe.css 는 `curl <base-url>/api/static/wireframe/wireframe.css` 로 받아
  **별도 preview.html wrapper(로컬 전용, 업로드 X)** 에서만 link — 본문엔 안 박음

**cascade 후보**
- NAV (route 변경 시)
- UC.related_screens
- SEQ (FE 참여자 시작점)
- HTML 정적 렌더 (sections 변경 시 재업로드 필요)

**HTML 재업로드 별도 처리**: cascade_candidates에 HTML-upload 가상 항목으로 보고 (메인이 별도 처리).
sections 변경 시 surface 별로 `upload_static_render` 재호출 필요 — 신규 가이드 Multi-surface 호출순서 참조.

### diagram_sequence (SEQ-XXX)

**필수 자체 점검**
- participants[].kind: actor/service/database/queue/external/system
- participants[id=DB].name path-by-key 작동
- messages[].kind: sync/async/return/self/note
- messages[].item_ref 자동 link
- fragments[].kind: alt/opt/loop/par/critical
- fragments[].start_index/end_index는 messages[] index
- realizes_use_cases / invokes_apis / publishes_events 정형 필드 채움
- source mermaid + 정형 필드 둘 다 갱신 (불일치 금지)

**cascade 후보**
- 보통 잎 노드. UC 변경 시 받는 입장
- 신규 API/EVT 인용 시 해당 ITEM 존재 확인

### domain_feature (DFEAT-XXX)

**필수 자체 점검**
- **(2026-05-14~) patch path `"title"` set 시 outer title 자동 sync** — 별도 title 매개변수 호출 불필요. 이전 "2단계 처리" 우회 폐기 (api_endpoint·domain_feature 모두 적용)
- persists_in_tables[]는 텍스트 (ITEM 매칭 안 됨, 그래프 link 없음)
- implemented_by_endpoints[]는 API-XXX 패턴 (자동 link)
- triggers / consumes는 EVT-XXX (자동 link)
- description에 다른 ADR/ITEM 인용 → references generic link 자동 추출

**cascade 후보**
- UC (DFEAT backing)
- SCREEN (DFEAT backing)
- API (책임 endpoint 변경 시)

### erd (ERD-XXX)

**필수 자체 점검**
- 논리(한글)·물리(영문) 페어 항상 동시 갱신
- tables[N] remove op 작동 (index 기반)
- tables[name=foo].columns[name=bar] path-by-key 작동
- columns[].description 모든 컬럼 필수
- DBMS별: PostgreSQL은 bigserial/jsonb/timestamptz/PostGIS+GIST 등

**cascade 후보**
- DFEAT.persists_in_tables 인용 ITEM (텍스트 매칭이라 grep 필요)
- API request_body/responses에 컬럼명 인용
- SCREEN sections에 컬럼명 인용 (KeyValue label 등)

**페어 처리**: ERD-021(논리)/ERD-022(물리) 등 페어 ID는 항상 한 라운드에 둘 다 큐 추가

### use_case (UC-XXX)

**필수 자체 점검**
- main_flow[].step 1부터 순차
- secondary_actors는 외부 actor만 (시스템 내부 도메인 actor 아님)
- alternate_flows[].trigger 필수
- realizes_features (FEAT-XXX)
- related_screens (SCREEN-XXX, 자동 link)

**cascade 후보**
- SEQ (realizes_use_cases)
- AC (covered_by_acceptances)

### adr (ADR-XXX)

**필수 자체 점검**
- considered_options[] 최소 1개 (실질적으로 2~3개 권장)
- decision.chosen_option + justification 필수
- consequences.positive + negative 필수
- **(2026-05-14~) references[].item_id 직접 지원** — `{item_id: "DFEAT-064"}` 형식 (pattern `^[A-Z]+-\d+$`). `logicraft://item/<ID>` URL 우회 폐기. `anyOf [{item_id}, {url}]` 둘 다 허용
- patch path `references` predicate selector: `predicate_key_candidates: ["item_id"]` — 정밀 갱신 가능
- supersedes는 한번 설정 후 변경 불가

**cascade 후보**
- 본 ADR 인용 가능한 DFEAT/SCREEN/UC 등 (description grep)
- 직접 link는 description 자동 추출에 의존

### navigation_tree (NAV-XXX)

**필수 자체 점검**
- nodes[key=foo].children[key=bar].visible_when path-by-key 작동
- **단, `get_item_schema` patch_paths에는 `nodes` selector가 `["index"]`만 명시** (2026-05-14 검증) — key-path는 실제 작동하나 메타데이터 미반영. 안전하게 key-path 사용 권장
- menuCode·route 정합
- ROLE 매핑 (required_roles 또는 visible_when)

**cascade 후보**
- SCREEN route 변경 cascade
- ROLE 매트릭스 변경 시 영향

## auto_estimation_failed 보고 정책

다음 필드는 추정 실패 시 비우고 보고 (사용자 종료 시 일괄 확정):
- brownfield.legacy_source.identifier (1차 소스 식별자)
- brownfield.legacy_source.repo (1차 레포명)
- brownfield.decided_by (변경 근거 ADR)
- domain_id (도메인 미지정 ITEM)
- specializes_feature (DFEAT의 상위 FEAT)

## 흔한 함정 (Session 33까지 검증)
- PowerShell `ConvertFrom-Json` 한글 깨짐 → Python `json.load(encoding='utf-8')` 우회
- `create_item` `domain_id` 매개변수 자동 매핑
- ~~patch concurrent base_version conflict는 retry 패턴~~ → **(2026-05-14~) `update_item.auto_retry: 0~5` 파라미터 사용**. 병렬 cascade에서 client retry 로직 폐기
- ~~references에 ITEM ID 문자열 거부 (url 형식만)~~ → **(2026-05-14~) ADR `references[].item_id` 직접 지원**
- ERD logical/physical 페어 patch path 각각

## 플랫폼 도구 진화 (2026-05-14 검증)

### list_items
- `limit` max **1000** (이전 200) — persisted-output 분할 우회 폐기
- `offset` 파라미터 추가 — pagination 지원
- `domain_id` 필터 추가 (pattern `^DOMAIN-\d+$`) — 도메인 단위 fetch에서 `get_neighbors` 우회 폐기

### update_item
- `auto_retry: 0~5` 파라미터 — base_version conflict 서버 측 재시도. 병렬 add op에 특히 유효

### get_item_schema
- 응답에 **`patch_paths[]` 배열 신설** — `path` + `selectors`(`index`/`predicate`) + `predicate_key_candidates` 명시
- 사용 흐름: patch 작성 전 `get_item_schema(type)` → `patch_paths` 확인 → 지원되는 selector만 사용 (시행착오 폐기)
- ERD: `tables[].columns` 두 단계 path-by-key 공식 지원 (`predicate_key_candidates: ["name"]`)
- ADR: `references` predicate (`predicate_key_candidates: ["item_id"]`)
- screen_spec: `sections` index + predicate 모두

### 미해결 잔재
- navigation_tree `nodes` patch_paths 메타데이터에 `predicate` selector 미명시 (실제는 작동하나 공식 가시화 안 됨)
- create_item `change_summary` 자동 기본값 ("Claude가 생성" 등) 잔존 — runtime 검증 필요
