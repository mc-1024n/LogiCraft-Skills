---
name: {{skill_prefix}}-dispatch
description: {{project_name}} 전용 수정 오케스트레이터. 이미 구현된 코드를 테스트·수정 반복 단계에서 고칠 때 쓴다. 자유서술 수정요청을 받아 ① 의도 파악 → ② 변경지시서(Change Order) 파일 작성 + 마스터 등록(LogiCraft 설계·로컬 키트는 즉시 반영 안 함 — 나중 배치) → ③ 영향 도메인 판정 → ④ 확인 게이트 → ⑤ 도메인별 구현 에이전트(<매핑표의 도메인 에이전트명>)<!-- IF frontend_track -->·프론트({{prefix}}-web-implementer)<!-- ENDIF frontend_track -->로 병렬 fan-out(구현+self검증+추적, 키트 SYNC 없이 메인이 change_detail 직접 전달) → ⑥ 독립 QA({{prefix}}-qa-verifier — self검증 불신, 실측 재실행+수용기준 재대조+어드버서리얼, fail 시 재구현) → ⑦ 회수·마스터 갱신. 사용자가 "이거 고쳐줘", "이 수정사항 반영해줘", "테스트하다 이거 바꿔야 해", "/{{skill_prefix}}-dispatch" 등 기존 코드 수정을 요청하면 실행. 변경지시·영향범위는 사용자 확인 후 진행(AI 임의 진행 금지).<!-- IF has_build --> 미착수 도메인의 최초 구현은 이 스킬이 아니라 {{skill_prefix}}-build.<!-- ENDIF has_build -->
---

# {{skill_prefix}}-dispatch — {{project_name}} 수정 오케스트레이터

자유서술 수정요청 하나를 받아, **변경지시서(CO)를 파일로 남기고 → 영향 도메인 코드를 도메인 전용 에이전트로 구현**한다.
규칙의 **까닭·실측 사례**는 같은 폴더의 `reference.md` 에 있다(📎 표시). 이 본문은 절차만 담는다.

## 단계 체크리스트 — 이 표만 남아도 뼈대는 지킨다
☠️ 대화가 압축됐거나 이어서 하는 중이면 **이 스킬을 다시 호출해 본문을 다시 읽고** 진행한다(기억으로 이어 가지 않는다).

| 단계 | 반드시 할 것 |
|---|---|
| 1 의도 파악 🚦 | 무엇·왜·범위 정리 → 사용자 확인 |
| 2 CO 작성 | `_TEMPLATE.md` 로 CO 파일 + MASTER 행(📝·⏳) |
| 3 영향범위 🚦 | **아래 게이트 형식 그대로**(탐색근거·QA 계획 세 줄<!-- IF parallel_lanes --> · 레인 판정<!-- ENDIF parallel_lanes -->) → 승인 |
| 3.5 메인 선처리 | 스키마·마이그레이션·공유기반을 건드리면 메인이 먼저 — **마이그레이션 절차 4단계** |
| 4 구현 fan-out | 프롬프트에 `knowhow_dir_abs` + 색인 훑기 명령 + 「실물이 진실원」 |
| 5 회수 | `design_facts` → CO §6 · **`knowhow_read` 열람 게이트**(표대로 되돌려 보내기) |
| 5.5 독립 QA | 다른 모델 · verdict 로 판정 · **인용 확인**(바뀐 파일을 실제로 인용했나) · fail 이면 재구현 |
| 5.9 노하우 🚦 | `learned` 있으면 사용자 동의 → append → **머리말 재생성** · 본체 400줄 게이트 |
| 5.95 전체 시험 🚦 | `{{full_test_gate}}` 에 따라 메인이 한 번 |
| 6 마감 🚦 | **IMPREC 늘었나 실측** → MASTER ✅ → 사용자 보고(쉬운 말) · 커밋은 묻고 |

