#!/usr/bin/env python3
"""mc-logi-schema-fill — 새 칸 채우기(구조 칸·담당자 종류)·산문 슬림화·담당자 안내표.

연결 칸(산문 속 ID → 포인터 칸)은 prose_migrate.py 가 맡는다. 이 파일은 그 밖의 전부다.
통신·스냅샷·적용·로그는 prose_migrate.py 의 것을 그대로 쓴다(한 곳에서만 고친다).

  diagnose      새 칸 채움 현황 — 항목×칸 판정표(채움/빈칸/문자열 담당자)와 요약 md
  worklist      빈 칸 작업표 — 에이전트가 산문을 읽고 칸마다 판정·값·근거를 적을 자리
  fill-fields   판정 반영 — 「채움」은 값+근거 인용(산문에 실재해야 함), 나머지는 사유 필수
  review-fields 사람 검토용 md
  plan-fields   적용 계획 — 빈 칸만 채운다(담당자 문자열→객체 승격은 예외). apply 는 prose_migrate 로
  guide         「안내」 판정 → 담당자용 단계별 체크리스트 md + 답변 양식 json
  slim-plan     산문 슬림화 계획 — «삭제만» 허용, 지운 문장마다 옮겨 간 칸이 채워져 있어야 한다
  relation-cands  재료 E — 근거 없는 설계 의도 관계의 후보(그래프 이웃·개념 겹침·같은 도메인) 뽑기
  relation-fill   AI 판정(제안·아님·보류 + 사유) 반영 — 대상은 실재 항목만
  relation-review 사람 검토표 + 결정 양식(채택·기각)
  relation-plan   «채택»한 줄만 적용 계획으로 — 기각·아님은 장부에 남겨 다시 제안하지 않는다
  check         적용 후 최종값 == 계획값 대조(구조 칸·슬림화 공용)
  progress      진단 두 번의 차이(before/after) — 무엇이 채워졌나

☠️ 추정 금지 — 값의 근거가 산문에 없으면 「채움」이 아니라 「안내」다. fill-fields 가 인용문이
   실제 산문에 있는지 글자 그대로 대조한다(담당자 답변은 `담당자:` 로 시작하는 근거로 구분).
"""
from __future__ import annotations

import argparse
import importlib.util
import json
import re
import sys
from collections import Counter, OrderedDict
from pathlib import Path

HERE = Path(__file__).resolve().parent
_sp = importlib.util.spec_from_file_location("prose_migrate", HERE / "prose_migrate.py")
pm = importlib.util.module_from_spec(_sp)
_sp.loader.exec_module(pm)  # type: ignore[union-attr]
load, dump, die, mcp, server = pm.load, pm.dump, pm.die, pm.mcp, pm.server

MANIFEST = HERE.parent / "references" / "new-fields.json"
VERDICTS = ["채움", "제외", "안내", "해당 없음", "보류"]  # 제외 = 이 «후보 값»을 거절(칸 자체는 다른 값으로 채워질 수 있다)
OWNER_KINDS = {"team", "org", "role", "person"}
PROSE_KEYS = ("description", "notes", "rationale", "summary", "context", "purpose")
REF_RE = re.compile(r"\^([A-Z][A-Z0-9_]*)-\\d\+\$")


def fkey(item_id, field) -> str:
    return f"{item_id}|{field}"


def empty(v) -> bool:
    return v is None or v == "" or v == [] or v == {}


def field_kind(prop: dict) -> str:
    """서버 json_schema 로 칸 종류를 판정한다 — 목록을 손으로 들고 다니지 않는다."""
    if not isinstance(prop, dict):
        return "구조"
    pats = []
    for node in (prop, prop.get("items") or {}):
        if isinstance(node, dict) and isinstance(node.get("pattern"), str):
            pats.append(node["pattern"])
    for alt in prop.get("oneOf") or prop.get("anyOf") or []:
        if isinstance(alt, dict) and alt.get("type") == "object" and "kind" in (alt.get("properties") or {}):
            return "담당자"
    return "연결" if any(REF_RE.search(p) for p in pats) else "구조"


# 구조 칸 — 「어디서 구현했나」 같은 위치·연결 값이지 서술이 아니다. evidence 의 근거로 쓰면
# 커밋 해시만 보고 «검증됨»을 만든다(KLID 상용 2026-10-02: 한 묶음 208건 전부 commits 해시로 채움).
STRUCT_KEYS = {"commits", "module_paths", "modules", "implementation", "records", "subtasks", "evidence",
               "design_item_id", "related_apis", "related_dfeats", "related_erds", "attached_files"}


def prose_text(data: dict, exclude: "set[str] | None" = None) -> str:
    """근거 대조용 — 항목 data 의 모든 문자열을 이어 붙인다(산문 칸만 보면 notes 하위 등을 놓친다).
    exclude 의 키(하위 포함)는 건너뛴다 — evidence 판정은 STRUCT_KEYS 를 빼고 대조한다."""
    out = []

    def walk(v):
        if isinstance(v, str):
            out.append(v)
        elif isinstance(v, dict):
            for k, x in v.items():
                if exclude and k in exclude:
                    continue
                walk(x)
        elif isinstance(v, list):
            for x in v:
                walk(x)
    walk(data)
    return "\n".join(out)


def norm(s: str) -> str:
    return re.sub(r"\s+", " ", s).strip()


# ── diagnose ──────────────────────────────────────────────────────────────
def cmd_diagnose(a) -> None:
    srv = server(a.server)
    man = load(MANIFEST)
    targets: "OrderedDict[str, list]" = OrderedDict()
    for t, fs in man["new_fields"].items():
        targets.setdefault(t, []).extend(fs)
    for t, fs in man["owner_fields"].items():
        targets.setdefault(t, []).extend(f for f in fs if f not in targets.get(t, []))
    if a.type:
        targets = OrderedDict((t, v) for t, v in targets.items() if t in a.type.split(","))
    out = Path(a.out_dir)
    snap = out / "snap"
    snap.mkdir(parents=True, exist_ok=True)
    scan_hit = set()
    if a.scan:
        for f in load(a.scan)["findings"]:
            scan_hit.add(fkey(f["item_id"], f["field"]))
    schemas, rows, perms = {}, [], {}
    for t, fields in targets.items():
        ids, off = [], 0
        while True:
            r = mcp(srv, "list_items", {"project_id": a.project, "type": t, "limit": 500, "offset": off})
            ids += [i["id"] for i in r.get("items") or []]
            if r.get("items"):
                perms[t] = bool((r.get("my_permissions") or {}).get("can_write"))
            pg = r.get("pagination") or {}
            if not pg.get("has_more"):
                break
            off = pg["next_offset"]
        if not ids:
            continue
        sch = mcp(srv, "get_item_schema", {"type": t})
        props = (sch.get("json_schema") or {}).get("properties") or {}
        summ = {f.get("name"): f for f in sch.get("fields_summary") or []}
        notes = [n for n in ((sch.get("hints") or {}).get("workflow_notes") or []) if isinstance(n, str)]
        schemas[t] = {}
        for f in fields:
            if f not in props:
                schemas[t][f] = {"kind": "서버에 없음", "description": "", "notes": []}
                continue
            schemas[t][f] = {"kind": field_kind(props[f]),
                             "description": (props[f].get("description") or summ.get(f, {}).get("description") or "")[:600],
                             "notes": [n for n in notes if n.startswith(f + ":") or f"`{f}`" in n][:3],
                             "schema": props[f]}
        for item_id in ids:
            p = snap / f"{item_id}.json"
            if not p.exists() or a.refresh:
                p.write_text(json.dumps(mcp(srv, "get_item", {"project_id": a.project, "id": item_id}),
                                        ensure_ascii=False, indent=1), encoding="utf-8")
            it = load(p).get("item", {})
            if it.get("id") != item_id or not isinstance(it.get("data"), dict):
                die(f"스냅샷 검산 실패: {item_id}")
            data = it["data"]
            for f in fields:
                meta = schemas[t][f]
                v = data.get(f)
                if meta["kind"] == "서버에 없음":
                    state = "서버에 없음"
                elif meta["kind"] == "담당자":
                    state = "빈칸" if empty(v) else ("문자열" if isinstance(v, str) else "채움")
                else:
                    state = "빈칸" if empty(v) else "채움"
                rows.append({"key": fkey(item_id, f), "item_id": item_id, "type": t, "title": it.get("title", ""),
                             "status": it.get("status"), "field": f, "kind": meta["kind"], "state": state,
                             "prose_ref": fkey(item_id, f) in scan_hit,
                             "prose_len": sum(len(data.get(k) or "") for k in PROSE_KEYS if isinstance(data.get(k), str))})
        print(f"   {t:<24} 항목 {len(ids):>4} · 칸 {len(fields)}")
    dump(out / "diagnose.json", {"server": a.server, "project_id": a.project, "schemas": schemas, "rows": rows,
                                 "can_write": perms})
    # 요약 md — 타입×칸 별로 «채움/전체»
    agg: "OrderedDict[tuple, Counter]" = OrderedDict()
    for r in rows:
        agg.setdefault((r["type"], r["field"], r["kind"]), Counter())[r["state"]] += 1
        if r["state"] == "빈칸" and r["prose_ref"]:
            agg[(r["type"], r["field"], r["kind"])]["산문근거"] += 1
    kinds = Counter()
    for r in rows:
        kinds[(r["kind"], r["state"])] += 1
    L = ["# 새 칸 채움 현황", "",
         f"항목×칸 **{len(rows)}** · 타입 {len({r['type'] for r in rows})} · 항목 {len({r['item_id'] for r in rows})}", "",
         "| 종류 | 채움 | 빈칸 | 문자열(종류 미표시) |", "|---|---:|---:|---:|"]
    for k in ["연결", "구조", "담당자"]:
        L.append(f"| {k} | {kinds[(k, '채움')]} | {kinds[(k, '빈칸')]} | {kinds[(k, '문자열')] if k == '담당자' else '—'} |")
    ro = sorted(t for t, w in perms.items() if not w)
    if ro:
        # ☠️ 적용 단계에서 처음 알면 분류·검토에 쓴 시간이 통째로 버려진다(CudoCall 실측 — 1라운드 49칸 준비 뒤 0건 적용).
        L += ["", f"🔒 **이 키로는 쓸 수 없는 타입 {len(ro)}/{len(perms)}**: {', '.join(ro)}",
              "   → 그 타입은 채울 수 없다. 프로젝트 담당자 키로 실행하거나 쓰기 권한을 받아 오라. **여기서 멈추고 사용자에게 알린다.**"]
    if kinds[("서버에 없음", "서버에 없음")]:
        L += ["", f"⚠️ **서버가 모르는 칸 {kinds[('서버에 없음', '서버에 없음')]}건** — 이 서버는 아직 배포 전이다. 그 칸은 채울 수 없다."]
    L += ["", "| 타입 | 칸 | 종류 | 채움 | 빈칸 | 빈칸 중 산문에 ID 있음 | 문자열 |", "|---|---|---|---:|---:|---:|---:|"]
    for (t, f, k), c in agg.items():
        tot = sum(v for s, v in c.items() if s != "산문근거")
        L.append(f"| {t} | `{f}` | {k} | {c['채움']}/{tot} | {c['빈칸']} | {c['산문근거'] or ''} | {c['문자열'] or ''} |")
    (out / "diagnose.md").write_text("\n".join(L) + "\n", encoding="utf-8")
    # ☠️ 재료 타입도 스냅샷한다 — derive 는 «다른 항목의 구조 칸»(ADR.references · 역할.permissions · 사고.timeline)을
    #    읽는데, 그 타입에 새 칸이 없으면 위 루프가 받지 않는다. 빠지면 역방향 후보가 «조용히 0»이 된다
    #    (CudoCall 상용 복사본 실측 — ADR 후보 19 → 0. dev 에서는 전체 항목을 수동으로 넣어 둬서 가려졌다).
    for t in DERIVE_SOURCES:
        off = 0
        while True:
            r = mcp(srv, "list_items", {"project_id": a.project, "type": t, "limit": 500, "offset": off})
            for i in r.get("items") or []:
                p = snap / f"{i['id']}.json"
                if not p.exists() or a.refresh:
                    p.write_text(json.dumps(mcp(srv, "get_item", {"project_id": a.project, "id": i["id"]}),
                                            ensure_ascii=False, indent=1), encoding="utf-8")
            pg = r.get("pagination") or {}
            if not pg.get("has_more"):
                break
            off = pg["next_offset"]
    print("\n".join(L[2:9]))
    if ro:
        print(f"🔒 쓰기 불가 타입 {len(ro)}/{len(perms)} — diagnose.md 참조")
    print(f"✅ 진단 → {out}/diagnose.md · diagnose.json")


# ── 단서 문장 ──────────────────────────────────────────────────────────────
# ☠️ 이 단어들은 «판정»이 아니라 «읽을 문장 고르기»에만 쓴다. 정규식으로 걸러 안내·보류로 보내면
#    적혀 있는 것을 «없다»고 안내하게 된다(CudoCall 실측 — IMPREC 9건 중 6건을 「산문에 없다」로 오판).
HINT_WORDS = {
    "evidence": r"검증|확인|실측|테스트|test|스모크|smoke|PASS|통과|일치|대조군|재현|로그|diff|health",
    "started_at": r"발생|시작|부터|최초|처음|~|이후",
    "acknowledged_at": r"인지|발견|보고|제보|알게|알림",
    "mitigated_at": r"완화|우회|임시|반영|조치|복구|되돌|롤백",
    "verification": r"확인|검증|검사|판정|대조|쿼리|SELECT",
    "owner": r"담당|운영|관리|주체|소유|책임|오너|owner",
    "owner_team": r"담당|운영|관리|주체|소유|책임|오너|owner",
}


def hints_for(data: dict, field: str, limit: int = 6) -> list:
    pat = HINT_WORDS.get(field)
    if not pat:
        return []
    out = []
    for txt in prose_text(data).split("\n"):
        for sent in re.split(r"(?<=[.。])\s+", txt):
            if re.search(pat, sent, re.I) and len(sent.strip()) > 8:
                out.append(sent.strip()[:300])
                if len(out) >= limit:
                    return out
    return out


def item_status_now(snapdir: Path, item_id: str):
    """항목의 «진행 상태» — 구현기록·마이그레이션 등은 data.status, 구현추적 mixin 은 implementation.status."""
    p = Path(snapdir) / f"{item_id}.json"
    if not p.exists():
        return None
    d = load(p).get("item", {}).get("data") or {}
    return d.get("status") or (d.get("implementation") or {}).get("status")


