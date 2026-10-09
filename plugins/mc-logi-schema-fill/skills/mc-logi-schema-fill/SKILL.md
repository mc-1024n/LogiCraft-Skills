---
name: mc-logi-schema-fill
description: LogiCraft 스키마 개편(«산문을 칸으로», CO-138~171)으로 새로 생긴 칸 — 연결 칸(based_on_adrs·operates_on·related_apis·actor_roles 등 90여 칸), 구조 칸(migration_plan.steps·verification, incident.started_at, implementation_record.evidence, slo.error_budget 등), 담당자 종류(owner → {kind,name}) — 을 프로젝트의 기존 ITEM 마다 채워 넣고, 칸으로 옮겨 간 문장만큼 산문을 줄이는 표준 절차. 진단(채움 현황표) → 연결 칸 이관 → 구조 칸·담당자 채우기 → 산문 슬림화 → 산문에 근거가 없는 칸은 담당자에게 단계별 안내표로 넘기기까지. 코드가 있는 프로젝트는 «구현 사실» 칸(API·SVC·DFEAT 의 operates_on·required_roles)을 레포 코드에서 먼저 채운다(재료 D). AI 는 산문·코드에 근거가 있는 값만 채우고(인용을 글자 그대로 대조), 지어낸 값은 기계적으로 거부된다. 근거가 어디에도 없는 설계 의도 관계(이 화면이 어느 결정을 따르나 등)는 AI 가 후보를 «제안»만 하고 사람이 줄마다 채택한 것만 적용한다(재료 E · 관계 초안). **한 번 돌리면 끝까지 간다** — 모으기·판정을 전부 먼저 끝내고 자세한 통합 검토 문서를 한 번 보여 준 뒤, 확정되면 적용·검증·재진단까지 멈추지 않는다(scripts/oneshot.py). 시작할 때 사용자에게 무엇이 바뀌었고 스킬이 무엇을 채우고 무엇을 못 채우는지, 스킬 없이 직접 채우는 길도 있다는 것을 먼저 설명한다. 사용자가 "새 스키마 채워줘", "추가된 칸 채우기", "스키마 마이그레이션", "산문을 칸으로", "산문 슬림하게", "description 줄이기", "산문 참조 이관", "*_IN_PROSE 경고 정리", "OWNER_KIND_MISSING 정리", "based_on_adrs 채워줘", "우리 프로젝트 새 필드 현황", "/mc-logi-schema-fill" 등을 말하거나, 상용 배포 뒤 기존 항목의 빈 칸·산문 경고를 한꺼번에 정리하려 할 때 반드시 이 스킬을 쓴다. 항목 하나를 손으로 고치는 건 mc-logi-update 가 맞다.
license: MIT
allowed-tools: Read, Write, Edit, Grep, Glob, Bash, ToolSearch, AskUserQuestion, TaskCreate, TaskUpdate, TaskList
metadata:
  version: 0.9.1
  requires: "LogiCraft 서버 main b1abce67 이후(새 칸 + scan_prose_refs + 전파 억제 CO-177·178·181~184·191·192 + 자기 재검토 표시 보존·복원 CO-189 restore_review_needed + 제목 동기화 수정 CO-190). 이전 서버에 쓰면 재검토 표시가 대량 전파되거나 자기 표시가 조용히 풀린다"
---

# mc-logi-schema-fill — 새 스키마 칸 채우기

## 왜 이 스킬이 있나

LogiCraft 는 산문(description·notes)에 몰려 있던 내용을 **칸**으로 옮길 수 있게 스키마를 넓혔다
(39타입 · 새 칸 109 · 담당자 칸 18의 모양 변경 — 목록은 `references/new-fields.json`).
칸만 생겼고 **기존 항목은 비어 있다.** 각 프로젝트 담당자가 채워야 한다.

칸이 비면 생기는 일:
- **연결 칸** — cascade 는 링크만 따라간다. 산문에만 `ADR-024` 라고 적힌 항목은 그 ADR 이 바뀌어도
  영향 범위에 **안 뜬다**(실측: 같은 ADR 의 의존자가 이관 전 14 → 후 34).
- **구조 칸** — 이행 단계·검증 방법·사고 시각·구현 근거가 산문 속에 섞여 있으면 도구가 읽지 못하고,
  사람은 매번 전문을 읽어야 한다. 채우고 나면 **산문을 줄일 수 있다**(토큰·중복 감소).
- **구조 칸에는 저장 경고가 없다** — 아무도 알려주지 않는다. 이 스킬의 진단표가 유일한 안내다.

## ★ 시작할 때 — 사용자에게 먼저 설명한다

이 스킬을 쓰는 사람은 대개 **스키마가 왜 바뀌었는지 모른다.** 진단부터 들이밀면 「빈칸이 4,700개」 같은 숫자만 보고
겁을 먹거나, 전부 AI 가 채워 주는 줄 안다. 그래서 **Phase 0 전에** 아래 내용을 사용자 말로 풀어 설명하고,
진행 방식을 고르게 한다. 문장은 상황에 맞게 다듬되 **다섯 덩어리는 빠뜨리지 마라.**

### ① LogiCraft 에서 무엇이 바뀌었나
- 예전에는 설계 항목의 중요한 내용이 **산문**(설명·비고)에 섞여 있었다 — 「이 화면은 ADR-024 를 따른다」,
  「이행은 3단계: …」, 「담당: 플랫폼팀」.
- 사람은 읽을 수 있지만 **도구는 못 읽는다.** 그래서 ADR-024 가 바뀌어도 이 화면은 영향 범위에 안 떴다.
- 그래서 스키마를 넓혀 그 내용을 담을 **칸**을 만들었다(39타입 · 새 칸 109). 세 종류다.

| 종류 | 예 | 채우면 좋아지는 것 |
|---|---|---|
| **연결 칸** | 따르는 결정(`based_on_adrs`) · 다루는 데이터 모델(`operates_on`) · 구현하는 요구(`implements_requirements`) | 상대가 바뀌면 이 항목에 **재검토 표시**가 뜬다(영향 추적) |
| **구조 칸** | 이행 단계 · 검증 방법 · 사고 시각 · 구현 근거(`evidence`) | 도구가 읽고, 산문을 줄일 수 있다 |
| **담당자 종류** | `owner: "플랫폼팀"` → `{kind: team, name: 플랫폼팀}` | 사람·팀·역할을 구분해 모아 볼 수 있다 |

- **칸만 생겼고 기존 항목은 비어 있다.** 이 스킬은 그 빈칸을 채우는 도구다.

### ② 이 스킬이 채울 수 있는 것 — «근거가 어딘가 적혀 있는 값»

| 재료 | 근거 | 예 |
|---|---|---|
| A 자기 산문 | 항목 산문에 적힌 ID | 설명에 「ADR-024 를 따른다」 → `based_on_adrs: [ADR-024]` |
| B 같은 항목의 다른 칸 | 옛 칸에 있던 값 | 옛 `forward_ddl`·`post_steps` → 새 `steps` |
| C 남의 산문 | 다른 항목이 이 항목을 적은 곳 | 요구사항 「근거: API-017」 → API-017 의 `implements_requirements` |
| D 코드 (레포가 있을 때) | 실제 코드 줄 | API 핸들러가 `designPreset` 테이블을 읽는다 → `operates_on: [ERD-…]` |

### ③ 어떻게 채우나 — 지어내지 못하게 막는 장치
- AI 가 값과 **근거**(산문 인용 또는 `파일:줄 — 코드 조각`)를 함께 낸다. 스크립트가 그 인용이 **원문에 글자 그대로 있는지**
  대조한다. 하나라도 없으면 **그 묶음 전체를 거부**한다.
