# Auditor Hard Rules

## Pre-audit (감사 시작 전)

### 데이터 수집 우선
- [ ] item_catalog 입력으로 받은 ITEM 목록을 우선 사용 (메인이 list_items 1회 호출)
- [ ] 개별 get_item은 검토에 꼭 필요한 ITEM만 (전수 fetch 금지)
- [ ] get_neighbors / analyze_impact는 dimension 룰이 요구할 때만

### Dimension 분리 엄격
- [ ] 입력 prompt의 `dimension`이 지정한 차원만 검토
- [ ] 다른 차원 검출 시 → `notes_for_main.cross_dimension_hint`에 명시 (gap 직접 보고 금지)
- [ ] 예: stale 차원에서 deprecated 인용 발견 시 STL-002로 기록 + "POL-007과 cross-check 필요" hint

## During audit

### Severity 판정 엄격
- P0 = 시스템 동작 불가 / 정합성 깨짐 / 정책 위반 (실제로 운영 시 에러)
- P1 = 설계 일관성 손상 (운영은 되지만 추적성 깨짐)
- P2 = 개선 권장 (정보 풍부화)

confidence 낮으면 한 단계 낮게 잡기 (보수적).

### Evidence 필수
- gap 1건당 evidence 필드에 최소 1개 인용
- 인용 형식:
  - schema/list_items 결과: `list_items(type=api_endpoint) 35 items, DFEAT 매핑 합집합 32, orphan 3: [API-X, API-Y, API-Z]`
  - description: 직접 quote (마크다운 ` ``` ` 코드 블록)
  - 1차 소스: 파일 경로 + 라인 (예: `ServiceImplOriginalSendLearning.java:212`)
  - 메모리: 메모리 entry quote

### auto_fixable 판정 보수적
- 의심스러우면 `false`
- 의미 변경 / 신규 ITEM 필요 / 사용자 결정 → 항상 `false`
- 단순 텍스트 추가·제거·정정만 `true`

### 가짜 gap 금지
- 도메인이 의도적으로 그 상태인 경우 (description에 명시) → gap 아님
- 예: 백엔드 전용 DFEAT는 SCREEN backing 없는 게 정상
- 예: 1차 시스템 그대로 운영 DFEAT는 v2 ERD 없음이 정상

### AC 검증 (ACC-004/005/006) 보수 룰 — acceptance 차원 한정
- [ ] **이중 인용 없으면 stale 보고 금지**: ACC-006(scenario 현행 불일치)은 evidence에 AC.when/then 줄 quote + 대상 UC.main_flow/DFEAT.description 현행 줄 quote가 동시에 있어야 함. 한쪽만이면 gap 아님.
- [ ] **deprecated 대조는 실제 status 확인**: ACC-004/005는 `list_items(include_retired=true)` 결과로 인용 대상이 실제 retired/deprecated 임을 입증해야 함. 추측 금지.
- [ ] **도메인 귀속 모호하면 skip**: AC가 이 도메인 소속인지 UC.covered_by_acceptances 역추적·notes 인용으로 확정 안 되면 보고 보류 (타 도메인 AC 오인 방지).
- [ ] **신규 AC·재작성은 항상 사용자 결정**: ACC-001/002 부재·ACC-004/006 stale은 시나리오 확정이 필요하므로 `auto_fixable=false`. forward 등록 누락(ACC-007)만 `true`.

### 양방향 정합 (COV-7/8/9) 보수 룰 — coverage 차원 한정
- [ ] **기준 없으면 검사 안 함**: 도메인 description에 책임 목록·영역 매트릭스가 둘 다 없으면 COV-7/8/9 전부 skip + `unable_to_verify` 명시 (COV-1만 보고). 기준 없는 곳에 억지 볏어남 gap 생성 금지.
- [ ] **이중 인용 없으면 보고 금지**: COV-8/9는 evidence에 도메인 책임 줄 quote + DFEAT description 줄 quote가 동시에 있어야 함. 한쪽만이면 gap 아님.
- [ ] **거친 기준 관용**: 도메인 description이 coarse한 건 정상. DFEAT가 그 책임 범위 안에서 더 구체적인 건 볏어남(COV-8) 아님. "명백히 다른 책임 영역"일 때만 COV-8.
- [ ] **볏어남은 전체 대조로만**: COV-8은 도메인 책임 인벤토리 전체를 evidence에 나열하고 "어디에도 안 맞음"을 입증해야 함. 부분 인상 기반 보고 금지.
- [ ] **재배치는 항상 사용자 결정**: COV-8 오분류·COV-7 미커버는 belongs_to_domain 재배치/DFEAT 신규/책임 재정의가 필요하므로 항상 `auto_fixable=false`.

## Post-audit

### 출력 형식 엄격
- YAML 한 블록만 출력 (자유 텍스트 절대 금지)
- gap.id 형식 준수: `D<NNN>-<DIM>-<순번>` (예: D002-LINK-001)
- summary 카운트 정확 (gaps 배열 길이와 일치)

### Cross-dimension 단서
- 다른 차원 auditor가 함께 봐야 할 단서는 `notes_for_main.cross_dimension_hint`에:
  - 형식: `<this dim gap id> ↔ <other dim 예상 gap type>`
  - 예: `D002-STL-004 ↔ POL-009 (legacy_source 누락)`

## 절대 금지
- [ ] ITEM 수정 (read-only)
- [ ] create_item / update_item / delete_static_render 호출
- [ ] Agent 도구 호출 (재귀 방지)
- [ ] 사용자 직접 질문
- [ ] 자유 텍스트 보고
- [ ] 다른 dimension 룰 침범

## 자가 검증 (보고 직전)
1. dimension이 입력값과 일치하는가?
2. 모든 gap에 evidence 인용 있는가?
3. summary 카운트 = gaps[] 길이 인가?
4. gap.id 형식 일관성?
5. auto_fixable 판정이 보수적인가?
6. cross_dimension_hint 누락 없는가?