def ledger_skip(ledger, recheck: bool, snapdir) -> "set[str]":
    """장부에서 «다시 묻지 않을» 칸. 해당 없음은 영구, 보류·안내는 --recheck 로만 다시 연다 —
    단 보류에 `status_at`(판정 때 항목 상태)이 있고 지금 상태가 달라졌으면 자동으로 다시 연다
    (KLID 상용 2026-10-02: 진행 중 구현기록의 evidence 를 보류해 두면 구현이 끝나도 다시 묻지 않았다)."""
    if not ledger or not Path(ledger).exists():
        return set()
    skip = {"해당 없음"} if recheck else {"해당 없음", "보류", "안내"}
    out = set()
    for k, v in load(ledger).items():
        if v.get("verdict") not in skip:
            continue
        if v.get("verdict") == "보류" and v.get("status_at") and snapdir is not None:
            now = item_status_now(snapdir, k.split("|")[0])
            if now and now != v["status_at"]:
                continue  # 상태가 바뀌었다 — 다시 판정
        out.add(k)
    return out


# ── worklist ──────────────────────────────────────────────────────────────
def cmd_worklist(a) -> None:
    dg = load(a.diagnose)
    kinds = set(a.kind.split(","))
    types = set(a.type.split(",")) if a.type else None
    want = {"빈칸", "문자열"} if "담당자" in kinds else {"빈칸"}
    # ★ 「해당 없음」은 한 번 정하면 다시 묻지 않는다 — 장부(ledger)에 남은 것을 뺀다.
    na = ledger_skip(a.ledger, getattr(a, "recheck", False), Path(a.diagnose).parent / "snap")
    rows = [r for r in dg["rows"] if r["kind"] in kinds and r["state"] in want and r["key"] not in na
            and r["status"] not in pm.RETIRED and (types is None or r["type"] in types)]
    if na:
        print(f"   장부의 「해당 없음」 {len(na)}칸 제외")
    out = []
    for r in rows:
        meta = dg["schemas"][r["type"]][r["field"]]
        out.append({"key": r["key"], "item_id": r["item_id"], "type": r["type"], "title": r["title"],
                    "field": r["field"], "kind": r["kind"], "state": r["state"],
                    "field_help": meta["description"], "field_notes": meta["notes"],
                    "field_schema": json.dumps(meta.get("schema"), ensure_ascii=False)[:1500],
                    "hints": hints_for(load(Path(a.diagnose).parent / "snap" / f"{r['item_id']}.json")
                                       .get("item", {}).get("data") or {}, r["field"]),
                    "verdict": "", "value": None, "basis": "", "reason": ""})
    dump(a.out, {"server": dg["server"], "project_id": dg["project_id"], "snapshot_dir": str(Path(a.diagnose).parent / "snap"),
                 "rows": out})
    c = Counter((r["type"], r["field"]) for r in out)
    print(f"✅ 작업표 {len(out)}칸 (폐기 항목 제외) → {a.out}")
    for (t, f), n in c.most_common(20):
        print(f"   {t}.{f:<22} {n}")


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


# ── fill-fields ───────────────────────────────────────────────────────────
def cmd_fill_fields(a) -> None:
    wl = load(a.worklist)
    snap = Path(wl["snapshot_dir"])
    # 같은 key 가 여러 행일 수 있다(재료 A 와 C1 이 같은 후보를 낸 경우) — 판정은 그 key 의 모든 행에 반영한다.
    by_key: "dict[str, list]" = {}
    for r0 in wl["rows"]:
        by_key.setdefault(r0["key"], []).append(r0)
    idx = {k: v[0] for k, v in by_key.items()}
    bad = []
    src = load(a.input)
    # 판정 파일은 JSON 배열이 표준. {"judged": [...]} 로 감싸 오면 벗긴다.
    # `담당자:` 근거는 cmd_answers 가 만든 파일({"source": "answers", "rows": [...]})에서만 받는다 —
    # 판정 에이전트가 이 접두를 쓰면 인용 대조를 건너뛰는 통로가 된다(KLID 상용 2026-10-02: 87건).
    from_answers = isinstance(src, dict) and src.get("source") == "answers"
    guard_reasons = Counter()
    if isinstance(src, dict):
        src = src.get("rows") or src.get("judged") or []
    for d in src:
        r = idx.get(d.get("key"))
        if not r:
            bad.append(f"없는 key: {d.get('key')}")
            continue
        v = d.get("verdict")
        if v not in VERDICTS:
            bad.append(f"{d['key']}: 판정 '{v}' 는 어휘 밖 — {VERDICTS}")
            continue
        if v == "채움" and any(x.get("guard") for x in by_key.get(r["key"], [r])):
            g = sorted({h for x in by_key.get(r["key"], [r]) for h in (x.get("guard") or [])})
            why = guard_reason_problem(d.get("reason"), " ".join(str(x.get("context") or "") for x in by_key.get(r["key"], [r])))
            if why:
                bad.append(f"{d['key']}: 경계·선례 문구가 붙은 후보({'; '.join(g)[:60]})를 채우려면 {why}(아니면 제외·보류)")
                continue
            guard_reasons[(d.get("reason") or "").strip()] += 1
        if v == "채움":
            val, basis = d.get("value"), (d.get("basis") or "").strip()
            if empty(val):
                bad.append(f"{d['key']}: 채움인데 값이 비었다")
                continue
            if not basis:
                bad.append(f"{d['key']}: 채움인데 근거가 없다 — 산문 인용 또는 `담당자: …`")
                continue
            if basis.startswith("재료 "):
                # derive 가 결정적으로 뽑은 근거만 이 접두를 쓸 수 있다 — 인용 대조를 우회하는 통로가 되면 안 된다.
                if basis not in {x.get("derived_basis") for x in by_key.get(r["key"], [r])}:
                    bad.append(f"{d['key']}: `재료 …` 근거는 derive 가 준비한 것과 같아야 한다({r.get('derived_basis')!r})")
                    continue
            elif basis.startswith("코드:"):
                # 재료 D — 근거가 산문이 아니라 레포 코드다. 「코드: 경로:줄 — 조각」(여럿은 ` … `).
                # 파일·줄이 실재하고 그 줄 ±3 안에 조각이 글자 그대로 있어야 한다 — 지어낸 경로·심볼을 막는다.
                why = code_basis_problem(basis, wl.get("repo_root"))
                if why:
                    bad.append(f"{d['key']}: 코드 근거 — {why}")
                    continue
            elif basis.startswith("담당자:"):
                if not from_answers:
                    bad.append(f"{d['key']}: `담당자:` 근거는 담당자 답변 파일(answers 명령 출력)에서만 쓸 수 있다 — "
                               "판정에서는 원문을 글자 그대로 인용하라(담당자 문자열 승격이면 기존 문자열 그대로)")
                    continue
            else:
                data = load(snap / f"{r['item_id']}.json").get("item", {}).get("data") or {}
                quotes = [q for q in re.split(r"\s*…\s*|\s*\|\s*", basis) if q.strip()]
                ptxt = norm(prose_text(data, STRUCT_KEYS if r["field"] == "evidence" else None))
                miss = [q for q in quotes if norm(q) not in ptxt]
                if miss:
                    bad.append(f"{d['key']}: 근거 인용이 산문에 없다 → {miss[0][:80]!r} (지어낸 값은 채움이 아니라 안내다)")
                    continue
            if r["field"] == "evidence":
                # Phase 2 의 evidence 도 Phase 3.6 과 같은 규칙(references/evidence-judging.md) — CatchAll 실측:
                # 17칸 전부 reference 에 「테스트로 각 흐름 검증(…). test SUCCEEDED.」 같은 설명문이 들어갔다.
                pro = norm(prose_text(load(snap / f"{r['item_id']}.json").get("item", {}).get("data") or {}, STRUCT_KEYS))
                ev_bad = evidence_value_problems(val, pro)
                if ev_bad:
                    bad.append(f"{d['key']}: evidence — {ev_bad} (지침: references/evidence-judging.md)")
                    continue
                # result_quote 는 검사용 — 서버 스키마에 없는 키라 떼어 낸다. 날짜는 시간대 붙인 ISO 로.
                d["value"] = [{k: (norm_dt(x) if k in ("captured_at", "voided_at") else x) for k, x in ev.items()
                               if k != "result_quote"} for ev in val]
            if r["kind"] == "담당자":
                # CO-175 — 담당이 여럿이면 배열(원소마다 duty·최종 책임 lead 최대 하나). 서버가 이 모양을 모르면
                # 적용에서 거부된다(배포 전 서버) — 그때는 보류로 돌린다.
                one = lambda o: isinstance(o, dict) and o.get("kind") in OWNER_KINDS and isinstance(o.get("name"), str) and o["name"]  # noqa: E731
                if isinstance(val, list):
                    if not val or len(val) > 20 or not all(one(o) for o in val):
                        bad.append(f"{d['key']}: 담당자 배열 원소는 전부 {{kind, name}} 객체여야 한다(1~20개)")
                        continue
                    if sum(1 for o in val if o.get("lead") is True) > 1:
                        bad.append(f"{d['key']}: 최종 책임자(lead: true)는 최대 하나다")
                        continue
                elif not one(val):
                    bad.append(f"{d['key']}: 담당자는 {{kind, name}} 객체 또는 그 배열이어야 한다")
                    continue
        elif not (d.get("reason") or "").strip():
            bad.append(f"{d['key']}: '{v}' 는 사유가 필수다")
            continue
        if v == "해당 없음" and r["field"] in ("evidence", "verified_at", "verified_by") and not from_answers:
            st = item_status_now(snap, r["item_id"])
            if st in ("planned", "in_progress", "draft"):
                bad.append(f"{d['key']}: 항목이 아직 {st} — 검증 칸은 «해당 없음» 이 아니라 «보류»(구현이 끝나면 다시 판정된다)")
                continue
        for rr in by_key.get(r["key"], [r]):
            rr.update(verdict=v, value=d.get("value") if v == "채움" else None,
                      basis=d.get("basis", ""), reason=d.get("reason", ""), optional=bool(d.get("optional")),
                      batch=d.get("batch") or Path(a.input).stem)
    bad += [f"같은 사유가 가드 행 {n}건에 반복 — 행마다 그 문장을 인용해 따로 판정하라: {t[:60]!r}"
            for t, n in guard_reasons.items() if n >= 5]
    if bad:
        die("반영 거부 — 아무것도 쓰지 않았다:\n   " + "\n   ".join(bad[:20]))
    dump(a.worklist, wl)
    if a.ledger:
        led = load(a.ledger) if Path(a.ledger).exists() else {}
        for r in wl["rows"]:
            if r["verdict"] in ("해당 없음", "보류", "안내", "제외"):
                led[r["key"]] = {"verdict": r["verdict"], "reason": r["reason"]}
                st = item_status_now(snap, r["item_id"]) if r["verdict"] == "보류" else None
                if st:
                    led[r["key"]]["status_at"] = st  # 상태가 바뀌면 ledger_skip 이 다시 연다
        dump(a.ledger, led)
    c = Counter(r["verdict"] or "(미판정)" for r in wl["rows"])
    print("✅ 반영 · " + " · ".join(f"{k} {c[k]}" for k in [*VERDICTS, "(미판정)"] if c[k]))


# ── 재료 D — 코드 근거 (구현 사실 칸) ──────────────────────────────────────────
# 코드가 진실원인 «구현 사실» 칸. 설계 의도 칸(based_on_adrs·implements_requirements 등)은 코드에 없으니 여기 넣지 않는다.
CODE_FACT_FIELDS = {
    "api_endpoint": ["operates_on", "required_roles"],
    "service_interface": ["operates_on"],
    "domain_feature": ["operates_on", "required_roles"],
    # 구현 가이드라인은 «코드가 그 규칙을 실제로 지키는가»로 확인된다(상용 Self: GUIDE-001 응답 가드 → 웹 모듈).
    "code_module": ["follows_guidelines"],
}
CODE_FRAG = re.compile(r"^\s*(?P<path>[^\s:][^:]*?):(?P<line>\d+)\s*(?:[—–-]+\s*)?(?P<snip>.+?)\s*$")


def code_basis_problem(basis: str, repo_root) -> str:
    if not repo_root:
        return "작업표에 repo_root 가 없다 — code-worklist 로 만든 작업표에서만 `코드:` 근거를 쓸 수 있다"
    root = Path(repo_root).resolve()
    # 조각마다 「코드:」 를 다시 붙여 쓰는 형태(`코드: A … 코드: B`)도 받는다 — 지침 예시가 그 모양이다.
    frags = [re.sub(r"^\s*코드:\s*", "", f) for f in re.split(r"\s*…\s*", basis[len("코드:"):]) if f.strip()]
    if not frags:
        return "`코드: 경로:줄 — 조각` 이 비었다"
    for f in frags:
        m = CODE_FRAG.match(f)
        if not m:
            return f"형식이 `경로:줄 — 조각` 이 아니다 → {f[:80]!r}"
        path = (root / m["path"].strip()).resolve()
        if root not in path.parents or not path.is_file():
            return f"파일이 레포에 없다 → {m['path']!r}"
        lines = path.read_text(encoding="utf-8", errors="replace").split("\n")
        n = int(m["line"])
        if not 1 <= n <= len(lines):
            return f"줄 번호가 파일 범위 밖이다 → {m['path']}:{n} (총 {len(lines)}줄)"
        snip = norm(m["snip"])
        if len(snip) < 3:
            return f"조각이 너무 짧다 → {m['snip']!r}"
        window = norm("\n".join(lines[max(0, n - 4): n + 3]))
        if snip not in window:
            return f"{m['path']}:{n} 근처(±3줄)에 조각이 없다 → {m['snip'][:60]!r} (지어낸 근거는 채움이 아니라 안내다)"
    return ""


def cmd_code_worklist(a) -> None:
    dg = load(a.diagnose)
    repo = Path(a.repo).resolve()
    if not (repo / ".git").exists():
        die(f"--repo 가 git 레포가 아니다: {repo}")
    types = set(a.type.split(",")) if a.type else set(CODE_FACT_FIELDS)
    snapdir = Path(a.diagnose).parent / "snap"
    na = ledger_skip(a.ledger, getattr(a, "recheck", False), snapdir)
    out = []
    for r in dg["rows"]:
        if r["type"] not in types or r["field"] not in CODE_FACT_FIELDS.get(r["type"], []):
            continue
        if r["state"] != "빈칸" or r["key"] in na or r["status"] in pm.RETIRED:
            continue
        item = load(snapdir / f"{r['item_id']}.json").get("item", {})
        data = item.get("data") or {}
        impl = data.get("implementation") or {}
        hint = {"title": item.get("title"), "method": data.get("method"), "path": data.get("path"),
                "file_path": data.get("file_path"), "kind": data.get("kind"),
                "module_paths": impl.get("module_paths") or [], "modules": impl.get("modules") or []}
        meta = dg["schemas"][r["type"]][r["field"]]
        out.append({"key": r["key"], "item_id": r["item_id"], "type": r["type"], "title": r["title"],
                    "field": r["field"], "kind": r["kind"], "state": r["state"], "source": "D",
                    "field_help": meta["description"], "field_notes": meta["notes"],
                    "field_schema": json.dumps(meta.get("schema"), ensure_ascii=False)[:1500],
                    "code_hints": {k: v for k, v in hint.items() if v},
                    "verdict": "", "value": None, "basis": "", "reason": ""})
    if a.limit:
        out = out[: a.limit]
    dump(a.out, {"server": dg["server"], "project_id": dg["project_id"], "snapshot_dir": str(snapdir),
                 "repo_root": str(repo), "rows": out})
    c = Counter((r["type"], r["field"]) for r in out)
    print(f"✅ 코드 작업표 {len(out)}칸 (repo {repo}) → {a.out}")
    for (t, f), n in c.most_common(20):
        print(f"   {t}.{f:<22} {n}")