- 사람은 **통합 검토 문서를 한 번** 본다 — 적용될 모든 줄이 값·근거와 함께 들어 있다. 확정하면 적용은 5항목씩 재검토 표시를 전후 비교하며 끝까지 가고, 적용 뒤 최종값을 계획과 대조한다.
- 이미 있는 값은 덮지 않는다. 이미 걸려 있던 재검토 표시는 지켜서, 채우다가 풀리면 되살린다.
- 산문 줄이기는 **칸이 다 채워진 뒤에, 삭제만** 한다.

### ④ 채우지 못하는 것 — 그리고 대신 어떻게 돕나
근거가 **어디에도 적혀 있지 않은** 값은 스킬이 채울 수 없다. 흔히 가장 많다(상용 LogiCraft Self 실측:
연결 칸이 전부 빈 항목 1,218/1,524 — 산문에 ID 가 없었다).

| 못 채우는 것 | 예 | 스킬이 대신 하는 일 |
|---|---|---|
| **설계 의도 관계** | 이 화면이 어느 결정을 따르나 · 이 수용기준이 어느 요구를 검증하나 — 아무도 적어 두지 않았다 | **관계 초안(Phase 1.8)** — 그래프 이웃·드문 낱말 겹침으로 후보를 뽑고, AI 가 두 항목을 읽어 «제안 + 이유»를 낸다. **사람이 줄마다 채택한 것만** 적용한다. 기각은 기억해서 다시 묻지 않는다 |
| **아무도 적지 않은 사실** | 담당 팀 · 사고 발생 시각 · 이행 검증 방법 | **담당자 안내표(Phase 4)** — 묶을 수 있는 질문은 묶어서(예: 「이 API 15개의 담당은?」 한 번) 묻고, 답을 받아 채운다 |
| **판정자가 새로 짜야 하는 구조 값** | 산문을 읽고 재구성한 설정 객체 | **보류** — 원문 글자 그대로 넣을 수 없으면 채우지 않는다(재구성한 값은 산문 복사로 인정되지 않아 하위 항목에 재검토 표시가 번진다) |

☠️ 관계 초안은 **AI 의 판단**이 근거다. 그래서 자동으로 적용하지 않는다 — 이 점을 반드시 말한다.

### ⑤ 스킬 없이 직접 채워도 된다
AI 제안이 싫거나, 항목 수가 적거나, 관계를 가장 잘 아는 사람이 설계 담당자 본인이라면 **직접 검토해 채우는 편이 낫다.**
- **LogiCraft 웹** — 항목 상세에서 칸을 열어 직접 편집한다. 연결 칸은 대상 항목을 골라 넣는다.
- **대화로 한 항목씩** — 「SCREEN-069 가 따르는 ADR 을 넣어 줘」 → `mc-logi-update` 가 그 항목 하나를 고친다.
- **진단표만 받기** — 이 스킬의 Phase 0 만 돌려 `diagnose.md`(타입×칸 채움 현황)를 체크리스트로 쓰고, 채우는 건 직접 한다.
- 섞어도 된다 — 근거가 있는 것(②)은 스킬로, 설계 의도 관계는 직접.

### 그다음 고르게 한다
`AskUserQuestion` 으로 묻는다(권장을 첫 번째에):

| 선택 | 무엇을 하나 |
|---|---|
| **근거 있는 것은 스킬로, 관계 초안은 제안만 받아 검토** (권장) | Phase 0 → (1.7) → 1 → 1.5 → 2 → **1.8** → 4 → 3 |
| 근거 있는 것만 스킬로, 관계는 직접 | 1.8 을 건너뛴다. 끝에 「관계 칸이 빈 항목」 목록만 넘긴다 |
| 진단만 | Phase 0 만 — 채우기는 사용자가 직접 |


## ★ 한 번에 진행 (기본)

사람 게이트는 **세 번**뿐이다. 그 사이는 멈추지 않는다.

| # | 사람 | 에이전트 |
|---|---|---|
| ① 시작 | 설명을 듣고 방식을 고른다 | 「시작할 때」 절의 설명 → 방식 선택 |
| — | (기다림) | **모으기**: 진단 → 단계별 작업표 → **판정 에이전트 병렬 fan-out**(전 단계·전 타입 동시) → 판정 검사(fill·fill-fields·relation-fill) |
| ② 한 번 | **통합 검토 문서**를 읽고, 뺄 줄만 ID 로 말한다(기본 전부 채택) | `oneshot.py review-all` → `REVIEW.md` · 말한 ID 는 `oneshot.py reject` |
| — | (기다림) | **일괄 적용**: `oneshot.py apply-all` — 단계 순서대로 대상 새로 뜨기 → 계획 → `--probe --restore-self --allow-dependents` → 대조 → 해당 없음 장부 기록 |
| ③ 끝 | 보고를 읽는다 | 재진단 + `progress` → `REPORT.md` 와 함께 보고 |

### 모으기 — 라운드 폴더 하나에 표준 배치
```bash
R=<폴더>/run-<N>;  D=<폴더>/diag-<날짜>
python3 $PM scan … --out $D/scan.json && python3 $SF diagnose … --out-dir $D --scan $D/scan.json
python3 $PM snapshot … --from-scan $D/scan.json --dir $R/refs/snap && python3 $PM draft --scan $D/scan.json --snapshot-dir $R/refs/snap --out $R/refs/decisions.json
python3 $SF derive --diagnose $D/diagnose.json --ledger <장부> --prose --scan $D/scan.json --out $R/c/worklist.json
python3 $SF code-worklist --diagnose $D/diagnose.json --repo <레포> --ledger <장부> --out $R/code/worklist.json     # 코드가 있을 때
python3 $SF worklist --diagnose $D/diagnose.json --ledger <장부> --out $R/fields/worklist.json
python3 $SF auto-na --diagnose $D/diagnose.json --server <서버> --ledger <장부> --out $R/auto-na.json          # 판정 없이 확정되는 해당 없음
python3 $SF relation-cands --diagnose $D/diagnose.json --server <서버> --ledger <장부> --type <전 타입> --round-dir $R --out $R/rel/cands.json   # L·C·D·S 작업표 뒤에
python3 $SF history-paras --snapshot-dir $D/snap --out $R/hist/paras.json
```
- 한 번 판정한 칸(장부의 해당 없음·보류·안내)은 다시 묻지 않는다(`--recheck` 로만 다시 연다).
- **`auto-na` 를 판정 전에 돌린다** — 칸 설명·프로젝트 상태만으로 비워 두는 게 정답인 칸(가리킬 대상 타입 0개 · 레포 1개 이하의 `code_module.repo_ref`)을
  판정에 올리지 않고 장부로 보낸다. 상용 Self: 코드 모듈 `repo_ref` 585칸.
- ☠️ **타입을 규모로 빼지 마라** — 코드 모듈(수백 개)도 대상이다. 상용 Self 에서 «범위 밖»으로 뺐던 1,170칸은 585칸이 auto-na, 나머지는 코드 근거
  (`follows_guidelines`)로 바로 판정됐다. 서버·스키마 코드처럼 가이드라인 적용 범위 밖이 명백한 묶음은 경로로 한 번에 「해당 없음」 처리해도 된다(이유 필수).
