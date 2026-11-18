---
name: mc-logi-build-onboard
description: LogiCraft 설계를 쓰는 프로젝트에 구현 오케스트레이션 세트(수정 dispatch · 설계 backfill · build · E2E · 도메인 구현 에이전트 · 독립 QA 에이전트 · 선택으로 병행 레인)를 만들어 넣는 메타 스킬. 이미 세트가 있으면 덮어쓰지 않고 레포 밖에 백업한 뒤 병합한다. 게이트마다 사용자 확인. "이 프로젝트 온보딩해줘", "구현 세트 만들어줘", "dispatch/build 스킬 세팅", "세트 업그레이드", "/mc-logi-build-onboard" 에 쓴다.
metadata:
  version: 1.11.2
---

# mc-logi-build-onboard — 구현 오케스트레이션 세트 온보딩

프로젝트마다 손으로 dispatch/build/backfill 스킬 + 도메인 에이전트를 포팅하면 매번 미묘하게 달라진다(드리프트). 이 스킬이 그걸 접는다 — **불변 뼈대 + 스위치 조각 + 슬롯**을 조립해 **일관된 세트**를 방출한다.

**용어** — **CO**(변경지시서: 수정 한 건의 문서 · `{{change_orders_path}}`) · **키트**(LogiCraft 설계를 내려받은 로컬 사본 `docs/design/…`) · **IMPREC**(LogiCraft 구현 기록 — 어느 설계를 어느 코드가 구현했나) ·
**work_claim**(LogiCraft 의 «지금 이걸 고치는 중» 알림 — 팀 작업용) · **노하우 묶음**(에이전트가 쌓는 주제별 함정 메모 `{{knowhow_dir}}` — 본체엔 색인만) · **레인**(워크트리 하나 + 작업자 하나).

## 필요한 것 (시작 전에 확인 — 없으면 무엇이 안 되는지 알리고 묻는다)

| 무엇 | 왜 | 없으면 |
|---|---|---|
| LogiCraft MCP(`mcp__logicraft__*`) | 프로젝트·도메인·설계 조회, 방출물의 IMPREC 추적 | 설계 근거 없이 골격만 — 그 사실을 보고 |
| `git` · `bash` | repo 스캔 · 방출물 검사 · 레인 스크립트(bash 3.2 이상) | 진행 불가 |
| `git` **2.31 이상** | 병행 레인(`--path-format=absolute`) | `parallel_lanes` 를 off 로 제시 |
| `python3` | 노하우 머리말 생성기 · Orca 레인 · 열람 대조 | 머리말 생성·검사를 못 한다 — 보고 |
| (선택) 코드 탐색 MCP | 에이전트 `tools:` 의 `{{code_nav_tools}}` | 빈 값 — Grep 으로 한다 |
| (선택) Orca CLI | `worktree_tool=orca` | git 길로 |
| macOS · 리눅스 | 레인 스크립트는 둘 다에서 돈다(프로세스 확인은 lsof 없으면 /proc) | Windows 는 WSL 에서 |
| 스킬 `mc-logi-update` | 방출된 backfill 이 설계 ITEM 수정을 이 스킬에 맡긴다 | backfill 이 설계를 못 고친다 — 「설치 필요」로 안내하고 backfill 절에 적는다 |
| 스킬 `mc-logi-implement-kit` | 키트 SYNC(Phase 4 의 (b) 선택 · build 의 진실원) | (b) 를 못 고른다 — (a)·(c) 만 제시 · build 는 키트 없이 LogiCraft live 로 |
| (선택) 스킬 `mc-logi-schema-fill` | backfill 이 옛 산문을 칸으로 옮길 때 가리킨다 | 그 안내만 빠진다 |

Phase 0 에서 위 스킬이 설치돼 있는지(`~/.claude/skills/` · 프로젝트 `.claude/skills/` · 플러그인) 확인해 게이트①에 함께 보고한다.

★ 산출물(스킬·에이전트·규약)의 문장은 **한국어**다. 다른 언어 팀이면 템플릿을 번역해 쓴다(슬롯·마커는 그대로).

## 진실원 파일 (이 스킬이 참조)

| 파일 | 역할 |
|---|---|
| `toggles.md` | ★ 두뇌 — 15개 스위치 정의·판정신호·프리셋 2종·프리셋 밖 조합규칙·슬롯 해설(§5) |
| `templates/_TEMPLATING.md` | 치환 문법(`{{slot}}`·`<!-- IF -->`·`<!-- INSERT -->`)·**슬롯 카탈로그(진실원 · 「출처」 칸)**·방출 위치·검증 규칙 |
| `templates/_invariant/*` | 🟩 항상 생성 (dispatch·backfill·implementer·qa-verifier) |
| `templates/_switched/*` | 🟨 스위치 on 일 때만 (build·conventions·work_claim·phase0·layers·e2e 4종·web-implementer·**병행 레인** `lanes/`) |
| `templates/_assets/_gen-headnote.py` | 노하우 머리말 생성기(슬롯 치환해 방출) |
| `references/qa-delegation.md` | QA 모델 인터뷰 상세 · 갈래별 값 예시 |
| `references/reonboarding.md` | 재온보딩 상세 — 감지·분석 판정 기준 · 버전별 신호 · 노하우 정리 |
| `references/knowhow-measurement.md` | 재온보딩 사후 측정 — 노하우 전달을 재는 법 |
| `references/verification-notes.md` | Phase 5 검사들의 배경(왜 그 검사가 있나) |

**시작 전 반드시 `toggles.md` 와 `templates/_TEMPLATING.md` 를 정독한다.** 사례 이름은 익명이다(실측 사례 A~E).

## 원칙 (전 파이프라인 관통)

- **AI 임의 추정 금지** — 스위치·슬롯 값은 repo/LogiCraft 근거 또는 인터뷰로만 확정. 근거 없으면 비우고 "정보부족" 보고(placeholder·가짜 ID 금지).
- **게이트 우선** — ①스위치 확정 · (1.5 실측 동의) · ②슬롯 · ③도메인 지침 · ④최종 검증에서 사용자 확인. 그 사이의 «읽기»만 자동이다.
- **기존 세트 존중** — 이미 `{{skill_prefix}}-dispatch` 등이 있으면 재온보딩(업그레이드 모드) — 덮어쓰기 전 백업·diff·질의.
- **구현은 안 돌린다 · 실측 실행은 게이트 뒤·동의 후에만** — 이 스킬은 세트를 만들 뿐 구현을 돌리지 않는다. 다만 슬롯 값을 «돌려 보고» 확정해야 하는 것이 있다:
  앱 기동 · 인증 우회 시험 · 시험용 데이터 삭제 호출 · 권한 부여 · 연관/전체 시험 실행 · QA 모델 시험 호출.
  이것들은 **게이트① 뒤에, 호출마다 대상·되돌리는 법을 보이고 동의를 받은 뒤**에만 한다. 대상이 localhost·개발 환경이 아니면 **멈추고 묻는다.** 🚫 운영 환경은 건드리지 않는다.
