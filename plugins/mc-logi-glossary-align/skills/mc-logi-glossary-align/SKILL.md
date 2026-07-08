---
name: mc-logi-glossary-align
description: ERD ITEM 1건의 전 컬럼을 LogiCraft 4계층 용어사전(도메인→단어→용어)에 정합시키고, 사업 사전 신규 등록 + ERD update_item + cascade 까지 완주하는 오케스트레이터 스킬. 사용자가 "ERD 논리/물리 명칭 용어사전화", "{도메인} 컬럼 표준화", "용어사전 정합" 등을 요청하면 실행. gov→program→domain→word→term 5단계 절차, AI 임의 INSERT 금지, AI 추정 금지, 등록 순서 절대 규칙 강제.
license: MIT
allowed-tools: Read, Write, Edit, Grep, Glob, Bash, Agent, ToolSearch, AskUserQuestion
metadata:
  version: "1.1.0"
  domain: logicraft-glossary
  triggers: 용어사전 정합, ERD 용어사전화, 논리 물리 명칭, 컬럼 표준화, glossary align, gov compliance, program 용어, 단어 등록, 용어 등록
  role: orchestrator
  scope: erd-glossary-alignment
  output-format: 9 md set + ID 매핑표 + cascade 라운드 로그
  related-skills: mc-logi-update, mc-logi-domain-review
  defaults:
    Q1_english_rename: A   # 영문 컬럼 전부 표준 약어 rename
    Q2_abbr_conflict: keep # 약어 충돌 시 기존 유지
    Q3_synonym_policy: ASK # 동의어 정책은 사용자 질의
    Q4_delegation: bulk    # 전체 일괄 위임
    Q5_priority: recommend # 권장 처리 순서
    Q6_klid_bm_conflict: ASK # KLID-BM 표준 충돌 시 사용자 질의
---

# mc-logi-glossary-align — ERD 용어사전 정합 오케스트레이터

ERD 1건의 모든 컬럼(logical_column_name + 물리명)을 LogiCraft 4계층 용어사전에 정합시키는 전 과정을 자동 실행. Session 95 (D001 ERD-005) 실측 절차를 그대로 구현.

## When to Use

- 사용자가 "{도메인} ERD 용어사전화", "ERD-XXX 논리/물리 명칭 정합" 등 명시
- 신규 ERD 도입 후 gov compliance 향상 작업
- 도메인별 일괄 표준화 캠페인 (D001 → D002 → ...)
- ERD에 비표준 영문 (`created_at` 등)과 표준 약어 (`crt_dt` 등) 혼재 발견 시

## When NOT to Use

- ERD 외 ITEM 수정 → `mc-logi-update`
- 도메인 7-dimension 감사 → `mc-logi-domain-review`
- 단어/용어 단건 등록 (사전 작업 없음) → MCP 직접 호출
- 코드 변경 동반 → `mc-logi-update` + 별도 코드 작업

## 절대 불변 규칙 (Top of Mind)

1. **AI 임의 INSERT 금지** — `program_domain_create` / `program_word_create` / `program_glossary_create` 는 후보 제시 → 사용자 명시 승인("등록해" / "박아" / "일괄 위임") 후에만 호출
2. **AI 추정 금지** — cascade patch는 본문 grep으로 실제 인용 확인된 것만. 추정만으로 patch ❌ (확인 안 되면 ack)
3. **등록 순서 절대 규칙** — 도메인 → 단어 → 용어 (의존 방향 역행 불가)
4. **specialist 동시 ≤3건** — 5건 이상 동시 위임 시 소켓 끊김 (Session 95 실측)

## 사용자 사전 결정 디폴트 (질문 생략)

본 스킬은 다음 결정을 **묻지 않고** 디폴트 적용:

| 항목 | 디폴트 | 의미 |
|---|---|---|
| **Q1 영문 rename** | **A** | 비표준 영문(`created_at`)을 gov 표준약어(`crt_dt`)로 전부 rename |
| **Q2 약어 충돌** | **유지** | 동일 en_abbr 의미충돌 시 기존 우선, description에 충돌 명시 |
| **Q4 위임 수준** | **전체 일괄** | 카테고리/건별 분할 없이 일괄 진행 |
| **Q5 우선순위** | **권장 순서** | 메타(C-7) → 운영 메트릭(C-2) → 보안(C-1) → 이벤트(C-6) → 영상(C-3) → 감사(C-5) → 로그(C-4) |

