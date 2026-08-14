---
name: {{prefix}}-design-backfill
description: {{project_name}} 변경지시서(Change Order) 기반 LogiCraft 설계 backfill 스킬. {{prefix}}-dispatch 가 코드를 먼저 구현하고 미룬 "설계 반영"을 나중에 배치로 처리한다. {{change_orders_path}}MASTER.md 에서 설계반영 대기(⏳)인 CO 를 모아(또는 특정 CO 지정), 각 CO 의 §6(관련 설계 ITEM)·변경 내용·실제 커밋된 코드를 근거로 LogiCraft ITEM 을 실제 구현에 맞춰 retro-align 한다. 실제 ITEM 수정·cascade 는 mc-logi-update 에 위임하고, 이 스킬은 CO→입력 변환 + 게이트 + MASTER 상태(🎨) 갱신만 담당. 사용자가 "CO 설계 반영해줘", "backfill 해줘", "/{{prefix}}-design-backfill" 이라고 하면 실행. AI 추정 금지 — CO·코드에 근거 없는 값은 넣지 않는다(애매하면 사용자).
---

# {{prefix}}-design-backfill — CO 기반 LogiCraft 설계 backfill

`{{prefix}}-dispatch` 는 **코드 구현을 먼저** 하고 LogiCraft 설계 반영을 **나중 배치**로 미룬다(변경지시서 CO 파일이 1차 진실원). 이 스킬이 그 미뤄둔 배치를 처리한다 — **이미 구현·커밋·QA 통과된 코드에 맞춰 LogiCraft 설계 ITEM 을 retro-align** 하고, MASTER 의 설계반영 상태를 🎨로 닫는다.

## ★ 핵심 원칙

1. **코드가 진실원(retro-align)** — 이 시점엔 코드가 이미 구현·커밋·QA 통과 상태다. 설계를 코드에 **맞춘다**(설계→코드가 아니라 코드→설계). ⚠️ "retro-align"은 개념 이름일 뿐 mc-logi-update 의 형식 모드·파라미터가 아니다 — 코드 우선 정합은 **edit_intent/edit_context 문구로** 전달한다("코드가 이미 이렇게 구현·커밋됨 → 설계를 이 코드에 맞춰 정정하라").
2. **실제 수정은 mc-logi-update 위임** — 이 스킬은 LogiCraft ITEM 을 직접 고치지 않는다. CO 를 mc-logi-update 입력(target_id·edit_intent·edit_context)으로 변환해 넘기고, cascade·specialist·검증은 그 스킬이 처리한다.
3. **CO §6 + 본문 + 실제 코드가 근거** — 무엇을 어떻게 고칠지는 CO 파일의 §6·§2~3·§7(커밋)과, 필요하면 그 커밋의 실제 코드에서 확인. **AI 추정 금지**.
4. **MASTER 가 진척 진실원** — 처리 대상·완료 상태는 `{{change_orders_path}}MASTER.md` 의 `설계반영` 열(⏳ 대기 → 🎨 완료)로 추적.
5. **게이트** — 실제 mc-logi-update 실행 전에 backfill 계획(CO별 어떤 ITEM 을 어떻게)을 사용자에게 확인받는다.
<!-- IF work_claim -->
6. **work_claim drift 해소 = backfill 의 종착** — dispatch 는 CO 착수 시 advisory `work_claim` 을 `design_pending=true` 로 열어두고 닫지 않는다. 그 claim 을 닫는 건 **이 스킬의 책임**이다 — backfill 완료 시 `update_work_claim(design_pending=false)` → `close_work_claim` 을 **MASTER 🎨 전환과 동시에** 처리해 크로스세션 drift 신호를 닫는다.
<!-- ENDIF work_claim -->

## 프로젝트 상수
```yaml
project_id: {{project_id}}
change_orders: "{{change_orders_path}}"
```

## 파이프라인

### Phase 0 — 대상 CO 선정
1. `MASTER.md` 를 읽어 `설계반영` 열이 **⏳ 대기**인 CO 행을 모은다.
   - 인자로 특정 CO 지정되면 그것만. 없으면 **⏳ 대기 전체**. 이미 🎨·—인 CO 는 제외.