- 0행인 작업표는 지운다(그 단계는 건너뛴다).
- `relation-cands --round-dir $R` — 같은 라운드의 L·C·D·S 가 이미 채우기로 정한 칸을 후보에서 뺀다(KLID: 2,780칸 중 301칸 낭비). 그래서 **판정(fill·fill-fields)이 끝난 뒤** 뽑는다.
- **모으기가 끝나면 규모를 본다** — `python3 scripts/oneshot.py scale --dir $R` 가 단계별 행 수·판정 에이전트 수 추정을 표로 낸다.
  합계가 20(동시 실행 한도)을 크게 넘으면 **시작 게이트에서** 이번 라운드 범위를 고르게 한다(예: H·T 는 다음 라운드, E 는 핵심 타입만).
  KLID 실측: 판정 47개 · 경위 문단 304만 자 — 사람이 즉석에서 범위를 정해야 했다.

### 판정 fan-out — 한 메시지에 전부 띄운다
| 단계 | 나누는 단위 | 에이전트 출력 | 검사 |
|---|---|---|---|
| L 산문 이관 · D 코드 | 작으면 한 에이전트 | `refs/judged.json` · `code/judged.json` | 에이전트가 `fill` · `fill-fields` 까지 |
| C · S | 항목 단위 | `…/judged.json` | `fill-fields` |
| E 관계 | 후보 약 200개씩 | `rel/judged-<k>.json` | 메인이 합쳐 `relation-fill` 한 번(같은 파일 동시 쓰기 금지) |
| H 경위 + T 슬림화 | 문단 약 8만 자씩, **같은 항목을 한 에이전트가 두 판정 모두** | `hist/judged/judged-<k>.json` · `slim/parts/slim-<k>.json` | 메인이 slim 조각을 합쳐 `slim/proposals.json` |
| V 증적 | H 판정 뒤 `evidence-cands` → 한 에이전트 | `ev/judged.json` | — |
- ★ **판정 프롬프트는 `references/judging-prompt.md` 의 공통 머리말을 그대로 붙인다** — 손으로 쓰면 묶음마다 기준이 갈린다.
  KLID 상용: 같은 칸을 세 에이전트가 나눴는데 채움률이 27%·100%·90%(정규식 추출기·커밋 해시 근거). 스크립트 검사는 셋 다 통과했다.
  회수 때 「전부 정독 N행」 보고와 임시 폴더의 판정 생성기 흔적을 확인한다.
- 판정 지침은 각각 `references/classification.md`·`code-judging.md`·`relation-judging.md`·`history-judging.md`·`evidence-judging.md`.
- ☠️ **동시 실행 한도 20** — 큰 프로젝트(MindLog: 판정 29개)는 한 번에 다 못 띄운다. 20개를 먼저 띄우고, 끝나는 대로 남은 배치(보통 H·T)를 이어 띄운다. 배치를 더 크게 잡아 20개 안에 맞추는 것도 방법이다(관계 ~300·문단 ~12만 자).
- 판정 출력은 **JSON 배열**이어야 한다 — 가끔 `{"judged": [...]}` 로 감싸 오므로 병합 전에 벗긴다(MindLog 실측: 6개 중 1개). 프롬프트에 「배열로, 객체로 감싸지 말 것」을 적는다.
- ☠️ 판정 에이전트 프롬프트에 **전용 임시 폴더**(예: `$R/tmp/<에이전트 번호>/`)를 준다 — 공용 scratchpad 를 같이 쓰면 병렬 에이전트끼리 덤프 파일을 덮어쓴다(NexusSystem 실측).
- 슬림화 판정: 경위로 빼는 문단 안의 문장은 고르지 않는다(겹침 방지). 삭제 문장은 원문 그대로·옮겨 간 칸이 **지금** 채워져 있어야 한다.

### 통합 검토 문서 — 자세해야 한다 (중간에 멈추는 곳이 없으므로)
`python3 scripts/oneshot.py review-all --dir $R --diagnose $D/diagnose.json --server <서버> --project <id>`
- 담기는 것: 한눈에 표(단계별 적용 줄·대상 항목·뺀 것·하위 재검토 표시 상한 추정) · **눈여겨볼 것**(스크립트가 뽑는다 — 묶음별 채움률 편차 ·
  🚧 가드 행 일괄 사유 · 코드에서 채운 역할 칸 · 목록 밖 관계 제안) · 자동 해당 없음 칸 · 본문 충돌 · **단계별 모든 줄** · 적용 순서 · 멈추는 조건.
- 줄이 400개를 넘으면 단계별 상세를 `REVIEW-<단계>.md` 로 나누고 `REVIEW.md` 는 요약본이 된다(KLID: 한 파일 2.2MB 는 사람이 못 본다).
  사람에게는 요약본과 「눈여겨볼 것」부터 보여 준다.
- 장부의 «해당 없음»으로 닫히는 것은 **auto-na 뿐**이다. 관계 후보가 전부 「아님」이었던 칸은 닫지 않는다 — E 를 적용하면 후보별 「아님」만 장부에 남고, E 를 기각하면 아무것도 남지 않는다(KLID: E 를 뺐는데 404칸이 영구 해당 없음이 될 뻔했다).
- 사용자에게는 문서 경로와 **한눈에 표 + 눈여겨볼 점**(본문 충돌·목록 밖 제안·구조 편집이라 번질 수 있는 것)을 대화로 요약해 준다.
- 사용자가 뺄 줄을 말하면: `oneshot.py reject --dir $R --ids E-0012,H-0003` · 단계 통째 `--stages T` · 칸 통째 `--field based_on_adrs --field-stage E`.

### 일괄 적용
`python3 scripts/oneshot.py apply-all --dir $R --server <서버> --project <id> --diagnose $D/diagnose.json --ledger <장부>` (`--dry` 로 계획만)
- 순서 L → C → D → S → E → V → H → T. 단계마다 대상을 **그 순간 새로 떠서** 계획한다(앞 단계와 버전 충돌 없음).
- 버전 충돌은 그 단계 나머지를 한 번 다시 떠서 재계획 · 산문이 이미 바뀌어 삭제 문장이 없으면 그 줄만 건너뜀.
- **멈추는 경우**: 서버 거부(권한·스키마) · 되살린 재검토 표시가 원래와 다름 · 최종값이 계획과 다름 → `REPORT.md` 에 원인·로그.
- 끝나면 재진단(`diagnose --refresh`)·`progress` 로 전후 비교해 ③ 보고.
- 진행은 `apply/run.log` 와 화면에 줄마다 흐른다(「⏳ 묶음 n/N · 누적」). 적용 로그는 줄 버퍼라 바로 읽힌다(KLID: 10분 넘게 0바이트였다).

아래 Phase 절은 **각 단계의 판정 기준·함정**이다(한 번에 모드에서도 판정 에이전트가 따른다). 개별 실행 명령도 남겨 둔다.

## 원칙 — 먼저 읽어라

1. **추정 금지.** 값은 **그 항목의 산문에 근거가 있을 때만** 채운다. 근거 인용이 산문에 글자 그대로
   없으면 스크립트가 거부한다. 근거가 없으면 「안내」로 돌려 담당자에게 묻는다.
   **유일한 예외 = 재료 E(관계 초안, Phase 1.8)** — 근거 대신 «제안 + 이유»를 내고, **자동 적용 없이** 사람이
   줄마다 채택한 것만 적용한다. 채택하지 않은 제안은 한 칸도 쓰지 않는다.
2. **빈 칸만 채운다.** 이미 값이 있는 칸은 덮지 않는다(예외: 담당자 문자열 → `{kind,name}` 승격).
3. **순서는 연결 → 구조·담당자 → 슬림화.** 산문을 줄이는 건 **맨 마지막**이다 — 칸이 확정되기 전에
   산문을 지우면 되돌릴 근거가 사라진다.
4. **슬림화는 보수적으로** — **삭제만** 한다(고쳐 쓰기 금지). 지우는 문장마다 옮겨 간 칸을 적고,
   그 칸이 실제로 채워져 있어야 한다. 「왜」·배경·주의 문장은 칸으로 옮겨지지 않았으므로 남는다.
