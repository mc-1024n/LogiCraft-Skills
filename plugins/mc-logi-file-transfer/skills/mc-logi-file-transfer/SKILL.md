---
name: mc-logi-file-transfer
description: LogiCraft **프로젝트 자료실**의 파일을 올리고 내려받는 스킬. hwp·pdf·zip·xlsx 같은 바이너리를 최대 3GB 까지 다루며, 재개 가능한 청크 업로드와 sha256 무결성 대조를 한다. 서식·반입세트·증빙·계약서·신청서처럼 **여러 산출물이 함께 참조하는 자료**가 대상. 사용자가 "이 파일 자료실에 올려줘", "hwp 업로드", "반입세트 등록", "FILE-003 받아줘", "자료실에서 내려받아", "첨부파일 다운로드", "/mc-logi-file-transfer" 등을 요청할 때 실행. MCP 로는 자료실 파일을 만들 수 없다(3GB 가 tool call 에 안 들어가고, 실물 없이 메타만 지어낸 ITEM 이 남는다) — 이 스킬이 유일한 경로다.
metadata:
  version: 1.0.0
---

# mc-logi-file-transfer — LogiCraft 자료실 업로더/다운로더

로컬 파일을 LogiCraft **프로젝트 자료실**(CO-080)에 올리고, 거기 있는 파일을 내려받는다.
결정적 스크립트(`bin/file-transfer.mjs`)가 파일을 직접 스트리밍하므로 **본문이 AI 컨텍스트를
거치지 않는다** — 3GB 파일도 토큰 0 이다.

## When to Use
- 로컬 바이너리를 자료실에 등록 (예: "이 신청서 hwp 올려줘", "반입세트 zip 등록")
- 자료실 파일을 로컬로 가져오기 (예: "FILE-003 받아줘")
- 여러 ITEM 이 함께 참조할 **서식·증빙·패키지**를 프로젝트에 1벌 두려 할 때
- 끊긴 업로드를 이어서 올릴 때 (`--resume`)

## When NOT to Use
- **AI 가 만든 HTML/markdown 산출물 등록** → **`mc-logi-upload-kit`**
  (앱 데모·프로젝트 아티팩트·디자인 렌더·md 첨부. 저쪽은 텍스트 전용이고 한 방 POST 다)
- **스킬을 마켓플레이스에 발행** → `mc-logi-publish-skill`
- **설계 ITEM 다운로드**(도메인 키트) → `mc-logi-implement-kit`
- ITEM 설계 자체 수정 → `mc-logi-update`

> ★ `mc-logi-upload-kit` 과 헷갈리기 쉽다. 기준은 **"AI 가 만든 렌더 산출물인가,
> 사람이 주고받는 자료인가"** 다. HTML 이면 저쪽, hwp·pdf·zip 이면 여기다.

## ★★ 왜 MCP 도구가 아니라 스킬인가

MCP 로 자료실 파일을 만드는 건 **서버가 막아 놓았다**(`create_item(type='file')` → 거절).
이유가 둘이다:

1. **3GB 가 tool call 인자에 안 들어간다.**
2. **`byte_size`·`sha256`·`file_path` 는 서버가 받은 실물을 실측해야만 참값**이다.
   MCP 로 열어 두면 **실물 없이 메타만 지어낸 ITEM** 이 남는다 —
   "설계에는 있는데 파일이 없는" 상태가 되고, 이 기능의 발단이 정확히 그 유실 사고였다.

그래서 **REST 업로드가 유일한 생성 경로**이고, 이 스킬이 그 REST 를 실행한다.
`finalize` 가 `FILE-NNN` ITEM 을 **자동 생성**한다.

## 사전 준비 (환경)
- `LOGICRAFT_API_KEY` — MCP 와 **동일한 lc_ 키**. **write 권한 필수**(read 전용 키는 403).
- `LOGICRAFT_API_BASE` — 대상 서버(`/api` 포함). 상용 `https://logicraft.cudo.co.kr:10000/api`.
  ★ 미설정이면 `~/.claude.json` 의 `mcpServers` 에서 자동 조달(`--server` 로 지정 가능).
  **로컬 기본값은 없다** — 둘 다 없으면 종료코드 1 로 중단한다.

## 워크플로

### Phase 1 — 대상 확정
- **업로드**: 파일 경로 · `project_id` · **표시 이름** · **분류** 를 확정. 불명확하면 되묻는다.
  - 분류: `form`(서식) · `package`(반입세트 등 패키지) · `evidence`(증빙) ·
    `reference`(참고자료) · `other`
  - ⚠️ **표시 이름을 AI 가 지어내지 마라.** 파일명과 이름은 다른 값이다 — 사용자에게 물어라.