- **파일 쓰기는 방출물·부트스트랩뿐** — `.gitignore`·`CLAUDE.md` 처럼 원래 있던 파일을 고칠 때는 **넣을 줄을 게이트④에서 먼저 보이고** 확인받는다.

---

## 파이프라인

### Phase 0 — Discovery (읽기만)
스위치 판정신호와 슬롯 값을 모은다. **repo 스캔 + LogiCraft 이중.** 이 단계는 아무것도 실행·변경하지 않는다(예외: 재온보딩의 ⓪ 백업 — 동의 후 레포 밖에 복사만).

**★ 0-A. 기존 세트 감지 — 재온보딩인지 먼저 가른다**
`.claude/skills/*-dispatch/` 와 `.claude/agents/*-implementer.md` 가 **둘 다 있으면 재온보딩**이다(하나만 있으면 반쪽 세트 — 게이트①에 알리고 재온보딩으로 갈지 묻는다) → 아래 **⓪ 를 지금 한다**(Phase 1 보다 먼저), 이후 §재온보딩 절차로 병합한다.
☠️ 이 분기를 안 하면 **손으로 쌓은 것을 덮어쓴다.** 감지 결과를 게이트①에 함께 보고한다.

**⓪ 덮일 대상과 백업 (재온보딩일 때 · 🚦 무엇보다 먼저)**
1. **되돌릴 수 있는지** — `git check-ignore -q .claude/skills && echo IGNORED` · `git ls-files .claude | wc -l`(0 이면 git 이 안전망이 아니다).
   ☠️ `.claude/` 가 gitignore 인 프로젝트가 실재한다 — 그러면 되돌릴 방법도, 「보존됐나」 대조할 원본도 없다 → **경고하고 백업을 «기본값 예»로** 제안.
2. **덮일 대상 목록** — 스킬 본문(dispatch·backfill·build·e2e) · 규약 · 에이전트(도메인·web·qa) · (있으면) `scripts/lanes/`·`.claude/lanes/` — 파일별 줄 수와 함께. 노하우 `_archive/` 는 노하우만 덮는다는 것도 알린다.
3. **묻는다** — 「재온보딩은 위 N개 파일을 고칩니다. 착수 전에 통째로 백업할까요?」
   - **예** → **레포 밖**에 복사한다: `B=~/.claude-backups/<repo 이름>-<YYYYMMDD-HHMM>; mkdir -p "$B" && chmod 700 "$B" && rsync -a --exclude 'worktrees/' .claude "$B"/`(+ 있으면 `scripts/lanes`).
     레인 워크트리(`.claude/worktrees/` — 설치물까지 든 작업 사본)는 빼고, 비밀이 든 설정이 섞이므로 폴더는 주인만 읽게 한다. **경로를 보고**한다.
     🚫 레포 안(`.claude.bak-…`)에 두지 마라 — `settings.local.json`·토큰 사본이 gitignore 밖에 생겨 **커밋될 수 있다.**
   - **아니오** → 기록하고 진행하되, git 안전망이 없으면 한 번 더 확인받는다.

**A. repo 스캔**
- 코드 루트(→ `{{code_base}}`)에 실제 소스가 있나 / README·빈 폴더뿐인가 → `has_build` 신호.
- `.gitmodules` 존재 / 코드 루트가 서브모듈 폴더들인가 → `commit_strategy`·`code_boundary` 신호.
- 빌드 파일(pyproject/build.gradle/package.json/Makefile) → `{{build_cmds}}`·`{{tech_stack_table}}`·`{{package_layout}}` 원자료.
- `frontend/`·`package.json`(UI 프레임워크) · LogiCraft `screen_spec` 건수 → `frontend_track` 신호 → on 이면 `{{frontend_stack_block}}`·`{{frontend_stack_short}}`·`{{frontend_code_root}}`.
- 여러 도메인 폴더가 함께 쓰는 경로(공용 lib·스키마/마이그레이션·앱 진입점·빌드·테스트 하네스) → `{{shared_base}}` **후보**(확정은 인터뷰 — toggles.md §5.5).
- `CLAUDE.md` → `{{project_id}}`·도메인 표·주의사항.
- 설치된 MCP(설정 파일·`/mcp`) 중 코드 탐색 도구 → `{{code_nav_tools}}` 후보.
- **병행 레인 신호**(`parallel_lanes` — 시범 · 기본 off · **신호만 모은다**): `git --version`(≥ 2.31) · bare/서브모듈 여부 · `command -v orca`(→ `worktree_tool` 권고) · `command -v python3` · 지금 브랜치(→ `lane_main_branch` 후보) ·
  락파일·빌드 파일·`.env.example`·시험 DB 설정(→ `lane_prep` 초안) · scripts 의 lint/typecheck/test/build(→ `lane_checks` 초안) · 이미 `scripts/lanes/`·`.claude/lanes/` 가 있나(→ 있으면 **덮지 않는다**).
- **E2E 신호** → `e2e_track`: 브라우저로 조작 가능한 앱 표면이 있나 · 기존 `playwright.config.*`/`cypress.config.*`/spec 폴더(→ `{{e2e_root}}`·`{{e2e_run_cmd}}`) · `grep -r "data-testid"` 건수(→ `e2e_selector`) · 인증 라우트 유무(→ `e2e_auth`).
- **시험 범위 후보** — 스택의 연관 시험 명령 후보(toggles §5.7 표) · 시험 파일 수(실행 없이 센다).

**B. LogiCraft 조회** (project_id 확보 후)
- `project_id` 없으면 `list_projects({q})` 로 검색·사용자 확정. `{{project_name}}` 도 여기서.
- 도메인 목록·이름 → 매핑표(`{{domain_mapping_table}}`) 골격 — 행마다 `{{domain_id}}`·`{{domain_name}}`·`{{domain_short}}`·`{{domain_code_root}}`·`{{domain_agent_name}}`. `get_project_kickoff` → 기술스택·아키텍처 결정.
- ADR(진실원·정책) → 도메인 지침 초안 근거(Phase 4).
- 로컬 키트 `docs/design/*/IMPLEMENTATION.md` 존재·last sync → `has_build` 보강, `{{domain_kit_root}}` · (phase0 on) 키트 ERD → `{{foundation_schema_note}}`.

**C. 슬롯 점검** — `_TEMPLATING.md §1` 카탈로그를 위에서부터 훑어 **각 슬롯의 값·후보·「인터뷰 필요」·「규약 기본값」**을 표로 만든다
(`{{PrefixTitle}}`·`{{conventions_path}}`·`{{change_orders_path}}`·`{{knowhow_dir}}` 처럼 규약 기본값인 것도 표에 넣어 게이트②에서 보인다). 빈칸으로 남는 슬롯이 없게 한다.

산출: **스위치별 추정값(신호 근거 포함) + 슬롯 표**. 자동판정 불가분(work_claim·계층내용·E2E 우회수단·parallel_lanes)은 "인터뷰 필요"로 표시.

