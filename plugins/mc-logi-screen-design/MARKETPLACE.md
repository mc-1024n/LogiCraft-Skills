# mc-logi-screen-design — 화면 키트 기반 고충실도 디자인 오케스트레이터

`mc-logi-screen-kit` 이 만든 로컬 화면 키트를 입력으로, **와이어프레임 골격을 보존한 고충실도 화면**을 Claude 가 직접 작성해 `screens/SCREEN-NNN/design/` 에 떨군다. 확정 디자인은 `screen_design`(SD) ITEM 으로 역등록된다.

## 왜 필요한가 — "컬러 와이어프레임" 이 아니다

와이어프레임을 그대로 두고 색만 입히면 디자인이 아니라 채색이다. 반대로 자유 창작에 맡기면 디자인 시스템 밖으로 나가 구현이 불가능해진다.

이 스킬은 그 사이를 잡는다 — **와이어프레임에 없는 디자인 결정**(상태별 표현·데이터 밀도·시각 위계·컴포넌트 디테일)을 입히되, **DS 토큰 경계 안에서** 한다. 토큰을 기계적으로 칠하는 게 아니라 위계·여백 리듬·디테일을 의도적으로 다듬어 제네릭한 결과(AI slop)를 피하고, 토큰 밖 폰트·색·장식(그라데이션·noise·grain)·그리드 파괴는 금지한다. **"절제를 장인정신으로"** 가 핵심이다.

## 원칙

| # | 원칙 |
|---|---|
| 1 | **키트가 단일 진실원** — 화면 구조·토큰·컴포넌트 카탈로그를 스킬에 하드코딩하지 않는다. 키트에 없는 도메인 지식은 지어내지 않는다 |
| 2 | **골격 보존, 디자인 추가** — 와이어프레임이 정한 sections·components·API 바인딩은 유지한다 |
| 3 | **DS 토큰 강제 + 접근성 검증** — 임의 hex/px 금지. raw hex grep 으로 검출하고, 토큰 색 조합의 명암대비를 WCAG 로 검사한다 |
| 4 | **컴포넌트는 그리되, 등록은 동의 후** — 카탈로그에 없는 컴포넌트는 당연히 새로 그려 화면을 완성한다. 다만 `ui_component` ITEM 등록은 사용자 동의 후에만 |

## 자기완결 (vendored)

공용 스킬이므로 **외부 형제 스킬에 의존하지 않는다.** WCAG 명암대비 검사기(`scripts/contrast_checker.py`)는 표준 라이브러리만 쓰는 자립 스크립트로 스킬 폴더에 동봉돼 있다 — 별도 설치가 필요 없다. 가져온 것은 코드가 아니라 **공개 표준(WCAG 2.1)의 자립 구현**뿐이다.

## Phase

```
Phase 0  키트 게이트        SCREENS.md 존재·신선도 확인. 없으면 screen-kit 선행, stale 이면 SYNC
Phase 1  디자인 입력 합성   design-system.md(토큰)·SCREEN-NNN.md(골격)·wireframe-*.html·
                            ui-catalog.md 를 읽어 디자인 프롬프트 슬롯에 주입
Phase 2  로컬 디자인 작성   surface 별 고충실 HTML+CSS 를 Claude 가 직접 작성(외부 도구 없음, 무 JS)
                            → 🚦 프리뷰 보고 반복
Phase 3  검증 & 노트        raw hex 검출 + WCAG 대비 검증 + design-notes.md 작성
Phase 4  키트 반영          SCREENS.md 에 산출물 인덱스 추가
Phase 5  역등록             screen_design(SD) ITEM 에 upload_design_render(css 분리)
Phase 6  컴포넌트 보강 권고 새 컴포넌트 안내 → 동의 시 register_ui_components(신규 한정)
```

**역등록의 요령** — HTML 은 `html`, 스타일은 **`css` 파라미터로 분리**해 올린다. `render_id`·`surface` 를 와이어프레임과 동일하게 맞추면 비교 뷰에서 **짝지어지면서도 와이어프레임을 덮어쓰지 않는다.**

## 함께 쓰는 스킬

`mc-logi-screen-kit`(선행 — 키트 생성) → **이 스킬** → `mc-logi-screen-implement`(구현. 와이어프레임보다 이 디자인을 우선 소비한다)

재개 지원: "입력합성부터" · "Phase N 부터" 로 중단 지점부터 이어갈 수 있다. 단 **Phase 0 키트 게이트는 재개 시에도 생략하지 않는다.**
