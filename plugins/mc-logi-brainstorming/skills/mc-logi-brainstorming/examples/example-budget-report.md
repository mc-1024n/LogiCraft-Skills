---
sketch_id: SKETCH-099
sketch_md: ./docs/scene-sketch/SK-012_video_upload.md
date: 2026-05-30
author: claude
status: budgeted
---

# 운영자 영상 수동 업로드 — 산출물 책정 리포트 (예시)

## 시나리오 출처
- scene-sketch: SKETCH-099 (운영자 영상 수동 업로드)
- 진실원 .md: ./docs/scene-sketch/SK-012_video_upload.md

## 산출물 책정표
| 산출물 타입 | 후보 ID·제목 | 상태 | 근거 step | 예상 cascade |
|---|---|---|---|---|
| API endpoint | (신규) POST /api/videos/manual-upload | 신규 | step2 command | ~4 |
| SCREEN | SCREEN-024 업로드 모달 | 갱신 | step1 read_model | ~2 |
| ERD | ERD-010 datasets | 재사용 | step3 data_store | - |
| domain_event | (신규) VideoUploaded | 신규 | step4 event | ~1 |
| ADR | (신규) 업로드 기본 분류 정책 | 신규 | D-1 hotspot | ~3 |
| NFR | (신규) 업로드 200MB 제한 | 신규 | 제약 언급 | ~1 |

## 책정 요약
- 신규 4건 / 재사용 1건 / 갱신 1건

## 결정대기 hotspot
- D-1: 업로드 시 기본 이벤트 타입을 운영자가 선택하게 할지, 시스템 기본값으로 둘지

## 다음 액션
- 신규 4건 + 갱신(SCREEN-024) → `mc-logi-update` 로 실제 생성/정합
- D-1 결정 수집 후 ADR 확정
