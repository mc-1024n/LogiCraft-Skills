# mc-logi-integration-bootstrap — 외부 연동 부트스트랩

설계 ITEM(FEAT/DFEAT) 본문에 흩어진 **외부 시스템 의존을 자동 발굴**해 **EXTSYS + INT 카탈로그로 일괄 등록**하는 부트스트랩 스킬입니다. 빈 외부연동 카탈로그를 한 번에 채울 때 씁니다.

## 무엇을 하나

`discover_external_integrations` MCP 도구로 FEAT/DFEAT/API 본문을 스캔 → 외부 시스템 후보를 휴리스틱별로 추출 → **사용자 검토 2회 게이트**를 거쳐 `register_external_system` × N, `register_integration_point` × M 호출.

## 언제 쓰나

- 프로젝트에 EXTSYS/INT 가 거의 없는데 FEAT/DFEAT 엔 외부 의존 언급이 흩어진 상황
- 2차 설계 / brownfield 프로젝트의 외부 연동 정리
- "외부 연동 정리해줘", "EXTSYS 발굴해줘", "외부 시스템 카탈로그 만들어줘"

## 언제 쓰지 않나

- C4·SEQ에 external 정형화 완료 → `promote_external_systems` 직접
- greenfield 신규 단건 → `register_external_system` 직접
- 단일 EXTSYS 수정/cascade → `mc-logi-update`

## 핵심 원칙

1. **AI 추정 금지** — vendor/owner_team/criticality/environments 는 사용자 답변만
2. **MCP 도구 경유** — `db.insert` 우회 금지
3. **검토 게이트 2회** — EXTSYS 등록 전, INT 등록 전 각각 confirm
4. **벤더 단위 1 EXTSYS** — sub-component 는 별도 INT
5. **discover 결과는 후보** — 사용자 검토 시 분류 수정 가능

## 효과 / 받는 것

- 흩어진 외부 의존을 **벤더 단위 EXTSYS + 방향별 INT**로 정형화
- 후보 표 + 4종 질문(vendor/owner/수용/environments)으로 **추정 없이 정확히** 등록
- 양방향 link·FK 검증은 `register_integration_point`가 자동 처리

## 사용 예

```
"KLID 외부 연동 정리해줘"
→ discover → 5 EXTSYS + 9 INT 후보 표
→ vendor/owner 질문 → 수용 4건 → register_external_system × 4
→ INT 후보 검토 → register_integration_point × 9 → 보고
```

휴리스틱(legacy_relay/genai/mobile_id/gpki/payment/slack/object_storage/smtp/public_data) 외 시스템은 자동 발견되지 않으므로, 그 경우 사용자 확인 후 수동 등록 안내.

## 관련 스킬

`mc-logi-update` · `mc-logi-domain-review`

> 미검증 마켓플레이스 항목 — 설치 전 SKILL.md 원문도 함께 확인하세요.