### Phase 1 — 아키타입/스위치 확정  🚦게이트①
1. Discovery 신호로 **가까운 프리셋(P1 greenfield-monolith / P2 brownfield-submodule)** 선택.
2. `toggles.md §4` 조합규칙으로 프리셋과 다른 스위치를 **오버라이드** 계산(프리셋 밖 구조도 여기서 흡수).
3. 스위치 표를 사용자에게 제시 — 각 행에 `값 · 근거(신호) · ⚠️override 여부 · 인터뷰필요`:
```
스위치               값        근거
has_build            off       코드 루트에 기존 소스 존재
code_boundary        package   단일 repo, 서브모듈 없음
conventions_location shared ⚠️  monolith 균일 스택 → override(P2 는 embedded)
work_claim           ?         인터뷰 필요 (팀 작업 여부)
parallel_lanes       ?         인터뷰 필요 — 병행 요구 없음 · git worktree 가능 · Orca 없음 · 서브모듈 아니오
프리셋: P2(brownfield) 기반 + monolith 오버라이드(package/single/shared)
```
사용자 확인·수정 후 스위치 확정. (프리셋 밖 새 조합이 반복되면 toggles.md 에 P3 로 승격 제안.)
★ `parallel_lanes` 는 프리셋이 정하지 않는다(둘 다 off). git worktree 가 불가하면(오래된 git · bare · 서브모듈 미해결) **off 로 제시**하고 사유를 적는다.
★ 게이트① 끝에 **Phase 1.5 에서 무엇을 실행할지 목록**을 미리 보인다(없으면 「실측 없음」).

### Phase 1.5 — 실측 확인 (게이트① 뒤 · 호출마다 동의)  🚦
읽어서 얻은 값이 실제와 다른 슬롯만 «돌려 보고» 확정한다. **한 번에 하나씩**, 각 호출 전에 이렇게 보인다:
> 「`<무엇>` 을 실행합니다 — 대상 `<URL·명령·DB>` · 영향 `<생기는 것·지워지는 것>` · 되돌리는 법 `<…>` · 예상 소요 `<…>`. 할까요? (아니오 → 아는 값·수치만 알려 주셔도 됩니다)」

- ☠️ 대상 base_url·DB 가 **localhost·개발 환경이 아니면 멈추고 묻는다**(운영·공유 스테이징 금지 — 우회·삭제가 실제 사용자 데이터에 닿는다).
- **E2E**(`e2e_track` 후보가 on · toggles §5.2):
  - 앱 기동 → `{{e2e_service_up}}`·`{{e2e_base_url}}`·`{{e2e_api_base}}`(문서와 다른 기동 명령·죽은 프로세스가 잡은 포트가 여기서 드러난다).
  - 인증 우회를 태워 세션이 발급되는지 → `{{e2e_auth_bypass}}` · 환경 의존이면 `{{e2e_env_caveat}}`.
  - **시험용으로 만든 데이터 하나**에 대해서만 삭제 API 호출 → `{{e2e_cleanup}}`(오삭제 방지 요구가 400 으로만 드러나는 경우가 많다).
  - 권한을 실제로 써 본다 → `{{e2e_roles}}`·`{{e2e_fixture_setup}}`. 권한 부여가 필요하면 **부여 전에 되돌리는 법을 확정**하고 따로 동의받는다.
- **시험 범위**(toggles §5.7): ① 연관 시험 명령을 한 번 돌려 몇 파일이 도는지 ② 전체 시험을 한 번 돌려 파일 수·건수·소요를 잰다 —
  ☠️ 전체 시험은 오래 걸리고 공유 DB 에 닿을 수 있다 → **소요·DB 접근을 먼저 알리고** 묻는다. 원하지 않으면 사용자가 아는 수치를 받는다.
- 확인 못 한 값은 **비우고 "정보부족"**(추정 금지 — 추정값을 넣으면 그 위에서 3종 스킬 전체가 깨진다).

### Phase 2 — 슬롯 인터뷰  🚦게이트②
Phase 0-C 의 슬롯 표를 보이고, 자동판정 불가한 것만 묻는다:
- `{{prefix}}`(에이전트 접두) · `{{skill_prefix}}`(스킬 접두 — 기본 `{{prefix}}` 와 같다. **다르면 그때만 묻는다**) · `{{PrefixTitle}}`.
  ☠️ 재온보딩이면 **실물 이름을 먼저 보라** — `.claude/skills/` 와 `.claude/agents/` 의 접두가 다를 수 있다. 한 슬롯으로 만들면 스킬이 자기를 틀린 이름으로 부른다.
- `work_claim` on/off (팀 구성 질문).
- `{{shared_base}}`(`code_boundary=package` 일 때) — 후보를 보이고 「도메인 에이전트가 임의로 고치면 안 되는 것」을 고르게 한다. ☠️ 웹앱 기본값(`core/`·`db/migrations/`·앱 진입점)을 묻지 않고 넣지 마라(toggles §5.5).
- `frontend_track` 이 신호로 안 갈리면 묻는다. `{{layer_rounds}}`(dependency_layers=on) — 계약 의존 근거 초안 → 확정. `{{commit_forbidden}}`. `{{code_nav_tools}}`(없으면 빈 값). 매핑표의 code_root·에이전트명 최종 확인.
- **★ QA 검증 모델 4값** — `{{qa_model}}` · `{{qa_invoke}}` · `{{qa_fallback}}` · `{{qa_fail_signal}}`. **자동판정 불가 — 반드시 묻는다**(상세 `references/qa-delegation.md`).
  > 「QA 는 토큰을 가장 많이 먹는 단계입니다. 구현과 **다른 모델**로 돌리면 서로 다른 맹점을 덮고, 토큰 비용을 줄이려면 저렴한 모델을 권합니다.
  >  ① **외부 도구에 위임** — 별도 CLI·러너로 다른 벤더 모델을 부른다. ⚠️ **QA 프롬프트에 실리는 레포 내용(코드·diff·CO·설계 발췌)이 그 벤더로 전송됩니다.**
  >  ② **같은 계열의 값싼 모델** — 지금 세션과 같은 제품군의 저비용 모델을 서브에이전트로.
  >  어느 쪽으로 할까요? 쓰시는 도구·모델 이름을 그대로 알려 주세요.」
  - ☠️ 후보 «목록»을 읽어 제시하지 마라 — **범주 둘만** 제시하고 사용자가 말한 값을 그대로 받는다.
  - ☠️☠️ **받은 값이 실제로 응답하는지 확인**한다 — **동의를 받고**(①이면 반출에 대한 동의 포함) 아주 짧은 과제 하나를 던져 결과를 눈으로 본다.
    없는 모델 이름 → 즉시 실패 → 래퍼가 정상 종료처럼 보임 → 「통과」로 오독 → **검증 0회로 라운드가 닫힌** 실측이 있다. 건너뛰었으면 「미확인」으로 보고한다.
  - ②를 골라도 된다 — 위임 도구가 없는 것이 정상이다. 온보딩 중에 래퍼를 만들라고 요구하지 마라. 판별 신호가 없으면 그 사실을 `qa_fail_signal` 에 적는다(「없음 — 결과 블록 부재로만 판정」).
  - ☠️ 받은 값은 **반드시 방출물에 실린다**(dispatch · build) — Phase 5 가 grep 으로 확인한다.
