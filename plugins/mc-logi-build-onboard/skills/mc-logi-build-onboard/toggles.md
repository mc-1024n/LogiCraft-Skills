# toggles.md — 구현 오케스트레이션 세트의 스위치 정의 (온보딩의 두뇌)

이 파일은 `mc-logi-build-onboard` 가 **현재 프로젝트에 맞는 구현 오케스트레이션 세트**(dispatch / design-backfill / (선택) build 스킬 / (선택) E2E 3종 + 도메인 implementer·qa-verifier 에이전트)를 조립할 때 참조하는 **의사결정 규칙**이다.

핵심 발상: 프로젝트마다 세트가 달라지는 이유는 "값 몇 개"가 아니라 **15개 구조 스위치의 on/off 조합**이다. 아키타입(greenfield-monolith / brownfield-submodule)은 그 스위치의 **프리셋**일 뿐이고, 프리셋에 안 맞는 3번째 구조는 스위치를 개별 판정해 **조합**한다.

이 세트의 뿌리는 실측 사례 A(brownfield-submodule)에서 시작해 실측 사례 B(greenfield-monolith)로 진화했다. 사례 B 쪽이 더 나중·정제판이므로 **기본 프리셋의 기준선**으로 삼고, 사례 A 특성은 스위치 오버라이드로 흡수한다. (사례 이름은 익명이다 — 특정 조직·프로젝트를 가리키지 않는다.)

---

## 0. 3층 모델 (무엇이 왜 달라지는가)

| 층 | 이름 | 성격 | 온보딩의 처리 |
|---|---|---|---|
| 🟩 A | **불변(invariant)** | 양쪽 프로젝트에서 글자까지 거의 동일 | `templates/_invariant/*` 를 항상 삽입 (스위치 무관) |
| 🟨 B | **스위치(switch)** | 뼈대 자체를 켜고 끔 — 아래 15개 | Discovery+인터뷰로 on/off 판정 → 조각 조립 |
| 🟥 C | **슬롯(slot)** | 값만 채움 (project_id·매핑표 등) | Discovery 결과·인터뷰로 치환 |

- 🟩 A 는 이 파일이 관리하지 않는다(§6 목록만 참조). 스위치와 무관하게 늘 들어간다.
- 🟨 B 가 이 파일의 본체다(§1~§4).
- 🟥 C 는 §5 에 목록만 둔다(값은 Discovery/인터뷰가 채움).

---

## 1. 15개 스위치 정의

각 스위치는 **① 무엇을 제어하나 ② 자동 판정 신호(Discovery) ③ 값 ④ 게이트하는 템플릿 조각 ⑤ 왜 중요한가** 를 갖는다. 자동 판정이 애매하면 **추정 말고 인터뷰**(AI 임의 추정 금지 원칙).

### SW1. `has_build` — greenfield 최초구현 빌더 유무
- **제어**: `{prefix}-build` 스킬을 생성할지. greenfield(백지에서 짓기)면 필요, brownfield(기존 코드 수정)면 불필요.
- **판정 신호**: 코드 루트에 실제 소스가 있나? (비어있음/README뿐 → greenfield=on) · LogiCraft 도메인들의 구현 현황이 "미착수"인가 · CLAUDE.md 에 "greenfield 미착수" 문구.
- **값**: `on`(빌더 생성) | `off`(dispatch·backfill만)
- **조각**: `_switched/build.SKILL.tmpl.md`
- **왜**: 사례 A 엔 build 스킬이 아예 없다 — brownfield 라 처음부터 지을 게 없었다. 사례 B 가 greenfield 라 build 를 새로 추가했다. **이 스위치가 "2종 vs 3종"을 가른다.**

### SW2. `phase0_foundation` — 공통기반 선순차
- **제어**: 도메인 fan-out 전에 "공통기반(스키마+앱골격)을 메인이 먼저 순차로" 세우는 Phase 0 단계를 넣을지.
- **판정 신호**: 아키텍처가 단일 앱(modular monolith)이고 도메인들이 `core/`·`db/migrations/`·`main` 을 **공유**하나? → on. 도메인이 물리적으로 분리(서브모듈/마이크로서비스)면 공유기반이 없으니 → off.
- **값**: `on` | `off`
- **조각**: `_switched/phase0.section.md` (build 스킬 안에 삽입)
- **왜**: monolith 는 무작정 병렬 fan-out 하면 `core/`·마이그레이션 충돌 → Phase 0 선순차 필수. 서브모듈은 각자 독립이라 불필요.
- **의존**: `has_build=off` 면 이 스위치는 무의미(N/A). build 안에서만 산다.

### SW3. `dependency_layers` — 의존 계층 fan-out 순서
- **제어**: 도메인을 "의존 계층 순서(계층1→2→…)"로 라운드 나눠 빌드할지, 아니면 수정 단위로 개별 처리할지.
- **판정 신호**: `has_build=on`(greenfield 전량 빌드)이면 대체로 on — 도메인 간 계약 의존(예: 검색⊃접근제어 RLS, 서빙⊃검색)이 있으니 순서가 필요. dispatch(수정)는 계층 개념 없음.
- **값**: `on`(build 에 계층표) | `off`
- **조각**: `_switched/layers.section.md` (build 스킬)
- **왜**: greenfield 전량 빌드는 "무엇을 먼저"가 중요. 계층 순서 = 재작업 방지. **계층 내용(어느 도메인이 몇 계층)은 슬롯** — 인터뷰로 확정.
- **의존**: `has_build=on` 전제.

### SW4. `work_claim` — 멀티세션 협업 점유
- **제어**: dispatch 에 LogiCraft `work_claim` 정찰→점유선언→heartbeat→종결 라이프사이클을 넣을지.
- **판정 신호**: **자동 판정 불가 → 항상 인터뷰**. "이 프로젝트를 2인 이상이 각자 AI 세션으로 동시 작업하나?" yes → on.
- **값**: `on` | `off`
- **조각**: `_switched/work_claim.recon.md`·`work_claim.declare.md`·`work_claim.heartbeat.md` (dispatch Phase 3·3.4·6 에 INSERT) + backfill 의 `IF work_claim` 블록(Phase 3 종결)
- **왜**: 사례 A 는 2인 팀이라 `design_pending` claim 으로 "코드 done·설계 대기" drift 를 크로스세션 가시화. 1인 프로젝트(사례 B)엔 불필요한 오버헤드. advisory(안 막음)라 켜도 해는 없지만, 없으면 스킬이 단순해짐.
- **주의**: on 이면 backfill 의 "claim 종결" 책임도 함께 켜진다(dispatch 가 연 claim 을 backfill 이 닫음 — 쌍으로 움직임).

### SW5. `commit_strategy` — 커밋 방식
- **제어**: Phase 6 "커밋" 서술을 단일 repo 로 쓸지, 서브모듈 2단 커밋(서브모듈→상위 포인터)으로 쓸지.
- **판정 신호**: repo 에 `.gitmodules` 가 있거나 코드 루트가 서브모듈 폴더들인가? → `submodule`. 아니면 `single`.
- **값**: `single` | `submodule`
- **조각**: dispatch·build 의 Phase 6 커밋 문구 (조각이라기보다 슬롯 치환에 가까움)
- **왜**: 사례 A 는 서브모듈 2단 커밋 + 환경설정 파일 커밋금지. 사례 B 는 단일 repo. 커밋금지 파일 목록도 프로젝트별(→ 슬롯).

### SW6. `agent_mode` — 에이전트 작동 모드
- **제어**: implementer 에이전트를 dual 모드(greenfield 빌드 + 수정)로 쓸지, 수정 전용으로 쓸지.
- **판정 신호**: `has_build` 를 따라간다. build 있으면 `dual`(build=greenfield 진실원=키트, dispatch=수정 진실원=change_detail 둘 다 받음), build 없으면 `modify`(change_detail 만).
- **값**: `dual` | `modify`
- **조각**: `implementer.tmpl.md` 상단 "진실원(2모드)" 블록 on/off
- **왜**: 같은 도메인 에이전트가 build·dispatch 두 오케스트레이터에 불릴 수 있으면 dual. 사례 A 는 build 가 없어 dispatch 만 부르므로 modify-only.
- **의존**: `has_build` 에 종속(파생 스위치).