## ★ 핵심 원칙
1. **LogiCraft 설계·로컬 키트는 즉시 반영하지 않는다.** 수정사항은 **CO 파일**(`{{change_orders_path}}CO-NNN-*.md`)에만 쓰고, 설계 backfill 은 나중에 `/{{skill_prefix}}-design-backfill` 로 한다.
2. **적용 상태는 `{{change_orders_path}}MASTER.md`** 표로 관리한다(CO 별·도메인별 구현/설계반영).
3. **구현 에이전트는 키트를 SYNC 하지 않는다.** 메인이 CO 의 도메인 변경 상세(`change_detail`)를 프롬프트로 준다 → **수정 모드**(`change_detail` 이 진실원).
<!-- IF code_boundary == package -->
4. **공유기반**({{shared_base}})은 도메인 에이전트가 못 고친다 → **메인이 먼저**(Phase 3.5) 처리한 뒤 fan-out.
<!-- ENDIF code_boundary -->
5. **오케스트레이션만** — 직접 코드/ITEM 안 짬(선처리 예외). 구현은 도메인 에이전트, QA 는 `{{prefix}}-qa-verifier`, 설계 반영은 별도 스킬.
6. **AI 추정 금지 · 정직 회수** — 판정·값을 임의로 확정하지 않는다(애매하면 사용자). 에이전트·QA 결과는 가감 없이, red 숨김 금지. 노하우 반영 책임은 메인(에이전트는 자기 파일을 못 고친다).
<!-- IF work_claim -->
7. **협업 점유는 advisory** — 경고만, 구현을 막지 않는다. 생성 실패·MCP 다운이어도 진행하고 「점유 미선언」만 보고. MASTER 를 대체하지 않는다.
<!-- ENDIF work_claim -->

## 상수 · 매핑표 (라우팅 진실원)
project_id `{{project_id}}` · code_base `{{code_base}}` · CO 폴더 `{{change_orders_path}}`<!-- IF conventions_location == shared --> · 규약 `{{conventions_path}}`<!-- ENDIF conventions_location -->

{{domain_mapping_table}}

- 매핑표에 없는 대상은 **임의 진행 말고** 사용자에게 code_root·에이전트를 확인한다.
<!-- IF frontend_track -->
- 화면까지 미치면 백엔드 에이전트 + `{{prefix}}-web-implementer` **둘 다** — **백엔드 먼저, 프론트 뒤**(프론트는 응답 계약 소비만).
<!-- ENDIF frontend_track -->
- 계약 의존(상류⊃하류)이면 상류 회수 후 하류(라운드 분리).

## 파이프라인

### Phase 1 — 의도 파악  🚦게이트①
요청을 **무엇을 / 왜 / 어느 범위**로 정리. 버그면 근본원인까지 코드에서 확인. 애매하면 되묻는다.
확인: *"요청 이해: [정리]. 변경지시서로 정리하고 구현까지 진행할까요?"*

### Phase 2 — 변경지시서(CO) 작성
1. **영향 도메인 판정** — grep(`grep -ri '@design'` · API 경로 · `SCREEN-`/`API-`) + 매핑표 + 에이전트 특화지식. 여러 도메인<!-- IF frontend_track -->·백/프론트<!-- ENDIF frontend_track -->에 걸치면 각각 분해.<!-- IF code_boundary == package --> 공유기반·스키마를 건드리면 CO §3 에 명시하고 **메인 선처리** 표시.<!-- ENDIF code_boundary -->
2. **CO 파일** — `{{change_orders_path}}_TEMPLATE.md` 골격으로 `CO-NNN-{slug}.md`(번호 = MASTER 최하단 +1). **도구를 모르는 사람도 이것만 읽고 이해**하게 쓴다. §3 은 에이전트가 받아 구현할 만큼 구체적으로(대상 파일/심볼·변경·불변·주의·수용기준). §6 에 backfill 예상 ITEM.
3. **MASTER 등록** — 행 추가(📝 · 대상 도메인 · 생성일 · 설계반영 ⏳).
- ☠️ CO 에 **실측한 곳 목록**을 넣을 때는 반드시: 「이것만 고치지 말고 **전수 grep 으로 누락을 재확인**하라」 + 수용기준은 「표의 N곳 수정」이 아니라 **「구 식별자 잔존 0건」** + **그 grep 명령 자체**를 수용기준에 적는다.
  식별자는 요약 파일 · 단언 문자열 · 절차 주석 · 문서 주석(given/when/then)의 네 층에 흩어지고, template literal / f-string 안의 행은 단순 grep 에 안 걸린다. 📎 reference「CO 실측 목록」

