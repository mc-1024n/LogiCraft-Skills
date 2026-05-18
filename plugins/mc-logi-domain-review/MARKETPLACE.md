# mc-logi-domain-review — Logicraft 도메인 감사기

Logicraft 한 도메인을 **5개 차원으로 병렬 감사**해 설계 정합성 갭을 우선순위별로 뽑아내는 **read-only** 스킬입니다. ITEM을 수정하지 않고 **검출만** 합니다 — 수정은 `mc-logi-update`를 따로 호출.

## 무엇을 하나

`logi-domain-auditor` 에이전트 5건을 한 번에 병렬 실행해 도메인 소속 ITEM 전체를 다음 차원으로 점검합니다.

| 차원 | 보는 것 |
|---|---|
| **coverage** | DFEAT↔API↔UC↔SCREEN 매핑 누락, orphan ITEM |
| **links** | 단방향/끊긴 link, `implemented_by_endpoints` 누락 등 |
| **schema** | 스키마 불일치, 누락 테이블/필드 |
| **stale** | deprecated ITEM의 활성 참조, 오래된 인용 |
| **policy** | 메모리·ADR에서 추출한 정책 위반(예: BFF 잔재) |

## 언제 쓰나

- "D002 검토해줘", "DOMAIN-001 갭 찾아줘" 같은 도메인 정합 점검
- 도메인 작업/대규모 ITEM 추가 후 무결성 확인
- 다른 도메인 cascade 후 영향 점검
- cron + `/loop` 와 묶어 정기 audit

## 효과 / 받는 것

- **P0/P1/P2 우선순위 갭 리포트** (Markdown 표 + YAML 원본)
- `auto_fixable` 항목을 분리해 **`mc-logi-update` 입력 포맷으로 미리 변환** — 바로 이어서 수정 가능
- 도메인 전체를 한 번에 훑어 **사람이 놓치는 link/policy 위반**을 체계적으로 검출

## 사용 예

```
"D002 검토해줘"
→ 5차원 병렬 감사 → 18 gaps (P0:3 / P1:9 / P2:6)
→ 자동수정 가능 11건은 mc-logi-update 후보로 분리 보고

"D001 정책 위반만 확인해줘"   # 단일 차원만
"D001, D002 갭 검출"          # 여러 도메인 동시
```

## 한계

- **검출만** — 수정·자동 fix 없음 (의도적 분리)
- `list_items` 의 `domain_id` 필터 미지원 → `get_neighbors` 기반 우회 수집
- 코드 리뷰/중복 검출은 대상 아님 (`mc-code-reviewer`/`mc-code-hunter`)

## 관련 스킬

`mc-logi-update`(검출된 갭 수정) · `skill-creator`

> 미검증 마켓플레이스 항목 — 설치 전 SKILL.md 원문도 함께 확인하세요.
