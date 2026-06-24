# notes-template.md — design-notes.md 작성 템플릿

Phase 3 에서 회수 후 `screens/SCREEN-NNN/design/design-notes.md` 를 아래 골격으로 작성한다.
이 파일은 mc-logi-screen-implement 가 읽어 "이 디자인을 어떤 컴포넌트·토큰으로 구현할지" 판단하는 가이드다.

특정 프로젝트 값(실제 토큰명·컴포넌트 id)은 **키트에서 읽은 실제 값**으로 채운다 — 이 템플릿은 형식만 정의.

---

```markdown
---
screen: SCREEN-NNN
generated_at: <ISO8601>
screen_design_item: <Phase 5 역등록 SD-NNN (designs → SCREEN-NNN)>
design_render_urls: <SD render URL 목록 (render_id=와이어프레임 동일)>
surfaces: [main, detail, ...]            # 생성한 surface 키 목록
ds: <design-system.md 의 DS id/이름>     # 키트의 실제 DS (예: DS-001) — 특정 DS 가정 안 함
source_wireframes: [wireframe-main.html, ...]  # 골격 출처
generated_by: mc-logi-screen-design
---

# SCREEN-NNN 디자인 노트

## § 디자인 결정 (와이어프레임 대비 추가분)

> 와이어프레임 골격에 없던, 이 디자인이 내린 결정. implement 가 이 시각 의도를 재현하도록.

- 상태별: <빈 상태/로딩 스켈레톤/에러/상태 뱃지를 어떻게 표현했는지 — 1줄씩>
- 데이터 밀도: <테이블 다행·긴 텍스트 처리 방식>
- 시각 위계: <여백 리듬·1차/보조 액션 구분·그루핑>
- 컴포넌트 디테일: <카드·hover/focus/disabled·인라인 검증 등>

## § 컴포넌트 · 토큰 매핑

> 화면 영역 → ui-catalog UI-NNN + design-system 토큰명. implement 가 그대로 구현에 쓴다.
> ★ 레포에 이미 대응 base 컴포넌트(예: Badge·Table·Pagination)가 있으면 그것을 **우선** 매핑하고,
> 디자인이 직접 만든 tint/raw hex 는 그 컴포넌트 variant(예: `Badge shape="bg-light" color="success"`)로
> 흡수한다 — raw hex 를 구현에 그대로 옮기지 말 것. (성숙한 토큰·컴포넌트 체계가 있는 레포에서 이 매핑이 핵심 가치)

| 화면 영역 | 컴포넌트 (ui-catalog) | 주요 토큰 (design-system) | 비고 |
|---|---|---|---|
| <예: 목록 테이블> | <UI-NNN 이름> | <color/spacing/typography 토큰명> | <상태/variant> |
| ... | ... | ... | ... |

## § surface 파일 인덱스

| surface | 파일 | SCREEN surface 대응 |
|---|---|---|
| main | design-main.html | 목록 페이지 |
| ... | design-{surface}.html | ... |

- 공유 스타일: design.css
- 스크린샷: design-{surface}.png (있으면)

## § 역등록 기록 (Phase 5 에서 실행)

확정 디자인을 logicraft **screen_design(SD-NNN) ITEM** 에 `upload_design_render` 로 올린다(static_render 아님 —
SD 가 디자인의 전용 자리). 스타일은 `css` 파라미터로 분리 전달:

​```
# SD 없으면 먼저 create_item(type=screen_design, data.title 필수, data.designs_screen="SCREEN-NNN")
upload_design_render(
  project_id=<키트 frontmatter 값>, item_id="SD-NNN",
  render_id="<와이어프레임과 동일: main|detail-relay|...>", surface="page|modal|...",
  label="<화면명> — 고충실 디자인", uploaded_by="claude-screen-design",
  html=<design-{surface}.html 본문(인라인 <style>·design.css link 제거)>,
  css=<design.css 본문>          # ★ {render_id}.css 로 서빙, wireframe.css 미주입
)
​```

- **render_id·surface 를 screen_spec 와이어프레임과 동일하게** → 비교 뷰에서 짝지어짐. SD 는 별 ITEM 이라 와이어프레임 미손상.
- ⚠️ 렌더가 `<script>` 제거할 수 있음 → 시안은 무 JS·CSS-only.
- 역등록 결과(render_id·surface·action)를 아래 표/이 노트에 기록.
```

---

## 작성 규칙

1. frontmatter 의 `surfaces` 는 실제 생성한 surface 키 목록과 일치.
2. § 컴포넌트·토큰 매핑은 **추측 금지** — `_shared/ui-catalog.md` 의 실제 UI-NNN 과 `_shared/design-system.md`
   의 실제 토큰명만. 카탈로그/토큰에 없으면 `⚠️ 미정` 으로 표기.
3. § 역등록 기록은 Phase 5 에서 실제 업로드한 SD-NNN·render_id·surface·action 을 적는다(screen_design ITEM, css 분리 전달).