### Phase 3 — 영향범위 확인  🚦게이트②
<!-- INSERT _switched/work_claim.recon.md IF work_claim -->
게이트 문구는 **이 형식 그대로** 쓴다(줄을 빼지 않는다):
```
변경지시서 작성: CO-NNN (제목)
<!-- IF code_boundary == package -->공유기반 선처리 필요: (있으면) <건드리는 공유기반 경로·무엇을> → 메인이 먼저
<!-- ENDIF code_boundary -->스키마·마이그레이션: <없음 | 있음 — Phase 3.5 마이그레이션 절차 · QA 전수>
영향 백엔드: DOMAIN-00N → <매핑표의 도메인 에이전트명>
<!-- IF frontend_track -->영향 프론트: SCREEN-NNN → {{prefix}}-web-implementer
권장 순서: (공유기반 →) 백엔드 → 프론트
<!-- ENDIF frontend_track -->탐색근거: <무엇을 어떻게 좁혔는지 — 빈칸 금지>
QA 계획: <전수|경량|생략> · 회귀 <변경파일만|1홉> · 예상 <N>분
  근거: <왜 그 등급인가 — 한 줄>
<!-- IF parallel_lanes -->레인 판정: <메인 | 레인 <이름>(구현 N/{{lane_concurrency}})> — 근거: <「병행 레인」 판정 넷> · 박아 보낼 번호: <CO·마이그레이션 — 열린 레인과 메인 최신값을 함께 보고>
<!-- ENDIF parallel_lanes -->이대로 진행할까요?
```
승인 후 진행. 판정 불명확·미매핑·breaking<!-- IF frontend_track -->·프론트 구현 여부<!-- ENDIF frontend_track --> 는 그때 되묻는다.

**QA 등급** — 질문은 하나: 「빌드·테스트가 그린인데도 **사용자 화면에서 터질 수 있는가**」 📎 reference「QA 계획 합의」
| 등급 | 대상 |
|---|---|
| **전수** | 물리명 rename · 스키마·마이그레이션 · 외부 계약 접점 · 인증/권한 · 캐시 정책 · 공용 컴포넌트 |
| **경량** | 정적으로 확정되는 것 — 주석·문서 · 로직 0 변경 · 설계 서술 |
| **생략** | 오타·문구 1줄 |
- ☠️ 착수 뒤에 **공용 컴포넌트·공용 모듈 편입 / 물리명·스키마 변경 / 인증·권한 / 외부 계약**이 나타나면 등급을 **다시 판정**한다.
- 경량이어도 빼지 않는 셋: ①구현자 주장 수치의 **독립 재현** ②동시 작업과의 **경계 침범 양방향 확인** ③「무엇이 없음」 AC 의 **음성 대조**(위반을 일부러 넣어 잡히는지).
<!-- INSERT _switched/work_claim.declare.md IF work_claim -->

### Phase 3.5 — 메인 선처리 (해당 시, 메인 직접)
<!-- IF code_boundary == package -->
CO 가 공유기반({{shared_base}})을 건드리면 **도메인 fan-out 전에 메인이 먼저** 처리한다(공용 시그니처·빌드 스크립트 등). 도메인 에이전트는 이 결과를 전제로 구현하고, 여기서 실패하면 도메인 구현은 보류한다.
<!-- ENDIF code_boundary -->
**스키마·마이그레이션을 건드리면 — 누가 쓰든 이 네 단계를 지킨다** 📎 reference「마이그레이션 절차」
1. **사본에 먼저 적용** — 개발 데이터의 사본(복제 DB·덤프 복원·임시 스키마)에 먼저 돌리고, **표마다 행 수를 적용 전·후로 비교**한다. 바뀐 칸은 몇 행을 골라 값을 눈으로 확인한다. 줄어든 표가 있으면 멈추고 이유를 찾는다.
2. **마이그레이션 시험** — 옛 모양 → 새 모양 시험을 쓴다. 경계(빈 값·중복·참조가 걸린 행·순서가 의미 있는 행)를 넣는다.
3. **자동 적용을 멈춘다** — 개발 서버·데몬이 파일 변경 때 마이그레이션을 자동 적용하거나 다시 빌드하면, 작업 동안 멈추거나 떼어 놓는다(반쯤 쓴 파일이 공유 개발 DB 에 먼저 들어간다).
4. **QA 는 전수** — 그 CO 의 QA 등급은 전수이고, probe_axes 에 「마이그레이션: 행 수 보존 · 변환 칸 값 · 순서 · 되돌리기」를 명시한다.

