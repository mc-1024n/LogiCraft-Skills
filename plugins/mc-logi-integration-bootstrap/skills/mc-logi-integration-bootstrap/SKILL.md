---
name: mc-logi-integration-bootstrap
description: Logicraft 프로젝트의 외부 연동 카탈로그(EXTSYS + INT)를 설계 ITEM 본문에서 자동 발굴해 일괄 등록하는 부트스트랩 스킬. 사용자가 "외부 연동 정리해줘", "EXTSYS 발굴해줘 [프로젝트]", "INT 등록해줘", "외부 시스템 카탈로그 만들어줘", "integration bootstrap" 등을 요청할 때 실행. discover_external_integrations MCP 도구로 FEAT/DFEAT 본문 스캔 → 사용자에게 vendor/owner/criticality 4종 질문 → register_external_system × N → INT 후보 검토 → register_integration_point × M. C4·SEQ 정형 표현 기반 promote_external_systems 와 다른 design-tier 부트스트랩 (시나리오 D).
license: MIT
allowed-tools: Read, Write, Edit, Grep, Glob, Bash, ToolSearch, AskUserQuestion, TaskCreate, TaskUpdate, TaskList
metadata:
  version: "1.0.0"
  domain: logicraft-orchestration
  triggers: 외부 연동 정리, 외부 시스템 발굴, EXTSYS 등록, INT 등록, integration bootstrap, integration discovery, 외부 의존 카탈로그, 외부 연동 카탈로그
  role: orchestrator
  scope: logicraft-external-integration-onboarding
  output-format: 후보 표 + 사용자 확인 + 등록 결과 표
  related-skills: mc-logi-update, mc-logi-domain-review
---

# mc-logi-integration-bootstrap — Logicraft 외부 연동 부트스트랩

설계 ITEM 본문에서 외부 시스템 의존을 발굴해 EXTSYS / INT 카탈로그로 일괄 등록.

## When to Use

- 프로젝트에 EXTSYS / INT 가 거의 없는데 FEAT/DFEAT 에는 외부 의존 언급이 흩어져 있는 상황
- 2차 설계 / brownfield 프로젝트의 외부 연동 정리
- 사용자가 "외부 연동 정리해줘", "EXTSYS 발굴해줘", "외부 시스템 카탈로그 만들어줘" 등 요청

## When NOT to Use

- C4·SEQ 에 이미 external 표현이 정형화되어 있음 → `promote_external_systems` MCP 도구 직접 호출 (시나리오 A)
- 처음부터 등록 (greenfield) → `register_external_system` 직접 호출 (시나리오 B)
- 단일 EXTSYS 수정 / cascade → mc-logi-update
- 도메인 정합 검토 → mc-logi-domain-review

## 핵심 원칙

1. **AI 추정 금지** — vendor / owner_team / criticality / environments 는 사용자 답변만 사용. 모르면 "TBD" 또는 비움.
2. **MCP 도구 경유** — `register_external_system` / `register_integration_point` 만 사용. `db.insert` 직접 우회 금지.
3. **사용자 검토 게이트 2회** — EXTSYS 등록 전, INT 등록 전 각각 사용자 confirm.
4. **벤더 단위 1 EXTSYS** — 같은 벤더의 sub-component (예: GenAI ↔ VLM) 는 1 EXTSYS + 별도 INT 로.
5. **discover 결과는 후보일 뿐** — title / direction / triggers vs invoked 분류는 사용자가 검토 시 수정 가능.

## 워크플로우

### Phase 1 — 진입 + 프로젝트 식별

1. 사용자 요청 파싱:
   - 프로젝트명 명시되면 채택 (예: "KLID 외부 연동 정리해줘")
   - 모호하면 메모리에서 현재 프로젝트 추출 → 없으면 `AskUserQuestion`
2. project_id 확보:
   - `list_projects` 호출 → name 부분 매칭으로 후보 → 사용자 confirm
