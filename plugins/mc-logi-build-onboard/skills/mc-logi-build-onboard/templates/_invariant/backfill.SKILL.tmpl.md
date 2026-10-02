---
name: {{skill_prefix}}-design-backfill
description: {{project_name}} 변경지시서(Change Order) 기반 LogiCraft 설계 backfill 스킬. {{skill_prefix}}-dispatch 가 코드를 먼저 구현하고 미룬 "설계 반영"을 나중에 배치로 처리한다. {{change_orders_path}}MASTER.md 에서 설계반영 대기(⏳)인 CO 를 모아(또는 특정 CO 지정), 각 CO 의 §6(관련 설계 ITEM)·변경 내용·실제 커밋된 코드를 근거로 LogiCraft ITEM 을 실제 구현에 맞춰 retro-align 한다. 실제 ITEM 수정·cascade 는 mc-logi-update 에 위임하고, 이 스킬은 CO→입력 변환 + 게이트 + MASTER 상태(🎨) 갱신만 담당. 사용자가 "CO 설계 반영해줘", "backfill 해줘", "/{{skill_prefix}}-design-backfill" 이라고 하면 실행. 처음부터 칸에 쓴다 — CO §6 「설계 사실」을 연결·구조 칸 값으로 넘기고, 변경 경위는 본문이 아니라 change_summary 로. AI 추정 금지 — CO·코드에 근거 없는 값은 넣지 않는다(애매하면 사용자).
---

# {{skill_prefix}}-design-backfill — CO 기반 LogiCraft 설계 backfill

`{{skill_prefix}}-dispatch` 는 **코드 구현을 먼저** 하고 LogiCraft 설계 반영을 **나중 배치**로 미룬다(변경지시서 CO 파일이 1차 진실원). 이 스킬이 그 미뤄둔 배치를 처리한다 — **이미 구현·커밋·QA 통과된 코드에 맞춰 LogiCraft 설계 ITEM 을 retro-align** 하고, MASTER 의 설계반영 상태를 🎨로 닫는다.

## ★ 핵심 원칙

1. **코드가 진실원(retro-align)** — 이 시점엔 코드가 이미 구현·커밋·QA 통과 상태다. 설계를 코드에 **맞춘다**(설계→코드가 아니라 코드→설계). ⚠️ "retro-align"은 개념 이름일 뿐 mc-logi-update 의 형식 모드·파라미터가 아니다 — 코드 우선 정합은 **edit_intent/edit_context 문구로** 전달한다("코드가 이미 이렇게 구현·커밋됨 → 설계를 이 코드에 맞춰 정정하라").
2. **실제 수정은 mc-logi-update 위임** — 이 스킬은 LogiCraft ITEM 을 직접 고치지 않는다. CO 를 mc-logi-update 입력(target_id·edit_intent·edit_context)으로 변환해 넘기고, cascade·specialist·검증은 그 스킬이 처리한다.
3. **CO §6 + 본문 + 실제 코드가 근거** — 무엇을 어떻게 고칠지는 CO 파일의 §6·§2~3·§7(커밋)과, 필요하면 그 커밋의 실제 코드에서 확인. **AI 추정 금지**.
4. **MASTER 가 진척 진실원** — 처리 대상·완료 상태는 `{{change_orders_path}}MASTER.md` 의 `설계반영` 열(⏳ 대기 → 🎨 완료)로 추적.
5. **★ 처음부터 칸에 쓴다(작성 규칙)** — 백필은 근거가 가장 좋은 자리다(방금 커밋한 코드·CO). 원문은 서버 가이드 `get_logicraft_guide("workflow")` 「산문을 칸으로」.
   - **관계·구현 사실은 칸 값으로** — CO §6 「설계 사실」(`ITEM.칸: 값 — 근거`)을 그대로 칸에. 산문에 ID 를 나열해 링크를 만들지 않는다.
   - **본문엔 현행만** — 「CO-NNN 에서 X 로 바꿨다」는 description·notes 에 붙이지 않고 `change_summary` 로. `### Session NN`·날짜 로그 절 금지.
   - **기존 항목은 `patch`/`merge`** — `replace` 금지(채운 칸이 사라진다).
   - **범위 = 이 CO 가 바꾼 것** — 손대지 않는 옛 문단의 산문 속 ID 는 옮기지 않는다(옛 잔고는 `mc-logi-schema-fill` 몫).
   - 왜: 이관 때 옮긴 «경위» 문단 대부분이 백필이 description 에 덧붙인 것이었다. 여기서 막지 않으면 바로 다시 쌓인다.
