# 예시: SK-001 (배경이미지 요청 → AI 영상 생성)

실제 등록된 SKETCH-001 의 약식 본문. mc-logi-scene-sketch 가 어떻게 작동했는지 참고.

## 사용자 원문 (raw_prompt)
> 지금 기존 영상 요청을 이미지 요청으로 변경. 사용자가 GIS 에서 위치 선택 → CCTV 다중선택 → 이미지 요청 → ... → 영상 확정. 이 시나리오를 거치려면 생성형 ai 서버를 등록하고 설정정보를 저장하는 시나리오가 필요.

## 분해 결과
**판정**: 본 흐름 + 선행 설정 흐름. 선행 step 6개 (≤15) + 본 흐름 의존성 → **통합 등록** (chapters = [prerequisite, main, context])

## 챕터 구성
| key | role | steps |
|---|---|---|
| `setup` | `prerequisite` | 6 (admin genai 엔드포인트 등록) |
| `main` | `main` | 16 (GIS → 이미지 요청 → AI 작업 → 확정 → D002) |
| `decisions` | `context` | 10 (D-1 ~ D-10 hotspot) |

## 등록 결과
- SKETCH-001 → 결정 수집 후 cascade P1~P4 → 약 50 ITEM 변경 → status=promoted
- 신규 15건 (ADR 2·UC 4·API 4·SCREEN 1·EVT 1·SEQ 6) + 보강 다수

## 핵심 교훈 (skill 작성자용)
1. **narrative_text verbatim** — 사용자 원문 그대로. AI 정제는 별도 섹션.
2. **선행 흐름 통합** — 6 step 이라 prerequisite 챕터로. 100 step 이면 분리.
3. **hotspot 명시** — 결정 미정은 context 챕터에 모아 cascade 트리거.
4. **자동 등록 후 후속** — skill 은 등록까지, cascade 는 mc-logi-update 안내만.
5. **MCP 재연결 주의** — scenario_sketch enum 차단 시 신규 세션 재시도 (SKETCH-002 등록 시 실제 겪음).