3. 진입 멘트:
   - "외부 연동 부트스트랩 시작 — 프로젝트: <name>. FEAT/DFEAT 스캔 → 후보 추출 → 사용자 검토 → 일괄 등록."

### Phase 2 — discover 실행

`get_logicraft_guide("external-integration")` 호출하여 시나리오 D 가이드 컨텍스트로 로드 (선택, 첫 사용 시).

`discover_external_integrations({project_id, include_existing: false})` 호출.

응답 파싱:
- `extsys_candidates[]` — 5종 휴리스틱별 후보
- `int_candidates[]` — path 클러스터 단위
- `scanned` — feature_count / dfeat_count / api_count
- `existing_extsys_count` — 이미 등록된 수

### Phase 3 — EXTSYS 후보 검토 + 사용자 질문 (4종)

1. **후보 표 출력**:
   ```
   | # | 후보 | kind | criticality | 근거 FEAT/DFEAT (수) | 매칭 API (수) | DOMAIN |
   |---|------|------|-------------|---------------------|---------------|--------|
   | 1 | KLID 1차 중계서버 | internal_legacy | critical | 18 | 28 | D001/002/009 |
   | ...
   ```

2. **사용자에게 4종 질문** (`AskUserQuestion`):
   - **vendor** : 누가 만든/운영하는지 (예: "CUDO", "행정안전부"). 후보별 다를 수 있음.
   - **owner_team** : 우리쪽 담당 팀 (예: "DX개발팀"). 보통 4건 모두 동일.
   - **수용/제외 후보**: 5개 중 어떤 것을 등록할지 (multi-select).
   - **environments** : prod/stage base URL — 기본 "추후 보강 (빈 배열)".

3. **확정 후 진행 의사 확인** — "위 N건 등록할까요?"

### Phase 4 — register_external_system 일괄 호출

각 확정 후보마다 `register_external_system` 호출:
- name (display_name)
- vendor (사용자 답변)
- kind (후보의 kind 추천)
- criticality (후보의 criticality 추천)
- owner_team (사용자 답변)
- description (후보의 evidence 요약 + 발굴 컨텍스트)
- environments (사용자 답변 또는 빈 배열)
- compliance_tags (보통 빈 배열)

응답에서 `extsys_id` 수집 (후보 key → extsys_id 매핑).

### Phase 5 — INT 후보 검토 + 사용자 confirm

1. **후보 표 출력**:
   ```
   | # | EXTSYS | 제목 | direction | invoked_by_apis (수) | triggers_apis (수) | DOMAIN | status |
   |---|--------|------|-----------|---------------------|--------------------|--------|--------|
   | 1 | EXTSYS-001 | 이벤트 batch 수신 | inbound | 0 | 2 | D001/D009 | active |
   | ...
   ```

2. **사용자 검토 포인트** (한 번의 `AskUserQuestion`):
   - 자동 분류된 direction / triggers vs invoked 가 정확한지 통째 confirm
   - 묶음 변경 (예: 2개 outbound 클러스터를 1개 INT 로 합치기) 필요 시 사용자가 명시
   - status_suggestion 그대로 사용 vs 모두 active 강제

3. 사용자가 수정사항 알려주면 반영.

### Phase 6 — register_integration_point 일괄 호출

각 INT 마다 `register_integration_point` 호출:
- external_system: extsys_id (Phase 4 매핑에서)
- title
- direction
- protocol: "rest"
- transport_meta: { notes: 후보의 reason }
- auth_type: "bearer" 기본 (사용자가 지정 시 변경)
- triggers_apis / invoked_by_apis / used_by_domains (후보값)
- status

### Phase 7 — 최종 보고 + 메모리 저장 문의

```
✅ 외부 연동 부트스트랩 완료 — 프로젝트: <name>

EXTSYS  N건 등록
INT     M건 등록

| EXTSYS | INT 수 | DOMAIN 영향 |
|--------|--------|-------------|
| EXTSYS-001 KLID 1차 중계서버 | 6 | D001/002/009 |
| ...

다음 권장 단계:
- environments 보강 (각 EXTSYS prod/stage base URL)
- INTSPEC 첨부 (정식 OpenAPI 가 있는 INT 부터)
- /integrations 모음 페이지에서 매트릭스/흐름 그래프 확인
```