6. **게이트** — 실제 mc-logi-update 실행 전에 backfill 계획(CO별 어떤 ITEM 을 어떻게)을 사용자에게 확인받는다.
<!-- IF work_claim -->
7. **work_claim drift 해소 = backfill 의 종착** — dispatch 는 CO 착수 시 advisory `work_claim` 을 `design_pending=true` 로 열어두고 닫지 않는다. 그 claim 을 닫는 건 **이 스킬의 책임**이다 — backfill 완료 시 `update_work_claim(design_pending=false)` → `close_work_claim` 을 **MASTER 🎨 전환과 동시에** 처리해 크로스세션 drift 신호를 닫는다.
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
   - **§6 관련 설계 ITEM** — 두 부분이다(1차 입력):
     - **설계 사실** — `ITEM.칸: 값 — 근거(코드: 경로:줄 — 조각 · CO §n)`. 구현 에이전트가 코드에서 확인해 낸 `design_facts` 를 dispatch 가 옮겨 둔 것 → **칸 값**으로 넘긴다.
     - **서술 변경** — 산문(description 등)에 반영할 **현행** 내용.
     - 옛 CO(§6 이 한 줄 자유 서술)는 설계 사실이 없다 → A 초안이 커밋 코드에서 뽑는다(아래).
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
    칸: operates_on +ERD-NNN (코드: apps/…/service.ts:88 — from(tbl)) · required_roles [ROLE-NNN] (코드: …controller.ts:17 — hasPermission(access,"write"))
    경위: change_summary ← "CO-NNN — envelope 로 정정"
```
- **retro-align 명시**: "코드가 이미 이러하므로 설계를 이에 맞춘다"를 근거로.
- **불확실 항목 분리**: CO §6 에 있으나 근거 약한 것은 "확인 필요"로 빼서 사용자에게(추정 반영 금지).
- 여러 CO 가 같은 ITEM 을 건드리면 **최신 코드 상태로 한 번에** 정합.

**승인 후** Phase 2.

### Phase 1.5 — 분업 계획 (★ 값싸게 돌리는 법)

CO 가 여러 건이거나 ITEM 이 많으면 **메인이 혼자 다 하지 않는다.** 네 단계로 갈라 워커에 위임한다.

**모델·위임**: `{{backfill_model}}` (비어 있으면 `{{qa_model}}` 과 같은 것) · 부르는 법 `{{qa_invoke}}`

#### ☠️ 레인마다 «성공 판정»이 다르다 — 초안·반영 레인에 `--require-verdict` 를 주지 마라

위 호출법은 **QA 용**이다. `--require-verdict` 는 출력에 `verdict:` 줄이 없으면 exit 20(DELEGATION_FAILED)을 낸다.
A 초안·B 반영·C 말단은 verdict 를 내지 않는 작업이라 **정상 완주해도 exit 20 이 난다** —
실측(2026-10-01 CO-193/195): 초안 2건이 MCP 조회 30여 회 + 초안 파일 완성까지 하고도 「인증 실패」로 찍혔다
(로그에 권한 코드 `ForbiddenException` 이 많아 러너가 오판 — 러너도 함께 고쳤다).

| 레인 | 호출 | 성공 판정 | 실패 시 |
|---|---|---|---|
| **A 초안** | `--require-verdict` **없이** | 지정한 **초안 파일이 생겼고 비어 있지 않다** + 최종 ```yaml 블록에 `draft_path` | 파일 없음 → 메인 서브에이전트로 대체 실행(대체했다고 보고) |
| **B 반영 · C 말단** | `--require-verdict` **없이** | 보고 YAML 의 항목별 `new_version` 을 **`get_item` 으로 실측** 대조 | 버전이 안 올랐으면 그 항목만 재위임 |
| **D 독립 검사** | `--require-verdict` **붙여서** (QA 와 같다) | `verdict:` 줄 + 근거 검증 게이트(`verify-qa-evidence.py`) | exit 20 → 대체 실행 |