### SW7. `conventions_location` — 공통 규약 위치
- **제어**: 기술스택·레이아웃·빌드명령·경계 같은 공통 규약을 공유 파일로 뺄지, 각 에이전트에 내장할지.
- **판정 신호**: 도메인 수가 많고 스택이 균일하면 `shared` 유리(DRY). 도메인마다 스택·빌드가 제각각이면 `embedded` 유리.
- **값**: `shared` | `embedded`
  - `shared` 의 **배치 위치는 프로젝트 루트 `.claude/conventions.md` 로 고정**한다(스킬 폴더에 종속시키지 않음). ← 사례 B 는 build 스킬 폴더(`<prefix>-build/conventions.md`)에 두어 build 스킬과 결합돼 있었으나, build 를 지우면 dispatch·backfill 이 깨지는 암묵 결합이 생긴다. 루트 독립 배치로 이 결합을 끊는다 — build 유무와 무관하게 모든 오케스트레이터·에이전트가 같은 경로를 참조.
- **조각**: `_switched/conventions.tmpl.md` → 생성 시 `.claude/conventions.md` 로 방출. 에이전트·스킬은 이 고정 경로를 참조.
- **왜**: 사례 B 는 규약 하나로 전 에이전트 공유(DRY). 사례 A 는 도메인마다 스택·함정이 제각각(레거시 WAR·서브모듈별)이라 에이전트 내장이 나음.
- **비고**: `has_build` 와 **독립**이다(과거엔 build 폴더에 얹혀 종속처럼 보였을 뿐). shared 면 build 유무와 상관없이 항상 `.claude/conventions.md`.

### SW8. `code_boundary` — 도메인 코드 경계 표현
- **제어**: 매핑표의 `code_root` 를 어떻게 쓸지 + 에이전트 "절대 경계" 문구.
- **판정 신호**: 아키텍처 구조에서 파생. `package`(단일 repo 내 `domains/<pkg>/`) | `submodule`(별도 폴더/repo) | `repo`(마이크로서비스 개별 repo).
- **값**: `package` | `submodule` | `repo`
- **조각**: 매핑표 슬롯 + 에이전트 경계 문구
- **왜**: monolith=`<app_root>/domains/<pkg>/` 패키지, submodule=`<서브모듈 루트>/<시스템>_<프레임워크>` 폴더(경로에 공백·한글이 섞이는 경우가 있어 → 항상 따옴표). 경계 종류가 "core 수정금지 → needs_core_change" vs "타 서브모듈 금지" 문구를 바꾼다.

### SW9. `e2e_track` — E2E 시험 트랙 유무
- **제어**: E2E 세트(`{prefix}-e2e-author`/`-run`/`-verify` 3종 + `.claude/e2e-conventions.md`)를 생성할지. **E2E 스위치들의 마스터** — off 면 SW10~13 은 N/A.
- **판정 신호**: 브라우저로 조작 가능한 앱 표면이 있나? (`frontend/`·`apps/web`·`package.json` 의 dev 스크립트 · 라우트 파일) · 이미 `playwright.config.*`/`cypress.config.*` 가 있나 · LogiCraft 에 `screen_spec`/`test_scenario` 가 있나.
- **값**: `on` | `off`
- **조각**: `_switched/e2e-conventions.tmpl.md` · `_switched/e2e-{author,run,verify}.SKILL.tmpl.md`
- **왜**: CLI·라이브러리·배치처럼 화면이 없는 프로젝트엔 E2E 트랙 자체가 무의미하다(단위·통합 테스트로 충분). 반대로 화면이 있는데 트랙이 없으면 "빌드·린트는 초록인데 화면은 깨져 있는" 상태를 아무도 못 잡는다.

### SW10. `e2e_design_link` — 시나리오와 설계의 연결
- **제어**: 시나리오를 LogiCraft `test_scenario`(TEST-NNN) ITEM 으로 등록하고 실행 결과를 `record_test_run` 으로 역등록할지. off 면 spec 과 로컬 문서로만 관리.
- **판정 신호**: `project_id` 가 있고 `use_case`/`acceptance` 가 실재하나? (`list_items` 로 확인 — **프로젝트가 등록만 되고 비어있는 경우가 있으므로 건수를 반드시 센다**)
- **값**: `logicraft` | `local`
- **조각**: 3종 스킬의 등록·역등록·cascade 감지 블록 (`<!-- IF e2e_design_link == logicraft -->`)
- **왜**: 설계 그래프에 들어가야 **UC 변경 → 그 시나리오가 stale** 로 뜬다. spec 주석에만 `UC-001` 이라 적으면 LogiCraft 는 모르고, 설계가 바뀌어도 spec 은 옛 흐름을 검증한 채 조용히 초록으로 통과한다. 설계가 없는 프로젝트는 이 장치를 못 쓰므로 `local`.

### SW11. `e2e_auth` — 인증 처리 방식  ★ 검증 공백이 가장 잘 생기는 지점
- **제어**: 전제조건 로그인의 우회 방법 + **로그인 자체를 검증하는 시나리오를 별도로 둘지**.
- **판정 신호**: 앱에 인증이 있나(로그인 라우트·세션/토큰) → 없으면 `none`. 있으면 **설계에 인증 UC/AC 가 있나**로 갈린다 — 있으면 `bypass_and_verify`, 인증이 요구사항으로 다뤄지지 않으면 `bypass`.
- **값**: `none` | `bypass` | `bypass_and_verify`
- **조각**: `e2e-conventions.tmpl.md` 인증 절 (3분기)
- **왜**: ★ **로그인은 두 역할을 겸한다.** 다른 걸 검증하려고 들어가는 *전제조건*이면 우회가 옳다(매번 UI 를 타면 느리고, 로그인 화면 변경 시 무관한 시나리오가 전부 깨진다). 그러나 로그인 자체가 요구사항이면 우회한 순간 **한 번도 검증되지 않은 채 모든 시나리오가 초록**이 된다. 이 둘을 섞으면 "검증했다"는 착각이 생기므로 스위치로 강제 분리한다.
- **주의**: `bypass_and_verify` 여도 우회 수단(`{{e2e_auth_bypass}}`)은 여전히 필요하다 — 둘 중 하나가 아니라 **둘 다**다.

### SW12. `e2e_selector` — 셀렉터 정책
- **제어**: spec 이 요소를 잡는 우선순위 규약.
- **판정 신호**: `grep -r "data-testid" <프론트 소스>` 건수. 유의미하게 쓰이면 `testid`, 0 이거나 극소수면 `role`.
- **값**: `testid` | `role`
- **조각**: `e2e-conventions.tmpl.md` 셀렉터 절
- **왜**: testid 가 없는데 testid 규약을 주면 앱 코드 수정이 선행돼야 해서 저작이 멈춘다. 반대로 접근성 이름이 잘 붙은 앱은 `getByRole` 만으로 충분해 앱을 건드릴 필요가 없다. **판정은 추정하지 말고 grep 으로 센다.**

### SW13. `e2e_account_strategy` — 테스트 계정 조달 방식
- **제어**: 계정을 **테스트가 스스로 만드는지 / 사용자에게 받는지 / 둘 다인지**. setup 프로젝트·`storageState` 재사용·시크릿 입력 구조의 유무가 갈린다.
- **판정 신호**: 앱에 **역할(권한 등급)이 여러 개**인가 · 가입·승인 흐름을 **API/화면으로 자동화할 수 있나**(가능하면 자급자족) · **기존 데이터가 쌓인 계정**이 있어야만 검증되는 시나리오가 있나(있으면 시드 필요). **자동판정 불가 → 인터뷰**(§5.3).
- **값**: `self_provision` | `seed` | `mixed`
  - `self_provision` — 테스트가 계정을 만들고 지운다. **자격증명 입력 불필요**(시크릿 문제 원천 소멸).
  - `seed` — 미리 준비된 계정을 쓴다. **자격증명을 사용자에게 받아야 한다**(env·시크릿 파일 경유, spec 하드코딩 금지).
  - `mixed` — 둘 다. 권한별 계정은 만들고, 데이터가 쌓인 계정만 받는다. **현실에서 가장 흔하다.**
- **조각**: `e2e-conventions.tmpl.md` 계정 전략 절 · setup 프로젝트 규약 · `{e2e_seed_accounts}` 블록
- **왜**: 계정 조달을 정하지 않으면 두 가지가 동시에 터진다 — ① 권한이 필요한 시나리오가 403 으로 막혀 "미커버"로 조용히 빠지고, ② 급한 대로 시드 계정 비밀번호를 spec 에 하드코딩해 **저장소에 커밋**된다. 전략을 먼저 세우면 둘 다 막힌다.
- **주의**: `seed`/`mixed` 여도 **가입·승인 흐름 자체는 자급자족으로 검증한다**(그 흐름이 요구사항이므로). 시드는 "그 흐름을 매번 반복하지 않으려고" 쓰는 것이지 검증을 건너뛰려는 게 아니다.