### Phase 4 — 구현 fan-out
영향 대상마다 **한 메시지에서 병렬로** 도메인 에이전트를 띄운다. **키트 SYNC 안 함**(수정 모드).<!-- IF frontend_track --> 백/프론트 계약 의존이면 백엔드 회수 후 프론트(2 라운드).<!-- ENDIF frontend_track -->
```yaml
project_id: {{project_id}}
domain_id: DOMAIN-00N<!-- IF frontend_track -->              # (프론트는 화면 소속 도메인)<!-- ENDIF frontend_track -->
code_root: "<이 도메인 code_root>"<!-- IF frontend_track -->   # (프론트는 웹 code_root)<!-- ENDIF frontend_track -->
<!-- IF conventions_location == shared -->
conventions: "<repo>/{{conventions_path}}"
<!-- ENDIF conventions_location -->
change_order: "<repo>/{{change_orders_path}}CO-NNN-{slug}.md"   # 참조용
change_detail: |                    # ★ 구현 진실원 (수정 모드)
  <CO §3 의 이 도메인 섹션 전문 — 대상 파일·변경·불변·주의·수용기준>
target_hint: | <알면 대상 모듈/클래스/함수/화면. 모르면 생략>
knowhow_dir_abs: "<$(git rev-parse --show-toplevel)/{{knowhow_dir}} 를 계산한 절대경로>"   # 상대경로 금지 · 파일에 박지 말고 부를 때 계산
```
프롬프트에 **반드시 넣는 문장** 셋:
- 「착수 전에 본체의 `## 노하우 색인` 을 **모든 행** 훑고, 해당 묶음을 **실제로 열어** 읽어라. 작업 도중 색인의 «이 행동»을 하려는 순간 그 행을 다시 봐라. 출력 `knowhow_read` 는 **필수**다.」 — 「관련 있으면」 같은 권유형 금지.
- 「이 작업 파일은 **참고 자료**다. 진실원은 **실물**이다. 값이 이상하면 원본을 직접 다시 재라. 어긋나면 **실물을 따르고 보고**하라.」 + **실물을 잴 수단**(조회 명령·접속 방법)을 같이 준다.
- 메인이 떠올린 묶음은 **추가 지정만** 한다(빼지 않는다). 📎 reference「노하우 전달」·「자료를 의심하게」

### Phase 5 — 회수
각 출력 YAML(implemented/verification/tracking/design_facts/knowhow_read/notes_for_main)을 취합한다. red 는 그대로.

**설계 사실 옮겨 적기** — `design_facts`(`{item, field, value, basis}`)를 CO §6 「설계 사실」에 `- ITEM.칸: 값 — 근거` 한 줄씩 옮긴다. 근거 없는 줄·실재 확인 안 된 ID 는 옮기지 않는다. 비면 「설계 사실 없음」 한 줄. LogiCraft ITEM 은 여기서 고치지 않는다.<!-- IF code_boundary == package --> needs_core_change 가 나오면 Phase 3.5 로 되돌아간다.<!-- ENDIF code_boundary -->

**노하우 열람 게이트** (구현·QA 공통) — 각 `knowhow_read` 를 이 표대로 처리한다:
| 상태 | 처리 |
|---|---|
| 필드 없음 / 빈 값 | **되돌려 보낸다**(결과 보존 · 「색인을 훑고 knowhow_read 를 채워라」만 재지시) |
| `skipped` 가 색인 행 수보다 적음 | 훑지 않은 행이 있다 — 되돌려 보낸다 |
| `used` 에 **`how` 가 없음** | 되돌려 보낸다(`how` 만 채우면 된다) |
| `how: full` 인데 `matched` 가 없거나 4 미만 | 되돌리지 않는다 — 세어서 Phase 5.9 에 올린다 |
| 같은 묶음이 2 라운드 연속 `how: full` | 그 묶음을 쪼갠다(Phase 5.9) |
| 채워져 있음 | **전사본과 대조**한다 ↓ |
- **대조**: 가능하면 서브에이전트 전사본에서 묶음 Read 의 `file_path`·`offset`·`"limit"` 을 뽑아 센다(스크립트 📎 reference「열람 대조 스크립트」). 외부 위임 QA 는 그 도구의 실행 로그에서 묶음 파일명을 grep 한다. 전사본·로그를 못 찾거나 0건이면 **「측정 불가」**로 적고 「안 읽었다」로 단정하지 않는다.
- 결론 전에 **측정기부터 검산**한다 — `head` 로 자르지 말고 총계와 목록 길이를 맞춰 보고, 실패 줄은 앞뒤를 읽어 성공 열람이 선행했는지 본다.
- 보고한 `how` 와 실제 Read 인자가 어긋나거나(`how: items` 인데 limit 없는 Read), `read` 에 적은 묶음이 실제 열람에 없으면 **결함**으로 보고하고 Phase 5.9 에서 본다.
- 라운드마다 「묶음 열람 수」를 보고에 한 줄 남긴다(목적은 벌이 아니라 측정).

