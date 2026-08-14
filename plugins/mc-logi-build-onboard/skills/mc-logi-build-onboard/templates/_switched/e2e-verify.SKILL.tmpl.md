---
name: {{prefix}}-e2e-verify
description: {{project_name}} 전용 E2E 정합 점검 스킬 (read-only). <!-- IF e2e_design_link == logicraft -->설계(use_case·acceptance·test_scenario)<!-- ELSE -->요구사항 문서<!-- ENDIF e2e_design_link -->·spec 코드·실행 이력을 3방향 대조해 커버리지 공백과 표류를 검출한다. 설계가 바뀌었는데 spec 이 옛 흐름을 검증하는 경우, 로그인 같은 검증 대상이 우회로만 처리된 경우, 근거 없는 spec, 오래된 실행 이력을 잡는다. 사용자가 "E2E 정합 확인", "시나리오 최신인지 봐줘", "커버리지 점검", "설계 바뀐 거 시나리오에 반영됐나", "/{{prefix}}-e2e-verify" 를 요청하면 실행. 검출만 하고 수정하지 않는다 — 후속은 author/dispatch 로 넘긴다.
---

# {{prefix}}-e2e-verify — E2E 정합 점검 (read-only)

**설계 · spec · 실행 이력**이 서로 어긋난 지점을 찾는다. 고치지는 않는다.

## ★ 핵심 원칙

1. **3방향 대조.** 둘만 보면 어느 쪽이 틀렸는지 모른다. 설계(무엇을 검증해야 하나) ·
   spec(무엇을 검증하고 있나) · 실행 이력(실제로 검증됐나)을 함께 본다.
2. **읽기만.** 설계도 spec 도 고치지 않는다. 검출·분류·핸드오프까지가 이 스킬의 끝이다.
3. **통과 = 검증됨이 아니다.** 옛 흐름을 검증하는 spec 도 초록으로 통과한다. 초록을 신뢰하지 않는다.
4. **근거를 붙인다.** 모든 발견은 ID·파일·라인·버전 근거와 함께. 추정이면 추정이라 적는다.

## 프로젝트 상수
```yaml
<!-- IF e2e_design_link == logicraft -->
project_id: {{project_id}}
<!-- ENDIF e2e_design_link -->
conventions: ".claude/e2e-conventions.md"
spec_root:   "{{e2e_root}}"
```

## 파이프라인

### Phase A — 점검 범위 확정
사용자가 지정한 범위(도메인·화면·UC), 없으면 전체. 규모가 크면 도메인 단위로 나눠 보고한다.

### Phase B — 3방향 재고 수집
<!-- IF e2e_design_link == logicraft -->
1. **설계**: `list_items(type=test_scenario|use_case|acceptance)` +
   대상 상세(`get_item`). 각 ITEM 의 `current_version`·`stale`·`stale_reason` 을 함께 본다.
2. **spec**: `{{e2e_root}}` 전량 스캔. `@design` 태그·상단 근거 주석·`test.step()` 목록을 추출.
3. **실행 이력**: `list_test_runs` / 대상별 `get_test_history`(latest·latest_at·pass_rate).
<!-- ELSE -->
1. **요구사항**: 문서·이슈에서 검증 대상 목록
2. **spec**: `{{e2e_root}}` 전량 스캔 (상단 근거 주석·`test.step()` 목록)
3. **실행 이력**: 최근 리포트·CI 결과
<!-- ENDIF e2e_design_link -->

### Phase C — 대조 · 분류
다음 유형으로 분류한다. **유형이 곧 후속 액션을 결정한다.**

| 유형 | 무엇 | 검출 방법 |
|---|---|---|
| **coverage_gap** | 검증해야 하는데 spec 이 없음 | 어떤 spec 도 참조하지 않는 UC/AC<!-- IF e2e_design_link == logicraft -->(특히 `priority=must/critical`, `verification_method=automated_test`)<!-- ENDIF e2e_design_link --> |
| **spec_drift** | 설계는 최신, spec 이 옛 흐름 검증 | spec 이 참조하는 ID 의 설계 본문과 spec 의 step·기대값이 불일치 |
| **design_stale** | spec·앱이 실제, 설계가 뒤처짐 | spec 이 검증하는 실제 동작이 설계에 없음<!-- IF e2e_design_link == logicraft --> / 참조 ITEM 이 `stale=true`<!-- ENDIF e2e_design_link --> |
| **orphan_spec** | 근거 없는 spec | 상단 근거 주석·`@design` 태그 없음, 또는 참조 ID 가 실재하지 않음 |
| **auth_bypass_only** | 인증이 **검증 대상**인데 우회로만 처리됨 | 로그인·권한 UC/AC 가 있는데, 그것을 **화면으로 조작하는** spec 이 없음 |
| **stale_result** | 검증된 지 오래됨 | `latest_at` 이 참조 설계의 `last_updated_at` 보다 과거 = 설계 변경 후 재검증 안 됨 |
| **untrustworthy_green** | 통과했지만 신뢰 불가 | 정리 로직 없음 / 단정(assert) 없는 step / `expected` 없는 step |
| **untagged_spec** | 그룹 태그가 없어 선택 실행에서 누락 | spec 에 그룹 태그 없음 (규약의 시나리오 그룹 절) |
| **permanently_skipped** | 항상 skip 되어 사실상 검증 안 됨 | 시드 계정 미주입·조건부 skip 이 계속 걸림 — 실행 이력에 pass 가 없고 skip 만 쌓임 |

> ★ **auth_bypass_only 를 반드시 본다.** 로그인을 전제조건으로 우회하는 것은 정상이지만,
> 그것만 있으면 로그인은 한 번도 검증되지 않은 채 모든 시나리오가 초록이 된다.
> 규약(`.claude/e2e-conventions.md` 인증 절)의 분리가 지켜졌는지 확인한다.

### Phase D — 보고 · 핸드오프
우선순위(P0 커버리지 공백·인증 미검증 / P1 표류 / P2 품질)로 정렬해 제시한다.

```
[P0] coverage_gap — AC-0NN "…" (priority=critical, automated_test) 를 덮는 spec 없음
     근거: {{e2e_root}} 전량에 AC-0NN 참조 0건
     → {{prefix}}-e2e-author 로 시나리오 저작

[P1] spec_drift — login-ui.spec.ts 가 UC-00N v3 기준, 현재 v5
     근거: UC-00N.alternate_flows 에 신규 분기 추가됨(v4)
     → {{prefix}}-e2e-author 로 갱신
```

핸드오프 버킷은 셋뿐이다:
- **spec 수정** → `{{prefix}}-e2e-author`
- **앱 수정** → `{{prefix}}-dispatch`
<!-- IF e2e_design_link == logicraft -->
- **설계 갱신** → `mc-logi-update` 또는 `{{prefix}}-design-backfill`
<!-- ENDIF e2e_design_link -->

## 게이트 요약
점검 범위 확인 1회. 나머지 자동 (읽기만 하므로).

## 원칙
- **read-only** — ITEM·spec·앱 무엇도 고치지 않는다.
- **초록을 의심한다** — 통과 여부가 아니라 "무엇을 검증하고 있는가"를 본다.
- **근거 필수** — ID·파일·버전 없는 지적은 하지 않는다.
- **분류가 핸드오프** — 유형별로 갈 곳을 지목한다.
