---
name: mc-logi-screen-design
description: mc-logi-screen-kit 이 만든 로컬 화면 키트(./docs/screen-design/{도메인슬러그}-{DOMAIN-ID}/)를 입력으로, 와이어프레임 골격을 보존한 고충실도 화면을 Claude 가 직접 작성해 screens/SCREEN-NNN/design/ 에 떨구는 화면 디자인 오케스트레이터 스킬. 사용자가 "SCREEN-027 디자인해줘", "화면 디자인해줘", "고충실도 목업 만들어줘", "D001 화면 디자인", "/mc-logi-screen-design" 등 화면 비주얼 디자인을 요청할 때 실행. 키트가 없으면 mc-logi-screen-kit 을 먼저 호출하고, 키트가 stale 이면 SYNC 재실행을 먼저 한다. 결과는 mc-logi-screen-implement 가 와이어프레임보다 우선 소비한다. 단순 흑백→컬러 치환이 아니라 와이어프레임에 없는 디자인 결정(상태별·데이터밀도·시각위계·컴포넌트 디테일)을 DS 토큰 안에서 입힌다(규격 내 AI slop 회피). 외부 디자인 도구 없이 Claude 가 직접 작성하고, 확정 디자인은 screen_design(SD) ITEM 에 upload_design_render(css 분리)로 역등록한다(와이어프레임과 비교 뷰 짝지음, 렌더 URL=프리뷰).
license: MIT
allowed-tools: Read, Write, Edit, Grep, Glob, Bash, ToolSearch, AskUserQuestion, TaskCreate, TaskUpdate, TaskList
metadata:
  version: "1.3.4"
  domain: logicraft-orchestration
  triggers: 화면 디자인, 화면 디자인해줘, screen design, 고충실도 목업, 고충실도 디자인, SCREEN-NNN 디자인, D001 화면 디자인, 화면 비주얼 디자인, 디자인 목업 만들어줘
  role: orchestrator
  scope: logicraft-screen-visual-design
  output-format: docs/screen-design/{slug}-{DOMAIN-ID}/screens/SCREEN-NNN/design/ (design-{surface}.html + design.css + design-{surface}.png + design-notes.md) + SCREENS.md design 인덱스 갱신 + logicraft screen_design(SD) upload_design_render(render_id=와이어프레임 동일, css 분리) + (선택) 새 컴포넌트 ui_component 보강 권고·동의 시 register_ui_components
  related-skills: mc-logi-screen-kit, mc-logi-screen-implement, mc-logi-update
---

# mc-logi-screen-design — 화면 키트 기반 고충실도 디자인 오케스트레이터

mc-logi-screen-kit 이 만든 로컬 화면 키트를 읽고, **키트 게이트 → 디자인 입력 합성 → 로컬 디자인 작성(Claude
직접) → 검증·노트 → 키트 반영 → screen_design 역등록 → ui_component 보강 권고**를 거쳐 `screens/SCREEN-NNN/design/`
에 프로덕션 수준 화면 목업을 떨군다. 이 스킬은 **절차만** 안다 — 어떤 토큰으로 색칠하고 어떤 컴포넌트를 쓸지는 전부 키트가 말한다.

> **디자인을 그리는 주체는 Claude 다 — 외부 디자인 도구(Claude Design 등)에 의존하지 않는다.** 디자인 결정·
> HTML/CSS 작성은 Claude 가 직접 하고, 프리뷰/호스팅은 로컬 파일 + logicraft `screen_design` 렌더 URL 로 갈음한다.

생태계 위치: `mc-logi-screen-kit`(준비) → **`mc-logi-screen-design`(디자인·옵셔널)** → `mc-logi-screen-implement`(구현).
이 단계를 건너뛰면 implement 는 기존대로 흑백 와이어프레임을 레이아웃 기준으로 쓴다(하위 호환).

## 핵심 원칙

1. **키트가 단일 진실원** — 화면 구조·디자인 토큰·컴포넌트 카탈로그를 이 스킬에 하드코딩하지 않는다.
   `kit-input.md` 의 매핑대로 키트 파일에서 읽어 디자인 작성에 반영한다. 키트에 없는 도메인
   지식을 지어내지 않는다(모르면 사용자에게).
2. **"컬러 와이어프레임" 이 아니라 "프로덕션 목업" + 규격 내 AI slop 회피** — 이 스킬의 존재 이유는
   와이어프레임에 **없는 디자인 결정**을 입히는 것이다(§Phase 2 / `design-prompt.md`). 단 그 결정은 **DS 토큰
   경계 안에서** 한다 — 토큰을 기계적으로 칠하는 게 아니라 위계·여백 리듬·상태·디테일을 **의도적으로** 다듬어
   제네릭(AI slop)을 피하되, **토큰 밖 폰트·색·장식(그라데이션·noise·grain)·그리드 파괴는 금지**(그건 무규격
   창작용 `frontend-design` 영역 — 규격 환경엔 부적합). "절제를 장인정신으로" 가 핵심.
