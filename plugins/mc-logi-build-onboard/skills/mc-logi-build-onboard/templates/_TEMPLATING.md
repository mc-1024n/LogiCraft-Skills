# _TEMPLATING.md — 템플릿 조립 문법 규약

`mc-logi-build-onboard` 가 `_invariant/*`·`_switched/*` 를 읽어 실제 스킬·에이전트로 방출할 때 쓰는 치환 문법이다. 조립기(SKILL.md 「Phase 3 — 조립」)는 이 규약대로 처리한다.

## 1. 슬롯 치환 (값 채움) — `{{slot}}`
- `{{slot_name}}` → 리터럴 문자열로 치환. Discovery/인터뷰가 값 제공(toggles.md §5).
- 값이 없으면 채우지 말고 **"정보부족"으로 남기고 보고**(placeholder·가짜값 금지).
- ★ **이 절이 슬롯 카탈로그의 진실원이다.** 템플릿이 쓰는 슬롯은 전부 여기 있고, 표마다 「출처」(어디서 값을 얻나)가 있다.
  SKILL.md Phase 0~2 는 이 표를 훑어 **값이 안 정해진 슬롯이 남지 않게** 한다. toggles.md §5 는 판정 해설이다.
- 산출물(스킬·에이전트·규약)의 문장은 **한국어**다 — 이 세트는 한국어 팀을 전제로 쓰였다. 다른 언어로 쓰려면 템플릿을 번역해 쓴다.

**공통 슬롯**
| 슬롯 | 의미 | 출처 |
|---|---|---|
| `{{prefix}}` | **에이전트** 접두사 (`acme`) — `acme-d001-implementer` | 인터뷰 |
| `{{skill_prefix}}` | **스킬** 접두사. 비우면 `{{prefix}}` 와 같다 — `team-acme-dispatch` 처럼 **스킬만 접두를 더 붙이는** 프로젝트가 있다 | 인터뷰(다를 때만) |
| `{{PrefixTitle}}` | 사람용 제목 표기 (`Acme`) | 인터뷰 — 기본은 프로젝트 이름 |
| `{{project_id}}` | LogiCraft project UUID | LogiCraft / CLAUDE.md |
| `{{project_name}}` | "Acme Platform" | LogiCraft |
| `{{code_base}}` | 코드 루트 (monolith `src/<pkg>` / submodule `<서브모듈 루트 폴더>`) | repo 스캔 |
| `{{change_orders_path}}` | `.claude/change-orders/` — ★ **끝에 `/` 를 붙인다**(뒤에 파일 이름이 바로 붙는다) | 규약(기본값) |
| `{{conventions_path}}` | `.claude/conventions.md` (shared 일 때 고정) | 규약(고정) |
| `{{domain_mapping_table}}` | 도메인↔code_root↔에이전트 매핑표 전체 | LogiCraft 도메인 + repo 스캔 → 게이트② 확인 |
| `{{build_cmds}}` | 빌드·테스트·린트 명령(전부 — 규약 파일의 목록용. 🚫 에이전트의 자체검증 줄에 그대로 넣지 않는다 — 전체 시험이 매번 돈다) | repo(Makefile·package.json·pyproject·gradle) |
| `{{test_scope_table}}` | ★ 시험 범위 표 — 갈래(백엔드·프론트 등)마다 네 줄: **검사**(lint·typecheck·build) · **연관 시험**(바꾼 파일을 넘기는 명령 · 없으면 「없음 — 경로로 고른다」) · **항상 묶음**(가로지르는 규칙 시험 경로 · 없으면 「없음」) · **전체 시험**(+ 실측 파일 수·건수·소요). toggles.md §5.7 | repo 초안 → **실측(동의 후) + 인터뷰** |
| `{{full_test_gate}}` | 전체 시험을 언제 한 번 돌리나 — `per_co`(기본) · `per_batch` · `pre_deploy`. toggles.md §5.7 | 인터뷰 |
| `{{commit_forbidden}}` | 커밋금지 파일 목록 | 인터뷰 + repo(.gitignore·비밀 파일) |
| `{{code_nav_tools}}` | 에이전트 `tools:` 에 더할 코드 탐색 MCP 도구(쉼표로 이음 — 예 `mcp__serena__find_symbol, mcp__serena__get_symbols_overview`). **빈 값이면 그 자리가 통째로 빠진다**(슬롯 조건) | Discovery(설치된 MCP 확인) → 인터뷰 · 없으면 빈 값 |

