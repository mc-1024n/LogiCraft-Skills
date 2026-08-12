# 다중 시나리오 분해 규칙

## 핵심 원칙
**독립 흐름 = SKETCH 분리** (사용자에게 묻지 않고 자동 분리). 사용자가 명시적으로 "한 sketch 로 통합" 요청 시만 통합.

## 분해 매트릭스

| 입력 신호 | 처리 |
|---|---|
| 단일 흐름 (start → end 1줄) | **SKETCH 1건**, chapters = `[main]` |
| "이 시나리오를 거치려면 ~ 시나리오가 필요" / "선행으로 ~" | **SKETCH 1건**, chapters = `[prerequisite, main]` |
| "그리고 별개로 ~ 시나리오" / "또 다른 흐름은 ~" | **SKETCH N건 자동 분리** + linked_items 상호 참조 |
| "결정 미정인 부분은 ~" | **decisions 챕터** (role=context) + hotspot step |
| "만약 실패하면 ~" / "에러 시 ~" | **error_handling 챕터** (메인 내부) |
| "후속으로 ~" | **followup 챕터** |
| "또는 / 대안으로 ~" | **alternative 챕터** |

## 독립 흐름 판정 기준 (2개 이상 충족 시 자동 분리)
1. 다른 actor 가 트리거 (admin vs operator vs system)
2. 다른 도메인 경계
3. 시간적/상황적 독립 (선행 ≠ 본 흐름 명시)
4. 출력이 분리 (메타·설정 등록 vs 실제 트랜잭셔)

**1개만** 충족 → 같은 SKETCH 내 챕터로 (setup/main).

## 선행 통합 임계값
선행 흐름이 **15 step 이하 + 본 흐름 의존성 명시** → 통합 (prerequisite 챕터). 그 이상이면 분리.

## chapters[].role 매핑
| 분해 시 분류 | role |
|---|---|
| 선행 설정·등록·부트스트랩 | `prerequisite` |
| 본 시나리오 | `main` |
| 결정 미정 hotspot 모음 | `context` |
| 대안 흐름 | `alternative` |
| 후속 작업 | `followup` |
| 에러 처리 | `error_handling` |

★ `decisions` 자유 키 금지 — `context` 사용 (스키마 강제).

## linked_items 상호 참조 (분리 등록 시)
SKETCH-A, SKETCH-B 분리 등록 시 create_item 후 update_item 으로 양방향 백필.

## 통합 임계값 요약
| 조건 | 통합 | 분리 |
|---|---|---|
| 선행이 본 흐름 의존성 + ≤15 step | ✅ prerequisite 챕터 | — |
| 선행 step >15 | — | ✅ 분리 |
| 다른 actor + 다른 도메인 + 독립 출력 | — | ✅ 분리 (★ 자동) |
| 사용자 명시 "한 sketch 로" | ✅ 통합 | — |
| 사용자 명시 "별도 sketch 로" | — | ✅ 분리 |
