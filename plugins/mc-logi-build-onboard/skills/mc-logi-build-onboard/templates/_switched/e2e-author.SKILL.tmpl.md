---
name: {{prefix}}-e2e-author
description: {{project_name}} 전용 E2E 시나리오 저작 스킬. <!-- IF e2e_design_link == logicraft -->LogiCraft 설계(use_case·acceptance·screen_spec)를 근거로<!-- ELSE -->요구사항 문서와 실제 화면을 근거로<!-- ENDIF e2e_design_link --> 시험 시나리오를 도출하고, Playwright MCP 로 실제 화면을 탐색해 셀렉터를 확정한 뒤 spec 을 생성한다.<!-- IF e2e_design_link == logicraft --> 확정된 시나리오는 test_scenario(TEST-NNN) ITEM 으로 등록해 설계 그래프에 연결한다.<!-- ENDIF e2e_design_link --> 사용자가 "E2E 시나리오 만들어줘", "이 화면 시나리오 작성", "UC-00N 시험 시나리오", "/{{prefix}}-e2e-author" 등 시나리오 저작을 요청하면 실행. 대상·시나리오 초안은 사용자 확인 후 진행(AI 임의 진행 금지).
---

# {{prefix}}-e2e-author — E2E 시나리오 저작

설계와 실제 화면을 대조해 시나리오를 만들고, **돌아가는 spec 까지** 내놓는다.

## ★ 핵심 원칙

1. **설계가 "무엇을", 화면이 "어떻게".** 설계는 검증 대상(무엇을 확인할지)을 주고, 실제 화면 탐색은
   셀렉터(어떻게 조작할지)를 준다. 설계만 보고 셀렉터를 추정하면 깨지는 spec 이 나온다.
2. **차단 요소는 분할점이지 제외 사유가 아니다.** 승인·권한·외부연동 때문에 바로 검증이 안 되면
   "미커버"로 넘기지 말고 **시나리오를 나눈다**(신청 → 승인 → 결과). 그 절차 자체가 요구사항이다.
3. **실행하지 않은 spec 은 만들다 만 것이다.** 셀렉터가 맞는지는 돌려봐야만 안다(Phase G 필수).
4. **못 한 것은 드러낸다.** 커버 못 한 AC/UC 는 이유와 함께 파일과 보고에 명시. 조용히 빠뜨리지 않는다.
5. **오케스트레이션 + 저작만.** 앱 코드는 고치지 않는다. 앱에 문제가 있으면 보고하고 `{{prefix}}-dispatch` 로 넘긴다.

## 프로젝트 상수
```yaml
<!-- IF e2e_design_link == logicraft -->
project_id: {{project_id}}
<!-- ENDIF e2e_design_link -->
conventions: ".claude/e2e-conventions.md"    # ★ 착수 전 정독 (경로·인증·정리·셀렉터)
spec_root:   "{{e2e_root}}"
```

## 파이프라인

### Phase A — 대상 확정  🚦게이트①
"무엇을 시나리오로 만들 것인가"를 정한다.
<!-- IF e2e_design_link == logicraft -->
- 사용자가 대상을 지정했으면(UC/AC/화면/도메인) 그 범위로.
- 지정 안 했으면 **커버리지 공백을 근거로 제안**한다:
  `list_items(type=test_scenario)` 로 기존 TEST 를 모으고, `use_case`·`acceptance` 중
  **어떤 TEST 도 covers 하지 않는 것**을 추린다. 그중 우선순위(priority=must/critical)가 높은 것부터.
- 이미 같은 흐름을 덮는 TEST 가 있으면 **신규 생성이 아니라 갱신 후보**로 제시한다(중복 생성 금지).
<!-- ELSE -->
- 사용자가 지정한 화면·기능 범위로. 지정 안 했으면 주요 사용자 흐름을 제안한다.
- 기존 `{{e2e_root}}` 의 spec 목록을 훑어 이미 덮인 흐름은 제외한다(중복 금지).
<!-- ENDIF e2e_design_link -->
**★ 유형으로 훑는다 — 눈에 띄는 것부터 집으면 편중된다**
커버리지 공백을 찾을 때 아래 축으로 훑는다. **인증·계정은 이 중 하나일 뿐이다** — 그것만 쌓이면
"로그인은 되는데 정작 업무가 되는지는 아무도 모르는" 상태가 된다.