5. **쓰기는 통합 검토 문서 확정 뒤.** 사람 게이트는 시작·통합 검토 문서·끝 보고 **세 번뿐**이다. 단계마다·타입마다 멈춰 묻지 마라 —
   상용 Self 첫 적용(2026-09-28~30)에서 단계·라운드마다 확인을 받다 사흘이 걸렸고, 확인이 판단을 바꾼 적이 거의 없었다.
   안전은 사람의 분할 검토가 아니라 스크립트 검사(인용 대조·지어낸 ID 거부·재검토 표시 전후 비교·자동 복원·최종값 대조)가 맡는다.
6. **세는 건 스크립트가.** 보고의 숫자는 스크립트 출력을 그대로 옮긴다.

## 준비

**서버와 프로젝트를 «말로» 확정한다.** 설정엔 보통 상용(`logicraft`)과 개발(`logicraft-dev`)이 함께 있다.
기본값은 없다 — 이후 모든 명령에 같은 `--server` 를 넘기고 도중에 바꾸지 마라.
☠️ 스크립트는 `~/.claude.json` 과 **현재 폴더에서 위로 올라가며** `.mcp.json` 을 찾는다.
   키는 서버 항목의 `env`(AUTH_TOKEN 등) · `args` 의 `Authorization: …` · **HTTP 형식 등록의 `headers.Authorization`** 어디에 있어도 읽는다(0.9.1).
프로젝트 전용 서버 설정이면 **그 프로젝트 폴더에서** 실행해야 찾는다.

```
작업 폴더  ./.schema-fill/<프로젝트-slug>/            ← 여러 번에 걸쳐 이어서 한다. 날짜 폴더를 만들지 마라
  ledger.json             판정 장부 — 「해당 없음」은 다음부터 안 묻는다
  diag-<YYYYMMDD>/        진단 (diagnose.md · diagnose.json · snap/)
  refs-<N>/               연결 칸 라운드 (prose_migrate.py 산출물)
  fields-<N>/             구조·담당자 라운드
  slim-<N>/               슬림화 라운드
  rel-<N>/                관계 초안 라운드 (cands.json · judged.json · review.md · decisions.json · plan.json)
  guide/                  담당자 안내표 · 답변
```

```bash
PM=~/.claude/skills/mc-logi-schema-fill/scripts/prose_migrate.py   # 연결 칸
SF=~/.claude/skills/mc-logi-schema-fill/scripts/schema_fill.py     # 나머지 전부
```

## Phase 0 — 진단 (읽기만)

```bash
python3 $PM preflight --server <서버> --project <id>
python3 $PM scan      --server <서버> --project <id> --out <폴더>/diag-<날짜>/scan.json
python3 $SF diagnose  --server <서버> --project <id> --out-dir <폴더>/diag-<날짜> --scan <폴더>/diag-<날짜>/scan.json
```

`diagnose.md` 를 사용자에게 보여 준다. 읽는 법을 함께 설명하라:

| 종류 | 「빈칸」의 뜻 | 할 일 |
|---|---|---|
| **연결** | 대부분 **비어 있는 게 정상**이다(모든 API 가 ADR 을 따르진 않는다) | **「산문에 ID 있음」 열만** 작업 대상 → Phase 1 |
| **구조** | 채울 수 있는지 산문을 읽어 봐야 안다 | Phase 2 |
| **담당자** | 「문자열」= 종류 미표시 | Phase 2 (같은 절차) |
| 서버에 없음 | 이 서버가 아직 배포 전 | **여기서 멈춘다** — 채울 수 없다 |
| 🔒 쓰기 불가 타입 | 이 키의 역할에 그 타입 쓰기 권한이 없다 | **여기서 멈추고 알린다** — 담당자 키로 실행하거나 권한을 받아 온다 |

☠️ 권한은 **진단에서** 확인한다. 적용 단계에서 처음 알면 분류·검토가 통째로 버려진다
(CudoCall 실측 — 49칸을 준비한 뒤 첫 쓰기에서 `E_AUTH_FORBIDDEN`, 프로젝트 전체가 읽기 전용이었다).

☠️ 연결 칸의 「빈칸」 총수(수천)를 할 일로 보고하지 마라. **산문에 근거가 있는 것만** 할 일이다.
근거 없이 관계를 짐작해 채우면 틀린 연결이 생긴다.

라운드를 나누지 않는다 — 대상 전부를 한 번에 모은다(아래 「한 번에 진행」).

### 순서 정하기 — 코드가 있나?
사용자에게 **이 프로젝트의 코드 레포(로컬 경로)** 가 있는지 묻는다.

| 코드 | 순서 |
|---|---|
| **있다**(구현된·brownfield) | **Phase 1.7(재료 D — 코드)** 로 «구현 사실» 칸 먼저 → Phase 1(산문 이관)·1.5 → Phase 2 → 1.8(관계 초안) |
| 없다(설계 먼저) | Phase 1 → 1.5 → 2 → 1.8(관계 초안) |

1.8 은 **근거로 채우는 단계를 다 돈 뒤**다 — 근거 있는 관계가 먼저 들어가야 그래프 후보가 좋아지고, 사람이 검토할 줄이 준다.

왜: 구현 사실 칸(API 가 어느 테이블을 읽나·어느 권한을 요구하나)은 **코드가 진실원**이고 산문은 낡을 수 있다.
그리고 산문에 ID 가 없는 항목은 산문 이관으로는 영영 안 채워진다(상용 Self 실측: 연결 칸이 전부 빈 항목 1,218/1,524).
설계 의도 칸(based_on_adrs·implements_requirements 등)은 코드에 없으니 산문(Phase 1·1.5)이 맡고, 산문에도 없으면 관계 초안(Phase 1.8)이 제안한다.

## Phase 1 — 연결 칸 (산문 속 ID → 포인터 칸)

`references/classification.md` 를 먼저 읽는다. 산문 속 ID 의 약 17%는 관계가 아니다
(예시·비유·「연결 안 했다」 선언·폐기 항목·다른 프로젝트 번호).

```bash
python3 $PM snapshot --server <서버> --project <id> --from-scan <scan.json> --dir <R>/snap-before
python3 $PM draft    --scan <scan.json> --snapshot-dir <R>/snap-before --out <R>/decisions.json
#   ↓ 에이전트가 각 행의 context 를 읽고 부류를 정해 JSON 으로 → fill
python3 $PM fill      --decisions <R>/decisions.json --input <판정.json>
python3 $PM review-md --decisions <R>/decisions.json --out <R>/review.md
```
판정 JSON: `[{"key": "...", "kind": "이관|다른 항목의 사례|선례·비유 인용|경계 선언|쓰지 않게 된 이력|폐기 항목|측정 표본|목업 라벨|형제 프로젝트 번호|보류", "reason": "..."}]`
판단 질문 하나 — **「그 대상이 내일 바뀌면 이 항목을 다시 열어 봐야 하나?」** 예면 이관.
부정어(「별도」「미연결」「범위 외」)를 놓치지 마라. 확신이 없으면 보류. 제외·보류는 핵심 구절 인용이 사유다.

