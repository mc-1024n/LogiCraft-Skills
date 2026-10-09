#!/usr/bin/env python3
"""
mc-logi-schema-fill 결정적 도우미 — 대량 입출력과 «세는 일»을 에이전트 손에서 뺀다.

왜 스크립트인가
  1) 크기 — 큰 프로젝트는 스캔 결과가 수천 행·수 MB 다. 그걸 에이전트 컨텍스트로 통과시키면
     분류할 자리가 남지 않는다. 스캔·스냅샷·적용·재스캔은 여기서 MCP 를 직접 부른다.
  2) 분모 — LogiCraft Self 이관 캠페인에서 분모를 여섯 번 틀렸다(발화 행 vs 참조 id, 폐기 포함/제외,
     페이지 수 vs 전체 수). 계획·검증의 모든 수는 여기서만 나온다.

에이전트가 하는 일은 둘뿐이다 — ①문맥을 읽고 부류를 정한다(fill) ②게이트에서 사람에게 묻는다.

하위 명령 (순서대로)
  preflight   서버가 이 스킬을 지원하는지(scan_prose_refs 존재)·프로젝트 접근 가능한지
  scan        전 페이지 스캔 → scan.json (+ 항등식 검산)
  snapshot    항목 전체를 받아 폴더에 저장 + 뜬 직후 파싱 검산
  draft       scan + 스냅샷 → decisions.json 초안(참조 1건 = 1행, 문맥 문장 포함)
  fill        에이전트가 정한 부류를 초안에 반영(어휘 검사)
  review-md   사람 검토용 표
  plan        decisions + 스냅샷 → plan.json (항목별 patch op)
  apply       plan 을 서버에 적용(시범 --only / 전량). 실패·NOOP 이면 즉시 중단
  verify      plan + 재스캔 + 적용 후 스냅샷 → 합격/불합격
  tally       부류별 집계

표준 라이브러리만 쓴다(설치 불필요).
"""
from __future__ import annotations

import argparse
import json
import os
import re
import sys
import time
import urllib.error
import urllib.request
from collections import Counter, OrderedDict
from pathlib import Path

# ── 분류 어휘 ──────────────────────────────────────────────────────────────
# 서버의 산문 경고 면제 절과 **같은 말**을 쓴다(references/classification.md).
MIGRATE = "이관"
HOLD = "보류"
EXCLUDE_KINDS = [
    "다른 항목의 사례",
    "선례·비유 인용",
    "경계 선언",
    "쓰지 않게 된 이력",
    "폐기 항목",
    "측정 표본",
    "목업 라벨",
    "형제 프로젝트 번호",
]
ALL_KINDS = [MIGRATE, *EXCLUDE_KINDS, HOLD]
RETIRED = {"deprecated", "superseded"}
PAGE = 200  # 서버 기본값과 같게. 큰 페이지는 전송이 수백 KB 가 된다.


def die(msg: str, code: int = 1) -> None:
    print(f"❌ {msg}", file=sys.stderr)
    sys.exit(code)


def load(p):
    try:
        return json.loads(Path(p).read_text(encoding="utf-8"))
    except Exception as e:  # noqa: BLE001
        die(f"JSON 을 읽을 수 없다: {p} — {e}")