| 유형 | 무엇을 검증하나 |
|---|---|
| **업무 흐름** (end-to-end) | 여러 화면·역할을 잇는 실제 일 — 등록 → 검토 → 승인 → 반영 |
| **목록·조회** | 검색·필터·정렬·페이징·**빈 상태**·대량 데이터에서의 동작 |
| **폼·입력 검증** | 필수값·형식·중복·경계값 · **저장 후 재조회했을 때 그대로인가** |
| **권한별 차이** | 같은 화면이 역할에 따라 다르게 보이는가(숨김·비활성·차단) |
| **상태 전이** | 초안 → 승인 → 폐기, 되돌리기, 이미 처리된 것 재처리 |
| **파일** | 업로드·다운로드·용량/형식 제한·이어올리기 |
| **에러 처리** | 서버 오류·권한 없음·동시 수정 충돌 시 화면이 무엇을 보여주나 |
| **화면 산출물** | 렌더·내보내기·인쇄처럼 결과물이 나오는 것 |
| **인증·계정** | 로그인·가입·승인 — 요구사항일 때만. 전제조건이면 규약의 우회를 쓴다 |

확인: *"이번 저작 대상: [범위]. 이대로 진행할까요?"*

### Phase B — 설계 정독 (검증 대상 추출)
<!-- IF e2e_design_link == logicraft -->
대상 UC/AC 를 `get_item` 으로 읽고 **검증 항목**을 뽑는다. 근거 ID 를 항상 붙인다.
- `use_case.main_flow[]` → 시나리오 단계의 뼈대
- `use_case.alternate_flows[]` → 분기 시나리오 후보(로컬 로그인·재설정 등)
- `acceptance.scenario.given/when/then` → step 의 사전조건·행위·예상결과
- `acceptance.is_negative` → negative 시나리오(거부·차단)로 분리
- `screen_spec` → 거치는 화면·구성요소
- 설계에 **없는** 검증 항목을 지어내지 않는다. 화면에서 발견한 미설계 동작은 보고만 하고
  `{{prefix}}-design-backfill` 대상으로 넘긴다.
<!-- ELSE -->
요구사항 문서·기존 spec·화면에서 검증 항목을 뽑는다. 출처를 항상 명시한다.
<!-- ENDIF e2e_design_link -->

**★ 차단 요소 판정 (원칙 2 적용)** — 다음이 있으면 시나리오를 **나눈다**:
- 승인·심사 대기 (신청 → 승인 → 이용)
- 권한 계층 (일반 사용자 / 관리자 — 액터별 별도 컨텍스트)
- 상태 전이 (생성 → 활성 → 비활성)
"준비가 복잡하다"는 제외 사유가 아니다. 정말 자동화 불가한 것(외부 실서비스 의존 등)만 미커버로 두고
**이유를 적는다**.

<!-- IF e2e_auth == none -->
<!-- ELSE -->
**★ 계정 요구 판정** — 이 시나리오가 **어떤 계정**을 필요로 하는지 먼저 정한다(규약 계정 절):
- **어떤 역할인가** — 규약의 역할 목록에 없으면 그 역할을 어떻게 확보할지부터 정한다.
  권한이 없어 403 이 나는 것을 "미커버"로 넘기지 않는다.
- **새 계정으로 되는가, 데이터가 쌓인 계정이어야 하는가** — 대량 목록·페이징·통계·오래된 이력은
  갓 만든 빈 계정으로 검증되지 않는다. 이 경우 **시드 계정이 필요하다고 보고**하고,
  자격증명은 환경변수로 받도록 설계한다(spec 하드코딩 금지).
- **계정 확보 자체가 검증 대상인가** — 가입·승인 흐름이면 그것은 `@provisioning` 시나리오다.
  다른 시나리오는 그 흐름을 반복하지 말고 setup 이 만든 `storageState` 를 쓴다.
<!-- ENDIF e2e_auth -->

### Phase C — 실제 화면 탐색 (셀렉터 확정)
Playwright MCP 로 대상 흐름을 **직접 타본다**. 규약(`.claude/e2e-conventions.md`)의 인증·셀렉터 정책을 따른다.
1. `browser_navigate` 로 진입 → `browser_snapshot` 으로 접근성 트리 확인
2. 각 단계를 실제로 조작(`browser_click`/`browser_type`/`browser_fill_form`) —
   MCP 가 반환하는 Playwright 코드가 곧 셀렉터 초안이다
3. **검증 앵커를 찾는다**: 성공·실패 시 화면에 나타나는 것(heading·상태 badge·토스트·URL 변화·응답 코드)
4. 실패 경로도 실제로 유발해 문구를 확인한다(추정 금지)

> 앱이 안 떠 있으면 규약의 기동 절차대로 띄운다. 환경 전제(`e2e-conventions.md` ⚠️)가 어긋나면
> 탐색 전에 먼저 맞춘다.

### Phase D — 시나리오 초안  🚦게이트②
표 형태로 제시한다. **step 은 "행위 + 예상결과" 쌍**으로 쓴다(예상결과 없는 step 은 검증이 아니다).

