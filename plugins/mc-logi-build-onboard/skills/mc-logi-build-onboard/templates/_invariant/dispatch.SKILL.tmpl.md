---
name: {{prefix}}-dispatch
description: {{project_name}} 전용 수정 오케스트레이터. 이미 구현된 코드를 테스트·수정 반복 단계에서 고칠 때 쓴다. 자유서술 수정요청을 받아 ① 의도 파악 → ② 변경지시서(Change Order) 파일 작성 + 마스터 등록(LogiCraft 설계·로컬 키트는 즉시 반영 안 함 — 나중 배치) → ③ 영향 도메인 판정 → ④ 확인 게이트 → ⑤ 도메인별 구현 에이전트({{prefix}}-d00N-implementer)·프론트({{prefix}}-web-implementer)로 병렬 fan-out(구현+self검증+추적, 키트 SYNC 없이 메인이 change_detail 직접 전달) → ⑥ 독립 QA({{prefix}}-qa-verifier — self검증 불신, 실측 재실행+수용기준 재대조+어드버서리얼, fail 시 재구현) → ⑦ 회수·마스터 갱신. 사용자가 "이거 고쳐줘", "이 수정사항 반영해줘", "테스트하다 이거 바꿔야 해", "/{{prefix}}-dispatch" 등 기존 코드 수정을 요청하면 실행. 변경지시·영향범위는 사용자 확인 후 진행(AI 임의 진행 금지).<!-- IF has_build --> 미착수 도메인의 최초 구현은 이 스킬이 아니라 {{prefix}}-build.<!-- ENDIF has_build -->
---

# {{prefix}}-dispatch — {{project_name}} 수정 오케스트레이터

자유서술 수정요청 하나를 받아, **변경지시서(Change Order)를 파일로 남기고 → 영향 도메인 코드를 도메인 전용 에이전트로 구현**하는 프로젝트 전용 디스패처.

## ★ 핵심 원칙

1. **LogiCraft 설계·로컬 키트는 즉시 반영하지 않는다.** 수정사항을 **변경지시서(CO) 파일**(`{{change_orders_path}}CO-NNN-*.md`)에 자세히 기술만 하고, LogiCraft ITEM backfill 은 **나중에 배치**(`/{{prefix}}-design-backfill`)로 한다. 이 스킬은 설계·키트를 안 건드린다.
2. **적용 상태는 마스터 파일로 관리** — `{{change_orders_path}}MASTER.md` 표에 CO 별·도메인별 구현/설계반영 상태.
3. **구현 에이전트는 로컬 키트를 SYNC 하지 않는다.** 메인이 CO 의 해당 도메인 변경 상세(`change_detail`)를 프롬프트로 직접 내려준다 → 에이전트는 **수정 모드**로 동작(`change_detail` 이 진실원).
<!-- IF code_boundary == package -->
4. **공유기반 주의** — 도메인들이 `core/`·`db/migrations/`·앱 진입점을 **공유**한다. 변경이 스키마/공유기반을 건드리면 도메인 에이전트가 못 고침 → **메인이 먼저 처리**(Phase 3.5) 후 도메인 fan-out.
<!-- ENDIF code_boundary -->
5. **오케스트레이션만.** 이 스킬은 직접 코드/ITEM 안 짬. 구현은 도메인 에이전트, QA 는 `{{prefix}}-qa-verifier`, 설계 backfill 은 별도 스킬.

## 프로젝트 상수
```yaml
project_id: {{project_id}}
code_base: "{{code_base}}"
change_orders: "{{change_orders_path}}"
<!-- IF conventions_location == shared -->
conventions: "{{conventions_path}}"
<!-- ENDIF conventions_location -->
```

## 도메인 ↔ code_root ↔ 구현 에이전트 매핑표 (라우팅 진실원)
{{domain_mapping_table}}

> - 매핑표에 없는 대상이 나오면 **임의 진행 말고 사용자에게 code_root·에이전트 확인**.
> - 백엔드 변경이 화면까지 미치면 백엔드 도메인 에이전트 + `{{prefix}}-web-implementer` **둘 다** fan-out. 프론트는 백엔드 응답 계약 소비만 → **백엔드 먼저, 프론트 뒤**.
> - 계약 의존(상류⊃하류)이면 상류 도메인 회수 후 하류(라운드 분리).
<!-- IF code_boundary == package -->
> - 공유 기반(`core/`·`db/migrations/`·앱 진입점)은 도메인 소속이 아니다 — **메인 직접**(Phase 3.5).
<!-- ENDIF code_boundary -->

## 파이프라인

### Phase 1 — 의도 파악  🚦게이트①
자유서술 요청을 **무엇을 / 왜 / 어느 범위**로 정리. 버그면 근본원인까지 코드에서 확인(대상 파일 grep/read). 애매하면 되묻는다.
확인: *"요청 이해: [정리]. 변경지시서로 정리하고 구현까지 진행할까요?"*