- **★ 시험 범위** — `{{test_scope_table}}` · `{{full_test_gate}}`(toggles §5.7). Phase 1.5 수치를 보이고 묻는다:
  > 「전체 시험이 N파일·M건·S초입니다. 구현 에이전트와 QA 는 바꾼 파일과 연관된 시험만 돌리고, 전체는 변경지시서를 닫기 직전에 **한 번** 돌리게 하겠습니다(여러 건을 묶어 한 번 / 배포 직전 한 번도 됩니다). 이대로 할까요?」
  ③ 「항상 묶음」(가로지르는 규칙 시험)이 있는지 묻는다. ☠️ 연관 명령을 못 돌려 봤으면 「미확인」 + `없음 — 경로로 고른다` — 추정 명령을 넣으면 에이전트가 **0건을 통과로 읽는다.**
- **★ 설계 반영 워커 모델** `{{backfill_model}}`(toggles §5.4.1) — 「설계 반영도 초안·반영·말단·검사 네 단계로 나눠 값싼 모델에 맡길 수 있습니다. QA 와 같은 것으로 할까요?」 **비우면 `{{qa_model}}` 과 같은 것.**
- **★ 병행 레인** `parallel_lanes`(시범 · toggles SW15·§5.6) — **항상 묻는다**, 기본 off.
  > 「일을 레인(워크트리 하나 + 작업자 하나)으로 병행하는 도구를 넣을까요? 레인마다 워크트리가 따로라 격리되고 메인이 풀려나며 QA 통과분만 한 줄씩 합칩니다. 대가는 자원(설치·빌드 × 레인) · 번호 충돌 관리 · 레인에서 화면 확인을 못 하는 것입니다.」
  on 이면 확정: `{{worktree_tool}}`(기본 git · Orca 가 있으면 권한다) · `{{lane_prep}}`(초안 확정 · 비워도 된다) · `{{lane_checks}}`(`그룹|이름|통과줄|명령` · 시험 단계엔 통과 건수 정규식) ·
  ☠️ 검사 명령에 비밀(토큰·비밀번호)을 넣지 마라 — `--plan` 이 명령을 그대로 찍는다(필요하면 환경 변수로) ·
  `{{lane_concurrency}}` — ★ **반드시 묻는다**(기본값으로 넘기지 마라):
  > 「구현 레인은 동시에 몇 개까지 띄울까요? 기본은 2개입니다. 레인 하나마다 설치·빌드·시험이 따로 돌아 메모리와 CPU 를 그만큼 더 씁니다. 설계 반영(백필) 레인은 이 수에 들어가지 않습니다. 나중에 바꾸려면 레인을 띄울 때 `LANE_MAX=<수>` 를 붙이거나 `scripts/lanes/_common.sh` 의 `LANE_MAX_DEFAULT` 를 고칩니다.」
  답이 없으면 2 · 1 이상 정수만 받는다 · `{{lane_main_branch}}` · `{{lane_heavy_tests}}` · `{{deploy_gate}}`(비우면 사용자 승인만) · `{{backfill_lane_auto}}`(기본 off) ·
  `{{lane_qa_shell}}`(새로 묻지 않는다 — `qa_invoke` 가 셸 실행줄이면 `{label}`·`{prompt}`·`{main}` 자리로 옮겨 보이고 확인만. 자리는 맨으로 쓰거나 자리만 따옴표로 감싼다 — 다른 글자와 붙여 따옴표 안에 넣지 않는다. 갈래 ②면 비운다).
  ☠️ **원본 프로젝트의 값(특정 패키지 관리자 명령·공용 패키지 빌드·DB 꼬리표·원격 배포)을 기본값으로 넣지 마라.**
- **E2E 계정 전략**(`e2e_track=on` · `e2e_auth != none` · toggles §5.3) — **반드시 묻는다**: `{{e2e_roles}}`(역할별 획득 방법 · 부여면 되돌리는 법) · `e2e_account_strategy`(「데이터가 쌓여 있어야만 검증되는 시나리오가 있습니까?」) · `{{e2e_seed_accounts}}`(자격증명 값이 아니라 env 키 이름과 용도) · `{{e2e_groups}}`.

### Phase 3 — 조립 (assembler)
`_TEMPLATING.md` 규약대로 **결정적 치환**한다(외부 엔진 없음 — 이 스킬이 직접):
1. **방출 목록 결정** (스위치 기준 · 스킬 경로는 `{{skill_prefix}}`, 에이전트는 `{{prefix}}`):
   - 항상: `.claude/skills/{{skill_prefix}}-dispatch/SKILL.md` + 같은 폴더 `reference.md`(까닭·실측 — 본문은 절차만) · `.claude/skills/{{skill_prefix}}-design-backfill/SKILL.md` · `.claude/agents/{{prefix}}-qa-verifier.md` · 도메인마다 `.claude/agents/{{domain_agent_name}}.md` · `{{knowhow_dir}}_gen-headnote.py`.
   - `has_build=on`: `.claude/skills/{{skill_prefix}}-build/SKILL.md`.
   - `conventions_location==shared`: `.claude/conventions.md`.
   - `frontend_track=on`: `.claude/agents/{{prefix}}-web-implementer.md`. off 면 생성하지 않고 dispatch·build 의 프론트 참조도 조건 블록으로 함께 빠진다.
   - `parallel_lanes=on`: `scripts/lanes/` 6개(`_common.sh` + `lane-new`·`lane-orca`·`lane-prep`·`lane-qa`·`lane-merge` `.sh` — 뒤 다섯은 `chmod +x`) + `.claude/lanes/lane-prompt-block.md`. dispatch·backfill 에는 「병행 레인」·「백필 레인」 절이 INSERT 된다. ☠️ `scripts/lanes/` 가 이미 있으면 **Write 하지 말고 diff 를 보인다.**
   - `e2e_track=on`: `.claude/e2e-conventions.md` + `.claude/skills/{{skill_prefix}}-e2e-author`/`-run`/`-verify`. 규약 파일을 먼저 만들고 3종이 참조하게 한다(슬롯 값은 규약 한 곳에만).
> ☠️ 아래 「Write」는 **신규 온보딩** 기준이다. 재온보딩이면 §재온보딩의 ①~④를 거친 **병합**이다. 충돌하면 §재온보딩이 우선한다.

1-a. **이미 있는 파일 확인** 🚦 — 신규 온보딩이어도 방출 목록 중 **이미 있는 파일**(예: `.claude/conventions.md` · `{{change_orders_path}}MASTER.md`·`_TEMPLATE.md` · `{{knowhow_dir}}` 안의 파일 · `scripts/lanes/`)을 목록으로 보이고
   파일마다 **diff 보기 → 병합 / 건너뜀 / 덮어쓰기(백업 뒤)** 중 고르게 한다. 묻지 않고 Write 하지 않는다. 특히 MASTER·노하우는 기존 기록이라 덮어쓰기를 권하지 않는다.

