# 다중 시나리오 분해 규칙

## 핵심 원칙
**독립 흐름 = SKETCH 분리** (사용자에게 묻지 않고 자동 분리). 사용자가 명시적으로 "한 sketch 로 통합" 요청 시만 통합.

## 분해 매트릭스

| 입력 신호 | 처리 |
|---|---|
| 단일 흐름 (start → end 1줄) | **SKETCH 1건**, chapters = `[main]` |
| "이 시나리오를 거치려면 ~ 시나리오가 필요" / "선행으로 ~" | **SKETCH 1건**, chapters = `[prerequisite, main]` (SK-001 패턴) |
| "그리고 별개로 ~ 시나리오" / "또 다른 흐름은 ~" | **SKETCH N건 자동 분리**, 각 `[main]` + linked_items 상호 참조 |
| "결정 미정인 부분은 ~" / "D-1 ~ 어떻게 할지" | **decisions 챕터** (role=context) + hotspot step |
| "만약 실패하면 ~" / "에러 시 ~" | **error_handling 챕터** (메인 SKETCH 내부) |
| "후속으로 ~" / "이후 ~" | **followup 챕터** (메인 SKETCH 내부) |
| "또는 / 대안으로 ~" | **alternative 챕터** (메인 SKETCH 내부) |

## 독립 흐름 판정 기준 (자동 분리 대상)

다음 중 **2개 이상 충족** 시 독립 SKETCH 로 자동 분리:
1. 다른 actor 가 트리거 (admin vs operator vs system)
2. 다른 도메인 경계 (D001 vs D007 vs D002)
3. 시간적/상황적 독립 (선행 ≠ 본 흐름이라 명시)
4. 출력이 분리 (메타·설정 등록 vs 실제 트랜잭션)

**1개만** 충족하면 같은 SKETCH 안 챕터로 분리 (setup/main).

## SK-001 사례 분석 (참고)

사용자 원문:
> "사용자가 GIS 에서 위치 선택 → CCTV 다중선택 → 이미지 요청 → ... → 영상 확정.
> 이 시나리오를 거치려면 생성형 ai 서버를 등록 하고 설정정보를 저장 하는 시나리오가 필요"

**판정**:
- 본 흐름 (op·서비스운영자, D003→D001→D007→D002, 시간적 본 작업, 출력=이벤트 영상)
- 선행 흐름 (admin·서비스관리자, D007, 시간적 선행, 출력=설정 row)

**자동 분리?** → 1번(actor) + 3번(시간) + 4번(출력) 충족 = 분리 가능
**하지만 SK-001 은 통합 등록** 함 — 선행이 본 흐름의 의존성으로만 의미 있고 양이 작아 (6 step) → **chapters=[prerequisite, main]** 통합

**룰 보강**: 선행 흐름이 **15 step 이하 + 본 흐름 의존성 명시** → 통합 (prerequisite 챕터). 그 이상이면 분리.

## 자동 분리 알고리즘

```
scenes = []
chunks = split_by_strong_separator(raw_prompt)  // "그리고 별개로", "또 다른 흐름"

for chunk in chunks:
    actors = extract_actors(chunk)
    domains = infer_domains(chunk)
    steps = estimate_steps(chunk)
    is_prerequisite = detect_prereq_keyword(chunk)  // "거치려면 ~ 시나리오 필요"

    if is_prerequisite and steps <= 15:
        attach_as_prerequisite_chapter(scenes[-1], chunk)
    elif independence_score(chunk, scenes) >= 2:
        scenes.append(new_sketch(chunk))
    else:
        attach_as_chapter(scenes[-1], chunk, infer_role(chunk))

return scenes
```

## chapters[].role 매핑 표

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

SKETCH-A, SKETCH-B 두 건 분리 등록 시:
- SKETCH-A.linked_items += [SKETCH-B]
- SKETCH-B.linked_items += [SKETCH-A]

(create_item 후 update_item 으로 양방향 백필)

## 분리 후 .md 파일 정책

- 각 scene = 별도 .md (`SK-001_xxx.md`, `SK-002_yyy.md`)
- frontmatter 에 `related_sketches: [SKETCH-A, SKETCH-B]` 명시
- 본 시나리오 .md 의 "## 3. 분해 scene" 섹션에 다른 sketch 링크

## 통합 임계값

| 조건 | 통합 (한 SKETCH) | 분리 (N SKETCH) |
|---|---|---|
| 선행이 본 흐름 의존성 | ✅ prerequisite 챕터 | — |
| 선행 step 수 ≤15 | ✅ 통합 | — |
| 선행 step 수 >15 | — | ✅ 분리 (linked_items) |
| 동일 actor + 동일 도메인 | ✅ 통합 (alt/followup 챕터) | — |
| 다른 actor + 다른 도메인 + 독립 출력 | — | ✅ 분리 (★ 자동) |
| 사용자 명시: "한 sketch 로" | ✅ 통합 (룰 무시) | — |
| 사용자 명시: "별도 sketch 로" | — | ✅ 분리 (룰 무시) |
