# summary-templates.md — 타입별 구현지향 요약 포맷

목표: 요약만 읽고 **바로 코드 작성**이 가능해야 함. 추상 설명 X, 구현 결정 O.
원본 JSON 은 `_raw/` 에 보존되므로 요약은 "구현자가 알아야 할 것"에 집중.

## 공통 frontmatter (모든 타입 .md 최상단)

```yaml
---
logicraft_item: <ID>
type: <type code>
version: <current_version 정수>
last_updated_at: <ISO>
domain: <DOMAIN-ID>
project_id: <uuid>
synced_at: <ISO>
sync_session: <n>
stale: <bool>
status: <synced|NEW|CHANGED|RETIRED>
prev_version: <CHANGED 일 때만, 아니면 null>
raw: ./_raw/<ID>.json
links:                      # get_neighbors 핵심 링크만 (구현 의존 파악용)
  <link_type>: [<ID>...]
---
```
CHANGED 면 frontmatter 직후 `version-tracking.md` 의 변경 배너 삽입.

## 공통 본문 골격

```markdown
# <ID> — <title>

**한 줄**: <이 ITEM 이 코드로 무엇이 되는가 1줄>

## 구현 요지
<구현자가 만들 것: 클래스/함수/테이블/엔드포인트 단위로 구체적으로>

## 의존 (먼저/함께 구현)
<links 기반: 이 ITEM 구현에 필요한 다른 ITEM ID + 한 줄 이유>

## 구속 제약
<적용 ADR/NFR/GUIDE/CONST — 코드가 반드시 지킬 것>

## (타입별 상세 — 아래 섹션)

## 구현 체크리스트
- [ ] <검증 가능한 구현 단위>
```

---

## domain_feature (DFEAT)

```markdown
## 비즈니스 로직
- 책임: <서비스 계층에서 하는 일>
- 입력 → 처리 → 출력 (서비스 메서드 시그니처 수준으로)
- 트리거: triggers=[EVT-...] / 호출: implemented_by_endpoints=[API-...]
- 소비 이벤트: consumes=[EVT-...]
- 영속: persists_in_tables=[<물리 테이블명>] → 어떤 ERD
- 분기/규칙: <비즈니스 규칙 — if/else 수준으로 구체화>
- 예외/에러: <실패 케이스 + 처리>
- **적용 상수**: uses_constant=[CONST-NNN(`name`=`value` unit)...] ← 상태값·임계치·기본값 등. 분기 조건의 매직넘버는 이 CONST 값 사용(인라인 하드코딩 금지)
- 1차 보존/brownfield: <preserved/modified/new — 기존 코드 재사용 여부>
```

## api_endpoint (API)

```markdown
## 엔드포인트 계약
- `<METHOD> <path>`
- 인증: <헤더/토큰 — ADR 인증정책 반영>
- Path/Query params: <name: type — 설명>
- Request body: <필드: 타입, 필수, 검증규칙> (JSON 예시)
- Response 200: <스키마 + JSON 예시>
- 에러: <status: 조건/코드/메시지> 표
- 구현 DFEAT: <어느 DFEAT 의 로직 호출>
- 흐름: realized_by=[SEQ-...] (호출 순서는 SEQ 요약 참조)
- 권한: required_roles=[ROLE-...]
- **적용 상수**: uses_constant=[CONST-NNN(`name`=`value` unit)...] ← req/res enum·range·임계치 등. **값은 추정 말고 이 CONST 값 그대로**. 역링크 없으면 도메인 CONST 표(IMPLEMENTATION)에서 해당 값 확인
```

## erd (ERD)

```markdown
## 데이터 모델 (구현: 마이그레이션/엔티티)
- level: logical | physical / dbms: <postgresql 등>
- 테이블별:
  ### <물리 테이블명> (논리: <한글명>)
  | 컬럼 | 타입 | 제약 | 설명 |
  |---|---|---|---|
  | id | uuid | PK | ... |
  - 인덱스: <idx 정의>
  - FK/관계: <table.col → table.col, cardinality>
  - 파티셔닝/정책: <있으면>
- 물리면 DDL 초안 (CREATE TABLE) 까지 작성 — 바로 마이그레이션 가능하게
- logical_source/based_on: <논리 ERD ID> (물리일 때)
- **적용 상수**: uses_constant=[CONST-NNN(`name`=`value` unit)...] ← 컬럼 default·CHECK range·enum 값. DDL 의 DEFAULT/CHECK 에 이 CONST 값 그대로 반영
```

