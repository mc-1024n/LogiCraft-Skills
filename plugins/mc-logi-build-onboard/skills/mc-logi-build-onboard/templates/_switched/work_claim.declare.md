
### Phase 3.4 — 점유 선언 (work_claim create)
게이트 승인 직후 · fan-out **전에** 메인이 CO 당 claim **1개**(도메인 여럿이면 경로·ITEM 합집합):
`create_work_claim(project_id, intent: "CO-NNN <제목>"(≤200자), claimed_paths: [<영향 code_root globs>], claimed_items: [<CO §6 예상 ITEM · 없으면 []>], design_pending: true, branch: <있으면>)`
- 반환 `claim_id`(full UUID)를 **CO 헤더 표의 `work_claim` 행**(정본)에 반드시 박는다 — 비면 backfill 이 어느 claim 을 닫을지 몰라 drift 신호가 TTL 만료까지 남는다. 보조로 §7·MASTER 커밋열에도 짧게.
- `conflicts[]` 는 사용자에게 노출(advisory). 생성 실패(MCP 다운)여도 구현은 진행하고 「점유 미선언」을 보고 · 헤더 행에 `(점유 미선언 — MCP 실패)`.