---

### SW14. `frontend_track` — 프론트(화면) 구현 트랙 유무
- **제어**: `{prefix}-web-implementer` 에이전트를 생성할지 + dispatch·build 본문이 **그 에이전트를 참조하는 문장**(description 의 프론트 fan-out · 「백엔드 먼저, 프론트 뒤」 · 게이트의 `영향 프론트:` 줄 · 노하우 반영 대상)을 넣을지.
- **판정 신호**: repo 에 프론트 패키지(`frontend/`·UI 프레임워크가 든 `package.json`)가 있나 · LogiCraft 에 `screen_spec` 이 있나. 둘 다 없으면 off(라이브러리·임베디드·배치·API 전용 서버).
- **값**: `on` | `off`
- **조각**: `_switched/web-implementer.tmpl.md` + dispatch·build 템플릿의 `<!-- IF frontend_track -->` 블록
- **왜**: 예전엔 「프론트 트랙 있으면 web-implementer 생성」이 **방출 목록에만** 걸려 있고 dispatch 본문은 조건 없이 그 에이전트를 불렀다. 화면 없는 레포(C/C++ 라이브러리)에서 **없는 에이전트로 fan-out 한다고 적힌 스킬**이 나왔고, 최종 검증(게이트④)의 「참조하는 모든 에이전트가 실재」가 구조상 항상 실패했다(실측 사례 E · 2026-10-01).
- **e2e_track 과 다른 축이다** — e2e_track 은 「브라우저로 조작할 앱 표면이 있나」(시험), frontend_track 은 「이 세트가 화면 코드를 구현하나」(구현). 화면이 있어도 E2E 를 안 돌릴 수 있고, 그 반대(다른 팀이 만든 화면을 시험만)도 있다.

### SW15. `parallel_lanes` — 병행 레인 (시범 · experimental)
- **제어**: 일을 **레인**(= 워크트리 하나 + 작업자 하나)으로 병행할 도구 세트를 방출할지 — `scripts/lanes/` 스크립트 6개(`_common.sh`·`lane-new.sh`·`lane-orca.sh`·`lane-prep.sh`·`lane-qa.sh`·`lane-merge.sh`) + 작업자 지시 표준 블록 `.claude/lanes/lane-prompt-block.md` + dispatch 「병행 레인」 절 + backfill 「백필 레인」 절.
- **판정 신호**: ① 사용자가 **병행·속도**를 요구하나(「한 줄로 하니 느리다」·「워크트리로 던져 줘」) 또는 팀 작업 ② `git worktree` 를 쓸 수 있나(git ≥ 2.31 · bare 아님 · 서브모듈 구조는 주의 — 아래) ③ Orca 가 깔려 있나(`orca --version` 등 — `worktree_tool` 판정). **자동판정 불가 → 항상 인터뷰.** 기본 **off**.
- **값**: `on` | `off`
- **조각**: `_switched/lanes/*`(스크립트·블록) · `_switched/lanes.dispatch.section.md` · `_switched/lanes.backfill.section.md` · dispatch Phase 3 게이트의 `레인 판정:` 줄
- **왜**: 일이 한 줄로 서면 느리고, 사람이 손으로 워크트리를 만들고 환경을 올리고 합치는 것이 다시 병목이 된다. 한 프로젝트(실측 사례 D)에서 사흘간 레인 20여 개를 돌려 **실측으로 세운 규칙**이 스크립트와 블록에 박혀 있다(아래 §5.6).
- **주의**: `commit_strategy=submodule` 이면 워크트리가 서브모듈을 따로 체크아웃해야 해서 이 도구가 그대로는 맞지 않는다 — 켜기 전에 사용자와 확인하고, 켜면 `lane_prep` 에 서브모듈 초기화를 넣는다.

## 2. 스위치 의존 그래프 (파생 관계)

몇몇 스위치는 독립이 아니라 다른 스위치에서 파생된다 — 온보딩은 이 순서로 판정한다.

```
has_build ─────┬──▶ phase0_foundation   (build=off 면 N/A)
               ├──▶ dependency_layers    (build=off 면 off)
               ├──▶ agent_mode           (build=on→dual, off→modify)
               └──▶ conventions_location (build=on→대체로 shared)

아키텍처(monolith/submodule/multirepo) ──▶ code_boundary, commit_strategy, phase0_foundation

코드 성숙도(기존 소스 유무) ──▶ has_build

팀 구성(1인/다인) ──▶ work_claim   ← 자동판정 불가, 항상 인터뷰

e2e_track ─────┬──▶ e2e_design_link      (track=off 면 N/A)
               ├──▶ e2e_auth             (track=off 면 N/A)
               ├──▶ e2e_selector         (track=off 면 N/A)
               └──▶ e2e_account_strategy (track=off 또는 e2e_auth=none 이면 N/A)

프론트 패키지 유무 + screen_spec 유무 ──▶ frontend_track
병행 요구(사용자) + git worktree 가능 ──▶ parallel_lanes   ← 인터뷰 · 기본 off
  └─ Orca 설치 여부 ──▶ worktree_tool(슬롯 · 기본 git · 있으면 orca 권함)
앱 표면(HTTP/브라우저 진입점 유무) ──▶ e2e_track
LogiCraft 설계 유무 ──▶ e2e_design_link
앱의 인증 유무 + 설계의 인증 UC/AC 유무 ──▶ e2e_auth
역할 수 + 가입·승인 자동화 가능성 + 데이터 의존 시나리오 유무 ──▶ e2e_account_strategy  ← 인터뷰
```

**독립 판정(자동 신호로 못 정함 → 인터뷰 필수)**: `work_claim`(팀 구성), `dependency_layers` 의 **계층 내용**(어느 도메인이 몇 계층 — on/off 는 파생이나 내용은 슬롯), `e2e_auth` 의 **우회 수단**(`{{e2e_auth_bypass}}` — 코드에서 찾되 확정은 인터뷰).

---

## 3. 아키타입 프리셋 (2종)

프리셋 = 스위치 기본값 묶음. 온보딩은 Discovery 로 "가장 가까운 프리셋"을 고른 뒤, 안 맞는 스위치만 오버라이드한다.

### 프리셋 P1: `greenfield-monolith` (기준선 — 사례 B)
| 스위치 | 값 |
|---|---|
| has_build | **on** |
| phase0_foundation | **on** |
| dependency_layers | **on** |
| work_claim | off |
| commit_strategy | single |
| agent_mode | dual |
| conventions_location | shared |
| code_boundary | package |
| e2e_track | 신호 판정 (앱 표면 있으면 **on**) |
| e2e_design_link | **logicraft** (설계 키트 기반이므로) |
| e2e_auth | 신호 판정 (인증 UC/AC 있으면 `bypass_and_verify`) |
| e2e_selector | grep 판정 (기본 `role`) |
| e2e_account_strategy | 인터뷰 (§5.3 — 신규 앱은 데이터가 없어 대개 `self_provision`) |
| frontend_track | 신호 판정 (프론트 패키지 또는 `screen_spec` 있으면 **on**) |
| parallel_lanes | **off** (인터뷰 — 병행 요구가 있을 때만 on · 시범) |

용례: 백지에서 시작하는 단일 앱(FastAPI/Spring 등 modular monolith). LogiCraft 설계 키트가 진실원.

### 프리셋 P2: `brownfield-submodule` (사례 A)
| 스위치 | 값 |
|---|---|
| has_build | **off** |
| phase0_foundation | N/A (build 없음) |
| dependency_layers | off |
| work_claim | **on** (팀 작업 시) |
| commit_strategy | submodule |
| agent_mode | modify |
| conventions_location | embedded |
| code_boundary | submodule |
| e2e_track | 신호 판정 (기존 시스템에 화면 있으면 **on**) |
| e2e_design_link | **logicraft** |
| e2e_auth | 신호 판정 (기존 시스템은 대개 인증 있음 → `bypass_and_verify`) |
| e2e_selector | grep 판정 (레거시는 testid 없는 경우가 많아 대개 `role`) |
| e2e_account_strategy | 인터뷰 (§5.3 — 운영 데이터 의존 시나리오가 많아 대개 `mixed`) |
| frontend_track | 신호 판정 (프론트 패키지 또는 `screen_spec` 있으면 **on**) |
| parallel_lanes | **off** (인터뷰 · 서브모듈 구조는 §SW15 주의) |

용례: 이미 돌아가는 다중 서브모듈 시스템을 테스트·수정 반복으로 고도화. change_detail(CO)이 진실원.