# ── 재료 E — 관계 초안 (Phase 1.8 · 근거 없는 설계 의도 관계) ─────────────────────
# 산문에도 코드에도 적혀 있지 않은 관계(이 화면이 어느 결정을 따르나 · 어느 요구를 구현하나)는 재료 A~D 로는
# 영영 안 채워진다(상용 Self 실측: 연결 칸이 전부 빈 항목 1,218/1,524). 여기서는 AI 가 «제안»만 한다.
#   ☠️ 제안은 적용 대상이 아니다 — 사람이 줄마다 「채택」한 것만 relation-plan 이 계획으로 만든다.
#   ☠️ 후보는 «실재하는 항목»에서만 뽑는다 — 판정자가 ID 를 지어낼 통로를 두지 않는다.
ALL_TYPES = ["rfp_item", "requirement", "feature", "acceptance", "adr", "glossary", "diagram_c4_context",
             "diagram_c4_container", "diagram_c4_component", "diagram_deployment", "class_diagram", "diagram_sequence",
             "diagram_state", "domain", "erd", "api_endpoint", "domain_feature", "domain_event", "use_case", "nfr", "risk",
             "screen_spec", "screen_design", "permission_role", "infra_component", "migration_plan", "slo", "runbook",
             "incident", "postmortem", "monitor_alert", "prompt_template", "model_usage", "guardrail", "ai_eval",
             "ai_dataset", "ai_policy", "code_module", "constant", "navigation_tree", "app_shell", "legacy_artifact",
             "implementation_record", "implementation_guideline", "design_system", "ui_component", "external_system",
             "integration_point", "integration_spec", "scenario_sketch", "test_scenario", "data_pipeline",
             "service_interface", "library_api", "permission_manifest", "settings_schema", "module_api",
             "oss_dependency", "deployment_spec", "network_rule", "repo", "meeting"]
REL_VERDICTS = ["제안", "아님", "보류"]
ID_RE = re.compile(r"\b([A-Z][A-Z0-9]*)-(\d+)\b")
STOP = set("""설계 기능 항목 관리 화면 목록 추가 수정 조회 처리 사용 경우 위한 대한 있는 없는 데이터 정보 내용 기반 지원
제공 확인 표시 선택 입력 저장 삭제 생성 등록 변경 결과 방식 구조 단계 필요 가능 기본 전체 이상 이하 이후 이전 모든 각각
그리고 또는 에서 으로 하는 한다 된다 있다 없다 the and for with from api item data""".split())


def field_ref_prefix(meta: dict):
    """연결 칸 스키마에서 대상 ID 접두와 배열 여부를 읽는다 — 목록을 손으로 들고 다니지 않는다."""
    prop = meta.get("schema") or {}
    arr = prop.get("type") == "array"
    for node in (prop, prop.get("items") or {}, *(prop.get("oneOf") or []), *(prop.get("anyOf") or [])):
        if isinstance(node, dict) and isinstance(node.get("pattern"), str):
            m = REF_RE.search(node["pattern"])
            if m:
                return m.group(1), arr
    return None, arr


def ref_ids(data) -> set:
    return {f"{m.group(1)}-{m.group(2)}" for m in ID_RE.finditer(prose_text(data) if isinstance(data, dict) else str(data))}


def concept_tokens(title: str, data: dict) -> set:
    txt = (title or "") + " " + " ".join(str(data.get(k) or "")[:600] for k in ("description", "summary", "purpose", "context"))
    txt = ID_RE.sub(" ", txt)
    toks = {t.lower() for t in re.findall(r"[가-힣]{2,}|[A-Za-z_][A-Za-z0-9_]{2,}", txt)}
    # 한국어 조사 떼기(가볍게) — 「화면을」「화면」을 같은 말로
    toks = {re.sub(r"(을|를|이|가|은|는|의|에|로|으로|과|와|도|만|에서|까지)$", "", t) if re.match(r"[가-힣]", t) else t
            for t in toks}
    return {t for t in toks if len(t) >= 2 and t not in STOP}


def excerpt(it: dict, n=220) -> str:
    d = it.get("data") or {}
    for k in ("description", "summary", "purpose", "context", "decision"):
        v = d.get(k)
        if isinstance(v, str) and v.strip():
            return norm(v)[:n]
    return norm(prose_text(d))[:n]  # description 이 없는 타입(수용기준의 given/when/then 등)은 글자 칸 전부에서


def load_pool(a, dg, prefixes: set, must: "set | None" = None) -> dict:
    """후보 풀 = 진단 스냅샷 + (없는 접두면) 서버에서 그 타입만 받아 캐시. {id: item}"""
    snap = Path(a.diagnose).parent / "snap"
    pool_dir = Path(a.pool_dir) if a.pool_dir else Path(a.diagnose).parent / "pool"
    items = {}
    for d in (snap, pool_dir):
        if d.exists():
            for p in d.glob("*.json"):
                it = load(p).get("item", {})
                if it.get("id"):
                    items[it["id"]] = it
    have = {i.split("-")[0] for i in items}
    missing = prefixes - have
    if missing and a.server:
        srv = server(a.server)
        pool_dir.mkdir(parents=True, exist_ok=True)
        typemap_p = pool_dir / "_prefix-types.json"
        typemap = load(typemap_p) if typemap_p.exists() else {}
        todo = [t for t in ALL_TYPES if t not in typemap.values()] if any(m not in typemap for m in missing) else []
        for t in todo:  # 접두 → 타입 표를 한 번만 만든다(list_items 는 type 이 필수다)
            try:
                r = mcp(srv, "list_items", {"project_id": dg["project_id"], "type": t, "limit": 1})
            except RuntimeError:
                continue
            for i in r.get("items") or []:
                typemap[i["id"].split("-")[0]] = t
            typemap.setdefault(f"_seen:{t}", t)
        dump(typemap_p, typemap)
        ignored = []
        for pre in sorted(missing):
            t = typemap.get(pre)
            if not t:
                # 칸이 받는 접두(must)만 경고 — 다리 접두는 산문 속 항목 아닌 토큰(CAM003-·KEPCO-·CO-)이 섞여 소음이 된다
                if must is None or pre in must:
                    print(f"   ⚠️ 접두 {pre}- 인 항목이 이 프로젝트에 없다 — 후보 풀 없음")
                else:
                    ignored.append(pre)
                continue
            off, n = 0, 0
            while True:
                r = mcp(srv, "list_items", {"project_id": dg["project_id"], "type": t, "limit": 500, "offset": off})
                for i in r.get("items") or []:
                    p = pool_dir / f"{i['id']}.json"
                    if not p.exists():
                        p.write_text(json.dumps(mcp(srv, "get_item", {"project_id": dg["project_id"], "id": i["id"]}),
                                                ensure_ascii=False, indent=1), encoding="utf-8")
                    items[i["id"]] = load(p).get("item", {})
                    n += 1
                pg = r.get("pagination") or {}
                if not pg.get("has_more"):
                    break
                off = pg["next_offset"]
            print(f"   후보 풀 보충: {pre}- ({t}) {n}건 → {pool_dir}")
    elif missing:
        print(f"   ⚠️ 스냅샷에 없는 대상 접두 {sorted(missing)} — --server 를 주면 받아 온다(주지 않으면 그 칸은 후보 0)")
    if 'ignored' in locals() and ignored:
        print(f"   (항목이 아닌 다리 접두 {len(ignored)}종 무시: {', '.join(p + '-' for p in ignored[:8])}{' …' if len(ignored) > 8 else ''})")
    return items


def cmd_relation_cands(a) -> None:
    dg = load(a.diagnose)
    types = set(a.type.split(",")) if a.type else None
    fields = set(a.field.split(",")) if a.field else None
    ledger = load(a.ledger) if a.ledger and Path(a.ledger).exists() else {}
    # 같은 라운드의 L·C·D·S 가 이미 채우기로 정한 칸은 뺀다(KLID 상용 2026-10-02: 후보 칸 2,780 중 301칸 낭비)
    same_round = set()
    if getattr(a, "round_dir", None):
        R = Path(a.round_dir)
        if (R / "refs" / "decisions.json").exists():
            same_round |= {(r["item_id"], r["field"]) for r in load(R / "refs" / "decisions.json")["decisions"] if r.get("kind") == pm.MIGRATE}
        for sub in ("c", "code", "fields"):
            if (R / sub / "worklist.json").exists():
                same_round |= {(r["item_id"], r["field"]) for r in load(R / sub / "worklist.json")["rows"] if r.get("verdict") == "채움"}
    cells = []
    for r in dg["rows"]:
        if r["kind"] != "연결" or r["state"] != "빈칸" or r["status"] in pm.RETIRED:
            continue
        if (r["item_id"], r["field"]) in same_round:
            continue
        if (types and r["type"] not in types) or (fields and r["field"] not in fields):
            continue
        if ledger.get(r["key"], {}).get("verdict") == "해당 없음":
            continue
        if r["prose_ref"] and not a.include_prose:
            continue  # 산문에 ID 가 있다 — Phase 1 의 몫이다
        if r["field"] in CODE_FACT_FIELDS.get(r["type"], []) and not a.include_code_facts:
            continue  # 구현 사실 칸 — 코드가 있으면 Phase 1.7 의 몫이다
        pre, arr = field_ref_prefix(dg["schemas"][r["type"]][r["field"]])
        if pre:
            cells.append((r, pre, arr))
    cell_pre = {pre for _, pre, _ in cells}
    items = load_pool(a, dg, cell_pre, must=cell_pre)
    # 다리 항목도 풀에 넣는다 — 설계 연결은 흔히 DFEAT→FEAT→REQ 처럼 스냅샷에 없는 타입(FEAT 등)을 거친다.
    #   빠지면 그래프 경로가 끊겨 «낱말 겹침»만 남는다(상용 Self 시험: SCREEN 후보가 전부 흔한 낱말로 뽑혔다).
    bridge = {x.split("-")[0] for r, _, _ in cells if r["item_id"] in items
              for x in ref_ids(items[r["item_id"]].get("data") or {})}
    if bridge - {i.split("-")[0] for i in items}:
        items = load_pool(a, dg, bridge | cell_pre, must=cell_pre)
    live = {i: it for i, it in items.items() if it.get("status") not in pm.RETIRED}
    live_set = set(live)  # 루프 안에서 set(live) 를 매번 만들면 칸×이웃×이웃 만큼 재생성된다(KLID 3,776항목: 30분+ → 한 번만)
    refs = {i: ref_ids(it.get("data") or {}) - {i} for i, it in live.items()}
    rev: "dict[str, set]" = {}
    for i, rs in refs.items():
        for x in rs:
            rev.setdefault(x, set()).add(i)
    toks = {i: concept_tokens(it.get("title", ""), it.get("data") or {}) for i, it in live.items()}
    df = Counter(t for ts in toks.values() for t in ts)
    N = max(1, len(toks))
    import math
    idf = {t: math.log(N / (1 + c)) for t, c in df.items()}
    rare = {t for t, c in df.items() if c <= max(3, N * 0.02)}  # 흔한 말(사용자·프로젝트·필터…)은 신호가 아니다
    deg = {i: len(refs.get(i, set())) + len(rev.get(i, set())) for i in live}
    rev_type_n: "dict[str, Counter]" = {n: Counter(live[x].get("type") for x in xs if x in live) for n, xs in rev.items()}
    dom = {i: (it.get("domain_id") or (it.get("data") or {}).get("domain_id")) for i, it in live.items()}
    out = []
    for r, pre, arr in cells:
        me = r["item_id"]
        if me not in live:
            continue
        # 경유지는 «실재 항목»만 — CO 번호·해시처럼 항목이 아닌 번호를 거친 경로는 설계 관계가 아니다(같은 CO 에 적혔을 뿐).
        near = {n for n in refs.get(me, set()) | rev.get(me, set()) if n in live}
        sc: "dict[str, dict]" = {}

        def hit(c, why, w):
            if c == me or c not in live or not c.startswith(pre + "-"):
                return
            if f"{r['key']}|{c}" in ledger:  # 이미 기각·아님 — 다시 제안하지 않는다
                return
            e = sc.setdefault(c, {"score": 0.0, "signals": []})
            e["score"] += w
            if why not in e["signals"]:
                e["signals"].append(why)
        # 가중치: 그래프 경로 > 같은 도메인 > 드문 낱말 겹침. 낱말 겹침만으로는 후보 기준(MIN_SCORE)을 겨우 넘게 둔다.
        for c in refs.get(me, set()):
            hit(c, "직접 언급(산문 밖 칸)", 6)
        for c in rev.get(me, set()):
            hit(c, "상대가 이 항목을 언급", 5)
        # 허브(수십 곳이 가리키는 항목)를 거친 경로는 약하게 — 안 그러면 허브의 이웃이 모든 항목의 후보가 된다
        #   (상용 Self 시험: ADR-025 를 거쳐 REQ-012 가 아티팩트·공지 화면 모두의 1순위 후보로 떴다).
        # 경유지 감쇠 — 상용 Self 시범(rel-1)에서 기각된 고득점 후보 3유형을 낮춘다:
        #   ① 허브(수십 곳이 가리키는 항목) — 허브의 이웃이 모든 항목의 후보가 된다
        #   ② 대상과 같은 타입의 경유지(ADR→ADR·REQ→REQ) — 정답 ADR 이 선례로 인용한 ADR·같은 허브 ADR 의 다른 자식이 딸려 온다
        #   ③ 같은 타입 형제가 함께 쓰는 경유지(여러 화면이 공유하는 API) — 한 화면의 결정이 형제 화면에 옮겨 붙는다
        my_type = live[me].get("type")

        hub_memo: "dict[str, float]" = {}

        def hub(n):
            if n in hub_memo:
                return hub_memo[n]
            w = min(1.0, 8 / max(1, deg.get(n, 0)))
            if n.startswith(pre + "-"):
                w *= 0.3
            # 형제 수 = n 을 가리키는 같은 타입 항목 수(자기 제외) — 타입별 개수를 미리 세 둔 표로(매 호출 전수 순회는 칸당 수 초)
            sib = rev_type_n.get(n, {}).get(my_type, 0) - (1 if me in rev.get(n, ()) else 0)
            hub_memo[n] = w / (1 + sib)
            return hub_memo[n]
        hop2: "dict[str, dict]" = {}
        for n in near:
            for c in (refs.get(n, set()) | rev.get(n, set())) & live_set:
                hop2.setdefault(c, {})[n] = hub(n)
        for c, via in hop2.items():
            names = sorted(via, key=lambda n: -via[n])[:3]
            hit(c, "그래프 2홉(" + "·".join(names) + " 경유)", min(3 * sum(via.values()), 9))
        hop3: "dict[str, dict]" = {}
        for n in near:
            for m in (refs.get(n, set()) | rev.get(n, set())) & live_set:
                if m == me or m in near:
                    continue
                for c in (refs.get(m, set()) | rev.get(m, set())) & live_set:
                    if c not in hop2:
                        hop3.setdefault(c, {})[f"{n}→{m}"] = hub(n) * hub(m)
        for c, via in hop3.items():
            best = max(via, key=via.get)
            hit(c, f"그래프 3홉({best} 경유)", min(sum(via.values()), 2))
        if dom.get(me):
            for c, dm in dom.items():
                if dm == dom[me]:
                    hit(c, "같은 도메인", 0.5)
        mine = toks.get(me, set()) & rare
        for c in [x for x in live if x.startswith(pre + "-")]:
            shared = mine & toks.get(c, set())
            if len(shared) >= 2:
                w = sum(idf.get(t, 0) for t in shared)
                top = sorted(shared, key=lambda t: -idf.get(t, 0))[:4]
                hit(c, "드문 낱말 겹침(" + "·".join(top) + ")", min(w / 6, 2))
        sc = {c: v for c, v in sc.items() if v["score"] >= a.min_score}
        ranked = sorted(sc.items(), key=lambda kv: -kv[1]["score"])[: a.top]
        if ranked:  # 1위의 rel_cutoff 배 미만은 버린다 — rel-1 시뮬레이션: 0.5 까지 정답 손실 0, 오답 56→49
            ranked = [kv for kv in ranked if kv[1]["score"] >= a.rel_cutoff * ranked[0][1]["score"]]
        if not ranked:
            continue
        it = live[me]
        out.append({"key": r["key"], "item_id": me, "type": r["type"], "title": r["title"], "field": r["field"],
                    "target_prefix": pre, "array": arr,
                    "field_help": dg["schemas"][r["type"]][r["field"]]["description"],
                    "item_excerpt": excerpt(it, 400),
                    "candidates": [{"id": c, "title": live[c].get("title", ""), "type": live[c].get("type"),
                                    "score": round(v["score"], 2), "signals": v["signals"][:4],
                                    "excerpt": excerpt(live[c])} for c, v in ranked],
                    "judged": {}})
        if a.limit and len(out) >= a.limit:
            break
    dump(a.out, {"server": dg["server"], "project_id": dg["project_id"],
                 "snapshot_dir": str(Path(a.diagnose).parent / "snap"),
                 "pool_ids": sorted(live), "rows": out})
    c = Counter((r["type"], r["field"]) for r in out)
    print(f"✅ 관계 후보 — 칸 {len(out)} · 후보 {sum(len(r['candidates']) for r in out)} → {a.out}")
    for (t, f), n in c.most_common(15):
        print(f"   {t}.{f:<26} {n}")