본 스킬이 **반드시 질문**하는 결정:

| 항목 | 질문 시점 | 이유 |
|---|---|---|
| **Q3 동의어 정책** | gov synonym 겹침 검출 시 (예: 송신=전송, 발송=전송) | 의미 보존 여부는 도메인 컨텍스트 의존 |
| **Q6 KLID-BM 표준 충돌** | KLID-BM 표준용어정의서 기존 용어와 en_abbr 불일치 검출 시 | 표준 정합성 vs ERD 일관성 트레이드오프 |

---

## 워크플로우 (5 Phase)

### Phase 0 — 스코프 + 사전 확인

1. **입력 파라미터 확정**:
   - target_erd_id (예: ERD-005)
   - project_id, program_id (사업 ID)
   - domain_id (예: DOMAIN-001)
   - output_dir (예: `./용어 정리/D001/`)

2. **모호하면 AskUserQuestion 1회**: target ERD ID, output 디렉토리 명.

3. **사전 도구 활성 확인**:
   - `program_word_search` 핑 (program_id 만 줘서 limit=1 호출)
   - `program_glossary_search` 핑
   - 실패 시 ToolSearch로 `select:program_word_search,program_glossary_search,gov_compare_erd,program_glossary_compare_erd,suggest_term_from_words` 로드

4. **ERD 크기 가드**: `get_item(target_erd_id)` 결과 ≥50KB면 `D:/project_with_ai/.../{...}.claude-tmp/glossary/erd_dump_{id}.json` 로 덤프 후 offset/limit + grep 으로 분석.

### Phase 1 — 현황 조사 + A/B/C 분류

사용자 정의 5단계 절차 그대로:

```
컬럼 → gov 용어사전 있나? (gov_compare_erd exact)
       ↓ 없음
       → program 용어사전 있나? (program_glossary_compare_erd source=program)
         ↓ 없음(term 미매칭 — ★ 신규 단정 금지, 착시 주의)
         → ★ 물리명 단어 분해 → 각 토큰이 표준 단어(약어)인가? (gov_word_search/program_word_search)
           ├─ 비표준 토큰인데 동일 의미 표준 단어 존재(event→EVNT 등) → A그룹 물리 rename (신규 아님)
           ↓ 의미 단어가 사전에 아예 없음
           → gov 도메인 있나? (gov_domain_search by classification)
             ↓ 없으면 → 사업 도메인 신설 후보
           → 누락 단어 신설 후보
           → 단어 조합으로 용어 생성 (suggest_term_from_words)
       → ERD 적용 (Phase 4)
```

#### Phase 1 도구 호출 순서

1. `gov_compare_erd(erd_id=target)` — exact + similar(Jaccard). 결과 통계 + miss 목록.
2. `program_glossary_compare_erd(erd_id=target, program_id)` — 통합 비교. source=gov|program|none **임시 표시**.
   ⚠️ **이 도구는 term_en_norm(용어 전체 약어) 정확일치**라, 물리명이 표준 단어약어가 아니라 full English 를
   쓴 drift 를 **none 으로 오분류**한다. 예: `event_type_cd` — 표준 단어는 `evnt`(EVNT)인데 `event`(full)를 써서
   term 매칭 실패 → none. **none 을 곧바로 신규(C)로 보내지 말 것.** (term-level 착시)
3. **★ none 컬럼 word 분해 재판정 (필수 — 근본 정합의 핵심)**:
   용어 = 단어의 조합이고, **표준 준수의 원자 단위는 단어(word_en_abbr)** 다. 각 none 컬럼의 물리명을 단어
   토큰으로 분해 → 각 토큰을 `gov_word_search`/`program_word_search`(한글 의미로도) 조회해 판정:
   - **모든 토큰이 표준 단어약어와 일치** → 이미 표준 (compare 가 term-level 이라 놓친 것). coverage 재계산, 조치 없음
   - **일부 토큰이 비표준 full English 인데 동일 의미의 표준 단어가 존재** (event→**EVNT**, relay→**RELY**,
     server→**SRVR**, video→**VDO**, statistic→**STAT** 등) → **A 그룹(물리 rename)** 로 재분류. **신규 등록 아님.**
     · `word_en_full`("Event")은 뜻풀이일 뿐 물리 약어가 아니다 — 컬럼은 반드시 `word_en_abbr`(EVNT)를 쓴다.
   - **토큰의 의미 단어가 사전에 아예 없음** → 비로소 **C 그룹(신규 단어/용어 합성)**
