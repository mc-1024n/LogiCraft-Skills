
### Phase 3.5 — 점유 선언 (work_claim create)
게이트 승인 직후, Phase 4 fan-out **전에** 메인이 CO 당 claim **1개**를 생성한다(owner=사용자 키 자동). claim 은 CO 전체를 덮는다(도메인 여럿이면 경로·ITEM 을 합집합으로).
```
create_work_claim(project_id,
  intent: "CO-NNN <제목>",                 # ≤200자
  claimed_paths: [<영향 code_root 경로 globs 합집합>],
  claimed_items: [<CO §6 예상 설계 ITEM>],  # 없으면 []
  design_pending: true,                     # ★ 코드 먼저·설계 나중 = 항상 true 로 시작
  branch: <있으면>)
```
반환 `claim_id`(full UUID)를 **CO 상단 헤더 표의 `work_claim` 행**(정본)에 기록 — backfill 이 여기서 집어 close 한다. 보조로 §7·MASTER 커밋열에도 짧게. ★ **claim 을 열었으면 반드시 헤더 행에 claim_id 를 박는다** — 비면 backfill 이 어느 claim 을 닫을지 몰라 drift 신호가 TTL 만료까지 방치된다. `conflicts[]` 있으면 사용자에게 노출(advisory). 생성 실패(MCP 다운)여도 구현은 진행하되 "점유 미선언"을 보고하고 헤더 행에 `(점유 미선언 — MCP 실패)` 표기.