> E2E 스위치와 `frontend_track` 은 두 프리셋에서 값이 같다 — 아키타입(greenfield/brownfield·monolith/submodule)이 아니라
> **앱 표면·인증·설계 유무**라는 다른 축에서 갈리기 때문이다. 프리셋으로 못 정하고 신호로 판정한다.

---

## 4. 프리셋 밖 구조 대응 — 조합 규칙 (★ "2종 밖" 해결)

Discovery 가 두 프리셋 중 하나로 딱 안 떨어질 때(예: brownfield-monolith, greenfield-multirepo, 1인 brownfield). **통짜 새 아키타입을 만들지 말고, 스위치를 §2 의존순서대로 개별 판정해 조합**한다.

### 판정 절차
1. **아키텍처 축 판정** → `code_boundary`·`commit_strategy`·`phase0_foundation` 후보. (monolith→package/single/phase0-가능, submodule→submodule/submodule-commit/phase0-off, multirepo→repo/repo별/phase0-off)
2. **코드 성숙도 축 판정** → `has_build`(빈 코드=on)(그래프 있으면 on).
3. **has_build 파생 전개** → `agent_mode`·`conventions_location`·`dependency_layers` 를 §2 규칙으로.
4. **팀 구성 인터뷰** → `work_claim`.
5. 남는 애매점은 **가장 가까운 프리셋 값**을 기본으로 제시하고 게이트에서 사용자 확인.

### 예시: `brownfield-monolith` (기존 단일 앱을 수정 중심으로)
- 아키텍처=monolith → code_boundary=`package`, commit=`single`, phase0 는 **build 가 없으니 N/A**.
- 성숙도=기존 코드 있음 → has_build=`off`.
- has_build=off 파생 → agent_mode=`modify`, dependency_layers=`off`.
- conventions_location: build 없음 + monolith 균일 스택 → **shared 로 오버라이드 권장**(루트 `.claude/conventions.md` — 스킬 폴더 무관). ← P2 는 embedded 지만 monolith 라 shared 가 나음.
- work_claim: 인터뷰.
- 결과: "P2(brownfield) 기반 + monolith 오버라이드(package/single/shared)". build 없이 dispatch·backfill 2종.

### 예시: `greenfield-multirepo` (백지에서 마이크로서비스)
- 아키텍처=multirepo → code_boundary=`repo`, commit=repo별, phase0=`off`(공유기반 없음, 서비스별 독립).
- 성숙도=백지 → has_build=`on`.
- has_build=on 파생 → agent_mode=`dual`, dependency_layers=**계약 의존 있으면 on**(서비스 간 API 계약 순서).
- conventions: 서비스별 스택이 다르면 `embedded`, 균일하면 `shared`.
- 결과: "P1(greenfield) 기반 + multirepo 오버라이드(phase0 off/repo 경계)".

### 규칙 요약
- 프리셋은 **출발점**이지 구속이 아니다. 오버라이드한 스위치는 게이트 표에 **⚠️ override** 로 표시해 사용자가 검토.
- 새 조합이 반복되면(예: brownfield-monolith 를 자주 씀) 그때 정식 프리셋 P3 로 승격해 이 파일에 추가한다. **프리셋 추가는 스위치 조합의 이름표일 뿐** — 새 로직이 아니다.

---

## 5. 슬롯 목록 (🟥 C — 값만 채움, Discovery/인터뷰가 채운다)

스위치가 "어떤 조각을 넣나"라면, 슬롯은 "그 조각의 빈칸을 뭘로 채우나"다.

★ **카탈로그의 진실원은 `templates/_TEMPLATING.md §1`** 이다(템플릿이 쓰는 슬롯 전부 · 「출처」 칸 포함). 아래 표는 같은 이름으로 판정 해설과 예를 붙인 것이다 — 슬롯을 더하면 **두 곳에 함께** 더한다.

| 슬롯 | 출처 | 예 |
|---|---|---|
| `{prefix}` (에이전트 접두) | 인터뷰 | `acme` |
| `{skill_prefix}` (스킬 접두) | 인터뷰 — 기본 `{prefix}` 와 동일 | `team-acme` (스킬만 접두가 다른 경우) |
| `{PrefixTitle}` (사람용 제목) | 인터뷰 — 기본 프로젝트 이름 | `Acme` |
| `{project_id}` | LogiCraft / CLAUDE.md | UUID |
| `{project_name}` | LogiCraft | "Acme Platform" |
| `{code_base}` | repo 스캔 | monolith `src/<pkg>` / submodule `<서브모듈 루트 폴더>` |
| `{domain_mapping_table}` (id·이름·code_root·에이전트명) | LogiCraft 도메인 조회 + 키트 폴더 → 게이트② 확인 | 표 전체 |
| `{change_orders_path}` | 규약 — 기본 `.claude/change-orders/`(끝에 `/`) | 고정 |
| `{conventions_path}` | 규약 — shared 일 때 `.claude/conventions.md` | 고정 |
| `{tech_stack_table}` | LogiCraft ADR/킥오프 + repo(pyproject/build.gradle) | 영역·스택·근거 표 |
| `{package_layout}` | repo 스캔 | 코드 레이아웃 트리 |
| `{build_cmds}` | repo (Makefile·pyproject·gradle) | `uv run pytest …` |
| `{test_scope_table}` · `{full_test_gate}` | ★ repo 스캔으로 후보 → **실측(동의 후) + 인터뷰로 확정**(§5.7) | 갈래별 검사·연관 시험·항상 묶음·전체 시험 표 / `per_co` |
| `{frontend_stack_block}` · `{frontend_stack_short}` · `{frontend_code_root}` | repo(package.json) + 키트 DS (`frontend_track=on`) | React/Vite 블록 · `React SPA` · `frontend` |
| `{web_guidance}` | ★ screen_spec·DS·소비 API 정독 초안(§5.1 과 같은 방식) → 게이트③ | 근거 SCREEN/API ID 붙은 초안 |
| `{shared_base}` (공유기반 경로 — `code_boundary=package` 일 때) | ★ repo 스캔으로 후보 제시 → **인터뷰로 확정**(§5.5) | 웹앱 `` `core/`·`db/migrations/`·앱 진입점 `` / 라이브러리 `` `lib/common/`·`tools/harness/`·빌드 스크립트 `` |
| `{layer_rounds}` (layers=on 시) | 인터뷰 (LogiCraft 계약 의존 참고) | 계층1 access+identity … |
| `{foundation_schema_note}` (phase0=on 시) | 키트 ERD · 없으면 빈 값 | 스키마 부연 한 줄 |
| `{commit_forbidden}` (커밋금지 파일) | 인터뷰/repo(.gitignore·secrets) | 환경설정 properties, .env |
| `{code_nav_tools}` | Discovery(설치된 코드 탐색 MCP) → 인터뷰 · 없으면 빈 값 | `mcp__serena__find_symbol, …` |
| `{domain_guidance}` (도메인별 함정·진실원·경계) | ★ 온보딩이 LogiCraft 설계 정독해 **초안 생성**(§5.1) | 근거 ITEM 붙은 초안 → 사용자 확정 |
| 도메인별 **노하우** (슬롯 아님) | 첫 구현부터 점진 축적 | (온보딩 시엔 비움) · ☠️ **400줄 상한 게이트**(§5.4) |
| `{qa_model}` (QA 검증 모델) | ★ **인터뷰 필수 — 자동판정 불가**(§5.4) | 사용자가 말한 값 그대로 |
| `{qa_invoke}` (부르는 방법) | ★ 인터뷰 + **동의 후 그 자리에서 실행 확인**(§5.4) | 래퍼 경로·호출 형태 |
| `{qa_fallback}` (대체 경로) | ★ 인터뷰(§5.4) | 메인 세션 서브에이전트 + 모델명 |
| `{qa_fail_signal}` (실패 판별 신호) | ★ 인터뷰 + 실측(§5.4) | 「아예 안 돎」 vs 「종료코드만 이상」 |
| `{backfill_model}` (설계 반영 워커) | ★ 인터뷰(§5.4.1) · 비우면 `{qa_model}` 과 동일 | 값싼 모델 위임 |
| `{knowhow_dir}` / `{knowhow_archive_dir}` | 규약 (기본 `.claude/agents/_knowhow/` · `_archive/`) | 고정 — 절대경로는 슬롯이 아니라 실행 시 계산 |

**E2E 슬롯** (`e2e_track=on` 일 때만 — §5.2 참조)

