# Coverage Dimension

도메인 책임 영역이 DFEAT로 충분히 커버되었는지, DFEAT가 UC/SCREEN/SEQ로 backing되었는지 검토.

## 검토 룰

### COV-1: 도메인 책임 영역 매트릭스 vs DFEAT 분포
- 도메인 description에 영역 매트릭스 있는지 확인 (예 D002 "A 통계 / B VLM / C 검수 / D 업로드 / E 학습 / F 운영설정")
- 각 영역마다 책임 DFEAT 1개 이상 존재해야 함
- 영역 매트릭스가 없으면 P2 gap (description 보강 권장)

**gap 예시**: "D002 영역 G(가칭 추가 영역)에 책임 DFEAT 없음 — 도메인 description은 7영역 명시했으나 DFEAT는 6개"

### COV-2: DFEAT → UC backing
- 활성 DFEAT는 최소 1개 UC가 realizes_features 또는 backing 관계여야 함
- backing UC 없는 DFEAT → P1 gap

**검출**: UC.realizes_features에 본 DFEAT의 specializes_feature(FEAT-XXX) 포함 또는 UC.description에 DFEAT 인용

### COV-3: DFEAT → SCREEN backing
- 사용자가 접근하는 DFEAT는 SCREEN backing 필요 (admin/manage 책임)
- 백엔드 전용 DFEAT (이벤트 수신·정기 batch)는 SCREEN 불필요 (notes에 명시 시 OK)

**검출**: 활성 DFEAT 중 어떤 SCREEN.references_features에도 인용 안 된 + description에 백엔드 전용 명시 없음 → P1

### COV-4: UC → SEQ realizes
- 활성 UC는 happy path SEQ 1개 + error path SEQ 1개 권장 (Session 32 표준)
- happy path 없으면 P0
- error path 없으면 P1

**검출**: UC-XXX에 대해 SEQ.realizes_use_cases 매칭 SEQ 수집, scenario_type별 카운트

### COV-5: API → DFEAT 매핑
- 도메인 활성 API는 모두 어떤 DFEAT의 implemented_by_endpoints에 포함되어야 함
- 매핑 없는 API → P0 gap (orphan API)

**검출**: 도메인 API 목록 vs 도메인 DFEAT의 implemented_by_endpoints 합집합 차집합

### COV-6: 1차 핵심 기능 vs 2차 DFEAT 매핑 (legacy_grep_enabled=true 시만)
- 1차 소스 주요 service/controller가 2차 DFEAT로 매핑됐는지 grep
- 미매핑 1차 기능 → P1 gap (보존 정책 위반 가능성)

## Gap 분류 코드
- `D<NNN>-COV-001`: 도메인 영역 매트릭스 부재 또는 영역 누락
- `D<NNN>-COV-002`: DFEAT UC backing 없음
- `D<NNN>-COV-003`: DFEAT SCREEN backing 없음
- `D<NNN>-COV-004`: UC SEQ 없음 (happy/error)
- `D<NNN>-COV-005`: Orphan API (DFEAT 매핑 없음)
- `D<NNN>-COV-006`: 1차 기능 미매핑

## auto_fixable 정책
- COV-005 orphan API → `false` (DFEAT 책임 판단 필요, 사용자 확정)
- COV-002/003 backing 누락 → `false` (UC/SCREEN 신규 또는 기존 UC에 references 추가 판단 필요)
- COV-004 SEQ 누락 → `false` (SEQ 신규 작성 필요)
- COV-001 영역 매트릭스 부재 → `false`

→ Coverage 차원은 거의 모두 `auto_fixable=false`. 사용자 결정 필수.

## Evidence 인용 룰
- list_items 결과 인용: `list_items(domain_id=DOMAIN-002, type=api_endpoint) → 35 items, DFEAT 매핑된 합집합 32 items, 차집합 3 orphan`
- 도메인 description 인용: 책임 영역 매트릭스 줄 직접 quote
- 1차 소스 인용 (legacy_grep_enabled=true): `klid_system_was_clip/com.cudo.klid.api.original.ApiOriginalSendLearning` 같은 식별자
