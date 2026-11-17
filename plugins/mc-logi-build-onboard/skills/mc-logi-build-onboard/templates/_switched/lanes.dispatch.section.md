## 병행 레인 (시범 · `parallel_lanes`)
Phase 3 게이트에서 CO 를 **레인**(워크트리 하나 + 작업자 하나)으로 보낼지 메인(Phase 4)에서 할지 정한다. 구현 레인은 동시에 **{{lane_concurrency}}개**까지(백필·조사 레인은 세지 않는다). 📎 reference「병행 레인」

**레인 판정 — 넷 다 통과해야 레인** (하나라도 걸리면 메인)
1. 고칠 파일이 열린 레인·점유와 **안 겹친다**<!-- IF work_claim -->(`list_work_claims` overlapping)<!-- ENDIF work_claim --> — 겹치는 CO 여럿은 **같은 레인에 차례로**(CO 마다 커밋 하나)
2. **스키마 마이그레이션이 없다**(있으면 메인에서 — Phase 3.5 절차 — 하거나 번호를 미리 박아 보낸다)
3. 공용 부품(<!-- IF code_boundary == package -->{{shared_base}}<!-- ELSE -->여러 도메인이 함께 쓰는 부품<!-- ENDIF code_boundary -->)을 크게 바꾸지 않는다
4. 아직 메인에 없는 **앞 일의 결과에 기대지 않는다**

**띄우기 (메인에서)** — ① **CO 를 메인에 먼저 커밋**(§6 도 채워서 · 레인은 메인 끝에서 갈라진다) ② **번호는 메인이 정한다** — CO·마이그레이션 번호는 메인 최대값과 **열린 레인 브랜치들의 것까지**(`git for-each-ref refs/heads/lane/` + 레인 기록) 보고 정해 레인 지시에 **박아** 보낸다(레인은 번호를 새로 잡지 않는다) ③ 기본 길은 **{{worktree_tool}}**:
<!-- IF worktree_tool == orca -->
   - 구현 레인 = Orca 작업자: `scripts/lanes/lane-orca.sh <이름> CO-NNN "<제목>" <지시 파일>` — 먼저 `--dry-run` 으로 spec 을 본다. QA·조사·시안은 서브에이전트(워크트리가 필요하면 `lane-new.sh --kind other <이름>`).
<!-- ELSE -->
   - 구현 레인 = git 워크트리 + 서브에이전트: `scripts/lanes/lane-new.sh <이름> CO-NNN` → 지시문에 `.claude/lanes/lane-prompt-block.md` 의 「복사 시작~끝」을 붙여 도메인 에이전트를 띄운다(`worktree:` = 레인 경로). 이 길은 격리가 지시뿐이다 — **블록을 줄이지 마라.** Orca 가 있으면 `lane-orca.sh` 도 쓸 수 있다.
<!-- ENDIF worktree_tool -->
   - 🚫 새 공간은 늘 `git worktree add`(또는 Orca)로 — 워크트리 폴더를 `cp` 로 복사하지 마라. 준비는 `scripts/lanes/lane-prep.sh`. 레인이 끝나면(보고 회수) **QA** → **합치기**.

**QA — 레인 커밋에 고정**
- `scripts/lanes/lane-qa.sh <라벨> <프롬프트>` 를 **메인 폴더에서**. 프롬프트에 넷(빠지면 거절): `knowhow_dir_abs: <메인에서 "$(git rev-parse --show-toplevel)/{{knowhow_dir}}" 로 계산한 절대경로>` · `lane_worktree: <레인 절대경로>` · `lane_commit: <레인 HEAD sha>` · 범위 줄 `QA 범위: 전체 시험은 합치기에서 한 번만 돈다 — 여기서는 바꾼 파일·직접 사용처·변이만`(이 문장 그대로).
- ☠️ **QA 동안 그 레인에 쓰지 않는다**(바뀌면 무효 21). 판정은 **verdict 줄**(없으면 「QA 안 돎」 20 → `{{qa_fallback}}`). 셸 명령이 없는 갈래면 22 — 메인이 띄우고 로그를 남겨 `lane-qa.sh --verdict-from <로그>`. pass 전에 Phase 5.5 의 **인용 확인**도 한다.
  fail 이면 같은 레인에 재작업(새 커밋으로 QA 다시). 레인 QA 범위는 바꾼 파일 · 1홉 · 변이 — 레인이 아닌 기존 방식의 QA 범위는 그대로(회귀 범위 2단).

**합치기 — 한 줄씩**
- `scripts/lanes/lane-merge.sh <이름> [--with <그룹>] [--check '<이름>|<통과줄>|<명령>'] [--push]` — **메인 폴더에서**, 먼저 `--plan`.
  🚦 **`--plan` 결과를 사용자에게 보이고 동의를 받은 뒤** 실행한다(메인 브랜치를 바꾸고, 레인 폴더의 남은 프로세스를 끝내고, 워크트리를 지운다). `--push` 는 그 동의에 푸시까지 들어 있을 때만(프로젝트 `CLAUDE.md` 가 상시 허용하면 예외). Orca 작업자 레인은 `worker_done` 을 확인한 **뒤에**.
  순서: rebase → 빨리감기 → 메인 검사 → (초록·`--push`) 푸시 → Orca 작업자 놓아주기 → 남은 프로세스 끝내기 → 워크트리·브랜치·레인 기록 정리.
- **rebase 충돌**(3)이면 abort 하고 멈춘다 — ☠️ 손으로 합치지 말고 레인을 재작업으로. git 잠금(8)은 충돌이 아니다. **검사 빨강**(5)이면 합친 채 푸시·정리만 멈춘다 — 레인에서 고쳐 커밋하고 같은 명령을 다시. 대화형 프로세스가 남으면 정리가 멈춘다(7) — 사용자에게 닫아 달라고 하고 다시.
- 합치기는 **한 번에 하나**(같은 파일을 건드리던 레인이 합쳐지면 남은 레인에 미리 rebase). 화면 확인은 **합친 뒤 메인에서**(레인 웹 포트에는 로그인 세션이 없다).
<!-- IF lane_heavy_tests -->
- **무거운 시험은 한 번에 한 레인** — {{lane_heavy_tests}}. 레인 안에서는 돌리지 않고 합칠 때 `--check` 로 한 레인씩.
<!-- ENDIF lane_heavy_tests -->

**공용 기록 — 칸마다 주인**: MASTER 구현·배포 칸 · CO 상태·로그 · 노하우(`{{knowhow_dir}}`)<!-- IF work_claim --> · work_claim<!-- ENDIF work_claim --> · IMPREC = **메인**(합친 뒤) / MASTER 설계반영 칸 · LogiCraft 설계 반영 = **백필 레인** / 그 밖의 레인 = **쓰지 않는다**(보고 `learned` 로).

**레인이 지킬 것**(표준 블록에 박혀 있다): 워크트리 안에서만 · 메인 읽기만 · 키트·생성물 고치지 않기 · 비밀 출력 금지 · 공용 기록·번호 금지 · `git stash`/`checkout --`/`restore`/`add -A` 금지 · 🚫 운영 데이터 금지 · 레인용 로컬 서비스(DB·컨테이너) 정지·삭제는 **사용자 동의** 뒤 메인이.

**배포** — 레인에 넘기지 않는다(메인이 판단). <!-- IF deploy_gate -->자동 금지 — 모아서 **사용자 승인** + 배포 전 확인: {{deploy_gate}}<!-- ELSE -->자동 금지 — 모아서 **사용자 승인**만 받고 한다(별도 배포 전 확인 없음으로 확정).<!-- ENDIF deploy_gate -->
