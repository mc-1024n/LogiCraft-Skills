---
name: {{prefix}}-build
description: {{project_name}} 전용 greenfield 구현 오케스트레이터. 로컬 키트(docs/design/*/IMPLEMENTATION.md)를 진실원으로, 도메인별 구현 에이전트({{prefix}}-d00N-implementer)와 독립 QA({{prefix}}-qa-verifier)를 팀처럼 지휘한다. 사용자가 "구현하자", "이 도메인 만들어줘", "다음 계층 진행", "/{{prefix}}-build" 등 구현 진행을 요청하면 실행. 착수 범위는 사용자 확인 후 진행(AI 임의 진행 금지). 이 스킬은 오케스트레이션만 — 실제 코드는 도메인 에이전트, 검증은 QA 에이전트가 한다.
---

# {{prefix}}-build — {{project_name}} greenfield 구현 오케스트레이터

로컬 설계 키트를 진실원으로, 도메인 전용 에이전트 팀을 지휘해 시스템을 세운다.

## ★ 핵심 원칙

1. **키트가 진실원.** `docs/design/<slug>-<DOMAIN-ID>/IMPLEMENTATION.md` 가 곧 구현 지시다.
<!-- IF phase0_foundation -->
2. **공통 기반 선행.** 도메인들이 `core/`·`db/migrations/`·앱 진입점을 공유한다. 무작정 병렬로 띄우면 충돌 → **Phase 0(스키마+앱 골격)을 먼저 순차로** 세운 뒤 도메인 fan-out.
<!-- ENDIF phase0_foundation -->
<!-- IF dependency_layers -->
3. **의존 계층 순서.** 도메인 간 계약 의존이 있어 완전 병렬 불가 → 계층 순서로 라운드를 나눈다.
<!-- ENDIF dependency_layers -->
4. **독립 QA.** 구현 에이전트 self-verify 는 확증편향 → `{{prefix}}-qa-verifier` 로 실측 재검증, fail 시 재구현(최대 2라운드).
5. **오케스트레이션만.** 이 스킬은 직접 코드 안 짬. 상태는 `docs/design/BUILD-MASTER.md` 로 추적.

## 프로젝트 상수
```yaml
project_id: {{project_id}}
app_root: "{{code_base}}"
kit_root: "docs/design"
<!-- IF conventions_location == shared -->
conventions: "{{conventions_path}}"
<!-- ENDIF conventions_location -->
build_master: "docs/design/BUILD-MASTER.md"
```

## 도메인 ↔ code_root ↔ 키트 ↔ 에이전트 매핑표 (라우팅 진실원)
{{domain_mapping_table}}

<!-- INSERT _switched/layers.section.md IF dependency_layers -->

## 파이프라인

### Phase A — 착수 범위 확인  🚦게이트①
사용자 요청을 **어느 <!-- IF dependency_layers -->계층/<!-- ENDIF dependency_layers -->도메인까지** 로 정리. 현재 BUILD-MASTER 상태 확인(어디까지 됐나).
확인: *"이번 라운드: [범위]. 이대로 진행할까요?"*
<!-- INSERT _switched/phase0.section.md IF phase0_foundation -->

### Phase C — 도메인 fan-out
해당 <!-- IF dependency_layers -->계층의 <!-- ENDIF dependency_layers -->도메인마다 **한 메시지에서 병렬로** `{{prefix}}-d00N-implementer` 를 띄운다.
```yaml
project_id: {{project_id}}
domain_id: DOMAIN-00N
code_root: "<이 도메인 code_root>"
kit_root:  "<이 도메인 키트 경로>"     # IMPLEMENTATION.md = 진실원
<!-- IF conventions_location == shared -->
conventions: "<repo>/{{conventions_path}}"
<!-- ENDIF conventions_location -->
scope: | <이번 라운드 이 도메인 구현 범위. 명시 안 하면 키트 빌드순서대로 전량>
```
계약 의존(상류⊃하류)이면 상류 회수 후 하류(라운드 분리).

### Phase D — 회수
각 에이전트 출력 YAML(implemented/verification/tracking/notes_for_main) 취합. red 그대로.

### Phase E — 독립 QA ({{prefix}}-qa-verifier)
회수 직후 대상마다 QA 병렬. 구현이 red 면 QA 생략, 바로 재구현.
프롬프트: domain_id·code_root·kit_root<!-- IF conventions_location == shared -->·conventions<!-- ENDIF conventions_location -->·implemented·claimed_verification.
- `pass`/`pass_with_notes` → Phase F.
- `fail` → 해당 구현 에이전트에 issues+fix_hint 담아 재호출(최대 2라운드), 그래도 fail 이면 red 보고.
- `blocked`(실측 불가) → 정직 보고, 런타임 검증 잔여.

### Phase E.5 — 노하우 반영 (에이전트 파일 갱신)  🚦게이트
회수한 각 에이전트 출력의 `notes_for_main.learned` 를 본다. **전부 비어있으면 건너뛴다**(보고에 "노하우 신규 없음").
- 있으면 항목별로 **사용자에게 제시** — 어느 에이전트의 `## 노하우` 에 무엇을 추가할지 + 근거(evidence)·재발조건.
- 동의한 항목만 해당 `{{prefix}}-d00N-implementer`(프론트는 `{{prefix}}-web-implementer`) 파일의 `## 노하우` 섹션에 **append**. 기존 항목 삭제·재작성 금지(축적이지 교체가 아님).
- **QA(Phase E)에서 fail → 재구현으로 드러난 함정도 후보**로 함께 올린다.
<!-- IF dependency_layers -->
- **계층 라운드마다 수행한다** — 앞 계층에서 얻은 노하우가 다음 계층 구현에 실제로 쓰이게 하려면 라운드 종료 시점에 반영해야 한다(전량 빌드 후 몰아서 = 늦음).
<!-- ENDIF dependency_layers -->
- 근거(evidence) 없는 항목은 반영하지 않는다(AI 추정 금지). 키트 설계에서 온 제약은 노하우가 아니라 특화지침·backfill 대상이다.

### Phase F — 마스터 갱신 · 커밋
- **BUILD-MASTER.md 갱신**: 도메인별 <!-- IF dependency_layers -->계층·<!-- ENDIF dependency_layers -->상태(⬜미착수/🔨구현/✅QA통과/⚠️잔여), 커밋 여부.
- 실패·red 그대로 노출. notes 의 cross_domain·info_gaps 는 다음 액션.
- **커밋은 자동 안 함** — 사용자에게 물음.<!-- IF commit_strategy == submodule --> 서브모듈 2단 커밋.<!-- ENDIF commit_strategy -->

## 게이트 요약
1. Phase A — 착수 범위
2. Phase E.5 — 노하우 반영 확인 (`learned` 가 있을 때만<!-- IF dependency_layers -->, 계층 라운드마다<!-- ENDIF dependency_layers -->)
3. QA fail 2라운드 초과 / 미매핑 / breaking / core 변경 요청 → 그때 확인
그 외 자동.

## 원칙
- **오케스트레이션만** — 직접 코드 안 짬<!-- IF phase0_foundation -->(Phase 0 공통 기반은 예외적으로 메인이)<!-- ENDIF phase0_foundation -->.
- **키트가 진실원** — 도메인 에이전트는 자기 IMPLEMENTATION.md 대로. CONST 값 추정 금지.
<!-- IF dependency_layers -->
- **계층 순서 준수** — 앞 계층 QA pass 전 다음 계층 금지(기반 미완이면 재작업).
<!-- ENDIF dependency_layers -->
- **정직 회수** — QA 결과 가감 없이. red 숨김 금지.
- **노하우 축적** — 에이전트가 `notes_for_main.learned` 로 올린 새 함정/패턴을 **Phase E.5 에서** 해당 `{{prefix}}-d00N-implementer` 노하우 섹션에 append(사용자 동의 하에). 에이전트는 자기 파일을 직접 못 고친다 — 반영 책임은 메인에 있다.