☠️ 종료코드·러너 메시지로 판정하지 마라 — **산출물(파일·버전·verdict)로 판정한다.**

#### 왜 네 단계로 가르나 — 한 워커에 다 맡기면 **검증할 제3자가 없어진다**

| 단계 | 하는 일 | 성격 | 배분 |
|---|---|---|---|
| **A 초안** | CO §관련설계ITEM + **커밋된 실제 코드**를 읽고 ITEM별 수정 초안(md)만 작성 — 초안마다 **「칸 값」 절 필수**(값 + 근거, 산문 수정안과 분리) + 「경위 → change_summary」 한 줄. **쓰기 도구 전면 금지** | 코드를 **설계 문장으로 번역** — 판단 무거움 | 추론 쪽 |
| **B 반영** | 초안을 근거로 실제 `update_item`/`create_item` | 초안대로 patch — **기계적** | **가장 싸게** |
| **C 말단** | 상위 ITEM 마다 `analyze_impact`·`get_neighbors` 로 하위 전개 후 대조 | 전개는 기계적, 「변경 불요」 판정은 판단 | 중간 |
| **D 독립 검사** | 전 ITEM 을 초안·CO·**코드**와 재대조 + **작성 규칙 5검사**(아래). **쓰기 금지** | 3방향 재대조 — 판단 무거움 | 추론 쪽 + **다른 눈** |

☠️ **D 를 빼지 마라 — 유일한 그물이다.** 설계는 **틀려도 아무것도 안 깨진다.** 코드는 빌드가 잡지만
설계 ITEM 은 잘못 써도 **버전만 올라간다.** 게다가 **「맞는 말인데 엉뚱한 칸에 쓴 것」은 버전 대조로
안 잡힌다**(이력 칸에만 쓰고 현행 칸은 옛 서술로 둔 실사고).