def cmd_relation_fill(a) -> None:
    wl = load(a.worklist)
    idx = {r["key"]: r for r in wl["rows"]}
    pool = set(wl.get("pool_ids") or [])
    bad, n = [], 0
    for d in load(a.input):
        r = idx.get(d.get("key"))
        tgt, v, why = d.get("target"), d.get("verdict"), (d.get("reason") or "").strip()
        if not r:
            bad.append(f"없는 key: {d.get('key')}")
            continue
        if v not in REL_VERDICTS:
            bad.append(f"{d['key']} {tgt}: 판정 '{v}' 는 어휘 밖 — {REL_VERDICTS}")
            continue
        if not (isinstance(tgt, str) and tgt.startswith(r["target_prefix"] + "-")):
            bad.append(f"{d['key']}: 대상 {tgt!r} 은 이 칸이 받는 {r['target_prefix']}- 가 아니다")
            continue
        if tgt not in pool:
            bad.append(f"{d['key']}: 대상 {tgt} 는 프로젝트에 없는(또는 폐기된) 항목이다 — 지어낸 ID")
            continue
        if len(why) < 10:
            bad.append(f"{d['key']} {tgt}: 사유가 없거나 너무 짧다 — 무엇이 무엇에 기대는지 한두 문장")
            continue
        outside = tgt not in {c["id"] for c in r["candidates"]}
        r["judged"][tgt] = {"verdict": v, "reason": why, "outside": outside}
        n += 1
    bad += [f"같은 사유가 가드 행 {n}건에 반복 — 행마다 그 문장을 인용해 따로 판정하라: {t[:60]!r}"
            for t, n in guard_reasons.items() if n >= 5]
    if bad:
        die("반영 거부 — 아무것도 쓰지 않았다:\n   " + "\n   ".join(bad[:20]))
    dump(a.worklist, wl)
    c = Counter(j["verdict"] for r in wl["rows"] for j in r["judged"].values())
    left = sum(1 for r in wl["rows"] if not r["judged"])
    print(f"✅ 반영 {n} · " + " · ".join(f"{k} {c[k]}" for k in REL_VERDICTS if c[k]) + f" · 판정 없는 칸 {left}")


def cmd_relation_review(a) -> None:
    wl = load(a.worklist)
    rows = [r for r in wl["rows"] if any(j["verdict"] == "제안" for j in r["judged"].values())]
    hold = [(r, t, j) for r in wl["rows"] for t, j in r["judged"].items() if j["verdict"] == "보류"]
    nope = sum(1 for r in wl["rows"] for j in r["judged"].values() if j["verdict"] == "아님")
    title = {c["id"]: c["title"] for r in wl["rows"] for c in r["candidates"]}
    L = ["# 관계 초안 — 검토표", "",
         f"제안 **{sum(1 for r in rows for j in r['judged'].values() if j['verdict'] == '제안')}줄** "
         f"(항목·칸 {len(rows)}) · 보류 {len(hold)} · AI 가 아니라고 본 후보 {nope}", "",
         "> 이 관계들은 **산문에도 코드에도 적혀 있지 않다.** AI 가 두 항목을 읽고 «관련 있어 보인다»고 제안한 것이다.",
         "> 줄마다 **채택/기각**을 정해 `decisions.json` 에 적는다(비워 둔 줄은 이번에 적용하지 않고 다음에 다시 나온다).",
         "> 판단 질문: **「오른쪽 항목이 내일 바뀌면, 왼쪽 항목을 다시 열어 봐야 하나?」** — 예면 채택.", ""]
    dec = []
    for r in rows:
        L += [f"## {r['item_id']} — {r['title'][:60]} · `{r['field']}`", "",
              f"- 칸 뜻: {r['field_help'][:200]}", f"- 이 항목: {r['item_excerpt'][:200]}", ""]
        for t, j in r["judged"].items():
            if j["verdict"] != "제안":
                continue
            L.append(f"- [ ] **{t}** {title.get(t, '')[:60]}{' _(후보 목록 밖)_' if j.get('outside') else ''} — {j['reason']}")
            dec.append({"key": r["key"], "target": t, "item": r["item_id"], "field": r["field"], "decision": "", "note": ""})
        L.append("")
    if hold:
        L += ["## 보류 — AI 가 판단하지 못한 후보 (보고 싶으면)", ""]
        L += [f"- {r['item_id']} `{r['field']}` → {t} — {j['reason']}" for r, t, j in hold]
        L.append("")
    Path(a.out).write_text("\n".join(L) + "\n", encoding="utf-8")
    dump(a.decisions, dec)
    print(f"✅ 검토표 → {a.out} · 결정 양식 {len(dec)}줄 → {a.decisions}  (decision: 채택 | 기각 | 비움)")


def cmd_relation_plan(a) -> None:
    wl = load(a.worklist)
    idx = {r["key"]: r for r in wl["rows"]}
    led = load(a.ledger) if a.ledger and Path(a.ledger).exists() else {}
    adopt: "OrderedDict[str, list]" = OrderedDict()
    bad, nrej = [], 0
    for d in load(a.decisions):
        dec = (d.get("decision") or "").strip()
        r = idx.get(d.get("key"))
        if not dec:
            continue
        if not r or d.get("target") not in r["judged"]:
            bad.append(f"검토표에 없는 줄: {d.get('key')} → {d.get('target')}")
            continue
        if dec == "채택":
            adopt.setdefault(r["key"], []).append(d["target"])
        elif dec == "기각":
            led[f"{r['key']}|{d['target']}"] = {"verdict": "기각", "reason": d.get("note") or "관계 초안 기각(담당자)"}
            nrej += 1
        else:
            bad.append(f"{r['key']} → {d['target']}: decision '{dec}' 는 채택·기각·비움만")
    for key, tg in adopt.items():
        if not idx[key]["array"] and len(tg) > 1:
            bad.append(f"{key}: 값 하나만 받는 칸인데 {len(tg)}개를 채택했다 → {tg}")
    if bad:
        die("계획 거부 — 아무것도 쓰지 않았다:\n   " + "\n   ".join(bad[:20]))
    # AI 가 «아님»으로 본 후보도 장부에 남긴다 — 다음 라운드에 같은 후보를 다시 판정하지 않게.
    for r in wl["rows"]:
        for t, j in r["judged"].items():
            if j["verdict"] == "아님":
                led.setdefault(f"{r['key']}|{t}", {"verdict": "아님", "reason": j["reason"]})
    if a.ledger:
        dump(a.ledger, led)
    rows = []
    for key, tg in adopt.items():
        r = idx[key]
        reasons = "; ".join(f"{t}: {r['judged'][t]['reason']}" for t in tg)
        rows.append({"key": key, "item_id": r["item_id"], "type": r["type"], "field": r["field"], "kind": "연결",
                     "verdict": "채움", "value": tg if r["array"] else tg[0],
                     "basis": f"담당자 확정: 관계 초안 채택 — {reasons}"[:1000], "reason": ""})
    fw = Path(a.out).with_name("adopted-worklist.json")
    dump(fw, {"server": wl["server"], "project_id": wl["project_id"], "snapshot_dir": wl["snapshot_dir"],
              "source": "relation", "rows": rows})
    print(f"   채택 {sum(len(v) for v in adopt.values())}줄(칸 {len(adopt)}) · 기각 {nrej}줄 → 장부")
    cmd_plan_fields(argparse.Namespace(worklist=str(fw), out=a.out, partial=False))


# ── auto-na — 칸 설명·프로젝트 상태만으로 «해당 없음»이 확정되는 칸 (판정 없이) ─────────────
# 사람·AI 판정에 올릴 필요가 없는 빈칸을 먼저 걷어 낸다. 서버에는 쓰지 않고 장부에만 남긴다.
#   R1 대상 타입 항목이 프로젝트에 0개 — 가리킬 것이 없다(예: 가이드라인 0개인 프로젝트의 follows_guidelines)
#   R2 code_module.repo_ref — 레포(REPO) 항목이 1개 이하면 칸 설명 그대로 «단일 레포면 비워 둔다»(CO-141)
def cmd_auto_na(a) -> None:
    dg = load(a.diagnose)
    ledger = load(a.ledger) if a.ledger and Path(a.ledger).exists() else {}
    cells = []
    for r in dg["rows"]:
        if r["kind"] != "연결" or r["state"] != "빈칸" or r["status"] in pm.RETIRED or r["key"] in ledger:
            continue
        pre, _ = field_ref_prefix(dg["schemas"][r["type"]][r["field"]])
        if pre:
            cells.append((r, pre))
    items = load_pool(a, dg, {pre for _, pre in cells} | {"REPO"})
    have = Counter(i.split("-")[0] for i, it in items.items() if it.get("status") not in pm.RETIRED)
    out = []
    for r, pre in cells:
        if r["type"] == "code_module" and r["field"] == "repo_ref" and have["REPO"] <= 1:
            out.append({"key": r["key"], "item": r["item_id"], "field": r["field"], "rule": "R2",
                        "why": f"레포 항목 {have['REPO']}개 — 칸 설명: 단일 레포면 비워 둔다(CO-141)"})
        elif have[pre] == 0:
            out.append({"key": r["key"], "item": r["item_id"], "field": r["field"], "rule": "R1",
                        "why": f"가리킬 대상({pre}-) 항목이 이 프로젝트에 0개"})
    dump(a.out, out)
    c = Counter((x["rule"], x["field"]) for x in out)
    print(f"✅ 자동 해당 없음 {len(out)}칸 → {a.out}")
    for (rule, f), n in c.most_common(15):
        print(f"   {rule} {f:<28} {n}")


# ── derive (재료 B · A — 결정적) ─────────────────────────────────────────────
# derive 가 읽는 «재료» 타입 — 새 칸이 없어도 스냅샷해야 한다(diagnose 가 함께 받는다).
DERIVE_SOURCES = ["adr", "permission_role", "incident", "postmortem", "migration_plan"]

INC_KIND = {"occurred": "occurred", "detected": "detected", "acknowledged": "acknowledged", "mitigation": "mitigated",
            "mitigated": "mitigated", "resolution": "resolved", "resolved": "resolved", "decision": "decision"}


