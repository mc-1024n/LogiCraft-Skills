# Requirement Dimension

요구사항(REQ)이 **상위 진실원천(RFP)** 과 **하위 현재 설계(도메인)** 사이에서 **최신·정합·추적 가능**한지 검토.

배경: 설계가 도메인 기준으로 반복 수정되면 freshness 가 역전 — RFP(불변) → REQ(가장 stale) → 도메인+하위(최신). 이 차원은 REQ 계층을 위·아래 양쪽과 대조.

핵심 체인: `RFP(rfp_item) → (derived_from_rfp) → REQ`, `REQ → DFEAT·도메인`, `REQ.description/rationale ↔ 도메인+활성 하위 현행 본문`.

## 정책
- RFP 원천 = logicraft `rfp_item`. 충돌 시 **도메인(현재) 우선 + RFP 배경**. divergence 자체는 gap 아니고 **divergence 미명시**가 gap.

## 입력 보강 (STEP 0)
도메인 책임 REQ 식별: get_neighbors backward belongs_to_domain requirement(1차) + DFEAT specializes·REQ.description 도메인 인용(2차). 보강: REQ 의 source·derived_from_rfp·description·rationale·acceptance_criteria + 후보 rfp_item(title/workstream/keyword 추정) + 도메인 description + include_retired 대조.

## ★ 검증 모드 (가용 입력별 자동)
- **모드 A** — REQ 없음 → 차원 전체 SKIP (gap 0 + unable_to_verify). REQ 부재 자체를 gap으로 키우지 말 것.
- **모드 B** — REQ 있음 + RFP 없음/매핑불가 → RQ-002·RQ-005만. RFP 의존 룰(RQ-001/003/004/006) SKIP.
- **모드 C** — REQ+RFP+도메인 모두 → RQ-001~006 전체.
→ summary에 적용 모드(A/B/C) 1줄 명시.

## 검토 룰
- **RQ-001**: REQ ↔ RFP 미연결 (derived_from_rfp 없이 source=stakeholder만) → P1. 대응 RFP 명확하면 auto=true.
- **RQ-002**: REQ 내용이 도메인보다 stale (폐기 모델 서술) → P1 (must/critical P0). ★ 이중 인용 의무.
- **RQ-003**: REQ ↔ RFP divergence 미명시 (도메인이 ADR로 벗어났는데 rationale 미기재) → P1.
- **RQ-004**: RFP 핵심 요구가 도메인 REQ로 미하향 → P2 (핵심이면 P1). 이 도메인 책임 범위만.
- **RQ-005**: REQ acceptance_criteria 빈약 → P2
- **RQ-006**: RFP 중 도메인 비책임(외부 workstream) 부분 미명시 → advisory P2 ("우리 영역 아닌 것으로 보임"). RQ-004의 반대면. 신규 REQ 만들지 말 것(책임 경계 섹션만).

## Gap 분류 코드
- `D<NNN>-RQ-001`~`006` (YAML dimension=requirement, prefix RQ)

## auto_fixable 정책
- RQ-001 — 대응 RFP 명확 시 `true`, 모호 `false` / RQ-002~006 → 모두 `false` (재대조·판단 필요)

## cross-dimension hint
- RQ-002 ↔ STL / RQ-001 ↔ LINK / RQ-004 ↔ COV / RQ-006 ↔ COV(advisory로만). 후속 수정은 mc-logi-update 상류 requirement sync.