**검증 위임 슬롯** (★ 인터뷰 필수 — toggles.md §5.4. dispatch·backfill·qa-verifier 가 공유한다)

| 슬롯 | 의미 | 출처 |
|---|---|---|
| `{{qa_model}}` | 독립 QA 를 돌릴 **모델 또는 위임 방식**. 구현과 **다른 모델**이어야 서로 다른 맹점을 덮는다 | ★ 인터뷰 (두 갈래 제시 — 외부 도구 위임 / 같은 계열의 값싼 모델) |
| `{{qa_invoke}}` | 그걸 **실제로 부르는 명령·호출 형태** (래퍼 스크립트 경로 등). 이름만 적으면 다음 세션이 못 쓴다 | ★ 인터뷰 + 그 자리에서 실행 확인 |
| `{{qa_fallback}}` | 그 모델이 **실패했을 때 무엇으로** 돌릴지(예: 메인 세션 서브에이전트 + 모델명) | ★ 인터뷰 |
| `{{qa_fail_signal}}` | 「**아예 안 돈 것**」과 「**돌았는데 종료코드만 이상한 것**」을 가르는 신호. 없으면 만들어야 한다 | ★ 인터뷰 + 실측 |
| `{{backfill_model}}` | 설계 backfill 분업 워커를 돌릴 모델·위임 방식. 비우면 `{{qa_model}}` 과 같은 것으로 본다(방출물에 「비움 = `<qa_model>` 과 동일」 문장이 실린다 — 슬롯 조건) | ★ 인터뷰 (없으면 빈 값) |

☠️ **이 다섯은 「물어만 보고 안 싣는」 사고가 실제로 났던 자리다**(2026-09-16 인터뷰만 추가되고
방출 템플릿에 슬롯이 없었다). 슬롯이 여기 등록돼 있어야 §6 미치환 스캔에 걸린다.

**노하우 구조 슬롯**

| 슬롯 | 의미 | 출처 |
|---|---|---|
| `{{knowhow_dir}}` | 주제별 노하우 묶음 디렉토리 (기본 `.claude/agents/_knowhow/` · 끝에 `/`) | 규약(기본값) |
| `{{knowhow_archive_dir}}` | 정리 시 원문 보관 디렉토리 (기본 `.claude/agents/_archive/`) | 규약(기본값) |

★ **묶음의 절대경로(`knowhow_dir_abs`)는 슬롯이 아니다** — 커밋되는 파일에 절대경로를 박으면 팀원마다 저장소 자리가 달라 틀린다.
  방출물은 **부를 때 계산**한다: `"$(git rev-parse --show-toplevel)/{{knowhow_dir}}"`(레인 스크립트는 `lane_main_root` 로).
  프롬프트의 `knowhow_dir_abs:` 줄은 오케스트레이터가 그 값으로 채운다.

**병행 레인 슬롯** (`parallel_lanes=on` — `_switched/lanes/*`·`lanes.*.section.md` 용 · toggles.md §5.6)

