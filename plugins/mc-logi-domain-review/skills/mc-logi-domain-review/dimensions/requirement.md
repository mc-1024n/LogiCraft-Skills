# Requirement Dimension

요구사항(REQ)이 **상위 진실원천(RFP)** 과 **하위 현재 설계(도메인·DFEAT/UC/API)** 사이에서 **최신·정합·추적 가능**한지 검토.

배경: 설계가 **도메인 기준**으로 반복 수정되면 산출물 freshness 가 역전된다 —
```
RFP (rfp_item, 발주처 원본 = 불변 진실원천)
   ↓ 파생
요구사항 (requirement)   ← ★ 자주 가장 stale (도메인 낳은 뒤 미갱신)
   ↓ 파생
도메인 (domain) + 하위 ITEM (DFEAT/UC/API/SEQ/ERD/AC)  ← 가장 최신
```
이 차원은 **REQ 계층**을 위(RFP)·아래(도메인) 양쪽과 대조해 stale·미연결·divergence·누락을 검출한다.

핵심 관계 체인:
- `RFP(rfp_item) → (derived_from_rfp) → REQ`  (상위 추적)
- `REQ → (specializes_feature / implements / belongs_to_domain) → DFEAT·도메인`  (하위 파생)
- `REQ.description / rationale ↔ 도메인 description + 활성 DFEAT/UC/API 현행 본문`  (현행성)

## 정책 (이 차원의 판단 기준 — 사용자 결정 반영)
- **RFP 원천 = logicraft `rfp_item`** (RFP-001~018 = SFR-01~18). 외부 .md 는 이 차원에서 안 봄.
- **충돌(divergence) 시 도메인(현재 설계) 우선 + RFP 배경**: 도메인이 ADR 로 RFP 의도에서 의도적으로 벗어난 경우(예: 1차 보존·책임 외부 위임·모델 대전환), REQ 는 **현재 설계 기준으로 기술하되 RFP 의도를 rationale 에 배경으로 보존**. 이때 "RFP 와 다름"은 gap 이 아니라 **divergence 미명시**가 gap.

## 입력 보강 (STEP 0 — 검사의 전제)

도메인 책임 REQ 식별:
1. `get_neighbors(DOMAIN-XXX)` backward 의 `belongs_to_domain` requirement (1차)
2. 도메인 활성 DFEAT 의 `specializes_feature`/상위 추적, REQ.description 의 도메인 책임 인용 (2차)

⚠️ 검사 전 보강(item_catalog 에 없으면 get_item):
- 각 도메인 REQ 의 `source`·`derived_from_rfp`(또는 rfp link 필드)·`description`·`rationale`·`acceptance_criteria`
- 후보 `rfp_item` (RFP-001~018) — REQ↔RFP 매핑이 명시 없으면 **title·workstream·keyword 로 추정** (예 학습데이터 REQ ↔ RFP-013/015/016/017)
- 도메인 `description`(현재 진실) + deprecated 대조용 `list_items(type=domain_feature|use_case|api_endpoint, include_retired=true)`

## ★ 검증 모드 (STEP 0 — 가용 입력에 따라 자동 결정)

이 차원은 3개 입력(**RFP · REQ · 도메인**)의 가용성에 따라 단계적으로 동작한다. 비교의 축이 없으면 그 룰은 돌지 않는다.

### 모드 A — REQ 없음 (도메인 귀속 REQ 0건) → ★ 차원 전체 SKIP
- requirement 검증의 **대상 자체가 없음** → 룰 RQ-001~006 전부 미수행. gap 0 으로 반환.
- `notes_for_main.unable_to_verify` 에 "도메인 귀속 REQ 0건 — requirement 차원 검증 대상 없음(skip)" 명시.
- ⚠️ 도메인이 REQ 없이 도메인→DFEAT 로만 설계된 것은 **정상일 수 있음** — REQ 부재 자체를 gap 으로 키우지 말 것(이 차원은 "기능이 안 도는" 게 아니라 "검증할 입력이 없는" 상태로 처리).

### 모드 B — REQ 있음 + RFP 없음/매핑 불가 → domain ↔ REQ 대조만
- 후보 rfp_item 을 title/workstream/keyword 로도 식별 못 하거나 프로젝트에 RFP 자체가 없을 때.
- **수행**: RQ-002(REQ stale vs 도메인) · RQ-005(inline AC). = 도메인 현재 설계와 REQ 의 정합·현행성만 본다.
- **SKIP**: RQ-001 · RQ-003 · RQ-004 · RQ-006 (전부 RFP 를 한 축으로 쓰는 룰).
- `notes_for_main.unable_to_verify` 에 "후보 RFP 미식별 — RFP 의존 룰(RQ-001/003/004/006) skip, domain↔REQ 대조만 수행" 명시.

