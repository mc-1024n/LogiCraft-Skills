# mc-logi-implement — 키트 기반 구현 오케스트레이터

`mc-logi-implement-kit` 이 내려받은 **로컬 구현 키트**(`docs/design/{slug}-{DOMAIN-ID}/`)를 단일 진실원으로 삼아, logicraft 도메인의 실제 코드 구현을 **스펙 → 플랜 → TDD 구현 → 반영 → logicraft 추적**까지 phase 게이트로 완주합니다.

## 무엇을 하나
- **Phase 0 키트 게이트**: 키트 존재·신선도 확인. 없으면 `mc-logi-implement-kit` 선행 호출, stale 이면 SYNC.
- **Phase 1 스펙**: `superpowers:brainstorming` 에 키트 컨텍스트(보존 영역·제약·미정 사항)를 주입해 스펙 문서 생성. [게이트: 승인]
- **Phase 2 플랜**: `superpowers:writing-plans` 로 키트 빌드 순서 = 태스크 순서. [게이트: 승인]
- **Phase 3 구현**: `feature/{slug}` 브랜치 + `superpowers:subagent-driven-development` (태스크별 스펙리뷰→품질리뷰) + 최종 전체 리뷰.
- **Phase 4 반영**: 클린 테스트·빌드 → (지시 시) DB 적용 → [게이트: 머지 방식].
- **Phase 5 추적**: `create_implementation_record` 로 IMPREC 기록 + 키트 현황·CLAUDE.md 갱신 + mc-logi-update 권고.

## 핵심 원칙
- **키트가 단일 진실원** — 도메인 규칙(보존 정책·제약·빌드 순서)을 스킬에 하드코딩하지 않고 전부 키트(`kit-contract.md` 매핑)에서 읽어 주입. 키트에 없는 지식은 지어내지 않음.
- **superpowers 재사용** — 스펙/플랜/구현은 검증된 superpowers 스킬을 그대로 쓰고, 그 사이에 "키트 컨텍스트 주입 + logicraft 왕복"만 접착.
- **추적 역동기화** — 구현 후 IMPREC 쓰기만 (설계 ITEM 수정은 `mc-logi-update`, 키트 생성은 `mc-logi-implement-kit`).
- **phase 재개** — "플랜부터", "구현만", "추적만" 등 인자로 중단 지점부터 재개.

## 호출 예
"D005 구현해줘" / "키트대로 구현하자" / "구현 계획 세우고 구현까지" / "DOMAIN-003 구현 시작" / "/mc-logi-implement"

## 패밀리
`mc-logi-implement-kit`(키트 다운로드) → **`mc-logi-implement`**(구현) → `mc-logi-implement-review`(코드↔키트 정합 점검) · `mc-logi-update`(설계 수정) · `mc-logi-domain-review`(설계 갭 검출).