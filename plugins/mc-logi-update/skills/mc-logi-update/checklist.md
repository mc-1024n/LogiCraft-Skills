# Specialist Hard Rules — 절대 위반 금지

## Pre-edit (편집 전)

### 가이드 숙지 (★★ STEP B)

**스키마 가이드 — 캐시 우선 (★ 직접 get_item_schema 호출 금지)**
- [ ] 입력의 `schema_cache_path` 받았는가? → **이 로컬 캐시 파일을 정독** (메인 Phase 2.5 가 24h TTL 로 워밍해둠)
- [ ] 캐시 파일은 크다 (screen_spec ≈ 71KB). **반드시 끝까지 읽을 것**:
      - `Grep` 으로 `workflow_notes` 의 신규 섹션 마커(`★★`, `★`) 전수 확인
      - 또는 `Read offset/limit` 으로 분할 정독 — 앞 청크(json_schema)만 보고 멈추지 말 것
      - `workflow_notes` 배열의 **마지막 라인까지** 읽었는지 self-check (라인수 vs 읽은 범위)
- [ ] 캐시의 `_cache_meta.schema_version` 확인 → STEP C 의 `get_item` 응답 `schema_version` 과 불일치 시 `notes_for_main.schema_cache_stale: <type>` 보고 (메인이 다음 라운드 강제 refresh)
- [ ] `schema_cache_path` 가 없거나 파일 부재 → **그때만** `get_item_schema(type)` 직접 호출 (fallback) + persisted-output 이면 파일을 청크로 끝까지 읽기
- [ ] 캐시 파일에 write 금지 (read-only — 갱신은 메인 책임, 동시성 보호)

**워크플로 가이드**
- [ ] `get_logicraft_guide("update-item")` 호출했는가? → patch path 컨벤션·base_version 룰
- [ ] brownfield 타입이면 `get_logicraft_guide("brownfield")`도 호출했는가?
- [ ] 스키마 캐시 + 두 가이드 응답 모두 읽기 전에는 update_item 호출 금지
- [ ] `get_logicraft_guide("workflow")` 의 「산문을 칸으로」 절을 읽었는가? → 작성 규칙 원문(관계는 칸 · 본문엔 현행만 · 경위는 change_summary)
- [ ] 스키마에서 이 타입의 **연결 칸 / 담당자 칸 / 구조 칸** 목록을 뽑았는가? (하드코딩 금지 — 스키마가 늘면 따라간다)
- [ ] ★ 충돌 시 우선순위: **MCP 스키마 캐시(workflow_notes) > cascade-patterns.md > checklist.md** — 보조 문서가 구버전일 수 있으므로 최신 workflow_notes 를 항상 우선 적용

### 현재 상태 확인 (★ STEP C)
- [ ] `get_item(target_id)` 호출 → current_version 보존
- [ ] 기존 brownfield 메타는 보존 (덮어쓰지 않음)
- [ ] 기존 links / unresolved_links 확인

## During edit (편집 중)