메모리 저장 여부 문의 (선택).

## 사용자 결정 정책

기본 자동 진행. 다음 경우만 사용자에게 묻기:

1. **Phase 1**: 프로젝트 모호
2. **Phase 3**: vendor / owner_team / 수용 후보 / environments
3. **Phase 5**: INT 분류·묶음 검토
4. **Phase 7**: 메모리 저장 여부 (선택)

## 안티패턴

- ❌ vendor 나 owner_team 을 LLM 이 추정해서 채움 — 항상 사용자에게 물어야 함
- ❌ `db.insert` 또는 seed 스크립트로 우회 — MCP 도구만 경유
- ❌ 후보 검토 없이 바로 등록 — 사용자 confirm 필수
- ❌ 같은 벤더의 sub-component 마다 EXTSYS 분리 — 1 EXTSYS + N INT 로
- ❌ INT 의 direction 을 임의로 bidirectional 로 통일 — 후보의 path 분석 결과 신뢰
- ❌ MAX_DEPTH 반복 — 이 스킬은 cascade 없음. 한 번에 끝.

## 휴리스틱 한계 (사용자에게 알릴 것)

discover_external_integrations 는 다음 9개 휴리스틱만 지원:
- legacy_relay (1차/중계서버)
- genai (생성형 AI / VLM)
- mobile_id (모바일 공무원증)
- gpki (행정전자서명)
- payment (결제 게이트웨이)
- slack
- object_storage (S3/MinIO)
- smtp (이메일)
- public_data (공공데이터/재난안전)

**그 외 시스템은 자동 발견 X.** 휴리스틱에 없는 외부 의존이 있으면 사용자에게 보강 등록 의사 확인 후 `register_external_system` 직접 호출.

## 호출 예시

### 예시 1: KLID 2차 부트스트랩 (실제 시나리오)

```
사용자: "KLID 외부 연동 정리해줘"

→ Phase 1: list_projects → "KLID 2차 - 관제지원시스템 고도화" 매칭
→ Phase 2: discover_external_integrations(project_id) → 5 EXTSYS + 9 INT 후보
→ Phase 3: 표 출력 + 4종 질문
   사용자: vendor=CUDO/딥러닝/행정안전부 owner=DX개발팀
           수용=4건 (public_data 제외) environments=추후
→ Phase 4: register_external_system × 4 → EXTSYS-001~004
→ Phase 5: 9 INT 후보 표 출력
   사용자: "그대로 등록"
→ Phase 6: register_integration_point × 9 → INT-001~009
→ Phase 7: 보고 + 메모리 저장 (Y)
```

### 예시 2: 휴리스틱에 없는 시스템

```
사용자: "외부 연동 정리해줘. 우리 Twilio SMS 도 쓰고 있어"

→ Phase 2: discover → SMTP/Slack 만 매칭 (Twilio 휴리스틱 없음)
→ 사용자에게 알림: "Twilio 는 자동 발견 X. 따로 register_external_system 수동 등록 필요"
→ Phase 3 이후: 발견된 후보 처리
→ 종료 후: Twilio 1건 별도 register_external_system + 관련 INT 추가 안내
```

## 진입 멘트 (메인이 사용자에게 첫 응답)

"mc-logi-integration-bootstrap 시작합니다.

프로젝트: `<name>`
절차: discover → 사용자 검토 (vendor/owner) → EXTSYS 등록 → INT 검토 → INT 등록.

진행할까요?"

사용자 OK 시 Phase 2~7 진행.

## 보안·범위

- 다른 프로젝트 ITEM 영향 X (project_id 고정)
- 기존 EXTSYS 와 중복 등록 안 함 (discover 의 include_existing=false default)
- INT 의 양방향 link 갱신은 register_integration_point 가 자동 (FK 검증 포함)