def cmd_derive(a) -> None:
    """산문보다 먼저 쓰는 재료 — 같은/연결된 항목의 «구조 칸»(B)과 그래프 역방향(A).

    규칙은 전부 여기 명시한다. 규칙에 없는 짝은 쓰지 않는다 — 비슷해 보이는 짝이 실제로는
    다른 뜻인 경우가 있었다(IMPREC ← 설계 항목 implementation.records 74칸 = 전부 자기 design_item_id 중복).
      B1 migration_plan.steps   ← pre_steps · forward_ddl(+rollback_ddl) · post_steps 를 순서대로
      B2 incident.{started,acknowledged,mitigated}_at ← timeline 의 occurred/acknowledged/mitigation 항목 시각
         ☠️ detected 를 acknowledged 로 쓰지 않는다(탐지≠인지 — 칸 설명이 둘을 구분한다)
      B3 postmortem.timeline    ← incident_id 가 가리키는 사고의 timeline
      A1 api_endpoint.required_roles ← permission_role.permissions[target_kind=api_endpoint]   (강 — 바로 채움)
      A2 *.based_on_adrs        ← adr.references[item_id]   (중 — 「참조」≠「따름」이라 AI 판정 → 사람 확인)
    """
    dg = load(a.diagnose)
    snap = Path(a.diagnose).parent / "snap"
    items = {}
    for p in snap.glob("*.json"):
        it = load(p).get("item", {})
        if it.get("id"):
            items[it["id"]] = it
    live = lambda i: i.get("status") not in pm.RETIRED  # noqa: E731
    na = set()
    if a.ledger and Path(a.ledger).exists():
        na = {k for k, v in load(a.ledger).items() if v.get("verdict") in ("해당 없음", "보류")}
    empty_cells = {(r["item_id"], r["field"]): r for r in dg["rows"]
                   if r["state"] == "빈칸" and r["status"] not in pm.RETIRED and r["key"] not in na}
    rows = []

    ledger = load(a.ledger) if a.ledger and Path(a.ledger).exists() else {}

    def put(item_id, field, value, basis, source, verdict="채움", context="", cand="", guard=None):
        r = empty_cells.get((item_id, field))
        if not r:
            return
        key = f"{r['key']}|{cand}" if cand else r["key"]
        if key in ledger:  # 이미 판정한 후보(제외·보류 등)는 다시 묻지 않는다
            return
        dup = next((x for x in rows if x["key"] == key), None)
        if dup:  # 같은 후보를 다른 재료가 또 냈다 — 한 행으로 합치고 출처·문맥만 덧붙인다
            dup["source"] = dup["source"] + "+" + source
            dup["context"] = (dup.get("context") or "") + " ‖ " + (context or basis)
            if guard:
                dup["guard"] = sorted(set((dup.get("guard") or []) + guard))
            return
        meta = dg["schemas"][r["type"]][field]
        rows.append({"key": key, "item_id": item_id, "type": r["type"], "title": r["title"], "field": field,
                     "kind": r["kind"], "state": r["state"], "source": source,
                     "field_help": meta["description"], "field_notes": meta["notes"],
                     "field_schema": json.dumps(meta.get("schema"), ensure_ascii=False)[:1500],
                     "context": context, "derived_basis": basis, "guard": guard or None,
                     "verdict": verdict, "value": value if verdict == "채움" else None,
                     "basis": basis if verdict == "채움" else "", "reason": "",
                     "candidate": value})
    for it in filter(live, items.values()):
        d, t, iid = it.get("data") or {}, it.get("type"), it["id"]
        if t == "migration_plan":
            # ☠️ 옛 pre/post_steps 에는 단계와 «경고문»이 섞여 있다(실측 MIG-002: 「⚠️ 데이터가 영구 소멸된다」).
            #    경고는 단계가 아니다 — 옮기지 않는다(원래 칸에 그대로 남는다).
            is_step = lambda x: isinstance(x, str) and not x.lstrip().startswith(("⚠", "☠", "주의", "※"))  # noqa: E731
            steps = [{"title": s} for s in d.get("pre_steps") or [] if is_step(s)]
            if d.get("forward_ddl"):
                st = {"title": f"스키마 적용 (V{d.get('to_version')})" if d.get("to_version") else "스키마 적용",
                      "command": d["forward_ddl"][:1000]}
                if d.get("rollback_ddl"):
                    st["rollback"] = d["rollback_ddl"][:1000]
                steps.append(st)
            steps += [{"title": s} for s in d.get("post_steps") or [] if is_step(s)]
            if steps and all(len(s["title"]) <= 200 for s in steps):
                steps = [dict(order=n, **s) for n, s in enumerate(steps, 1)]
                src = "·".join(k for k in ("pre_steps", "forward_ddl", "post_steps") if d.get(k))
                put(iid, "steps", steps, f"재료 B: {iid}.{src}", "B")
        if t == "incident":
            for want, field in (("occurred", "started_at"), ("acknowledged", "acknowledged_at"),
                                ("mitigated", "mitigated_at")):
                hit = [e for e in d.get("timeline") or [] if INC_KIND.get(e.get("kind")) == want and e.get("at")]
                if hit:
                    put(iid, field, hit[0]["at"], f"재료 B: {iid}.timeline[{want}]", "B")
        if t == "postmortem" and d.get("incident_id") in items:
            tl = []
            for e in (items[d["incident_id"]].get("data") or {}).get("timeline") or []:
                if not e.get("at") or not (e.get("description") or e.get("what")):
                    continue
                x = {"at": e["at"], "what": (e.get("description") or e.get("what"))[:500]}
                x["kind"] = INC_KIND.get(e.get("kind"), "note")
                tl.append(x)
            if tl:
                put(iid, "timeline", tl, f"재료 B: {d['incident_id']}.timeline", "B")
    # 재료 A — 역방향
    rr, adr = {}, {}
    for it in filter(live, items.values()):
        d = it.get("data") or {}
        if it.get("type") == "permission_role":
            for pmn in d.get("permissions") or []:
                if isinstance(pmn, dict) and pmn.get("target_kind") == "api_endpoint" and pmn.get("target_id"):
                    rr.setdefault(pmn["target_id"], []).append(it["id"])
        if it.get("type") == "adr":
            for ref in d.get("references") or []:
                if isinstance(ref, dict) and ref.get("item_id"):
                    adr.setdefault(ref["item_id"], []).append(it["id"])
    for api, roles in rr.items():
        roles = sorted(set(roles))
        put(api, "required_roles", roles, f"재료 A: {'·'.join(roles)}.permissions", "A")
    for target, adrs in adr.items():
        if items.get(target, {}).get("type") == "adr":
            continue  # ADR 의 references 가 다른 ADR 을 가리키는 것은 «전제»가 아니다(관련 목록) — C2 가 산문으로 본다
        for aid in sorted(set(adrs)):
            ad = (items[aid].get("data") or {})
            ctx = f"{aid} 「{items[aid].get('title', '')}」 — references 에 {target} 가 있다."
            body = prose_text(ad)
            if target in body:
                i = body.find(target)
                ctx += f" 본문: …{body[max(0, i - 150): i + 150]}…"
            else:
                ctx += " ADR 본문에는 이 항목 언급이 없다."
            put(target, "based_on_adrs", [aid], f"재료 A: {aid}.references", "A", verdict="", context=ctx, cand=aid)
    # ── 재료 C — 산문이지만 «저장 경고 규칙이 보지 않는» 자리 (판정 필요 · 사람 확정) ─────────────
    #  C1 역방향 산문 — S 의 산문이 X 를 적었는데, 그 관계를 담는 칸은 «X 쪽»에 있다(X.F ∋ S).
    #     실측: 요구사항 rationale 「근거: DFEAT-002/004」 → DFEAT.implements_requirements. dev 41프로젝트 93건 전부 비어 있었다.
    #  C2 규칙 밖 산문 — X 자신의 산문이 P-id 를 적었는데 그 조합엔 산문 경고 규칙이 없다(scan_prose_refs 가 못 본다).
    #     예: ADR→ADR(adr.based_on_adrs) · 상수→상수(constant.uses_constants) · 사고→DFEAT/EXTSYS(incident.affects).
    #  C3 「영향 ITEM:」 명시 목록 → 같은 항목의 affects.
    #  ☠️ 전부 «판정 필요»로만 낸다 — 산문 언급의 상당수는 관계가 아니다(개요 표·경계·선례·다른 프로젝트 번호).
    if a.prose:
        scan_keys = set()
        if a.scan and Path(a.scan).exists():
            for f in load(a.scan)["findings"]:
                for ref in f["refs"]:
                    scan_keys.add((f["item_id"], f["field"], ref))
        PRO = ("description", "notes", "rationale", "summary", "context", "consequences", "decision", "impact",
               "mitigation", "tech_considerations")
        def prose_of(d):
            out = []
            def w(v, top):
                if isinstance(v, str):
                    if top in PRO:
                        out.append(v)
                elif isinstance(v, dict):
                    for x in v.values():
                        w(x, top)
                elif isinstance(v, list):
                    for x in v:
                        w(x, top)
            for k, v in d.items():
                w(v, k)
            return "\n".join(out)
        def ctx_of(text, ref, width=110):
            m = re.search(re.escape(ref) + r"(?!\d)", text)
            if not m:
                return ""
            return "…" + text[max(0, m.start() - width): m.end() + width].replace("\n", " ⏎ ") + "…"
        def ids_in(text):
            """ID 와 범위 표기를 펼친다 — 「DFEAT-020/021」·「API-031~045」(서버 판별기 CO-171 과 같은 취지).
            범위는 50개 이하만 펼친다(오탐 방지). 자릿수는 첫 번호를 따른다."""
            out = set(re.findall(r"\b[A-Z]+-\d+\b", text))
            for m in re.finditer(r"\b([A-Z]+)-(\d+)((?:/\d+)+)", text):
                w = len(m.group(2))
                for n in m.group(3).strip("/").split("/"):
                    out.add(f"{m.group(1)}-{n.zfill(w)}")
            for m in re.finditer(r"\b([A-Z]+)-(\d+)\s*[~∼～]\s*(?:\1-)?(\d+)\b", text):
                a0, b0 = int(m.group(2)), int(m.group(3)); w = len(m.group(2))
                if 0 < b0 - a0 <= 50:
                    out |= {f"{m.group(1)}-{str(k).zfill(w)}" for k in range(a0, b0 + 1)}
            return out
        def prefixes(schema):
            pats = []
            for node in (schema or {}, (schema or {}).get("items") or {}):
                if isinstance(node, dict) and isinstance(node.get("pattern"), str):
                    pats.append(node["pattern"])
            out = set()
            for pt in pats:
                m = re.match(r"^\^\(?([A-Z|]+)\)?-", pt)
                if m:
                    out |= set(m.group(1).split("|"))
            return out
        # 새 칸 중 «연결» 칸의 (타입, 칸) → 받는 접두사
        ptr = {}
        for t, fs in dg["schemas"].items():
            for f, meta in fs.items():
                if meta.get("kind") == "연결":
                    ptr[(t, f)] = prefixes(meta.get("schema"))
        pref_of = lambda i: i.split("-")[0]  # noqa: E731
        type_of_prefix = {}
        for it in items.values():
            type_of_prefix.setdefault(pref_of(it["id"]), it.get("type"))
        P = {i: prose_of(it.get("data") or {}) for i, it in items.items() if live(it)}
        man = load(MANIFEST)
        unruled = {(t, f) for t, fs in (man.get("unruled_pointer_fields") or {}).items() for f in fs}
        n1 = n2 = n3 = 0
        for sid, text in P.items():
            s_pref = pref_of(sid)
            for ref in sorted(ids_in(text)):
                if ref == sid or ref not in items or not live(items[ref]):
                    continue
                s_t, r_t = items[sid].get("type"), items[ref].get("type")
                # C2 — 내 칸이 그 접두사를 받는데 경고 규칙이 없는 조합
                for (t, f), pre in ptr.items():
                    if (t, f) not in unruled:
                        continue  # 경고 규칙이 있는 칸은 scan_prose_refs(재료 E)의 몫 — 겹치면 규칙이 일부러 건너뛴 것까지 되살린다
                    if t == s_t and pref_of(ref) in pre and (sid, f, ref) not in scan_keys:
                        before = (items[sid].get("data") or {}).get(f) or []
                        if ref not in before:
                            put(sid, f, [ref], f"재료 C2: {sid} 산문", "C2", verdict="",
                                context=f"{sid} 자신의 산문: {ctx_of(text, ref)}", cand=ref,
                                guard=pm.guard_signal(text, ref))
                            n2 += 1
                # C1 — 상대(ref) 쪽 칸이 내 접두사를 받는다
                for (t, f), pre in ptr.items():
                    # ☠️ 같은 타입끼리는 뒤집지 않는다(ADR X 가 ADR Y 를 적었다고 «Y 가 X 를 전제»가 아니다).
                    #    구현 기록 쪽 칸도 뒤집지 않는다(설계 산문이 IMPREC 를 가리키는 것은 추적 표기다).
                    if t == s_t or t == "implementation_record":
                        continue
                    if t == r_t and s_pref in pre:
                        before = (items[ref].get("data") or {}).get(f) or []
                        if sid not in before:
                            put(ref, f, [sid], f"재료 C1: {sid} 산문", "C1", verdict="",
                                context=f"{sid}({s_t}) 의 산문이 {ref} 를 적었다: {ctx_of(text, ref)}", cand=sid,
                                guard=pm.guard_signal(text, ref))
                            n1 += 1
            # C3 — 「영향 ITEM:」 목록 → 같은 항목의 affects
            for m in re.finditer(r"영향\s*(?:ITEM|항목)\s*[:：]\s*([^\n]+)", text):
                for ref in sorted(ids_in(m.group(1))):
                    if ref in items and ref != sid:
                        it_s = items[sid]
                        before = (it_s.get("data") or {}).get("affects") or []
                        key = f"{sid}|affects|{ref}"
                        # affects 는 «새 칸»이 아니라 진단 행에 없다 — 빈칸만 받는 put 을 쓰면 조용히 버려진다.
                        #   이미 값이 있어도 덧붙일 수 있게 직접 행을 만든다(plan-fields 가 연결 칸은 합집합으로 붙인다).
                        if it_s.get("type") in ("risk", "incident") and ref not in before and key not in ledger \
                                and all(r["key"] != key for r in rows):
                            rows.append({"key": key, "item_id": sid, "type": it_s.get("type"), "title": it_s.get("title", ""),
                                         "field": "affects", "kind": "연결", "state": "빈칸" if not before else "채움",
                                         "source": "C3", "field_help": "이 항목이 영향을 준 대상", "field_notes": [],
                                         "field_schema": "", "context": f"「{m.group(0)[:160]}」",
                                         "derived_basis": f"재료 C3: {sid} 「영향 ITEM」", "verdict": "", "value": None,
                                         "basis": "", "reason": "", "candidate": [ref]})
                            n3 += 1
        print(f"   재료 C — 역방향 C1 {n1} · 규칙 밖 C2 {n2} · 영향 목록 C3 {n3} (후보 수 — 칸이 비어 있지 않은 것은 put 이 거른다)")
    dump(a.out, {"server": dg["server"], "project_id": dg["project_id"], "snapshot_dir": str(snap), "rows": rows})
    c = Counter((r["source"], r["type"] + "." + r["field"], "판정 필요" if not r["verdict"] else "채움") for r in rows)
    print(f"✅ 재료 A·B → {len(rows)}칸 · {a.out}")
    for (src, tf, v), n in sorted(c.items()):
        print(f"   {src}  {tf:<36} {v:<6} {n}")


