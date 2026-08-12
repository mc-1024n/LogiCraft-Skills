# Event Storming sticky 색깔 — step.kind 분류 가이드

scenario_sketch 의 `chapters[].steps[].kind` 는 Event Storming 워크숍의 sticky 색깔 컨벤션을 따른다.
AI 가 자동 분류 시 아래 결정 트리 사용.

## 6종 enum

| kind | 색 | 정체 | 예시 |
|---|---|---|---|
| `command` | 🟦 파랑 | 사용자/액터의 **의도·요청** | "운영자가 CCTV 다중선택", "버튼 클릭" |
| `event` | 🟧 주황 | 시스템에서 발생한 **사실·결과** | "BackgroundImageUploaded", "Webhook 수신", "row INSERT" |
| `policy` | 🟪 보라 | **비즈니스 규칙·정책·로직** | "24h 중복 차단", "active 1건 강제", "재시도 상한 3" |
| `read_model` | 🟩 연두 | **조회·화면·UI 표시** | "라이브러리 목록 조회", "상세 진입", "GIS 표시" |
| `hotspot` | 🟥 빨강 | **미해결 질문·결정 대기** | "D-1 화면 진입점?", "재시도 정책?" |
| `note` | ⬜ 회색 | 메모·외부 시스템 처리·부연 설명 | "외부 처리 비결정적", "잠시 대기" |

## 분류 결정 트리

```
사용자/액터가 적극적으로 트리거하는 것인가?
├─ YES → 'command' (의도)
└─ NO → 시스템에서 발생한 사실/결과인가?
     ├─ YES → 'event' (이미 일어난 일)
     └─ NO → 규칙·정책·계산인가?
          ├─ YES → 'policy' (비즈니스 룰)
          └─ NO → 화면 조회·UI 렌더인가?
               ├─ YES → 'read_model'
               └─ NO → 미해결 질문/결정?
                    ├─ YES → 'hotspot'
                    └─ NO → 'note' (부연·외부)
```

## 안티패턴

| 잘못된 분류 | 정정 |
|---|---|
| "API 호출" → `command` | 사용자 의도가 아니라 시스템 동작 → `event` |
| "DB SELECT" → `event` | 조회 결과 표시면 → `read_model` |
| "재시도 3회" 단순 동작 → `event` | 규칙이면 → `policy` |
| 결정 미정 항목 → `note` 로 묻기 | 명확히 → `hotspot` (decisions 챕터로 분리) |
| 외부 AI 가 영상 생성 → `command` | 외부 시스템 처리 → `note` 또는 `event` |

## SK-001 사례 (참고)

```
1. op → GIS 진입 + CCTV 선택           [command]
2. 시스템 → 주변 CCTV 조회 결과 표시      [read_model]
3. op → 「배경이미지 요청」 클릭          [command]
4. klid → BackgroundImageRequested        [event]
5. 중계 → 이미지 추출 (외부, 비결정)      [note]
6. 중계 → BackgroundImageUploaded         [event]
7. klid → 상태 머신: requested→...        [policy]
8. op → 라이브러리 목록 조회              [read_model]
9. op → 「AI 작업 요청」 + 부분 메타       [command]
10. klid → GenAiJobRequested              [event]
11. ai → 영상 생성 (외부, 비결정)         [note]
12. klid → polling_interval_sec 마다 폴   [policy]   ← P3 에서 Webhook 으로 변경
13. klid → GenAiJobCompleted              [event]
14. op → 「확정」                         [command]
15. klid → GenAiVideoConfirmed            [event]
16. d002 → D002 검수 큐 등록              [event]

[D-1 ~ D-10]                              [hotspot]  ← decisions 챕터
```

## kind 별 description 톤

- `command`: 능동태 + 액터 명시 (예: "운영자가 ~ 클릭")
- `event`: 과거형/완료형 (예: "~ 완료", "~ 발행", PascalCase 이벤트명)
- `policy`: 규칙 명시 (예: "~ 시 ~ 함", "상한 N", "1건 강제")
- `read_model`: 조회·표시 동사 (예: "~ 목록 조회", "~ 표시", "~ 렌더")
- `hotspot`: 의문문 또는 옵션 나열 (예: "D-1 ~ 방식?", "옵션 A/B/C")
- `note`: 자유 텍스트 (외부 처리·부연·시간 비결정 등)