3. **골격 보존, 디자인 추가** — 와이어프레임이 정한 sections/components/API 바인딩 골격은 유지하고,
   그 위에 디자인 시스템 톤으로 디자인을 완성한다. 골격을 바꾸지 않는다.
4. **DS 토큰 강제 + 접근성 검증** — 색·간격·타이포는 `_shared/design-system.md` 토큰만. 임의 hex/px 금지
   (implement D6 룰과 동일 기준). 회수 후 raw hex grep 으로 가볍게 검출(D4)하고, **토큰 색 조합의 명암대비는
   이 스킬에 동봉된 `scripts/contrast_checker.py`(WCAG) 로 검증(D5)** — 토큰을 *생성*하는 게 아니라 *이미 있는 조합*을
   검사할 뿐이라 "DS 진실원=logicraft" 원칙과 무충돌. ★ **자기완결 원칙**: 이 스킬은 logicraft 에 올려 누구나 쓰는
   공용 스킬이므로 **외부 형제 스킬(ui-design-system / ui-ux-pro-max 등)에 의존하지 않는다.** WCAG 검사 스크립트는
   표준 라이브러리만 쓰는 자립 스크립트로 **스킬 폴더에 동봉**(vendored)했다 — 외부 스킬 설치 불필요. ★ **디자인
   *생성* 은 Claude 직접** 한다 — `mc-design-master` 를 라우터로 호출하지 않고, `frontend-design`(창작 비주얼)·토큰/
   스펙 *생성* 스킬도 통합하지 않는다(원칙2 와 진실원 원칙에 어긋남). 외부 디자인 스킬에서 가져온 것은 "코드"가 아니라
   "공개 표준(WCAG 2.1 공식)의 자립 구현" 뿐이다.
5. **디자인 산출물 = screen_design(SD-NNN) ITEM 에 upload_design_render(css 분리)** — 확정 디자인을 SCREEN 을
   `designs` 하는 **screen_design 전용 ITEM** 에 올린다(Phase 5). HTML 은 `html`, 스타일은 **`css` 파라미터로 분리**
   → `{render_id}.css` 서빙·wireframe.css 미주입(고충실 시안). SD 는 screen_spec 과 별 ITEM 이라 **render_id·surface 를
   와이어프레임과 동일하게** 맞추면 비교 뷰에서 짝지어지면서 와이어프레임을 덮어쓰지 않는다. logicraft 쓰기는
   사용자 확정 디자인에 한함(SD 생성·업로드 전 1줄 확인).
6. **mc-logi-screen-kit 선행 종속** — 키트가 없으면 그 스킬을 먼저 실행하고, 키트가 오래됐으면
   SYNC 재실행을 먼저 한다.
7. **컴포넌트는 (디자인에선) 새로 그린다 — 단 logicraft 등록은 "동의 후" (ui_component 보강)** —
   ★ 화면 디자인 중 `_shared/ui-catalog.md` 카탈로그에 **없는 컴포넌트**(예: Button·Badge·ContentTile)는
   **당연히 새로 그려서 화면을 완성한다** — 컴포넌트가 없다고 화면을 못 그리는 게 아니다. 카탈로그가 0건이면
   사실상 **전부 신규**라 등록 대상이 된다. 다만 이 스킬은 그 "그린 컴포넌트"를 logicraft `ui_component` ITEM 으로
   **동의 없이 임의 등록하지 않는다.** "만들지 말라"가 아니라 **"동의 없이 등록하지 말라"**는 뜻이다. Phase 6 에서
   "이러이런 새 컴포넌트가 생겼으니 logicraft `ui_component` 를 보강하길 추천한다"고 **안내**하고, 사용자가
   동의("알겠다")하면 그때 `register_ui_components`(배치·idempotent)로 등록한다. **등록은 신규 한정** — 기존
   UI-NNN 수정/cascade 는 `mc-logi-update` 소관(이 스킬은 register_ui_components 만, 기존 ITEM 갱신은 안 함).
   카탈로그가 0건이어도 디자인은 중단하지 않는다(DS 부재와 달리 ui_component 부재는 하드 게이트 아님 —
   매핑을 `⚠️ 미정`으로 남기고 Phase 6 에서 일괄 보강 권고). **★ 등록한 경우 `mc-logi-screen-kit` SYNC 는
   필수** — 등록만 하고 SYNC 를 안 하면 로컬 카탈로그가 0건으로 남아 다음 작업이 등록을 못 본다(Phase 6-4).

