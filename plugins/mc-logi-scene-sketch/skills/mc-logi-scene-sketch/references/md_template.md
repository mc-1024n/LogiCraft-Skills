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

{raw_prompt 그대로 — 정제 손실 방지 위해 원문 보존}

---

## 2. AI 정제 요약

**목적**: {한 줄}
**핵심 변경**: {bullet}
**도메인 경계**: {D001/D007/... → 책임}

---

## 3. 분해 scene ({N}개)

### Scene A: {제목} (logicraft SKETCH-{nnn})
- **chapters**:
  - setup(prerequisite, {m} step): 선행 작업
  - main({n} step): 본 흐름
  - decisions(context, {k} hotspot): 결정 대기
- **actors**: {n}명 (human / our_system / external_system / ui / data_store)
- **요약 단계**:
  1. {actor} → {action}
  2. ...

### Scene B: {제목} (필요 시 SKETCH-{nnn+1})
...

---

## 4. 추가 고려사항

### 누락 결정 (hotspot → decisions 챕터)
- **D-1** {질문}: 옵션 A/B/C
- **D-2** {질문}: ...

### 외부 의존성
- {외부 시스템}: {계약 확인 필요 항목}

### 데이터 정합 위험
- {위험 1}
- {위험 2}

---

## 5. 선행 작업

- [ ] 기존 ITEM rename: {UC-xxx / DFEAT-xxx} → {새 의미}
- [ ] 신규 ADR 필요: {제목 후보}
- [ ] 다른 SKETCH 선행: {SKETCH-xxx}
- [ ] 외부 협의: {대상·내용}

---

## 6. 예상 cascade 규모

| 카테고리 | 신규 | 보강 | Deprecated |
|---|---|---|---|
| UC | {n} | {n} | {n} |
| API | {n} | {n} | {n} |
| ERD 컬럼/테이블 | {n} | {n} | {n} |
| SCREEN | {n} | {n} | {n} |
| DFEAT | {n} | {n} | {n} |
| SEQ | {n} | — | — |
| ADR | {n} | {n} | — |
| **총합** | {n} | {n} | {n} |

**예상 라운드**: P1 ~ P{n}

---

## 7. linked_items 후보 (자동 채움)

| ITEM | 관계 | 비고 |
|---|---|---|
| DOMAIN-{NNN} | 소속 | {도메인명} |
| UC-{NNN} | rename | {제목} |
| API-{NNN} | deprecated | {경로} |
| ... | ... | ... |

---

## 8. 사용자 검토 (자동 등록 모드는 SKIP)

- [ ] 정제본이 원문 의도와 일치
- [ ] 분해된 scene 분리 기준이 적절
- [ ] 추가 고려사항 누락 없음
- [ ] linked_items 후보가 정확

---

## 9. 등록 결과 (자동 등록 후 백필)

- **SKETCH-{nnn}** v{n} | status=`draft` | tags=[...]
- Logicraft URL: {ui_link} (있다면)
- 생성 시각: {ISO}
- linked_items 양방향 확인: {n}건 OK / {m}건 unresolved

---

## 10. 다음 단계

1. Hotspot D-1 ~ D-{m} 결정 수집
2. mc-logi-update cascade 진입 (P1 ~ P{n})
3. SKETCH status: draft → reviewed → promoted
```

## slug 명명 규칙
- 제목에서 한글·영문·숫자만 추출
- 공백 → `_`
- 특수문자 제거
- 50자 이내 절단
- 예: `배경이미지_요청_AI영상생성`

## 다중 scene 일 때
- scene 1개 = .md 1개 = SKETCH 1건
- 파일명: `SK-{nnn}_{slug}.md`, `SK-{nnn+1}_{slug}.md` 연번
- 각 .md frontmatter 에 `parent_sketch` 또는 `related_sketches` 명시 (선택)

## frontmatter 갱신 정책
- 등록 전: `sketch_id`, `sketch_version` 비움
- 등록 후: 자동 백필 (write file 다시)
- status 변경 시: frontmatter 동기화
