# claude-md-block.md — 프로젝트 CLAUDE.md 화면 키트 블록 규약

키트 생성/SYNC 후, 키트의 존재와 워크플로를 **모든 후속 세션**이 알 수 있도록 레포 루트
`CLAUDE.md` 에 자동 관리 블록을 쓴다. CLAUDE.md 는 매 세션 자동 로드되는 유일한 진입점이다 —
키트가 `docs/screen-design/` 에만 있으면 새 세션은 그 존재를 모른다.

## 원칙

1. **포인터 + 최소 요약만** — 도메인 지식을 블록에 복붙하지 않는다. 키트와 이중 관리(drift)가
   되기 때문이다. 주의사항은 "N건 존재 + 어느 파일 §어디를 보라" 수준으로 제한하고 상세는
   SCREENS.md 가 책임진다.
2. **마커 구간만 교체** — `<!-- mc-logi-screen-kit:start -->` ~ `<!-- mc-logi-screen-kit:end -->`
   사이만 재생성한다. 사용자가 CLAUDE.md 에 직접 쓴 다른 내용은 절대 건드리지 않는다.
   CLAUDE.md 가 없으면 새로 만들고 블록만 넣는다.
3. **기존 도메인 키트 블록과 공존** — 마커가 다르므로(`<!-- mc-logi-kit:start/end -->` vs
   `<!-- mc-logi-screen-kit:start/end -->`) 두 블록은 충돌 없이 공존한다. 한 레포에 도메인 키트
   (mc-logi-implement-kit)와 화면 키트(mc-logi-screen-kit)가 함께 있어도 각자의 마커 구간만
   관리하며 서로의 블록을 건드리지 않는다.
4. **멀티 도메인** — 한 레포에 여러 도메인 화면 키트가 있으면 표에 행을 추가/갱신한다 (도메인 ID
   로 행 식별). 블록 재생성 시 기존 표의 다른 도메인 행을 보존한다 (기존 블록을 파싱해 병합).
5. **내용의 출처는 키트** — 표·현황·주의 건수 전부 키트 파일(SCREENS.md / version-master.md)에서
   추출한다. 스킬이 소유하는 것은 "작업 규칙" 5줄(도메인 무관 워크플로)뿐이다.

## 블록 템플릿

```markdown
<!-- mc-logi-screen-kit:start (자동 관리 — 직접 수정 금지, mc-logi-screen-kit 재실행 시 갱신) -->
# Logicraft 화면 키트

이 레포는 logicraft 화면 설계 기반으로 프론트엔드를 구현한다. **화면 작업 전 아래 키트의 SCREENS.md 를 먼저 읽을 것.**

| 도메인 | 화면 수 | 키트 경로 | ui_component 카탈로그 | last sync |
|---|---|---|---|---|
| {DOMAIN-ID} {도메인명} | {n}개 ({SCREEN-NNN, ...}) | docs/screen-design/{slug}-{DOMAIN-ID}/ | {populated N건 \| ⚠️ 비어있음(시드 필요)} | {YYYY-MM-DD} (s{n}) |

## 작업 규칙 (화면 키트 워크플로)
1. **키트가 설계 진실원** — 화면 규칙·제약·빌드순서는 키트에서 읽는다. 키트 파일은 read-only 산출물 — **직접 수정 금지**.
2. **화면/시나리오를 수정하려면**: `/mc-logi-update` 로 logicraft 설계를 먼저 수정 → `/mc-logi-screen-kit` SYNC 로 로컬 키트 재동기화 → 그 다음 코드 반영. (코드만 고치고 설계를 안 고치면 다음 SYNC 때 충돌)
3. **구현 착수는** `/mc-logi-screen-implement` — 키트 신선도 게이트부터 시작한다.
4. **구현 완료 시** logicraft 에 IMPREC 추적 기록 (mc-logi-screen-implement Phase 5 가 수행).
5. 작업 전 키트가 오래됐으면(`version-master.md` last sync 확인) SYNC 먼저.

## 도메인별 주의 (상세는 각 SCREENS.md §주의)
- **{DOMAIN-ID}**: {⚠️ 변경 N건 코드 재반영 필요 / 카탈로그 시드 필요 등 — 1~2줄 + 섹션 포인터}
<!-- mc-logi-screen-kit:end -->
```

## 필드 추출 출처

| 필드 | 출처 |
|---|---|
| 도메인 ID·명, 키트 경로 | version-master.md 헤더 |
| 화면 수·화면 ID 목록 | version-master.md "다운로드 화면" 항목 |
| ui_component 카탈로그 상태 | _shared/ui-catalog.md 첫 섹션 (건수 또는 "카탈로그 비어있음" 플래그) |
| last sync (날짜 + 세션) | version-master.md 헤더 Last sync |
| 주의 줄 | SCREENS.md 의 ⚠️ 섹션(변경 알림·카탈로그 비어있음·운영 전 확인) 스캔 — 건수 + 섹션 위치만 |

## 갱신 시점·규칙

- **INITIAL 생성 후**: 블록 신규 작성 (해당 도메인 행 추가).
- **SYNC 후**: last sync 갱신. CHANGED/RETIRED 가 있었으면 해당 도메인 행 주의 칸에
  `⚠️ 변경 N건 코드 재반영 필요` 를 덧붙인다 — 이 표식은 mc-logi-screen-implement Phase 5
  (구현 반영 완료) 가 지운다.
- **ui_component 카탈로그 비어있음**: 카탈로그 상태 칸에 `⚠️ 비어있음(시드 필요)` 기재.
  Phase 0.5 에서 시드 완료 시 `populated N건` 으로 갱신.
- **mc-logi-screen-implement Phase 5**: 주의 줄(운영 전 확인 잔여)을 갱신한다.
- 블록 갱신은 키트 산출물과 같은 커밋 흐름에 포함 (별도 커밋 불필요).

## 도메인 키트 블록과의 공존 예시

같은 도메인에 도메인 키트(mc-logi-implement-kit)와 화면 키트(mc-logi-screen-kit) 가
모두 존재하는 경우 CLAUDE.md 는 다음과 같이 두 블록이 독립적으로 공존한다:

```markdown
<!-- mc-logi-kit:start (자동 관리 — mc-logi-implement-kit 재실행 시 갱신) -->
# Logicraft 구현 키트
...
<!-- mc-logi-kit:end -->

<!-- mc-logi-screen-kit:start (자동 관리 — mc-logi-screen-kit 재실행 시 갱신) -->
# Logicraft 화면 키트
...
<!-- mc-logi-screen-kit:end -->
```

- 두 블록은 마커가 달라 서로 영향을 주지 않는다.
- mc-logi-implement-kit 실행 시 `mc-logi-kit` 마커만 갱신한다.
- mc-logi-screen-kit 실행 시 `mc-logi-screen-kit` 마커만 갱신한다.
- 두 블록이 같은 도메인을 가리킬 수 있으며, 이는 "백+프론트 도메인 키트"와 "화면 특화 키트"가
  공존하는 정상 상태다.
