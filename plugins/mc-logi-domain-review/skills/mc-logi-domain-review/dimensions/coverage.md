# Coverage Dimension

도메인 책임과 DFEAT 의 **양방향 정합**, 그리고 DFEAT 가 UC/SCREEN/SEQ 로 backing 되었는지 검토.

- **① 도메인 → DFEAT (누락)**: 도메인이 선언한 책임을 DFEAT 가 다 덮었는가
- **② DFEAT → 도메인 (벗어남·모자람)**: 각 DFEAT 의 책임이 도메인 책임 범위를 벗어나거나(오분류) 모자라지(빈약) 않는가
- **backing 정합**: DFEAT → UC/SCREEN, UC → SEQ, API → DFEAT

## 책임 인벤토리 추출 (STEP 0 — 양방향 검사의 전제)

COV-7/8/9 는 도메인 description 을 **단일 진실원**로 사용한다. 검사 전 도메인 책임 인벤토리를 추출:

기준점 우선순위:
1. 도메인 description 의 **핵심 책임 목록** (번호 매겨진 책임 `R1 … Rn`)
2. 없으면 **책임 영역 매트릭스** (예 D002 "A 통계 / B VLM / C 검수 / D 업로드 / E 학습 / F 운영설정")
3. **"책임 제외" 섹션** → ② 의 *negative 기준* (`X1 … Xm`: 여기 적힌 책임을 DFEAT 가 수행하면 위반)

→ 도메인 description 에 1·2 가 **둘 다 없으면** COV-1 발동 (P2) + COV-7/8/9 **전부 skip** + `notes_for_main.unable_to_verify` 에 "도메인 책임 인벤토리 부재 — 양방향 정합 검증 불가" 명시. 기준 없는 곳에 억지 gap 만들지 않는다.

⚠️ ② 검사는 각 DFEAT 의 **description 본문**이 필요하다. item_catalog 에 DFEAT description 이 없으면 STEP C 에서 `get_item(DFEAT-XXX)` 로 보강 (활성 DFEAT 만, 전수 fetch 금지).

## 검토 룰

### 도메인↔DFEAT 책임 양방향 정합 (COV-1 / COV-7 / COV-8 / COV-9)

#### COV-1: 책임 인벤토리 기준 확립 (게이트)
- 도메인 description 에 책임 목록 또는 영역 매트릭스가 명시됐는지 확인
- 둘 다 없음 → **P2** + COV-7/8/9 skip (양방향 검사 기준 부재, description 보강 권장)
- 있음 → 책임 인벤토리 (`R1…Rn` + 제외 `X1…Xm`) 추출 후 COV-7/8/9 진행

**gap 예시**: "DOMAIN-005 description 에 핵심 책임 목록·영역 매트릭스 모두 없음 — DFEAT 양방향 정합 기준 없음"

#### COV-7: 도메인 책임 미커버 (① 누락 방향)
- 책임 인벤토리 `Ri` 각각에 대해, 그 책임을 맡는 활성 DFEAT 가 1개 이상 있는지
- 어떤 활성 DFEAT 에도 안 덮인 `Ri` → **P1** (핵심 책임이면 **P0**)
- 검출: 도메인 책임 줄 ↔ DFEAT description / specializes_feature 매칭. 매칭 0건이면 gap

**gap 예시**: "DOMAIN-002 책임 R4 '업로드' 를 맡는 활성 DFEAT 없음 — description 은 6영역 명시했으나 DFEAT 는 5영역만 커버"

#### COV-8: DFEAT 오분류 / scope creep (② 벗어남 방향)
- 각 활성 DFEAT 의 책임이 도메인 책임 인벤토리 `R1…Rn` 중 **어디에도 안 맞는지**
- 안 맞음 → **P1** (오분류 / 도메인 모순)
- "책임 제외" 목록 `Xj` 에 해당하는 책임을 DFEAT 가 수행 → **P0** (명시적 위반)
- 타 도메인 책임에 더 적합해 보이면 → `notes_for_main` 에 후보 도메인 제시

**검출**: DFEAT description 의 핵심 책임 ↔ 도메인 인벤토리 전체 대조. 매칭되는 `Ri` 가 0개면 벗어남.

**gap 예시**: "DFEAT-031 책임 '비용 집계' 가 DOMAIN-008 책임 인벤토리 R1~R7 어디에도 없음 — 도메인 모순 (Session 37 DFEAT-031 FEAT-009→FEAT-010 케이스), 후보 도메인 검토 필요"

#### COV-9: DFEAT 부분 실현 / 빈약 (② 모자람 방향)
- DFEAT 가 매핑된 도메인 책임 `Ri` 를 **부분만** 실현하거나, description 이 책임 대비 빈약한지
- 핵심 책임의 부분 실현 → **P1**, 단순 description 빈약 → **P2**

**검출**: DFEAT 가 `Ri` 에 매핑되나 description 이 `Ri` 의 일부 행위만 다룸 (예: 책임은 "수집·정제·검증"인데 DFEAT 는 "수집"만).

### backing 정합 (COV-2 ~ COV-6)