### Phase 5.5 — 독립 QA 검증 ({{prefix}}-qa-verifier)
회수 직후 대상마다 병렬. 구현이 red 면 QA 생략, 바로 재구현. 규모가 아주 작으면(오타·문구 1줄) 생략할 수 있으나 **기본은 실행**.

**검증은 구현과 다른 모델로 돈다**(온보딩 확정값) 📎 reference「다른 모델로 검증」
| 항목 | 값 |
|---|---|
| **검증 모델·위임** | `{{qa_model}}` |
| **부르는 방법** | `{{qa_invoke}}` |
| **실패 시 대체 경로** | `{{qa_fallback}}` |
| **실패 판별 신호** | `{{qa_fail_signal}}` |

```yaml
# Phase 4 의 project_id · domain_id · code_root<!-- IF conventions_location == shared --> · conventions<!-- ENDIF conventions_location --> · change_order · change_detail 그대로 + 아래
implemented: | <구현 에이전트가 보고한 변경 파일·요지>
claimed_verification: | <구현 에이전트가 주장한 결과 — QA 가 실측 대조>
changed_files: | <`git diff --name-only` 결과 — 1차 회귀 범위>
qa_scope: | <Phase 3 에서 합의한 등급·회귀 홉수 **그리고 그 근거**. 근거가 틀렸다고 보이면 반증하고 보고하라>
probe_axes: | <★ 메인이 정한 «파고들 축». 비우지 마라. design_facts 가 있으면 「각 basis 의 파일:줄이 실재하고 ±3줄 안에 조각이 글자 그대로 있나 · 값(ID)이 실제 테이블·가드·이벤트와 맞나」 축을 넣는다. 마이그레이션이면 Phase 3.5 의 축>
knowhow_dir_abs: "<$(git rev-parse --show-toplevel)/{{knowhow_dir}} 를 계산한 절대경로>"   # ★ 필수 — 위임하면 묶음이 안 따라간다
```
- 프롬프트에 함께 넣는 줄: 「색인 전 행 훑기 · `knowhow_read` 필수」 · 「**전체 시험은 오케스트레이터가 한 번 돈다 — 여기서는 연관 시험만**」 · 회귀 범위 2단(아래) · 「**반드시 돌려라. 부작용은 공개하면 된다**」(회피 명분 금지) · 「못 하면 왜 못 했는지와 무엇이 미검증인지 적어라」(갈음 금지).
- 띄우기 전에 조립한 프롬프트를 `grep knowhow_dir_abs` 로 확인한다. 위임은 **로그를 파일로 남기게** 부른다(`> qa-out.log 2>&1`).
- **회귀 범위 2단**: 1차 = 변경 파일 전건 정독 · 2차 = 바뀐 심볼을 «직접» 부르는 곳(1홉)까지 — 「안 본다」가 아니라 **어디까지 봤는지 1홉 목록과 판정을 적게** 한다. 범위를 좁힌 근거도 주고, 틀렸으면 반증하게 한다. ⚠️ 물리명 rename · 스키마 변경 · 공유 DB 접점은 이 제한 없이 **전수 스윕**.
- 축(`probe_axes`)은 메인 몫이다 — 비면 모델 탓이 아니라 지시 탓이다.

