# Cascade Patterns — 주요 타입 토폴로지

logi-update-specialist가 STEP D 검증 + STEP F cascade 후보 분류 시 참조.

> ★ **미등재 타입 기본 규칙**: 이 표에 없는 타입(서버에 타입이 계속 추가됨 — 진실원은
> `get_item_schema(type)` 응답의 링크 정의)을 수정할 때는 ① `get_item_schema` 의
> from/to 링크 목록과 `cascade_hint` 로 하류를 판정하고 ② `analyze_impact` 결과를 병행한다.
> 표는 자주 다루는 타입의 캐시일 뿐 — 표에 없다고 "cascade 없음" 단정 금지.

## 토폴로지 의존 (선행 처리 우선순위)

낮은 번호 먼저 처리. 같은 번호는 병렬 가능.

| 순위 | 타입 | 사유 |
|---|---|---|
| 1 | `adr` | 다른 ITEM이 description/brownfield.decided_by로 인용 |
| 2 | `erd` | DFEAT.persists_in_tables / SCREEN sections / IAPI.operates_on / DP.reads_from·writes_to 참조 |
| 3 | `api_endpoint` | DFEAT.implemented_by_endpoints / SEQ.invokes_apis / SCREEN.consumes_apis 참조 |
| 3 | `service_interface` / `module_api` | **경계 계약 — api_endpoint 와 동급.** DFEAT 가 `implements` 로 실현(SVC·IAPI 수정 → 실현 DFEAT 재검토), MOD 가 implements/implemented_by. AC `verifies` 짝 |
| 3 | `library_api` | 경계 계약. implemented_by MOD / verifies AC / uses_constant CONST |
| 4 | `domain_feature` | UC / SCREEN backing |
| 5 | `use_case` | SEQ.realizes_use_cases |
| 6 | `diagram_sequence` | 잎 노드 (보통 더 이상 cascade 없음) |
| 6 | `screen_spec` | 잎 노드 (단, NAV에 영향 시 5순위) |
| 6 | `diagram_c4_component` / `class_diagram` | 잎 노드 — ★ `depicts_dfeats`(DFEAT 레벨)만 연결, 필드 변경·**범위 확장(신규 모듈/컴포넌트/클래스 추가)** 시 analyze_impact 미surface → **모델 대전환·범위 확장 시 수동 큐잉 필요**(아래 전용 섹션) |
| 6 | `test_scenario` / `acceptance` | 잎 노드 — 검증 산출물. UC/SCREEN/REQ/NFR/API/ERD 의미 변경 시 steps/scenario stale → 약-link 라 **수동 큐잉**(아래 test_scenario 전용 섹션) |
| 6 | `data_pipeline` | 잎에 가까움 — 하류는 emits EVT·implemented_by MOD 정도. 반대로 ERD/EXTSYS 변경 시 DP 의 reads_from/writes_to·stages 가 cascade 대상(하류)임에 주의 |
| 6 | `permission_manifest` / `settings_schema` | 잎 노드 — 전용 링크 없음(범용 links 만). desktop 프로파일 산출물. FEAT(requested_by_features)·CONST(uses_constants) 변경 시 **수동 큐잉** |
| 5 | `navigation_tree` | SCREEN route 변경 cascade |
| 0 | `requirement` | ★ 상류(upstream). 도메인/DFEAT 의 부모 — 의미 변경 시 상류로 sync (아래 별도 섹션) |

## ★ 상류(upstream) cascade — requirement sync (RFP+도메인 재대조)

기존 cascade 는 **하류**(변경 ITEM → 의존 ITEM). 그러나 산출물은 `RFP(rfp_item) → requirement → domain/DFEAT/UC...` 파생 구조라,
**도메인 기준으로 수정을 반복하면 부모 requirement 가 가장 stale** 해지는 역전이 발생한다 (Session 71 D004 실증: REQ-025/026 이 폐기 모델 잔존). 따라서 도메인 계층 ITEM 을 **의미 변경**할 때 부모 REQ 를 상류 cascade 후보로 함께 점검한다.