## diagram_sequence (SEQ)

```markdown
## 호출 흐름 (코드 시퀀스로 직역)
1. <actor/component> → <component>: <메시지> (어떤 API/메서드)
2. ...
- 동기/비동기 표기, 에러 분기, 보상 트랜잭션
- 참여자 ↔ 코드 매핑: <participant = 어느 클래스/서비스/외부시스템>
- 이 흐름이 구현하는 API/DFEAT: <ID>
→ 구현 시 이 순서대로 호출 배선
```

## screen_spec (SCREEN)

```markdown
## 화면 (UI 구현)
- 경로/라우트: <추정 또는 NAV 참조>
- role=main 본문 sections:
  ### <section name> (layout)
  - components: <컴포넌트: 동작/바인딩 데이터>
  - references_apis: [API-...] → 어떤 데이터 fetch/submit
- 페이지 고유 필터/액션/모달
- consumes_apis: [API-...] (바인딩 표)
- required_roles: [ROLE-...] (노출/가드 조건)
- **적용 상수**: uses_constant=[CONST-NNN(`name`=`value` unit)...] ← 입력 validation 범위·셀렉트 옵션·레이블 등. UI 검증/옵션 값은 이 CONST 값 사용
- static_renders: <_raw 의 static_render URL/HTML 참조 — 와이어프레임>
- 셸(헤더/메뉴/푸터)은 범위 외 (NAV/SHELL 별도)
```

## use_case (UC)

```markdown
## 유스케이스 (→ 통합 테스트 시나리오)
- Actor / 사전조건 / 사후조건
- 주 흐름: 1..n (각 단계 = 테스트 스텝)
- 대안/예외 흐름
- 검증: verified_by=[AC-...]
- 관련 API/SCREEN/DFEAT
→ 테스트 코드 골격으로 변환 가능하게 Given/When/Then 으로 정리
```

## acceptance (AC)

```markdown
## 수용 기준 (→ 테스트 단언)
- 검증 대상: verifies=[REQ-/FEAT-/UC-...]
- 기준: Given <상태> / When <행위> / Then <기대결과> (목록)
- last_run: <있으면 통과 여부 — verified 게이트 참고>
→ 각 기준 = 1 테스트 케이스. 자동화 가능 형태로 기술
```

## domain_event (EVT)

```markdown
## 이벤트 계약
- 이벤트명/토픽: <name>
- payload 스키마: <필드: 타입 — 설명> (JSON 예시)
- 발행자(emitter): <DFEAT/API ID — triggers 로 연결된>
- 구독자(consumer): <DFEAT ID — consumes>
- 전달 보장/순서/멱등성: <정책>
- 버전/스키마 진화 정책
→ 이벤트 타입 정의 + 발행/구독 인터페이스 코드로 직역
```

## permission_role (ROLE)

```markdown
## 역할-권한 (authz 구현)
- role key / 표시명 / 상위 역할
- 권한 매트릭스: | 리소스/액션 | 허용 | 조건(데이터 스코프) |
- 데이터 스코프 규칙 (예: 본인 지자체 한정 — ADR 반영)
- 적용 SCREEN/API: required_roles 역참조
→ 가드/미들웨어/정책 코드로 직역
```

## constant (CONST)

> CONST = 코드/설정/스키마에 **그대로 박을 실제 값**(magic_value·enum·range·default·임계치·token·env_var).
> 구현자가 값을 추정·하드코딩하지 않도록 **단일 진실원**으로 노출한다. `value` 는 **절대 의역 금지** — logicraft 원문 그대로.

