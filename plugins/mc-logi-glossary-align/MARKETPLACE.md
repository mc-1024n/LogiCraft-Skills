# mc-logi-glossary-align

ERD 1건의 모든 컬럼(논리·물리명)을 LogiCraft 4계층 용어사전(도메인→단어→용어)에 정합시키고, 사업 사전 신규 등록 + ERD update + cascade까지 완주하는 오케스트레이터. 5 Phase로 등록 순서·AI 임의 INSERT 금지를 강제한다.

## 무엇을 하나
- **Phase 0 — 스코프**: target ERD·도메인·사업 ID 확정, ERD 크기 가드(≥50KB 덤프 분석).
- **Phase 1 — 현황 조사 + A/B/C 분류**: gov/program `compare_erd` → 비표준 영문(A)·사업 기존(B)·신규 등록(C) 분류, 9 md 세트 산출.
- **Phase 2 — 결정 게이트**: 디폴트(영문 rename·약어 유지·일괄)는 묻지 않고, 동의어 정책·KLID-BM 표준 충돌만 조건부 질문.
- **Phase 3 — 등록**: 사용자 승인 후 도메인→단어→용어 순서로 등록(절대 규칙), 충돌 시 기존 ID 재사용.
- **Phase 4 — ERD 정합**: `update_item` patch 2-round(논리명 → 영문 rename), gov compliance·coverage 추적.
- **Phase 5 — Cascade**: rename 영향 본문 grep → specialist 위임(동시 ≤3건).

## 어떤 효과
- gov compliance·통합 coverage를 정량 추적하며 ERD를 표준 용어로 정합.
- **gov→program→domain→word→term 5단계 + 등록 순서 절대 규칙** 강제 — 의존 역행 방지.
- **AI 임의 INSERT 금지·추정 금지** — 후보 제시 → 사용자 승인 후만 등록, cascade는 실제 본문 인용만 patch.

## 사용 예
- "D001 ERD 용어사전화"
- "ERD-005 논리/물리 명칭 정합"
- "용어사전 정합"

## 요구 사항
- **LogiCraft MCP**: `program_glossary_compare_erd` / `gov_compare_erd` / `gov_*`·`program_*` search / `suggest_term_from_words` / `program_word_create`·`program_glossary_create`(승인 후) / `update_item`(patch)
- **에이전트**: logi-update-specialist(cascade 위임)

## 구성
- `SKILL.md` — 5 Phase 절차·절대 규칙·도구 매트릭스
- `REFERENCE.md` — Session 95 실측 12 노하우·충돌 핸들링 레퍼런스

## 한계
- **ERD 전용** — ERD 외 ITEM은 mc-logi-update, 도메인 감사는 mc-logi-domain-review.
- specialist 동시 위임 ≤3건(5건 이상 소켓 끊김).
- 등록은 사용자 명시 승인 후만 진행(자동 INSERT 안 함).