### 트리거 (★ 과익 방지 가드 — 의미 변경만)
다음 **의미(모델·범위·계약) 변경** 시에만 부모 REQ 를 cascade 후보로 플래그:
- DFEAT/domain 의 책임·모델·범위 재정의 (예 sample 매트릭스→ver 타임라인, mode 폐기, 책임 외부 위임)
- ERD 의 테이블/컴럼 모델 대전환, 핵심 enum/식별자 변경
- ADR 대전환이 도메인 책임을 바꾼 경우

다음은 **상류 트리거 안 함** (가드):
- stale-ack / 단순 명칭·오타 정정 / field-count 진동 / link 무결성 정합 / description 라이트 터치 / HTML 재업로드

### 부모 REQ 식별
1. 변경 DFEAT 의 상위 추적 (`specializes_feature` → FEAT, REQ.description 의 도메인 책임 인용)
2. `get_neighbors(DOMAIN-XXX)` backward 의 `belongs_to_domain` requirement
3. REQ 가 변경된 책임 영역을 서술하는지 본문 대조 (해당 REQ 만 후보)

### requirement refresh 방법 (specialist 가 REQ 처리 시)
정책: **도메인(현재 설계) 우선 + RFP 배경** (사용자 결정, Session 71).
1. `get_item(REQ-XXX)` 현재 내용 + `derived_from_rfp`(없으면 RFP 추정: rfp_item title/workstream 매핑) 확인
2. `get_item(RFP-NNN)` 진실원천(rfp_item) 의도 + `get_item(DOMAIN-XXX)` 현재 설계 정독
3. REQ 재작성:
   - **현재 설계(도메인) 기준**으로 description/title/rationale 갱신 (폐기 모델 어휘·구 필드·구 endpoint 제거)
   - RFP 의도를 **rationale 에 배경**으로 인용. 도메인이 ADR 로 RFP 에서 벗어났으면(divergence) 그 차이를 rationale 에 명시
   - **`derived_from_rfp` link 보강** (요구사항이 source=stakeholder 만이고 RFP 미연결이면 추적성 복구)
4. `change_summary` 에 "RFP+도메인 기준 최신화" 명시

### cascade 방향성 (중요)
- **자동 상류 검토 (사용자 결정)**: 의미 변경 트리거 시 부모 REQ cascade_candidate 는 `auto_propagate: true` 로 **자동 큐잉**(pending 보류 아님). refresh 정책(도메인 우선+RFP 배경)이 결정적이므로 specialist 가 자동 재작성. 단 **Phase 5 보고에 REQ 변경을 명시**해 사용자 가시화(요구사항 변경은 중요).
  - 예외: RFP↔도메인 divergence 가 **새로운 정책 판단**을 요구하거나 REQ 가 신규 범위를 추가해야 하면 `auto_propagate: false` → pending_user_decisions.
- 도메인→REQ 상류 sync 는 **REQ 가 catch-up** 하는 것 → REQ 변경은 **다시 하류로 재전파 금지**(하위는 이미 현재 모델, 무한루프·중복 방지). REQ 처리 후 그 하위 ITEM 은 큐에 추가하지 않음.
- REQ 의 부모 RFP(rfp_item)는 **불변 진실원천 — 절대 수정 안 함** (읽기만).

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
- test_scenario (related_apis — API 계약/path 재정의 시 steps stale, 약-link 수동 점검)

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