- **다운로드**: `project_id` · `FILE-NNN`. ID 를 모르면 `list_items(type='file')` 로 찾는다.

### Phase 2 — 실행
스크립트 위치는 설치 무관하게 `Glob("**/mc-logi-file-transfer/bin/file-transfer.mjs")` 로 탐색 후:

```bash
# 업로드
LOGICRAFT_API_KEY=<lc_ 키> LOGICRAFT_API_BASE=<서버 base> \
  node <file-transfer.mjs> upload --project <uuid> --file <경로> \
    --name "표시 이름" --category <form|package|evidence|reference|other> \
    [--description ...] [--source ...] [--retention ...] [--version-label ...] [--notes ...] \
    [--resume <sessionId>] [--chunk-bytes N] [--mime-type ...]

# 다운로드
LOGICRAFT_API_KEY=... LOGICRAFT_API_BASE=... \
  node <file-transfer.mjs> download --project <uuid> --id FILE-001 [--out <경로>] [--force]
```

### Phase 3 — 결과 보고
- 업로드: 생성된 `FILE-NNN` 과 `sha256`·`byte_size`·`storage_backend` 를 보고.
  **다른 산출물에서 참조하려면** 그 ITEM 의 `attached_files` 에 `FILE-NNN` 을 넣으라고 안내
  (`update_item` — `attaches` 링크가 자동 생성된다).
- 다운로드: 저장 경로와 **sha256 대조 결과**를 보고.
- 실패면 종료코드·stderr 를 **그대로** 노출한다.

## 종료코드

| 코드 | 뜻 | 대처 |
|---|---|---|
| 0 | 성공 | — |
| 1 | 인자 오류 | 필수 인자·분류 값 확인 |
| 2 | HTTP/인증 오류 | 키·write 스코프·base·네트워크 |
| 3 | 파일 오류 | 경로·권한, 다운로드 시 `--force` |
| 4 | **무결성 불일치** | 아래 참조 |

## ★ 재개 — 끊겼을 때

업로드가 중간에 끊기면 스크립트가 **세션 id 를 알려준다**:

```
✖ 청크 전송 실패(네트워크, offset=8388608): ...
  ↻ 이어서 올리려면: --resume 6ce36b0b-...
```

`--resume <sessionId>` 로 다시 실행하면 `HEAD` 로 서버가 이미 받은 지점을 확인해
**거기서부터** 보낸다. 세션은 **마지막 청크로부터 24시간**(설정값) 살아 있다 —
느리게라도 올리는 중이면 안 지워진다.

## ★ 무결성 — sha256 이 두 번 대조된다

1. **업로드**: 클라이언트가 보내기 전에 해시를 선언(`expected_sha256`)하고,
   서버가 `finalize` 에서 **받은 실물을 다시 해시해 대조**한다.
   어긋나면 **422 + 세션 통째 폐기**(부분 수용 없음) — 올리는 도중 파일이 바뀐 경우다.
   ⚠️ 이때는 `--resume` 이 소용없다. **처음부터** 올려야 한다.
2. **다운로드**: 받은 뒤 로컬에서 해시를 계산해 ITEM 의 `sha256` 과 대조한다.
   어긋나면 종료코드 4 로 알리고 **파일은 지우지 않는다**(원인 파악용).

## ⚠️ 서버가 실측한 값은 못 고친다

`original_name` · `mime_type` · `byte_size` · `sha256` · `storage_backend` · `file_path`
6개는 업로드 서버가 실물을 받아 확정한 **사실 기록**이다. `update_item` 으로 덮으려 하면
거절된다 — 덮으면 DB 가 디스크에 대해 거짓말을 하게 되기 때문이다.

사람이 적는 7개(`name`·`category`·`source`·`description`·`retention`·`version_label`·`notes`)는
`update_item` 으로 언제든 고칠 수 있다.

**파일 내용이 바뀌었으면 새로 업로드**한다 — `finalize` 가 새 FILE ITEM 을 만든다.

## 자세히
`get_logicraft_guide("file-library")` — 자료실의 전체 그림(참조 거는 법·삭제 의미론·
아티팩트 연결·찾는 법).

## 설계 근거
CO-080(자료실 본체 — `file` ITEM 타입 · 재개 가능 업로드 · 저장 백엔드 · 쓰기 가드) ·
CO-086(이 스킬). 키·base 자동 조달은 CO-049.
분리 근거는 CO-035 와 같다 — **대상·시맨틱·리스크가 다르면 한 스킬에 묶지 않는다**
(`mc-logi-upload-kit` 은 소형 텍스트 산출물 전용이고 한 방 POST 다).
