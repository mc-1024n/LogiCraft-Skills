# Stale Dimension

stale ITEM·deprecated 잔재·brownfield 메타 누락 검토.

## 검토 룰
- **STL-1**: stale=true ITEM → P1 (30일 이상 P0)
- **STL-2**: deprecated 상태 ITEM 잔재 인용 → P0
- **STL-3**: retired_items 매핑 검증 → 참조 발견 P0
- **STL-4**: brownfield.status=modified + legacy_source 비어있음 → P1
- **STL-5**: status=new + legacy_source.identifier 채워짐 → P1 (의도 split이면 notes 명시)
- **STL-6**: change_summary "Claude가 생성" 잔재 → P2
- **STL-7**: prominent 필드 비어있음 → P2
- **STL-8**: implementation.status 진행률 추적 누락 → 낮은 우선순위

## Gap 분류 코드
- `D<NNN>-STL-001`~`008` (위 순서)

## auto_fixable 정책
- STL-001 stale 해소 → `true`
- STL-002 deprecated 잔재 청소 → `true`
- STL-003 retired 참조 → `true`
- STL-004 legacy_source 보강 → 메모리/edit_context에 식별자 있으면 `true`, else `false`
- STL-005/006/007/008 → `false`

## Evidence 인용 룰
- stale_reason 직접 quote·description grep 결과·last_updated_at 경과일.
