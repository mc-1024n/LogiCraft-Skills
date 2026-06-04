# Dimension: Content (내용 명료성)

> ITEM 본문(서술 필드)이 **제목·구조 필드가 말하는 그 ITEM 을 정확·명료하게** 서술하는가.
> 구조(링크·필드)는 멀줦한데 자연어 본문이 틀리거나 장황한 갑. 다른 차원이 못 잡는 사각지대 (D006 DFEAT-025/073/074 rotation 오염 실증 — Session 121).

## 검토 대상
도메인 내 모든 active ITEM 의 서술 필드: description / goal·user_story / name·title 정합. **진실원 = 구조 필드** (title, user_story, persists_in_tables·implemented_by_endpoints, realizes_dfeats·related_screens, implements_in_modules·ubiquitous_language).

## 갑 유형
| 유형 | 정의 | severity |
|---|---|---|
| CNT-001 | 제목↔본문 불일치 — title 과 description이 서로 다른 기능 서술 | P0 |
| CNT-002 | 형제 ITEM rotation 오염 — 같은 도메인 형제 ITEM 끼리 본문이 뒤바뀌마 | P0 |
| CNT-003 | 과잉 장황 — 핵심을 1~2문장 요약 가능한데 만연체 | P1 |
| CNT-004 | 핵심 매몰 — 핵심 책임이 장황한 서술에 묻힘 | P1 |
| CNT-005 | 변경이력 본문 혼입 — description에 "Session NN·vN cascade" 누적 (brownfield.notes로 가야) | P1 |
| CNT-006 | 중복 서술 — 본문 내 반복 / user_story↔description 동어반복 | P2 |
| CNT-007 | 빈약 — description 30자 미만 또는 일반론 | P2 |

## 작업 절차
1. active ITEM 목록 (deprecated 제외).
2. 각 ITEM get_item 본문 정독 + 구조 필드 수집.
3. 제목↔본문 대조 (CNT-001/002).
4. 형제 교차 확인 (CNT-002): title은 다른데 description 첫 문장이 형제 것과 동일·유사면 rotation 오염 의심.
5. 명료성 점검 (CNT-003~007).
6. 갑 발견 시 fix_hint에 올바른 서술 초안 포함.

## 주의
- read-only — 검출·초안 제안만. 수정은 mc-logi-update.
- deprecated ITEM 제외 (active만). 단 deprecated 본문이 active 오염시 active 쪽 gap.
- CNT-005 변경이력 혼입은 관행상 흔함 — 가독성 실제 해치는 수준만 P1, 짧은 1~2줄 P2.
- CNT-001/002가 최우선. P0는 의미가 명백히 틀린 경우만.
- evidence에 title + 구조필드값 + 어긋난 description 인용을 함께 넣어 모순 증명.
