# mc-logi-upload-kit — LogiCraft 파일 업로더

로컬에 작업해둔 파일(HTML 데모·아티팩트·디자인 렌더·markdown 첨부)을 LogiCraft 에 **REST 로 직접 업로드**하는 스킬. `mc-logi-implement-kit`(키트 다운로더)의 **역방향**이다.

## 왜 필요한가

`create_app_demo(html="...")` 처럼 본문을 문자열 인자로 넘기면, 로컬에 파일이 이미 있어도 AI 가 그 파일을 **Read → 인자로 재출력**하는 왕복이 생긴다. 5MB 데모 HTML 이면 토큰이 수백만 단위로 터져 사실상 등록 불가다.

이 스킬은 결정적 스크립트(`bin/upload-artifact.mjs`)가 **파일을 직접 읽어 REST 로 전송**하므로 **본문이 AI 컨텍스트를 거치지 않는다(토큰 0)**. 상용/로컬 어느 서버든 동일하게 동작한다.

## 대상 타입 (5종 어댑터)

| `--type` | 대상 | 필수 인자 |
|---|---|---|
| `app_demo` | 앱 데모 후보(+v1) | `--title` |
| `app_demo_version` | 앱 데모 버전 추가 | `--parent`(demoId) |
| `project_artifact` | 프로젝트 아티팩트 | `--title` |
| `attachment` | 아티팩트 md 첨부 | `--parent`(artifactId) `--title` |
| `design_render` | 디자인 렌더(html+css, multipart) | `--parent`(SD-ID) |

## 사용 예

```bash
LOGICRAFT_API_KEY=<lc_ 키> LOGICRAFT_API_BASE=<서버 base> \
  node upload-artifact.mjs --type app_demo --project <uuid> --file demo.html --title "글래스모피즘 버전"
```

- 인증: MCP 와 **동일한 lc_ 키**. 서버 guard 가 write 스코프를 강제(read-only 키는 403).
- 종료코드: 0 성공 / 1 인자 / 2 HTTP·인증 / 3 파일.

## 보안

업로드된 본문도 **서버가 기존 sanitize + 봉인(ADR-025) 파이프라인을 그대로 경유** — 스크립트는 전송만 한다. 익명 업로드 불가(guard fail-closed).

## 설계 근거

ADR-029(파일 업로드 채널) · DFEAT-060 · API-159~163 · CO-007. `mc-logi-implement-kit`(ADR-026 다운로더)의 대칭.