#### COV-2: DFEAT → UC backing
- 활성 DFEAT 는 최소 1개 UC 가 realizes_features 또는 backing 관계여야 함
- backing UC 없는 DFEAT → P1 gap

**검출**: UC.realizes_features 에 본 DFEAT 의 specializes_feature(FEAT-XXX) 포함 또는 UC.description 에 DFEAT 인용

#### COV-3: DFEAT → SCREEN backing
- 사용자가 접근하는 DFEAT 는 SCREEN backing 필요 (admin/manage 책임)
- 백엔드 전용 DFEAT (이벤트 수신·정기 batch) 는 SCREEN 불필요 (notes 에 명시 시 OK)

**검출**: 활성 DFEAT 중 어떤 SCREEN.references_features 에도 인용 안 된 + description 에 백엔드 전용 명시 없음 → P1

#### COV-4: UC → SEQ realizes
- 활성 UC 는 happy path SEQ 1개 + error path SEQ 1개 권장 (Session 32 표준)
- happy path 없으면 P0
- error path 없으면 P1

**검출**: UC-XXX 에 대해 SEQ.realizes_use_cases 매칭 SEQ 수집, scenario_type 별 카운트

#### COV-5: API → DFEAT 매핑
- 도메인 활성 API 는 모두 어떤 DFEAT 의 implemented_by_endpoints 에 포함되어야 함
- 매핑 없는 API → P0 gap (orphan API)

**검출**: 도메인 API 목록 vs 도메인 DFEAT 의 implemented_by_endpoints 합집합 차집합

#### COV-6: 1차 핵심 기능 vs 2차 DFEAT 매핑 (legacy_grep_enabled=true 시만)
- 1차 소스 주요 service/controller 가 2차 DFEAT 로 매핑됐는지 grep
- 미매핑 1차 기능 → P1 gap (보존 정책 위반 가능성)

## Gap 분류 코드
- `D<NNN>-COV-001`: 책임 인벤토리 기준 부재 (게이트)
- `D<NNN>-COV-002`: DFEAT UC backing 없음
- `D<NNN>-COV-003`: DFEAT SCREEN backing 없음
- `D<NNN>-COV-004`: UC SEQ 없음 (happy/error)
- `D<NNN>-COV-005`: Orphan API (DFEAT 매핑 없음)
- `D<NNN>-COV-006`: 1차 기능 미매핑
- `D<NNN>-COV-007`: 도메인 책임 미커버 (① 누락)
- `D<NNN>-COV-008`: DFEAT 오분류 / scope creep (② 벗어남)
- `D<NNN>-COV-009`: DFEAT 부분 실현 / 빈약 (② 모자람)

## auto_fixable 정책
- COV-001 기준 부재 → `false` (도메인 description 책임 목록 작성 = 사용자)
- COV-002/003 backing 누락 → `false` (UC/SCREEN 신규 또는 기존 UC 에 references 추가 판단 필요)
- COV-004 SEQ 누락 → `false` (SEQ 신규 작성 필요)
- COV-005 orphan API → `false` (DFEAT 책임 판단 필요, 사용자 확정)
- COV-007 책임 미커버 → `false` (DFEAT 신규 또는 책임 재배치 = 사용자 결정)
- COV-008 오분류 → `false` (belongs_to_domain 재배치 / 책임 재정의 = 사용자 확정)
- COV-009 부분 실현 → `false` (실제 내용 보강 필요)

→ Coverage 차원은 거의 모두 `auto_fixable=false`. 사용자 결정 필수.

## Evidence 인용 룰
- list_items 결과 인용: `list_items(domain_id=DOMAIN-002, type=api_endpoint) → 35 items, DFEAT 매핑된 합집합 32 items, 차집합 3 orphan`
- 도메인 description 인용: 책임 목록 / 영역 매트릭스 줄 직접 quote
- 1차 소스 인용 (legacy_grep_enabled=true): `klid_system_was_clip/com.cudo.klid.api.original.ApiOriginalSendLearning` 같은 식별자

### ★ 양방향 정합 (COV-7/8/9) Evidence 강제 룰 — false positive 억제
1. **이중 인용 의무**: COV-008/009 는 evidence 에 **도메인 책임 줄 직접 quote + DFEAT description 줄 직접 quote 를 동시에** 넣어야만 gap 인정. 한쪽만 있으면 보고 금지.
2. **벗어남 입증 책임**: COV-008 은 도메인 책임 인벤토리 **전체(`R1…Rn` + 제외 `X1…Xm`)를 evidence 에 나열**하고 "어디에도 안 맞음" 을 보여야 함. "그냥 안 맞아 보임" 금지.
3. **거친 기준 관용**: 도메인 description 이 coarse 하면 DFEAT 가 더 구체적인 건 *정상* (벗어남 아님). **"명백히 다른 책임 영역"** 일 때만 COV-008. confidence 낮으면 한 단계 낮게 (checklist 보수 룰).
4. **cross-dimension hint**: COV-008(오분류) 은 `LINK-011`(UC.realizes_dfeats 도메인 불일치) 과 연동 가능 → `cross_dimension_hint` 에 `D<NNN>-COV-008 ↔ LINK-011` 명시.