```markdown
## 상수 값 (코드/설정에 그대로 박을 값)
- **name**: `<name>`  (예: MIN_BANDWIDTH_MBPS, JWT_EXPIRY_MS)
- **value**: `<value>`   ← logicraft 원문 그대로. 객체/배열이면 JSON 그대로
- **kind**: <token|enum|config|env_var|magic_value>
- **unit**: <ms·px·count·Mbps … / 없으면 "-">
- **의미/결정 근거**: <description 요지>
- **결정 ADR**: based_on/decided_in=[ADR-...]  (왜 이 값인지)
- **근거 REQ**: derived_from/derived_from_requirement=[REQ-...]  (있으면)
- **사용 모듈**: used_in_modules=[MOD-...] (이 상수를 import 하는 기존 코드 모듈)
- **사용 설계 ITEM**(uses_constant 역링크): [API-.../SCREEN-.../ERD-.../DFEAT-...]
  ← 이 값이 실제로 박히는 곳. 역링크 없으면 "⚠️ uses_constant 링크 없음 — description/사용처 수동 확인"
- **env_var 주의**: kind=env_var 이고 is_secret=true 면 값은 placeholder — 실제 시크릿은 코드에 박지 말 것
```
→ enum/range 는 설계 ITEM 본문에 중복 적지 말고 **이 CONST 를 단일 진실원으로** 참조.

## adr (ADR)

```markdown
## 결정 (코드가 반드시 지킬 제약)
- 결정: chosen_option
- 근거: justification (요지)
- **구현 영향**: <이 결정이 코드에 강제하는 것 — 금지/필수 사항 bullet>
- 대체/폐기 대상: <deprecated ITEM>
→ "구현 영향" 이 핵심. IMPLEMENTATION.md 제약 섹션에 집계됨
```

## nfr (NFR)

```markdown
## 비기능 제약 (예산)
- 분류: 성능|보안|가용성|...
- 측정 지표 + 목표값 (예: API p95 < 200ms)
- 구현 강제사항: <코드/인프라에서 지킬 것>
→ 성능 예산·보안 요구를 구현 체크리스트로 변환
```

## implementation_guideline (GUIDE)

```markdown
## 공통 코딩 규칙
- category / rule (원문)
- applies_to_types/tags: <적용 범위>
- 위반 예 / 준수 예
→ 모든 관련 코드에 적용. linter 규칙화 가능하면 명시
```

## code_module (MOD)

```markdown
## 기존 구현 (재사용 — 새로 만들지 말 것)
- 모듈 경로/이름
- realizes: [FEAT-/DFEAT-...] (이미 구현하는 설계)
- 책임/공개 인터페이스
- implementation.status / progress
→ 이 모듈이 커버하는 범위는 재구현 금지, 확장만
```

## feature (FEAT) / class_diagram / diagram_state / integration_point / external_system / AI 거버넌스

```markdown
- feature: 상위 기능 컨텍스트 (specialized_by DFEAT 목록 — 경계 이해용, 간략)
- class_diagram: 클래스/속성/메서드/관계 → 코드 구조 직역
- diagram_state: 상태/전이/가드/액션 → 상태머신 코드
- integration_point/external_system: 외부 시스템·프로토콜·인증·엔드포인트·계약 → 어댑터 코드
- ai_policy/model_usage/guardrail/prompt_template: 모델·프롬프트·가드레일·평가 → AI 호출 코드 제약
```

## 작성 원칙 (fetcher 준수)

1. **구현 결정만** — "사용자가 X 할 수 있다" 같은 일반론 금지
2. **logicraft 데이터 충실** — 값/이름/타입/경로 의역·추정 금지. 모르면 "원본 _raw 참조" 명시
3. **링크는 ID 로** — 의존 ITEM 은 ID 로 적어 IMPLEMENTATION.md 그래프와 연결
4. **코드 직역 가능 수준** — ERD→DDL, API→시그니처, SEQ→호출순서, AC→테스트
5. **불확실은 표기** — logicraft 에 없는 정보는 채우지 말고 `⚠️ 미정 (logicraft 미기재)` 로 남김