**wf-* 컴포넌트 렌더 규칙 (★ Session 37 SCREEN-001/020 적발·명문화 — 재발 방지)**
- ✅ **KeyValue**: label 과 value 는 **균형 잡힌 동급 본문 타이포그래피**. label=`wf-label`, value=`wf-muted`(또는 동급 본문). ❌ value 에 거대 heading 태그(`<h1~h3>`)·강한 bold·과대 inline `font-size` 금지 — value 가 label 보다 훨씬 크고 굵게 렌더되는 안티패턴(상태 정보 카드 날짜/플래그가 거대 bold 로 튀는 현상)이 실제 발생함
- ✅ **Button**: 본문은 **label 만**. 섹션 description·부가 설명("한 트랜잭션 PATCH (API-259)" 류)을 버튼 옆에 붙이지 말 것 → 별도 caption(`wf-help`) 영역으로 분리. 버튼 옆 설명 텍스트가 어색하게 붙는 안티패턴 방지
- ✅ Stat/Badge/Alert 등도 동일 원칙 — 값/라벨 타이포 균형, 의미 없는 과대 강조 금지. 값 강조는 wf-* 표준 클래스로만(임의 inline 확대 금지)
- ★ 충돌 시 schema `workflow_notes` 우선이나, 위 3건은 workflow_notes 미반영 시에도 specialist 가 반드시 준수 (Session 37 사용자 화면 검수 적발 사항)

**cascade 후보**
- NAV (route 변경 시)
- UC.related_screens
- SEQ (FE 참여자 시작점)
- test_scenario (exercises_screens / steps[].screen_ref — 화면 흐름·sections 변경 시 steps stale, 약-link 수동 점검)
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
- columns[].description 모든 컴럼 필수
- DBMS별: PostgreSQL은 bigserial/jsonb/timestamptz/PostGIS+GIST 등

**cascade 후보**
- DFEAT.persists_in_tables 인용 ITEM (텍스트 매칭이라 grep 필요)
- API request_body/responses에 컴럼명 인용
- SCREEN sections에 컴럼명 인용 (KeyValue label 등)

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
- test_scenario (covers_use_cases — integration TEST. UC 의미 변경 시 steps stale, 약-link 라 수동 점검)
- ★ 상류: 부모 REQ (의미 변경 시 — "상류 cascade" 섹션)

### requirement (REQ-XXX)

> ★ 보통 **상류 sync 대상**(도메인 변경이 끌어올림). 위 "상류 cascade — requirement sync" 섹션의 refresh 방법 적용.

**필수 자체 점검**
- `derived_from_rfp` (상위 rfp_item link) — 부재 시 보강(추적성). source.type=stakeholder 만이면 RFP 매핑 추가
- description/rationale 이 **현재 도메인 모델**과 정합 (폐기 모델 어휘 금지)
- RFP divergence(도메인이 RFP 의도에서 벗어난 점)는 rationale 에 명시
- acceptance_criteria(inline) — REQ 자체 수용기준 (별도 AC ITEM 과 무관)

**진실원천 (읽기 전용)**
- `rfp_item`(RFP-NNN) = 불변 발주처 원천. **절대 수정 안 함** — 재대조 입력으로만 사용

**cascade 후보**
- 보통 **없음** (REQ 는 상류 종착 — catch-up 이라 하류 재전파 금지)
- 단 REQ 가 *신규 책임*을 추가(범위 확대)하면 그 책임의 DFEAT/UC 부재 여부만 점검(coverage)

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

### diagram_c4_component (CMP-XXX) / class_diagram (CDIAG-XXX) — ★ 정형 cascade 종착 + 본문 수동 refresh

**문제 (D002 CMP-002 실증)**: C4 컴포넌트(CMP)·클래스(CDIAG) 다이어그램은 도메인/DFEAT 에 `depicts_dfeats`(DFEAT 레벨) 로만 연결된다. ADR/ERD/API 의 **필드 레벨 모델 변경**(ADR-078 배치/썸네일 제거, ADR-055 push 전환, ADR-075 식별자 변경, cron→push 등)은 `depicts_dfeats` 가 그대로 활성 DFEAT 를 가리키면 link 무변 → **analyze_impact 에 CMP/CDIAG 를 dependent 로 안 띄운다**. 그래서 C4/CDIAG 는 cascade 에서 자동 누락되어 **본문(components[].description·classes[].description·relationships)이 구 모델로 표류**한다 (CMP-002 = ADR-078/055/075/278 누적 미반영 → batches·썸네일·8:30 cron·API-009/010 잔재).