4. 최종 분류:
   - **A 그룹** — 비표준 영문 컬럼(`created_at`·`event_type_cd`·`relay_server_id` 등) → 표준 단어약어
     (`crt_dt`·`evnt_type_cd`·`rely_srvr_id`)로 물리 rename (Q1=A 디폴트)
   - **B 그룹** — program 사전 기존 있음, logical 만 정합
   - **C 그룹** — word 분해 결과 의미 단어가 사전 부재 → 도메인/단어/용어 합성 등록
5. C 그룹 각 컬럼:
   - 한글 logical + 물리 토큰을 단어로 분해 (사용자 협의 또는 명확한 경우 자동 분해)
   - `gov_word_search` / `program_word_search` 로 단어 ID 회수
   - 누락 단어 후보 목록화
   - `suggest_term_from_words` 로 합성 시뮬 + unresolved 0 검증

#### Phase 1 산출물 (이번 세션 9 md 세트)

`{output_dir}/` 하위:

| 파일 | 내용 |
|---|---|
| `README.md` | 작업 개요·5단계 절차·도구 매트릭스·디폴트 결정 |
| `01_현황요약.md` | 컬럼 총수·A/B/C 분류 통계·gov compliance·통합 coverage |
| `02_A_영문표준약어_정합.md` | A 그룹 rename 매핑 표 (변경 전/후/대상 테이블) |
| `03_B_사업용어_정합.md` | B 그룹 logical 정합 표 |
| `04_C_신규등록_계획.md` | C 그룹 서브카테고리별 신규 등록 후보 |
| `05_신규단어_목록.md` | 단어 신설 후보 (W## ID 가배정·en_abbr·도메인) |
| `06_결정필요.md` | Q3 동의어 / Q6 KLID-BM 충돌 항목만 (디폴트 결정은 본문에 명시) |
| `07_등록단어_ID매핑.md` | Phase 3 등록 후 채움 (실제 word_id) |
| `08_등록용어_ID매핑.md` | Phase 3 등록 후 채움 (실제 term_id) |

### Phase 2 — 결정 게이트 (조건부 질문만)

**디폴트 적용 결정** (Q1=A·Q2=유지·Q4=일괄·Q5=권장)은 **묻지 않음**. README.md 본문에 "디폴트 적용됨" 명시.

**조건부 질문** (해당 항목 검출 시만 `AskUserQuestion` 1콜 멀티문항):

#### Q3 동의어 정책
- 트리거: gov word/term 의 synonyms 에 한글 표현 중복 검출 (예: "전송"의 synonyms 에 "송신" 등록됨)
- 질문 예시: "gov 사전 '전송(TRSM)' synonyms 에 '송신'이 등록되어 있습니다. ERD 의 `tx_bps`(송신대역폭)/`rx_bps`(수신대역폭) 처리:"
  - A. gov synonym 따름 (송신=전송=TRSM 통일, 수신은 별도 RCV 등록)
  - B. 송신/수신 각각 별도 단어로 사업 등록 (SND/RCV)

#### Q6 KLID-BM 표준 충돌
- 트리거: `program_glossary_search` 결과 기존 용어와 en_abbr 다름 (예: 우리 RQST_DT vs KLID-BM DMND_DT)
- 질문 예시: "`requested_at` 컬럼은 KLID-BM 표준용어정의서에 '요청일시 = DMND_DT(term_id=796)'로 박혀있습니다. ERD 패턴은 `requested_at` → RQST_DT 였습니다:"
  - A. KLID-BM 표준 적용 (ERD 영문 `dmnd_dt` 로 rename + 기존 term 재사용)
  - B. ERD 영문 유지 (KLID-BM 용어 의미만 매핑, 영문 약어 불일치 허용)

**질문 후 `06_결정필요.md` 에 사용자 답 기록**.

### Phase 3 — 등록 (사용자 명시 승인 후만)

승인 트리거 키워드: "등록해", "박아", "전체 일괄", "고고", "고", "진행해" 등.

#### 등록 순서 (절대 규칙)

```
1) 도메인 신설 (대부분 0건 — gov 100% 커버 경험)
   ↓
2) 단어 등록 (program_word_create)
   - E_CONFLICT 핸들링: program_word_search 로 기존 id 회수 후 재사용
   - is_format_word=false 인 형식단어는 program_word_update 로 보정
   ↓
3) 용어 등록 (program_glossary_create)
   - E_CONFLICT: KLID-BM 표준 등 기존 우선 활용
   - mode 선택: gov 매핑 있으면 mode=gov + gov_term_id, 사업 신조어면 mode=program
```

#### 등록 시 표준 핸들링

| 케이스 | 처리 |
|---|---|
| E_CONFLICT (word_ko + word_en_abbr 동일) | program_word_search 로 기존 id 회수 |
| 기존 단어 is_format_word=false 인데 형식단어 필요 | program_word_update(is_format_word=true, default_domain_classification) |
| 용어 E_CONFLICT (KLID-BM 표준 기존) | Q6 결정 따름 (KLID-BM 우선이면 기존 term_id 재사용) |
| 동일 word_en_abbr 의미 다름 (Q2 디폴트=유지) | 기존 유지, description 에 충돌 명시 |

#### Phase 3 산출물

- `07_등록단어_ID매핑.md` — word_id ↔ word_ko/en_abbr/도메인 (실제 id)
- `08_등록용어_ID매핑.md` — term_id ↔ term_ko/en_abbr/gov_domain/대상 컬럼 (실제 id)
- 충돌 후 재사용 4건 / 신규 N건 통계 명시

### Phase 4 — ERD 정합 (2-Round Split)

`update_item(target_erd_id, data_mode=patch)` patch ops 사용.

**2-Round Split** (Session 95 실측 패턴):

```
Round 1: logical_column_name 정합 (76건 등)
  - selector: tables[name=X].columns[name=Y].logical_column_name
  - set op
  - base_version 추적

Round 2: 영문 컬럼 rename (12건 등) — Q1=A 디폴트로 진행
  - selector: tables[name=X].columns[name=Y].field
  - set op (name 필드도 함께)
  - 동반: MIG-{ERD} forward_ddl / brownfield.diff_summary 갱신
```

각 Round 후:
- `program_glossary_compare_erd` 재실행 → coverage 향상 확인
- `gov_compare_erd` 로 gov compliance % 추적

#### ERD update_item 주의사항

- `data_mode: merge` 는 top-level replace (deep merge ❌, omit 시 리셋) → **patch ops 권장**
- selector path 끝까지 명시 (`tables[name=X].columns[name=Y].field` 까지)
- ERD_MAPPING_STALE_COLUMN / STALE_TABLE_REF warning → ERD-001(논리 페어) deprecated 사유 benign, 무시

### Phase 5 — Cascade

`analyze_impact(target_erd_id, depth=3)` 는 **graph-link 만 감지** (이번 5건). 실제 본문 cascade는 grep 필요.

#### Cascade 후보 식별 (semantic grep)

영문 rename 발생 시 (Q1=A 디폴트로 항상 trigger):

```
rename 매핑 각 항목 (created_at → crt_dt 등) 에 대해:
  - DFEAT.persists_in_tables 본문 grep
  - API endpoint payload schema / example / responses grep
  - SCREEN binding (sections·components 안의 컬럼명 인용) grep
  - SEQ messages (시퀀스 메시지 본문) grep
  - AC scenario (검증 기준 본문) grep
  - CDIAG attributes (클래스 다이어그램 속성) grep
  - RUNBOOK / RISK / DOMAIN 본문 grep
```

#### Specialist 위임 (Q4=일괄 디폴트)

- 후보 ITEM 전체를 한 라운드에 1 에이전트 1 ITEM 으로 위임
- **동시 ≤3건** (5건 이상 소켓 끊김)
- self-contained prompt 필수:
  - rename 매핑 표 전체
  - edit_intent (예: "영문 컬럼 rename cascade, 실제 본문 인용만 patch, 추정 금지")
  - AI 추정 금지 명시
- 결과 YAML 수집:
  - patch 적용 / ack-only / 부분 실패 분류
  - cascade_candidates (재귀 후보)
- ack 비율 ~50% 정상 (실제 인용 없으면 ack)

#### 잔여 sweep 분리

SCREEN.static_render 재업로드 같은 외부 파일 변경은 cascade 본 라운드와 분리:
- `06_결정필요.md` 또는 새 `09_잔여작업.md` 에 명시
- 사용자가 별도 sweep 명시 후 처리 (mc-logi-update 위임)

---

## 종료 보고 (사용자에게)

```
✅ {ERD-ID} 용어사전 정합 완료

📊 통계
- 단어 신규 N건 (id A~B sparse, K 기존 활용)
- 용어 신규 M건 (id C~D sparse, L 기존 활용)
- ERD vXX → vYY (P logical + Q 영문 rename)
- 본문 patch R건 + ack S건 = 총 T ITEM cascade
- gov compliance X.X% → Y.Y%
- 통합 coverage X.X% → Y.Y%

📁 산출물
- 로컬: {output_dir}/ (9 md files)
- LogiCraft: {ERD-ID} v{new}, 신규 용어 M, 신규 단어 N

⚠️ 잔여
- (있는 경우만 나열)
- SCREEN-XXX static_render 재업로드
- KLID-BM 표준 추가 정합 대상
- ...
```

종료 시 사용자에게 **메모리 저장 여부** 확인 (mc-logi-update 패턴 그대로):
- `~/.claude/projects/{project}/memory/session_NN_{description}_{date}.md` 저장 제안
- MEMORY.md 인덱스 1줄 추가 제안

---

## 노하우 체크리스트 (REFERENCE)

Session 95 실측 + 근본 정합 노하우 (각 Phase 진입 시 점검):

1. **용어사전 4계층 모델** 절대 의존순 (도메인→단어→용어)
2. **영문 표준약어 혼재 발견 패턴** (event_type_mappings 표준 vs relay_* 비표준 같은 부분 표준)
3. **MIG in-place ADD 시점에 표준 약어로 정의** → 1차 보존 원칙 저촉 0
4. **★ program_glossary_compare_erd 는 term-level(전체 약어 정확일치) — word drift 를 none 으로 오분류**. `event_type_cd`(표준 `evnt_type_cd`)·`relay_server_id`(표준 `rely_srvr_id`) 처럼 full English 단어를 쓴 컬럼이 none 으로 떨어짐. **none = 신규 아님**. 반드시 Phase 1 step 3(word 분해)로 재판정해 A(rename) vs C(신규) 를 가른다. compare 는 coarse 프리필터일 뿐, 권위는 word 검사
5. **단어 등록 충돌 케이스** (카테고리/IP/초/주기/플랫폼/범위/승인 흔히 기존)
6. **KLID-BM 표준용어정의서 기존 존재** (영문 약어 차이 발견 시 Q6)
7. **ERD update_item 2 round 분리** (logical + 영문, atomic + base_version)
8. **analyze_impact 한계** (graph link 만, semantic cascade 별도 grep)
9. **specialist 동시 ≤3건** (5건 소켓 끊김)
10. **ERD-001 deprecated STALE warning benign** (기능 영향 0)
11. **SCREEN cascade 특성** (한글 라벨+API 식별자 위주, 영문 컬럼 노출 적음)
12. **API payload schema vs ERD column 분리** (대부분 별 네임스페이스, 일부만 직접 노출)
13. **★ 용어 = 단어의 조합, 표준 준수의 원자 단위는 단어(word_en_abbr)**. 컬럼 표준 검사는 term 문자열 비교가 아니라 **물리명 → 단어 토큰 분해 → 각 토큰이 표준 단어약어인가** 로 해야 정확. `word_en_full`("Event")은 뜻풀이·설명용이지 물리 약어가 아니다 — 컬럼은 `word_en_abbr`(EVNT)를 써야 하며, full English(`event`)를 쓴 건 "신규 용어"가 아니라 **비표준 단어 사용 = 표준 위반(rename 대상)**. drift 원인 대부분이 개발자가 약어 대신 full English 를 컬럼명에 쓴 것

---

## 도구 매트릭스

| 단계 | 도구 |
|---|---|
| 비교 | `gov_compare_erd`, `program_glossary_compare_erd` |
| 검색 | `gov_word_search`, `gov_domain_search`, `gov_term_search`, `program_word_search`, `program_glossary_search` |
| 합성 시뮬 | `suggest_term_from_words` |
| 등록 (사용자 승인 후) | `program_word_create`, `program_word_update`, `program_glossary_create` |
| ERD 수정 | `update_item` (data_mode=patch) |
| Cascade 분석 | `analyze_impact` + 본문 grep |
| Cascade 적용 | `Agent(subagent_type=logi-update-specialist)` |

---

## 재사용

도메인 인자만 바꾸면 D001~D008 + 다른 ERD 그대로 적용. `{output_dir}` 만 도메인별로 분리.

```
./용어 정리/D001/   ← ERD-005 (이번)
./용어 정리/D002/   ← 다음
./용어 정리/D003/   ← ...
```