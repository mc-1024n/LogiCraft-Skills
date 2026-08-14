---
name: {{prefix}}-e2e-run
description: {{project_name}} 전용 E2E 실행 스킬. 실행 전 서비스 기동·환경 전제를 먼저 확인하고, Playwright 를 돌려 결과를 수집한 뒤 실패를 원인별(앱 결함 / spec 문제 / 환경)로 분류한다.<!-- IF e2e_design_link == logicraft --> 결과는 record_test_run 으로 LogiCraft 에 역등록해 설계의 검증 상태를 갱신한다.<!-- ENDIF e2e_design_link --> 사용자가 "E2E 돌려줘", "테스트 실행", "시나리오 검증해줘", "/{{prefix}}-e2e-run" 등 실행을 요청하면 실행. 환경 전제가 어긋나면 실행하지 않고 보고한다.
---

# {{prefix}}-e2e-run — E2E 실행 · 결과 회수

돌리기 전에 **돌릴 수 있는 상태인지** 먼저 본다. 그 다음 돌리고, 결과를 정직하게 회수한다.

## ★ 핵심 원칙

1. **환경부터 확인.** 전제가 깨진 채 돌리면 전부 red 가 나오고, 그 red 는 아무것도 알려주지 않는다.
   어긋나면 **실행하지 말고 보고**한다.
2. **red 를 가공하지 않는다.** 실패는 실패로 보고한다. 통과시키려고 spec 을 느슨하게 고치지 않는다.
3. **실패 원인을 분류한다.** 앱 결함 / spec 문제 / 환경 문제는 후속 액션이 완전히 다르다.
4. **실행만.** 앱 코드도 spec 도 이 스킬은 고치지 않는다. 고칠 곳을 지목해 넘긴다.

## 프로젝트 상수
```yaml
<!-- IF e2e_design_link == logicraft -->
project_id: {{project_id}}
<!-- ENDIF e2e_design_link -->
conventions: ".claude/e2e-conventions.md"    # ★ 착수 전 정독
spec_root:   "{{e2e_root}}"
run_cmd:     "{{e2e_run_cmd}}"
```

## 파이프라인

### Phase A — 환경 확인 (실행 전 필수)
규약의 기동 절차대로 확인한다. **떠 있다고 가정하지 않는다.**
1. 서비스 응답 확인 — 안 떠 있으면 규약대로 기동하고 준비될 때까지 대기
<!-- IF e2e_env_caveat -->
2. **환경 전제 확인**: {{e2e_env_caveat}}
   → 어긋나면 **실행 중단**. 사용자에게 현재 상태와 맞추는 방법을 알리고 지시를 받는다.
<!-- ENDIF e2e_env_caveat -->
<!-- IF e2e_fixture_setup -->
3. 사전 데이터(fixture) 확인 — 없으면 규약대로 준비
<!-- ENDIF e2e_fixture_setup -->
<!-- IF e2e_auth == none -->
<!-- ELSE -->
4. **계정 확인** (규약 계정 절)
   - setup 이 만드는 `storageState` 는 실행 시 자동 생성되므로 미리 볼 필요 없다.
<!-- IF e2e_seed_accounts -->
   - **시드 계정 주입 여부**를 확인한다. 값이 없으면 해당 시나리오가 skip 되므로,
     **실행 전에 무엇이 skip 될지 사용자에게 알린다**(돌린 뒤 "통과"로 보이면 오해가 생긴다).
<!-- ENDIF e2e_seed_accounts -->
<!-- ENDIF e2e_auth -->

### Phase B — 실행
```
{{e2e_run_cmd}}
```
- 대상은 사용자가 지정한 spec, 없으면 전량.
- **그룹 선택 실행**(규약의 시나리오 그룹 절) — 사용자가 범위를 말했으면 태그로 좁힌다:
  `--grep @smoke`(핵심만) / `--grep-invert @provisioning`(계정 생성 흐름 건너뛰기).
  범위를 안 밝혔고 전량이 오래 걸리면 **무엇을 돌릴지 먼저 제안**한다(가입·승인은 느리다).