> **★ 2차 실증 (ADR-081 D004, 2026-06-12) — 범위 확장(scope-expand)도 동일 사각지대**: ADR-081(데이터마트 배포 3종, `change_kind=[scope-expand, new-policy]`)은 신규 클래스 6개·신규 모듈 3개를 **추가**했는데, ADR-081 의 `analyze_impact` backward dependents = MOD/NAV/REQ/FEAT 뿐 **C4 없음**(시드에서 도달 불가). 같은 cascade 에서 CDIAG-004(클래스=데이터 모델 자체라 자명)·SEQ·SCREEN·AC·UC 는 전부 갱신됐으나 **CMP-003 만 누락**됐다(v9 잔존). 원인: (a) 시드 ADR 가 C4 미surface (b) **수동 큐잉 트리거 키워드에 `scope-expand` 부재** → 안전장치 미발동 (c) CMP 는 `backward=[]` 진짜 leaf 라 누락이 하류에 안 보임(컴포넌트 설계서 동기화에서야 발각). ★ 단 **수정된 DFEAT(DFEAT-068, deploy_type 추가) 의 `analyze_impact` 는 CMP-003 을 depicts·notify_strong 으로 정상 surface** → 시드가 아니라 **변경 DFEAT 를 기점으로 점검하면 잡힌다**(아래 필수 규칙 2 참조).
> ★★ **mc-logi-domain-review 의 diagram 차원(DIAG-001~004)도 못 잡는다** — 그건 depicts 레벨(활성 DFEAT 를 그리나)만 보므로 depicts 정상·본문 구모델이면 통과. (DIAG-005 본문-구모델 신설로 검출 보강됨.)

