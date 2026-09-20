#!/usr/bin/env python3
"""묶음 파일 머리에 「먼저 여기만」 목록을 만든다 — 과잉 열람을 막기 위한 파생물.

## 왜 있나 (LogiCraft CO-167 실측 · 2026-09-20)

묶음을 쪼개 본체를 3,333 → 708줄로 줄였는데, 에이전트가 **11개 중 6~8개를 열고**
대부분 전문을 읽어 **노하우 주입이 833 → 2,218줄(2.7배)로 늘었다.** 분할의 목적이 무너졌다.

원인 셋 — ⑴ 「실제로 열어 읽어라」를 명령형으로 밀어 과잉 열람을 유도했다
⑵ 색인이 «행동» 단위인데 한 라운드가 변이·테스트·DB·규범·렌더를 다 해서 6~8행이 전부 해당한다
⑶ 파일 안에 무엇이 있는지 **열어보지 않고는 알 수 없었다.**

⑶을 이 머리말이 닫는다. 에이전트는 **머리말만 먼저** 읽고, 해당 항목이 있을 때만 그 줄로 간다.

## 쓰는 법

    python3 {{knowhow_dir}}_gen-headnote.py           # 전부 갱신
    python3 {{knowhow_dir}}_gen-headnote.py --check    # 낡았는지만 확인(rc=1 이면 낡음)

☠️ **멱등이 아니다 — `rc=0` 이 나올 때까지(보통 2회) 돌려라.**
머리말을 삽입하면 그 아래 본문의 줄 번호가 전부 밀리고, 다음 계산은 «밀린 뒤»의 번호를 쓴다.
그래서 **한 번만 돌리면 `--check` 가 계속 rc=1(낡음)** 을 낸다 — 고장이 아니라 고정점 미도달이다.
표준 절차는 **`gen → gen → --check`**(실측 2026-09-20: 2회차에서 rc=0 도달).

☠️ **항목을 더했으면 다시 돌려라.** 머리말은 파생물이라 본문이 바뀌면 조용히 낡는다
(줄 번호가 밀리면 「여기로 가라」가 엉뚱한 곳을 가리킨다).
"""
## ☠️ 이 스크립트가 «의존»하는 것 — 없으면 빈 목록이 나온다
##
##  1) 묶음 항목이 `- **★★ …` / `- **☠️☠️ …` 처럼 **최상위 불릿 + 등급 표기**로 시작해야 한다.
##     등급이 없는 묶음은 뽑을 것이 없어 머리말이 비고, 그러면 에이전트는 결국 전문을 연다.
##  2) 파일명이 `{{prefix}}-*.md` 여야 한다(이 디렉터리 안).
##  3) **파생물이다.** 본문에 항목을 더했으면 다시 돌려라 — 줄 번호가 밀리면
##     「여기로 가라」가 엉뚱한 곳을 가리킨다(끊긴 참조와 같은 유형의 사고).
##  4) ☠️ **멱등이 아니다.** 삽입이 줄 번호를 밀므로 1회 실행 후 `--check` 는 rc=1 이 정상이다.
##     **rc=0 이 나올 때까지(보통 2회)** 돌려라 — `gen → gen → --check`.

import re, sys, pathlib

HERE = pathlib.Path(__file__).parent
BEGIN = "<!-- HEADNOTE:BEGIN (자동 생성 — _gen-headnote.py) -->"
END = "<!-- HEADNOTE:END -->"

# 한 줄 요약에서 걷어낼 장식
STRIP = re.compile(r"^[★☠️⚠️✅❌🔴\s]+|[★☠️⚠️\s]+$")


def summarize(text: str, width: int = 88, prefer_full: bool = False) -> str:
    """항목 첫 줄 → 한 줄 요약. 굵은 글씨가 있으면 그것을, 없으면 앞부분을."""
    bold = re.findall(r"\*\*(.+?)\*\*", text)
    s = text if prefer_full else (bold[0] if bold else text)
    s = re.sub(r"\*\*", "", s)
    s = STRIP.sub("", s).strip(" —·")
    s = re.sub(r"\s+", " ", s)
    return s[:width] + ("…" if len(s) > width else "")