### 모드 C — REQ + RFP + 도메인 모두 가용 → 전체 룰 (표준)
- RQ-001~006 전부 수행.

→ 각 auditor 출력 `summary` 에 적용된 모드(A/B/C)를 1줄로 명시 권장.

## 검토 룰

### 추적성 (RQ-001)

#### RQ-001: REQ ↔ RFP 미연결
- REQ 가 `derived_from_rfp`(상위 RFP link) 없이 `source.type=stakeholder`(회의 등)만 → **P1** (추적성 끊김 — RFP→REQ→도메인 체인 단절)
- **검출**: REQ.derived_from_rfp 비어있음 AND title/내용상 대응되는 rfp_item 존재
- **auto**: 대응 RFP 가 title/workstream 으로 **명확히** 식별되면 derived_from_rfp 추가 = `true`. 모호하면 `false`(사용자 확정).

**gap 예시**: "REQ-025(학습데이터셋 ver 관리) derived_from_rfp=[] · source=stakeholder(회의 2026-05-11) — 대응 RFP-008/016/017 미연결"

### 현행성 — REQ vs 도메인 (RQ-002)

#### RQ-002: REQ 내용이 도메인보다 stale (폐기 모델 서술)
- REQ.description/title 이 **도메인 description·활성 하위 ITEM 의 현행 모델과 모순**되는 옛 모델(폐기 용어·구 필드·구 endpoint·폐기 enum)을 서술 → **P1** (priority=must/critical REQ 면 **P0**)
- **검출**: REQ.description 의 모델 어휘 ↔ 도메인 description / 활성 DFEAT·UC·ERD 현행 본문 비교
- ★ **이중 인용 의무**: REQ.description 의 옛 모델 줄 quote + 도메인/하위 ITEM 의 현행 줄 quote 를 **동시에** 제시해야 gap 인정. 한쪽만이면 보고 금지(false positive 억제).

**gap 예시**: "REQ-025.description 'sample 단위 버전 **매트릭스**·PJT_ID·ProjectComplete 통지' ↔ DOMAIN-004 v14 'ver 타임라인+json_change_history·job_id·notify-completed/updated 2 API' — Session 48 폐기 모델 잔존"

### 정합성 — REQ vs RFP (RQ-003)

#### RQ-003: REQ ↔ RFP 의도 divergence 미명시
- 도메인이 ADR 로 RFP 원래 요구에서 **의도적으로 벗어났는데**(책임 외부 위임·범위 축소·1차 보존 등) REQ 가 그 변경·divergence 를 **rationale 에 명시하지 않음** → **P1**
- ※ RFP 와 단순히 다른 것 자체는 gap 아님(도메인 우선 정책). **divergence 가 REQ 에 흔적조차 없는 것**이 gap.
- **검출**: RFP.details/definition 의 핵심 요구 ↔ 도메인 현재 책임 차이 식별 → REQ.rationale 에 그 차이 설명 유무

**gap 예시**: "RFP-013 '학습데이터셋 검색·통합 다운로드·이력관리' (시스템 기능) ↔ 현재 D004 책임=배치 송신만(검색/다운로드는 외부 포탈 위임) — REQ-026 rationale 에 위임 divergence 미기재"

### 커버리지 — RFP → REQ (RQ-004)

#### RQ-004: RFP 핵심 요구가 도메인 REQ 로 미하향
- 도메인이 책임지는 rfp_item 의 **핵심 요구 항목**이 어떤 도메인 REQ 로도 안 내려옴(요구사항 부재) → **P2** (도메인 핵심 책임이면 P1)
- ⚠️ RFP 1건이 여러 도메인에 걸칠 수 있음 — **이 도메인 책임 범위**의 요구만 대상. 타 도메인 몫은 skip.

**gap 예시**: "RFP-017 'CoT/VQA 라벨링 가이드라인' 은 저작도구(외부) 책임이라 D004 REQ 부재 정상 / 단 'ver 재배포'는 D004 책임인데 REQ 명시 약함"

### 책임 경계 — RFP 비책임 식별 (RQ-006)