| 슬롯 | 출처 | 예 |
|---|---|---|
| `{e2e_root}` | repo 스캔 (기존 spec 폴더 · 없으면 프론트 루트 하위 제안) | `apps/web/e2e` |
| `{e2e_base_url}` | repo(dev 스크립트 포트) + 실행 확인 | `http://localhost:3000` |
| `{e2e_api_base}` | repo(API 포트·프록시 설정) | `http://localhost:14000` |
| `{e2e_run_cmd}` | repo(package.json scripts · playwright.config) | `npx playwright test` |
| `{e2e_service_up}` | ★ **실제로 띄워보고 확정** — 기동 명령 + 준비 확인(health) | `pnpm --filter @x/api dev` + `curl /api/health` |
| `{e2e_auth_bypass}` | ★ 코드에서 찾고 **실제로 통과시켜 확인** | mock OAuth `/api/auth/login` 직행 |
| `{e2e_env_caveat}` | ★ 우회가 특정 환경설정에 의존하면 명시 (없으면 빈 값) | `OAUTH_PROVIDER=mock 로 기동 필요` |
| `{e2e_fixture_setup}` | 인터뷰 + 코드 — 권한·시드 계정 **+ 업무 데이터**(목록·통계 검증에 필요한 건수) (없으면 빈 값) | 관리자 권한 계정 · 자산 N건 |
| `{e2e_cleanup}` | ★ 실제 삭제 API 를 **호출해보고** 확정 | `DELETE /api/x/:id` + `confirm_name` 일치 필요 |
| `{e2e_roles}` | ★ 인터뷰 + 코드(권한 카탈로그) — 역할별 **획득 방법**까지 (§5.3) | admin=가입 후 역할부여 / member=가입만 |
| `{e2e_seed_accounts}` | ★ 인터뷰 — **자격증명 자체가 아니라 env 키 이름과 용도** (없으면 빈 값) | `E2E_BULK_USER` = 자산 1만건 보유 계정 |
| `{e2e_storage_dir}` | 규약 (기본 `<e2e_root>/.auth`) — **gitignore 필수** | `apps/web/e2e/.auth` |
| `{e2e_groups}` | ★ 인터뷰 + 시나리오 성격 — 태그 체계 (§5.3) | `@provisioning` / `@smoke` / `@regression` |

**병행 레인 슬롯** (`parallel_lanes=on` 일 때만 — §5.6 참조)

| 슬롯 | 출처 | 예 |
|---|---|---|
| `{worktree_tool}` | ★ 인터뷰 — **기본 `git`**. Orca 가 깔려 있으면(`orca --version`) `orca` 를 **권한다** | `git` / `orca` |
| `{lane_prep}` | ★ repo 스캔 초안(락파일·빌드 파일·`.env.example`·시험 DB 설정) → **인터뷰 확정** · **비울 수 있음**(준비 없음) | `"설치\|pnpm install --frozen-lockfile --offline"` 줄들 |
| `{lane_checks}` | ★ 빌드 파일(package.json scripts·Makefile·pyproject)에서 초안 → 인터뷰 확정 | `"always\|서식\|-\|lane_changed_files npx --no-install prettier --check --ignore-unknown"` 줄들 |
| `{lane_concurrency}` | ★ 인터뷰 — **반드시 묻는다**(질문 문장은 SKILL.md 게이트②) · 답이 없으면 **2** · 구현 레인만 센다 · 재온보딩이면 현재 값을 보이고 유지 여부를 묻는다 | `2` |
| `{deploy_gate}` | 인터뷰 — 배포 전 확인 한 줄 · **비움 = 사용자 승인만** | `야간 일괄 작업이 도는 중이 아닌지 확인` |
| `{backfill_lane_auto}` | ★ 인터뷰 — **반드시 묻는다**(질문 문장은 SKILL.md 게이트②) · `on`\|`off` · 답이 없으면 **off** · on 이면 상용 반영 계획 사전 승인임을 한 번 더 확인 · 재온보딩이면 현재 값을 보이고 유지 여부를 묻는다 | `off` |
| `{lane_main_branch}` | repo — 레인이 갈라지고 합쳐질 브랜치(지금 체크아웃 · 확인) | `main` / `develop` |
| `{lane_qa_shell}` | **새로 묻지 않는다** — `{qa_invoke}` 가 셸 실행줄이면 그것을 `{label}`·`{prompt}`·`{main}` 자리로 옮겨 적은 것 · 갈래 ②(서브에이전트)면 **빈 값** | `qa-runner --agent acme-qa-verifier --label {label} {prompt}` |
| `{lane_heavy_tests}` | 인터뷰 — 한 번에 한 레인만 돌릴 무거운 시험(공유 DB 를 쓰는 전체 시험 등) · **비울 수 있음** | `서버 전체 시험(pnpm test)` |

★ QA 는 **기존 `{qa_model}`·`{qa_invoke}`·`{qa_fallback}` 을 그대로 쓴다** — 레인용 QA 모델을 따로 묻지 마라.

### 5.1 도메인 특화지침은 "언제/어떻게" 채우나 (★ 중요 — 비워두지 않는다)

에이전트의 **도메인 특화지침**(책임·경계 / 저장 진실원·엔티티 / 함정 top / 정책·제약 / 코드 레이아웃)은 첫 구현 **전에** 이미 있어야 가드레일 역할을 한다 — 비워두면 첫 구현이 무방비가 되어 이 에이전트의 존재 이유가 사라진다. 따라서 온보딩이 **채운다**. 다만 지어내지 않는다:

- **채우는 시점**: 온보딩 파이프라인의 **도메인 지침 초안 단계**(§7 step 5.5). 스위치 조립 직후, 검증 게이트 전.
- **채우는 방식**: 도메인마다 설계를 정독해 **근거 ITEM ID 를 붙여** 추출한다. 진실원 = 키트 신선하면 로컬 키트, **stale 이면 사용자에게 3택(현재 키트 그대로 / 키트 업데이트 SYNC / LogiCraft live)**, 키트 없으면 LogiCraft(live). 키트는 LogiCraft 스냅샷이라 궁극 진실원은 LogiCraft다(상세: SKILL.md Phase 4).
  - 책임·경계 ← 도메인 개요 · DFEAT · 인접 도메인 경계
  - 진실원·엔티티 ← ERD · ADR(진실원 결정) · "폐기/구현금지" 스캐폴드
  - 함정 top ← CONST(enum·임계치 정본) · ADR(정책 반전) · EVT/API 계약의 divergence
  - 코드 레이아웃 ← 키트 빌드순서 · 모듈 구성
- **AI 추정 금지의 진짜 의미**: "설계에 **없는** 함정을 지어내지 마라"이지 "설계에 **있는** 걸 옮기지 마라"가 아니다. 근거 ITEM 이 있으면 옮기는 것은 추출이지 추정이 아니다.
- **근거 없으면 비운다 + 보고**: 어떤 함정이 근거 ITEM 으로 뒷받침 안 되면 그 항목은 비우고 "정보부족 — 설계 보완 또는 첫 구현 중 확인 필요"로 보고. placeholder·가짜 ID 금지.
- **사용자 확정**: 초안은 게이트에서 사용자가 검토·수정 후 확정(LogiCraft 작업 정책과 동일 — AI 초안 → 사용자 확정).
- **설계가 얇거나 없으면**(예: LogiCraft 미등록 greenfield): 특화지침은 골격만 두고 "첫 구현 후 노하우로 축적"으로 명시 — 이 경우에 한해 비움이 정당하다.

> 요약: **특화지침 = 온보딩이 설계 읽고 초안(근거첨부)** · **노하우 = 구현하며 축적**. 둘은 에이전트의 서로 다른 섹션이며 채우는 주체·시점이 다르다.

### 5.2 E2E 슬롯은 "추정하지 말고 돌려보고" 채운다 (★ 중요)

E2E 슬롯은 다른 슬롯과 성격이 다르다 — **문서나 코드를 읽어서 얻은 값이 실제와 다른 경우가 흔하다.**
온보딩은 **게이트① 뒤 「Phase 1.5 실측 확인」**(SKILL.md)에서 아래를 **실제로 실행해 확인**하고, 확인한 값만 슬롯에 넣는다.
☠️ 그 실행은 **남의 환경**에서 일어난다 — 무엇을 부르는지(대상 URL·메서드·되돌리는 법)를 **호출마다 보이고 동의를 받은 뒤** 한다.
대상이 localhost·개발 환경이 아니면(운영·공유 스테이징) **멈추고 묻는다.** 사용자가 원하지 않으면 「수치·값만 알려 주기」로 받는다.

- `{e2e_service_up}` — 앱이 지금 떠 있는지, 안 떠 있으면 어떤 명령으로 뜨는지, 준비되기까지 얼마나 걸리는지.
  (기동 명령이 문서와 다르거나, 죽은 프로세스가 포트를 잡고 있는 경우가 있다.)