### 작성 규칙 (★ STEP D2 · 모든 수정·신규 등록)
- [ ] edit_context 에 든 관계·구조 값·담당을 **같은 patch 의 칸 값**으로 넣었다 (값마다 근거 기억 → `fields_written`)
- [ ] 이번에 새로 쓰는 산문에 **ITEM ID 나열이 없다** — 관계는 칸, 산문엔 이유·맥락
- [ ] 이번에 쓰는 산문에 **경위 문장이 없다**(「vN 에서 바꿈」「CO-NNN 로 정정」「### Session NN」) → `change_summary`
- [ ] **손대지 않는 옛 문단은 그대로** 뒀다 — 옛 산문 ID 이관은 `mc-logi-schema-fill` 몫
- [ ] 기존 항목에 `data_mode=replace` 를 쓰지 않았다 (edit_context 가 통째 교체를 명시한 경우만 예외)
- [ ] 근거 없는 칸은 비우고 `fields_left_empty` 에 사유
- [ ] **재검토 표시 보존(STEP E3)** — `resolves_review_from` 에 **실제로 반영한 원인만**(재검토 해소가 목적일 때만 `"all"`, 불확실하면 생략) · 옛 서버(입력 거부·`review_marks` 없음)면 저장 뒤 `restore_review_needed(since=저장 직전, dry_run=false)`

### patch 컨벤션
- 점 표기: `field.subfield`
- key path: `tables[name=foo].columns[name=bar]`
- index: `tables[3]`, `sections[N]`
- add op 별칭: `tables[-]`
- nested 2단계 path: `sections[N].components[M].triggers_api`
- ★ `brownfield/notes` (슬래시) 거부 → `brownfield.notes` (점) 사용

### enum 직접 인용
- enum 값은 schema 응답에서 그대로 복사
- "kind", "type" 등 추정 금지
- 알려진 거부 enum:
  - `brownfield.legacy_source.kind` → 거부 (정답: `type`)
  - `screen_spec component.value` → 거부 (label에 통합)
  - ~~`api_endpoint data.title` → 필드 자체 없음~~ ← **낡음. 2026-08-26 실측으로 정정** (아래 참조)

### 타입별 함정 (Session 1~33 누적)

**api_endpoint**
- ✅ **`data.title` 이 존재한다** (2026-08-26 실측 · 워커 둘이 독립 확인)
  - 스키마 `fields_summary`·`display_hints` 에 `title` 이 있고, 실제 ITEM(API-002·014·021·092)이 전부 갖고 있다
  - patch path `"title"` 을 set 하면 **outer title 이 자동 sync** 된다 (cascade-patterns.md 2026-05-14 항목과 일치)
  - **신설 시 outer `title` 과 같은 값을 `data.title` 에도 넣는다**
- ⚠️ 이 문서의 옛 서술(「필드 없음」)이 워커를 두 번 헷갈리게 했다 — **캐시된 스키마보다 실제 `get_item_schema` 응답이 이긴다**

**domain_feature**
- ⚠️ `data.title` 있지만 outer title sync 안 됨
- ✅ title 변경 시 매개변수 `title` + patch `data.title` 둘 다

**screen_spec**
- ❌ `components[N].value`
- ✅ `components[N].label`에 통합
- ✅ static_renders[] 변경은 별도 `upload_static_render`

**erd**
- ✅ tables[N] remove op 작동
- ✅ tables[name=foo].columns[name=bar].description path-by-key
- ⚠️ 논리·물리 페어 항상 동시 갱신

**adr**
- ❌ references에 ITEM ID 문자열만
- ✅ `{"title": "...", "url": "logicraft://item/<ID>"}` 또는 https://

**diagram_sequence**
- ✅ participants[id=DB].name path-by-key
- ✅ messages[].item_ref 자동 link 추출
- ⚠️ fragments[] index는 messages[] array index 기준
- ⚠️ source mermaid + 정형 필드 둘 다 갱신 (불일치 금지)

**navigation_tree**
- ✅ nodes[key=foo].children[key=bar].visible_when path-by-key
- ⚠️ 숫자 segment 거부 → merge 우회

## Post-edit (편집 후)

### 응답 처리
- [ ] `warnings[]` 처리(★ STEP E2) — `*_IN_PROSE` 를 «이번에 쓴 문단 / 옛 문단»으로 가른다
      - 이번 것: 관계면 칸으로 옮겨 **1회** 재저장 · 관계 아님(경계·선례 등)이면 `prose_refs_kept` 에 사유
      - 옛 것: 손대지 않고 `legacy_prose_refs` 수만
      - 처리 후에도 남은 것만 notes_for_main.unresolved_warnings 에
- [ ] `links: { created, updated, removed, unresolved }` 확인
- [ ] unresolved > 0면 보고에 명시 (자동 추출 실패 ITEM 확인)
- [ ] base_version conflict (409) → get_item 재호출 후 최대 2회 retry

### Cascade 분석 (★ STEP F)
- [ ] `analyze_impact(target_id, depth=2)` 호출
- [ ] direct_dependents + transitive_dependents 모두 cascade_candidates에 포함
- [ ] forward_references는 cascade 아님 (본 ITEM이 참조하는 쪽 — 영향 받는 쪽 아님)
- [ ] severity는 analyze_impact의 severity_score 기반

### 자동 추정 (사용자 결정 #4)
다음 우선순위로 brownfield 메타 채움:
1. edit_context 명시 인용
2. 로컬 코드 `Grep` (edit_context 가 알려 준 1차 소스·레포 경로)
3. `find_legacy_artifact` MCP
4. 실패 시 `auto_estimation_failed: [field]` 보고

## 보고 형식 (★★★ 엄격)

```yaml
edited:
  id: ...
  type: ...
  base_version: ...
  new_version: ...
  diff_summary: ...
  fields_changed: [...]
  warnings: [...]
  auto_estimation_failed: [...]
  fields_written: [{field, value, basis}]
  fields_left_empty: [{field, reason}]
  prose_refs_kept: [{id, reason}]
  legacy_prose_refs: <수>
  history_to: change_summary|<경위 칸>|none
  data_mode: patch|merge|replace
  review_marks: {mode, declared, before, resolved, kept, restored}

cascade_candidates:
  - id: ...
    type: ...
    reason: ...
    severity: low|medium|high
    auto_propagate: true|false
    depends_on_completion: [...]
    suggested_edit_intent: ...

notes_for_main:
  user_decisions_needed: [...]
  unresolved_warnings: [...]
  follow_up: ...
```

## 절대 금지
- [ ] 자유 텍스트 보고 (YAML만)
- [ ] Agent 도구 호출 (재귀 방지)
- [ ] 사용자 직접 질문
- [ ] create_item / delete_static_render (메인 지시 없이)
- [ ] 다른 ITEM 편집 시도 (1 specialist = 1 ITEM) — 같은 ITEM 의 STEP E2 재저장 1회는 허용
- [ ] 가이드 응답 읽지 않고 편집

## 자가 검증 (보고 직전 체크)
1. STEP A~H 모두 수행했는가? (D2 칸 채우기 · E2 경고 처리 · F2 끝 점검 포함)
2. YAML 형식이 cascade-patterns.md 규격과 일치하는가?
3. warnings 누락 없는가? «이번 것»이 남아 있지 않은가?
6. 이번에 쓴 산문에 ID 나열·경위 문장이 없는가? 경위는 change_summary 에 갔는가?
4. cascade_candidates에 처리 완료 집합 ITEM 포함되지 않았는가?
5. auto_propagate 판단이 보수적인가? (의심스러우면 false)