### Phase 2 — 변경지시서(CO) 작성  (LogiCraft 대신)
1. **영향 도메인 판정** — 코드 기반. grep(traceability 태그는 `grep -ri '@design'` — 기본형 `@design` 과 어노테이션 `@DesignRef` 를 한 번에 잡는다 ·API 경로·`SCREEN-`/`API-`) + 도메인 매핑표 + 도메인 에이전트 특화지식. 한 변경이 여러 도메인·백/프론트에 걸치면 각각 분해.
<!-- IF code_boundary == package -->
   - ★ **공유기반 영향 체크**: 변경이 `core/`·`db/migrations/`·앱 진입점을 건드리는지 판정. 건드리면 CO §3 에 명시하고 **메인 선처리** 대상으로 표시.
<!-- ENDIF code_boundary -->
2. **CO 파일 작성** — `{{change_orders_path}}_TEMPLATE.md` 골격으로 `{{change_orders_path}}CO-NNN-{slug}.md`. CO 번호 = MASTER 표 최하단 +1.
   - ★ **도구 모르는 사람도 이것만 읽고 이해**하도록 자세히. §3 "도메인별 변경 상세"는 각 도메인 에이전트가 받아 구현할 만큼 구체적으로(대상 파일/심볼·변경·불변·주의).
   - §6 "관련 설계 ITEM"에 나중에 backfill 할 예상 ITEM 기록(지금 반영 안 함).
3. **MASTER 등록** — `MASTER.md` 표에 행 추가(상태 📝, 대상 도메인, 생성일, 설계반영 ⏳).

### Phase 3 — 영향범위 확인  🚦게이트②
<!-- INSERT _switched/work_claim.recon.md IF work_claim -->
```
변경지시서 작성: CO-NNN (제목)
<!-- IF code_boundary == package -->공유기반 선처리 필요: (있으면) core/db 마이그레이션 X → 메인이 먼저
<!-- ENDIF code_boundary -->영향 백엔드: DOMAIN-00N → {{prefix}}-d00N-implementer
영향 프론트: SCREEN-NNN → {{prefix}}-web-implementer
권장 순서: (공유기반 →) 백엔드 → 프론트
이대로 진행할까요?
```
승인 후 Phase 3.5~. (판정 불명확·미매핑 도메인·breaking 변경·프론트 구현 여부는 그때 되묻는다.)
<!-- INSERT _switched/work_claim.declare.md IF work_claim -->
<!-- IF code_boundary == package -->

### Phase 3.5 — 공유기반 선처리 (해당 시, 메인 직접)
CO 가 스키마·`core/`·앱 진입점을 건드리면 **도메인 fan-out 전에 메인이 먼저** 처리한다(마이그레이션 작성·적용, core 시그니처 변경 등). 도메인 에이전트는 이 결과를 전제로 구현. 여기서 실패하면 도메인 구현 보류.
<!-- ENDIF code_boundary -->

### Phase 4 — 구현 fan-out
영향 대상마다 **한 메시지에서 병렬로** 해당 도메인 에이전트를 띄운다. **키트 SYNC 안 함** — CO 의 해당 도메인 상세를 프롬프트로 직접 전달(=수정 모드). 백/프론트 계약 의존이면 백엔드 회수 후 프론트(2 라운드).
```yaml
project_id: {{project_id}}
domain_id: DOMAIN-00N              # (프론트는 화면 소속 도메인)
code_root: "<이 도메인 code_root>"   # (프론트는 웹 code_root)
<!-- IF conventions_location == shared -->
conventions: "<repo>/{{conventions_path}}"
<!-- ENDIF conventions_location -->
change_order: "<repo>/{{change_orders_path}}CO-NNN-{slug}.md"   # 참조용
change_detail: |                    # ★ 구현 진실원 (수정 모드)
  <CO §3 의 이 도메인 섹션 전문 — 대상 파일·변경·불변·주의·수용기준>
target_hint: | <알면 대상 모듈/클래스/함수/화면. 모르면 생략>
```

### Phase 5 — 회수
각 에이전트 출력 YAML(implemented/verification/tracking/notes_for_main) 취합. red 그대로.<!-- IF code_boundary == package --> notes 의 needs_core_change 가 뒤늦게 나오면 Phase 3.5 로 되돌아감.<!-- ENDIF code_boundary -->

### Phase 5.5 — 독립 QA 검증 ({{prefix}}-qa-verifier)
회수 직후 대상마다 `{{prefix}}-qa-verifier` 병렬. 구현이 red 면 QA 생략, 바로 재구현.
```yaml
project_id: {{project_id}}
domain_id: DOMAIN-00N
code_root: "…/<이 도메인 code_root 또는 웹>"
<!-- IF conventions_location == shared -->
conventions: "<repo>/{{conventions_path}}"
<!-- ENDIF conventions_location -->
change_order: "…/{{change_orders_path}}CO-NNN-*.md"
change_detail: | <해당 도메인 변경 상세 — 수용기준·불변>
implemented: | <구현 에이전트가 보고한 변경 파일·요지>
claimed_verification: | <구현 에이전트가 주장한 결과 — QA 가 실측 대조>
```
- `pass`/`pass_with_notes` → Phase 6.
- `fail` → 해당 구현 에이전트에 issues+fix_hint 담아 재호출(최대 2라운드), 그래도 fail 이면 red 보고.
- `blocked`(실측 불가) → 정직 보고, 런타임 검증 잔여.
> 규모/리스크가 아주 낮으면(오타·문구 1줄) QA 생략 가능하나 **기본은 실행**.