- `{e2e_auth_bypass}` — 우회 경로를 **실제로 태워 세션이 발급되는지** 확인. 코드에 mock provider 가 있어도
  환경설정이 실서비스를 가리키면 우회가 동작하지 않는다 → 그 조건을 `{e2e_env_caveat}` 에 적는다.
- `{e2e_cleanup}` — **시험용으로 만든 데이터 하나에 대해서만** 삭제 API 를 실제로 호출해 성공 코드를 확인(동의 후). 오삭제 방지 장치(확인 문구 일치, 2단계 확인,
  권한 요구)가 있으면 그 요구사항까지 슬롯에 담는다. **문서에 없고 400 응답으로만 드러나는 경우가 많다.**
- 확인 못 한 값은 **비우고 "정보부족 — 첫 저작 시 확인"으로 보고**한다. 추정값을 넣으면 3종 스킬 전체가
  그 추정 위에서 동작해 첫 실행이 통째로 깨진다.

### 5.3 계정 전략은 인터뷰로 확정한다 (★ SW13 · 추정 금지)

계정은 **자동판정이 불가능하다.** 역할이 몇 개인지는 코드로 알 수 있어도, "어떤 계정으로 무엇을
검증할 것인가"는 사용자만 안다. Phase 2 에서 아래를 묻고 확정한다.

**① 어떤 역할(권한 등급)이 시나리오에 필요한가 → `{e2e_roles}`**
역할마다 **획득 방법**까지 함께 적는다. 방법이 안 정해지면 그 역할의 시나리오는 403 으로 막혀
조용히 "미커버"가 된다.
- 가입만으로 얻어지는 역할인가 / 승인이 필요한가 / **역할 부여(관리자 조작·DB)가 필요한가**
- 부여가 필요하면 **되돌리는 방법까지** 확정한다(온보딩이 켠 권한을 나중에 끌 수 있어야 한다)

**② 자급자족으로 만들 수 있나, 받아야 하나 → SW13**
- **만들 수 있으면 만든다**(`self_provision`). 자격증명 입력이 필요 없어 시크릿 문제가 사라진다.
- **받아야만 하는 경우**가 있다 — 대표적으로 **이미 데이터가 쌓여 있어야 검증되는 시나리오**
  (대량 목록 페이징·통계·성능·오래된 이력). 이건 새로 만든 빈 계정으로는 검증이 안 된다.
  → `seed`. 이때 받는 것은 **자격증명 값이 아니라 "어떤 env 키로 주입할지"**다(`{e2e_seed_accounts}`).
- 현실에서는 대개 **`mixed`** — 권한별 계정은 만들고, 데이터 의존 계정만 받는다.

**③ 시크릿 취급 (예외 없음)**
- 자격증명을 **spec·규약 파일에 하드코딩하지 않는다.** spec 은 저장소에 커밋된다.
- env 또는 gitignore 된 시크릿 파일로 주입하고, 규약에는 **키 이름과 용도만** 적는다.
- 테스트가 스스로 만든 계정의 비밀번호는 시크릿이 아니다(매 실행 새로 만들고 지움). 다만
  **그 값이 상수로 보이면 다음 사람이 시드 계정에도 같은 짓을 한다** — 규약에 구분을 명시한다.
- `{e2e_storage_dir}`(세션 상태 저장소)는 **반드시 gitignore** 한다. 로그인 세션 그 자체다.

**④ 어떻게 그룹으로 나눌 것인가 → `{e2e_groups}`**
매 실행마다 가입·승인부터 다시 타면 느리고 번거롭다. 시나리오에 태그를 달아 **선택 실행**한다.
- `@provisioning` — 계정 생성·승인 흐름 **자체를 검증**하는 시나리오. 느리지만 요구사항이라 반드시 있어야 한다.
- `@smoke` — 핵심 흐름. 자주 돌린다.
- `@regression` — 전체.
- 실행: `--grep @smoke` / 건너뛰기: `--grep-invert @provisioning`
- **핵심 구조** — 계정 확보를 **setup 프로젝트**가 전담하고 결과를 `storageState` 로 남기면,
  본 시나리오는 계정 출처(만들었는지·받았는지)를 몰라도 된다. 그래서 `@provisioning` 을 건너뛰어도
  나머지가 전부 돌아간다. 이 분리가 없으면 그룹 건너뛰기가 성립하지 않는다.

### 5.4 검증 위임과 노하우 구조 (★ 실측 사례 A · 2026-09-16 · 2026-09-18 개정)

#### `{qa_model}` — 묻되, **두 갈래를 제시하고, 응답을 확인**하라

구현과 검증에 **다른 모델**을 쓰면 서로 다른 맹점을 덮는다. **서열이 아니다** — 「비싼 쪽이 검증」이
아니라 **각자 놓치는 것이 다르다**는 게 전부다. QA 는 토큰을 가장 많이 먹는 단계이므로
**「토큰 비용을 줄이려면 저렴한 모델을 권장한다」**고 알리고 받는다.

★ **두 갈래를 제시한다**(제품 이름은 나열하지 않는다 — 곧 낡는다. **범주는 안 낡는다**):
> 「① **외부 도구에 위임** (별도 CLI·에이전트 러너로 다른 벤더 모델을 부르는 방식)
>  ② **같은 계열의 값싼 모델** (지금 세션과 같은 제품군의 저비용 모델을 서브에이전트로)
>  어느 쪽으로 할까요? 쓰시는 도구·모델 이름을 그대로 알려주세요.」

- ☠️ **후보 목록을 읽어 제시하지 마라** — 프로젝트마다 도구가 다르고 목록이 곧 낡는다.
  **범주 둘만 제시**하고 **사용자가 말한 값을 그대로** 받는다.
- ☠️ **①(외부 도구)은 데이터 반출이다** — QA 프롬프트에 실리는 레포 내용(코드·diff·CO·설계 발췌)이 **그 벤더로 전송된다.**
  묻는 문장에 그 사실을 적고, 응답 확인(시험 호출)도 **동의를 받은 뒤** 한다. 조직 정책상 반출이 안 되면 ②로 간다.
- ☠️☠️ **받은 값이 실제로 응답하는지 그 자리에서 확인**하라. 사례 A 에서 기본 모델이 **없는 이름**을
  가리켜 QA 가 **시작조차 못 했는데 정상 종료처럼 보였고**, 「통과」로 오독된 채 라운드가 닫혔다.
  ⇒ 짧은 과제를 실제로 던져 응답을 눈으로 본다.
- **네 값을 함께 확정한다** — `{qa_model}`(무엇) · `{qa_invoke}`(**어떻게 부르나**) ·
  `{qa_fallback}`(실패 시 무엇으로) · `{qa_fail_signal}`(「아예 안 돈 것」과 「종료코드만 이상한 것」을
  가르는 신호). 신호가 없으면 **그것부터 만든다** — 없으면 오독이 반복된다.

☠️☠️ **받은 값은 «반드시 방출물에 실린다»** — 2026-09-16 에 인터뷰만 추가되고
**dispatch 템플릿에 슬롯이 없어** 답이 어디에도 안 실렸다. 물어만 보고 흘리면 안 한 것과 같다.
슬롯은 `_TEMPLATING.md §1 검증 위임 슬롯`에 등록돼 있고 **§6 미치환 스캔이 잡는다.**

#### 5.4.1 `{backfill_model}` — 설계 반영도 값싸게 돌릴 수 있다

설계 backfill 은 **단계마다 성격이 다르다.** 전부 비싼 모델로 돌릴 이유가 없다.

| 단계 | 성격 | 배분 |
|---|---|---|
| **초안**(읽기 전용) | 코드를 읽고 **설계 문장으로 번역** — 판단 무거움 | 추론 쪽 |
| **반영**(쓰기) | 초안대로 patch — **기계적** | **가장 싸게** |
| **말단 훑기** | 전개는 기계적, 「변경 불요」 판정은 판단 | 중간 |
| **독립 검사** | 초안·CO·**실제 코드** 3방향 재대조 | 추론 쪽 + **다른 눈** |

- **근거** — 사례 A 에서 값싼 워커가 **오케스트레이터의 지시 오류를 여러 번 잡았다**(화면 ID 오지목·
  API ID 오지목·「이미 폐기돼 반영 불가」를 한 라운드에 3건). 사고가 난 경우는 원인이
  **경고를 일부 레인에만 박은 것**이었다 — **지시 탓이지 모델 탓이 아니다.**