## Phase 개요

```
Phase 0   키트 게이트        대상 화면/도메인 식별 → SCREENS.md 존재/신선도 확인.
                            없으면 screen-kit 선행, stale 이면 SYNC. CHANGED/RETIRED 영향 정리.
Phase 1   디자인 입력 합성   kit-input.md 매핑대로 design-system.md(토큰)·SCREEN-NNN.md(골격)·
                            wireframe-*.html(surface)·ui-catalog.md(컴포넌트) 읽어 컨텍스트 구성.
                            design-prompt.md 템플릿 슬롯에 주입.
Phase 2   로컬 디자인 작성  Claude 가 surface 별 고충실 HTML+CSS 를 design/ 에 직접 작성(외부 도구 없음).
                            DS 토큰만·골격 보존·AI slop 회피·무 JS. → [게이트1: 로컬/렌더 URL 프리뷰 → 반복]
Phase 3   검증 & 노트       raw hex 검출(D4) + WCAG 대비 검증(D5·contrast_checker.py) + notes-template.md 로
                            design-notes.md 작성.
Phase 4   키트 반영         SCREENS.md 에 design 산출물 인덱스 행 추가(로컬).
Phase 5   logicraft 역등록  확정 디자인을 screen_design(SD) ITEM 에 upload_design_render(css 분리)로 올림.
                            render_id=와이어프레임과 동일 → 비교 뷰 짝지음 / wireframe.css 미주입.
Phase 6   ui_component 보강  디자인에서 쓴 컴포넌트 ↔ ui-catalog.md 대조 → 새 컴포넌트 있으면 "logicraft
          권고               ui_component 보강 추천" 안내. 동의 시 register_ui_components 로 등록(새 것만).
                            ★ 등록했으면 screen-kit SYNC 필수(로컬 카탈로그 0→N 갱신).
```

재개: 사용자가 phase 를 지정하면("입력합성부터", "회수만", "Phase N 부터") 선행 산출물 존재를 확인하고
그 지점부터 진행한다. **Phase 0(키트 게이트)는 재개 시에도 생략하지 않는다.**

---

## Phase 0 — 키트 게이트 (선행 종속)

1. **대상 식별**: 화면/도메인 ID(SCREEN-NNN / DOMAIN-NNN / D001 등)와 프로젝트를 인자·대화·메모리에서
   확정. 불명확하면 `AskUserQuestion` 으로 질문.
2. **키트 탐색**: `docs/screen-design/*-{DOMAIN-ID}/SCREENS.md` 존재 확인.
   - **없음** → `Skill(mc-logi-screen-kit)` 를 먼저 실행해 키트 생성(사용자에게 선행 실행을 알림). 생성 후 계속.
   - **있음** → `version-master.md` 의 last sync 확인. 오래됐거나 사용자가 "최신으로" 요청 시 screen-kit
     SYNC 재실행 권고(간단 확인 후). SYNC 결과 **CHANGED/RETIRED 가 있으면** 목록을 보여주고 디자인 범위
     영향을 정리한 뒤 진행. RETIRED 화면은 디자인 대상 제외.
3. **키트 컨텍스트 적재**: `kit-input.md` 의 "Phase 0 적재" 목록을 읽는다 — `SCREENS.md` 전체(화면 목록·
   surface 집합·공유자산 인덱스·변경 알림) + `version-master.md` 헤더. 여기서 디자인 대상 화면 집합과
   surface 목록, 도메인 슬러그를 얻는다.
4. **Phase 0 보고** 후 Phase 1 진입.

## Phase 1 — 디자인 입력 합성

`kit-input.md` 의 주입 표대로 키트 파일을 읽어 `design-prompt.md` 템플릿 슬롯을 채운다.