| 슬롯 | 의미 | 출처 |
|---|---|---|
| `{{worktree_tool}}` | 구현 레인의 기본 길 — `git`(lane-new.sh + 서브에이전트) \| `orca`(lane-orca.sh + Orca 작업자). **조건으로도 쓴다** — `<!-- IF worktree_tool == orca -->` | ★ 인터뷰 · 기본 `git` · Orca 설치 시 `orca` 권함 |
| `{{lane_prep}}` | 준비 단계 — bash 배열 원소 줄들 `"이름\|명령"` (한 줄 하나 · 큰따옴표로 감싼다 · 명령은 워크트리 꼭대기에서 하위 셸 · `lane_link_from_main <경로>` 로 환경 파일 링크). **빈 값 → 빈 배열**(IF/ELSE) | ★ repo 스캔 초안 → 인터뷰 |
| `{{lane_checks}}` | 합치기 검사 — 배열 원소 줄들 `"그룹\|이름\|통과줄 정규식 또는 -\|명령"` · 그룹 `always` 는 늘 돈다 · `lane_changed_files <명령…>` 로 합친 파일만 넘긴다 · 정규식에 `\|` 금지 | ★ 빌드 파일 초안 → 인터뷰 |
| `{{lane_concurrency}}` | 구현 레인 동시 상한(숫자) | 인터뷰 · 기본 `2` |
| `{{deploy_gate}}` | 배포 전 확인 한 줄. **빈 값 → 「사용자 승인만」 문장**(IF/ELSE) | 인터뷰 |
| `{{backfill_lane_auto}}` | `on`\|`off` — 설계반영 ⏳ 가 생기면 묻지 않고 백필 레인을 띄우나. **조건으로 쓸 때는 `== on`** (`off` 도 빈 값이 아니라서 맨 `IF` 는 늘 참이 된다) | 인터뷰 · 기본 `off` |
| `{{lane_main_branch}}` | 레인이 갈라지고 합쳐질 메인 브랜치 | repo(지금 체크아웃) + 확인 |
| `{{lane_qa_shell}}` | `{{qa_invoke}}` 를 셸 한 줄로 옮긴 것 — 자리 `{label}`·`{prompt}`·`{main}`. 자리는 맨으로 쓰거나 자리만 따옴표로 감싼다(다른 글자와 붙여 따옴표 안에 넣지 않는다 — 공백 든 경로가 갈라진다). **빈 값 → 서브에이전트 갈래**(`lane-qa.sh` 가 22 로 알리고 `--verdict-from` 을 쓴다) | **새로 묻지 않는다** — `qa_invoke` 에서 파생 |
| `{{lane_heavy_tests}}` | 한 번에 한 레인만 돌릴 무거운 시험 설명 — **빈 값이면 그 절이 통째로 빠진다**(슬롯 조건) | 인터뷰 · 비울 수 있음 |

★ 셸 템플릿(`*.sh.tmpl`)에 슬롯을 넣는 규칙 — **값에 따옴표·`$`·줄바꿈이 있을 수 있는 슬롯**(`qa_*`·`lane_qa_shell`)은
  **따옴표 heredoc(`<<'EOF'`)** 안에만 넣는다. 주석·큰따옴표 문자열 안에 직접 넣으면 여러 줄 값이 코드가 되거나 `$(…)` 가 실행된다.
  짧은 고정 꼴 값(`lane_main_branch`·`lane_concurrency`·`change_orders_path`)만 작은따옴표 대입에 넣는다.

**도메인별 슬롯** (implementer 는 도메인마다 1회 인스턴스화 — 출처는 전부 매핑표 행, `domain_guidance` 만 Phase 4)
| 슬롯 | 의미 |
|---|---|
| `{{domain_id}}` | `DOMAIN-001` |
| `{{domain_name}}` | "데이터 수집·적재" |
| `{{domain_short}}` | "D001" |
| `{{domain_agent_name}}` | `acme-d001-implementer` |
| `{{domain_code_root}}` | 이 도메인 code_root |
| `{{domain_kit_root}}` | 이 도메인 키트 경로 (has_build 시) |
| `{{domain_guidance}}` | ★ 온보딩이 설계 정독해 초안한 특화지침(toggles §5.1). 근거 없으면 골격만. |

