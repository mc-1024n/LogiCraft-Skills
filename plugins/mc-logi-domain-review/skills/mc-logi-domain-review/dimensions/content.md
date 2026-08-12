# Dimension: Content (내용 명료성)

> ITEM 본문(서술 필드)이 **제목·구조 필드가 말하는 그 ITEM 을 정확·명료하게** 서술하는가.
> 구조(링크·필드)는 멀쩡한데 **자연어 본문이 틀리거나 장황한** 갭을 찾는다.
> 다른 7 차원이 못 잡는 사각지대 (D006 DFEAT-025/073/074 제목↔본문 rotation 오염이
> 이 차원 부재로 자동검출 실패한 실증 사례 — Session 121).

## 검토 대상

도메인 내 모든 active ITEM 의 **서술 필드**:
- `description` (DFEAT·DOMAIN·UC·SCREEN·ADR 등 — 주 대상)
- `goal` · `user_story` (UC·DFEAT)
- `name` / `title` 과 본문의 정합

**진실원 = 구조 필드.** 본문이 맞는지 판정할 때 다음을 기준으로 삼는다:
- title
- user_story (as/i_want/so_that)
- persists_in_tables · implemented_by_endpoints (DFEAT)
- realizes_dfeats · related_screens (UC)
- implements_in_modules · ubiquitous_language (DOMAIN)

## 갭 유형

| 유형 | 정의 | severity |
|---|---|---|
| CNT-001 | **제목↔본문 불일치** — title 과 description(첫 문장·요지)이 서로 다른 기능 서술. 구조 필드와 본문 모순 | P0 |
| CNT-002 | **형제 ITEM rotation 오염** — 같은 도메인 형제 ITEM 끼리 본문이 뒤바뀜 (예: 서비스요청 ITEM 에 공지 설명) | P0 |
| CNT-003 | **과잉 장황** — 핵심을 1~2 문장 요약 가능한데 만연체로 길거나, 한 문장이 너무 길어 의미 파악 어려움 | P1 |
| CNT-004 | **핵심 매몰** — 핵심 책임이 장황한 서술에 묻힘 / 구조(헤더·불릿) 없이 줄글이라 첫 눈에 안 들어옴 | P1 |
| CNT-005 | **변경이력 본문 혼입** — description 본문에 "Session NN 정합"·"vN cascade"·날짜별 메모 누적 (→ brownfield.notes·change_summary 로 가야 함) | P1 |
| CNT-006 | **중복 서술** — 본문 내 같은 내용 반복 / user_story↔description 동어반복 | P2 |
| CNT-007 | **빈약** — description 30자 미만 또는 의미 없는 일반론 ("이 기능은 사용자가 X 를 할 수 있게 합니다") | P2 |

## 작업 절차

1. item_catalog 에서 active ITEM 목록 확보 (deprecated 제외).
2. 각 ITEM 을 `get_item` 으로 **본문 정독** + 구조 필드 수집.
3. **제목↔본문 대조** (CNT-001/002): title·user_story·persists_in_tables·implemented_by_endpoints 가 가리키는 실제 책임과 description 첫 문장·요지가 일치하는가.
4. **형제 교차 확인** (CNT-002): 같은 도메인 형제 ITEM 끼리 description 을 나란히 놓고 본문이 섞이지 않았는지 확인. 특히 title 은 다른데 description 첫 문장이 형제 것과 동일/유사하면 rotation 오염 의심.
5. **명료성 점검** (CNT-003/004/005/006/007): 장황·핵심매몰·이력혼입·중복·빈약.
6. 갭 발견 시 gap entry 생성. **fix_hint 에 올바른 서술 초안 포함** (아래 규칙).

## fix_hint 작성 규칙 (mc-logi-update 입력용)

명료화 **방향을 구체적으로** 적되 실제 재작성은 안 한다 (검출·제안만):
- CNT-001/002: `description 첫 문장을 title·user_story·persists_in_tables 기준 기능 한 줄로 교정. 올바른 서술: "<초안>"`
- CNT-003 장황: `변경이력/부가설명 N줄을 brownfield.notes 로 이동, 본문은 핵심 책임 N불릿으로 재구조화`
- CNT-004 핵심매몰: `도메인 개요 1문단 + 핵심 책임 불릿 구조로 재편, 부가 설명은 하위 절로`
- CNT-005 이력혼입: `description 의 'Session NN…' 이력 줄을 brownfield.notes 로 이관, 본문엔 현재 상태만`

## 주의

- **read-only** — 절대 본문을 직접 수정하지 않는다. 검출·초안 제안만. 수정은 사용자가 mc-logi-update 로.
- deprecated ITEM 은 제외 (active 만). 단 deprecated 본문이 다른 active ITEM 으로 오염을 일으켰으면 active 쪽을 gap 으로.
- 변경이력 본문 혼입(CNT-005)은 **이 프로젝트 관행상 흔함** — 과하게 많이 잡지 말고, 본문 가독성을 실제로 해치는 수준(이력이 핵심보다 길거나 핵심을 가림)만 P1, 짧은 1~2줄 메모는 넘어가거나 P2.
- CNT-001/002(제목↔본문)가 **이 차원의 최우선**. 나머지는 보조. P0 는 의미가 명백히 틀린 경우만 (장황·문체는 P1/P2).
- evidence 에 반드시 **title + 구조필드값 + 어긋난 description 인용**을 함께 넣어 모순을 증명.

## gap 예시

```yaml
- id: D006-CNT-001
  severity: P0
  type: CNT-002
  affected_items: [DFEAT-074]
  reason: 제목(공지 관리)과 본문(페이지 가이드 설명) 불일치 — 형제 rotation 오염
  evidence: |
    title="공지 관리 (로그인 공지)", persists_in_tables=[notices, notice_dismissals],
    user_story.i_want="운영 공지를 등록·게시기간 설정" 인데
    description 첫 문장="각 화면(페이지)에 대한 도움말 가이드를 등록·수정..." (페이지가이드 DFEAT-073 서술).
  suggested_fix: description 첫 문장을 공지 기능으로 교정 (구조 필드 기준)
  auto_fixable: true
  fix_intent: |
    description 첫 문장을 공지 기능으로 교정. 초안: "운영 공지를 등록·게시기간 설정하고,
    로그인 시 게시기간 내 신규 공지를 모달로 노출하는 기능. '다시 보지 않음'(notice_dismissals) 지원."
```