2. 각 대상 CO 파일을 읽어 backfill 재료를 뽑는다:
   - **§6 관련 설계 ITEM** — 반영할 예상 ITEM 목록 + 판단 근거(1차 입력).
   - **§2 변경 요지 · §3 도메인별 변경 상세** — 무엇이 어떻게 바뀌었나.
   - **§7 구현 로그의 커밋 해시** — 실제 구현된 코드. §6 이 애매하면 이 커밋 코드를 실측해 정확한 계약 확인.
<!-- IF work_claim -->
   - **work_claim `claim_id`** — CO 상단 표 또는 §7 에 기록된 advisory claim ID. Phase 3 에서 이 claim 을 닫는다. 없거나 만료됐으면 close 생략.
<!-- ENDIF work_claim -->
3. 대상 0건이면 "설계반영 대기 CO 없음" 보고 후 종료.

### Phase 1 — backfill 계획  🚦게이트
CO별로 **어떤 ITEM 을 어떻게 고칠지** 초안을 만들어 제시. 형식:
```
CO-NNN (제목) — 설계반영 대기
  · API-NNN: 응답 스키마를 flat → envelope 로 정정
    (근거: CO-NNN §6 + 실제 코드. 현 설계 vN 은 코드와 drift)
```
- **retro-align 명시**: "코드가 이미 이러하므로 설계를 이에 맞춘다"를 근거로.
- **불확실 항목 분리**: CO §6 에 있으나 근거 약한 것은 "확인 필요"로 빼서 사용자에게(추정 반영 금지).
- 여러 CO 가 같은 ITEM 을 건드리면 **최신 코드 상태로 한 번에** 정합.

**승인 후** Phase 2.

### Phase 2 — mc-logi-update 위임
승인된 계획대로 mc-logi-update 호출. CO(또는 같은 ITEM 공유 CO 묶음) 단위로.

**★ 호출 방식**: `Skill(skill="mc-logi-update", args="<입력>")` — 그 스킬이 내부에서 logi-update-specialist 를 띄우고 **cascade LOOP** 를 돈다. ⚠️ **logi-update-specialist 를 Task/Agent 로 직접 띄우지 말 것**(단건 처리라 cascade 안 돎). backfill 은 cascade 가 핵심 → 반드시 오케스트레이터 경유.

입력(자연어 args):
```
프로젝트: {{project_name}} (project_id {{project_id}})
대상 (ITEM + item_type):        # CO §6 의 ID prefix 로 타입 확정 → 명시
  - API-NNN   (api_endpoint)
  - ERD-NNN   (erd)
  - AC-NNN    (acceptance)
의도(edit_intent): 코드 우선 정합 — 코드가 이미 구현·커밋됨, 설계를 그 코드에 맞춤
edit_context: |
  <CO §2/§3 변경 요지 + §6 근거 + §7 커밋 해시. "코드 먼저 구현됨, 설계를 그 코드에 정합하라" 명시.>
```

★★ **말단(leaf) ITEM 누락 방지 — 반드시 위임 프롬프트에 명시** ★★
mc-logi-update 는 cascade 시 **말단 항목을 종종 빠뜨린다**(AC·SCREEN·SEQ·CDIAG·CMP 등 leaf 는 비가시). 위임 프롬프트에 명시:
- *"cascade 를 **말단까지 완주**하라. 바뀐 상위 ITEM 마다 `analyze_impact` 로 하위 영향을 조회해 **AC·SCREEN·SEQ·CDIAG·CMP 등 leaf 를 빠짐없이 큐에 넣고** 정합하라. leaf 를 '변경 없음'으로 단정 말고 실제 대조 후 판정."*
- CO §6 에 예상 하위 ITEM 이 있으면 그 ID 를 **명시적 cascade 대상으로 함께** 넘긴다.

회수: 바뀐 ITEM 목록(id·version·요지) 회수. 실패·미처리는 그대로 노출.