0. **★ DS/토큰 부재·미선택 게이트 (착수 전 필수)**: `_shared/design-system.md` 가 **없거나** 토큰 섹션(color /
   typography / spacing / radius)이 **통째로 비어** 있으면 디자인 생성을 **중단**하고 아래 순서로 처리한다.
   `{{DS_TOKENS}}` 가 공집합이면 "이 토큰만 사용" 절대 규칙이 가리킬 대상이 없어 임의 hex 로 흘러 Phase 3 D4 에서
   떼로 터진다. **★ DS 의 진실원은 logicraft.** 단계적으로:
   - ① **(기본) 다운로드** — `mc-logi-screen-kit` (재)실행/SYNC 로 logicraft 의 design_system 을 `get_design_md` 로
     받아온다. 키트가 stale 이거나 design_system 타입을 안 받아둔 경우가 대부분 — 받아지면 그대로 진행.
   - ② 받아왔는데도 비어있음 → **logicraft DS 상태를 확인**한다(`list_items(type=design_system)`):
     · **DS 가 있고 활성(선택)돼 있는데 키트만 누락** → ①의 SYNC 로 해결.
     · **DS ITEM 은 있으나 선택(active/`is_in_use`)된 게 없음 / 여러 개라 모호** → 어느 DS 를 쓸지 사용자에게
       묻고(`AskUserQuestion`) `set_design_system_active` 로 선택한 뒤 SYNC → 진행.
     · **DS ITEM 자체가 0건** → 사용자에게 **"logicraft 에 디자인 시스템이 없습니다. 새 DS 를 생성·등록할까요?"**
       를 `AskUserQuestion` 으로 묻는다.
       - **동의** → 디자인 방향을 1~2개만 확인(아키타입 minimal/corporate/…·주색·폰트 톤) → `register_design_system`
         으로 등록(임의 추정 금지·확인된 값만) → `set_design_system_active` 로 선택 → `mc-logi-screen-kit` SYNC 로
         design-system.md 확보 → 진행.
       - **거절** → 중단(임의 DS 생성·임의 hex 금지). DS 가 확보된 뒤 재개.
   - (개별 토큰 1~2개 결손은 "부재" 가 아님 — `kit-input.md` 규칙3 대로 "해당 토큰 미정·임의색 금지" 로 전달하고 진행)

