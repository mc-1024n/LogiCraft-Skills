# Event Storming sticky 색깔 — step.kind 분류 가이드

scenario_sketch 의 `chapters[].steps[].kind` 는 Event Storming sticky 색깔 컨벤션을 따른다.

## 6종 enum

| kind | 색 | 정체 | 예시 |
|---|---|---|---|
| `command` | 파랑 | 사용자/액터의 **의도·요청** | "CCTV 다중선택", "버튼 클릭" |
| `event` | 주황 | 시스템에서 발생한 **사실·결과** | "BackgroundImageUploaded", "row INSERT" |
| `policy` | 보라 | **비즈니스 규칙·정책** | "24h 중복 차단", "임계점 이상 시" |
| `read_model` | 연두 | **조회·화면·UI 표시** | "목록 조회", "상세 진입" |
| `hotspot` | 빨강 | **미해결 질문·결정 대기** | "D-1 화면 진입점?" |
| `note` | 회색 | 메모·외부 시스템 처리·부연 | "외부 처리 비결정적" |

## 분류 결정 트리

```
사용자/액터가 적극 트리거?
├─ YES → 'command'
└─ NO → 시스템 발생 사실/결과?
     ├─ YES → 'event'
     └─ NO → 규칙·정책·계산?
          ├─ YES → 'policy'
          └─ NO → 화면 조회·UI 렌더?
               ├─ YES → 'read_model'
               └─ NO → 미해결 질문/결정?
                    ├─ YES → 'hotspot'
                    └─ NO → 'note'
```

## 안티패턴

| 잘못된 분류 | 정정 |
|---|---|
| "API 호출" → command | 사용자 의도 아닌 시스템 동작 → event |
| "DB SELECT" → event | 조회 표시면 → read_model |
| "재시도 3회" 단순 동작 → event | 규칙이면 → policy |
| 결정 미정 → note | 명확히 → hotspot (decisions 챕터) |

## kind 별 description 톤
- `command`: 능동태 + 액터 명시
- `event`: 과거형/완료형 (PascalCase 이벤트명)
- `policy`: 규칙 명시 ("~ 시 ~ 함", "상한 N")
- `read_model`: 조회·표시 동사
- `hotspot`: 의문문 또는 옵션 나열
- `note`: 자유 텍스트 (외부 처리·부연)
