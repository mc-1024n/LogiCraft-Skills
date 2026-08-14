# _TEMPLATING.md — 템플릿 조립 문법 규약

`mc-logi-build-onboard` 가 `_invariant/*`·`_switched/*` 를 읽어 실제 스킬·에이전트로 방출할 때 쓰는 치환 문법이다. 조립기(SKILL.md 파이프라인 §조립)는 이 규약대로 처리한다.

## 1. 슬롯 치환 (값 채움) — `{{slot}}`
- `{{slot_name}}` → 리터럴 문자열로 치환. Discovery/인터뷰가 값 제공(toggles.md §5).
- 값이 없으면 채우지 말고 **"정보부족"으로 남기고 보고**(placeholder·가짜값 금지).

**공통 슬롯**
| 슬롯 | 의미 |
|---|---|
| `{{prefix}}` | 스킬·에이전트 접두사 (`graphrag`, `klid`) |
| `{{PrefixTitle}}` | 사람용 제목 표기 (`Graph-RAG`, `KLID`) |
| `{{project_id}}` | LogiCraft project UUID |
| `{{project_name}}` | "Graph-RAG System" |
| `{{code_base}}` | 코드 루트 (monolith `src/<pkg>` / submodule `<서브모듈 루트 폴더>`) |
| `{{change_orders_path}}` | `.claude/change-orders/` |
| `{{conventions_path}}` | `.claude/conventions.md` (shared 일 때 고정) |
| `{{domain_mapping_table}}` | 도메인↔code_root↔에이전트 매핑표 전체 |
| `{{build_cmds}}` | 빌드·테스트·린트 명령 |
| `{{commit_forbidden}}` | 커밋금지 파일 목록 |

**도메인별 슬롯** (implementer 는 도메인마다 1회 인스턴스화)
| 슬롯 | 의미 |
|---|---|
| `{{domain_id}}` | `DOMAIN-001` |
| `{{domain_name}}` | "데이터 수집·적재" |
| `{{domain_short}}` | "D001" |
| `{{domain_agent_name}}` | `graphrag-d001-implementer` |
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
| `{{frontend_stack_short}}` | 프론트 스택 짧은 표기 (Next.js / React SPA) — 제목·description 용 | repo(package.json) |
| `{{frontend_build_cmds}}` | 프론트 빌드·테스트·린트 명령 (`pnpm lint && pnpm test && pnpm build`) | repo(package.json scripts) |
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

**스위치 이름**(toggles.md §1): `has_build` · `phase0_foundation` · `dependency_layers` · `work_claim` · `commit_strategy`(single|submodule) · `agent_mode`(dual|modify) · `conventions_location`(shared|embedded) · `code_boundary`(package|submodule|repo) · `e2e_track` · `e2e_design_link`(logicraft|local) · `e2e_auth`(none|bypass|bypass_and_verify) · `e2e_selector`(testid|role) · `e2e_account_strategy`(self_provision|seed|mixed)

## 3. 조각 삽입 — `<!-- INSERT ... -->`
```
```
- 스위치가 on 이면 그 파일 내용을 이 위치에 끼워넣고(그 파일도 슬롯 치환 대상), off 면 마커 삭제.
- `IF` 없이 쓰면 무조건 삽입(불변 조각 재사용).

## 4. 도메인 반복 — implementer.tmpl.md
`implementer.tmpl.md` 는 **매핑표의 도메인마다 1회** 인스턴스화한다(도메인별 슬롯 치환). 프론트 트랙이 있으면 `{{prefix}}-web-implementer` 도 별도 생성(웹 전용 변형은 조립기가 프론트 슬롯으로).

## 5. 방출 위치
| 템플릿 | 방출 경로 |
|---|---|
| dispatch.SKILL.tmpl.md | `.claude/skills/{{prefix}}-dispatch/SKILL.md` |
| backfill.SKILL.tmpl.md | `.claude/skills/{{prefix}}-design-backfill/SKILL.md` |
| _switched/build.SKILL.tmpl.md (IF has_build) | `.claude/skills/{{prefix}}-build/SKILL.md` |
| _switched/conventions.tmpl.md (IF shared) | `.claude/conventions.md` |
| implementer.tmpl.md ×N | `.claude/agents/{{domain_agent_name}}.md` |
| qa-verifier.tmpl.md | `.claude/agents/{{prefix}}-qa-verifier.md` |
| _switched/web-implementer.tmpl.md (IF 프론트 트랙) | `.claude/agents/{{prefix}}-web-implementer.md` |
| _switched/e2e-conventions.tmpl.md (IF e2e_track) | `.claude/e2e-conventions.md` |
| _switched/e2e-author.SKILL.tmpl.md (IF e2e_track) | `.claude/skills/{{prefix}}-e2e-author/SKILL.md` |
| _switched/e2e-run.SKILL.tmpl.md (IF e2e_track) | `.claude/skills/{{prefix}}-e2e-run/SKILL.md` |
| _switched/e2e-verify.SKILL.tmpl.md (IF e2e_track) | `.claude/skills/{{prefix}}-e2e-verify/SKILL.md` |

## 6. 검증 (방출 후 — 게이트②)
- 스킬 본문이 참조하는 **모든 `{{prefix}}-*` 에이전트명**이 `.claude/agents/` 에 실제 존재하는지 교차검증.
- 매핑표의 도메인 수 == 생성된 implementer 수.
- `conventions_location==shared` 면 `.claude/conventions.md` 존재 + 스킬·에이전트 참조 경로 일치.
- `e2e_track=on` 이면 `.claude/e2e-conventions.md` + E2E 스킬 3종 존재 + 3종이 모두 그 규약 경로를 참조.
- 남은 `{{...}}`·`<!-- IF/INSERT ... -->` 마커가 없는지(미치환 잔존물) 스캔.
- **빈 슬롯 보고**: 확인 못 해 비운 E2E 슬롯을 목록으로 제시한다("정보부족 — 첫 저작 시 확인"). 조용히 넘기지 않는다.