2. **각 파일**: 템플릿 Read → `<!-- INSERT … IF sw -->`(on 이면 조각 삽입, off 삭제) → `IF`/`ELSE`/`ENDIF` 해소 → `{{slot}}` 치환 → 방출 경로에 Write.
3. **implementer 는 도메인마다 1회** 인스턴스화. `{{domain_guidance}}` 는 Phase 4 에서 채우므로 여기선 골격으로 두고 Phase 4 후 갱신.
4. 머리말 생성기는 방출 직후 한 번 돌린다(`python3 {{knowhow_dir}}_gen-headnote.py` — 묶음이 없으면 「전부 최신」).

### Phase 4 — 도메인 지침 초안 (설계 정독)  🚦게이트③
`toggles.md §5.1` 대로, 도메인마다 특화지침(책임·경계 / 진실원·엔티티 / 함정 top / 정책·제약 / 코드 레이아웃)을 **근거 ITEM ID 붙여** 초안한다.

**진실원 결정 (로컬 키트는 LogiCraft 의 스냅샷 — 궁극 진실원은 LogiCraft):**
1. **신선도 먼저 판정** — 키트 `version-master`/last sync 와 `_raw` 의 `current_version` 을 LogiCraft 와 대조해 도메인별 **fresh / stale / 없음**.
2. **fresh 면 로컬 키트가 진실원** — `IMPLEMENTATION.md` + 타입별 요약 + `_raw/*.json`. (묻지 않고 진행)
3. **stale 면 3택을 묻는다(자동 결정 금지)** — (a) 현재 키트 그대로(선택 사실을 지침에 명기) · (b) `/mc-logi-implement-kit` SYNC 후(권장) · (c) LogiCraft(live) 직접. drift 요지를 함께 보인다.
4. **키트 없음/부분이면 LogiCraft(live)가 1차** — `get_item`/`list_items`(ADR·ERD·DFEAT·CONST) + 코드에서 추출.
- 근거 없으면 비우고 "정보부족 — 설계 보완 또는 첫 구현 중 확인"으로 보고. 설계가 얇으면 골격만 + "첫 구현 후 노하우로 축적".
- 프론트 트랙이면 `{{web_guidance}}` 도 같은 방식 — 근거는 `screen_spec`·디자인시스템·소비 API 계약.
- 노하우 섹션은 비워 둔다(구현하며 축적). 도메인이 많으면 도메인별 병렬 가능.

### Phase 5 — 검증 · 완료  🚦게이트④
`_TEMPLATING.md §6` 검증 + 아래. 하나라도 실패하면 고치고 다시 본다. **왜 이 검사들이 있는지는 `references/verification-notes.md`.**
- **참조 무결성** — 스킬이 참조하는 모든 `{{prefix}}-*` 에이전트가 `.claude/agents/` 에 실재 · 매핑표 도메인 수 == implementer 수 · `frontend_track=off` 면 `web-implementer` 0건 · shared 면 `.claude/conventions.md` 존재·경로 일치 · e2e 면 규약 + 3종 + 참조 일치 · dispatch `### Phase` 번호 중복 0.
- **역방향 고아** — `.claude/agents/` 중 어느 스킬도 안 부르는 파일을 목록화 → 실패가 아니라 「의도된 독립 실행인가?」로 보고(재온보딩이면 ③질의에 포함).
- **미치환 0** — 방출물 전부(스크립트·`_gen-headnote.py` 포함)에 `{{`·`<!-- IF`·`<!-- ELSE`·`<!-- ENDIF`·`<!-- INSERT` 가 없다.
- **비운 슬롯 보고** — 확인 못 해 비운 것(특히 E2E)을 "정보부족 — 첫 저작 시 확인"으로 목록화.
- **받은 값이 실렸는지(grep)** — QA 4값이 **dispatch 와(`has_build=on` 이면) build** 에 · `{{backfill_model}}` 이 **backfill** 에.
  비우기로 한 `backfill_model` 은 빈 문자열 grep 이 아니라 **「비움 = `<qa_model 값>` 과 동일」 문장**이 backfill 에 있는지로 본다.
- **dispatch 본문·reference** — `reference.md` 방출 · 본문 `wc -l` ~250 안팎 · 본문에 핵심 게이트 문자열이 있는지(grep): `단계 체크리스트` · `탐색근거:` · `QA 계획:` · `노하우 열람 게이트` · `인용 확인` · `read_evidence` · `스키마·마이그레이션을 건드리면` · `Phase 5.95 — 전체 시험 게이트` · `IMPREC 추적 게이트` · `쉬운 말` · (레인 on) `레인 판정:`·`## 병행 레인`. qa-verifier 출력에 `read_evidence:` · 에이전트 3종·레인 블록·backfill 에 `사용자의 언어로`.
- **시험 범위** — ⑴ `{{test_scope_table}}` 이 dispatch(Phase 5.95)·build(Phase E.95)·implementer·web-implementer·qa-verifier·conventions·레인 블록에 **같은 글자로** 실렸다
  ⑵ 에이전트 「자체검증」·QA 「실측 재실행」 절에서 **표 줄(`|` 로 시작)을 뺀 나머지**에 전체 시험 명령이 없다(표 안의 전체 시험 칸은 정상)
  ⑶ dispatch 에 `Phase 5.95 — 전체 시험 게이트`, build 에 `Phase E.95` 와 `{{full_test_gate}}` 값 ⑷ 연관 시험 명령이 Phase 1.5 에서 **0건이 아니었다**(못 돌렸으면 「미확인」).
- **노하우 구조** — `{{knowhow_dir}}`·`{{knowhow_archive_dir}}` 생성 · implementer·web-implementer·qa-verifier **전부**에 `## 노하우 색인`·`## 노하우 — 상시` 와 출력 `knowhow_read`.
- **머리말 규칙이 재어지는지** — ⑴ 에이전트 절차에 `limit=40` ⑵ 스키마에 `how: headnote|items|full` ⑶ dispatch 게이트에 `how` 누락 / `matched` 4건 미만 판정 행 ⑷ 대조 스크립트(dispatch `reference.md`)가 `"limit"` 을 뽑는다.
  ⑸ Phase 5.9(노하우 append)에 `_gen-headnote.py` 호출이 있다 ⑹ `python3 {{knowhow_dir}}_gen-headnote.py --check` 가 rc=0(생성기가 고정점까지 스스로 반복한다 — rc=1 이면 진짜 이상).
- **작성 규칙(1.6.0)** — ⑴ implementer·web 출력에 `design_facts:` · 절차 `Phase 3.5 — 설계 사실 보고` ⑵ dispatch Phase 5 에 `설계 사실 옮겨 적기` · probe_axes 의 design_facts 축 · IMPREC 게이트의 `evidence`
  ⑶ `_TEMPLATE.md` §6 에 「설계 사실」「서술 변경」 ⑷ backfill 에 `fields:` · `작성 규칙 5검사` · 「처음부터 칸에 쓴다」 ⑸ backfill 에 「단계마다 «성공 판정»이 다르다」 표 ⑹ 「재검토 표시 보존 검사」.
