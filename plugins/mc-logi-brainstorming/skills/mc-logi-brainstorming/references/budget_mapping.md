# Phase D 책정 매핑 규칙 — step/신호 → 산출물 타입

scene-sketch step kind(command/event/policy/read_model/hotspot/note) +
actor kind(human/our_system/external_system/ui/data_store/other) +
본문 신호를 산출물 타입으로 결정론적 매핑한다.

## 코어 7종
| 근거 신호 | 산출물 타입 |
|---|---|
| command (사용자/시스템 명령 step) | API endpoint |
| event (상태 변화 발생) | domain_event |
| read_model / ui actor (조회·표시) | SCREEN (또는 조회 API endpoint) |
| data_store actor (영속 데이터) | ERD |
| hotspot (미결 결정포인트) | ADR |
| actor=human 의 목표 단위 흐름 | UC (use_case) |
| 성능·보안·가용성·정합성 제약 언급 | NFR |

## 인프라·연동 4종
| 근거 신호 | 산출물 타입 |
|---|---|
| external_system actor / 외부 API 호출 | integration_point + external_system |
| 스키마 변경·데이터 이행 신호 | migration |
| 서버·큐·스토리지·배치 워커 언급 | infra_component |

## AI 산출물 6종 (시나리오에 AI/LLM 신호가 있을 때만)
| 근거 신호 | 산출물 타입 |
|---|---|
| LLM/모델 호출 | model_usage |
| 프롬프트 설계 필요 | prompt_template |
| 학습·평가 데이터 | ai_dataset |
| 품질 평가 기준 | eval |
| AI 사용 정책·제약 | policy |
| 가드레일·안전장치 | guardrail |

## 규칙
- 신호 없으면 해당 타입은 책정표에서 제외 (억지로 만들지 않음)
- 한 step 이 복수 타입 유발 가능 (command → API + 그 결과 event → domain_event)
- AI 6종은 프로젝트가 AI 성격일 때만 적극 책정, 아니면 생략