# ── review-fields ─────────────────────────────────────────────────────────
def cmd_review_fields(a) -> None:
    wl = load(a.worklist)
    rows = wl["rows"]
    c = Counter(r["verdict"] or "(미판정)" for r in rows)

    def cell(x) -> str:
        s = x if isinstance(x, str) else json.dumps(x, ensure_ascii=False)
        return (s or "").replace("|", "\\|").replace("\n", " ⏎ ")[:400]
    L = ["# 새 칸 채우기 — 검토표", "", "칸 **%d** — " % len(rows) + " · ".join(f"{k} {c[k]}" for k in [*VERDICTS, "(미판정)"] if c[k]),
         "", "> ☠️ **근거 없는 값은 채움이 아니다.** 산문에 없는 값을 AI 가 만들었다면 「안내」로 돌려라.", ""]
    for v in [*VERDICTS, ""]:
        sel = [r for r in rows if (r["verdict"] or "") == v]
        if not sel:
            continue
        L += [f"## {v or '(미판정)'} ({len(sel)})", "", "| 항목 | 칸 | 값 | 근거 / 사유 |", "|---|---|---|---|"]
        for r in sel:
            L.append(f"| {r['item_id']} | `{r['field']}` | {cell(r['value']) if v == '채움' else ''} | "
                     f"{cell(r['basis'] if v == '채움' else r['reason'])} |")
        L.append("")
    Path(a.out).write_text("\n".join(L) + "\n", encoding="utf-8")
    print(f"✅ 검토표 → {a.out}")


# ── plan-fields ───────────────────────────────────────────────────────────
def cmd_plan_fields(a) -> None:
    wl = load(a.worklist)
    left = [r for r in wl["rows"] if r["verdict"] not in VERDICTS]
    if left and not a.partial:
        die(f"미판정 {len(left)}칸 — 판정을 끝내거나 --partial 로 판정된 것만 계획하라")
    snap = Path(wl["snapshot_dir"])
    by_item: "OrderedDict[str, list]" = OrderedDict()
    for r in wl["rows"]:
        if r["verdict"] == "채움":
            by_item.setdefault(r["item_id"], []).append(r)
    items, skipped = [], []
    for item_id, rs in by_item.items():
        it = load(snap / f"{item_id}.json").get("item", {})
        data = it.get("data") or {}
        ops, changes, planned = [], [], set()
        for r in rs:
            before = data.get(r["field"])
            if r["kind"] != "연결" and r["field"] in planned:
                # 같은 칸을 두 재료가 냈다(derive B 와 작업표 등) — 구조 값은 한 번만 설정한다.
                #   두 번 set 하면 두 번째가 서버에서 PATCH_OP_NOOP → 배치가 멈춘다(KLID 2차 MIG-033 실측).
                skipped.append(f"{item_id}.{r['field']}: 같은 칸이 이미 계획됨 — 중복 행 건너뜀")
                continue
            planned.add(r["field"])
            if r["kind"] == "연결" and isinstance(r["value"], list):
                cur = list(before or []) if isinstance(before, list) else ([before] if before else [])
                add = [x for x in r["value"] if x not in cur]
                if not add:
                    skipped.append(f"{item_id}.{r['field']}: 이미 전부 있다")
                    continue
                ops += ([{"op": "set", "path": r["field"], "value": cur + add}] if not cur else
                        [{"op": "add", "path": r["field"], "value": x} for x in add])
                changes.append({"field": r["field"], "before": before, "after": cur + add, "add": add})
                data = {**data, r["field"]: cur + add}  # 같은 칸의 다음 행이 이 결과 위에 쌓이게
                continue
            # ☠️ 빈 칸만 채운다. 예외는 담당자 문자열 → 객체 승격 하나(같은 내용에 종류만 붙인다).
            if not empty(before) and not (r["kind"] == "담당자" and isinstance(before, str)):
                skipped.append(f"{item_id}.{r['field']}: 이미 값이 있다 — 덮어쓰지 않음")
                continue
            ops.append({"op": "set", "path": r["field"], "value": r["value"]})
            changes.append({"field": r["field"], "before": before, "after": r["value"], "add": [f"{r['field']} 채움"]})
        if ops:
            merged: "OrderedDict[str, dict]" = OrderedDict()
            for ch in changes:
                m = merged.setdefault(ch["field"], {"field": ch["field"], "before": ch["before"], "add": []})
                m["after"] = ch["after"]
                m["add"] += ch["add"]
            items.append({"item_id": item_id, "item_type": it.get("type"), "snapshot_version": it.get("current_version"),
                          "ops": ops, "changes": list(merged.values())})
    plan = {"server": wl["server"], "project_id": wl["project_id"], "guard_version": True,
            "change_summary": ("새 스키마 칸 채우기(mc-logi-schema-fill · 재료 D) — {summary}. 값은 레포 코드(" + Path(wl["repo_root"]).name
                               + ")에서 확인했다. 산문은 그대로 둔다." if wl.get("repo_root") else
                               "관계 초안(mc-logi-schema-fill · 재료 E) — {summary}. AI 가 제안한 관계를 담당자가 검토해 채택했다. 산문은 그대로 둔다."
                               if wl.get("source") == "relation" else
                               "새 스키마 칸 채우기(mc-logi-schema-fill) — {summary}. 값은 이 항목 산문 또는 담당자 답변에서 옮겼다. 산문은 그대로 둔다."),
            "totals": {"items_to_update": len(items), "fields_to_set": sum(len(i["ops"]) for i in items),
                       "skipped": len(skipped)},
            "items": items, "skipped": skipped}
    dump(a.out, plan)
    print(f"✅ 계획 — 항목 {len(items)} · 칸 {plan['totals']['fields_to_set']} · 건너뜀 {len(skipped)} → {a.out}")
    for s in skipped[:10]:
        print(f"   ⚠️ {s}")


# ── guide ─────────────────────────────────────────────────────────────────
def cmd_guide(a) -> None:
    """담당자 안내표 — «질문 수»를 줄이는 것이 목적이다.

    ① 같은 타입·같은 칸이 BULK_MIN 개 이상이면 **묶음 질문 하나**로 묻는다(답 하나를 전부에 펼친다).
       CudoCall 실측: 102칸을 칸마다 물으면 688줄 — 담당자가 읽지 않는다.
    ② 모를 가능성이 큰 칸(optional)은 맨 뒤 「아시면만」 절로 내린다(오래된 사고의 발생 시각 등).
    ③ 나머지만 개별로 묻는다.
    """
    wl = load(a.worklist)
    rows = [r for r in wl["rows"] if r["verdict"] == "안내"]
    must = [r for r in rows if not r.get("optional")]
    opt = [r for r in rows if r.get("optional")]
    groups: "OrderedDict[tuple, list]" = OrderedDict()
    for r in must:
        groups.setdefault((r["type"], r["field"]), []).append(r)
    # 묶음은 «같은 답일 가능성이 높은 칸»에만 — 담당자. 이행 검증 방법처럼 항목마다 답이 다른 칸을
    # 묶으면 한 답이 여러 항목에 복제된다(틀린 값이 조용히 퍼진다).
    bulk = {k: v for k, v in groups.items() if len(v) >= a.bulk_min and v[0]["kind"] == "담당자"}
    single = [r for k, v in groups.items() if k not in bulk for r in v]

    def help_lines(r):
        L = [f"- **무엇을 적나**: {r['field_help'] or ('이 항목을 책임지는 팀·조직·역할·사람' if r['kind'] == '담당자' else '(스키마 설명 없음)')}"]
        if r["kind"] == "담당자":
            L.append('- **형식**: `{"kind": "team|org|role|person", "name": "…"}` — 역할이면 `"role_ref": "ROLE-NNN"` 도. 여럿이면 배열 `[{…, "duty": "맡은 일", "lead": true}, {…}]`')
        return L
    n_q = len(bulk) + len(single)
    L = ["# 담당자 작성 안내", "",
         f"질문 **{n_q}개** (묶음 {len(bulk)} · 개별 {len(single)}) · 아시면만 {len(opt)}칸",
         f"— 원래 칸 수로는 {len(rows)}칸이지만 같은 답이 반복되는 칸은 한 번만 묻는다.", "",
         "## 하는 법", "",
         "1. **묶음 질문**부터 답한다. 답 하나가 그 묶음의 모든 항목에 들어간다. 항목마다 다르면 「예외」에 그 항목만 따로 적는다.",
         "2. **개별 질문**에 답한다.",
         "3. **아시면만** 절은 모르면 건너뛴다 — 비워 두는 것이 정상이다.",
         "4. 모르는 칸은 비워 둔다(다음 진단에 다시 나온다). 이 항목에 해당하지 않으면 `na` 에 사유를 적는다(다시 묻지 않는다).",
         "5. 다 적었으면 에이전트에게 「답변 반영해줘」 → 검토표 → 적용 → 검증.", ""]
    ans = {"bulk": [], "items": []}
    if bulk:
        L += ["## A. 묶음 질문", ""]
        for n, ((t, f), rs) in enumerate(bulk.items(), 1):
            L += [f"### A{n}. `{t}` {len(rs)}개의 `{f}`", "", *help_lines(rs[0]),
                  f"- **대상**: {', '.join(r['item_id'] + ' ' + r['title'][:24] for r in rs)}",
                  f"- **왜 묻나**: {rs[0]['reason']}", ""]
            ans["bulk"].append({"group": f"{t}.{f}", "keys": [r["key"] for r in rs], "value": None,
                                "except": {}, "na": ""})
    if single:
        L += ["## B. 개별 질문", ""]
        for n, r in enumerate(single, 1):
            L += [f"### B{n}. {r['item_id']} — {r['title'][:50]} · `{r['field']}`", "", *help_lines(r),
                  f"- **왜 묻나 / 어디서 찾나**: {r['reason']}", ""]
            ans["items"].append({"key": r["key"], "value": None, "na": ""})
    if opt:
        L += ["## C. 아시면만 — 모르면 건너뛰세요", ""]
        for r in opt:
            L += [f"- **{r['item_id']}** `{r['field']}` — {r['reason']}"]
            ans["items"].append({"key": r["key"], "value": None, "na": "", "optional": True})
        L.append("")
    Path(a.out).write_text("\n".join(L) + "\n", encoding="utf-8")
    dump(a.answers, ans)
    print(f"✅ 안내표 — 질문 {n_q}개(묶음 {len(bulk)}·개별 {len(single)}) + 아시면만 {len(opt)} · 원래 {len(rows)}칸 → {a.out}")


def cmd_answers(a) -> None:
    """담당자 답변(answers.json) → fill-fields 입력. 묶음 답은 그 묶음의 모든 key 로 펼친다(예외 우선)."""
    src = load(a.answers)
    if isinstance(src, list):  # 옛 형식
        src = {"bulk": [], "items": src}
    out, seen = [], set()
    for d in src.get("items", []):
        if d.get("na"):
            out.append({"key": d["key"], "verdict": "해당 없음", "reason": f"담당자: {d['na']}"})
        elif not empty(d.get("value")):
            out.append({"key": d["key"], "verdict": "채움", "value": d["value"], "basis": "담당자: 답변"})
        else:
            continue
        seen.add(d["key"])
    for g in src.get("bulk", []):
        for k in g["keys"]:
            if k in seen:
                continue
            item_id = k.split("|")[0]
            if item_id in (g.get("except") or {}):
                v = g["except"][item_id]
                out.append({"key": k, "verdict": "채움", "value": v, "basis": "담당자: 답변(예외)"})
            elif g.get("na"):
                out.append({"key": k, "verdict": "해당 없음", "reason": f"담당자: {g['na']}"})
            elif not empty(g.get("value")):
                out.append({"key": k, "verdict": "채움", "value": g["value"], "basis": f"담당자: 묶음 답({g['group']})"})
    dump(a.out, {"source": "answers", "rows": out})
    print(f"✅ 답변 {len(out)}칸 → {a.out} (빈 답은 건너뜀 — 다음 진단에 다시 나온다)")


