# conventions.md — {{project_name}} 구현 공통 규약 (전 도메인 에이전트 공통 참조)

모든 `{{prefix}}-d00N-implementer` 와 `{{prefix}}-qa-verifier` 는 구현/검증 전에 이 파일을 정독한다. 값·경계·명령을 여기서 단일 진실원으로 가져간다. **AI 임의 추정 금지.**

## 확정 기술 스택 (킥오프 + ADR — 재논의 금지)
{{tech_stack_table}}

## 코드 레이아웃
```
{{package_layout}}
```
- 도메인 code_root 경계 안에서만 작업한다.
<!-- IF code_boundary == package -->
- `core/`·`db/migrations/`·앱 진입점은 **공통** — 도메인 에이전트가 임의 수정 금지. 필요하면 notes_for_main 으로 요청(오케스트레이터가 조율).
<!-- ELSE -->
- 다른 서브모듈/서비스는 **경계 밖** — 임의 수정 금지. 필요하면 notes_for_main 으로 요청.
<!-- ENDIF code_boundary -->

{{frontend_stack_block}}

## 빌드·테스트·품질 명령
```bash
{{build_cmds}}
```
- red(실패)는 숨기지 말고 그대로 보고. 값·계약 불명확하면 **구현 멈추고** notes_for_main 에 질문.

<!-- IF has_build -->
## 작동 모드 (★ 구현 에이전트는 프롬프트로 어느 모드인지 판별)
같은 도메인 에이전트가 오케스트레이터에 따라 **두 모드**로 불린다. 프롬프트에 `change_detail` 이 있으면 수정 모드, 없으면 greenfield 모드다.

| | ① greenfield 빌드 | ② 수정(CO) |
|---|---|---|
| 오케스트레이터 | `{{prefix}}-build` | `{{prefix}}-dispatch` |
| **진실원** | 키트 `IMPLEMENTATION.md` (전량 정독) | 프롬프트 `change_detail` |
| 범위 입력 | `scope` | `change_detail` 이 곧 범위 |
| 키트 | 진실원 | 배경 참고 · SYNC 안 함 |
| 설계 반영 | 키트가 이미 최신 | 나중 배치 — `/{{prefix}}-design-backfill` |

- 수정 모드: `change_detail` 이 진실원 → 그 범위만 건드리고, 불명확하면 멈춰 질문(추정 금지).
<!-- ENDIF has_build -->

## 진실원·참조 우선순위
<!-- IF has_build -->
1. **키트 IMPLEMENTATION.md** = 빌드 순서·의존 그래프·CONST 값 표. (수정 모드에선 배경 참고 — 진실원은 `change_detail`.)
2. 타입별 요약 `.md`(코드 직역용) + `_raw/*.json`(원본).
3. CONST 값은 키트 CONST 표가 **단일 진실원** — enum/range/임계치 상상해서 하드코딩 금지.
<!-- ELSE -->
1. **`change_detail`**(CO 의 이 도메인 섹션) = 구현 진실원.
2. 기존 코드 관례 = 배경. LogiCraft ITEM 은 필요한 계약만 조회.
3. CONST/enum/임계치는 설계 근거 없이 상상해서 하드코딩 금지.
<!-- ENDIF has_build -->

## 절대 규칙
- **LogiCraft 쓰기 금지** — 구현은 코드만. 설계 변경 필요하면 notes_for_main 으로 올린다. 단 IMPREC 추적(`mark_implementation`)은 허용.
- 외부 엔드포인트/시크릿은 코드에 박지 않음 — config/env 경유. URL 하드코딩 금지.
- 커밋 안 함(오케스트레이터가 처리). 커밋금지 파일: {{commit_forbidden}}.

## 출력 규약 (구현 에이전트 — YAML 한 블록)
```yaml
implemented: {files: [...], summary: ...}
verification: {build: ..., tests: ..., lint: ..., acceptance: ...}
tracking: {imprec: ..., notes: ...}
notes_for_main: {needs_core_change: [...], info_gaps: [...], cross_domain: [...], follow_ups: [...]}
```
