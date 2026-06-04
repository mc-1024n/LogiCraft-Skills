# Stale Dimension

stale ITEM·deprecated 잔재·brownfield 메타 누락 검토.

## 검토 룰

### STL-1: stale=true ITEM
- 도메인 ITEM 중 `stale: true` 모두 P1 (cascade 미반영)
- stale_reason 인용 + 원인 ITEM 식별
- 30일 이상 stale → P0 (장기 미정합)

### STL-2: deprecated 상태 ITEM 잔재 인용
- 도메인 활성 ITEM의 description / sections / messages / consumes_apis / invokes_apis에서 deprecated 상태 ITEM ID grep
- 발견 시 P0 (정합 누락)

### STL-3: retired_items 매핑 검증
- list_items(include_retired=true)의 retired_items에 있는 ITEM이 활성 ITEM에서 참조되는지
- 참조 발견 시 P0

### STL-4: brownfield.status=modified + legacy_source 비어있음
- modified인데 legacy_source.identifier 비어있음 → P1 (BROWNFIELD_REUSE_WITHOUT_SOURCE warning)
- 메모리 패턴: Session 33 v3에서 자주 발생

### STL-5: brownfield.status=new + legacy_source.identifier 채워짐
- new인데 legacy_source가 있으면 P1 warning (BROWNFIELD_NEW_WITH_LEGACY_SOURCE)
- 의도된 split이면 notes에 명시 필요

### STL-6: change_summary "Claude가 생성" 잔재
- change_summary가 자동 생성 기본값 "Claude가 생성"으로 머물러 있음 → P2 (의미 없는 메타)

### STL-7: prominent 필드 비어있음
- schema의 displayHints에서 `prominent: true` 필드가 비어있음 → P2 (정보 부족)
- 예: domain_feature description / brownfield.diff_summary 등

### STL-8: implementation.status 진행률 0%
- 도메인 ITEM 중 design 완료된 것의 implementation.status / progress 추적 가능
- design 단계 완료된 ITEM의 implementation.status가 "planned" 유지 → 정보 부족 (낮은 우선순위)

## Gap 분류 코드
- `D<NNN>-STL-001`: stale=true
- `D<NNN>-STL-002`: deprecated ID 잔재 인용
- `D<NNN>-STL-003`: retired_items 활성 참조
- `D<NNN>-STL-004`: modified + legacy_source 누락
- `D<NNN>-STL-005`: new + legacy_source 의도 모호
- `D<NNN>-STL-006`: change_summary 기본값
- `D<NNN>-STL-007`: prominent 필드 비어있음
- `D<NNN>-STL-008`: implementation 진행 추적 누락

## auto_fixable 정책
- STL-001 stale 해소 → `true` (stale_reason 따라가서 정합)
- STL-002 deprecated 잔재 청소 → `true` (텍스트 제거)
- STL-003 retired 참조 → `true` (cascade)
- STL-004 legacy_source 보강 → `true` if 메모리/edit_context에 식별자 있음, else `false`
- STL-005/006/007/008 → `false` (사용자 검토)

## Evidence 인용 룰
- stale_reason 직접 quote: `"API-249의 5개 필드 변경 — consumes"`
- description grep 결과: `SCREEN-022 sections에 "API-191 (deprecated)" 인용 발견`
- last_updated_at 기준 stale 경과일 계산