# ── slim-plan ─────────────────────────────────────────────────────────────
def cmd_slim_plan(a) -> None:
    """산문 슬림화 — «삭제만». 고쳐 쓰기는 허용하지 않는다(검증할 수 없다).

    제안: [{"item_id", "path": "description",
            "remove": [{"text": "<원문 그대로>",
                        "moved_to": "<칸>"                       ← 칸으로 옮겨졌다
                        | "source_id": "<ID>", "source_quote": "<그 항목 원문 그대로>"}]}]  ← 상위 항목에 있다
    공통 검사: ① text 가 현재 값에 «정확히 한 번» ② 근거가 있어야 지운다 — 없으면 그 문장은 «고유 정보»라 남는다
      moved_to  : 그 칸이 현재(적용 후) 채워져 있다
      source_id : (a) 이 항목의 데이터에 그 ID 가 칸 값으로 있다(링크로 찾아갈 수 있어야 지울 수 있다)
                  (b) source_quote 가 그 항목 원문에 글자 그대로 있다 (c) 지운 문장과 인용의 내용어가 절반 이상 겹친다
    모드: conservative — 원문의 절반 넘게 지우면 거부 · norm — 「짧은 정의」까지 허용하되 남는 글이 min_chars 이상
    """
    snap = Path(a.snapshot_dir)
    src_dirs = [Path(x) for x in (a.source_dirs or [])] + [snap]

    def load_item(i):
        for d in src_dirs:
            p = d / f"{i}.json"
            if p.exists():
                return load(p).get("item", {})
        return None

    def words(t):
        return {w for w in re.findall(r"[가-힣A-Za-z0-9_]{2,}", t) if not re.fullmatch(r"[A-Z]+-\d+", w)}

    def id_in_fields(data, x):
        def walk(v, top):
            if isinstance(v, str):
                return top not in PROSE_KEYS and v.strip() == x
            if isinstance(v, list):
                return any(walk(y, top) for y in v)
            if isinstance(v, dict):
                return any(walk(y, top) for y in v.values())
            return False
        return any(walk(v, k) for k, v in data.items() if k not in PROSE_KEYS)

    items, bad, stats = [], [], Counter()
    for pr in load(a.proposals):
        item_id, path = pr["item_id"], pr.get("path", "description")
        it = load_item(item_id) or {}
        data = it.get("data") or {}
        before = data.get(path)
        if not isinstance(before, str):
            bad.append(f"{item_id}.{path}: 문자열 칸이 아니다")
            continue
        after, why, ok = before, [], True
        for rm in pr.get("remove") or []:
            t = rm.get("text") or ""
            if not t or after.count(t) != 1:
                bad.append(f"{item_id}: 지울 문장이 원문에 정확히 한 번 있지 않다({after.count(t) if t else 0}회) → {t[:60]!r}")
                ok = False
                break
            if rm.get("moved_to"):
                if empty(data.get(rm["moved_to"])):
                    bad.append(f"{item_id}: 옮겨 갔다는 칸 `{rm['moved_to']}` 이 비어 있다")
                    ok = False
                    break
                why.append(rm["moved_to"]); stats["칸"] += 1
            elif rm.get("source_id"):
                sid, q = rm["source_id"], rm.get("source_quote") or ""
                if not id_in_fields(data, sid):
                    bad.append(f"{item_id}: 근거 항목 {sid} 가 이 항목의 칸에 연결돼 있지 않다 — 링크로 못 찾아가면 지울 수 없다")
                    ok = False
                    break
                src = load_item(sid)
                if not src:
                    bad.append(f"{item_id}: 근거 항목 {sid} 스냅샷이 없다(--source-dir)")
                    ok = False
                    break
                if not q or norm(q) not in norm(prose_text(src.get("data") or {}) + " " + (src.get("title") or "")):
                    bad.append(f"{item_id}: {sid} 인용이 그 항목 원문에 없다 → {q[:60]!r}")
                    ok = False
                    break
                wt, wq = words(t), words(q)
                if not wt or len(wt & wq) / len(wt) < 0.5:
                    bad.append(f"{item_id}: 지운 문장과 {sid} 인용의 내용이 절반도 안 겹친다({len(wt & wq)}/{len(wt)}) — 고유 정보일 수 있다")
                    ok = False
                    break
                why.append(sid); stats["상위 항목"] += 1
            else:
                bad.append(f"{item_id}: 지우는 근거(moved_to 또는 source_id)가 없다 — 근거 없는 문장은 고유 정보라 남긴다 → {t[:60]!r}")
                ok = False
                break
            after = after.replace(t, "", 1)
        if not ok:
            continue
        # ☠️ 지운 문장의 ID 는 «칸 어딘가» 또는 «남은 산문»에 있어야 한다 — 슬림화로 관계 정보가 사라지면 안 된다.
        #    (KLID 2차 실측: security 칸을 근거로 「(ADR-027)」 문장을 지웠는데 security 는 ADR-027 을 담지 않았다.)
        rest_text = after + "\n" + "\n".join(v for k, v in data.items() if k in PROSE_KEYS and k != path and isinstance(v, str))
        lost = []
        for rm in pr.get("remove") or []:
            for x in set(re.findall(r"\b[A-Z]+-\d+\b", rm.get("text") or "")):
                if x == item_id or id_in_fields(data, x) or re.search(re.escape(x) + r"(?!\d)", rest_text):
                    continue
                lost.append(x)
        if lost:
            bad.append(f"{item_id}: 지우면 참조 {sorted(set(lost))} 가 항목에서 사라진다(칸에도 남은 산문에도 없다) — 먼저 칸에 올려라")
            continue
        after = re.sub(r"[ \t]+\n", "\n", after)
        after = re.sub(r"\n{3,}", "\n\n", after).strip()
        if a.mode == "conservative" and len(after) < len(before) * 0.5:
            bad.append(f"{item_id}: 원문의 절반 넘게 지운다({len(before)}→{len(after)}자) — 보수 모드 한도 초과")
            continue
        if a.mode == "norm" and len(after) < a.min_chars:
            bad.append(f"{item_id}: 남는 글이 {len(after)}자 — 짧은 정의라도 {a.min_chars}자는 남아야 한다")
            continue
        if after == before:
            continue
        items.append({"item_id": item_id, "item_type": it.get("type"), "snapshot_version": it.get("current_version"),
                      "ops": [{"op": "set", "path": path, "value": after}],
                      "changes": [{"field": path, "before": before, "after": after,
                                   "add": [f"{path} 슬림화({len(before)}→{len(after)}자, 근거 {'·'.join(sorted(set(why)))[:60]})"]}]})
    if bad and not a.skip_bad:
        die("슬림화 계획 거부 — 아무것도 쓰지 않았다:\n   " + "\n   ".join(bad[:30]))
    plan = {"server": a.server_name, "project_id": a.project, "guard_version": True, "change_kind": "editorial",
            "change_summary": "산문 슬림화(mc-logi-schema-fill, " + a.mode + ") — {summary}. 칸으로 옮겨졌거나 연결된 상위 항목에 있는 문장만 지웠다. 원문은 이전 버전에 남아 있다.",
            "items": items, "rejected": bad}
    dump(a.out, plan)
    b0 = sum(len(i["changes"][0]["before"]) for i in items); a0 = sum(len(i["changes"][0]["after"]) for i in items)
    L = ["# 산문 슬림화 — 전후 비교", "", f"항목 {len(items)} · {b0:,}자 → {a0:,}자 ({(1 - a0 / b0) * 100 if b0 else 0:.1f}% 감소) · 근거 칸 {stats['칸']} · 상위 항목 {stats['상위 항목']} · 거부 {len(bad)}", ""]
    for i in items:
        ch = i["changes"][0]
        L += [f"## {i['item_id']} `{ch['field']}` ({len(ch['before'])}→{len(ch['after'])}자)", "",
              "**전**", "", "```", ch["before"], "```", "", "**후**", "", "```", ch["after"], "```", ""]
    if bad:
        L += ["## 거부(적용 안 함)", "", *[f"- {x}" for x in bad]]
    Path(a.diff).write_text("\n".join(L) + "\n", encoding="utf-8")
    print(f"✅ 슬림화 계획 {len(items)}항목 · {b0:,}→{a0:,}자 · 거부 {len(bad)} → {a.out} · 전후 비교 → {a.diff}")


# ── history (경위 칸으로 옮기기, CO-179) ─────────────────────────────────────
HISTORY_KINDS = ("경위", "현행", "혼합", "본문 충돌")
PARA_RE = re.compile(r"(?:(?!\n\s*\n)[\s\S])+")


def cmd_history_paras(a) -> None:
    """산문 칸을 «빈 줄 기준 문단»으로 자른다(원문 부분 문자열 그대로). 판정 에이전트의 입력."""
    snap = Path(a.snapshot_dir)
    ids = set(Path(a.ids).read_text().split()) if a.ids else None
    out = []
    for f in sorted(snap.glob("*.json")):
        it = load(f).get("item") or {}
        if not it or (ids and it.get("id") not in ids) or it.get("status") in pm.RETIRED:
            continue
        for k in PROSE_KEYS + ("consequences", "decision", "impact"):
            v = (it.get("data") or {}).get(k)
            if not isinstance(v, str):
                continue
            for m in PARA_RE.finditer(v):
                if len(m.group(0).strip()) >= 25:
                    out.append({"pid": f"{it['id']}|{k}|{m.start()}", "item": it["id"], "type": it.get("type"),
                                "title": it.get("title", ""), "field": k, "text": m.group(0)})
    dump(a.out, out)
    print(f"✅ 문단 {len(out)}개 · {sum(len(x['text']) for x in out):,}자 → {a.out}")


def cmd_history_plan(a) -> None:
    """판정된 경위를 본문에서 «분리»하는 계획 — 본문엔 현행만 남긴다(CO-179 `history` 칸은 철회됐다).
    분리한 경위는 사라지지 않는다: 원문은 **적용 직전 버전**(item_versions 스냅샷)에 그대로 있고,
    변경 요약에 「원문은 vN」을 남겨 항목 상세의 변경 타임라인에서 찾아가게 한다.
    ☠️ 경위 중 «검증·증적 기록»은 원래 `acceptance.evidence`·`implementation_record.evidence` 가 제자리다
       (KLID 실측 경위의 42%) — evidence 로 옮기는 재료는 후속. 지금은 분리만 한다.

    판정 입력(여러 파일): [{"pid", "kind": 경위|현행|혼합|본문 충돌, "move": ["<원문 그대로 조각>", …], "reason"}]
      경위      : move 를 비우면 문단 전체를 옮긴다
      혼합      : move 에 옮길 조각(원문 그대로)만 — 나머지는 본문에 남는다
      본문 충돌 : 옮기지 않는다 — 정정이 본문을 뒤집어 경위만 빼면 틀린 규칙이 남는다 → 담당자 안내(--guide)
    검사: 조각이 문단에 «정확히» 있어야 한다 · 남는 본문이 min_chars 미만이면 그 칸은 옮기지 않는다 ·
          history 는 20,000자 상한(CO-179).
    """
    paras = {p["pid"]: p for p in load(a.paras)}
    J = {}
    bad = []
    for f in a.judged:
        for d in load(f):
            if d.get("pid") not in paras:
                bad.append(f"없는 pid: {d.get('pid')}"); continue
            if d.get("kind") not in HISTORY_KINDS:
                bad.append(f"{d['pid']}: kind {d.get('kind')!r} 는 어휘 밖"); continue
            if d["kind"] != "현행" and not (d.get("reason") or "").strip():
                bad.append(f"{d['pid']}: {d['kind']} 는 사유 필수"); continue
            J[d["pid"]] = d
    miss = [p for p in paras if p not in J]
    snap = Path(a.snapshot_dir)
    by_item = {}
    guide = []
    for pid, d in J.items():
        p = paras[pid]
        if d["kind"] == "현행":
            continue
        if d["kind"] == "본문 충돌":
            guide.append((p, d)); continue
        moves = d.get("move") or ([p["text"]] if d["kind"] == "경위" else [])
        if d["kind"] == "혼합" and not moves:
            bad.append(f"{pid}: 혼합인데 옮길 조각이 없다"); continue
        for m in moves:
            if not m.strip() or m not in p["text"]:
                bad.append(f"{pid}: 조각이 문단에 글자 그대로 없다 → {m[:60]!r}"); break
        else:
            by_item.setdefault(p["item"], []).append((p, moves))
    items = []
    stats = Counter()
    for iid, lst in sorted(by_item.items()):
        it = load(snap / f"{iid}.json").get("item") or {}
        data = it.get("data") or {}
        new = {}
        moved_blocks = []
        for p, moves in sorted(lst, key=lambda x: (x[0]["field"], int(x[0]["pid"].rsplit("|", 1)[1]))):
            k = p["field"]
            cur = new.get(k, data.get(k) or "")
            para_new = p["text"]
            for m in moves:
                para_new = para_new.replace(m, "", 1)
            if p["text"] not in cur:
                bad.append(f"{p['pid']}: 문단이 현재 값에 없다(스냅샷 낡음?)"); continue
            new[k] = cur.replace(p["text"], para_new, 1)
            moved_blocks.append((k, moves))
        ops, changes = [], []
        for k, v in new.items():
            v = re.sub(r"[ \t]+\n", "\n", v)
            v = re.sub(r"\n{3,}", "\n\n", v).strip()
            # 정의 칸(description)은 짧은 정의라도 남아야 한다. 그 밖의 칸(notes 등)은 통째로 경위면 칸을 비운다
            # — 내용은 history 에 글자 그대로 있다(KLID 실측: AC-068·SKETCH-003 notes 가 전부 경위).
            if k == "description" and len(v) < a.min_chars:
                bad.append(f"{iid}.{k}: 옮기면 정의가 {len(v)}자만 남는다 — 이 칸은 옮기지 않는다(현행 정의가 먼저 필요)")
                moved_blocks = [b for b in moved_blocks if b[0] != k]
                continue
            if not v:
                # ☠️ `remove` 로 칸을 지우면 «키 삭제» = 구조 변경이라 하위로 전파된다(KLID 실측: SKETCH-003·AC-068).
                #    빈 문자열로 두면 문자열 교체(서술 변경)라 전파되지 않는다.
                ops.append({"op": "set", "path": k, "value": ""})
                changes.append({"field": k, "before": data.get(k) or "", "after": "", "add": [f"{k} 전부 경위(분리)"]})
                continue
            ops.append({"op": "set", "path": k, "value": v})
            changes.append({"field": k, "before": data.get(k) or "", "after": v,
                            "add": [f"{k} 경위 분리({len(data.get(k) or '')}→{len(v)}자)"]})
        if not moved_blocks:
            continue
        sv = it.get("current_version")
        for ch in changes:
            ch["add"] = [ch["add"][0] + f" — 원문 v{sv}"]
        stats["항목"] += 1
        stats["옮긴 글자"] += sum(len(s) for b in moved_blocks for s in b[1])
        items.append({"item_id": iid, "item_type": it.get("type"), "snapshot_version": it.get("current_version"),
                      "ops": ops, "changes": changes})
    plan = {"server": a.server_name, "project_id": a.project, "guard_version": True, "change_kind": "editorial",
            "change_summary": "경위 분리(mc-logi-schema-fill) — {summary}. 본문엔 현행 정의·규칙·이유만 남겼다. 분리한 결정·정정·검증 기록 원문은 표시한 이전 버전에 그대로 있다.",
            "items": items, "rejected": bad}
    dump(a.out, plan)
    if a.guide:
        G = ["# 본문 먼저 고칠 곳 — 경위를 옮기면 틀린 규칙이 남는 문단", "",
             "정정·변경 기록이 본문의 옛 서술을 뒤집었는데 본문은 그대로입니다. 본문을 현행으로 고친 뒤 경위를 옮기세요.", ""]
        for p, d in guide:
            G += [f"## {p['item']} `{p['field']}` — {p['title']}", "", f"> {p['text'][:600]}", "", f"- 사유: {d.get('reason', '')}", ""]
        Path(a.guide).write_text("\n".join(G) + "\n", encoding="utf-8")
    kinds = Counter(d["kind"] for d in J.values())
    print(f"✅ 경위 분리 계획 {stats['항목']}항목 · 분리한 {stats['옮긴 글자']:,}자 · 판정 {dict(kinds)} · 담당자 안내 {len(guide)} · 미판정 {len(miss)} · 거부 {len(bad)} → {a.out}")
    for b in bad[:15]:
        print("   ✗", b)


# ── evidence (경위 중 «검증 기록» → evidence 구조 칸) ─────────────────────────
EVIDENCE_TYPES = ("test_case", "test_run", "document", "screenshot", "log", "external_link", "code")
EVIDENCE_OWNER_TYPES = ("acceptance", "implementation_record")   # evidence 칸이 있는 타입(CO-167)
RESULT_WORDS = {"pass": r"통과|passing|passed|\bpass\b|성공|green|GREEN|그린|SUCCEEDED|BUILD SUCCESSFUL|\b0 failures\b",
                "fail": r"실패|레드|failing|failed|\bfail\b|red|RED|FAILED",
                "inconclusive": r"inconclusive|판단 불가|보류|blocked|미확정|조건부"}


def looks_like_prose(ref: str) -> bool:
    """reference 는 «다시 찾아갈 위치»(경로·spec·해시·CO 번호)다. 문장이면 설명문이다."""
    return len(ref) > 200 or (len(ref) > 80 and " " in ref) or len(ref.split()) > 4 or bool(re.search(r"[.。]\s*$|다[.\s]|했다|한다|됐다|검증\b", ref))