**판정 — verdict 로 한다(종료 코드가 아니다)**
1. `{{qa_fail_signal}}` 로 **「아예 안 돈 것」**을 먼저 가린다 → 그렇다면 `{{qa_fallback}}` 으로 대신 돌리고 **대신 돌렸다는 사실을 보고**한다. 연속 2회면 모델 설정을 의심한다.
2. 완주했는데 verdict 직전에 끊겼으면(예: 강제 종료) **재실행하지 말고 로그에서 판정을 회수**한다.
3. ★ **인용 확인** — pass 를 받기 전에 QA 출력 `read_evidence`(없으면 보고 본문)가 **이번 `changed_files` 중 하나 이상을 경로(+줄)로 인용**하는지, 인용한 경로가 **이 저장소에 실재**하는지 본다(`test -e`). 하나도 인용하지 않았거나 없는 경로를 인용했으면 **「안 돈 것」으로 보고 1번의 대체 경로**로 간다. 📎 reference「인용 확인」
4. `pass`/`pass_with_notes` → Phase 5.9 · `fail` → 구현 에이전트에 issues+fix_hint 로 재호출(최대 2라운드), 그래도 fail 이면 red 보고 · `blocked` → 정직 보고(런타임 검증 잔여).
- QA 의 adversarial 보고가 **CO 전제를 반증**하면, 메인이 그 반증을 **한 번 재현**한 뒤 CO 본문에 정정문을 박는다. 드러난 선존 결함은 **별건 CO 로 이월**한다(이번 CO 에 끼워 넣지 않는다). 📎 reference「QA 가 CO 를 뒤집을 때」

### Phase 5.9 — 노하우 반영 (에이전트 파일 갱신)  🚦게이트
`notes_for_main.learned` 가 전부 비면 건너뛴다(보고에 「노하우 신규 없음」).
- 있으면 항목별로 **사용자에게 제시**(어느 에이전트에 무엇을 + 근거·재발조건) → 동의한 것만 해당 에이전트 파일(`<매핑표의 도메인 에이전트명>`<!-- IF frontend_track --> · 프론트는 `{{prefix}}-web-implementer`<!-- ENDIF frontend_track -->)에 **append**. 기존 항목은 함부로 지우지 않는다. QA fail → 재구현으로 드러난 함정도 후보. 근거 없는 항목은 반영하지 않고, 동의 못 받은 것은 CO §7 에 남긴다. 설계에서 온 제약은 노하우가 아니라 backfill 대상이다.
- ☠️ **append 하면 그 자리에서 머리말을 다시 만든다** — `python3 {{knowhow_dir}}_gen-headnote.py` → `--check` rc=0 을 보고에 적는다. 새 항목에는 **등급(★/☠️)을 붙인다**(없으면 머리말이 빈다).
- `knowhow_read.skipped` 사유를 라운드 내용과 대조한다 — 「해당 없음」이라 건너뛴 묶음 항목이 그 라운드에 실제로 닿았으면 **묶음 배치가 틀린 것**이다 → 읽힐 묶음으로 옮기고 색인의 「이 행동을 하기 전」도 고친다.
- **본체 줄 수 게이트** — 반영 직후 `wc -l`. **400줄 초과면 사용자에게 묻는다**(자동 정리 금지 · 묶음은 세지 않는다). 처방 순서:
  ① 상시 절이 항목 5개 또는 120줄을 넘으면 **첫 묶음을 판다**(가장 큰 주제부터 · `{{knowhow_dir}}<prefix>-<주제>.md` · 색인에 **「이 행동을 하기 전」**으로 건다 — 주제가 아니라 행동)
  ② 새 노하우는 **주제에 붙인다 — 라운드 섹션 금지** · 같은 함정이 있으면 그 항목을 보강한다
  ③ 정리는 **보관 후** — 원문을 `{{knowhow_archive_dir}}<에이전트>-노하우전문-<YYYYMMDD>.md` 로 뜨고, **제목 단위 대조로 유실 0건**(본체 + 묶음 합산)을 확인한 뒤 뺀다. 제시할 것: 본체 줄 수 · 주제별 분량 · 묶음 후보와 근거 · 삭제 후보와 근거.
  ④ 매 라운드 필요한 것(게이트 판정법 · 검사 기준선 · 사고 이력이 있는 축)과 되돌리기 어려운 금지 규칙은 본체 상시 절에 둔다.
