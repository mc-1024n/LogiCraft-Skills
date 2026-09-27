---
name: mc-logi-schema-fill
description: LogiCraft 스키마 개편(«산문을 칸으로», CO-138~171)으로 새로 생긴 칸 — 연결 칸(based_on_adrs·operates_on·related_apis·actor_roles 등 90여 칸), 구조 칸(migration_plan.steps·verification, incident.started_at, implementation_record.evidence, slo.error_budget 등), 담당자 종류(owner → {kind,name}) — 을 프로젝트의 기존 ITEM 마다 채워 넣고, 칸으로 옮겨 간 문장만큼 산문을 줄이는 표준 절차. 진단(채움 현황표) → 연결 칸 이관 → 구조 칸·담당자 채우기 → 산문 슬림화 → 산문에 근거가 없는 칸은 담당자에게 단계별 안내표로 넘기기까지. AI 는 산문에 근거가 있는 값만 채우고(인용을 글자 그대로 대조), 지어낸 값은 기계적으로 거부된다. 사용자가 "새 스키마 채워줘", "추가된 칸 채우기", "스키마 마이그레이션", "산문을 칸으로", "산문 슬림하게", "description 줄이기", "산문 참조 이관", "*_IN_PROSE 경고 정리", "OWNER_KIND_MISSING 정리", "based_on_adrs 채워줘", "우리 프로젝트 새 필드 현황", "/mc-logi-schema-fill" 등을 말하거나, 상용 배포 뒤 기존 항목의 빈 칸·산문 경고를 한꺼번에 정리하려 할 때 반드시 이 스킬을 쓴다. 항목 하나를 손으로 고치는 건 mc-logi-update 가 맞다.
license: MIT
allowed-tools: Read, Write, Edit, Grep, Glob, Bash, ToolSearch, AskUserQuestion, TaskCreate, TaskUpdate, TaskList
metadata:
  version: 0.5.2
  requires: "LogiCraft 서버 main 36be2667 이후(새 칸 + scan_prose_refs + 이관 쓰기 전파 억제 CO-177·178·181~184). 이전 서버에 쓰면 재검토 표시가 대량 전파된다"
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

## 원칙 — 먼저 읽어라

1. **추정 금지.** 값은 **그 항목의 산문에 근거가 있을 때만** 채운다. 근거 인용이 산문에 글자 그대로
   없으면 스크립트가 거부한다. 근거가 없으면 「안내」로 돌려 담당자에게 묻는다.
2. **빈 칸만 채운다.** 이미 값이 있는 칸은 덮지 않는다(예외: 담당자 문자열 → `{kind,name}` 승격).
3. **순서는 연결 → 구조·담당자 → 슬림화.** 산문을 줄이는 건 **맨 마지막**이다 — 칸이 확정되기 전에
   산문을 지우면 되돌릴 근거가 사라진다.
4. **슬림화는 보수적으로** — **삭제만** 한다(고쳐 쓰기 금지). 지우는 문장마다 옮겨 간 칸을 적고,
   그 칸이 실제로 채워져 있어야 한다. 「왜」·배경·주의 문장은 칸으로 옮겨지지 않았으므로 남는다.
5. **쓰기는 전부 사람 승인 뒤.** 분류·값 확정 게이트와 적용 게이트를 건너뛰지 마라.
6. **세는 건 스크립트가.** 보고의 숫자는 스크립트 출력을 그대로 옮긴다.

## 준비

**서버와 프로젝트를 «말로» 확정한다.** 설정엔 보통 상용(`logicraft`)과 개발(`logicraft-dev`)이 함께 있다.
기본값은 없다 — 이후 모든 명령에 같은 `--server` 를 넘기고 도중에 바꾸지 마라.
☠️ 스크립트는 `~/.claude.json` 과 **현재 폴더에서 위로 올라가며** `.mcp.json` 을 찾는다.
프로젝트 전용 서버 설정이면 **그 프로젝트 폴더에서** 실행해야 찾는다.

```
작업 폴더  ./.schema-fill/<프로젝트-slug>/            ← 여러 번에 걸쳐 이어서 한다. 날짜 폴더를 만들지 마라
  ledger.json             판정 장부 — 「해당 없음」은 다음부터 안 묻는다
  diag-<YYYYMMDD>/        진단 (diagnose.md · diagnose.json · snap/)
  refs-<N>/               연결 칸 라운드 (prose_migrate.py 산출물)
  fields-<N>/             구조·담당자 라운드
  slim-<N>/               슬림화 라운드
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

그다음 **계획을 합의**한다: 어느 묶음부터, 한 라운드 몇 칸(권장 100칸 이하 — 사람이 검토할 수 있는 크기).

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
**이관·채움**으로 판정하려면 «왜 그래도 관계인지» `reason` 이 **필수**다 — 없으면 `fill`·`fill-fields` 가 거부한다.
자동 보류가 아니다(진짜 관계를 잃지 않게). 검토표에는 🚧 로 표시된다.
- 왜: KLID 링크 정밀도 표본 100건을 3개 모델(codex·antigravity·GLM)이 교차 판정했더니, 다수가 «틀림»이라 한
  4건이 **전부** 이 신호가 붙은 행이었다(부류는 기준에 이미 있었는데 판정자가 흘려보냈다).
- 교정: 같은 표본에서 틀린 4/4 검출 · 전원이 맞다고 한 85건 중 경고 1 · 교정에 안 쓴 1,357건에서 경고율 6.3%.
- ☠️ 이력 낱말(폐기·대체·이전)은 신호에 넣지 않았다 — 폐기 «결정»을 서술한 ADR 에서 맞는 행 7건에 울렸다.

🚦 **게이트** — `review.md` 로 사람이 확정. 확정 전엔 계획도 안 만든다.

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

🚦 **게이트** — 검토표로 사람이 확정. 그다음:
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
🚦 **게이트** — `diff.md`(전후 전문)를 사용자에게 보여 주고 승인받는다. → **공통 절차**로 적용 · `$SF check`.
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

모든 계획(plan.json)은 같은 적용기를 쓴다. **쓰기다 — 매 단계 사용자 명시 승인 후.**
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
- **첫 실패에서 멈춘다.** `unrecognized_keys` = 서버가 그 칸을 모름(배포 전) → 재시도 말고 보고.
  `E_CONFLICT_VERSION` = 스냅샷 뒤 누가 고쳤다 → 그 항목을 다시 떠서 다시 판단.
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
현재 채움: 연결 x/산문근거 y · 구조 p/q · 담당자 r/s
담당자 안내 대기: k칸 (guide/guide.md) · 해당 없음 장부: m칸 · 보류: n칸
검증: ✅/❌ · 산출물: <폴더>/
```
남은 일은 **다음 라운드 후보**다. 한 번에 끝내려 하지 마라.
