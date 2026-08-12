# 예시: SK-001 (배경이미지 요청 → AI 영상 생성)

실제 등록된 SKETCH-001 의 약식 본문. mc-logi-scene-sketch 가 어떻게 작동했는지 참고.

## 사용자 원문 (raw_prompt)

> 지금 기존 영상 요청을 이미지 요청으로 변경 해야해.
> 사용자가 GIS 에서 특정 지자체의 특정 위치를 선택 → 주변 cctv 조회 → 특정 cctv(다중선택 가능) 선택 → 이미지 요청 → ... → 영상 확정.
> 이 시나리오를 거치려면 생성형 ai 서버를 등록 하고 설정정보를 저장 하는 시나리오가 필요. 이 설정에는 base url, 동시 작업수, 원본 이미지 저장 위치, 완료 영상 저장 위치 등.

## 분해 결과

**판정**: 본 흐름 + 선행 설정 흐름. 선행 step 6개 (≤15) + 본 흐름 의존성 → **통합 등록** (chapters = [prerequisite, main, context])

= SKETCH 1건, chapters 3개

## 챕터 구성

| key | role | steps | 내용 |
|---|---|---|---|
| `setup` | `prerequisite` | 6 | admin 이 SCREEN-033 에서 genai 엔드포인트 등록 (5 신규 설정 키) |
| `main` | `main` | 16 | 본 시나리오 (GIS → 이미지 요청 → AI 작업 → 확정 → D002) |
| `decisions` | `context` | 10 | D-1 ~ D-10 hotspot |

## actors (10명)

- op (human, ACT-003)
- admin (human, ACT-002)
- klid (our_system)
- gis (ui, SCREEN-008)
- lib (ui, 신규 SCREEN)
- cfg_scr (ui, SCREEN-033)
- relay (external_system)
- ai (external_system, ACT-104)
- d002 (our_system, DOMAIN-002)
- nas (data_store)

## hotspot → 결정 → 등록 후 cascade

D-1 ~ D-10 결정 수집 → SK-001 cascade 시작:
- P1 D001 lifecycle (9 task, 14 ITEM)
- P2 genai 엔드포인트 (6 task, 6 ITEM)
- P3 D007 라이브러리·AI·확정 (12 task, 13 ITEM)
- P4 D002 경계 (5 task, 5 ITEM)
- **총 ~50 ITEM 변경**

## 등록 결과

- SKETCH-001 v5 (status=promoted)
- linked_items 24건 (양방향 backref)
- .md 진실원: `98. docs/scenario_sketch/SK-001_배경이미지_요청_AI영상생성.md`
- 신규 ITEM 15건 (ADR 2·UC 4·API 4·SCREEN 1·EVT 1·SEQ 6) + 보강 다수

## 핵심 교훈 (skill 작성자용)

1. **narrative_text verbatim** — 사용자 원문 그대로. AI 정제는 별도 `## 2. AI 정제 요약` 섹션에만.
2. **선행 흐름 통합** — 6 step 이라 chapters[prerequisite] 로 통합. 100 step 이면 분리했을 것.
3. **hotspot 명시** — 결정 미정은 `decisions` 챕터 (role=`context`)에 모아 cascade 트리거.
4. **자동 등록 후 후속 진입** — SK-001 은 등록 직후 mc-logi-update cascade 진입했음. skill 자체는 등록까지만, cascade 는 안내만.
5. **linked_items 양방향** — 등록 후 백필 안 하면 backref 안 잡힘.