- **묶음 600줄은 검토 신호** — 순서: 중복 정리 → 잘못 놓인 항목 재배치 → 그래도 크면 «서로 다른 순간에 필요한가»로 판정해 **평면으로** 쪼갠다(`<주제>-<하위>` · 묶음 안에 묶음 금지 · 색인은 한 단). 600줄 초과면 쪼갤지 묻는다. 쪼갠 직후 **끊긴 참조 검사**(본체·스킬이 가리키는 `_knowhow/*.md` 실재). 📎 reference「노하우 구조」

### Phase 5.95 — 전체 시험 게이트 (메인 직접 · `{{full_test_gate}}`)
구현 에이전트와 QA 는 **연관 시험만** 돌렸다. 전체 시험은 **여기서 한 번**이다.

{{test_scope_table}}

| `{{full_test_gate}}` 값 | 언제 전체 시험을 돌리나 |
|---|---|
| `per_co`(기본) | 이 CO 의 구현·QA 가 다 통과한 뒤, Phase 6 **직전에 1회** |
| `per_batch` | CO 여러 건을 이어 처리할 때 **묶음 끝에 1회**(중간 CO 는 MASTER 에 「전체 미실행」) |
| `pre_deploy` | 배포·릴리스 직전에 1회 — 전체가 매우 느린 프로젝트용 |
- ☠️ 구현·QA 프롬프트에 전체 시험 명령을 넣지 않는다.
- 전체가 빨가면 이 CO 탓인지 먼저 가른다(그 시험 단독 재실행 · 바꾸기 전 지점과 대조). 원래 흔들리던 시험이면 그렇게 적고 **따로 CO** 로.
- CPU 를 다 쓰면 동시 작업 수를 줄여 돌린다(프로젝트 규약의 값). 보고·MASTER 에 **돌렸는지와 수치**(파일 수 · 건수 · 소요).

### Phase 6 — 마감<!-- IF work_claim --> · claim heartbeat<!-- ENDIF work_claim -->  🚦
**IMPREC 추적 게이트**(✅ 로 닫기 **전**) — 확인은 「했나?」가 아니라 **「늘었나?」**. 📎 reference「IMPREC 게이트」
- `get_implementation_coverage(domain_id=…)` 또는 `list_items(type=implementation_record, …)` 로 **이번 CO 분이 실제로 늘었는지** 센다(보고 문장은 근거가 아니다).
- 비면 구현 에이전트를 재호출하거나 메인이 `create_implementation_record` / `mark_implementation` 으로 채운다. 이번 IMPREC 의 **`evidence`**(커밋·시험 이름·파일 경로)가 비었으면 채운다.
- 설계 ITEM 이 없는 변경(리팩터·문서·설정)은 「대상 아님」을 한 줄로 남긴다.

**마스터·보고**
- MASTER: 도메인별 ✅(QA pass + IMPREC 게이트 통과 뒤) + 커밋. CO §7 구현 로그도 갱신.
<!-- INSERT _switched/work_claim.heartbeat.md IF work_claim -->
- 실패·red 는 그대로 노출. notes 의 추가 영향 도메인·정보 부족은 다음 액션.
- ★ **사용자에게 하는 마지막 보고는 쉬운 말로** — 내부 용어(변경지시서 번호·IMPREC·레인·verdict 등) 대신 **무엇이 바뀌었고 무엇을 확인했고 무엇이 남았는지**를 쓴다. 보고 언어는 사용자의 언어(프로젝트 지침이 정한 언어 · 없으면 사용자가 쓰는 언어).
- **커밋은 자동 안 함** — 사용자에게 묻는다.<!-- IF commit_strategy == submodule --> 서브모듈 2단 커밋(서브모듈 → 상위 포인터).<!-- ENDIF commit_strategy --> 커밋금지 파일({{commit_forbidden}}) 제외.

### [별도 배치] 설계 반영 → `/{{skill_prefix}}-design-backfill`
MASTER 의 설계반영 ⏳ CO 들을 모아 CO §6·본문·커밋 코드를 근거로 LogiCraft ITEM 을 맞춘다(실제 수정은 `mc-logi-update` 에 위임). 완료 시 MASTER 를 🎨 로 닫는다.

<!-- INSERT _switched/lanes.dispatch.section.md IF parallel_lanes -->