**conventions/build 슬롯** (`_switched/conventions.tmpl.md`·`build.SKILL.tmpl.md`·하위 조각용)
| 슬롯 | 의미 | 출처 |
|---|---|---|
| `{{tech_stack_table}}` | 확정 기술 스택 표 (영역·스택·근거) | LogiCraft ADR/킥오프 + repo(pyproject/build.gradle) |
| `{{package_layout}}` | 코드 레이아웃 트리 | repo 스캔 |
| `{{frontend_stack_block}}` | 프론트 트랙 스택 블록 (없으면 빈 문자열) | repo(package.json) + 키트 DS |
| `{{frontend_code_root}}` | 프론트 code_root (`frontend`) — web-implementer 용 | repo 스캔 |
| `{{shared_base}}` | 공유기반 경로 한 줄 나열 (`code_boundary=package` 일 때 — 예 `` `core/`·`db/migrations/`·앱 진입점 ``). 프로젝트마다 다르다 — toggles.md §5.5 | repo 스캔 후보 → **인터뷰 확정** |
| `{{frontend_stack_short}}` | 프론트 스택 짧은 표기 (Next.js / React SPA) — 제목·description 용 | repo(package.json) |
| `{{web_guidance}}` | ★ 온보딩이 screen_spec·DS·consumes_apis 정독해 초안한 프론트 특화지침(근거 SCREEN/API/DS ID 첨부). 근거 없으면 골격만. | screen_spec + design_system + api 계약 |
| `{{layer_rounds}}` | 의존 계층 라운드 순서 (dependency_layers=on) | 인터뷰 (LogiCraft 계약 의존 참고) |
| `{{foundation_schema_note}}` | Phase 0 스키마 부연 (없으면 빈 문자열) | 키트 ERD |

**E2E 슬롯** (`e2e_track=on` — `e2e-conventions.tmpl.md`·`e2e-{author,run,verify}.SKILL.tmpl.md` 용)
★ 이 슬롯들은 **읽어서 추정하지 말고 실제로 실행·호출해 확인한 값**만 넣는다(toggles.md §5.2).

| 슬롯 | 의미 | 출처 |
|---|---|---|
| `{{e2e_root}}` | spec 디렉토리 (`apps/web/e2e`) | repo 스캔 |
| `{{e2e_base_url}}` | 프론트 진입점 (`http://localhost:3000`) | repo + 실행 확인 |
| `{{e2e_api_base}}` | API 베이스 (fixture·정리용) | repo + 실행 확인 |
| `{{e2e_run_cmd}}` | 실행 명령 (`npx playwright test`) | package.json scripts |
| `{{e2e_service_up}}` | 기동 절차 + 준비 확인 방법 (여러 줄 가능) | ★ 실제로 띄워보고 |
| `{{e2e_auth_bypass}}` | 전제조건 로그인 우회 코드 스니펫 | ★ 실제로 통과시켜보고 |
| `{{e2e_env_caveat}}` | 우회가 의존하는 환경 조건 (없으면 **빈 값** → 블록 통째 삭제) | ★ 확인된 것만 |
| `{{e2e_fixture_setup}}` | 사전 데이터·권한 준비 (없으면 빈 값) | 인터뷰 + 코드 |
| `{{e2e_cleanup}}` | 테스트 데이터 정리 방법 (오삭제 방지 요구사항 포함) | ★ 실제로 호출해보고 |
| `{{e2e_roles}}` | 역할(권한 등급) 목록 + **각 역할의 획득 방법** | ★ 인터뷰 + 권한 카탈로그 |
| `{{e2e_seed_accounts}}` | 시드 계정 — **자격증명이 아니라 env 키 이름과 용도** (없으면 빈 값) | ★ 인터뷰 |
| `{{e2e_storage_dir}}` | `storageState` 저장 경로 (기본 `<e2e_root>/.auth`) — gitignore 필수 | 규약 |
| `{{e2e_groups}}` | 시나리오 그룹 태그 체계 | ★ 인터뷰 + 시나리오 성격 |