#### RQ-006: RFP 중 도메인(관제지원) 비책임 부분 미명시
- RFP 1건이 여러 workstream(관제지원·VLM·중계서버·저작도구·포탈 등)에 걸칠 때, 이 도메인이 **책임지지 않는 부분**(외부 workstream)이 도메인 REQ 에 "외부 위임·비책임"으로 명시되지 않으면 → **advisory 리포트 (P2, 정보성)**
- ★ **RQ-004 의 반대면**: RFP 의 핵심 요구 항목을 **책임 기준으로 분류**한다 — ⓐ 이 도메인 책임인데 REQ 미하향 = `RQ-004` / ⓑ 이 도메인 책임 아님(외부 workstream) = `RQ-006`. 같은 RFP 를 두 룰이 양면으로 본다.
- **검출**: RFP.details/definition/`workstream` 의 핵심 요구 항목 ↔ 도메인 현재 책임(description·활성 DFEAT) 비교 → **도메인 책임 밖 항목** 식별 → 그 비책임이 대응 REQ 의 rationale/책임경계 섹션에 "외부 위임" 으로 명시돼 있는지 확인.
- **리포트 방식 (★ gap 이 아니라 advisory)**: 단정하지 말고 **"~ 우리 영역이 아닌 것으로 보임"** 으로 사용자 확인을 요청. 예: `"RFP-XXX 중 [이 항목]은 관제지원(D00N) 영역이 아닌 것으로 보임 (workstream=VLM/중계서버). REQ 에 비책임(외부 위임) 명시 권장"`. **확정은 사용자 도메인 지식** — auditor 는 후보만 제시.
- **권장 수정 (mc-logi-update)**: 우리 책임 부분만 REQ화 + 해당 REQ 에 `## 관제지원 책임 경계` 섹션(RFP 중 우리 몫 + 외부 위임 부분 동시 명시) + `derived_from_rfp` 부분 연결. ★ **비책임을 위한 신규 REQ 를 만들지 말 것** (외부 workstream 기능을 REQ화하면 책임 범위 오염). Session 77 D002 패턴.

**예시**: "RFP-002(클립영상 중복 수집 방지) workstream=VLM — '오탐 검증·중복 판정 로직'은 VLM(외부) 책임으로 보임, 관제지원은 '오탐·중복 영상 운영자 선별·폐기'만. REQ-007 에 책임 경계 명시 권장 (신규 REQ 불필요)"

## Gap 분류 코드
- `D<NNN>-RQ-001`: REQ↔RFP 미연결 (추적성)
- `D<NNN>-RQ-002`: REQ 내용 stale vs 도메인
- `D<NNN>-RQ-003`: REQ↔RFP divergence 미명시
- `D<NNN>-RQ-004`: RFP 핵심 요구 도메인 REQ 미하향
- `D<NNN>-RQ-005`: REQ acceptance_criteria 빈약
- `D<NNN>-RQ-006`: RFP 비책임 부분 미명시 (advisory — "우리 영역 아닌 것으로 보임")

(YAML 출력의 `dimension:` 값은 `requirement`, gap prefix 는 `RQ`)

## auto_fixable 정책
- RQ-001 derived_from_rfp 추가 — 대응 RFP **명확** 시 `true`(link 추가), 모호 시 `false`
- RQ-002 REQ 재작성(폐기 모델→현행) — `false` (의미 재작성 = RFP+도메인 재대조 필요)
- RQ-003 divergence rationale 보강 — `false` (판단·서술 필요)
- RQ-004 REQ 신설/보강 — `false` (신규 요구사항 = 사용자)
- RQ-005 acceptance_criteria 작성 — `false`
- RQ-006 책임 경계 명시 — `false` (advisory — 책임 귀속 판단은 사용자 도메인 지식)

→ Requirement 차원은 RQ-001(link)만 auto 후보. 나머지는 RFP+도메인 재대조라 사용자/specialist 재작성. RQ-006 은 검출(advisory)만 — 수정은 사용자 확인 후 mc-logi-update.

## Evidence 인용 룰
- 미연결: `REQ-025.derived_from_rfp = [] · source.type=stakeholder` + 대응 추정 `RFP-016/017(학습데이터셋 구축)`
- stale 대조(이중 quote): `REQ-025.description "sample 매트릭스·PJT_ID" ↔ DOMAIN-004.description "ver 타임라인·job_id" (코드블록 동시 quote)`
- divergence: `RFP-013.details "검색·통합 다운로드" ↔ DOMAIN-004 "포탈(외부) 호스팅, D004=배치송신만" + REQ-026.rationale 에 위임 언급 없음`

## cross-dimension hint
- RQ-002(REQ stale) ↔ `STL`(도메인 ITEM stale) 연동 — 같은 대전환의 상·하류
- RQ-001(RFP link) ↔ `LINK`(link 무결성) — 상위 추적 link 부재
- RQ-004(RFP 미하향) ↔ `COV`(도메인 책임 커버리지) — RFP 책임 vs 도메인 DFEAT
- RQ-006(RFP 비책임) ↔ `COV` — RQ-004 와 짝(RFP 요구를 책임 기준으로 양분). 비책임은 advisory 로만, COV 갭으로 키우지 말 것
- RQ-002/003 후속 수정은 mc-logi-update 의 **상류(upstream) requirement sync** 로 처리 (RFP+도메인 재대조)