### Phase 2.5 — 말단 반영 검증 (누락 잡기)
mc-logi-update 회수 후, **상위 ITEM 의 하위 leaf 가 실제 정합됐는지 직접 검증**(위임만 믿지 않음):
- 바뀐 상위 ITEM 마다 `analyze_impact`/`get_neighbors`(하위)로 연결된 **AC·SCREEN·SEQ·CDIAG·CMP** 나열 → 각각 이번 라운드에 정합됐는지 확인.
- CO §6 의 예상 하위 ITEM 이 회수 목록에 없으면 = **누락** → 그 ITEM 대상 재위임. 누락 없을 때까지 반복. 남으면 "leaf 미반영 N건"으로 정직 보고(🎨 대신 부분 상태).

### Phase 3 — MASTER · CO 상태 갱신<!-- IF work_claim --> + work_claim 종결<!-- ENDIF work_claim -->
- **MASTER.md**: 성공 backfill 된 CO 의 `설계반영` 열을 **🎨 (반영 ITEM 요약)**. 부분 반영이면 🎨/⏳ 혼합으로 정직히.
- **CO 파일**: 상단 표 🎨, §6 아래 "반영 완료: <ITEM 목록·version>" 추가.
<!-- IF work_claim -->
- **★ work_claim 종결(drift 신호 닫기)** — CO 를 🎨로 완주한 경우에만, Phase 0 에서 수집한 `claim_id` 로: ① `update_work_claim(claim_id, design_pending=false)` ② `close_work_claim(claim_id, result="설계 backfill 완료 — CO-NNN")`. **MASTER 🎨 전환과 동시에** 처리. 부분 반영이면 close 하지 않음(design_pending=true 유지). 만료/claim_id 없으면 close 생략, MASTER 🎨 만.
<!-- ENDIF work_claim -->
- **보고**: CO별 반영 ITEM(id·version)·cascade 건수·미처리/확인필요를 표로.

## 게이트 요약
1. Phase 1 — backfill 계획 승인 (실제 설계 수정 전)
그 외는 mc-logi-update 정책(batch 자동)을 따름. 근거 약한 항목·breaking 변경은 그때 확인.

## 원칙
- **접착제 역할만** — 직접 LogiCraft ITEM 안 고침(mc-logi-update 위임).
- **retro-align** — 코드가 진실원. 설계를 코드에 맞춘다.
- **★ 말단 leaf 빠뜨리지 않기** — cascade 는 AC·SCREEN·SEQ·CDIAG·CMP leaf 를 자주 누락. 위임 시 "말단까지 완주" 명시(Phase 2), 회수 후 직접 대조(Phase 2.5). leaf 미반영으로 🎨 금지.
- **AI 추정 금지** — CO·코드 근거 없는 ITEM·값 반영 금지.
- **MASTER 를 닫는다** — 처리 후 반드시 MASTER 갱신(leaf 까지 완주해야 🎨, 부분이면 정직).
<!-- IF work_claim -->
- **work_claim 도 닫는다** — MASTER 🎨 와 **동시에** 그 CO 의 claim 을 update(design_pending=false)+close. dispatch 가 연 drift claim 의 종결 책임은 이 스킬에.
<!-- ENDIF work_claim -->
- **CO 는 안 지운다** — backfill 후에도 CO 파일은 이력으로 보존(상태만 🎨).

## 에러·중단
| 상황 | 대응 |
|---|---|
| ⏳ 대기 CO 0건 | "backfill 대상 없음" 보고 후 종료 |
| CO §6 근거 부족 | 그 항목은 "확인 필요"로 분리 → 사용자. 추정 반영 금지 |
| mc-logi-update 실패/보류 | 그대로 노출. 해당 CO 는 ⏳ 유지(부분 성공 정직 표기) |
| 여러 CO 가 같은 ITEM | 최신 코드 기준 한 번에 정합, 관련 CO 함께 근거·함께 🎨 |
<!-- IF work_claim -->
| work_claim 이 이미 만료(expired) | close 생략, MASTER 🎨 만. 만료 자체가 사실상 종결 |
| CO 에 claim_id 없음 | close 생략, MASTER 🎨 만 |
<!-- ENDIF work_claim -->