## 2. 조건 블록 (스위치) — `<!-- IF ... -->`
```
<!-- IF has_build -->
...has_build=on 일 때만 남는 내용...
<!-- ENDIF has_build -->
```
- 다값 스위치는 `==` 비교: `<!-- IF agent_mode == dual -->` / `<!-- IF code_boundary == package -->` / `<!-- IF commit_strategy == submodule -->`.
- `<!-- ELSE -->` 지원:
```
<!-- IF agent_mode == dual -->A<!-- ELSE -->B<!-- ENDIF agent_mode -->
```
- off(또는 조건 불일치)면 블록 통째로 **삭제**(주석 마커도 제거).
- **슬롯도 조건이 될 수 있다** — `<!-- IF e2e_env_caveat -->` 처럼 슬롯명을 쓰면 그 슬롯이 **빈 값일 때 블록 삭제**,
  값이 있으면 유지한다. 선택적 절(있으면 쓰고 없으면 통째로 빠지는 경고·준비 블록)에 쓴다.
  → 빈 슬롯을 그냥 치환하면 `⚠️ 환경 전제:` 뒤가 비어버리는 어색한 문서가 나온다. 이 문법으로 막는다.

**스위치 이름**(toggles.md §1): `has_build` · `phase0_foundation` · `dependency_layers` · `work_claim` · `commit_strategy`(single|submodule) · `agent_mode`(dual|modify) · `conventions_location`(shared|embedded) · `code_boundary`(package|submodule|repo) · `e2e_track` · `e2e_design_link`(logicraft|local) · `e2e_auth`(none|bypass|bypass_and_verify) · `e2e_selector`(testid|role) · `e2e_account_strategy`(self_provision|seed|mixed) · `frontend_track` · `parallel_lanes`

## 3. 조각 삽입 — `<!-- INSERT ... -->`
```
<!-- INSERT _switched/work_claim.recon.md IF work_claim -->
```
- 스위치가 on 이면 그 파일 내용을 이 위치에 끼워넣고(그 파일도 슬롯 치환 대상), off 면 마커 삭제.
- `IF` 없이 쓰면 무조건 삽입(불변 조각 재사용).

## 4. 도메인 반복 — implementer.tmpl.md
`implementer.tmpl.md` 는 **매핑표의 도메인마다 1회** 인스턴스화한다(도메인별 슬롯 치환). `frontend_track=on` 이면 `{{prefix}}-web-implementer` 도 별도 생성(웹 전용 변형은 조립기가 프론트 슬롯으로).