1. **DS 토큰**: `_shared/design-system.md` 전량(color base hex·scale / typography / spacing / radius /
   Do·Don't) → `{{DS_TOKENS}}`. 이 토큰만 쓰도록 강제 컨텍스트로 사용.
2. **화면 골격**: `screens/SCREEN-NNN/SCREEN-NNN.md` 의 sections[]·components[]·consumes_apis·layout·
   brownfield 보존 메모 → `{{SCREEN_STRUCTURE}}`.
3. **surface 레퍼런스**: `screens/SCREEN-NNN/wireframe-*.html`(또는 `wireframe.html`) → `{{WIREFRAME_REF}}`.
   surface 목록(main/detail/modal 등)과 배치를 추출.
4. **컴포넌트 카탈로그**: `_shared/ui-catalog.md` 인덱스 → `{{COMPONENT_CATALOG}}`. 카탈로그 외 컴포넌트
   추정 금지.
5. 셸(헤더·사이드·푸터)은 디자인 대상에서 제외(app_shell 소관) — 화면 본문만.

## Phase 2 — 로컬 디자인 작성 (Claude 직접)

> 외부 디자인 도구를 쓰지 않는다. **디자인 결정·HTML/CSS 작성은 Claude 가 직접** 한다. `design-prompt.md` 의
> 지침대로 surface 별 고충실도 화면을 작성한다.

1. **작업 위치**: `screens/SCREEN-NNN/design/` 생성 후 surface 별로 직접 작성:
   - `design-{surface}.html` (본문 HTML — 인라인 `<style>` 없이 클래스만) + `design.css` (공유 스타일)
   - 셸(헤더·사이드·푸터)은 제외 — 화면 본문만.
2. **작성 규칙** (`design-prompt.md` §디자인 지시 전량 적용):
   - **DS 토큰만** — 색·간격·타이포·radius·**font-family** 는 `_shared/design-system.md` 토큰을 `:root` CSS
     변수로 선언해 사용. 임의 hex/px/폰트 금지. (DS 에 font-family·@font-face 소스가 내려왔으면 그대로 선언·적용;
     소스 없으면 family 만 선언 + 폴백 + design-notes 에 "웹폰트 소스 미정" 기록)
   - **골격 보존** — 와이어프레임 sections/components/정보 순서 유지, 영역 가감 금지.
   - **AI slop 회피(규격 내)** — 토큰을 기계적으로 칠하지 말고 위계·여백 리듬·상태·디테일을 **의도적으로** 다듬는다.
     단 토큰 밖 폰트·색·장식·그리드 파괴는 금지(원칙2). canonical HTML(태그 명시 닫기·속성 큰따옴표).
   - **무 JS·CSS-only** — 렌더가 `<script>` 를 제거할 수 있으므로 상태 토글은 `:target`/`:checked`, 동적
     데이터(테이블 행)는 미리 렌더. filler/데이터 slop 지양하되 테이블 등은 대표 데이터 유지.
3. **[게이트1] 프리뷰 & 반복** — 두 경로:
   - (a) **로컬**: `design-{surface}.html`(+`design.css`)을 브라우저로 직접 연다(file://).
   - (b) **logicraft 렌더 URL**: Phase 5 역등록 시 `/uploads/designs/…/SD-NNN/{render_id}.html` 렌더 URL 이 나온다
     (공유 가능한 호스팅 프리뷰 — 빠른 확인용으로 Phase 5 를 먼저 당겨 써도 됨).
   사용자 피드백이 있으면 `design-prompt.md` §반복 지시대로 **델타만** 재작성. 골격 이탈 시 골격 재강조 후 재작성.

## Phase 3 — 검증 & 노트

1. **raw hex 검출(D4)**: 작성한 html/css 의 hex 를 **빈도 집계**로 점검한다. 한 줄에 규칙이 여러 개면
   (`background: #aaa; } .x { color: var(--y); }`) 라인 단위 grep 이 `var(--…)` 때문에 놓치므로, 토큰 단위로 추출한다:
   ```bash
   grep -oE "#[0-9a-fA-F]{3,6}" design-*.html design.css | sort | uniq -c | sort -rn
   ```
   추출 hex 를 `_shared/design-system.md` 토큰 값과 대조한다. `:root` 변수 정의(토큰 선언)는 허용,
   그 외 **사용처**에 토큰에 없는 hex(상태 뱃지 tint·`#fff` 등)가 있으면 → ① 가능하면 게이트1 로 돌아가
   토큰/컴포넌트로 교체 재작성, ② 남기면 그 hex 목록을 `design-notes.md` § 컴포넌트·토큰 매핑에
   `⚠️ 토큰 미정 — 레포 base 컴포넌트(예: Badge)로 매핑 또는 토큰 추가 필요` 로 기록한다(raw hex 를 구현에
   그대로 넘기지 않기 위함).
2. **WCAG 대비 검증(D5) — 동봉 스크립트(외부 의존 없음)**: 디자인에서 실제로 쓴 **텍스트/배경 색 조합**(본문
   글자색 × 배경, 상태 뱃지 글자 × tint, 보조 텍스트(muted) × 배경 등)을 `_shared/design-system.md` 의 토큰 hex 로
   환산해 명암대비를 검사한다. **공공 시스템이므로 본문은 WCAG AA(4.5:1), 큰글씨(≥18pt/14pt bold)는 3:1 이 하한.**
   - 도구: **이 스킬 폴더에 동봉된** `scripts/contrast_checker.py`(표준 라이브러리만 — 외부 스킬 설치 불필요, 출력
     ASCII 라 Windows cp949 에서도 인코딩 가드 불필요). 경로는 **이 스킬의 base directory** 기준으로 결합한다:
     ```bash
     SKILL_DIR="<이 스킬의 base directory>"   # 예: ~/.claude/skills/mc-logi-screen-design (배포 환경마다 다름)
     # 쌍 검사 (fg bg)
     python "$SKILL_DIR/scripts/contrast_checker.py" "<text-hex>" "<bg-hex>"
     # 토큰 팔레트 전체 조합 검사 (DS 토큰을 {"name":"#hex",...} JSON 으로 저장 후)
     python "$SKILL_DIR/scripts/contrast_checker.py" --palette tokens.json
     ```
     (토큰을 새로 *만들지* 않는다 — DS 의 *기존* 값만 넣는다.)
   - **파이썬이 없는 환경**이면 D5 를 하드 게이트로 강제하지 말고, 검증을 스킵하되 `design-notes.md` 에
     `⚠️ WCAG 대비 미검증(python 부재) — 수동 확인 필요` 로 명기 + 사용자 보고(조용히 넘기지 않는다).
   - **AA 실패 조합**이 나오면 → ① 게이트1 로 돌아가 그 텍스트에 **더 진한 DS 토큰 색**(예: gray-500→gray-700)으로
     교체 재작성. ② DS 토큰 조합만으로 AA 가 불가하면(토큰 자체 한계) `design-notes.md` 에
     `⚠️ WCAG AA 미달(<ratio>:1) — DS 토큰 보강 필요(접근성)` 로 기록 + 사용자 보고. **임의 색을 새로 추가하지 않는다**
     (그건 DS 진실원 침범 — 보강은 logicraft DS 갱신 소관).
3. **design-notes.md 작성**: `notes-template.md` 형식대로 — ① 와이어프레임 대비 추가된 디자인 결정
   ② 영역별 컴포넌트(ui-catalog UI-NNN)·DS 토큰 매핑(폰트 포함) ③ WCAG 대비 검증 결과(D5 — 조합·대비·판정·조치)
   ④ surface 파일 인덱스 ⑤ SD 디자인 렌더 URL(Phase 5 역등록 후 기입) ⑥ 역등록 기록란(Phase 5 에서 채움 — SD-NNN·render_id·surface·action).

## Phase 4 — 키트 반영 (로컬)

1. `SCREENS.md` 에 design 산출물 인덱스를 추가/갱신한다(화면별 `design/` 유무·surface 수·생성 시각).
   기존 SCREENS.md 의 다른 단락은 건드리지 않는다.

## Phase 5 — logicraft 역등록 (screen_design SD-NNN, css 분리)

> ★ 컨셉: 디자인은 **screen_design(SD-NNN) 전용 ITEM** 에 올린다(static_render 아님). `upload_design_render` 가
> `css` 를 받아 `{render_id}.css` 로 서빙하고 공통 wireframe.css 를 주입하지 않는다(고충실 시안). SD 는 screen_spec
> 과 별 ITEM 이라, **render_id·surface 를 와이어프레임과 똑같이 맞추면**(예 main/detail-relay, page) screen_spec 의
> static_renders 와 **비교 뷰에서 짝**지어지면서도 와이어프레임을 덮어쓰지 않는다. (이전 "디자인=static_render" 방침 대체.)
> ⚠️ 렌더가 `<script>` 를 제거할 수 있으므로(보수적으로) 시안은 **무 JS·CSS-only**(`:target`/`:checked`)로, 동적
> 데이터(테이블 행 등)는 미리 렌더해 둔다.

1. **도구 선로드**: `ToolSearch("select:mcp__logicraft__upload_design_render,mcp__logicraft__list_items,mcp__logicraft__create_item,mcp__logicraft__get_item_schema")`.
2. **project_id 확정(★ 오등록 방지)**: 키트의 `version-master.md` / `screens/SCREEN-NNN/SCREEN-NNN.md` frontmatter 의
   `project_id` 를 **진실원**으로 쓴다. project_id 추정 금지.
3. **SD ITEM 확보**: `list_items(type=screen_design, project_id)` 로 SCREEN-NNN 을 `designs` 하는 SD 가 있는지 확인.
   - **있으면** 그 SD-NNN 사용.
   - **없으면 생성**(사용자 1줄 확인 후): `get_item_schema('screen_design')` → `create_item(type=screen_design,
     title, domain_id, status="draft", data={…})`. ★ `data` 안에 **`title` 도 필수**(top-level title 과 별개 —
     빠지면 E_VALIDATION). data: `{title, designs_screen:"SCREEN-NNN", description, device, designer,
     design_source:{tool:"other", version}, brownfield:{status, legacy_source:{type:"screen", legacy_artifact_id},
     decided_by}}` — brownfield 는 SCREEN 1차 메타(LEGACY-NNN/ADR-NNN)에서.
4. **역등록(사용자 1줄 확인 후 — logicraft 쓰기 정책)**: surface 별로
   ```
   upload_design_render(
     project_id=<키트 frontmatter 값>, item_id="SD-NNN",
     render_id="<와이어프레임과 동일: main|detail-relay|...>", surface="page|modal|drawer|...",
     label="<화면명> — 고충실 디자인", uploaded_by="claude-screen-design",
     html=<design-{surface}.html 본문(인라인 <style>·design.css link 제거)>,
     css=<design.css 본문>          # ★ css 분리 → {render_id}.css 서빙, wireframe.css 미주입
   )
   ```
   - **render_id·surface 를 screen_spec 와이어프레임과 동일하게** 맞춰 비교 뷰 짝지음. SD 는 별 ITEM 이라
     와이어프레임을 **덮어쓰지 않는다.** 같은 render_id 재업로드는 교체.
5. **검증**: 응답 `render.css_url` 세팅·`action`(add/replace) 확인. `E_AUTH_FORBIDDEN`(권한)·item(SD) 미존재
   (오프로젝트)면 우회 불가 — 사용자에게 알리고 중단(토큰 RBAC·project_id 사안).
6. **결과 보고**: SD-NNN + 업로드 render(id·surface·url) + 게이트1 반복 횟수 + raw hex 클린 여부 +
   다음 단계 안내(mc-logi-screen-implement 가 design/ 를 우선 소비).

## Phase 6 — ui_component 카탈로그 보강 권고 (선택)

> 디자인을 그리다 보면 카탈로그에 없던 컴포넌트가 자연히 생긴다(0건 카탈로그면 전부 새것). 이 스킬은
> 그것을 **임의 등록하지 않고**, 완료 후 "새 컴포넌트가 이러이런 게 추가됐으니 logicraft `ui_component` 를
> 보강하길 추천한다"고 **안내**한다. 사용자가 동의해야만 등록한다. (logicraft 쓰기 = 사용자 확정 후 원칙)

1. **새 컴포넌트 식별**: 작성한 `design-*.html`/`design.css` 에서 반복 사용한 UI 단위(버튼·뱃지·카드·입력·
   페이지네이션·알림 등)를 추린 뒤, `_shared/ui-catalog.md` 의 기존 UI-NNN 인덱스와 **대조**한다.
   - 카탈로그에 이미 있으면 → 그 UI-NNN 에 매핑(신규 아님).
   - 카탈로그에 없으면 → **신규 후보**. design-notes.md 의 ⚠️ 미정 매핑이 곧 이 후보 목록이다.
   - 신규 후보가 0건이면 Phase 6 는 "보강 불필요"로 1줄 보고하고 종료.

2. **보강 권고 안내(필수 — 등록 전)**: 신규 후보를 표로 제시한다(name / category / variants / 쓰인 화면).
   "위 N건이 카탈로그에 없습니다. logicraft `ui_component` 로 등록해 두면 다음 화면·구현에서 재사용·정합이
   쉬워집니다. 등록할까요?" 로 **명시 동의를 받는다.** 동의 없으면 등록하지 않고 design-notes 에
   `⚠️ 미등록 신규 컴포넌트 N건 — 추후 ui_component 보강 권장` 으로 남긴다.

3. **동의 시 등록**: `ToolSearch("select:mcp__logicraft__register_ui_components,mcp__logicraft__find_ui_component")`
   로 도구 로드 → 중복 확인 후 배치 등록:
   ```
   register_ui_components(
     project_id=<키트 frontmatter 진실원>,
     design_system_id="DS-NNN",          # 키트 design-system.md 의 DS id (단일 DS 면 생략 가능)
     components=[ { name, category(input|action|display|feedback|layout|navigation|data|overlay),
                    variants:[{name,description}], props_schema:[{name,type,required,default,description}],
                    accessibility_notes, usage_example("쓰인 화면 SCREEN-NNN"), code_snippet } , ... ]
   )
   ```
   - **추정 금지**: props/variants 는 **디자인에서 실제로 쓴 것만** 적는다(상상한 prop 금지). 모르면 비우고
     "디자인 기준 초안 — 구현 시 확정" 으로 둔다.
   - `register_ui_components` 는 같은 name 이면 skip(idempotent) — 재실행 안전.
   - **신규 등록만** 한다. 기존 UI-NNN 의 props/variant 수정이 필요하면 이 스킬이 하지 말고 `mc-logi-update`
     로 넘긴다(이 스킬은 register_ui_components 외 ITEM 갱신 도구를 쓰지 않는다).

4. **★ 등록 후 screen-kit SYNC 필수 (선택 아님)**: 컴포넌트를 등록했으면 **반드시** `mc-logi-screen-kit` SYNC 를
   실행한다. 등록 직후 로컬 `ui-catalog.md` 는 0건/구버전이라 stale — SYNC 로 카탈로그를 N건으로 갱신하고
   SCREENS.md 카탈로그 플래그도 `populated N건` 으로 바꿔야 이후 화면 구현/디자인이 실제 UI-NNN 을 본다.
   **SYNC 를 건너뛰면 다음 세션이 등록 사실을 모르고 다시 `⚠️ 미정`으로 작업하게 되므로 금지.** 이어서
   design-notes.md 의 ⚠️ 미정 매핑을 실제 UI-NNN 으로 갱신한다. (이 스킬은 ui-catalog.md 를 직접 쓰지 않는다 —
   키트 산출물 갱신은 screen-kit SYNC 가 수행.)

5. **보고**: 등록한 UI-NNN 목록(또는 "사용자 거절 — design-notes 에 미등록 기록") + SYNC 권고 1줄.

---

## 게이트 / 에러 처리

| 상황 | 대응 |
|---|---|
| 키트 없음 | `Skill(mc-logi-screen-kit)` 선행 실행 후 계속 |
| 키트 stale / CHANGED | screen-kit SYNC 권고 → 변경분 확인 후 진행 |
| DS/토큰 부재·미선택 (design-system.md 없음·빈 토큰·active DS 없음) | **착수 전 처리**(Phase 1-0). ① 다운로드 누락 → `mc-logi-screen-kit` (재)SYNC. ② DS 있으나 미선택/모호 → 사용자 확인 후 `set_design_system_active` → SYNC. ③ DS 0건 → 사용자에게 **새 DS 생성·등록 여부 확인** → 동의 시 `register_design_system`+`set_design_system_active`+SYNC 후 진행, 거절 시 중단(임의 hex 금지) |
| DS 에 font-family 없음 | 폰트 토큰이 안 내려온 것 → 임의 폰트 추정 금지. 키트 SYNC 로 DS 갱신 시도 → 그래도 없으면 시스템 폴백 + design-notes 에 "폰트 토큰 미정" 기록 |
| 디자인이 와이어프레임 골격 이탈 | 게이트1 에서 골격 재강조해 재작성 |
| raw hex 검출됨 (토큰 밖 색/폰트/장식) | 게이트1 로 돌아가 "토큰만" 재강조 후 재작성 (AI slop 회피는 규격 내에서만) |
| WCAG 대비 실패 (본문 < 4.5:1 / 큰글씨 < 3:1, 동봉 `scripts/contrast_checker.py` D5) | 게이트1 로 돌아가 해당 텍스트를 더 진한 DS 토큰 색으로 교체 재작성. 토큰 조합만으로 AA 불가하면 design-notes 에 `⚠️ WCAG AA 미달 — DS 토큰 보강 필요` 기록 + 사용자 보고 (임의 색 추가 금지 — DS 보강은 logicraft 소관) |
| 파이썬 부재로 D5 검사 불가 | 하드 게이트 강제 안 함 — 검증 스킵하되 design-notes 에 `⚠️ WCAG 대비 미검증(python 부재)` 명기 + 사용자 보고 |
| 역등록 권한 거부 / 오프로젝트 | `E_AUTH_FORBIDDEN` 또는 SD/SCREEN 미존재 → 토큰 RBAC·project_id(키트 frontmatter 진실원) 확인. 우회 불가 — 사용자에게 알리고 중단 |
| SD 생성 시 E_VALIDATION(title) | `create_item(screen_design)` 은 top-level `title` 외 **`data.title` 도 필수** — data 에 title 누락 시 발생. data 에 title 추가 후 재시도 |
| 렌더가 `<script>` 제거 | 렌더가 스크립트 strip 할 수 있음 → 시안을 무 JS·CSS-only(`:target`/`:checked`)로 작성(게이트1) |
| 디자인에 카탈로그 밖 새 컴포넌트 생김 | 임의 등록 금지 — Phase 6 에서 신규 후보를 표로 안내·동의 후 `register_ui_components`(신규만). 거절 시 design-notes 에 미등록 기록. 기존 UI-NNN 수정은 `mc-logi-update` |
| ui_component 카탈로그 0건 | 하드 게이트 아님(디자인 진행) — 매핑 `⚠️ 미정` 으로 두고 Phase 6 에서 일괄 보강 권고 |

---

## 참조 파일

- `kit-input.md` — **키트 파일 → 디자인 작성 입력 슬롯 매핑**. Phase 0/1 진입 시 읽는다. 키트 포맷이
  바뀌면 이 파일만 갱신.
- `design-prompt.md` — **Phase 2 로컬 디자인 작성 지침** (DS 토큰·폰트 + 디자인 지시 체크리스트 + AI slop
  회피 + 반복 지시). 슬롯 이름은 kit-input.md 와 1:1 일치.
- `notes-template.md` — **design-notes.md 작성 템플릿** (디자인 결정 + 컴포넌트/토큰 매핑 + WCAG 검증 + 역등록 참고).
- `scripts/contrast_checker.py` — **동봉 WCAG 대비 검사기**(Phase 3 D5). 표준 라이브러리만 쓰는 자립 스크립트 —
  외부 스킬 의존 없음. WCAG 2.1 공식(W3C 공개 표준)의 구현. 토큰을 *생성*하지 않고 *기존* 조합만 검사한다.

---

## 진입 멘트

"mc-logi-screen-design 시작합니다.

대상: `<DOMAIN-ID | SCREEN-NNN,...> <도메인명/화면명>` / 프로젝트: `<project>`
키트: `<docs/screen-design/{slug}-{ID}/>` (last sync `<시각>`, 모드 `<신선/SYNC 필요/없음→screen-kit 선행>`)
재개 지점: `<Phase 0~6>`

키트 게이트부터 진행합니다. 외부 디자인 도구 없이 Claude 가 직접 작성하고, DS 토큰만 사용(규격 내 AI slop 회피).
산출물은 로컬 design/ + logicraft screen_design(SD) 역등록(와이어프레임 비교 뷰 짝지음, 렌더 URL=프리뷰)까지이며, 마지막에 카탈로그에 없던
새 컴포넌트가 있으면 logicraft ui_component 보강을 권고합니다(동의 시 register_ui_components — 신규만, 기존 수정은 mc-logi-update).
DS·토큰이 없거나 선택돼 있지 않으면 착수 전에 처리합니다 — SYNC/DS 선택, 그래도 DS 가 0건이면 새 DS 생성·등록
여부를 묻고 진행합니다(Phase 1-0 게이트). 컴포넌트를 새로 등록하면 screen-kit SYNC 가 필수입니다(Phase 6)."
