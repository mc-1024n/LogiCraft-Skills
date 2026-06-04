# Coverage Dimension

도메인 책임과 DFEAT 의 **양방향 정합**, 그리고 DFEAT 가 UC/SCREEN/SEQ 로 backing 되었는지 검토.

- **① 도메인 → DFEAT (누락)**: 도메인이 선언한 책임을 DFEAT 가 다 덮었는가
- **② DFEAT → 도메인 (볏어남·모자람)**: 각 DFEAT 의 책임이 도메인 책임 범위를 볏어나거나 모자라지 않는가
- **backing 정합**: DFEAT → UC/SCREEN, UC → SEQ, API → DFEAT

## 책임 인벤토리 추출 (STEP 0)

COV-7/8/9 는 도메인 description 을 단일 진실원으로 사용. 기준점 우선순위:
1. 핵심 책임 목록 (R1…Rn)
2. 없으면 책임 영역 매트릭스 (예 D002 A통계/B VLM/C검수/D업로드/E학습/F운영설정)
3. "책임 제외" 섹션 → ② negative 기준 (X1…Xm)
→ 1·2 둘 다 없으면 COV-1(P2) + COV-7/8/9 skip + `unable_to_verify`.

## 검토 룰

#### COV-1: 책임 인벤토리 기준 확립 (게이트) — 둘 다 없음 → P2 + 7/8/9 skip
#### COV-7: 도메인 책임 미커버 (① 누락) — 활성 DFEAT 0건인 Ri → P1 (핵심이면 P0)
#### COV-8: DFEAT 오분류 / scope creep (② 볏어남) — 인벤토리 어디에도 안 맞음 → P1, 제외 Xj 수행 → P0
#### COV-9: DFEAT 부분 실현 / 빈약 (② 모자람) → 핵심 P1, 단순빈약 P2
#### COV-2: DFEAT → UC backing 없음 → P1
#### COV-3: DFEAT → SCREEN backing 없음 (백엔드 전용 제외) → P1
#### COV-4: UC → SEQ realizes (happy 없으면 P0, error 없으면 P1)
#### COV-5: API → DFEAT 매핑 없음 (orphan API) → P0
#### COV-6: 1차 핵심 기능 vs 2차 DFEAT 매핑 (legacy_grep_enabled=true 시만) → P1

## Gap 분류 코드
- `D<NNN>-COV-001`: 책임 인벤토리 기준 부재 (게이트)
- `D<NNN>-COV-002`: DFEAT UC backing 없음
- `D<NNN>-COV-003`: DFEAT SCREEN backing 없음
- `D<NNN>-COV-004`: UC SEQ 없음 (happy/error)
- `D<NNN>-COV-005`: Orphan API (DFEAT 매핑 없음)
- `D<NNN>-COV-006`: 1차 기능 미매핑
- `D<NNN>-COV-007`: 도메인 책임 미커버 (① 누락)
- `D<NNN>-COV-008`: DFEAT 오분류 / scope creep (② 볏어남)
- `D<NNN>-COV-009`: DFEAT 부분 실현 / 빈약 (② 모자람)

## auto_fixable 정책
Coverage 차원은 거의 모두 `auto_fixable=false` (사용자 결정 필수).

## ★ 양방향 정합(COV-7/8/9) Evidence 강제 룰 — false positive 억제
1. 이중 인용 의무: COV-008/009 는 도메인 책임 줄 + DFEAT description 줄 동시 quote.
2. 볏어남 입증 책임: COV-008 은 인벤토리 전체(R1…Rn + 제외 X1…Xm) 나열 + "어디에도 안 맞음".
3. 거친 기준 관용: coarse description 안에서 구체적은 정상.
4. cross-dimension hint: COV-008 ↔ LINK-011.
