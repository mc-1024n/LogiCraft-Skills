# 증적 판정 지침 — 경위 조각에서 `evidence` 항목 뽑기

## 무엇을 하나

수용기준(acceptance)·구현기록(implementation_record) 본문에서 분리한 **경위** 조각 중,
**검증·증적 기록**을 `evidence` 칸의 구조로 옮긴다. `evidence` 는 「무엇으로 확인했나」를 적는 자리다 —
누가(verified_by)·언제(verified_at)와 별개로, **다시 찾아갈 수 있는 위치**를 남기는 게 핵심이다.

`evidence` 항목 모양:

| 칸 | 뜻 | 규칙 |
|---|---|---|
| `type` | 갈래 | `test_case`(시험 케이스·spec 파일·시나리오 ID) · `test_run`(한 번의 실행 — 실행 일시·CI·e2e 판) · `document`(문서·CO·보고서) · `screenshot` · `log` · `external_link`(URL) · `code`(코드 위치·커밋) |
| `reference` | 다시 찾아갈 위치 | **조각에 글자 그대로 있는 문자열**(파일 경로·spec 이름·시나리오 ID·커밋 해시·URL·CO 번호). 지어내거나 고쳐 쓰면 거부된다 |
| `captured_at` | 언제 | 조각에 `YYYY-MM-DD` 가 **글자 그대로** 있을 때만. 시각까지 있으면 ISO 로 |
| `result` | 결과 | `pass`·`fail`·`inconclusive` — **`result_quote`(조각의 원문 구절)에 결과 낱말**(통과·passing·실패·failing·보류·blocked·inconclusive·조건부 등)이 있어야 한다 |
| `voided_reason`·`voided_at` | 무효 처리 | 조각이 「void·무효·철회」를 말할 때만 |

## 판정

- 조각이 검증 기록이 **아니면**(설계 변경·결정 경위·정정 이력) `items: []`.
- 한 조각에 증적이 여럿이면 여럿. 같은 위치를 두 번 적지 마라.
- 확신이 없으면 넣지 마라 — 빈 것이 틀린 것보다 낫다. 원문은 버전 이력에 남는다.
- ☠️ `reference` 에 설명문을 넣지 마라(「e2e 통과」 ✗ → `ac-098-registration-failed-recovery` ✓).
- ☠️ 날짜가 조각에 없으면 `captured_at` 를 비워라 — 다른 조각·추측으로 채우지 마라.

## 입력·출력

- 입력: 후보 파일 — `[{cid, item, type, title, text}]`
- 출력: `[{"cid": "...", "items": [{"type", "reference", "captured_at"?, "result"?, "result_quote"?, "voided_reason"?, "voided_at"?}]}]` — **모든 cid** 에 대해(검증 기록 아니면 `items: []`).
- JSON 은 Write 도구로 쓰고, 개수가 입력과 같은지 확인하라. ☠️ `pkill`/`kill` 패턴·stdin 대기 명령 금지. DB·서버 접근 금지.