## 5. 방출 위치
| 템플릿 | 방출 경로 |
|---|---|
| dispatch.SKILL.tmpl.md | `.claude/skills/{{skill_prefix}}-dispatch/SKILL.md` — ★ 절차만(단계 체크리스트·게이트 형식·체크리스트). 렌더 결과가 스위치 전부 on 에서도 ~250줄 안팎이어야 한다(대화 압축 때 잘리지 않게) |
| dispatch.reference.tmpl.md | `.claude/skills/{{skill_prefix}}-dispatch/reference.md` — 본문 📎 표시가 가리키는 까닭·실측 사례. 🚫 규칙(명령문)은 넣지 않는다 — 규칙은 본문에 |
| backfill.SKILL.tmpl.md | `.claude/skills/{{skill_prefix}}-design-backfill/SKILL.md` |
| _switched/build.SKILL.tmpl.md (IF has_build) | `.claude/skills/{{skill_prefix}}-build/SKILL.md` |
| _switched/conventions.tmpl.md (IF shared) | `.claude/conventions.md` |
| implementer.tmpl.md ×N | `.claude/agents/{{domain_agent_name}}.md` |
| qa-verifier.tmpl.md | `.claude/agents/{{prefix}}-qa-verifier.md` |
| _switched/web-implementer.tmpl.md (IF frontend_track) | `.claude/agents/{{prefix}}-web-implementer.md` |
| _switched/e2e-conventions.tmpl.md (IF e2e_track) | `.claude/e2e-conventions.md` |
| _switched/e2e-author.SKILL.tmpl.md (IF e2e_track) | `.claude/skills/{{skill_prefix}}-e2e-author/SKILL.md` |
| _switched/e2e-run.SKILL.tmpl.md (IF e2e_track) | `.claude/skills/{{skill_prefix}}-e2e-run/SKILL.md` |
| _switched/e2e-verify.SKILL.tmpl.md (IF e2e_track) | `.claude/skills/{{skill_prefix}}-e2e-verify/SKILL.md` |
| _switched/lanes/_common.sh.tmpl (IF parallel_lanes) | `scripts/lanes/_common.sh` (source 전용 · 실행 권한 불필요) |
| _switched/lanes/lane-{new,orca,prep,qa,merge}.sh.tmpl (IF parallel_lanes) | `scripts/lanes/lane-{new,orca,prep,qa,merge}.sh` — ★ **`chmod +x`** |
| _switched/lanes/lane-prompt-block.tmpl.md (IF parallel_lanes) | `.claude/lanes/lane-prompt-block.md` |
| _switched/lanes.dispatch.section.md · lanes.backfill.section.md | (방출 파일 아님 — dispatch·backfill 안에 `INSERT`) |
| _assets/_gen-headnote.py | `{{knowhow_dir}}_gen-headnote.py` — 노하우 머리말 생성기(이 파일도 슬롯 치환·미치환 스캔 대상) |

☠️ **방출 경로의 스킬명은 `{{skill_prefix}}`, 에이전트명은 `{{prefix}}`** 다. 둘을 섞으면
스킬이 **자기를 틀린 이름으로 부른다**(실측: 스킬만 접두를 더 붙이는 프로젝트에서 한 슬롯으로 만들다가
`team-acme-dispatch` 가 자기를 `acme-dispatch` 라 부르는 조립본이 나왔다).

☠️ **`scripts/lanes/` 가 이미 있으면 덮지 마라** — 재온보딩(업그레이드 모드)과 같은 규약이다: 파일별 diff 를 보이고 질의한 뒤 병합한다(`references/reonboarding.md` ①-a‴).

**디렉토리**(파일 없이 생성 — 부트스트랩)
| 대상 | 경로 | 왜 |
|---|---|---|
| 노하우 묶음 | `{{knowhow_dir}}` | 주제별 노하우가 여기 쌓인다. 에이전트 본체는 **색인만** 갖는다 |
| 노하우 보관 | `{{knowhow_archive_dir}}` | 정리 시 원문을 먼저 옮긴다(지우지 않는다) |

## 6. 검증 (방출 후 — SKILL.md 게이트④)
- 스킬 본문이 참조하는 **모든 `{{prefix}}-*` 에이전트명**이 `.claude/agents/` 에 실제 존재하는지 교차검증.
- ★ **역방향도 본다** — `.claude/agents/` 에 있는데 **어느 스킬도 안 부르는** 파일을 목록화한다.
  정방향만 보면 **호출 줄이 사라져도 통과한다**(파일은 남으므로). 실패가 아니라 **보고** 항목이다 —
  독립 실행용 자산일 수 있다.