### Phase 5.9 — 노하우 반영 (에이전트 파일 갱신)  🚦게이트
회수한 각 에이전트 출력의 `notes_for_main.learned` 를 본다. **전부 비어있으면 건너뛴다**(보고에 "노하우 신규 없음").
- 있으면 항목별로 **사용자에게 제시** — 어느 에이전트의 `## 노하우` 에 무엇을 추가할지 + 근거(evidence)·재발조건.
- 동의한 항목만 해당 `{{prefix}}-d00N-implementer`(프론트는 `{{prefix}}-web-implementer`) 파일의 `## 노하우` 섹션에 **append**. 기존 항목 삭제·재작성 금지(축적이지 교체가 아님).
- **QA(Phase 5.5)에서 fail → 재구현으로 드러난 함정도 후보**로 함께 올린다. 같은 지적이 CO 를 넘어 반복되면 노하우 1순위.
- 근거(evidence) 없는 항목은 반영하지 않는다(AI 추정 금지). 동의 못 받은 항목은 버리지 말고 CO §7 구현 로그에 남긴다.
- 도메인 특화 지침(설계 근거)과 혼동 금지 — 여기 쌓는 건 **구현하며 얻은 경험**이고, 설계에서 온 제약은 backfill 대상이다.

### Phase 6 — 마스터 갱신 · 커밋<!-- IF work_claim --> · claim heartbeat<!-- ENDIF work_claim -->
- **MASTER.md 갱신**: 해당 CO 의 `구현 상태` 도메인별 ✅(QA pass 후) + `커밋`. CO 파일 §7 구현 로그도 갱신.
<!-- INSERT _switched/work_claim.heartbeat.md IF work_claim -->
- **실패·red 그대로 노출.** notes 의 추가 영향 도메인·정보 부족은 다음 액션.
- **커밋은 자동 안 함** — 사용자에게 물음.<!-- IF commit_strategy == submodule --> 서브모듈 2단 커밋(서브모듈 → 상위 포인터).<!-- ENDIF commit_strategy --> 커밋금지 파일({{commit_forbidden}}) 제외.

### [별도 배치] LogiCraft 설계 반영 → `/{{prefix}}-design-backfill`
이 스킬은 설계·키트를 건드리지 않는다. 나중에 `/{{prefix}}-design-backfill` 실행 시, MASTER 에서 **설계반영 대기(⏳)** CO 들을 모아 각 CO §6·본문·커밋 코드를 근거로 LogiCraft ITEM 을 retro-align(코드 진실원) — 실제 수정·cascade 는 `mc-logi-update` 에 위임하고, 완료 시 MASTER 의 `설계반영`을 🎨로 닫는다.

## 게이트 요약
1. Phase 1 — 의도 이해
2. Phase 3 — CO + 영향범위 확인<!-- IF work_claim --> (+ 협업 정찰, 겹치면 확인)<!-- ENDIF work_claim -->
3. Phase 5.9 — 노하우 반영 확인 (`learned` 가 있을 때만)
그 외 자동. 불명확·미매핑·breaking·<!-- IF code_boundary == package -->core 변경·<!-- ENDIF code_boundary -->프론트 구현 여부는 그때 확인.

## 원칙
- **오케스트레이션만** — 직접 코드/ITEM 안 고침<!-- IF code_boundary == package -->(공유기반 선처리는 예외적으로 메인이)<!-- ENDIF code_boundary -->. 구현은 도메인 에이전트, 설계 backfill 은 별도.
- **CO 가 진실원** — 구현 에이전트는 메인이 준 change_detail 대로. 키트 SYNC 안 함.
- **AI 추정 금지** — 도메인 판정·변경 값 임의 확정 안 함. 근거는 grep·매핑표·도메인 에이전트 지식, 애매하면 사용자.
- **정직 회수** — 에이전트/QA 결과 가감 없이. red 숨김 금지.
- **도메인 노하우 축적** — 에이전트가 `notes_for_main.learned` 로 올린 새 함정·패턴을 **Phase 5.9 에서** 해당 `{{prefix}}-d00N-implementer` 노하우 섹션에 append(사용자 동의 하에). 에이전트는 자기 파일을 직접 못 고친다 — 반영 책임은 메인에 있다.
<!-- IF work_claim -->
- **협업 점유는 advisory** — work_claim 은 경고만, 구현을 막지 않음. 생성 실패·MCP 다운이어도 구현은 진행하고 "점유 미선언"만 보고. MASTER 를 대체하지 않음.
<!-- ENDIF work_claim -->
