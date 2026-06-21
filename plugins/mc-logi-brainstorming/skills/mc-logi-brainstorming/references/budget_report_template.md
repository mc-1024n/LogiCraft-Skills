# 책정 리포트 템플릿 (budget_report_template)

산출 경로: `./docs/discovery/{slug}_budget.md`

```markdown
---
sketch_id: SKETCH-NNN
sketch_md: ./docs/scene-sketch/SK-nnn_{slug}.md
date: YYYY-MM-DD
author: claude
status: budgeted
---

# {시나리오 제목} — 산출물 책정 리포트

## 시나리오 출처
- scene-sketch: SKETCH-NNN ({제목})
- 진실원 .md: ./docs/scene-sketch/SK-nnn_{slug}.md

## 산출물 책정표
| 산출물 타입 | 후보 ID·제목 | 상태 | 근거 step | 예상 cascade |
|---|---|---|---|---|
| API endpoint | (신규) 영상 업로드 API | 신규 | step3 command | ~3 |
| ERD | ERD-008 (재사용) | 재사용 | step5 data_store | - |
| ADR | (신규) 재시도 정책 | 신규 | D-1 hotspot | ~2 |

## 책정 요약
- 신규 N건 / 재사용 M건 / 갱신 K건

## 결정대기 hotspot
- D-1: {결정 필요 항목}
- D-2: {결정 필요 항목}

## 다음 액션
- 신규/갱신 ITEM 실제 생성 → `mc-logi-update` 스킬
- hotspot 결정 수집 후 정책/이벤트 승급
```