- **끊긴 참조** — 본체·스킬이 가리키는 `_knowhow/*.md` 가 전부 실재:
  ```bash
  grep -rhoE '_knowhow/[^ `)」|]+\.md' .claude/agents/*.md .claude/skills/ | sort -u |
    while read r; do [ -f ".claude/agents/$r" ] || echo "끊김: $r"; done
  ```
- **병행 레인**(`parallel_lanes=on`):
  ```bash
  L=scripts/lanes
  for f in _common.sh lane-new.sh lane-orca.sh lane-prep.sh lane-qa.sh lane-merge.sh; do [ -f "$L/$f" ] || echo "없음: $f"; done
  for f in lane-new.sh lane-orca.sh lane-prep.sh lane-qa.sh lane-merge.sh; do [ -x "$L/$f" ] || echo "실행권한 없음: $f"; done
  for f in "$L"/*.sh; do bash -n "$f" || echo "문법 오류: $f"; done
  [ -f .claude/lanes/lane-prompt-block.md ] || echo "없음: 표준 블록"
  grep -q 'knowhow_dir_abs 가 없다' "$L/lane-qa.sh" || echo "lane-qa 의 knowhow_dir_abs 강제가 빠졌다"
  grep -q 'QA_SCOPE_LINE=' "$L/lane-qa.sh" || echo "lane-qa 의 범위 줄 검사가 빠졌다"
  grep -q 'lane_commit' "$L/lane-qa.sh" || echo "lane-qa 의 레인 커밋 고정이 빠졌다"
  grep -q 'lane_pids_in_dir' "$L/lane-merge.sh" || echo "lane-merge 의 남은 프로세스 끝내기가 빠졌다"
  git check-ignore -q .claude/worktrees/x && git check-ignore -q .lane-dispatch || echo "gitignore 누락"
  grep -rn '{{\|<!-- IF\|<!-- ELSE\|<!-- ENDIF\|<!-- INSERT' "$L" .claude/lanes && echo "미치환 잔존"
  grep -rn '/Users/\|/home/' "$L" .claude/lanes && echo "절대경로가 박혔다"
  ```
  ⑴ 슬롯이 실렸는지 — `lane_main_branch`·`lane_concurrency`(게이트②에서 사용자가 답한 값 그대로 — `grep "LANE_MAX_DEFAULT='<답>'"`)·`change_orders_path` 가 `_common.sh` 에, `lane_prep` 단계가 `lane-prep.sh` 에, `lane_checks` 가 `lane-merge.sh` 에, `qa_model`·`qa_fallback`(+`lane_qa_shell`)이 `lane-qa.sh` 에.
     비운 슬롯은 빈 문자열이 아니라 **ELSE 문장**(「준비할 것 없음」·「사용자 승인만」·「서브에이전트 갈래」)으로 본다.
  ⑵ dispatch 에 `## 병행 레인` 절과 Phase 3 게이트 `레인 판정:` 줄 · backfill 에 `## 백필 레인` 절.
  ⑶ **원본 프로젝트 고유값이 새지 않았는지** — 이 스킬을 만든 프로젝트들의 값(저장소 이름·패키지 범위·브랜치 이름·호스트 이름)이 방출물에 없어야 한다.
     검사 패턴은 「이 저장소에 없어야 할 이름」으로 사용자에게 물어 정한다(기본: 다른 프로젝트 이름·운영 호스트 이름).
  ⑷ `lane-merge.sh <아무이름> --plan --worktree /tmp --branch x` 로 검사 단계 목록이 확정한 그대로 찍히는지 본다(아무것도 안 바꾼다 · 「워크트리 목록에 없다」 경고가 함께 나오는 것이 정상).
  `parallel_lanes=off` 면 방출물에 `scripts/lanes` 언급이 없어야 한다.
- **에이전트 본체 줄 수** — `wc -l` 로 세어 보고. 재온보딩이면 400줄 초과분을 §재온보딩 ⑤ 형식으로 게이트에 올린다.
- **부트스트랩**(아래) 생성 — ☠️ 원래 있던 파일(`.gitignore`·`CLAUDE.md`)에 넣을 줄은 **먼저 보이고 확인받은 뒤** 넣는다.
- **보고**: 생성 파일 목록 · 스위치 표 · 비운 슬롯(정보부족) · 실측에서 실행한 것과 결과 · 다음 액션(build 실행 등).

---

## 부트스트랩 파일 (dispatch/build 가 전제하는 것 — Phase 5 에서 함께 생성)

- `{{change_orders_path}}_TEMPLATE.md` — CO 골격: 상단 헤더 표(제목·대상 도메인·구현상태·LogiCraft 설계반영, `work_claim=on` 이면 work_claim 행) + §1 배경 · §2 변경 요지 · §3 도메인별 변경 상세 · §4 영향·리스크 · §5 검증 · §6 관련 설계 ITEM(① 설계 사실 · ② 서술 변경 · ③ 결정 근거(사용자 확정 — ADR·REQ·RFP·NFR 를 만들거나 결정을 바꿀 때)) · §7 구현 로그.
  ★ **§6 은 두 부분** — ① **설계 사실**: `- ITEM.칸: 값 — 근거(코드: 경로:줄 — 조각 · CO §n)` 한 줄씩(구현 에이전트 `design_facts` 를 dispatch Phase 5 가 옮긴다 → backfill 이 칸 값으로 넘긴다) ② **서술 변경**: 산문에 반영할 **현행** 내용. 경위는 §7 에만.
- `{{change_orders_path}}MASTER.md` — `CO번호 · 제목 · 대상도메인 · 구현상태 · 설계반영(⏳/🎨/—) · 커밋 · 생성일` 빈 표.
- (`has_build=on`) `docs/design/BUILD-MASTER.md` — 도메인별 (dependency_layers=on 이면 계층·)구현 상태(⬜/🔨/✅/⚠️) 표.
- `{{knowhow_dir}}` — 빈 디렉토리 + `README.md` 한 단락: 「본체는 **색인만** · 새 노하우는 **주제 묶음에** · **라운드별 섹션 금지** · 본체 400줄 초과면 묶음을 하나 더 판다」.
- `{{knowhow_dir}}_gen-headnote.py` — 묶음 맨 앞에 「먼저 여기만 읽어라」 목록(항목 + 줄 번호)을 만드는 생성기. 이것이 없으면 에이전트는 결국 전문을 연다.
  묶음 항목은 `- **★★ …` / `- **☠️☠️ …` 처럼 **최상위 불릿 + 등급**으로 쓴다는 규약을 README 에 함께 적는다. 파생물이다 — 항목을 더하면 다시 돌린다.
- `{{knowhow_archive_dir}}` — 노하우 정리 시 원문 보관(정리는 지우는 게 아니라 옮기는 것).
- `.gitignore` 에 더할 줄(**게이트④에서 먼저 보이고 확인**): `parallel_lanes=on` 이면 `.claude/worktrees/`·`.lane-dispatch` · `e2e_auth != none` 이면 `{{e2e_storage_dir}}`(로그인 세션 그 자체).
- (선택 · 제안만) 루트 `CLAUDE.md` 에 세트 사용법 안내 블록(수정·구현·backfill 진입점). `parallel_lanes=on` 이면 「병행 레인」 한 단락(동시 상한 · 도구 · 공용 기록의 주인 · 번호는 메인이 정한다)을 더 제안한다.

## 게이트 요약
1. Phase 1 — 아키타입/스위치 확정 (재온보딩이면 그 전에 Phase 0 ⓪ 백업)
2. Phase 1.5 — 실측 실행마다 동의 (실측할 것이 없으면 건너뜀)
3. Phase 2 — 슬롯 인터뷰 (QA 모델 시험 호출 · 외부 위임 반출 동의 포함)
3-a. Phase 3 1-a — 이미 있는 파일마다 병합/건너뜀/덮어쓰기 선택
4. Phase 4 — 도메인 지침 초안 확정 (+ 키트 stale 시 진실원 3택)
5. Phase 5 — 최종 검증 (+ `.gitignore`·`CLAUDE.md` 에 넣을 줄 확인)

재온보딩이면 둘 더: **③ 질의**(실물에만 있는 절·호출을 보존/승격/폐기) · **⑤ 노하우 정리**(본체 400줄 초과 시 분류 초안). 건너뛰면 손으로 쌓은 것을 조용히 덮어쓴다.

## 재온보딩 (업그레이드 모드)

이미 세트가 있는 프로젝트에서 다시 실행하면(Phase 0-A 가 감지) **신규 온보딩과 다르게 돈다.** 상세·판정 기준·실측은 **`references/reonboarding.md`**.

> ☠️ **세트는 쓰이면서 자란다.** 라운드마다 실사고에서 얻은 규약이 붙는다 — **템플릿에 없는 자산**이다. 모르고 덮으면 그 프로젝트가 겪은 사고를 다시 겪는다
> (실측: 수정 절차서 690줄 vs 템플릿 186줄, 설계 반영 절차서 960줄 vs 116줄).

**⓪ 백업** — Phase 0 의 ⓪(레포 밖 백업)을 이미 했다.

**① 감지** — 실물과 새 조립 결과를 대조해 **실물에만 있는 절**(헤딩·줄 수)을 뽑는다. ☠️ 제목 비교는 문구만 바뀐 같은 절도 잡는다 — 「후보」이지 결론이 아니다.
- **①-a 버전 신호** — 실물이 어느 버전에서 멈췄는지 보고 「이번 업그레이드로 받을 것」을 게이트①에 올린다(1.6.0 작성 규칙 · 1.7.0 Phase 번호·frontend_track·shared_base · 1.8.0 병행 레인 · 1.9.0 시험 범위 · 1.10.x 레인·안전 · **1.11.0 dispatch 본문·reference 분리 · 마이그레이션 절차 · QA 인용 확인 · 보고 언어** · 1.11.1 결정 근거 · 1.11.2 레인 동시 상한을 묻는다 — 레인이 켜진 세트면 지금 `LANE_MAX_DEFAULT` 값을 보이고 유지할지 묻는다). 버전별 목록은 reference ①-a.
  새 절은 실물의 커스텀 절을 덮지 말고 **끼워 넣는다.** 기존 CO 파일은 고치지 않는다(`_TEMPLATE.md` 만).
- **①-b 참조 감지** — 헤딩 비교로는 «호출 한 줄»을 놓친다. **실물 스킬이 참조하는 심볼 − 신규 방출물이 참조하는 심볼 = 사라질 호출**을 **기계로** 뽑는다(reference 에 명령). 한 줄이라도 있으면 ③질의.

**② 분석** — 덩어리마다 분류 초안(근거 첨부): **개작**(같은 역할 · 문구만 다름 → 신규 채택) · **범용**(→ 템플릿 승격) · **프로젝트 전용**(→ 보존) · **낡음**(→ 폐기 후보).
☠️ 「개작」으로 판정한 `##` 절도 버리기 전에 `###`/`####` 하위 절을 훑어 **프로젝트 고유 하위 규약을 살려 옮긴다**(원래 소속 Phase 를 명시) — 통째로 버려 고유 규약 4개·CO 증거 9건을 잃은 실측이 있다. 검증은 CO 번호·파일 경로 같은 **고유 식별자 집합**으로.

**③ 묻는다** 🚦 — 분류 초안을 근거와 함께 보이고 「이건 무엇이고 어떻게 할까요」. 자동 판정 금지(특히 「낡음」).

**④ 처리** — 확정된 것만: 보존(다시 끼워 넣기) · 폐기(보관본을 남기고 보고) · **승격 제안** — 설치된 이 스킬(templates·`_TEMPLATING.md`)은 고치지 않는다.
  범용으로 판정한 절은 `.claude/onboard-upstream-proposals-<날짜>.md` 로 내보내(어느 템플릿 어디에 · 근거 · 원문) 이 스킬의 작성자·관리자에게 보고하게 한다.
- 보존이 덮어쓰기를 이긴다. 스위치 변경은 그대로 반영. 도메인 지침·노하우는 보존.
- `scripts/lanes/`·`.claude/lanes/` 가 이미 있으면 파일별 `diff -u` 를 보이고 실물에만 있는 단계·종료코드·검사를 ③에 올린다(실물 고유값은 슬롯 값 후보).

**⑤ 노하우 정리** 🚦 — 본체 400줄 초과면 게이트. 「나눌까요?」만 묻지 말고 **분류 초안**을 만들어 묻는다:
① 섹션별 분량 표 ② 라운드 조각(`CO-NNN`·날짜 제목)과 흡수될 주제 ③ 본체/묶음 배분과 근거 — **되돌리기 어려운 금지 규칙은 본체 `## 노하우 — 상시`**, 묶음은 색인에 **「이 행동을 하기 전」**으로 건다 ④ 삭제 후보와 근거 + 본체 예상 줄 수.
- 색인·상시·`knowhow_read` 는 400줄 초과분만이 아니라 **모든 본체에** 입힌다.
- 묶음 600줄은 쪼갤 이유가 아니라 **검토 신호**다 — ① 중복 정리 ② 잘못 놓인 항목 재배치 ③ 그래도 크면 «서로 다른 순간에 필요한가»로 판정해 **평면으로** 쪼갠다(묶음 안에 묶음 금지). 쪼갠 직후 끊긴 참조 검사.
- 정리는 **보관이 먼저** — `{{knowhow_archive_dir}}` 로 원문을 뜨고 제목 단위 대조로 **유실 0건**(본체 + 묶음 합산)을 확인한 뒤 뺀다.
- 결과를 표로: 감지 N → **개작(위양성) N** · 승격 · 보존 · 폐기 · 보류. 개작을 걸러낸 뒤의 수가 실제 판단 대상이다.

**⑥ 사후 측정** — 노하우를 묶음으로 옮기면 «항상 주입»이 «열어야 읽힘»으로 바뀐다. 라운드마다 묶음 열람 수와 `knowhow_read` ↔ 전사본 불일치를 재고, **최소 3라운드**로 판정한다(`references/knowhow-measurement.md`). 열람이 늘었다고 사고가 준다고 보고하지 마라 — 노하우는 이미 아는 함정만 막는다.

## 버전 기록

- **1.11.2** (2026-11-18) — 구현 레인 동시 상한(`lane_concurrency`)을 사용자에게 묻는다. 지금까지는 확정할 값 목록에 「기본 2」로만 있어 묻지 않고 2로 넘어갈 수 있었다. 질문 문장(자원 비용 · 백필 레인은 세지 않음 · 나중에 바꾸는 법)을 넣고, 재온보딩이면 현재 값을 보이고 유지할지 묻는다 · 검증은 답한 값이 `_common.sh` 에 실렸는지 본다. · `lane-qa.sh` 의 판정 읽기를 판정값 넷(pass_with_notes·pass·fail·blocked)으로 좁혔다 — 위임 래퍼의 요약 줄 `verdict : ok` 가 맨 뒤에 붙어 진짜 판정을 덮는 일이 있었다.

- **1.11.1** (2026-11-17) — 결정 근거(출처). LogiCraft 가 ADR·REQ·RFP·NFR 의 결정 변경에 근거를 받는데, 설계 반영 작업자가 CO 본문의 사용자 말을 따다 근거를 스스로 채운 실사고가 있었다. dispatch 는 CO 를 쓸 때 근거를 묻고 `_TEMPLATE.md` §6 「③ 결정 근거(사용자 확정)」에 적는다 · backfill 은 그 칸만 쓰고 비면 `unknown`·`not_written` 으로 남겨 보고한다(지어 채우기 금지).

- **1.11.0** (2026-11-16) — 첫 실전 프로젝트(한 세션 · 변경지시서 11건) 현장 보고 중 넷만 반영.
  - 방출 dispatch 를 절차만 남겨 줄였다(스위치 전부 on 렌더 632 → 257줄 · 대화 압축 때 Phase 3 게이트 형식·열람 대조·스킬 재호출이 잘려 나갔다). 사례·까닭은 같은 폴더 `reference.md` 로(📎 표시) · 맨 앞에 「단계 체크리스트」 · 압축되면 스킬을 다시 부르라는 줄.
  - 메인이 쓰는 스키마·마이그레이션 절차 4단계(사본에 먼저 적용해 표별 행 수 비교 · 옛→새 모양 시험 · 자동 적용 중지 · QA 전수 + 명시 축) — 현장 결함 둘이 모두 메인이 쓴 마이그레이션에서 나왔다.
  - QA 인용 확인 — pass 전에 `read_evidence` 가 이번 바뀐 파일을 실제로 인용하고 그 경로가 저장소에 있는지 본다(아니면 「안 돎」 → 대체 경로). qa-verifier 출력에 `read_evidence` 필수 · `lane-qa.sh` 가 자동으로 본다(종료 23). 다른 모델이 남의 프로젝트 내용을 지어내 pass 를 낸 현장 사례.
  - 보고 언어 — 에이전트·QA·레인 작업자·백필 워커는 사용자의 언어로 보고(프로젝트 지침 · 없으면 사용자 언어) · 사용자 최종 보고는 내부 용어 대신 쉬운 말로.
- **1.10.1** (2026-11-16) — 재검토 반영. 합치기가 «레인»만 받게(사용자 기능 워크트리를 넘기면 거절 — 실측 재현 사고) · 남은 프로세스 끝내기에서 터미널 붙은 것·셸·편집기는 끝내지 않고 정리를 멈춤 · -9 는 PID 를 다시 구해 터미널 없는 것에만 · 더러운지 먼저 확인 ·
  QA 실행줄 자리를 변수 참조로(한글·공백 경로 · bash 3.2) · 출력 거르기 확대 · 잠금 신호 처리와 낡은 잠금·예약 걷기 · 필요한 스킬 의존(mc-logi-update 등)과 용어 표 · 신규 온보딩도 이미 있는 파일은 묻고 병합 · 승격은 스킬을 고치지 않고 제안 파일로 ·
  백업에서 레인 워크트리 제외·권한 700 · `--push` 는 계획을 보이고 동의 뒤 · 도메인 에이전트 이름을 매핑표 기준으로 · 낡은 절 참조 정리 · 작성자 환경 흔적(orca-dev 등) 제거 · description 축약.
- **1.10.0** (2026-11-16) — 공유 마켓 공개를 위한 정리.
  - 안전: 실측 실행(앱 기동·삭제 API·권한 부여·전체 시험·QA 시험 호출)을 게이트① 뒤 **Phase 1.5** 로 옮기고 호출마다 동의 · localhost 가 아니면 멈춤 · 외부 QA 위임의 **데이터 반출 고지** · 재온보딩 백업을 **레포 밖**으로 · `.gitignore` 수정은 먼저 보이고 확인 · 재온보딩 백업 절을 본체 앞쪽(Phase 0 ⓪)으로.
  - 정합: 스킬 경로를 전부 `{{skill_prefix}}` 로 · build 에 QA 4값 표와 `Phase E.95 전체 시험 게이트` · 시험 범위 검사가 표 줄을 빼고 보게 · toggles 절 번호 정리(§5.4.1·§5.7) · 슬롯 카탈로그에 「출처」 칸과 `{{code_nav_tools}}` · `knowhow_dir_abs` 를 슬롯에서 빼고 실행 시 계산 · 머리말 생성기가 스스로 고정점까지 반복 · backfill 의 분업 「레인」을 「단계」로.
  - 레인 스크립트: 메인 찾기를 서브모듈에서도 맞게(core.worktree) · git 2.31 미만을 먼저 알림 · 출력 거르기 확대(password=·token=·bearer) · 합치기의 남은 프로세스 끝내기(이름으로만 판정 · 명령줄 비출력 · 부른 셸 제외 · /proc 대체) · 지울 워크트리·브랜치 확인 · QA 범위 줄 검사 · 동시 상한을 잠금 + 죽은 레인 제외로 · 작업자 블록에 부하·백그라운드 정리 금지 두 줄.
  - 본체를 줄이고 실측 서술을 `references/` 로 옮기며 사례 이름을 익명화했다. 필요한 도구 절 · 한국어 전용 명시.
- 1.9.0 시험 범위(전체 시험은 CO 하나에 한 번) · 1.8.0 병행 레인(시범) · 1.7.0 Phase 번호·frontend_track·shared_base · 1.6.0 작성 규칙(설계는 처음부터 칸에) — 각 버전에서 받을 것은 `references/reonboarding.md` ①-a.