def evidence_value_problems(val, prose_norm: str) -> str:
    """Phase 2(fill-fields) 용 evidence 값 검사 — evidence-plan 과 같은 기준. 문제 없으면 빈 문자열."""
    if not isinstance(val, list) or not val:
        return "배열이어야 한다"
    for ev in val:
        if not isinstance(ev, dict) or ev.get("type") not in EVIDENCE_TYPES:
            return f"type 은 {EVIDENCE_TYPES} 중 하나"
        ref = (ev.get("reference") or "").strip()
        if not ref or norm(ref) not in prose_norm:
            return f"reference 가 산문에 글자 그대로 없다 → {ref[:50]!r}"
        if looks_like_prose(ref):
            return f"reference 가 설명문이다 → {ref[:50]!r} (경로·spec 이름·해시·CO 번호만)"
        rs = ev.get("result")
        if rs is not None:
            q = ev.get("result_quote") or ""
            if rs not in RESULT_WORDS or not q or norm(q) not in prose_norm or not re.search(RESULT_WORDS[rs], q):
                return f"result={rs!r} 는 결과 낱말이 든 result_quote(원문 구절)가 있어야 한다"
    return ""


def norm_dt(s: str):
    """서버 스키마는 시간대가 있는 ISO 만 받는다(`datetime({offset:true})`). 날짜만이면 자정, 시간대가 없으면 한국 시간을 붙인다.
    (KLID 실측: 판정자가 「2026-09-08T11:31:26」처럼 시간대 없는 값을 냈다.)"""
    s = (s or "").strip().replace(" ", "T", 1)
    if re.fullmatch(r"\d{4}-\d{2}-\d{2}", s):
        return s + "T00:00:00+09:00"
    m = re.fullmatch(r"(\d{4}-\d{2}-\d{2}T\d{2}:\d{2}(?::\d{2}(?:\.\d+)?)?)(Z|[+-]\d{2}:\d{2})?", s)
    if not m:
        return None
    base = m.group(1) if m.group(1).count(":") == 2 else m.group(1) + ":00"
    return base + (m.group(2) or "+09:00")


def cmd_evidence_cands(a) -> None:
    """경위 판정(history-plan 입력과 같은 judged)에서 evidence 칸이 있는 타입의 «옮기는 조각»만 뽑는다."""
    paras = {p["pid"]: p for p in load(a.paras)}
    out = []
    for f in a.judged:
        for d in load(f):
            p = paras.get(d.get("pid"))
            if not p or d.get("kind") not in ("경위", "혼합") or p["type"] not in EVIDENCE_OWNER_TYPES:
                continue
            for n, m in enumerate(d.get("move") or [p["text"]]):
                out.append({"cid": f"{d['pid']}#{n}", "item": p["item"], "type": p["type"], "title": p["title"], "text": m})
    dump(a.out, out)
    print(f"✅ evidence 후보 조각 {len(out)}개 · 항목 {len({x['item'] for x in out})} → {a.out}")


def cmd_evidence_plan(a) -> None:
    """판정: [{"cid", "items": [{"type", "reference", "captured_at"?, "result"?, "result_quote"?,
                                 "voided_at"?, "voided_reason"?}]}]  (검증 기록이 아니면 items: [])
    검사 — 지어낸 값은 거부:
      reference  : 조각에 «글자 그대로» 있어야 한다
      captured_at: YYYY-MM-DD 가 조각에 글자 그대로 있어야 한다(시각이 없으면 T00:00:00+09:00)
      result     : result_quote 가 조각에 글자 그대로 있고, 그 구절이 결과 낱말(통과/실패/보류 …)을 담아야 한다
      voided_*   : 조각이 무효·void 를 말해야 한다
    적용: 기존 evidence 에 덧붙인다(type+reference 같으면 건너뜀). ☠️ 추가는 구조 변경이라 하위로 한 번 전파된다(KLID 실측 1홉 32곳).
    """
    cands = {c["cid"]: c for c in load(a.cands)}
    snap = Path(a.snapshot_dir)
    bad, add = [], {}
    for f in a.judged:
        for d in load(f):
            c = cands.get(d.get("cid"))
            if not c:
                bad.append(f"없는 cid: {d.get('cid')}"); continue
            txt = c["text"]
            for ev in d.get("items") or []:
                k = f"{d['cid']} {ev.get('reference', '')[:30]!r}"
                if ev.get("type") not in EVIDENCE_TYPES:
                    bad.append(f"{k}: type {ev.get('type')!r} 는 어휘 밖"); continue
                ref = (ev.get("reference") or "").strip()
                if not ref or ref not in txt:
                    bad.append(f"{k}: reference 가 조각에 글자 그대로 없다"); continue
                if looks_like_prose(ref):
                    bad.append(f"{k}: reference 가 설명문이다 — 경로·spec 이름·해시·CO 번호만"); continue
                item = {"type": ev["type"], "reference": ref}
                ca = ev.get("captured_at")
                if ca:
                    day = ca[:10]
                    if not re.fullmatch(r"\d{4}-\d{2}-\d{2}", day) or day not in txt:
                        bad.append(f"{k}: captured_at 날짜 {day} 가 조각에 없다"); continue
                    item["captured_at"] = norm_dt(ca)
                    if not item["captured_at"]:
                        bad.append(f"{k}: captured_at {ca!r} 형식이 틀렸다(ISO 날짜·시각)"); continue
                rs = ev.get("result")
                if rs:
                    q = ev.get("result_quote") or ""
                    if rs not in RESULT_WORDS or not q or q not in txt or not re.search(RESULT_WORDS[rs], q):
                        bad.append(f"{k}: result {rs!r} 의 근거 구절이 없거나 결과 낱말이 없다"); continue
                    item["result"] = rs
                if ev.get("voided_at") or ev.get("voided_reason"):
                    if not re.search(r"void|무효|철회|폐기", txt):
                        bad.append(f"{k}: 조각이 무효를 말하지 않는데 voided_* 가 있다"); continue
                    if ev.get("voided_reason"):
                        item["voided_reason"] = ev["voided_reason"]
                    va = ev.get("voided_at")
                    if va:
                        if va[:10] not in txt:
                            bad.append(f"{k}: voided_at 날짜가 조각에 없다"); continue
                        item["voided_at"] = norm_dt(va)
                        if not item["voided_at"]:
                            bad.append(f"{k}: voided_at {va!r} 형식이 틀렸다"); continue
                add.setdefault(c["item"], []).append(item)
    items = []
    n_new = 0
    for iid, evs in sorted(add.items()):
        it = load(snap / f"{iid}.json").get("item") or {}
        cur = list((it.get("data") or {}).get("evidence") or [])
        seen = {(e.get("type"), e.get("reference")) for e in cur}
        new = []
        for e in evs:
            if (e["type"], e["reference"]) in seen:
                continue
            seen.add((e["type"], e["reference"])); new.append(e)
        if not new:
            continue
        n_new += len(new)
        items.append({"item_id": iid, "item_type": it.get("type"), "snapshot_version": it.get("current_version"),
                      "ops": [{"op": "set", "path": "evidence", "value": cur + new}],
                      "changes": [{"field": "evidence", "before": cur, "after": cur + new,
                                   "add": [f"evidence {len(cur)}→{len(cur) + len(new)}건 — 원문 v{it.get('current_version')}"]}]})
    plan = {"server": a.server_name, "project_id": a.project, "guard_version": True,
            "change_summary": "검증 기록을 evidence 칸으로(mc-logi-schema-fill) — {summary}. 산문에 적힌 검증·증적 기록을 갈래·위치·날짜·결과로 옮겼다.",
            "items": items, "rejected": bad}
    dump(a.out, plan)
    print(f"✅ evidence 계획 {len(items)}항목 · 새 증적 {n_new}건 · 거부 {len(bad)} → {a.out}")
    for b in bad[:15]:
        print("   ✗", b)


# ── check (최종값 대조) ─────────────────────────────────────────────────────
def same_saved(actual, planned) -> bool:
    """저장값 == 계획값 — 단, 서버가 스키마 기본값(빈 배열·빈 객체·빈 문자열)을 «덧붙인» 것은 같은 것으로 본다.
    (KLID 2차 실측: migration_plan.verification 에 queries: [] 가 자동으로 붙어 3칸이 거짓 불합격.)
    값이 바뀌었거나 «내용 있는» 키가 붙으면 여전히 다르다."""
    if isinstance(actual, dict) and isinstance(planned, dict):
        extra = set(actual) - set(planned)
        if any(not empty(actual[k]) for k in extra) or set(planned) - set(actual):
            return False
        return all(same_saved(actual[k], planned[k]) for k in planned)
    if isinstance(actual, list) and isinstance(planned, list):
        return len(actual) == len(planned) and all(same_saved(x, y) for x, y in zip(actual, planned))
    return actual == planned


def cmd_check(a) -> None:
    plan = load(a.plan)
    after = Path(a.after_dir)
    only = set(a.only.split(",")) if a.only else None
    fail, n = [], 0
    for it in plan["items"]:
        if only and it["item_id"] not in only:
            continue
        p = after / f"{it['item_id']}.json"
        if not p.exists():
            fail.append(f"적용 후 스냅샷 없음: {it['item_id']}")
            continue
        data = load(p).get("item", {}).get("data") or {}
        for ch in it["changes"]:
            n += 1
            if not same_saved(data.get(ch["field"]), ch["after"]):
                fail.append(f"{it['item_id']}.{ch['field']}: 최종값이 계획과 다르다")
    print(f"{'✅ 합격' if not fail else '❌ 불합격'} — 최종값 대조 {n}칸 · 실패 {len(fail)}")
    for s in fail[:20]:
        print(f"   ❌ {s}")
    if fail:
        sys.exit(2)


def cmd_progress(a) -> None:
    b = {r["key"]: r["state"] for r in load(a.before)["rows"]}
    c = {r["key"]: r for r in load(a.after)["rows"]}
    moved = Counter()
    for k, r in c.items():
        if b.get(k) in ("빈칸", "문자열") and r["state"] == "채움":
            moved[r["kind"]] += 1
    tot = Counter((r["kind"], r["state"]) for r in c.values())
    print("이번에 채워진 칸: " + (" · ".join(f"{k} {v}" for k, v in moved.items()) or "0"))
    for k in ["연결", "구조", "담당자"]:
        all_ = sum(v for (kk, _), v in tot.items() if kk == k)
        if all_:
            print(f"   {k:<4} 채움 {tot[(k, '채움')]}/{all_}")


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sp = ap.add_subparsers(dest="cmd", required=True)

    def add(name, fn, *specs):
        s = sp.add_parser(name)
        for flag, kw in specs:
            s.add_argument(flag, **kw)
        s.set_defaults(fn=fn)
    R = {"required": True}
    add("diagnose", cmd_diagnose, ("--server", R), ("--project", R), ("--out-dir", R), ("--type", {}),
        ("--scan", {}), ("--refresh", {"action": "store_true"}))
    add("worklist", cmd_worklist, ("--diagnose", R), ("--kind", {"default": "구조,담당자"}), ("--type", {}), ("--out", R),
        ("--ledger", {}), ("--recheck", {"action": "store_true"}))
    add("derive", cmd_derive, ("--diagnose", R), ("--out", R), ("--ledger", {}),
        ("--prose", {"action": "store_true"}), ("--scan", {}))
    add("code-worklist", cmd_code_worklist, ("--diagnose", R), ("--repo", R), ("--out", R), ("--type", {}),
        ("--ledger", {}), ("--limit", {"type": int, "default": 0}), ("--recheck", {"action": "store_true"}))
    add("relation-cands", cmd_relation_cands, ("--diagnose", R), ("--out", R), ("--ledger", {}), ("--server", {}),
        ("--pool-dir", {}), ("--type", {}), ("--field", {}), ("--limit", {"type": int, "default": 0}),
        ("--top", {"type": int, "default": 6}), ("--min-score", {"type": float, "default": 1.5}), ("--rel-cutoff", {"type": float, "default": 0.5}), ("--include-prose", {"action": "store_true"}),
        ("--include-code-facts", {"action": "store_true"}), ("--round-dir", {}))
    add("auto-na", cmd_auto_na, ("--diagnose", R), ("--out", R), ("--ledger", {}), ("--server", {}), ("--pool-dir", {}))
    add("relation-fill", cmd_relation_fill, ("--worklist", R), ("--input", R))
    add("relation-review", cmd_relation_review, ("--worklist", R), ("--out", R), ("--decisions", R))
    add("relation-plan", cmd_relation_plan, ("--worklist", R), ("--decisions", R), ("--out", R), ("--ledger", {}))
    add("fill-fields", cmd_fill_fields, ("--worklist", R), ("--input", R), ("--ledger", {}))
    add("review-fields", cmd_review_fields, ("--worklist", R), ("--out", R))
    add("plan-fields", cmd_plan_fields, ("--worklist", R), ("--out", R), ("--partial", {"action": "store_true"}))
    add("guide", cmd_guide, ("--worklist", R), ("--out", R), ("--answers", R), ("--bulk-min", {"type": int, "default": 3}))
    add("answers", cmd_answers, ("--answers", R), ("--out", R))
    add("slim-plan", cmd_slim_plan, ("--proposals", R), ("--snapshot-dir", R), ("--server-name", R), ("--project", R),
        ("--out", R), ("--diff", R), ("--mode", {"default": "conservative", "choices": ["conservative", "norm"]}),
        ("--min-chars", {"type": int, "default": 40}), ("--source-dirs", {"nargs": "*", "default": []}),
        ("--skip-bad", {"action": "store_true"}))
    add("history-paras", cmd_history_paras, ("--snapshot-dir", R), ("--out", R), ("--ids", {}))
    add("history-plan", cmd_history_plan, ("--paras", R), ("--judged", {"nargs": "+", "required": True}),
        ("--snapshot-dir", R), ("--server-name", R), ("--project", R), ("--out", R), ("--guide", {}),
        ("--min-chars", {"type": int, "default": 40}))
    add("evidence-cands", cmd_evidence_cands, ("--paras", R), ("--judged", {"nargs": "+", "required": True}), ("--out", R))
    add("evidence-plan", cmd_evidence_plan, ("--cands", R), ("--judged", {"nargs": "+", "required": True}),
        ("--snapshot-dir", R), ("--server-name", R), ("--project", R), ("--out", R))
    add("check", cmd_check, ("--plan", R), ("--after-dir", R), ("--only", {"default": ""}))
    add("progress", cmd_progress, ("--before", R), ("--after", R))
    a = ap.parse_args()
    a.fn(a)


if __name__ == "__main__":
    main()
