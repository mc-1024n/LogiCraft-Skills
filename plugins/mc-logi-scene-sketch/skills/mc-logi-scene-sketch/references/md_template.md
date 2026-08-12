# .md 표준 템플릿

경로: `./docs/scene-sketch/SK-{nnn}_{slug}.md`

```markdown
---
sketch_id: SKETCH-{nnn}        # 등록 후 백필 (등록 전 비움)
sketch_version: {n}            # 등록 후 백필
project_id: {uuid}
domain_id: DOMAIN-{NNN}        # 선택 (cross-domain 시 비움)
date: YYYY-MM-DD
status: draft                  # draft / reviewed / promoted / archived
scenes: 1                      # 분해된 scene 수
tags: [scenario-sketch, auto-registered, ...]
---

# SK-{nnn} {제목}

> **로컬 원천**: `./docs/scene-sketch/SK-{nnn}_{slug}.md`
> **Logicraft**: SKETCH-{nnn} (등록 후 ID + version)

---

## 1. 사용자 원문 (verbatim — ★ 가공 금지)

{raw_prompt 그대로}

## 2. AI 정제 요약

**목적** / **핵심 변경** / **도메인 경계**

## 3. 분해 scene ({N}개)
### Scene A: {제목} (SKETCH-{nnn})
- chapters / actors / 요약 단계

## 4. 추가 고려사항
- 누락 결정 (D-1, D-2...) / 외부 의존 / 데이터 정합 위험

## 5. 선행 작업
- 기존 ITEM rename / 신규 ADR / 다른 SKETCH 선행 / 외부 협의

## 6. 예상 cascade 규모
| 카테고리 | 신규 | 보강 | Deprecated |

## 7. linked_items 후보

## 8. 사용자 검토 (자동 등록 모드는 SKIP)

## 9. 등록 결과 (백필)

## 10. 다음 단계
```

## slug 명명 규칙
- 제목에서 한글·영문·숫자만 추출, 공백 → `_`, 특수문자 제거, 50자 이내
- 예: `배경이미지_요청_AI영상생성`

## 다중 scene 일 때
- scene 1개 = .md 1개 = SKETCH 1건
- 파일명 연번, frontmatter 에 `related_sketches: [...]` 명시

## frontmatter 갱신 정책
- 등록 전: sketch_id/version 비움 → 등록 후 백필 → status 변경 시 동기화