def dump(p, obj) -> None:
    Path(p).parent.mkdir(parents=True, exist_ok=True)
    Path(p).write_text(json.dumps(obj, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")


def rkey(item_id, rule, field, ref) -> str:
    return f"{item_id}|{rule}|{field}|{ref}"


# ── 서버 설정 · MCP 호출 ───────────────────────────────────────────────────
def _pools():
    """MCP 서버 정의를 찾는 곳: ~/.claude.json(전역·프로젝트별) + cwd 에서 위로 올라가며 .mcp.json."""
    out = []
    home = Path(os.path.expanduser("~"))
    try:
        cfg = json.loads((home / ".claude.json").read_text(encoding="utf-8"))
        if cfg.get("mcpServers"):
            out.append(("~/.claude.json", cfg["mcpServers"]))
        for pth, proj in (cfg.get("projects") or {}).items():
            if isinstance(proj, dict) and proj.get("mcpServers"):
                out.append((f"~/.claude.json[{pth}]", proj["mcpServers"]))
    except Exception:  # noqa: BLE001
        pass
    d = Path.cwd()
    for p in [d, *d.parents]:
        f = p / ".mcp.json"
        if f.exists():
            try:
                out.append((str(f), json.loads(f.read_text(encoding="utf-8")).get("mcpServers") or {}))
            except Exception:  # noqa: BLE001
                pass
    return out


def server(name: str):
    """☠️ 서버는 반드시 이름으로 지정한다 — 기본값 없음.

    같은 설정 안에 상용(logicraft)과 개발(logicraft-dev)이 나란히 있다. 기본값을 두면
    「개발기에서 시험하려다 상용에 쓰는」 사고가 난다(2026-09 실제로 날 뻔했다).
    """
    base = os.environ.get("LOGICRAFT_MCP_URL")
    key = os.environ.get("LOGICRAFT_API_KEY")
    if base and key:
        return {"name": name, "url": base.rstrip("/"), "key": key.replace("Bearer ", "").strip(), "src": "env"}
    for src, pool in _pools():
        srv = pool.get(name)
        if not srv:
            continue
        env = srv.get("env") or {}
        argv = srv.get("args") or []
        k = env.get("LOGICRAFT_API_KEY") or env.get("AUTH_TOKEN") or env.get("API_KEY") or ""
        if not k:
            h = next((a for a in argv if isinstance(a, str) and re.match(r"^authorization\s*:", a, re.I)), None)
            if h:
                k = h.split(":", 1)[1]
        if not k:
            # HTTP 형식 등록(`claude mcp add --transport http … --header "Authorization: Bearer …"`)은
            # 키를 args 가 아니라 headers 에 둔다 — {"type":"http","url":…,"headers":{"Authorization":…}}.
            hdrs = srv.get("headers") or {}
            if isinstance(hdrs, dict):
                k = next((v for n, v in hdrs.items() if isinstance(n, str) and n.lower() == "authorization"), "") or ""
        k = re.sub(r"^\s*Bearer\s+", "", str(k), flags=re.I).strip()
        if re.fullmatch(r"\$\{.*\}", k):
            k = ""
        url = srv.get("url") or next((a for a in argv if isinstance(a, str) and re.match(r"^https?://", a)), "")
        if url and k:
            url = url.rstrip("/")
            if not url.endswith("/mcp"):
                url += "/mcp"
            return {"name": name, "url": url, "key": k, "src": src}
    die(f"MCP 서버 '{name}' 의 주소·키를 찾지 못했다 (~/.claude.json · .mcp.json 의 env·args·headers.Authorization · env LOGICRAFT_MCP_URL/LOGICRAFT_API_KEY)")


def mcp(srv, tool: str, args: dict, retries: int = 2):
    body = json.dumps(
        {"jsonrpc": "2.0", "id": 1, "method": "tools/call", "params": {"name": tool, "arguments": args}}
    ).encode()
    last = None
    for i in range(retries + 1):
        req = urllib.request.Request(
            srv["url"],
            data=body,
            headers={
                "Authorization": f"Bearer {srv['key']}",
                "Content-Type": "application/json",
                "Accept": "application/json, text/event-stream",
            },
        )
        try:
            with urllib.request.urlopen(req, timeout=120) as r:
                raw = r.read().decode("utf-8")
        except urllib.error.HTTPError as e:
            last = f"HTTP {e.code}: {e.read().decode('utf-8', 'replace')[:300]}"
        except Exception as e:  # noqa: BLE001
            last = str(e)
        else:
            if raw.lstrip().startswith("event:") or "\ndata:" in raw:  # SSE 로 올 때
                raw = "\n".join(l[5:].strip() for l in raw.splitlines() if l.startswith("data:"))
            j = json.loads(raw)
            res = j.get("result") or {}
            text = ((res.get("content") or [{}])[0]).get("text", "")
            if res.get("isError") or j.get("error"):
                raise RuntimeError(text or json.dumps(j.get("error"), ensure_ascii=False))
            return json.loads(text) if text else {}
        time.sleep(1.5 * (i + 1))
    raise RuntimeError(f"{tool} 호출 실패: {last}")


# ── preflight ─────────────────────────────────────────────────────────────
def cmd_preflight(a) -> None:
    srv = server(a.server)
    print(f"🔌 서버 {srv['name']} → {srv['url']}  (설정: {srv['src']}, 키는 출력하지 않음)")
    try:
        r = mcp(srv, "scan_prose_refs", {"project_id": a.project, "limit": 1})
    except RuntimeError as e:
        m = str(e)
        if "unknown tool" in m.lower() or "not found" in m.lower() and "tool" in m.lower():
            die("이 서버에는 scan_prose_refs 가 없다 — 서버 배포가 선행돼야 한다(CO-173 이후 버전).")
        die(f"스캔 시험 호출 실패: {m[:300]}")
    s = r["summary"]
    print(
        f"✅ 지원 확인 — 스캔 항목 {s['items_scanned']} · 발화 항목 {s['items_with_findings']} · "
        f"발화 행 {s['findings_count']} · 참조 {s['refs_count']}"
    )
    print("   규칙별: " + " · ".join(f"{k} {v}" for k, v in sorted(s["by_rule"].items(), key=lambda x: -x[1])))


# ── scan ──────────────────────────────────────────────────────────────────
def cmd_scan(a) -> None:
    srv = server(a.server)
    base = {"project_id": a.project, "limit": PAGE}
    if a.type:
        base["type"] = a.type
    if a.rule:
        base["rule"] = a.rule
    findings, summary, off = [], None, 0
    while True:
        r = mcp(srv, "scan_prose_refs", {**base, "offset": off})
        summary = summary or r["summary"]
        findings += r["findings"]
        if r.get("next_offset") is None:
            break
        off = r["next_offset"]
    # ☠️ 항등식 — 요약은 «전체», findings 는 «페이지를 이어 붙인 것». 같아야 누락이 없다.
    refs = sum(len(f["refs"]) for f in findings)
    probs = []
    if len(findings) != summary["findings_count"]:
        probs.append(f"발화 행 {len(findings)} ≠ 요약 {summary['findings_count']}")
    if refs != summary["refs_count"]:
        probs.append(f"참조 {refs} ≠ 요약 {summary['refs_count']}")
    keys = [(f["item_id"], f["rule"], f["field"]) for f in findings]
    if len(keys) != len(set(keys)):
        probs.append("같은 (항목,규칙,칸) 행이 중복 — 스캔 도중 데이터가 바뀌었을 수 있다. 다시 돌려라")
    if probs:
        die("스캔 항등식 실패:\n  " + "\n  ".join(probs))
    dump(a.out, {"server": a.server, "project_id": a.project, "filter": {"type": a.type, "rule": a.rule},
                 "summary": summary, "findings": findings})
    print(f"✅ 스캔 — 발화 행 {len(findings)} · 참조 {refs} · 발화 항목 {summary['items_with_findings']}"
          f" · 스캔 항목 {summary['items_scanned']} → {a.out}")


# ── snapshot ──────────────────────────────────────────────────────────────
def cmd_snapshot(a) -> None:
    """☠️ 스냅샷은 되돌리기의 유일한 안전망이다. «뜬 직후» 파싱까지 검산한다.

    LogiCraft Self 이관 1라운드에서 스냅샷이 백슬래시 재이스케이프로 깨진 채 작업했고,
    끝나고서야 알았다. 그 뒤로 뜨자마자 다시 읽어 본다.
    """
    srv = server(a.server)
    if a.from_scan:
        ids = sorted({f["item_id"] for f in load(a.from_scan)["findings"]})
    elif a.from_plan:
        ids = [i["item_id"] for i in load(a.from_plan)["items"]]
    else:
        ids = a.ids.split(",")
    d = Path(a.dir)
    d.mkdir(parents=True, exist_ok=True)
    for i, item_id in enumerate(ids, 1):
        r = mcp(srv, "get_item", {"project_id": a.project, "id": item_id})
        (d / f"{item_id}.json").write_text(json.dumps(r, ensure_ascii=False, indent=1), encoding="utf-8")
        if i % 25 == 0:
            print(f"   … {i}/{len(ids)}")
    bad = []
    for item_id in ids:
        try:
            obj = json.loads((d / f"{item_id}.json").read_text(encoding="utf-8"))
            it = obj.get("item", obj)
            if it.get("id") != item_id or not isinstance(it.get("current_version"), int) or not isinstance(it.get("data"), dict):
                bad.append(item_id)
        except Exception:  # noqa: BLE001
            bad.append(item_id)
    if bad:
        die(f"스냅샷 검산 실패 {len(bad)}건: {bad[:10]}")
    print(f"✅ 스냅샷 {len(ids)}건 저장·파싱·id·버전·data 확인 → {d}")


# ── 문맥 추출 ──────────────────────────────────────────────────────────────
def resolve(obj, path: str):
    """`data.tables[3].columns[2].description` · `data.responses.409.description` 를 따라간다."""
    cur = obj
    for seg in re.findall(r"[^.\[\]]+|\[\d+\]", path):
        if seg.startswith("["):
            idx = int(seg[1:-1])
            if not isinstance(cur, list) or idx >= len(cur):
                return None
            cur = cur[idx]
        elif isinstance(cur, dict):
            if seg not in cur:
                return None
            cur = cur[seg]
        elif isinstance(cur, list) and seg.isdigit():
            idx = int(seg)
            if idx >= len(cur):
                return None
            cur = cur[idx]
        else:
            return None
    return cur


def excerpt(text: str, ref: str, width: int = 110) -> str:
    """참조 주변 문장. 범위 표기(ADR-020~030)로만 걸린 경우엔 접두사 위치를 쓴다."""
    s = str(text)
    i = s.find(ref)
    if i < 0:
        m = re.search(re.escape(ref.split("-")[0]) + r"-\d", s)
        i = m.start() if m else 0
    lo, hi = max(0, i - width), min(len(s), i + len(ref) + width)
    frag = s[lo:hi].replace("\n", " ⏎ ")
    return ("…" if lo else "") + frag + ("…" if hi < len(s) else "")


# ── 경계·선례 가드 (2026-09-27 · KLID 3-모델 판정 실측) ────────────────────────
# 링크 정밀도 표본 100건을 codex·antigravity·GLM 이 교차 판정한 결과, 다수가 «틀림»이라 한 4건이 전부
# «ID 옆에 경계·선례 문구가 있는데 이관으로 판정한 것»이었다(「범위 밖이라 손대지 않음」·「## 잔여」 절·
# 「ADR-099 패턴」·「책임 제외」 절). 판정 기준(classification.md)엔 이미 있는 부류인데 판정자가 흘려보냈다.
# ⇒ 문구가 붙은 행은 «이관이면 사유 필수»로 만든다. 자동 보류가 아니다 — 진짜 관계까지 잃지 않게.
# 교정: 같은 100건에서 다수-틀림 4/4 검출 · 전원-맞음 85건 중 오탐 1 · 홀드아웃 1,357건 경고율 6.3%.
# ☠️ 이력 낱말(폐기·대체·이전)은 넣지 마라 — 폐기 «결정»을 서술한 ADR 에서 맞는 행 7건에 울렸다.
GUARD_SENT = re.compile("|".join([
    r"손대지\s*않", r"건드리지\s*않", r"범위\s*(?:밖|외)", r"(?:대상|책임)\s*(?:에서\s*)?제외", r"무관", r"관계\s*없",
    r"해당\s*없", r"대상이?\s*아니", r"다루지\s*않", r"포함하지\s*않", r"패턴\)?", r"와\s*같은\s*방식", r"선례", r"비유"]))
GUARD_HEAD = re.compile("|".join([
    r"잔여", r"미해결", r"해소되지\s*않", r"후속", r"남은\s*(?:것|일|과제)", r"미구현", r"범위\s*(?:밖|외)", r"비범위",
    r"제외", r"하지\s*않는\s*것", r"Out\s*of\s*scope", r"TODO", r"보류"]), re.I)
_HEADING = re.compile(r"(?:^|\n|⏎)\s*(?:#{1,6}\s*[^\n⏎]+|\*\*[^*\n]{2,40}\*\*\s*[:：]?\s*(?:\n|⏎|$)|[^\n⏎]{1,30}[:：]\s*(?:\n|⏎))")


def guard_signal(text, ref: str, width: int = 40):
    """ref 가 적힌 «같은 문장»의 경계·선례 문구 + ref 가 속한 «절 제목»의 잔여·제외 류. 없으면 None."""
    s, hits = str(text or ""), []
    for m in re.finditer(re.escape(ref) + r"(?!\d)", s):
        lo, hi = max(0, m.start() - width), min(len(s), m.end() + width)
        a = max([lo] + [k + 1 for k in (s.rfind(c, lo, m.start()) for c in ".\n⏎。") if k >= 0])
        ends = [k for k in (s.find(c, m.end(), hi) for c in ".\n⏎。") if k >= 0]
        n = GUARD_SENT.search(s[a:(min(ends) if ends else hi)])
        if n:
            hits.append("문장: " + n.group(0))
        heads = list(_HEADING.finditer(s, 0, m.start()))
        if heads and GUARD_HEAD.search(heads[-1].group(0)):
            hits.append("절: " + heads[-1].group(0).strip(" \n⏎#*")[:40])
    return sorted(set(hits)) or None


# ── draft · fill · review ─────────────────────────────────────────────────
def cmd_draft(a) -> None:
    scan = load(a.scan)
    snap = Path(a.snapshot_dir)
    rows = []
    for f in scan["findings"]:
        sp = snap / f"{f['item_id']}.json"
        item = load(sp).get("item") if sp.exists() else None
        for ref in f["refs"]:
            # 그 ID 가 «글자 그대로» 있는 문장을 먼저 보인다. 없을 때만(범위 표기 API-046~049 등)
            # 같은 접두 문장으로 물러선다 — 섞으면 검토자가 다른 ID 의 문장을 보고 판정한다.
            exact, loose = [], []
            for loc in f["locations"]:
                v = resolve(item or {}, loc)
                if not isinstance(v, str):
                    continue
                if re.search(re.escape(ref) + r"(?!\d)", v):
                    exact.append({"at": loc, "text": excerpt(v, ref)})
                elif ref.split("-")[0] + "-" in v:
                    loose.append({"at": loc, "text": excerpt(v, ref)})
            ctx = exact or loose
            g = sorted({h for loc in f["locations"] for h in (guard_signal(resolve(item or {}, loc), ref) or [])})
            retired = (f.get("item_status") or "") in RETIRED
            rows.append({
                "key": rkey(f["item_id"], f["rule"], f["field"], ref),
                "item_id": f["item_id"], "item_type": f["item_type"], "item_title": f.get("item_title", ""),
                "item_status": f.get("item_status"), "rule": f["rule"], "field": f["field"], "ref": ref,
                "context": ctx[:3],
                "guard": g or None,
                "kind": "폐기 항목" if retired else "",
                "reason": "주체 항목이 폐기됨(item_status)" if retired else "",
            })
    dump(a.out, {"server": scan.get("server"), "project_id": scan.get("project_id"), "decisions": rows})
    auto = sum(1 for r in rows if r["kind"])
    no_ctx = sum(1 for r in rows if not r["context"])
    guarded = sum(1 for r in rows if r.get("guard"))
    print(f"✅ 초안 — 참조 {len(rows)}건 · 자동 분류(폐기 항목) {auto} · 판단 필요 {len(rows) - auto}"
          + (f" · ⚠️ 문맥 못 찾음 {no_ctx}건(스냅샷 누락?)" if no_ctx else "")
          + (f" · 🚧 경계·선례 문구 {guarded}건(이관이면 사유 필수)" if guarded else ""))


def guard_reason_problem(reason: str, context_text: str) -> str:
    """🚧 경계·선례 문구가 붙은 행을 이관·채움할 때의 사유 검사 — 비어 있지 않은 것만으로는 부족하다.
    KLID 상용(2026-10-02): 가드 행 194건 중 22건이 행마다 같은 공통 문구였다(가드가 형식만 남음).
    사유에는 그 행 문맥의 원문 조각을 「」로 6자 이상 인용해야 하고, 그 조각이 문맥에 실재해야 한다."""
    reason = (reason or "").strip()
    if not reason:
        return "사유가 비었다"
    qs = [q for q in re.findall(r"「([^」]{6,})」", reason)]
    if not qs:
        return "사유에 그 행 문맥의 원문 조각을 「」로 6자 이상 인용하라(왜 이 문장이 경계·선례가 아니라 관계인지)"
    nc = re.sub(r"\s+", " ", context_text or "")

    def found(q: str) -> bool:
        # 「…」로 줄인 인용도 받는다 — 조각마다 문맥에 순서대로 있어야 한다
        pos = 0
        for part in [x.strip() for x in re.split(r"…|\.\.\.", re.sub(r"\s+", " ", q)) if len(x.strip()) >= 3]:
            i = nc.find(part, pos)
            if i < 0:
                return False
            pos = i + len(part)
        return pos > 0
    if not any(found(q) for q in qs):
        return f"사유의 인용 「{qs[0][:30]}」 이 그 행 문맥에 없다"
    return ""


def cmd_fill(a) -> None:
    """에이전트가 정한 부류를 반영. 입력 = [{key, kind, reason}] (key 는 draft 의 key)."""
    d = load(a.decisions)
    by = {r["key"]: r for r in d["decisions"]}
    inp = load(a.input)
    if isinstance(inp, dict):
        inp = inp.get("judged") or inp.get("rows") or []
    bad, miss = [], []
    guard_reasons = Counter()
    for x in inp:
        if x.get("kind") not in ALL_KINDS:
            bad.append(f"{x.get('key')} kind={x.get('kind')!r}")
            continue
        if x["kind"] != MIGRATE and not (x.get("reason") or "").strip():
            bad.append(f"{x.get('key')} — 제외·보류는 사유가 필수다")
            continue
        r = by.get(x["key"])
        if not r:
            miss.append(x["key"])
            continue
        if x["kind"] == MIGRATE and r.get("guard"):
            ctxt = " ".join(c.get("text", "") for c in (r.get("context") or []))
            if getattr(a, "snapshot_dir", None):  # 판정자는 발췌가 아니라 항목 원문을 읽는다 — 원문 전체로도 대조
                sp = Path(a.snapshot_dir) / f"{r['item_id']}.json"
                if sp.exists():
                    flat = []
                    def walk(v):
                        if isinstance(v, str): flat.append(v)
                        elif isinstance(v, dict): [walk(y) for y in v.values()]
                        elif isinstance(v, list): [walk(y) for y in v]
                    walk(load(sp).get("item", {}).get("data") or {})
                    ctxt += " " + " ".join(flat)
            why = guard_reason_problem(x.get("reason"), ctxt)
            if why:
                bad.append(f"{x['key']} — 경계·선례 문구가 붙은 행({'; '.join(r['guard'])[:60]})을 이관하려면 {why} "
                           "(아니면 경계 선언·선례 인용·보류)")
                continue
            guard_reasons[x["reason"].strip()] += 1
        r["kind"], r["reason"] = x["kind"], x.get("reason", "")
    bad += [f"같은 사유가 가드 행 {n}건에 반복 — 행마다 그 문장을 인용해 따로 판정하라: {t[:60]!r}"
            for t, n in guard_reasons.items() if n >= 5]
    if bad or miss:
        die("반영 거부:\n  " + "\n  ".join(bad[:20] + [f"없는 key: {m}" for m in miss[:20]]))
    dump(a.decisions, d)
    left = sum(1 for r in d["decisions"] if not r["kind"])
    print(f"✅ {len(inp)}건 반영 · 남은 미분류 {left}")


def cmd_review_md(a) -> None:
    d = load(a.decisions)["decisions"]
    left = [r for r in d if r.get("kind") not in ALL_KINDS]
    if left:
        die(f"미분류 {len(left)}건 — 예: {left[0]['key']}")
    c = Counter(r["kind"] for r in d)
    L = ["# 산문 참조 이관 — 분류 검토", "",
         f"참조 **{len(d)}건** — " + " · ".join(f"{k} {c[k]}" for k in ALL_KINDS if c[k]), "",
         "> ☠️ **이관이 아닌 것을 이관으로 바꾸면 틀린 엣지가 생긴다** — 그 항목이 바뀔 때마다 엉뚱한 곳에",
         "> 「재검토 필요」가 붙는다. 애매하면 「보류」로 두라. 보류는 실패가 아니다.", ""]
    for k in ALL_KINDS:
        rs = [r for r in d if r["kind"] == k]
        if not rs:
            continue
        L += [f"## {k} ({len(rs)})", "", "| 항목 | 칸 | 참조 | 문맥 | 사유 |", "|---|---|---|---|---|"]
        for r in rs:
            ctx = (r["context"][0]["text"] if r.get("context") else "").replace("|", "\\|")
            rsn = (r.get("reason") or "").replace("|", "\\|")
            if r.get("guard"):
                rsn = "🚧 " + "; ".join(r["guard"]).replace("|", "\\|") + (" — " + rsn if rsn else "")
            L.append(f"| {r['item_id']} | `{r['field']}` | {r['ref']} | {ctx[:160]} | {rsn} |")
        L.append("")
    Path(a.out).write_text("\n".join(L) + "\n", encoding="utf-8")
    print(f"✅ 검토표 → {a.out}")


# ── plan ──────────────────────────────────────────────────────────────────
def cmd_plan(a) -> None:
    dd = load(a.decisions)
    dec = dd["decisions"]
    left = [r for r in dec if r.get("kind") not in ALL_KINDS]
    if left:
        die(f"미분류 {len(left)}건 — 분류·검토를 끝내고 오라(예: {left[0]['key']})")
    snap = Path(a.snapshot_dir)
    shapes = {}
    if not getattr(a, "schemas", None) and not (a.string_fields or []):
        # ☠️ 두 번 났다(KLID SD-011 · CatchAll SD-009) — 옵션이 있어도 빠뜨리면 단일 값 칸을 배열로 올려 배치가 중단된다.
        die("--schemas <diag>/diagnose.json 이 필요하다 — 칸 모양(단일 값/배열)을 모르면 계획을 만들지 않는다")
    if getattr(a, "schemas", None):
        for t, fs in (load(a.schemas).get("schemas") or {}).items():
            for f, meta in fs.items():
                sch = meta.get("schema") or {}
                shapes[(t, f)] = sch.get("type")
    wanted: "OrderedDict[str, OrderedDict[str, list]]" = OrderedDict()
    for r in dec:
        if r["kind"] == MIGRATE:
            lst = wanted.setdefault(r["item_id"], OrderedDict()).setdefault(r["field"], [])
            if r["ref"] not in lst:
                lst.append(r["ref"])
    items, conflicts, already = [], [], []
    conflict_refs = 0
    for item_id, fields in wanted.items():
        sp = snap / f"{item_id}.json"
        if not sp.exists():
            die(f"스냅샷 없음: {sp}")
        it = load(sp).get("item", {})
        data = it.get("data") or {}
        ops, changes = [], []
        for field, refs in fields.items():
            before = data.get(field)
            # ☠️ 칸 모양은 추측하지 않는다 — 비어 있는 단일 값 칸(screen_design.design_system_id 등)을 배열로 가정하면
            #    서버가 전부 거부한다(KLID 2차 실측 — SD-011 에서 배치 중단). --schemas(진단 파일)가 있으면 그것으로 판정.
            single = field in (a.string_fields or []) or (
                shapes.get((it.get("type"), field)) == "string")
            if isinstance(before, str) or (before is None and single):
                # 단일 값 칸 — 이미 다른 값이 있으면 덮어쓰지 않는다. 사람이 정할 일이다.
                if len(refs) != 1:
                    conflicts.append(f"{item_id}.{field}: 단일 값 칸에 올릴 참조가 {len(refs)}개 {refs}")
                    conflict_refs += len(refs)
                elif before and before != refs[0]:
                    conflicts.append(f"{item_id}.{field}: 이미 {before!r} — {refs[0]!r} 로 덮어쓰지 않음")
                    conflict_refs += 1
                elif before == refs[0]:
                    already.append(f"{item_id}.{field} {refs[0]}")
                else:
                    ops.append({"op": "set", "path": field, "value": refs[0]})
                    changes.append({"field": field, "before": before, "add": refs, "after": refs[0]})
                continue
            if before is not None and not isinstance(before, list):
                conflicts.append(f"{item_id}.{field}: 배열도 문자열도 아님({type(before).__name__})")
                conflict_refs += len(refs)
                continue
            cur = list(before or [])
            add = [x for x in refs if x not in cur]
            already += [f"{item_id}.{field} {x}" for x in refs if x in cur]
            if not add:
                continue
            after = cur + add
            # 칸이 없거나 비었으면 add 가 실패할 수 있다 — 그땐 set 으로 통째 만든다.
            ops += [{"op": "set", "path": field, "value": after}] if not cur else \
                   [{"op": "add", "path": field, "value": x} for x in add]
            changes.append({"field": field, "before": before, "add": add, "after": after})
        if ops:
            items.append({"item_id": item_id, "item_type": it.get("type"),
                          "snapshot_version": it.get("current_version"), "ops": ops, "changes": changes})
    c = Counter(r["kind"] for r in dec)
    to_add = sum(len(ch["add"]) for i in items for ch in i["changes"])
    # ☠️ 항등식 — 이관 결정 = 올릴 것 + 이미 있던 것 + 충돌로 뺀 것
    if to_add + len(already) + conflict_refs != c[MIGRATE]:
        die(f"계획 항등식 불일치 — 이관 {c[MIGRATE]} ≠ 올릴 {to_add} + 이미 {len(already)} + 충돌 {conflict_refs}")
    plan = {"server": dd.get("server"), "project_id": dd.get("project_id"),
            "totals": {"refs": len(dec), "by_kind": {k: c[k] for k in ALL_KINDS if c[k]},
                       "items_to_update": len(items), "refs_to_add": to_add,
                       "already_present": len(already), "conflict_refs": conflict_refs},
            "items": items, "already_present": already, "conflicts": conflicts}
    dump(a.out, plan)
    print(f"✅ 계획 — 참조 {len(dec)} 중 이관 {c[MIGRATE]} → 올릴 {to_add} · 이미 있음 {len(already)}"
          f" · 충돌 {conflict_refs} · 갱신 항목 {len(items)}")
    for s in conflicts:
        print(f"   ⚠️ {s}")


# ── apply ─────────────────────────────────────────────────────────────────
def cmd_apply(a) -> None:
    plan = load(a.plan)
    srv = server(a.server)
    if plan.get("server") and plan["server"] != a.server:
        die(f"계획은 서버 '{plan['server']}' 기준인데 '{a.server}' 에 쓰려 한다 — 서버를 섞지 마라")
    only = set(a.only.split(",")) if a.only else None
    items = [i for i in plan["items"] if only is None or i["item_id"] in only]
    if a.limit:
        items = items[: a.limit]
    log = Path(a.log)
    log.parent.mkdir(parents=True, exist_ok=True)
    print(f"{'[예행] ' if a.dry else ''}적용 대상 {len(items)}항목 → 서버 {srv['name']} ({srv['url']})")
    ok = 0
    probe = bool(getattr(a, "probe", False)) and not a.dry
    batch = max(1, int(getattr(a, "batch", 5) or 5))
    chunks = [items[i:i + batch] for i in range(0, len(items), batch)] if probe else [items]
    with log.open("a", encoding="utf-8", buffering=1) as lf:  # 줄 버퍼 — 적용 중 진행이 로그로 바로 보이게
      for ci, chunk in enumerate(chunks, 1):
        print(f"⏳ 묶음 {ci}/{len(chunks)} · 이번 {len(chunk)}항목 · 누적 {sum(len(c) for c in chunks[:ci - 1])}/{len(items)}", flush=True)
        before = stale_state(srv, plan["project_id"], [x["item_id"] for x in chunk]) if probe else None
        t0 = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime(time.time() - 1))
        for it in chunk:
            summary = " / ".join(f"{'·'.join(ch['add'])}→{ch['field']}" for ch in it["changes"])
            args = {"project_id": plan["project_id"], "id": it["item_id"], "data_mode": "patch", "patch": it["ops"],
                    "change_summary": (plan.get("change_summary") or
                                       "산문에 적힌 참조를 포인터 칸으로 이관(mc-logi-schema-fill) — {summary}. 산문은 그대로 둔다."
                                       ).format(summary=summary)}
            if plan.get("change_kind"):
                args["change_kind"] = plan["change_kind"]
            if plan.get("guard_version") and it.get("snapshot_version"):
                # ☠️ 통째로 바꾸는 칸(산문 슬림화·구조 칸 set)은 스냅샷 뒤 남의 수정을 덮을 수 있다 — 버전으로 막는다.
                args["base_version"] = it["snapshot_version"]
            if a.dry:
                print(f"   {it['item_id']:<14} {summary}")
                ok += 1
                continue
            try:
                r = mcp(srv, "update_item", args, retries=0)
            except RuntimeError as e:
                m = str(e)
                lf.write(json.dumps({"item": it["item_id"], "ok": False, "error": m[:500]}, ensure_ascii=False) + "\n")
                hint = " — 서버가 이 칸을 모른다(배포가 안 된 서버?)" if "unrecognized" in m.lower() else ""
                die(f"{it['item_id']} 적용 실패{hint}: {m[:300]}\n   성공 {ok}/{len(items)} 에서 중단 — 나머지는 손대지 않았다", 3)
            warns = [w.get("code") for w in (r.get("warnings") or []) if isinstance(w, dict)]
            noop = [w for w in warns if w in ("DATA_UNCHANGED_NOOP", "PATCH_OP_NOOP")]
            ver = (r.get("item") or {}).get("current_version")
            lf.write(json.dumps({"item": it["item_id"], "ok": not noop, "version": ver, "warnings": warns},
                                ensure_ascii=False) + "\n")
            if noop:
                # 성공 응답이지만 «바뀌지 않았다» — 조용히 넘기면 반영된 것처럼 보인다.
                die(f"{it['item_id']} — 서버가 {noop} 를 돌려줬다(성공이지만 미반영). 중단.", 3)
            ok += 1
            print(f"   ✅ {it['item_id']:<14} v{ver}  {summary}")
        if probe:
            after = stale_state(srv, plan["project_id"], [x["item_id"] for x in chunk])
            ids = {x["item_id"] for x in chunk}
            changed = sorted(k for k in before if before[k] != after.get(k))
            lf.write(json.dumps({"probe_batch": ci, "items": sorted(ids), "targets": len(before),
                                 "changed": changed}, ensure_ascii=False) + "\n")
            print(f"   🔎 묶음 {ci}: 자기+하위 {len(before)}항목 재검토 상태 변화 {len(changed)}")
            self_rel = [k for k in changed if k in ids and before[k]["stale"] and not after[k]["stale"]]
            if self_rel and getattr(a, "restore_self", False):
                # 새 값을 넣는 쓰기(재료 D·구조 칸)는 «실제 변경»이라 자기 재검토 표시가 자동 해제된다 — 검토가 아니므로 되살린다.
                r = mcp(srv, "restore_review_needed", {"project_id": plan["project_id"], "item_ids": self_rel,
                                                         "since": t0, "dry_run": False})
                restored = {i["item_id"]: i["restored"] for i in r.get("items", [])}
                again = stale_state(srv, plan["project_id"], self_rel)
                # 원상 = «다시 재검토 필요 + 원래 있던 표시가 하나도 안 빠졌다». 같은 묶음의 형제 항목이 새로 붙인 표시로
                #   늘어나는 것은 허용한다(형제끼리 서로 가리키면 생긴다 — 상용 Self API-202 실측: 5 → 7).
                def _cnt(v):
                    return (((v or {}).get("flags") or {}).get("propagated") or {}).get("count") or 0
                still = [k for k in self_rel if not (again.get(k) or {}).get("stale") or _cnt(again.get(k)) < _cnt(before[k])]
                lf.write(json.dumps({"probe_batch": ci, "restored_self": restored, "still_differs": still},
                                    ensure_ascii=False) + "\n")
                print(f"      ↳ 자기 표시 자동 복원: {restored}" + (f" · 원상 불일치 {still}" if still else " · 원상 일치"))
                if still:
                    die(f"자기 표시 복원 뒤에도 원상과 다르다 → {still} — 멈춘다", 4)
                changed = [k for k in changed if k not in self_rel]
                self_rel = []
            if changed and getattr(a, "allow_dependents", False) and not self_rel:
                # 재료 D(코드 근거)처럼 «새 관계»를 만드는 라운드 — 하위에 표시가 붙는 것이 예상 동작이다. 기록만 하고 계속.
                print("      ↳ 하위 표시 변화(예상 동작으로 허용): " + ", ".join(changed[:12]))
                changed = []
            if changed:
                lines = [f"{k}: {json.dumps(before[k], ensure_ascii=False)} → {json.dumps(after.get(k), ensure_ascii=False)}"
                         for k in changed]
                die("재검토 상태가 바뀌었다 — 이 묶음에서 멈춘다(적용된 것은 그대로):\n   " + "\n   ".join(lines[:12])
                    + ("\n   ↳ 자기 표시가 풀린 항목: " + ", ".join(self_rel)
                       + " — 원인 확인 뒤 restore_review_needed(dry_run 먼저)로 복원" if self_rel else "")
                    + "\n   ↳ 하위에 새로 붙은 표시는 이 쓰기가 «산문 복사»로 인정되지 않았다는 뜻 — 값·근거를 다시 보라", 4)
    print(f"{'[예행] ' if a.dry else ''}완료 {ok}/{len(items)}")


def stale_state(srv, project_id: str, ids) -> dict:
    """묶음 전후 비교용 — 적용 항목 «자신» + 그것을 가리키는 항목(하위)의 재검토 상태.

    ☠️ 하위만 보면 안 된다: 항목 수정이 «자기» 재검토 표시를 자동 해제하는 경로가 있다(상용 Self 2026-09-28,
    21항목·47행이 조용히 풀렸다 — CO-189). 두 쪽을 다 본다.
    """
    targets = set(ids)
    for i in ids:
        n = mcp(srv, "get_neighbors", {"project_id": project_id, "id": i, "direction": "in"})
        targets |= {x["id"] for x in n.get("backward", [])}
    out = {}
    for t in sorted(targets):
        g = mcp(srv, "get_item", {"project_id": project_id, "id": t, "fields": ["_none"]})["item"]
        out[t] = {"stale": g.get("stale"), "flags": g.get("stale_flags")}
    return out


# ── verify ────────────────────────────────────────────────────────────────
def cmd_verify(a) -> None:
    plan = load(a.plan)
    dec = load(a.decisions)["decisions"]
    rescan = load(a.rescan)
    after = Path(a.after_dir)
    only = set(a.only.split(",")) if a.only else None
    now = {rkey(f["item_id"], f["rule"], f["field"], ref) for f in rescan["findings"] for ref in f["refs"]}
    fail, warn = [], []
    scope = [r for r in dec if only is None or r["item_id"] in only]
    migrated_keys = set()
    for it in plan["items"]:
        for ch in it["changes"]:
            for ref in ch["add"]:
                migrated_keys.add((it["item_id"], ch["field"], ref))
    for r in scope:
        applied = (r["item_id"], r["field"], r["ref"]) in migrated_keys
        if r["kind"] == MIGRATE and applied and r["key"] in now:
            fail.append(f"이관했는데 재스캔에 남음: {r['key']}")
        if r["kind"] != MIGRATE and r["key"] not in now:
            warn.append(f"제외·보류였는데 재스캔에서 사라짐(다른 편집?): {r['key']}")
    known = {r["key"] for r in dec}
    for k in sorted(now - known):
        if only is None or k.split("|")[0] in only:
            warn.append(f"계획에 없던 새 발화: {k}")
    # ★ 최종값 = 계획값 — 「올렸다」가 아니라 「그 값이 됐다」를 본다.
    checked = 0
    for it in plan["items"]:
        if only is not None and it["item_id"] not in only:
            continue
        p = after / f"{it['item_id']}.json"
        if not p.exists():
            fail.append(f"적용 후 스냅샷 없음: {p}")
            continue
        data = load(p).get("item", {}).get("data") or {}
        for ch in it["changes"]:
            checked += 1
            if data.get(ch["field"]) != ch["after"]:
                fail.append(f"{it['item_id']}.{ch['field']}: 최종값 {data.get(ch['field'])!r} ≠ 계획 {ch['after']!r}")
    c = Counter(r["kind"] for r in scope)
    L = ["# 산문 참조 이관 — 검증", "",
         f"결과: **{'✅ 합격' if not fail else '❌ 불합격'}** · 실패 {len(fail)} · 주의 {len(warn)} · 최종값 대조 {checked}칸"
         f" · 범위 {'시범 ' + str(len(only)) + '항목' if only else '전체'}", "",
         "| 부류 | 건수 |", "|---|---:|", *[f"| {k} | {c[k]} |" for k in ALL_KINDS if c[k]],
         f"| **합계** | **{sum(c.values())}** |", ""]
    if fail:
        L += ["## ❌ 실패", "", *[f"- {s}" for s in fail], ""]
    if warn:
        L += ["## ⚠️ 주의", "", *[f"- {s}" for s in warn], ""]
    Path(a.out).write_text("\n".join(L) + "\n", encoding="utf-8")
    print("\n".join(L[:3]))
    if fail:
        for s in fail[:10]:
            print(f"   ❌ {s}")
        sys.exit(2)


def cmd_tally(a) -> None:
    d = load(a.decisions)["decisions"]
    c = Counter(r.get("kind") or "(미분류)" for r in d)
    for k in [*ALL_KINDS, "(미분류)"]:
        if c[k]:
            print(f"{k:<12} {c[k]:>5}")
    print(f"{'합계':<12} {sum(c.values()):>5}")


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sp = ap.add_subparsers(dest="cmd", required=True)

    def add(name, fn, *specs):
        s = sp.add_parser(name)
        for flag, kw in specs:
            s.add_argument(flag, **kw)
        s.set_defaults(fn=fn)

    R = {"required": True}
    add("preflight", cmd_preflight, ("--server", R), ("--project", R))
    add("scan", cmd_scan, ("--server", R), ("--project", R), ("--type", {}), ("--rule", {}), ("--out", R))
    add("snapshot", cmd_snapshot, ("--server", R), ("--project", R), ("--dir", R),
        ("--from-scan", {}), ("--from-plan", {}), ("--ids", {"default": ""}))
    add("draft", cmd_draft, ("--scan", R), ("--snapshot-dir", R), ("--out", R))
    add("fill", cmd_fill, ("--decisions", R), ("--input", R), ("--snapshot-dir", {}))
    add("review-md", cmd_review_md, ("--decisions", R), ("--out", R))
    add("plan", cmd_plan, ("--decisions", R), ("--snapshot-dir", R), ("--out", R),
        ("--string-fields", {"nargs": "*", "default": []}), ("--schemas", {}))
    add("apply", cmd_apply, ("--server", R), ("--plan", R), ("--log", R), ("--only", {"default": ""}),
        ("--probe", {"action": "store_true"}), ("--batch", {"type": int, "default": 5}),
        ("--allow-dependents", {"action": "store_true"}), ("--restore-self", {"action": "store_true"}),
        ("--limit", {"type": int, "default": 0}), ("--dry", {"action": "store_true"}))
    add("verify", cmd_verify, ("--plan", R), ("--decisions", R), ("--rescan", R), ("--after-dir", R),
        ("--only", {"default": ""}), ("--out", R))
    add("tally", cmd_tally, ("--decisions", R))
    a = ap.parse_args()
    a.fn(a)


if __name__ == "__main__":
    main()
