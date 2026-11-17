## 백필 레인 (시범 · `parallel_lanes`)

설계 반영은 LogiCraft 와 MASTER 의 **설계반영 칸**만 건드린다 — 구현 레인과 파일이 겹치지 않는다.
그래서 **백필 전용 레인**으로 돌리고, 구현 레인 동시 상한({{lane_concurrency}})에 **세지 않는다**.

<!-- IF backfill_lane_auto == on -->
- ★ **묻지 않고 띄운다** — CO 가 합쳐져 설계반영 ⏳ 가 생기면(또는 몇 건 모아) 「백필 진행할까요?」를 묻지 않고 백필 레인을 띄운다
  (온보딩에서 사용자가 상시 승인). 지시문은 이 스킬 호출 + **「Phase 1 게이트 사전 승인」**을 적는다.
  결과(🎨 · 확인 필요 · 새로 등록한 ITEM)만 보고한다. 근거 약한 항목은 여전히 「확인 필요」로 남긴다 — 사전 승인은 추정 반영 허가가 아니다.
<!-- ELSE -->
- 백필 레인을 띄울지는 **매번 사용자에게 묻는다**(온보딩 확정 — `backfill_lane_auto=off`).
<!-- ENDIF backfill_lane_auto -->
- 띄우기: <!-- IF worktree_tool == orca -->`scripts/lanes/lane-orca.sh --kind backfill bf<번호> CO-NNN "설계 반영 CO-…" <지시 파일>`<!-- ELSE -->`scripts/lanes/lane-new.sh --kind backfill bf<번호> CO-NNN` → 지시문에 표준 블록을 붙여 이 스킬을 부른다<!-- ENDIF worktree_tool -->.
- **이 레인이 MASTER 의 설계반영 칸의 주인이다** — 구현·배포 칸은 쓰지 않는다(메인 몫). 합치기는 다른 레인과 같다(`lane-merge.sh`).
- 같은 ITEM 을 두 백필 레인이 동시에 고치지 않게 한다 — 나누는 축은 CO 가 아니라 **ITEM 소유권**(Phase 1.5).
