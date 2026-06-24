# design-prompt.md — 로컬 디자인 작성 지침

Phase 2 에서 **Claude 가 직접** 디자인 HTML/CSS 를 작성할 때 따르는 지침(외부 디자인 도구 없음 — Claude 가 작성 주체).
`{{...}}` 슬롯은 `kit-input.md` 매핑대로 Phase 1 에서 채운다.
슬롯 이름은 kit-input.md 와 **정확히 일치**: `{{DS_TOKENS}}` · `{{SCREEN_STRUCTURE}}` · `{{WIREFRAME_REF}}` · `{{COMPONENT_CATALOG}}` · `{{SCREEN_ID}}` · `{{SURFACE}}`.

---

## 1. 생성 프롬프트 템플릿 (surface 1개당 1회)

```
역할: 너는 공공 디지털 서비스 화면을 디자인하는 시니어 프로덕트 디자이너다.
주어진 화면 골격(와이어프레임)을 **보존**하면서, 디자인 시스템 토큰으로 **프로덕션 수준의 고충실도 화면**을
완성한다. 이것은 "흑백 와이어프레임을 컬러로 칠하는" 작업이 아니다 — 와이어프레임에 없는 디자인 결정을
입히는 작업이다(아래 §디자인 지시).

## 대상
- 화면: {{SCREEN_ID}} / surface: {{SURFACE}}
- 셸(헤더·사이드바·푸터)은 그리지 않는다. 화면 본문만.

## 디자인 시스템 (이 토큰만 사용 — 절대 규칙)
{{DS_TOKENS}}

> 위 토큰의 색(base hex/scale)·타이포(size/weight/line-height)·간격·radius·**font-family** 만 사용한다.
> 임의 hex(#RRGGBB)·임의 px·임의 폰트 직접 입력 금지. 토큰에 없는 값이 필요하면 가장 가까운 토큰으로 대체하고
> 주석으로 표기한다. **토큰을 `:root` CSS 변수로 선언해 쓴다.**
> ★ 폰트: DS 에 font-family 가 있으면 본문/제목에 그 family 를 적용한다. `@font-face` 소스(woff2 URL)가 같이
>   내려왔으면 선언해 실제 렌더되게 하고, 소스가 없으면 family 선언 + 시스템 폴백만 두고 design-notes 에
>   "웹폰트 소스 미정" 으로 남긴다. DS 에 폰트가 아예 없으면 임의 폰트를 고르지 말고 시스템 기본 + 미정 기록.

## 화면 골격 (이 구조를 유지)
{{SCREEN_STRUCTURE}}

## 레이아웃 레퍼런스 (surface 배치 기준)
{{WIREFRAME_REF}}

> 위 와이어프레임의 섹션 구성·컴포넌트 배치·정보 순서를 보존한다. 영역을 추가/삭제하지 않는다.

## 사용 가능 컴포넌트 (이 카탈로그에서 매핑)
{{COMPONENT_CATALOG}}

> 카탈로그에 있는 컴포넌트로 매핑한다. 카탈로그에 없는 컴포넌트를 새로 발명하지 않는다.

## 디자인 지시 (와이어프레임에 없는 결정 — 반드시 반영)
1. 상태별 비주얼: 빈 상태(empty) · 로딩 스켈레톤 · 에러 · 상태 뱃지(예: pending/active/suspended)를
   각각 시각적으로 구분해 표현. 색만으로 구분하지 말고 아이콘+텍스트 병기.
2. 데이터 밀도: 테이블은 현실적인 다행 더미 데이터로 채우고, 긴 텍스트는 ellipsis 처리. placeholder 가
   아닌 그럴듯한 실제 데이터로.
3. 시각 위계: 섹션 간 여백 리듬으로 절차를 구분, 1차 액션과 보조 액션을 명확히 구분(primary vs outline 등),
   관련 정보를 그루핑.
4. 컴포넌트 디테일: 카드 그림자/보더, 버튼·입력의 hover·focus·disabled 상태, 인라인 검증 메시지를 표현.
5. 접근성/공공 제약: 본문 17px 이상 + line-height 충분, focus ring(3px outline + 2px offset), 인터랙티브
   요소 hit area 44×44 이상, 장식적 일러스트·그라데이션·neumorphism·auto-play 금지.
6. AI slop 회피 (★ 규격 안에서만): 토큰을 기계적으로 칠한 "제네릭 폼" 을 피한다 — 위계·여백 리듬·정렬·상태
   디테일을 **의도적으로** 다듬어 완성도를 올린다(refined minimalism = 정밀한 절제). 단 이는 **DS 토큰 경계
   안에서만**: 토큰 밖 개성 폰트·강한 색·분위기 배경(gradient mesh·noise·grain)·비대칭/그리드 파괴는 **금지**
   (그건 무규격 창작용 `frontend-design` 영역이며 규격 환경엔 부적합). "튀게" 가 아니라 "빈틈없이 정돈" 으로 차별화.

## 출력
- {{SURFACE}} 화면 1개를 완결된 HTML + CSS 로 출력한다(CSS 변수로 토큰 선언 포함).
- 토큰을 벗어난 임의 색/간격이 없어야 한다.
```

---

## 2. 반복 지시 (게이트1 — 프리뷰 확인 후 재프롬프트)

프리뷰(로컬 파일/렌더 URL)를 사용자에게 보여준 뒤 피드백을 받으면, 위 지침을 유지한 채 **델타만** 반영해 재작성.
골격·토큰 규칙은 유지하고 변경 요청만 적용한다.

예시 델타:
```
이전 디자인을 기반으로 아래만 수정한다(골격·토큰 규칙은 유지):
- 상태 뱃지를 디자인 시스템 semantic 색(success/warn/error/info)으로 교체
- 메트릭 카드 그리드를 3열로
- pending 행 강조를 약하게(배경 tint 만)
- 검색 폼과 목록 사이 여백을 한 단계 키움
```

골격을 벗어난 결과가 나오면(영역 추가/삭제, 와이어프레임과 다른 정보 순서) 다음을 강조해 재생성:
```
와이어프레임 {{WIREFRAME_REF}} 의 섹션 구성과 정보 순서를 반드시 보존하라. 영역을 추가하거나 빼지 말 것.
```

---

## 3. 슬롯 채우기 체크리스트 (Phase 1)

- [ ] `{{DS_TOKENS}}` ← `_shared/design-system.md` 전량
- [ ] `{{SCREEN_STRUCTURE}}` ← `screens/{{SCREEN_ID}}/SCREEN-NNN.md` 골격
- [ ] `{{WIREFRAME_REF}}` ← `screens/{{SCREEN_ID}}/wireframe-{{SURFACE}}.html` (+ wireframe.css)
- [ ] `{{COMPONENT_CATALOG}}` ← `_shared/ui-catalog.md` 인덱스
- [ ] `{{SCREEN_ID}}` / `{{SURFACE}}` ← 대상 화면·surface