```
TEST 초안: <제목>   kind: integration|system
근거: UC-00N, AC-0NN, SCREEN-0NN
전제조건: ...
 seq | 행위                | 입력       | 예상결과                  | 화면
  1  | 로그인 화면 진입     | -          | 로그인 폼 표시            | SCREEN-001
  2  | 잘못된 자격증명 제출 | 임의 계정  | 401 + "…올바르지 않습니다" | SCREEN-001
미커버: AC-0NN (사유: …)
```
사용자 검토·수정 후 확정.

<!-- IF e2e_design_link == logicraft -->
### Phase E — TEST ITEM 등록
확정 시나리오를 `test_scenario` 로 등록한다. **등록 전 `get_item_schema("test_scenario")` 정독.**
- `kind`: 여러 UC 를 잇는 end-to-end → `integration` / REQ·NFR 검증 → `system`
- `steps[]`: Phase D 표 그대로 (seq·action·test_item·preconditions·input_data·expected·screen_ref)
- **링크 최소 1개 필수** — `covers_use_cases`(통합) 또는 `verifies_requirements`/`verifies_nfrs`(시스템).
  링크 없는 TEST 는 외톨이가 되어 설계 변경 감지가 안 된다.
- `related_domains`·`exercises_screens`·`related_apis` 도 근거 있으면 채운다.
- 기존 TEST 갱신이면 `update_item`(base_version 필수). 신규 남발 금지.
- 응답의 `warnings[]` 를 사용자에게 노출한다.
<!-- ENDIF e2e_design_link -->

### Phase F — spec 생성
규약대로 `{{e2e_root}}/<슬러그>.spec.ts` 작성.
- 상단 주석: 설계 근거 ID<!-- IF e2e_design_link == logicraft --> + `@design TEST-NNN`<!-- ENDIF e2e_design_link --> + 환경 전제
- **그룹 태그를 반드시 단다**(규약의 시나리오 그룹 절). 태그 없는 시나리오는 선택 실행에서
  누락되거나 항상 딸려온다. 계정 생성 흐름 자체를 검증하면 `@provisioning`.
- `test.step()` 으로 단계 분리<!-- IF e2e_design_link == logicraft --> — 순번을 `steps[].seq` 와 1:1 로<!-- ENDIF e2e_design_link -->
- 정리 로직(`afterEach`)을 **반드시** 넣는다(규약의 정리 절차)
<!-- IF e2e_auth == none -->
<!-- ELSE -->
- **계정은 규약대로** — 전제조건이면 setup 의 `storageState` 를 쓰고, 시나리오 안에서 가입부터
  반복하지 않는다(그건 `@provisioning` 의 몫). 자격증명은 환경변수로 읽는다.
- 시드 계정이 필요한데 주입값이 없으면 **skip 하고 사유를 남긴다**(조용히 통과 금지).
<!-- ENDIF e2e_auth -->
- 액터가 둘 이상이면 컨텍스트 분리
- 하단에 미커버 목록 + 사유

### Phase G — 실행 검증 (필수)
`{{e2e_run_cmd}}` 로 **방금 만든 spec 을 돌린다.**
- **통과할 때까지 고친다.** 단 고치는 대상은 spec 이지 앱이 아니다.
- 실패가 **앱 결함**이면 spec 을 억지로 맞추지 말고 **red 로 두고 보고**한다(원칙 4·5).
  결함 수정은 `{{prefix}}-dispatch` 로 넘긴다.
- 흔한 실패는 셀렉터 문제다 — 규약의 "부분 매칭 충돌"을 먼저 확인한다.
- 실행 후 **잔여 데이터가 0 인지 확인**한다(정리 로직이 실제로 도는지).

### Phase H — 보고
- 생성/갱신한 spec<!-- IF e2e_design_link == logicraft --> · TEST ITEM ID<!-- ENDIF e2e_design_link -->
- 실행 결과(건수·소요·통과 여부) — **red 는 그대로**
- **미커버 목록 + 사유** (숨기지 않는다)
- 탐색 중 발견한 앱 결함·미설계 동작 → 후속 액션 제안

## 게이트 요약
1. Phase A — 저작 대상
2. Phase D — 시나리오 초안 확정
3. 앱 결함 발견 / 설계에 없는 동작 발견 → 그때 확인
그 외 자동.

## 원칙
- **설계 근거 없는 검증 항목을 만들지 않는다** — 화면에서 본 미설계 동작은 backfill 대상으로 보고.
- **차단 요소는 나눈다** — 승인·권한·상태전이는 시나리오 분할점.
- **전제조건과 검증대상을 섞지 않는다** — 규약의 인증 절 참조.
- **실행으로 닫는다** — 안 돌려본 spec 은 미완성.
- **정직 보고** — 미커버·red·앱 결함을 가감 없이.