- ☠️ **다만 독립 검사는 빼지 마라** — 설계는 **틀려도 아무것도 안 깨진다.** 코드는 빌드가 잡지만
  설계 ITEM 은 잘못 써도 버전만 올라간다. 게다가 **「맞는 말인데 엉뚱한 칸에 쓴 것」은 버전 대조로
  안 잡힌다**(이력 칸에만 쓰고 현행 칸은 옛 서술로 둔 실사고). 그게 유일한 그물이다.
- 비우면 `{qa_model}` 과 같은 것으로 본다.

#### 노하우는 **애초에 나눠 담는다** (400줄 = 본체 기준)

에이전트는 매 호출마다 자기 파일을 통째로 읽는다 — 길어질수록 **고정 비용이 늘고 중요한 게 묻힌다.**

**실측(사례 A)** — QA 노하우가 660줄, 화면 구현 노하우가 **1,976줄**까지 부풀었다. 원인 셋:
1. 통합해 놓고 **원본 302줄을 안 지움** — 같은 내용이 두 벌.
2. 「라운드 섹션 만들지 마라」를 **적어 놓고도 3라운드 연속 어김.**
3. ☠️ **같은 함정이 9곳에 흩어져 적힌 숫자가 서로 달랐다**(선존 lint 오류 수 155·157·163).
   작업자가 어느 걸 읽느냐로 **판정이 갈린다.**

⇒ **사후 정리가 아니라 사전 구조로 막는다:**

| 어디에 | 무엇을 |
|---|---|
| **에이전트 본체** | 절차·경계·출력 규약 + **매 라운드 필요한 게이트 판정** + **`## 노하우 색인`**(행동 트리거 · 착수 전 전 행 훑기 **필수**) + **`## 노하우 — 상시`**(되돌리기 어려운 금지 규칙) |
| **`{knowhow_dir}`** | 주제별 묶음 (`<prefix>-<주제>.md`) — 색인이 가리킨다 |
| **`{knowhow_archive_dir}`** | 정리 시 원문 보관 (지우는 게 아니라 옮기는 것) |

- **400줄 상한은 «본체» 기준**이다. 묶음은 세지 않는다. 단 **묶음에도 600줄 상한**이 있다 —
  넘으면 **평면으로 더 쪼갠다**(`<주제>-<하위>`). ☠️ **묶음 안에 묶음 금지** — 색인이 2단이 되면
  에이전트가 「어느 하위를 읽을지」를 또 판단해야 해 비용이 되돌아온다.
- 본체가 넘으면 **「정리」가 아니라 「묶음을 하나 더 판다」**가 1순위 처방이다.
- ☠️ **뒤로 미루는 것만으로는 소용없다** — 파일을 통째로 읽으므로 **별도 파일로 분리**해야 준다.
- 오케스트레이터는 구현 위임 시 **「이 묶음도 읽어라」를 «추가»만** 한다. **빼지 않는다** —
  고르면 **예상 가능한 것만 남고**, 정작 예상 못 한 함정이 빠진다(실측: 「입력 상자 교체」 건에서
  실제로 걸린 것은 공유 저장소 커밋·검사 기준선·창 안의 키 입력이었다).
- 새 노하우는 **주제에 붙인다. 라운드 섹션을 만들지 마라** — 이 규칙은 **지켜지지 않는 쪽으로 기운다.**
- 삭제 전 **제목 단위 대조로 유실 0건** 확인. 상세 절차는 dispatch `Phase 5.9` / build `Phase E.5` 로 방출.

### 5.5 공유기반 경로는 프로젝트마다 다르다 (★ `{shared_base}` · 추정 금지)

`code_boundary=package` 면 dispatch·conventions·implementer·qa-verifier 가 「도메인 에이전트가 손대면 안 되는 **공유기반**」을 이름으로 적는다.
예전 템플릿은 이것을 `core/`·`db/migrations/`·앱 진입점으로 **고정**해 뒀는데, 그건 웹앱(modular monolith)에서만 맞는다.
라이브러리·임베디드 레포에서는 그 경로가 없고 **실제 공유기반(공용 lib·하네스·빌드 스크립트)은 경계 규칙에 안 잡혔다**(실측 사례 E).

- **후보 찾기**: 여러 도메인 폴더가 함께 import/include 하는 경로 · 스키마/마이그레이션 폴더 · 앱 진입점 · 공용 빌드·테스트 하네스.
- **확정은 인터뷰**: 후보를 보여 주고 「이 중 도메인 에이전트가 임의로 고치면 안 되는 것」을 고르게 한다. 추정으로 채우지 않는다.
- **형식**: 문장 안에 그대로 들어가는 **한 줄 나열** — 백틱 경로를 `·` 로 잇는다(예 `` `core/`·`db/migrations/`·앱 진입점 ``).
- 공유기반이 정말 없으면(도메인이 완전히 독립) `code_boundary` 판정부터 다시 본다 — `package` 가 아닐 가능성이 높다.

### 5.6 병행 레인 (★ SW15 · 시범 — 한 프로젝트 사흘 실측에서 일반화)

**서브에이전트 fan-out 과 무엇이 다른가**

| | 서브에이전트(dispatch Phase 4) | 레인 |
|---|---|---|
| 작업 트리 | 메인 **하나** — 격리가 «지시»뿐 | 레인마다 **자기 워크트리** — 구조적 격리 |
| 메인 세션 | 끝날 때까지 묶인다 | **풀려난다**(다음 일을 받는다) |
| 합치기 | 이미 섞여 있다 | **QA 통과분만** 한 줄씩(rebase → ff → 검사) |
| 대가 | — | 자원(설치·빌드 × 레인) · **번호 충돌** · 레인에서 **화면 확인 불가**(로그인 세션 없음) |

**실측으로 세운 규칙 — 템플릿·블록에 박혀 있다(빼지 마라)**
- **레인 = 워크트리 하나 + 작업자 하나.** 🚫 워크트리 폴더 `cp` 복사 금지 — 새 공간은 `git worktree add`(또는 Orca).
- **Orca 길은 Orca 가 워크트리를 만든다** — 저장소 안에 git 으로 만든 워크트리는 Orca 사이드바에 안 보였다.
- **QA 는 레인 커밋에 고정** · **QA 동안 그 레인에 쓰지 않는다**(`lane-qa.sh` 가 HEAD·작업 트리를 대조해 바뀌면 무효 21).
- **판정은 verdict 줄** — 없으면 「안 돌았다」(20). 위임 도구의 종료코드로 판정하지 않는다(pass 를 내고 exit 1 로 끝난 판이 있었다).
- **QA 는 메인 폴더에서 돈다** — 워크트리 안에서 위임하면 에이전트 정의 미러가 충돌·실패했다. 프롬프트에 `knowhow_dir_abs`(실행 시 계산한 절대경로)와 범위 줄 「전체 시험은 합치기에서 한 번만 돈다」 **필수**(스크립트가 거절한다).
- **공용 기록(MASTER) 칸마다 주인** — 구현·배포 칸 = 메인 · 설계반영 칸 = 백필 레인 · 그 밖의 레인은 쓰지 않는다.
- **CO·마이그레이션 번호는 열린 레인과 메인 최신값을 함께 보고 정한다** — 같은 시기 레인들이 같은 번호를 쓴 사고가 있었다. 레인은 번호를 새로 잡지 않는다.
- **무거운 시험은 한 번에 한 레인** — 공유 DB 부하로 레인들이 함께 돌리면 깨졌다.
- **레인 웹 포트엔 로그인 세션이 없다** — 화면 확인은 합친 뒤 메인에서.
- **레인용 로컬 서비스 정지·삭제는 사용자 동의** · **작업자는 운영 데이터를 건드리지 않는다.**
- **rebase 충돌은 abort 하고 레인을 재작업으로** — 손으로 합치지 않는다. git 잠금(index.lock)은 충돌이 아니다(종료 8 — 오판 사고).
- **검사가 빨가면 합친 채 푸시·정리만 멈춘다** — 메인을 되돌리지 않는다(되돌릴지는 사람). 고친 뒤 재실행이 이어 간다.
- **`cmd | tail` 은 종료코드를 가린다** — 파일로 받고 rc 를 따로 본다 · 시험 단계는 통과 건수 줄이 있어야 초록.
- **출력에서 자격증명 URL·password=·token= 줄을 거른다** — 시험 하네스 오류 문구가 DB 비밀번호를 찍었다.
- **합치기 전 레인 폴더의 남은 프로세스를 끝낸다**(이름으로만 판정 · 명령줄 비출력) — 부하용 프로세스가 레인을 지운 뒤에도 하루 가까이 돌았다. 작업자는 `yes` 같은 부하를 만들지 않고 백그라운드 프로세스를 끝내고 보고한다(`pgrep -l` 만 — `-f` 는 비밀 노출).
- **Orca 작업자는 백그라운드로 차례를 끝내면 멈춤 처리된다** · **끝은 `worker_done` 한 번** · **정리 전 `worker-release`.**