#### ★ D 독립 검사 — 작성 규칙 5검사 (백필마다 상시 · 회귀 방지)
1. 이번에 쓴 산문(수정 전후 diff 의 추가분)에 **ITEM ID 나열**이 없나 — 관계는 칸에 갔나
2. description·notes 에 **경위 문장**(「CO-NNN 로」「vN 에서」「### Session」「날짜 로그」)이 새로 붙지 않았나
3. 저장 경고 `*_IN_PROSE` 중 **이번 수정분**에서 난 것이 0 인가(옛 문단 것은 수만)
4. 기존 항목에 **`replace`** 를 쓰지 않았나 — 수정 전 채워져 있던 칸이 그대로인가
5. 칸 값마다 **근거**(CO 절·`코드: 경로:줄 — 조각`)가 있고, 코드 근거 줄이 **실재**하나
하나라도 걸리면 그 ITEM 은 B 로 되돌린다.

#### ★ 재검토 표시 보존 검사 (위 5검사와 별개 · 데이터 유실 방지)
백필은 항목의 일부만 고친다. 그런데 저장 하나로 그 항목의 재검토 표시가 원인과 무관하게 전부 지워지면, 검토하지 않은 표시가 **사라진다**.
실측(2026-10-01, CO-193·195·185·190·192): 저장 8항목에서 **58건 소실**, 그중 이번 수정과 관련 있던 것은 3건뿐이었다.
- **B 반영 레인 — 저장할 때 선언한다** (서버가 `resolves_review_from` 을 지원하는 경우 · LogiCraft CO-201 이후)
  - `update_item` 에 `resolves_review_from: [이번 CO 에서 함께 고친 원인 항목]` 을 준다(예: DFEAT-013 저장이면 같은 라운드에 고친 API-044).
  - 불확실하면 **생략**한다(표시가 남는다 — 안전).
  - `"all"` 은 쓰지 않는다. 백필은 원인 전부를 검토하지 않는다.
- **대비 — 옛 서버면 라운드 끝에 되살린다** (입력이 거부되거나 응답에 `review_marks` 가 없을 때)
  - `restore_review_needed(item_ids=[이번에 저장한 항목], since=<라운드 시작 시각>, dry_run=false)`
  - ☠️ **dry_run 기본값이 true** 다 — false 를 빼면 아무것도 안 되살아난다.
- **D 검사**
  - 해제된 표시가 선언한 원인뿐인지 본다(응답 `review_marks.resolved` · 상용이면 stale_flags 읽기 조회).
  - 옛 서버라면 `restore_review_needed` dry_run 으로 「라운드 시작 이후 풀린 것 0건」을 확인한다.

#### ★ A 초안 — 칸 값을 코드에서 뽑는 법 (§6 에 설계 사실이 없을 때)
- 구현 사실 칸 — `operates_on`(핸들러→서비스→쿼리를 따라가 **실제로 읽고 쓰는 테이블**) · `required_roles`(라우트의 **권한 가드**가 요구하는 역할) · `triggers`/`consumes`(발행·구독 이벤트) — 은 **커밋된 코드**가 진실원이다.
- 근거 형식: `코드: <레포 상대경로>:<줄> — <그 줄 근처의 글자 그대로 조각>`. 커밋 해시를 함께.
- 감사 로그·아웃박스처럼 모든 쓰기가 남기는 공통 테이블은 넣지 않는다. 로그인만 확인하는 가드는 역할이 아니다.
- 구현기록(IMPREC)의 `evidence` 는 커밋·spec 이름·파일 경로·CO 번호로 **구조화**한다 — 산문에 「테스트 N건 통과」로 쓰지 않는다.
- 설계 의도 칸(`based_on_adrs`·`implements_requirements`)은 CO 에 적힌 것만. 짐작해 채우지 않는다.

#### ★★ 나누는 축은 **CO 가 아니라 «ITEM 소유권»** 이다

사용자가 「연관된 CO 끼리 묶어 병렬로」라고 해도 그대로 하면 안 된다. **겹침 맵을 먼저 그려라** —
실측에서 한 SCREEN 을 **7개 CO** 가, 한 API 를 4개가 공유해 **CO 단위 병렬이 애초에 불가능**했다.

- **A 초안** → **CO 축 병렬 OK**(읽기만 하니 겹쳐도 안전)
- **B 반영** → **ITEM 소유권 축**. 공유 ITEM 은 **한 워커가 모든 CO 초안을 읽고 «통합 1회» patch**.
  ☠️ 따로 여러 번 고치면 **서로 덮는다**(lost update).
- **C·D** → 계열별로 분할(성격이 달라 겹치지 않는다)
- 각 워커 프롬프트에 **소유 밖 목록을 명시**하고 박아라:
  > 소유 밖 ITEM 은 **절대 수정하지 말고** 보고 본문에 「cascade 보고: `<ITEM-ID>` ← 사유」로 적어라.

#### ☠️ 전 레인 공통으로 박을 것 (일부 레인에만 박으면 사고 난다)

- **폐기 문서 함정** — 수정 전 대상 ITEM 의 `status` 를 확인하라. `deprecated`/`superseded` 면
  **멈추고 보고**한다. 실사고: 경고를 한 레인에만 박아 **API 13건이 전부 폐기 문서에 기록**됐다.
- **CO 인용 절이 최신인지** — CO 안에 「★ 재설계」·「정정」·날짜 표기가 있으면 **그 절이 정본**이다.
- **현행 실물을 먼저 읽어라** — 이미 반영돼 있을 수 있다. CO 만 보고 쓰면 **끝난 일을 또 한다.**
- **「반영할 자리가 없다」는 «변경 불요»가 아니라 «설계 누락» 신호**다 — 보고하고 사용자 판단을 받아라.
- **못 채운 것은 정직히 신고**하라. 「완료」만 받는 프롬프트는 **거짓 완료를 만든다.**
- **작성 규칙** — 관계·구현 사실은 칸 값으로 · 본문엔 현행만(경위는 `change_summary`) · 기존 항목은 `patch`/`merge`(replace 금지) · 손대지 않는 옛 문단은 그대로.

☠️ **워커 자기보고를 믿지 마라 — 양방향이다.** 재대조에서 결함이 나오기도 하지만, 반대로
**워커가 오케스트레이터의 지시 오류를 잡기도 한다**(실측: 화면 ID 오지목·API ID 오지목·
「이미 폐기돼 반영 불가」를 한 라운드에 3건). 워커의 `확인필요` 보고를 흘려듣지 말고 **CO 원문을 직접 열어라.**

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
  <CO §2/§3 변경 요지 + §6 서술 변경 + §7 커밋 해시. "코드 먼저 구현됨, 설계를 그 코드에 정합하라" 명시.>
  작성 규칙: 아래 fields 는 산문이 아니라 칸 값으로(patch). 산문엔 현행만. 경위는 change_summary. 기존 항목 replace 금지. 손대지 않는 옛 문단은 그대로.
fields:            # ★ CO §6 「설계 사실」 — 칸 값 + 근거 (산문과 분리)
  API-NNN:
    operates_on: [ERD-NNN]        # 코드: apps/api/src/…/x.service.ts:88 — from(tbl) · 커밋 abc123
    required_roles: [ROLE-NNN]    # 코드: …/x.controller.ts:17 — hasPermission(access,"write")
history: "CO-NNN — <한 줄>"         # → change_summary. description·notes 에 붙이지 않는다
```
- `fields` 가 비면(옛 CO) A 초안의 「칸 값」 절을 넣는다. 그것도 없으면 빈 채로 — 짐작해 채우지 않는다.

★★ **말단(leaf) ITEM 누락 방지 — 반드시 위임 프롬프트에 명시** ★★
mc-logi-update 는 cascade 시 **말단 항목을 종종 빠뜨린다**(AC·SCREEN·SEQ·CDIAG·CMP 등 leaf 는 비가시). 위임 프롬프트에 명시:
- *"cascade 를 **말단까지 완주**하라. 바뀐 상위 ITEM 마다 `analyze_impact` 로 하위 영향을 조회해 **AC·SCREEN·SEQ·CDIAG·CMP 등 leaf 를 빠짐없이 큐에 넣고** 정합하라. leaf 를 '변경 없음'으로 단정 말고 실제 대조 후 판정."*
- CO §6 에 예상 하위 ITEM 이 있으면 그 ID 를 **명시적 cascade 대상으로 함께** 넘긴다.

회수: 바뀐 ITEM 목록(id·version·요지) + mc-logi-update 보고의 **칸에 쓴 것 / 비운 칸 / 옛 산문 ID 수** 회수. 실패·미처리는 그대로 노출.

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
- **보고**: CO별 반영 ITEM(id·version)·**칸에 쓴 값 수**·cascade 건수·미처리/확인필요·D 5검사 결과를 표로.

## 게이트 요약
1. Phase 1 — backfill 계획 승인 (실제 설계 수정 전)
그 외는 mc-logi-update 정책(batch 자동)을 따름. 근거 약한 항목·breaking 변경은 그때 확인.

## 원칙
- **접착제 역할만** — 직접 LogiCraft ITEM 안 고침(mc-logi-update 위임).
- **retro-align** — 코드가 진실원. 설계를 코드에 맞춘다.
- **★ 말단 leaf 빠뜨리지 않기** — cascade 는 AC·SCREEN·SEQ·CDIAG·CMP leaf 를 자주 누락. 위임 시 "말단까지 완주" 명시(Phase 2), 회수 후 직접 대조(Phase 2.5). leaf 미반영으로 🎨 금지.
- **AI 추정 금지** — CO·코드 근거 없는 ITEM·값 반영 금지.
- **처음부터 칸에** — 관계·구현 사실은 칸 값, 본문엔 현행만, 경위는 change_summary, replace 금지.
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