- 매핑표의 도메인 수 == 생성된 implementer 수.
- `frontend_track=off` 면 방출물 어디에도 `web-implementer` 가 남지 않아야 한다(`grep -rn web-implementer` 0건). on 이면 `{{prefix}}-web-implementer.md` 존재.
- `code_boundary==package` 면 방출물의 공유기반 문구가 **인터뷰로 확정한 `{{shared_base}}`** 인지 확인한다 — 이 레포에 없는 경로(`core/`·`db/migrations/`)가 남아 있으면 실패.
- dispatch 의 `### Phase N` 헤딩 번호가 중복되지 않는지(`grep -n '^### Phase' | sort | uniq -d` 0건).
- dispatch `reference.md` 가 방출됐고, 본문의 📎 이름표마다 reference 에 같은 이름의 `##` 절이 있는지. 본문 `wc -l` 이 ~250 안팎인지.
- `conventions_location==shared` 면 `.claude/conventions.md` 존재 + 스킬·에이전트 참조 경로 일치.
- `e2e_track=on` 이면 `.claude/e2e-conventions.md` + E2E 스킬 3종 존재 + 3종이 모두 그 규약 경로를 참조.
- 남은 `{{...}}`·`<!-- IF/INSERT ... -->` 마커가 없는지(미치환 잔존물) 스캔.
- **빈 슬롯 보고**: 확인 못 해 비운 E2E 슬롯을 목록으로 제시한다("정보부족 — 첫 저작 시 확인"). 조용히 넘기지 않는다.
- ★ **검증 위임 슬롯이 실제로 실렸는지** — `{{qa_model}}`·`{{qa_invoke}}`·`{{qa_fallback}}`·`{{qa_fail_signal}}` 이
  **dispatch 와 (`has_build=on` 이면) build 방출물 안에 문자열로 존재**하는지 확인한다(`{{backfill_model}}` 은 backfill — 비웠으면 「비움 = … 과 동일」 문장). 인터뷰에서 받아 놓고 방출물에 안 실리면
  **다음 세션은 그 값을 모른다**(2026-09-16 실사고).
- ★ **노하우 구조** — `{{knowhow_dir}}`·`{{knowhow_archive_dir}}` 가 생성됐고,
  implementer/web-implementer/**qa-verifier** 방출물에 **`## 노하우 색인`·`## 노하우 — 상시` 섹션과 출력 `knowhow_read`** 가 있는지 확인한다.
  ☠️ 본체·스킬이 가리키는 `_knowhow/*.md` 가 **실재하는지**도 본다(쪼개기·개명 뒤 끊긴 참조 — SKILL Phase 5).
- ★ **병행 레인** (`parallel_lanes=on`) — SKILL Phase 5 의 「병행 레인 검증」(실재 · 실행 권한 · `bash -n` · 슬롯 실림 · `knowhow_dir_abs`·범위 줄 강제 · gitignore · 원본 고유값 누출).
  `off` 면 방출물 어디에도 `scripts/lanes`·`lane-merge` 가 없어야 한다(`grep -rn 'scripts/lanes' .claude/` 0건).
- ★ **에이전트 본체 줄 수** — 방출 직후 `wc -l` 로 센다. 온보딩 직후엔 노하우가 비어 있어 짧지만,
  **재온보딩이면 초과분을 게이트로 보고**한다(§재온보딩).

## 시험 범위 슬롯 (1.9.0 · build 는 1.10.0)

`{{test_scope_table}}` 은 **여러 방출물에 같은 글자로** 실린다 — dispatch(Phase 5.95) · build(Phase E.95 · has_build) · implementer · web-implementer · qa-verifier · conventions(shared) · 레인 지시 블록.
값은 한 번 정하고 전부에 같은 표를 넣는다(방출물마다 다르게 적지 않는다 — 두 벌이 갈린다). 모양:

```
| 갈래 | 검사 | 연관 시험 | 항상 묶음 | 전체 시험 |
|---|---|---|---|---|
| 백엔드 | `…lint && …typecheck` | `…related <바꾼 파일>` | `<경로들>` 또는 없음 | `…test` (N파일 · M건 · S초 실측) |
| 프론트 | … | … | … | … |
```

Phase 5 검증: 방출물마다 `{{test_scope_table}}` 이 치환됐는지 + **에이전트 자체검증·QA 실측 절에서 표 줄(`|` 로 시작)을 뺀 나머지에 전체 시험 명령이 남아 있지 않은지**를 grep 으로 본다(표 안의 「전체 시험」 칸은 정상이다).
