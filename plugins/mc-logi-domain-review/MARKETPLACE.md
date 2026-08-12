# mc-logi-domain-review — Logicraft Domain Auditor

Logicraft 도메인을 **10 차원 병렬 감사**해 설계 갭을 검출하는 **read-only** 스킬. ITEM은 절대 수정하지 않고 검출만 — 후속 수정은 사용자가 mc-logi-update를 별도 호출.

## 10 차원
| 차원 | 검출 대상 |
|---|---|
| **coverage** | 도메인 책임↔DFEAT 양방향 정합, DFEAT→UC/SCREEN/SEQ backing, orphan API |
| **links** | forward/backward link 무결성, deprecated 참조 잔재, unresolved_links |
| **schema** | DFEAT.persists↔ERD, API request/response↔ERD 컬럼, brownfield enum |
| **stale** | stale=true·deprecated 잔재·brownfield 메타 누락 |
| **policy** | ADR 정책 위반(1차 보존·BFF 제거·8대 이벤트·data scope·JWT 헤더·통신 방향) |
| **acceptance** | AC(인수기준)가 UC/DFEAT/REQ를 검증하는지 커버리지 + AC 본문 현행성 |
| **requirement** | RFP(원천)↔REQ↔도메인 정합·stale·추적성·divergence·책임 경계 |
| **content** | 제목↔본문 의미 일치·형제 rotation 오염·장황·핵심 매몰·이력 혼입 |
| **diagram** ⭐ | CDIAG·C4가 활성 DFEAT를 정형 depicts로 그리는지 + 본문 stale body(DIAG-005) |
| **test_scenario** ⭐ | 통합/시스템 시험 TEST가 핵심 흐름·REQ/NFR을 검증하는지 + steps 현행성 |

## 동작
- 사용자가 "D002 검토해줘" / "다이어그램 반영 확인" / "통합시험 시나리오 검토" 등을 요청
- `logi-domain-auditor` 에이전트 10건을 한 메시지에 병렬 실행(rate limit 시 5+5 배치)
- 각 차원 auditor는 해당 dimension 룰만 적용, 구조화 YAML(gaps[]+summary) 반환
- 메인이 합산·중복 병합·P0/P1/P2 정렬 → Markdown 리포트 + mc-logi-update 자동수정 후보 분리
- 부분 호출 가능: "AC만"→acceptance, "RFP 정합"→requirement, "C4 반영"→diagram 단독

## 1.3.0 신규 (8→10 차원)
- **diagram**: 신규 DFEAT가 다이어그램에 자동 미반영되던 사각지대를 차원화. `list_diagram_coverage` MCP로 missing/폐기참조/dangling 검출 + **DIAG-005 본문 구모델 stale body**(depicts는 정상이나 components/classes description이 폐기 테이블·구 API·superseded ADR 참조 — D002 CMP-002 실증, depicts 레벨 도구로 안 잡힘 → 본문 정독 필수).
- **test_scenario**: 통합(cross-UC end-to-end)·시스템(REQ/NFR 검증) 시험 시나리오 TEST가 도메인 핵심 흐름·책임 REQ/NFR을 빠짐없이 검증하는지(커버리지 TST-001/002) + steps 본문이 폐기 ITEM·옛 흐름/화면/API를 검증하지 않는지(현행성 TST-003~005) 검토. **AC(acceptance)와 짝** — AC=단위/인수기준, TEST=통합/시스템 레벨.

## 함께 쓰는 스킬
- **mc-logi-update** — 검출된 갭을 입력으로 받아 cascade 수정(diagram/test_scenario cascade 섹션 짝)