**필수 — 메인/specialist 책임**
- **(규칙 1) 도메인 모델 대전환·범위 확장 ADR 를 cascade 할 때는 해당 도메인의 CMP·CDIAG 를 cascade 후보로 수동 큐잉**한다 (analyze_impact 가 안 띄워도). 트리거 = 처리 ADR/ITEM 의 `change_kind` 에 `model-change`/`data-model-redesign`/`semantic-redefinition`/**`scope-expand`/`scope-shift`/`new-policy`** 포함, 또는 ERD 테이블/컴럼 대전환·API path/계약 재정의·식별자 변경·컴포넌트 책임 이동·엔티티 폐기·**신규 모듈/컴포넌트/엔티티·클래스 추가(범위 확장)**. ★ ADR-081 실증: `scope-expand`(신규 모듈 추가)도 반드시 포함 — "기존 모델 재설계"만이 아니라 "범위 확장"도 C4 본문 갱신이 필요하다.
- **(규칙 2 — ★ 신설, 가장 확실) 변경된 DFEAT 를 기점으로 C4 를 잡아라**: ADR/ERD/API 시드의 `analyze_impact` 는 C4 를 미surface 하지만, **수정된 DFEAT 의 `analyze_impact(DFEAT-XXX)` 는 그 DFEAT 를 `depicts` 하는 CMP/CDIAG 를 hop1 backward(notify_strong)로 정상 surface 한다**(ADR-081 실증: DFEAT-068 → CMP-003 정상 노출). 따라서 cascade 라운드에서 **DFEAT 를 처리·수정할 때마다 `analyze_impact(그 DFEAT)` 의 backward dependents 중 `diagram_c4_component`/`class_diagram` 타입을 빠짐없이 큐에 추가**한다. 신규 DFEAT(077/078 류)면 그걸 depicts 할 CMP/CDIAG 가 아직 없으므로 규칙 1(도메인 CMP/CDIAG 수동 큐잉)로 커버. → 규칙 1(도메인 단위 안전망) + 규칙 2(변경 DFEAT 기점 정밀 포착) **이중 가드**.
- C4/CDIAG 처리 = **본문 전면 대조**: components/classes 의 description·name 이 (a) 폐기 테이블/엔티티 (b) deprecated API id (c) 구 식별자/계약 (d) superseded ADR 인용 을 참조하면 현행 모델로 재작성. **depicts_dfeats 가 활성 DFEAT 정상이어도 본문이 구 모델이면 갱신 대상.**
- ★ **부분 수정 금지** — 한 다이어그램에서 일부(예: heatmap)만 고치고 batches/썸네일 잔재를 두면 또 표류(CMP-002 1차 부분수정 → 재지적 실증). `update_item` patch op set 으로 `components`/`relationships`/`external_dependencies`/`description` 통째 현행화.
- 구현 상태 알면 `components[].implementation.status` (implemented/planned) 도 반영.

**cascade 후보**: 보통 종착(자동 후보 없음). 단 신규 컴포넌트가 신규 API/DFEAT 를 인용하면 그 ITEM 존재만 확인.
**auto_propagate**: 모델 대전환 시 true(자동 큐잉 권장). 단 본문 전면 refresh 라 작업량 큼 → Phase 5 보고에 "C4 전면 refresh" 명시.

### test_scenario (TEST-XXX) — 검증 산출물 종착 (AC 와 동류, 통합/시스템 시험)

통합(integration, cross-UC end-to-end)·시스템(system, REQ/NFR 검증) 시험 시나리오. `covers_use_cases`(UC)·`exercises_screens`(SCREEN)·`verifies_requirements`(REQ)·`verifies_nfrs`(NFR)·`related_apis`(API) 로 추적하고, `steps[]`(순번·업무처리내용 action·시험항목 test_item·사전조건·입력자료 input_data·예상결과 expected·화면ID screen_ref)가 그 흐름을 1:1 반영. AC 와 같은 **검증 산출물 = 하류 종착**(cascade 받는 입장, 하류 없음).

**필수 자체 점검**
- `steps[].screen_ref`(SCREEN)·`related_apis`(API)·`covers_use_cases`(UC)·`verifies_requirements/nfrs` 인용 대상이 **활성**인지(deprecated 인용 금지).
- `steps[].action·expected·input_data` 가 대상 UC.main_flow·SCREEN sections·API 계약의 **현행** 흐름과 일치.
- kind=integration → `covers_use_cases` 필수. kind=system → `verifies_requirements`/`verifies_nfrs` 필수.
- patch path: `steps` 는 index/predicate(screen_ref). `status=deprecated` 는 top-level status param.

**★ 상류 변경 → test_scenario cascade (이 type 이 받는 입장 — 메인이 수동 큐잉)**
- UC main_flow/alternate_flows **의미** 변경 → `covers_use_cases` 에 그 UC 가진 TEST steps stale.
- SCREEN sections/route 변경 → `exercises_screens`·`steps[].screen_ref` 가진 TEST stale.
- API path/계약 재정의 → `related_apis` 가진 TEST steps stale.
- REQ/NFR 의미 변경 → `verifies_requirements`/`verifies_nfrs` 가진 system TEST stale.
- ERD 테이블/컴럼 대전환 → `steps.input_data/expected` 가 그 데이터 인용 시 stale.
> ★ test_scenario 의 위 link 는 cascade_hint 가 약하거나(notify_weak/없음) project-level 이라 **analyze_impact 에 backward 로 안 뜸 수 있다**(C4 와 유사 사각지대). UC/SCREEN/API/REQ/NFR/ERD 를 **의미 변경**할 때는 `list_items(type=test_scenario)` 로 covers/exercises/verifies/related 교차해 후보를 수동 점검.

**cascade 후보**: 종착(하류 없음).
**auto_propagate**: trivial(명칭·stale-ack·field-count)=false 무시 / **의미 변경**(흐름·화면·계약·데이터)=true 자동 큐잉. `steps` 재작성은 시험 내용이라 specialist + Phase 5 보고에 명시(시험 산출물 변경은 사용자 가시화). ※ AC(acceptance) 도 동일 패턴 — use_case 섹션 cascade 후보 + 본 원칙 적용.

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