# ★ 항목 표기는 두 가지다 — 둘 다 읽는다(2026-09-20 확장).
#   ⓪ 등급 불릿   `- **★★ …` / `- **☠️☠️ …`
#   ① 항목 헤딩   `### …` / `#### 🚨 …`  ← KLID 묶음 34/40 이 이 형식이었다.
#      불릿만 보면 그 34개가 통째로 «빈 머리말»이 되고, 그러면 에이전트는 결국 전문을 열다.
TOP_MARK = re.compile(r"★★|☠️☠️|🚨")
MID_MARK = re.compile(r"★|☠️|⚠️|🔗|🕳️|🎭|💬|🔴")


def _items(lines):
    """(줄번호, 요약, 등급) — 등급 2=최상위 1=그밖."""
    for i, ln in enumerate(lines, 1):
        if ln.startswith("- **"):
            if TOP_MARK.search(ln[:14]):
                yield i, summarize(ln), 2
            else:
                # 등급이 없어도 «굵은 글씨 최상위 불릿»은 항목이다 — 등급 표기는 권고지 전제가 아니다.
                # (2026-09-20: 등급 없는 묶음이 통째로 빈 머리말이 되던 것을 막는다)
                yield i, summarize(ln), 1
        elif re.match(r"^#{3,4}\s+\S", ln):
            title = re.sub(r"^#{3,4}\s+", "", ln)
            yield i, summarize(title, prefer_full=True), (2 if TOP_MARK.search(title[:8]) else 1)


def build(path: pathlib.Path) -> str:
    lines = path.read_text(encoding="utf-8").splitlines()
    found = [x for x in _items(lines)]
    total = len(found)
    top = [(i, s) for i, s, r in found if r == 2]
    other = sum(1 for _, _, r in found if r == 1)

    # 최상위가 너무 적은 파일은 그밖에서 보충한다 — 목록이 3줄이면 안내가 안 된다
    if len(top) < 4:
        for i, s, r in found:
            if len(top) >= 6:
                break
            if r == 1:
                top.append((i, s))
                other -= 1
        top.sort()

    out = [
        BEGIN,
        "## 먼저 여기만 읽어라 — 본문은 «해당할 때만»",
        "",
        f"> ☠️ 이 파일은 **{len(lines)}줄**이다. 전문을 열기 전에 아래 목록에서 **지금 하려는 일에 걸리는 항목이 있는지** 보라.",
        "> 있으면 그 줄로 가고, 없으면 **닫아라.** (실측: 묶음 과잉 열람으로 노하우 주입량이 2.7배가 된 적이 있다.)",
        "",
        f"**가장 자주 밟는 것 {len(top)}건**",
        "",
    ]
    out += [f"- L{i} — {s}" for i, s in top]
    out += [
        "",
        f"그 밖 ★/☠️ **{max(other,0)}건** · 전체 **{total}건**. "
        "제목만으로 안 걸리면 본문을 훑지 말고 닫아라 — 걸릴 때 다시 온다.",
        END,
    ]
    return "\n".join(out)


def apply(path: pathlib.Path, check: bool) -> bool:
    src = path.read_text(encoding="utf-8")
    note = build(path)
    if BEGIN in src:
        # ☠️ repl 을 «문자열»로 주면 본문의 `\x`·`\1` 이 치환 이스케이프로 해석돼 터진다.
        #    첫 실행(삽입)은 이 분기를 안 타므로 **재실행 때만** 드러나는 버그였다. lambda 로 막는다.
        new = re.sub(re.escape(BEGIN) + r".*?" + re.escape(END), lambda _m: note, src, flags=re.S)
    else:
        # 머리 인용 블록(>) 다음에 끼운다 — 제목·규약 아래
        lines = src.splitlines()
        k = 0
        for i, ln in enumerate(lines):
            if ln.startswith("#") or ln.startswith(">") or not ln.strip():
                k = i + 1
            else:
                break
        new = "\n".join(lines[:k] + [note, ""] + lines[k:]) + "\n"
    if new == src:
        return False
    if not check:
        path.write_text(new, encoding="utf-8")
    return True


def main() -> int:
    check = "--check" in sys.argv
    stale = []
    for p in sorted(HERE.glob("{{prefix}}-*.md")):
        if apply(p, check):
            stale.append(p.name)
            print(("낡음: " if check else "갱신: ") + p.name)
    if not stale:
        print("전부 최신")
    return 1 if (check and stale) else 0


if __name__ == "__main__":
    raise SystemExit(main())