**고유값은 슬롯으로만** — 원본 프로젝트의 패키지 관리자·공용 패키지 빌드·시험 DB 이름 꼬리표·긴 작업 중 배포 확인·원격 배포 명령은 전부 `lane_prep`·`lane_checks`·`deploy_gate` 의 **예시**일 뿐이다. 스크립트에 하드코딩하지 않는다.

### 5.7 시험 범위 — 전체 시험은 CO 하나에 한 번 (1.9.0)

**왜** — 세트는 CO 마다 시험을 남기고, 구현 에이전트와 QA 가 각자 시험을 「실측 재실행」한다. 1.8.0 까지는 그 줄이 `{{build_cmds}}`(전체) 였다 —
CO 가 쌓일수록 **CO 하나에 전체 시험이 «대상 수 × 2회 + 재구현 횟수»** 돌았다. 실측(사례 D · 2026-11): 웹 시험 485파일 8,269건 ·
시험 자체 82초 · CPU 약 1,000초(파일마다 드는 준비 비용이 대부분) · 화면 하나 고친 변경의 연관 시험은 61~76파일(약 1/5) · 공용 부품을 고치면 437파일(거의 전부 — 그때는 전체가 맞다).

**무엇을 정하나** — 갈래(백엔드·프론트·서브모듈)마다 네 가지 + 게이트 하나:

| 값 | 뜻 | 어떻게 정하나 |
|---|---|---|
| 검사 | lint·typecheck·build — 시험을 뺀 것 | `{build_cmds}` 에서 시험 명령을 덜어낸다 |
| 연관 시험 | 바꾼 파일을 넘기면 그것을 불러 쓰는 시험만 도는 명령 | 아래 표에서 스택에 맞는 것 → **실제로 한 번 돌려 본다** |
| 항상 묶음 | 가로지르는 규칙 시험(등록부·경계·금지 규칙·소스 글자를 읽는 시험) | 인터뷰 — 없으면 「없음」 |
| 전체 시험 | 지금의 전체 | **소요·DB 접근을 먼저 알리고 동의를 받아** 한 번 돌려 **파일 수·건수·소요를 적는다**(이 수치가 게이트 값을 고르는 근거). 원하지 않으면 사용자가 아는 수치를 받는다 |
| `full_test_gate` | 전체를 언제 한 번 | 인터뷰 — 기본 `per_co` · 전체가 10분을 넘으면 `per_batch`·`pre_deploy` 를 권한다 |

**스택별 연관 시험 명령(후보 — 실측으로 확인하고 쓴다)**

| 스택 | 연관 시험 |
|---|---|
| Vitest | `vitest related <바꾼 파일…> --run` |
| Jest | `jest --findRelatedTests <바꾼 파일…>` |
| pytest | 바꾼 모듈의 시험 경로를 넘긴다(`pytest tests/<모듈>`) · `pytest-testmon` 을 쓰면 `pytest --testmon` |
| Gradle·Maven(다중 모듈) | 바꾼 모듈만 — `./gradlew :<모듈>:test` / `mvn -pl <모듈> test` · 한 모듈 안에서는 `--tests '<패턴>'` |
| Go | `go test ./<바꾼 패키지>/...` |
| Rust | `cargo test -p <바꾼 crate>` |
| 그 밖·없음 | 「없음 — 경로로 고른다」: 바꾼 파일과 같은 디렉터리·모듈의 시험 + 그 파일을 직접 불러 쓰는 시험 |

☠️ **연관 판정의 사각 둘** — ① 소스·문서의 **글자**를 읽는 시험(가져오기 그래프에 없다) ② 모든 곳이 불러 쓰는 **묶음 파일**(바꾸면 거의 전부가 연관). ①은 「항상 묶음」에 넣고, ②는 「전체로 올리는 예외」로 다룬다.
☠️ **값을 추정으로 채우지 마라** — 연관 명령을 실제로 돌려 「N파일이 돌았다」를 본 뒤 적는다. 못 돌렸으면 「미확인」이라 적고 `없음 — 경로로 고른다` 로 둔다.

**시험 파일 규칙(함께 방출)** — 시험 파일은 CO 가 아니라 기능에 붙인다(기존 기능을 고치면 그 기능의 시험 파일에 더한다 · CO 번호는 시험 제목에). 프로젝트에 AC-ID 파일명 규약이 있으면 그 규약이 우선이다.

**재온보딩** — 1.8.0 이하 세트는 에이전트 본체의 자체검증·QA 실측 줄에 전체 시험 명령이 박혀 있다. 업그레이드 때 그 줄을 「범위 시험」 절로 바꾸고 dispatch 에 Phase 5.95 를 더한다(실물에만 있는 노하우·절은 보존). 기존 시험 파일을 기능별로 옮기는 일은 온보딩이 하지 않는다 — 원하면 프로젝트에서 따로 CO 로.

---

## 6. 불변 조각 목록 (🟩 A — 스위치 무관, 항상 삽입)

이 조각들은 스위치를 안 탄다. `templates/_invariant/*` 에서 슬롯만 치환해 늘 생성한다.

- **CO 파일 + MASTER.md 메커니즘** — dispatch 의 부채추적 (CO 작성·MASTER 등록·상태 표)
- **design-backfill 파이프라인** — retro-align → `mc-logi-update` 위임 → **Phase 2.5 leaf 누락검증**(AC·SCREEN·SEQ·CDIAG·CMP) → MASTER 🎨
- **qa-verifier 에이전트** — verdict(pass/pass_with_notes/fail/blocked) + 실측 재실행 + 수용기준 재대조 + 어드버서리얼 + 코드수정금지
- **implementer 골격** — 입력 / 도메인 특화지침(책임·경계·진실원·함정·레이아웃) / 구현절차 Phase0~3 / 절대경계 / 노하우 / 출력 YAML
- **출력 YAML 계약** — `implemented / verification / tracking / notes_for_main`(하위에 `learned` — 새로 알아낸 함정·패턴을 근거와 함께 올리는 자리)
- **노하우 되먹임 루프** — 에이전트가 `notes_for_main.learned` 로 보고 → 오케스트레이터가 노하우 반영 게이트(dispatch Phase 5.9 / build Phase E.5)에서 사용자 동의 후 implementer `## 노하우` 에 append. 에이전트는 자기 파일을 직접 못 고침.
- **5대 원칙** — 오케스트레이션만 · CO/키트 진실원 · AI추정금지 · 정직회수(red 숨김금지) · 노하우축적
- **게이트 규율** — 착수범위/영향범위 확인 게이트, 나머지 자동

> 불변이라도 슬롯(§5)·스위치 조각(work_claim 등)은 그 안에 **삽입점**으로 들어간다.

---

## 7. 온보딩이 이 파일을 쓰는 법 (요약)

1. **Discovery** → 각 스위치의 판정 신호를 수집(repo 스캔 + LogiCraft 조회).
2. **프리셋 선택** → P1/P2 중 가까운 것 + §4 로 오버라이드 계산.
3. **게이트①** → 스위치 표(프리셋값 + ⚠️override + 인터뷰필요 항목)를 사용자에게 확인. (재온보딩이면 그 전에 SKILL.md Phase 0 ⓪ 레포 밖 백업)
3.5. **실측 확인(SKILL.md Phase 1.5)** → 앱 기동·인증 우회·시험 실행 등 «돌려 봐야 아는» 슬롯을 호출마다 동의받고 확인(§5.2 · §5.7).
4. **인터뷰** → work_claim·계층내용·prefix·커밋금지 등 자동판정 불가분.
5. **조립** → 🟩A(항상) + 🟨B(on 스위치 조각) + 🟥C(슬롯 치환).
5.5. **도메인 지침 초안** → 도메인마다 LogiCraft 설계 정독해 특화지침(함정·진실원·경계)을 근거 ITEM 붙여 초안(§5.1) → 게이트에서 사용자 확정. 근거 없으면 비우고 "정보부족" 보고.
게이트 번호·전체 흐름의 진실원은 SKILL.md 「게이트 요약」이다(이 목록은 요약).
6. **게이트④(검증)** → 생성된 스킬이 참조하는 모든 에이전트가 실제로 생성됐는지 교차검증 · 매핑표 완전성 · conventions 경로(`.claude/conventions.md`) 정합.