🚧 **경계·선례 가드** — `draft`·`derive` 가 ID 주변에서 두 신호를 찾아 행에 `guard` 로 붙인다:
**같은 문장**의 경계·선례 문구(「범위 밖」「손대지 않」「무관」「패턴」「선례」…) · ID 가 속한 **절 제목**의
잔여·미해결·후속·제외·범위 밖 류(「## 잔여」「### 해소되지 않은 것」「책임 제외:」). `guard` 가 붙은 행을
**이관·채움**으로 판정하려면 «왜 그래도 관계인지» `reason` 이 **필수**다 — 사유에는 그 행 문맥의 **원문 조각을 「」로 6자 이상 인용**해야 하고
(줄였으면 …), 같은 사유 문장이 가드 행 5개 이상에 반복되면 `fill`·`fill-fields` 가 거부한다.
(KLID 상용: 가드 이관 194행 중 22행이 공통 문구 — 가드가 형식만 남았다. `fill --snapshot-dir <스냅샷>` 을 주면 발췌 밖 원문 인용도 받는다.)
자동 보류가 아니다(진짜 관계를 잃지 않게). 검토표에는 🚧 로 표시된다.
- 왜: KLID 링크 정밀도 표본 100건을 3개 모델(codex·antigravity·GLM)이 교차 판정했더니, 다수가 «틀림»이라 한
  4건이 **전부** 이 신호가 붙은 행이었다(부류는 기준에 이미 있었는데 판정자가 흘려보냈다).
- 교정: 같은 표본에서 틀린 4/4 검출 · 전원이 맞다고 한 85건 중 경고 1 · 교정에 안 쓴 1,357건에서 경고율 6.3%.
- ☠️ 이력 낱말(폐기·대체·이전)은 신호에 넣지 않았다 — 폐기 «결정»을 서술한 ADR 에서 맞는 행 7건에 울렸다.

(한 번에 모드: 개별 검토표 대신 통합 검토 문서의 [L] 절로 들어간다.)

```bash
python3 $PM plan   --decisions <R>/decisions.json --snapshot-dir <R>/snap-before --schemas <diag>/diagnose.json --out <R>/plan.json
```
→ 적용·검증은 **공통 절차**(아래). 연결 칸 검증에는 재스캔 대조가 더 붙는다:
```bash
python3 $PM scan   --server <서버> --project <id> --out <R>/rescan.json
python3 $PM verify --plan <R>/plan.json --decisions <R>/decisions.json --rescan <R>/rescan.json --after-dir <R>/snap-after --out <R>/verify.md
```

## Phase 1.5 — 저장 경고가 못 보는 산문 (재료 C · 판정 필요)

저장 경고(`*_IN_PROSE`)·`scan_prose_refs` 는 «자기 산문 → 자기 칸»만 본다. 그 밖의 세 자리를 `derive --prose` 가 후보로 낸다:
```bash
python3 $SF derive --diagnose <diag>/diagnose.json --ledger <폴더>/ledger.json --prose --scan <최신 scan.json> --out <R>/worklist.json
```
| 재료 | 무엇 | 실측(CudoCall 상용 복사본) |
|---|---|---|
| **C1 역방향** | A 의 산문이 B 를 적었는데 칸은 **B 쪽**에 있다 — 요구사항 「근거: DFEAT-002/004 · API-017~019」 → DFEAT·API 의 `implements_requirements` | 94칸 — dev 41프로젝트 93건이 전부 비어 있었다 |
| **C2 규칙 밖** | 경고 규칙이 **일부러 없는** 칸(`references/new-fields.json` 의 `unruled_pointer_fields`) — ADR→ADR `based_on_adrs` · 상수→상수 `uses_constants` | 21칸 |
| **C3 「영향 ITEM:」** | 위험·사고 요약의 명시 목록 → 같은 항목의 `affects`(이미 값이 있어도 덧붙인다) | 19칸 |

- 범위 표기(「DFEAT-020/021」·「API-031~045」)를 펼친다(50개 이하).
- ☠️ **C2(ADR→ADR)는 절반 이상이 관계가 아니다** — 실측 19칸 중 11칸 제외·보류:
  **후속 결과**(「그래서 coturn 으로 갔다(ADR-002)」 → 방향 반대) · **다른 프로젝트 번호**(「AOS ADR-017/018」) ·
  **경계**(「ADR-007 이라 영향 없다」) · **대체**(「붙였다가 되돌렸다」 → `supersedes` 칸 후보). 「이 결정이 그 결정 **위에 선다**」만 채움.
- C1 은 같은 타입끼리·구현 기록 쪽 칸으로는 뒤집지 않는다(방향이 틀어진다).
- 판정·검토·적용·검증은 Phase 2 와 같다(`fill-fields` → `review-fields` → `plan-fields` → 공통 절차).

## Phase 1.7 — 구현 사실 칸 (재료 D · 코드 근거)

코드 레포가 있을 때만. `references/code-judging.md` 를 **먼저 읽는다**(대상 칸·코드에서 무엇을 보나·함정).
```bash
python3 $SF code-worklist --diagnose <diag>/diagnose.json --repo <레포 경로> --ledger <폴더>/ledger.json [--type api_endpoint] [--limit 50] --out <D>/worklist.json
#   ↓ 판정 에이전트가 행마다 코드를 읽고 판정 → <D>/판정.json  (값 = 실재하는 ID, 근거 = `코드: 경로:줄 — 조각`)
python3 $SF fill-fields   --worklist <D>/worklist.json --input <판정.json> --ledger <폴더>/ledger.json
python3 $SF review-fields --worklist <D>/worklist.json --out <D>/review.md
python3 $SF plan-fields   --worklist <D>/worklist.json --out <D>/plan.json [--partial]
```
- `fill-fields` 가 `코드:` 근거의 **파일·줄이 실재하고 그 줄 ±3 안에 조각이 글자 그대로** 있는지 검사한다 — 지어낸 경로·심볼은 전체 거부.
- 산문과 코드가 다르면 코드를 따르고 `note` 에 「산문 불일치」 — 검토표에서 따로 보여 준다(설계가 낡은 곳).
- ☠️ 코드 근거 값은 **산문 복사가 아니다** — 서버가 새 관계로 보고 하위 항목에 재검토 표시를 붙인다. 실제로 관계가 생긴 것이라 정상.
  적용은 `apply --probe --allow-dependents --restore-self` — 하위 표시는 기록만 하고, 새 값을 넣어 **자기** 재검토 표시가
  풀리면(이미 재검토 필요 상태였던 항목 — 새 값은 «실제 변경»이라 자동 해제된다) 그 묶음 직전 시각 기준으로
  `restore_review_needed` 를 돌려 되살린 뒤 원상과 같은지 확인하고 계속한다(다르면 멈춤). 상용 Self 시험: API 9개 중 2개가 해당.
- 통합 검토 문서의 [D] 절로 들어간다.

## Phase 1.8 — 관계 초안 (재료 E · 제안 → 사람 채택)

근거로 채우는 단계(1·1.5·1.7·2)를 다 돈 뒤에도 **빈 연결 칸**이 대상이다. `references/relation-judging.md` 를 **먼저 읽는다.**
시작 전에 사용자에게 다시 한 번 말한다: **「이건 AI 의 제안입니다. 채택하신 줄만 들어갑니다.」**

```bash
python3 $SF relation-cands  --diagnose <diag>/diagnose.json --server <서버> --ledger <폴더>/ledger.json \
                            [--type screen_spec,use_case,acceptance] [--field based_on_adrs] [--limit 100] --out <R>/cands.json
#   ↓ 판정 에이전트가 행마다 «이 항목»과 «후보»를 읽고 판정 → <R>/judged.json  (제안 | 아님 | 보류 + reason)
python3 $SF relation-fill   --worklist <R>/cands.json --input <R>/judged.json
python3 $SF relation-review --worklist <R>/cands.json --out <R>/review.md --decisions <R>/decisions.json
#   🚦 사람이 review.md 를 보고 decisions.json 의 줄마다 decision = 채택 | 기각 | (비움)
python3 $SF relation-plan   --worklist <R>/cands.json --decisions <R>/decisions.json --ledger <폴더>/ledger.json --out <R>/plan.json
```
→ 적용·검증은 **공통 절차**(`apply --probe --allow-dependents --restore-self` → `check`).

**후보는 어떻게 뽑나** (`relation-cands` — 결정적)
| 신호 | 가중 |
|---|---|
| 두 항목이 이미 서로 언급(산문 밖 칸) | 강 |
| 그래프 2홉 — 이 항목과 연결된 X 가 후보와도 연결 | 중 · **허브(연결 많은 X)면 약하게** |
| 그래프 3홉 · 같은 도메인 · 드문 낱말 겹침 | 약 |

경유지 감쇠(rel-1 기각 사례에서): **허브** · **대상과 같은 타입의 경유지**(ADR→ADR 은 선례·형제 결정을 끌고 온다) ·
**같은 타입 형제가 함께 쓰는 경유지**(여러 화면이 공유하는 API) 를 거친 경로는 약하게 센다. 칸마다 1위 점수의 절반
(`--rel-cutoff 0.5`) 미만 후보는 버린다. ☠️ 그래도 **점수는 정답을 가르지 못한다** — 시범에서 오답을 더 줄이려고 기준을 조이면
정답부터 빠졌다(최저점 2.0: 정답 37→26). 후보는 넓게, 거르는 건 판정과 사람이다.

- 대상 칸 = 연결 칸 중 **빈칸**. 산문에 ID 가 있는 칸(Phase 1 의 몫)·구현 사실 칸(Phase 1.7 의 몫)은 기본 제외(`--include-prose`·`--include-code-facts`).
- 후보는 **실재·미폐기 항목만**. 스냅샷에 없는 타입(FEAT 같은 다리 항목 포함)은 `--server` 로 받아 `<diag>/pool/` 에 캐시한다.
- 경유지는 실재 항목만 — CO 번호·해시처럼 항목이 아닌 번호를 거친 경로는 버린다(같은 CO 에 적혔을 뿐 설계 관계가 아니다).
- 장부의 기각·아님 후보, 「해당 없음」 칸은 다시 뽑지 않는다.

**검사** (`relation-fill`·`relation-plan` — 하나라도 어기면 전체 거부)
- 대상 ID 가 칸이 받는 접두(예: `ADR-`)이고 **프로젝트에 실재**한다 — 지어낸 ID 차단.
- `reason` 10자 이상 — 사람은 이 문장만 보고 정한다.
- 값 하나만 받는 칸에 둘 이상 채택 금지.
- 채택분의 근거는 `담당자 확정: 관계 초안 채택 — <이유>`, 변경 요약에 「AI 가 제안한 관계를 담당자가 검토해 채택했다」가 남는다.

**운영**
- 실측(상용 Self rel-1 · 화면 51칸): 후보 98 → AI 제안 37(38%) + 목록 밖 9 → 사람이 46줄 전부 채택 → 34항목 36칸 적용.
- 전 타입을 한 번에 뽑아 **판정 에이전트 여럿에 병렬**로 나눈다(후보 약 200개씩). 결과는 통합 검토 문서의 [E] 절 — 항목별로 묶어 이유와 함께 보인다.
- 참고로 채택률이 낮은 칸(< 30%)은 다음부터 후보를 뽑지 않고 「직접 채우기」로 안내하는 게 낫다 —
  채택률이 낮으면(< 30%) 그 타입·칸은 제안을 멈추고 「직접 채우기」로 넘긴다 — 사람 시간을 오답 기각에 쓰게 하지 마라.
- 새 관계라 하위 항목에 재검토 표시가 붙는 것은 **예상 동작**이다(`--allow-dependents`).
- ☠️ 판정 에이전트에게 «점수가 높으니 제안» 을 허용하지 마라. 상용 Self 시험: 허브 경유 후보(ADR-025→REQ-012)가
  서로 무관한 화면·수용기준 셋의 1순위로 떴다 — 본문을 읽으면 전부 아님이다.

## Phase 2 — 구조 칸 · 담당자 종류

```bash
python3 $SF worklist --diagnose <diag>/diagnose.json --ledger <폴더>/ledger.json [--type migration_plan] --out <F>/worklist.json
```
작업표의 각 행에 칸 설명(`field_help`)·값 모양(`field_schema`)이 있다. 항목 원문은 `<diag>/snap/<ID>.json`.
**항목 단위로** 원문을 읽고, 그 항목의 빈 칸들을 한 번에 판정한다:

| 판정 | 언제 | 필수 |
|---|---|---|
| **채움** | 산문(또는 다른 칸)에 **그 값이 적혀 있다** | `value`(스키마 모양 그대로) + `basis`(원문 인용, 여러 조각은 ` … ` 로 이음) |
| **안내** | 칸이 이 항목에 해당하는데 **근거가 없다** | `reason` — 왜 못 채웠나 + **담당자가 어디서 찾을 수 있나** |
| **해당 없음** | 이 항목엔 의미가 없는 칸(예: `in_place` 이행의 `transition`) | `reason` — 장부에 남아 다음부터 안 묻는다 |
| **보류** | 판단이 서지 않는다 | `reason` |

```bash
python3 $SF fill-fields   --worklist <F>/worklist.json --input <판정.json> --ledger <폴더>/ledger.json
python3 $SF review-fields --worklist <F>/worklist.json --out <F>/review.md
```
- ☠️ **「안내」·「보류」로 보내기 전에 반드시 원문을 읽는다.** 작업표 각 행의 `hints` 는 그 칸과 관련된
  단어가 든 문장 후보다 — **판정이 아니라 읽을 거리**다. 정규식으로 걸러서 안내·보류로 보내지 마라.
  (CudoCall 실측: 정규식으로 거른 IMPREC `evidence` 9건 중 6건이 「산문에 없다」로 오판 — 담당자에게
  이미 적혀 있는 것을 다시 적으라고 안내할 뻔했다. 읽고 재판정하니 96칸 중 56칸이 채움이었다.)
  반대로 단서 문장이 있어도 **그 칸의 뜻이 아닐 수 있다** — 담당자 칸의 「관리·운영」 단서는 대부분 담당 표시가 아니었다.
- 사람이 발견한 사고는 탐지 시각 = 인지 시각이다(자동 탐지가 아니므로). 완화 단계 없이 바로 해결된 사고의
  `mitigated_at` 은 「해당 없음」이다. 모를 가능성이 큰 칸(오래된 사고의 발생 시각)은 판정에 `"optional": true` 를 붙여
  안내표의 「아시면만」 절로 보낸다.
- `fill-fields` 는 **근거 인용이 원문에 없으면 전체를 거부**한다(하나라도 틀리면 아무것도 안 씀). 거부되면
  그 값은 지어낸 것이다 → 「안내」로 바꿔라. 인용을 고쳐서 통과시키려 하지 마라.
- ☠️ 인용 대조는 **「그 문장이 원문에 있다」**만 보장한다. 값이 그 문장을 **맞게 옮겼는지**는
  사람이 본다 — 검토표에서 값과 근거를 나란히 보여 주는 이유다.
- **담당이 여럿이면 배열로** 적는다(CO-175 · 서버가 이 모양을 알아야 한다 — 모르면 적용 단계에서 거부되니 보류).
  `[{"kind":"team","name":"SERVER 세션","duty":"스크립트 작성"},{"kind":"person","name":"사용자","duty":"승인·실행","lead":true}]`
  - `duty`(맡은 일)는 **원문에 적힌 말 그대로**(괄호 속 「스크립트 작성」·「승인·실행」 등). 원문에 없으면 비운다.
  - ☠️ **`lead`(최종 책임자)를 추정하지 마라.** 원문이 「총괄」·「주 담당」·「책임」처럼 **명시할 때만** 붙인다.
    「A · B」처럼 나열만 돼 있으면 lead 없이 둔다 — 순서는 책임을 뜻하지 않는다.
  - ☠️ 구분자(`+`·`/`·`·`)만 보고 여럿으로 판정하지 마라 — `U+맞춤공지`(제품명)·`보안·플랫폼팀`(팀 이름)처럼 한 주체인 경우가
    실측 167칸 중 73칸이었다. **읽고** 주체가 둘 이상일 때만 배열이다.
  - 「사용자 판단 필요 + SERVER 세션」처럼 미정 표시가 섞이면 미정 부분은 원소로 만들지 않는다.
- 담당자는 반드시 `{"kind": "team|org|role|person", "name": "…"}`. 원래 문자열을 보고 종류를
  판단할 수 있으면 채움(근거 = 원래 문자열), 사람 이름인지 팀 이름인지 모르겠으면 안내.
- ☠️ **`evidence` 칸(수용기준·구현기록)은 Phase 3.6 과 같은 지침**(`references/evidence-judging.md`)으로 판정한다 —
  `reference` 는 **다시 찾아갈 위치만**(spec·테스트 이름·파일 경로·커밋 해시·CO 번호), `result` 는 결과 낱말이 든
  `result_quote` 가 있어야 한다. `fill-fields` 가 설명문 reference 를 거부한다(CatchAll 실측: 17칸 전부
  「테스트로 각 흐름 검증(…). test SUCCEEDED.」 같은 문장이 reference 에 들어갔다). `result_quote` 는 검사 후 떼어 낸다.
- 흔한 근거 위치: 이행 단계 = `forward_ddl`·`post_steps`·산문 「단계」 목록 / 사고 시각 = 산문의
  「HH:MM 인지·조치」 / 구현 근거(`evidence`) = IMPREC notes 의 「테스트 N건」「커밋 abc123」「코드 경로」.

(한 번에 모드: 통합 검토 문서의 [S] 절.) 개별 실행 시:
```bash
python3 $SF plan-fields --worklist <F>/worklist.json --out <F>/plan.json   # 미판정이 남았으면 --partial
```
→ **공통 절차**로 적용 · 검증(`$SF check`).

## Phase 3 — 산문 슬림화 (보수)

**Phase 1·2 가 적용·검증된 뒤에만** 한다. 먼저 현재 상태를 새로 뜬다(슬림화는 «채운 뒤»의 값을 기준으로 판단한다):
```bash
python3 $PM snapshot --server <서버> --project <id> --ids <이번 라운드에 채운 항목> --dir <S>/snap-before
```
에이전트가 항목마다 **칸으로 옮겨진 것과 같은 내용을 말하는 문장**만 고른다:
```json
[{"item_id": "MIG-006", "path": "description",
  "remove": [{"text": "<원문 그대로 — 한 글자도 바꾸지 말 것>", "moved_to": "steps"}]}]
```
남기는 것: 「왜」·배경·주의(⚠️)·경고·결정의 이유 — 칸이 담지 못하는 것은 **전부** 남긴다.
지우는 것: 칸에 그대로 들어간 **사실 나열**(단계 목록, 시각, 참조 번호 나열, 「LogiCraft: ERD-006 · API-046」 같은 추적 줄).

```bash
python3 $SF slim-plan --proposals <제안.json> --snapshot-dir <S>/snap-before --server-name <서버> --project <id> \
                      --out <S>/plan.json --diff <S>/diff.md
```
스크립트가 거부하는 것: 원문에 정확히 한 번 있지 않은 문장 · 옮겨 갔다는 칸이 비어 있음 · 원문의 절반 넘게 삭제.
통합 검토 문서의 [T] 절에 삭제할 문장이 전부 나온다. 적용 시점에 옮겨 간 칸이 비어 있으면 그 줄만 자동으로 건너뛴다(`--skip-bad`).
슬림화는 `change_kind: editorial` 로 저장되어 의존 항목에 재검토 표시를 퍼뜨리지 않는다. 원문은 이전 버전에 남는다.

## Phase 3.5 — 경위 분리 (본문엔 현행만)

본문(description·notes 등)에 섞인 **경위**(결정·정정·검증 기록)를 본문에서 **분리**한다. 지워도 사라지지 않는다 —
원문은 **적용 직전 버전**(항목 버전 이력)에 그대로 있고, 변경 요약에 「원문 vN」을 남겨 항목 상세의 **변경 요약 타임라인**에서 찾아간다.
(☠️ 한때 `history` 칸을 열었다가 철회했다 — CO-179 §8: 버전 이력과 진실원이 겹치고, 경위의 42%인 검증 기록은 `evidence` 가 제자리다.)
```bash
python3 $SF history-paras --snapshot-dir <R>/snap --out <R>/paras.json [--ids <대상 id 목록>]
#   ↓ 판정 에이전트가 묶음별로 문단을 «직접 읽고» 판정 → judged/*.json (지침: references/history-judging.md)
python3 $SF history-plan  --paras <R>/paras.json --judged <R>/judged/*.json --snapshot-dir <R>/snap \
                          --server-name <서버> --project <id> --out <R>/plan.json --guide <R>/owner-guide.md
```
판정 JSON: `[{"pid", "kind": "경위|혼합|현행|본문 충돌", "move": ["<원문 그대로 조각>"], "reason"}]`
- ☠️ **정규식으로 판정하지 마라** — 표본 직독에서 정규식 «경위»의 실제 경위 몫은 30%였다(「ADR-028 v3」 같은 버전·출처 표기가 붙은
  **현행 규칙**을 잡고, 「종전 표기는 해소됐다」 같은 날짜 없는 경위는 놓쳤다).
- **본문 충돌** — 정정 기록이 본문의 옛 서술을 뒤집었는데 본문은 그대로면 분리하지 않는다(경위만 빼면 틀린 규칙이 남는다) → `--guide` 담당자 안내.
- 판정자가 **항목 사이 모순**(다른 항목의 정정과 어긋난 낡은 본문)을 보고하면 모아서 담당자 안내에 붙인다 — KLID 실측 17건.
- 검사: 조각은 문단에 글자 그대로 · `description` 은 분리 뒤 40자 이상 남아야 함 · 다른 칸은 통째로 경위면 **빈 문자열**로
  (☠️ `remove` 는 «키 삭제» = 구조 변경이라 하위로 전파된다 — KLID 실측).
- 후속: 경위 중 **검증·증적 기록(42%)** 을 `acceptance.evidence`·`implementation_record.evidence` 로 옮기는 재료.
- 실측(KLID 2차, 이관 범위 370항목): 문단 1,532 → 경위 176 · 혼합 158 · 현행 1,193 · 본문 충돌 5 → **105항목 52,229자 분리**,
  본문 387,857 → 329,224자(**−15.1%**, 1차 슬림화 포함).

## Phase 3.6 — 검증 기록 → `evidence` (수용기준·구현기록)

경위 중 **검증·증적 기록**(e2e 통과·spec 파일·실측 일시·커밋)은 버전 이력에만 두지 말고 `evidence` 구조 칸으로 옮긴다
(「무엇으로 확인했나」를 갈래·위치·날짜·결과로). `evidence` 칸이 있는 타입은 `acceptance`·`implementation_record` 뿐이다.
```bash
python3 $SF evidence-cands --paras <R>/paras.json --judged <R>/judged/*.json --out <R>/ev/cands.json   # Phase 3.5 판정 재사용
#   ↓ 판정 에이전트 (지침: references/evidence-judging.md) → <R>/ev/judged.json
python3 $SF evidence-plan  --cands <R>/ev/cands.json --judged <R>/ev/judged.json --snapshot-dir <R>/snap \
                           --server-name <서버> --project <id> --out <R>/ev/plan.json
```
- 검사: `reference`·날짜·결과 구절이 조각에 **글자 그대로** 있어야 한다 — 지어낸 값은 거부. 기존 evidence 와 type+reference 가 같으면 건너뛴다.
- `evidence` 는 상태 게이트에 쓰이지 않는 기록 칸이다(검증 상태를 바꾸지 않는다). 다만 추가는 구조 변경이라 **하위로 한 번 전파**된다
  (KLID 실측: 대상 11항목의 1홉 32곳) — 규모가 작아 서버 억제 없이 둔다.
- 순서: Phase 3.6 을 Phase 3.5(경위 분리) **앞에** 적용하면 한 항목에 버전이 둘 생기지 않게 합칠 수도 있다 — 지금은 따로 적용한다.

## Phase 4 — 담당자 안내 (자동으로 못 채우는 칸)

```bash
python3 $SF guide --worklist <F>/worklist.json --out <폴더>/guide/guide.md --answers <폴더>/guide/answers.json
```
`guide.md` 는 **질문 수를 줄이는 것**이 목적이다(CudoCall: 102칸·688줄 → 질문 12개·126줄).
- **A 묶음 질문** — 같은 타입의 담당자 칸이 3개 이상이면 한 번만 묻고 답을 전부에 펼친다(항목별 예외 허용).
  ☠️ 묶음은 담당자 칸만 — 이행 검증 방법처럼 항목마다 답이 다른 칸을 묶으면 한 답이 조용히 복제된다.
- **B 개별 질문** — 나머지.
- **C 아시면만** — `optional` 판정. 모르면 건너뛴다.
담당자에게 전달하고, 한 번에 다 하지 않아도 된다고 알려라. 답이 오면:
```bash
python3 $SF answers --answers <폴더>/guide/answers.json --out <F2>/판정.json
```
→ 새 작업표(`worklist`)에 `fill-fields` 로 넣고 Phase 2 의 검토 → 적용 → 검증을 그대로 탄다
(근거 = `담당자: 답변` 이라 인용 대조는 건너뛴다. 대신 사람 검토 게이트는 그대로다).

## 공통 절차 — 적용 · 검증

모든 계획(plan.json)은 같은 적용기를 쓴다. 한 번에 모드에서는 `oneshot.py apply-all` 이 아래를 단계마다 자동으로 돈다. 개별 실행 시:
```bash
python3 $PM apply --server <서버> --plan <plan.json> --log <apply.log.jsonl> --limit 5 --dry   # 예행 → 보여 주고 승인
python3 $PM apply --server <서버> --plan <plan.json> --log <apply.log.jsonl> --limit 5         # 시범 5건
python3 $PM snapshot --server <서버> --project <id> --ids <시범 id> --dir <snap-after>
python3 $SF check --plan <plan.json> --after-dir <snap-after> --only <시범 id>                # 최종값 == 계획값
#   합격 보고 → 승인 → 나머지
python3 $PM apply --server <서버> --plan <plan.json> --log <apply.log.jsonl> --only <나머지 id>
python3 $PM snapshot --server <서버> --project <id> --from-plan <plan.json> --dir <snap-after>
python3 $SF check --plan <plan.json> --after-dir <snap-after>
```
- ★ **나머지는 `--probe` 로 적용한다**(기본 5항목 묶음). 묶음마다 **적용 항목 자신 + 그것을 가리키는 하위**의 재검토 상태를
  전후로 떠서, 하나라도 바뀌면 그 묶음에서 멈춘다(exit 4).
  ```bash
  python3 $PM apply --server <서버> --plan <plan.json> --log <apply.log.jsonl> --only <나머지 id> --probe [--batch 5] [--allow-dependents]
  ```
  왜: 상용 Self 첫 적용(2026-09-28)에서 dev 더미에 없던 경로가 셋 드러났다 — ① 수정이 **자기** 재검토 표시를 자동 해제(21항목·47행, CO-189)
  ② 칸 하나 채우기가 겉 제목을 바꿈(CO-190) ③ 슬래시 축약형 `SVC-009/010/013` 을 산문 근거로 못 읽음(CO-191). 셋 다 검산(check)은 통과했다 — 전후 비교만 잡았다.
  - 멈췄을 때 **자기 표시가 풀린 항목**은 원인을 확인한 뒤 `restore_review_needed`(project_id·item_ids·since=묶음 직전 시각, **dry_run 먼저**)로 원래 행 그대로 복원한다. 수동 표시(`mark_review_needed`)로 대신하지 마라 — 원인·시각이 복원되지 않는다.
  - **하위에 새 표시**가 붙었으면 그 값이 «산문 복사»로 인정되지 않았다는 뜻이다(판정자가 새로 구성한 구조 값·마크다운을 벗긴 문장·여러 조각을 이은 문장). 원문 **글자 그대로** 넣거나 그 칸은 보류한다. 재료 D 처럼 새 관계가 예상 동작이면 `--allow-dependents`.
- ★ **구조 칸은 적용 전에 «새로 구성한 값»을 가려 둔다** — `server_defaults` 객체·이행 단계처럼 판정자가 산문을 읽고 짠 값은 서버가 산문 복사로 인정 못 해 하위로 번진다(상용 Self 실측: 84항목 중 31항목). 문자열 칸은 근거 인용과 **같은 글자**를 값으로 넣으면 번지지 않는다.
- **첫 실패에서 멈춘다.** `unrecognized_keys` = 서버가 그 칸을 모름(배포 전) → 재시도 말고 보고.
  `E_CONFLICT_VERSION` = 스냅샷 뒤 누가 고쳤다 → 그 항목을 다시 떠서 다시 판단. ☠️ **나 자신**일 때가 많다 — 라운드를 이어 돌리면
  앞 라운드가 같은 항목의 버전을 올려 놓는다(상용 Self: rel-5 뒤 code-3 첫 항목에서 멈춤, 쓰기 0). 라운드마다 대상 항목을 새로 떠서 계획하라.
  `DATA_UNCHANGED_NOOP`·`PATCH_OP_NOOP` = 성공 응답이지만 미반영 → 멈추고 보고.
- ☠️ **SQL 이나 수작업으로 되돌리지 마라.** 되돌릴 땐 `snap-before/` 를 원본으로, 승인 후 `update_item` 으로.

## Phase 5 — 진행 보고

라운드가 끝나면 다시 진단하고 전후를 비교한다:
```bash
python3 $SF diagnose --server <서버> --project <id> --out-dir <폴더>/diag-<오늘> --scan <새 scan.json> --refresh
python3 $SF progress --before <이전 diag>/diagnose.json --after <폴더>/diag-<오늘>/diagnose.json
```
보고 틀:
```
## 새 칸 채우기 — <프로젝트> (<서버>) · 라운드 N
이번에 채운 칸: 연결 a · 구조 b · 담당자 c   (산문 슬림화 d항목, 평균 e자 → f자)
관계 초안: 제안 g줄 → 채택 h · 기각 i · 미결 j   (채택률 h/(h+i))
현재 채움: 연결 x/산문근거 y · 구조 p/q · 담당자 r/s
담당자 안내 대기: k칸 (guide/guide.md) · 해당 없음 장부: m칸 · 보류: n칸
검증: ✅/❌ · 산출물: <폴더>/
```
남은 일은 **다음 라운드 후보**다. 한 번에 끝내려 하지 마라.