- 결과 파싱이 필요하면 JSON 리포터로 함께 받는다(`--reporter=json`).
  Playwright JSON 의 각 result 는 `status`·`duration`·`errors` 와 `steps[]`(제목·duration·error)를 준다.
- 타임아웃·행이 걸리면 무한정 기다리지 말고 중단 후 원인 보고.

### Phase C — 결과 분류
실패마다 원인을 판정한다. **추정이면 추정이라고 적는다.**

| 분류 | 신호 | 후속 |
|---|---|---|
| **앱 결함** | 기대 동작이 실제로 안 일어남(응답 코드·상태 전이·데이터 미생성) | `{{prefix}}-dispatch` 로 수정 요청 |
| **spec 문제** | 셀렉터 불일치·strict mode 위반·타이밍(대기 부족)·기대값 오기 | `{{prefix}}-e2e-author` 로 수정 |
| **환경 문제** | 서비스 미기동·인증 설정 불일치·fixture 부재·포트 충돌 | Phase A 재확인 후 재실행 |
| **설계 표류** | 앱은 정상인데 spec 이 옛 흐름을 검증 중 | `{{prefix}}-e2e-verify` 로 정합 점검 |

실행 후 **잔여 테스트 데이터가 남았는지 확인**한다(정리 로직이 안 돌았다는 신호).

<!-- IF e2e_design_link == logicraft -->
### Phase D — 역등록  🚦게이트
`record_test_run` 으로 LogiCraft 에 결과를 남긴다.

> ⚠️ **기록은 MCP 로 삭제할 수 없다.** 잘못 남기면 이력에 영구히 남는다.
> 실험·검증 목적이면 `title`·`notes` 에 `[검증]` 을 명시하거나, 아예 남기지 않는다.

- 대상 spec 이 `@design TEST-NNN` 를 갖고 있을 때만 등록한다. 없으면 건너뛰고 보고
  (근거 없는 target 에 기록하면 설계 상태가 오염된다).
- `results[].target_id`: spec 의 `@design` 태그(TEST-NNN / AC-NNN)
- `results[].step_results[]`: `test.step()` 결과를 **seq 순서대로** 매핑.
  `expected` 는 설계 steps 의 예상결과, `actual` 은 실제 관측값.
- `kind`·`environment`·`runner`·`source: ci|manual|ai` 를 채운다. 어느 환경에서 돈 결과인지가 이력의 핵심.
- 응답의 `unknown_targets`·`warnings` 를 확인해 사용자에게 노출한다
  (`unknown_targets` 가 비어있지 않으면 = spec 의 태그가 실제 ITEM 과 안 맞는다).
- 실행 전 사용자에게 **무엇을 어디에 기록할지** 확인받는다.
<!-- ENDIF e2e_design_link -->

### Phase E — 보고
- 실행 결과: 총 건수 / 통과 / 실패 / 소요
- 실패 목록 — **분류 + 근거 + 지목한 후속 스킬**
- **건너뛴·skip 된 것** — 그룹 필터로 제외했거나 시드 미주입으로 skip 된 시나리오를 명시한다.
  **"검증 안 함"이지 "통과"가 아니다.** 이걸 빼면 초록만 보고 다 됐다고 오해한다.
- 잔여 데이터 유무
<!-- IF e2e_design_link == logicraft -->
- 역등록한 run_id·대상 / 건너뛴 spec 과 사유
<!-- ENDIF e2e_design_link -->

## 게이트 요약
1. Phase A — 환경 전제 어긋남 → 실행 여부 확인
<!-- IF e2e_design_link == logicraft -->
2. Phase D — 역등록 대상·범위 확인
<!-- ENDIF e2e_design_link -->
그 외 자동.

## 원칙
- **환경 먼저** — 전제 깨진 실행은 정보가 0 이다.
- **red 그대로** — 통과시키려 spec 을 느슨하게 만들지 않는다.
- **원인 분류** — "실패했다"로 끝내지 않고 어디를 고쳐야 하는지 지목한다.
- **실행만** — 앱·spec 수정은 각각 dispatch·author 의 몫.
