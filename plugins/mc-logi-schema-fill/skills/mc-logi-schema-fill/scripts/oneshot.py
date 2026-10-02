#!/usr/bin/env python3
"""mc-logi-schema-fill 한 번에 모드 — 통합 검토 문서(review-all)와 일괄 적용(apply-all).

사람이 개입하는 곳은 셋뿐이다: ① 시작(설명·방식 선택) ② 통합 검토 문서 한 번 ③ 끝 보고.
그 사이의 모으기·판정은 review-all 전에 끝나고, 적용·검증·재진단은 apply-all 이 끝까지 간다.

라운드 폴더 R 의 표준 배치(없는 단계는 건너뛴다):
  R/refs/decisions.json            Phase 1  산문 속 ID → 연결 칸   (prose_migrate draft + fill)
  R/c/worklist.json                Phase 1.5 남의 산문·규칙 밖 칸  (derive --prose + fill-fields)
  R/code/worklist.json             Phase 1.7 코드 근거            (code-worklist + fill-fields)
  R/fields/worklist.json           Phase 2  구조 칸·담당자        (worklist + fill-fields)
  R/rel/cands.json                 Phase 1.8 관계 초안           (relation-cands + relation-fill)
  R/ev/cands.json + judged.json    Phase 3.6 검증 기록 → evidence (evidence-cands + 판정)
  R/hist/paras.json + judged/*.json Phase 3.5 경위 분리          (history-paras + 판정)
  R/slim/proposals.json            Phase 3  산문 슬림화          (판정)

  review-all  → R/REVIEW.md(자세한 통합 검토 문서) · R/decisions.json(줄마다 ID, 기본 «채택»)
  apply-all   → 단계 순서대로: 대상 새로 뜨기 → 계획 → apply --probe --restore-self --allow-dependents →
                뜨기 → check. 버전 충돌은 그 단계를 한 번 다시 떠서 재계획. 그 밖의 실패만 멈춘다.
                끝에 재진단·전후 비교 → R/REPORT.md
"""
from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
from collections import Counter, OrderedDict, defaultdict
from pathlib import Path

HERE = Path(__file__).resolve().parent
PM = str(HERE / "prose_migrate.py")
SF = str(HERE / "schema_fill.py")
ID_RE = re.compile(r"\b[A-Z][A-Z0-9]*-\d+\b")

# 단계: (접두, 이름, 폴더) — 적용 순서이기도 하다(값 채우기 → 증적 → 경위 분리 → 슬림화).
STAGES = [("L", "연결 칸 — 산문 속 ID 이관 (Phase 1)", "refs"),
          ("C", "산문 보충 — 남의 산문·규칙 밖 칸 (Phase 1.5)", "c"),
          ("D", "구현 사실 — 코드 근거 (Phase 1.7)", "code"),
          ("S", "구조 칸·담당자 (Phase 2)", "fields"),
          ("E", "관계 초안 — AI 제안 (Phase 1.8)", "rel"),
          ("V", "검증 기록 → evidence (Phase 3.6)", "ev"),
          ("H", "경위 분리 — 본문엔 현행만 (Phase 3.5)", "hist"),
          ("T", "산문 슬림화 — 칸으로 옮긴 문장 삭제 (Phase 3)", "slim")]


def load(p):
    return json.loads(Path(p).read_text(encoding="utf-8"))


def dump(p, o):
    Path(p).parent.mkdir(parents=True, exist_ok=True)
    Path(p).write_text(json.dumps(o, ensure_ascii=False, indent=1), encoding="utf-8")


def cell(x, n=300) -> str:
    s = x if isinstance(x, str) else json.dumps(x, ensure_ascii=False)
    s = (s or "").replace("|", "\\|").replace("\n", " ⏎ ")
    return s if len(s) <= n else s[:n] + "…"


# ── 스냅샷 전체(진단 snap + 후보 풀)에서 역참조 수 — «하위에 재검토 표시가 붙을 수 있는 항목» 추정 ──
def reverse_refs(diag_dir: Path) -> dict:
    rev = defaultdict(set)
    for d in (diag_dir / "snap", diag_dir / "pool"):
        if not d.exists():
            continue
        for p in d.glob("*.json"):
            it = load(p).get("item", {})
            if not it.get("id"):
                continue
            for ref in set(ID_RE.findall(json.dumps(it.get("data") or {}, ensure_ascii=False))) - {it["id"]}:
                rev[ref].add(it["id"])
    return rev


# ── 단계별 줄 모으기 — 각 줄: {id, stage, item, field, show(검토 문서용 열), ref(적용용 키)} ─────────────
def rows_refs(R: Path):
    p = R / "refs" / "decisions.json"
    if not p.exists():
        return [], {}
    dec = load(p)["decisions"]
    out, other = [], Counter()
    for r in dec:
        if r.get("kind") == "이관":
            out.append({"item": r["item_id"], "field": r.get("target_field") or r.get("field"), "value": r.get("ref"),
                        "basis": " ‖ ".join(c.get("text", "") for c in (r.get("context") or []) if isinstance(c, dict)),
                        "why": r.get("reason") or "", "ref": {"key": r["key"]}})
        else:
            other[r.get("kind") or "(미판정)"] += 1
    return out, dict(other)


def rows_worklist(R: Path, sub: str):
    p = R / sub / "worklist.json"
    if not p.exists():
        return [], {}
    wl = load(p)
    out, other = [], Counter()
    for r in wl["rows"]:
        if r["verdict"] == "채움":
            out.append({"item": r["item_id"], "field": r["field"], "value": r.get("value"), "basis": r.get("basis") or "",
                        "why": r.get("reason") or r.get("note") or "", "ref": {"key": r["key"]}})
        else:
            other[r["verdict"] or "(미판정)"] += 1
    return out, dict(other)


def rows_rel(R: Path):
    p = R / "rel" / "cands.json"
    if not p.exists():
        return [], {}, []
    wl = load(p)
    title = {c["id"]: c["title"] for r in wl["rows"] for c in r["candidates"]}
    out, other, na_cells = [], Counter(), []
    for r in wl["rows"]:
        js = r.get("judged") or {}
        for t, j in js.items():
            if j["verdict"] == "제안":
                out.append({"item": r["item_id"], "field": r["field"], "value": t, "target_title": title.get(t, ""),
                            "basis": "", "why": j["reason"], "outside": j.get("outside"), "ref": {"key": r["key"], "target": t}})
            else:
                other[j["verdict"]] += 1
        if js and all(j["verdict"] == "아님" for j in js.values()):
            na_cells.append({"key": r["key"], "item": r["item_id"], "field": r["field"],
                             "why": "; ".join(f"{t}: {j['reason']}" for t, j in js.items())[:400]})
    return out, dict(other), na_cells


def rows_ev(R: Path):
    c, j = R / "ev" / "cands.json", R / "ev" / "judged.json"
    if not (c.exists() and j.exists()):
        return [], {}
    cands = {x["cid"]: x for x in load(c)}
    out, empty_n = [], 0
    for d in load(j):
        items = d.get("items") or []
        if not items:
            empty_n += 1
            continue
        x = cands.get(d["cid"], {})
        for n, ev in enumerate(items):
            out.append({"item": x.get("item"), "field": "evidence", "value": {k: v for k, v in ev.items() if k != "result_quote"},
                        "basis": x.get("text", ""), "why": ev.get("result_quote") or "", "ref": {"cid": d["cid"], "n": n}})
    return out, {"증적 아님": empty_n}


def rows_hist(R: Path):
    pp = R / "hist" / "paras.json"
    jd = sorted((R / "hist" / "judged").glob("*.json")) if (R / "hist" / "judged").exists() else []
    if not pp.exists() or not jd:
        return [], {}, []
    paras = {p["pid"]: p for p in load(pp)}
    out, other, conflicts = [], Counter(), []
    for f in jd:
        for d in load(f):
            p = paras.get(d.get("pid"), {})
            k = d.get("kind")
            if k in ("경위", "혼합"):
                frag = d.get("move") or [p.get("text", "")]
                out.append({"item": p.get("item"), "field": p.get("field"), "value": frag, "basis": p.get("text", ""),
                            "why": d.get("reason") or "", "kind": k, "ref": {"pid": d["pid"]}})
            elif k == "본문 충돌":
                conflicts.append({"item": p.get("item"), "field": p.get("field"), "why": d.get("reason") or "", "text": p.get("text", "")})
            else:
                other[k or "(미판정)"] += 1
    return out, dict(other), conflicts


def rows_slim(R: Path):
    p = R / "slim" / "proposals.json"
    if not p.exists():
        return [], {}
    out = []
    for d in load(p):
        for n, rm in enumerate(d.get("remove") or []):
            out.append({"item": d["item_id"], "field": d.get("path", "description"), "value": rm["text"],
                        "basis": "", "why": f"옮겨 간 칸: {rm.get('moved_to')}", "ref": {"item": d["item_id"], "path": d.get("path"), "n": n}})
    return out, {}


def attention(R: Path, stages) -> "list[str]":
    """사람이 통합 검토 문서에서 먼저 볼 것 — 스크립트가 뽑는다(KLID 상용 2026-10-02: REVIEW.md 2.2MB 를 사람이 못 봄)."""
    out = []
    # ① 같은 (타입, 칸)을 여러 판정 묶음이 나눠 맡았는데 채움률이 크게 갈림 — 규칙 추출기로 판정을 대신했을 가능성
    for sub, pre in (("c", "C"), ("code", "D"), ("fields", "S")):
        p = R / sub / "worklist.json"
        if not p.exists():
            continue
        g = defaultdict(lambda: defaultdict(lambda: [0, 0]))
        for r in load(p)["rows"]:
            if r.get("verdict"):
                b = g[(r["type"], r["field"])][r.get("batch") or "?"]
                b[0] += r["verdict"] == "채움"; b[1] += 1
        for (t, f), bs in g.items():
            rates = {k: v[0] / v[1] for k, v in bs.items() if v[1] >= 10}
            if len(rates) >= 2 and max(rates.values()) - min(rates.values()) > 0.4:
                det = " · ".join(f"{k} {v:.0%}" for k, v in sorted(rates.items(), key=lambda x: -x[1]))
                out.append(f"- ⚠️ **[{pre}] `{t}.{f}` 묶음별 채움률이 크게 갈림** — {det}. 판정 기준이 묶음마다 달랐을 수 있다(규칙 추출기로 판정을 대신했는지 확인하고 낮은·높은 쪽 표본을 직접 보라).")
    # ② 경계·선례 가드 행을 같은 사유로 이관한 묶음
    p = R / "refs" / "decisions.json"
    if p.exists():
        c = Counter((r.get("reason") or "").strip() for r in load(p)["decisions"] if r.get("guard") and r.get("kind") == "이관")
        for t, n in c.most_common():
            if n >= 3 and t:
                out.append(f"- ⚠️ **[L] 🚧 경계·선례 행 {n}건이 같은 사유로 이관** — 「{t[:80]}」. 행마다 문장이 다르면 판단도 달라야 한다.")
    # ③ 코드에서 채운 역할 칸 — 역할을 로직에서 «추론»했으면 보류가 맞다
    rows = stages.get("D", ([], {}))[0]
    roles = [r for r in rows if r["field"] in ("required_roles", "actor_roles")]
    if roles:
        out.append(f"- [D] 역할 칸 {len(roles)}줄 — 코드가 역할(또는 역할과 1:1 인 권한 코드)을 **직접** 검사할 때만 맞다. 권한 코드만 보고 역할을 추론했으면 기각하라(references/code-judging.md 「역할 칸」).")
    # ④ 관계 초안의 목록 밖 제안
    rows = stages.get("E", ([], {}))[0]
    outside = [r for r in rows if r.get("outside")]
    if outside:
        out.append(f"- [E] 후보 목록 밖에서 찾은 제안 {len(outside)}줄 — 점수 근거가 없는 AI 제안이다. 우선 확인하라.")
    return out


def cmd_review_all(a) -> None:
    R, D = Path(a.dir), Path(a.diagnose).parent  # --diagnose 는 diagnose.json 파일 — 스냅샷은 그 폴더의 snap/·pool/
    rev = reverse_refs(D)
    stages = OrderedDict()
    refs, o = rows_refs(R); stages["L"] = (refs, o)
    for pre, sub in (("C", "c"), ("D", "code"), ("S", "fields")):
        stages[pre] = rows_worklist(R, sub)
    rel, o, na_cells = rows_rel(R); stages["E"] = (rel, o)
    auto_na = load(R / "auto-na.json") if (R / "auto-na.json").exists() else []
    stages["V"] = rows_ev(R)
    hist, o, conflicts = rows_hist(R); stages["H"] = (hist, o)
    stages["T"] = rows_slim(R)
    decisions = []
    for pre, (rows, _) in stages.items():
        for n, r in enumerate(rows, 1):
            r["id"] = f"{pre}-{n:04d}"
            decisions.append({"id": r["id"], "stage": pre, "item": r["item"], "field": r["field"], "ref": r["ref"], "decision": "채택"})
    names = {p: n for p, n, _ in STAGES}
    link_stages = {"L", "C", "D", "E"}
    touched = {pre: {r["item"] for r in rows} for pre, (rows, _) in stages.items()}
    dep = {pre: set().union(*[rev.get(i, set()) for i in touched[pre]]) if touched[pre] else set() for pre in stages}
    all_items = set().union(*touched.values()) if touched else set()

    L = [f"# 새 칸 채우기 — 통합 검토 문서", "",
         f"프로젝트 `{a.project or ''}` · 서버 `{a.server or ''}` · 라운드 `{R.name}`", "",
         "## 0. 이 문서로 정하는 것 — 여기서 한 번만 봅니다", "",
         "이 문서를 확정하면 **아래 모든 단계가 멈추지 않고 끝까지 적용**됩니다(적용 → 최종값 대조 → 재진단 → 보고).",
         "그래서 여기에 **적용될 모든 줄**을 값·근거와 함께 전부 적었습니다.", "",
         "- **기본은 전부 채택**입니다. 빼고 싶은 줄은 **ID 로 알려 주세요**(예: 「E-0012, H-0003 기각」, 「E 단계 ADR 칸 전부 기각」).",
         "- 단계를 통째로 빼도 됩니다(예: 「T 단계는 이번에 하지 마」).",
         "- 적용 중 **자동으로 처리되는 것**: 자기 재검토 표시가 풀리면 되살림 · 스냅샷 뒤 누가 고친 항목은 다시 떠서 재계획 · 산문이 이미 바뀌어 삭제 대상 문장이 없으면 그 줄만 건너뜀(보고에 남김).",
         "- **멈추는 경우는 셋뿐**: 서버가 쓰기를 거부(권한·스키마) · 되살린 재검토 표시가 원래와 다름 · 적용 뒤 최종값이 계획과 다름.", "",
         "## 1. 한눈에", "",
         "| 단계 | 적용할 줄 | 대상 항목 | 판정에서 뺀 것 | 하위 재검토 표시가 붙을 수 있는 항목(상한 추정) |", "|---|---:|---:|---|---:|"]
    for pre, (rows, other) in stages.items():
        if not rows and not other:
            continue
        oth = " · ".join(f"{k} {v}" for k, v in other.items()) or "—"
        spread = pre in link_stages or pre in ("S", "V")
        d_n = len(dep[pre]) if spread else 0
        L.append(f"| **{pre}** {names[pre]} | {len(rows)} | {len(touched[pre])} | {oth} | "
                 f"{d_n if spread else '— (편집 저장 · 구조 편집만 번질 수 있음)'} |")
    L += ["", f"적용 대상 항목 합계 **{len(all_items)}** · 적용할 줄 합계 **{len(decisions)}**", "",
          "> 「하위 재검토 표시」 추정은 대상 항목을 가리키는 항목 수의 합(상한)입니다. 연결 칸이 새로 생기면 그 관계의 하위 항목에",
          "> «다시 볼 것» 표시가 붙습니다 — 관계가 새로 생긴 것이라 정상입니다. 산문 슬림화·경위 분리는 편집으로 저장해 번지지 않지만,",
          "> **목록 원소 추가·구현 진행 칸 변경처럼 구조가 바뀌는 편집은 번질 수 있습니다**(상용 Self 실측).", ""]
    if auto_na:
        cnt = Counter((x["field"], x["why"]) for x in auto_na)
        L += [f"### 자동 「해당 없음」 {len(auto_na)}칸 — 판정 없이 확정", "",
              "칸 설명이나 프로젝트 상태만으로 비워 두는 게 정답인 칸입니다. 서버에는 쓰지 않고 장부에만 남깁니다.", "",
              "| 칸 | 칸 수 | 이유 |", "|---|---:|---|"]
        L += [f"| `{f}` | {n} | {w} |" for (f, w), n in cnt.most_common()]
        L.append("")
    if na_cells:
        L += [f"### 관계 후보가 전부 「아님」이었던 칸 {len(na_cells)}개 — 칸은 «해당 없음»으로 닫지 않습니다", "",
              "후보가 없다는 것은 관계가 없다는 증거가 아닙니다(다음 라운드에 다른 후보가 나올 수 있다). E 를 적용하면 **후보 하나하나**의 「아님」만 장부에 남아 같은 후보를 다시 묻지 않고, 칸 자체는 열려 있습니다. E 를 기각하면 아무것도 남지 않습니다.",
              "", "<details><summary>목록 펼치기</summary>", "", "| 항목 | 칸 | 후보를 뺀 이유 |", "|---|---|---|"]
        L += [f"| {c['item']} | `{c['field']}` | {cell(c['why'], 220)} |" for c in na_cells]
        L += ["", "</details>", ""]
    if conflicts:
        L += [f"### ⚠️ 본문 충돌 {len(conflicts)}건 — 자동으로 고치지 않습니다", "",
              "정정 기록이 본문의 옛 서술을 뒤집었는데 본문이 그대로입니다. 경위만 빼면 틀린 규칙이 남으므로 **분리하지 않고** 담당자 확인으로 넘깁니다.", ""]
        L += [f"- **{c['item']}** `{c['field']}` — {cell(c['why'], 300)}" for c in conflicts]
        L.append("")

    att = attention(R, stages)
    L += ["## 눈여겨볼 것 — 스크립트가 뽑은 확인 지점", ""] + (att or ["- 특이 신호 없음."]) + [""]
    # 단계별 상세 — 크면 단계별 파일로 나눈다(요약본만 사람이 처음부터 끝까지 읽을 수 있는 크기로)
    big = len(decisions) > 400
    head_L, L = L, []
    detail_files = []
    sec = 2
    for pre, (rows, other) in stages.items():
        if not rows:
            continue
        if big:
            if L:
                (R / f"REVIEW-{prev}.md").write_text("\n".join(L) + "\n", encoding="utf-8")
            L, prev = [], pre
            detail_files.append((pre, len(rows)))
        L += [f"## {sec}. [{pre}] {names[pre]} — {len(rows)}줄", ""]
        sec += 1
        if pre == "L":
            L += ["산문에 적힌 ID 를 같은 항목의 연결 칸으로 옮깁니다. 근거 = 산문에 그 ID 가 적힌 문장.", "",
                  "| ID | 항목 | 칸 | 값 | 산문 속 문장 | 판정 이유 |", "|---|---|---|---|---|---|"]
            L += [f"| {r['id']} | {r['item']} | `{r['field']}` | {r['value']} | {cell(r['basis'], 200)} | {cell(r['why'], 120)} |" for r in rows]
        elif pre in ("C", "D", "S"):
            L += [{"C": "다른 항목의 산문·규칙 밖 칸에서 찾은 관계입니다. 근거 = 그 산문 인용.",
                   "D": "레포 코드에서 확인한 구현 사실입니다. 근거 = `파일:줄 — 코드 조각`(스크립트가 실재·일치를 검사함).",
                   "S": "산문에 적혀 있던 값을 구조 칸으로 옮깁니다. 근거 = 산문 인용(스크립트가 원문 일치를 검사함)."}[pre], "",
                  "| ID | 항목 | 칸 | 값 | 근거 |", "|---|---|---|---|---|"]
            L += [f"| {r['id']} | {r['item']} | `{r['field']}` | {cell(r['value'], 160)} | {cell(r['basis'], 260)} |" for r in rows]
        elif pre == "E":
            L += ["**산문에도 코드에도 적혀 있지 않은 관계**입니다. AI 가 두 항목의 본문을 읽고 «관련 있다»고 제안한 것이라 근거는 «이유» 문장입니다.",
                  "판단 질문: **「오른쪽 항목이 내일 바뀌면 왼쪽 항목을 다시 열어 봐야 하나?」** — 아니면 기각하세요.", ""]
            by = OrderedDict()
            for r in rows:
                by.setdefault((r["item"], r["field"]), []).append(r)
            cur = None
            for (it, f), rs in by.items():
                if it != cur:
                    L += ["", f"**{it}**", ""]
                    cur = it
                for r in rs:
                    mark = " _(후보 목록 밖에서 찾음)_" if r.get("outside") else ""
                    L.append(f"- `{r['id']}` `{f}` → **{r['value']}** {cell(r['target_title'], 60)}{mark} — {cell(r['why'], 260)}")
        elif pre == "V":
            L += ["경위 문단 속 검증 기록을 `evidence` 칸으로 옮깁니다. `reference`·날짜·결과 낱말은 조각에 글자 그대로 있어야 적용됩니다.", "",
                  "| ID | 항목 | 증적 | 원문 조각 |", "|---|---|---|---|"]
            L += [f"| {r['id']} | {r['item']} | {cell(r['value'], 200)} | {cell(r['basis'], 220)} |" for r in rows]
        elif pre == "H":
            L += ["본문에 섞인 **경위**(결정·정정·검증 기록)를 본문에서 뺍니다. 지워지지 않습니다 — 적용 직전 버전에 원문이 그대로 남고,",
                  "변경 요약에 «원문 vN» 이 적혀 항목 상세의 변경 이력에서 찾아갈 수 있습니다. 「혼합」은 문단 일부만 뺍니다.", ""]
            by = OrderedDict()
            for r in rows:
                by.setdefault(r["item"], []).append(r)
            for it, rs in by.items():
                L += ["", f"**{it}** — {len(rs)}문단", ""]
                for r in rs:
                    frag = " ‖ ".join(r["value"]) if isinstance(r["value"], list) else r["value"]
                    L.append(f"- `{r['id']}` [{r['kind']}] `{r['field']}` 뺄 것: «{cell(frag, 320)}» — {cell(r['why'], 140)}")
        elif pre == "T":
            L += ["칸으로 옮겨진 **사실 나열 문장만 삭제**합니다(고쳐 쓰지 않음). 「왜」·배경·주의 문장은 남습니다.",
                  "적용 시점에 옮겨 간 칸이 실제로 채워져 있지 않으면 그 줄은 자동으로 건너뜁니다.", "",
                  "| ID | 항목 | 칸 | 삭제할 문장 | 옮겨 간 칸 |", "|---|---|---|---|---|"]
            L += [f"| {r['id']} | {r['item']} | `{r['field']}` | {cell(r['value'], 260)} | {r['why'].replace('옮겨 간 칸: ', '')} |" for r in rows]
        L.append("")
    if big:
        if L:
            (R / f"REVIEW-{prev}.md").write_text("\n".join(L) + "\n", encoding="utf-8")
        L = head_L + ["## 단계별 상세 — 파일로 나눴습니다(줄 " + str(len(decisions)) + "개)", "",
                      "| 단계 | 줄 | 파일 |", "|---|---:|---|"] + \
            [f"| {p} {names[p]} | {n} | `REVIEW-{p}.md` |" for p, n in detail_files] + [""]
    else:
        L = head_L + L
    L += ["## 적용 순서", "",
          "L → C → D → S → E(연결·값 채우기) → V(증적) → H(경위 분리) → T(슬림화). 각 단계는 대상 항목을 **그 순간 새로 떠서** 계획하므로 앞 단계와 버전이 부딪히지 않습니다.",
          "단계마다 5항목씩 적용하며 자기·하위 재검토 상태를 전후로 비교하고, 끝나면 최종값을 계획과 대조합니다.", ""]
    Path(R / "REVIEW.md").write_text("\n".join(L) + "\n", encoding="utf-8")
    dump(R / "decisions.json", decisions)
    # ☠️ 장부 «해당 없음» 은 판정 없이 확정되는 auto-na 만 — E(AI 판정) 의 「후보 전부 아님」 칸을 넣으면
    #    E 를 기각해도 사람이 채택하지 않은 AI 판정이 영구히 다음 라운드를 막는다(KLID 상용 2026-10-02: 404칸).
    dump(R / "na-cells.json", [{"key": x["key"], "item": x["item"], "field": x["field"], "why": x["why"], "source": "auto-na"} for x in auto_na])
    print(f"✅ 통합 검토 문서 → {R/'REVIEW.md'} · 줄 {len(decisions)} · 항목 {len(all_items)} · 장부 해당 없음(auto-na) {len(auto_na)} · 후보 전부 아님 칸 {len(na_cells)}(장부 미기록) · 본문 충돌 {len(conflicts)}")
    for pre, (rows, other) in stages.items():
        if rows or other:
            print(f"   {pre} {names[pre]:<34} 적용 {len(rows):>5} · 뺀 것 {other}")


def cmd_reject(a) -> None:
    """사용자가 말한 ID·단계를 결정 파일에 반영 — 「E-0012 기각」 「T 단계 전부」 「E 의 based_on_adrs 전부」."""
    dec = load(Path(a.dir) / "decisions.json")
    ids = set(a.ids.split(",")) if a.ids else set()
    stages = set(a.stages.split(",")) if a.stages else set()
    n = 0
    for d in dec:
        hit = d["id"] in ids or d["stage"] in stages or (a.field and d["stage"] in (a.field_stage or d["stage"]) and d["field"] == a.field)
        if hit and d["decision"] != "기각":
            d["decision"] = "기각"; n += 1
    dump(Path(a.dir) / "decisions.json", dec)
    print(f"✅ 기각 {n}줄 · 채택 {sum(d['decision'] == '채택' for d in dec)}줄")


# ── apply-all ────────────────────────────────────────────────────────────
def run(cmd, log, check=True):
    """하위 명령을 돌리며 출력을 «줄마다» run.log 에 흘려 쓴다 — 끝날 때까지 잡아 두면 상용에 쓰는 동안
    진행이 전혀 안 보인다(KLID 상용 2026-10-02: 10분 넘게 로그 0바이트). 진행 줄(✅·⏳·묶음)은 화면에도 낸다."""
    with open(log, "a", encoding="utf-8", buffering=1) as f:
        f.write("$ " + " ".join(cmd) + "\n")
        if cmd and cmd[0] == sys.executable and "-u" not in cmd[:2]:
            cmd = [cmd[0], "-u", *cmd[1:]]  # 자식 파이썬의 출력 버퍼링을 끈다(파이프면 기본이 블록 버퍼)
        p = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, bufsize=1)
        lines = []
        for line in p.stdout:
            lines.append(line)
            f.write(line)
            if line.lstrip().startswith(("⏳", "❌", "⚠️")):
                print("   " + line.rstrip(), flush=True)
        p.wait()
        f.write(f"[exit {p.returncode}]\n")
    return subprocess.CompletedProcess(cmd, p.returncode, "".join(lines), "")


def cmd_apply_all(a) -> None:
    R = Path(a.dir)
    A = R / "apply"; A.mkdir(exist_ok=True)
    log = A / "run.log"
    dec = load(R / "decisions.json")
    adopted = defaultdict(list)
    rejected = defaultdict(list)
    for d in dec:
        (adopted if d["decision"] == "채택" else rejected)[d["stage"]].append(d)
    prev = (R / "REPORT.md").read_text(encoding="utf-8").splitlines() if (a.only and (R / "REPORT.md").exists()) else []
    report = prev + ([""] if prev else [f"# 새 칸 채우기 — 적용 보고 ({R.name})", ""])
    srv, proj = a.server, a.project
    ledger = a.ledger

    def snap(stage, ids, tag):
        dd = A / stage / tag
        dd.mkdir(parents=True, exist_ok=True)
        idf = A / stage / f"{tag}.ids"
        idf.write_text(",".join(sorted(ids)))
        p = run([sys.executable, PM, "snapshot", "--server", srv, "--project", proj, "--ids", ",".join(sorted(ids)), "--dir", str(dd)], log)
        if p.returncode != 0:
            raise SystemExit(f"❌ {stage} 스냅샷 실패 — {A/'run.log'}")
        return dd

    def build(stage, fresh):
        out = A / stage / "plan.json"
        if stage == "L":
            d = load(R / "refs" / "decisions.json")
            rej = {x["ref"]["key"] for x in rejected["L"]}
            for r in d["decisions"]:
                if r["key"] in rej:
                    r["kind"], r["reason"] = "보류", "사용자 기각(통합 검토)"
            dump(A / "L" / "decisions.json", d)
            cmd = [sys.executable, PM, "plan", "--decisions", str(A / "L" / "decisions.json"), "--snapshot-dir", str(fresh),
                   "--schemas", a.diagnose, "--out", str(out)]
        elif stage in ("C", "D", "S"):
            sub = {"C": "c", "D": "code", "S": "fields"}[stage]
            wl = load(R / sub / "worklist.json")
            rej = {x["ref"]["key"] for x in rejected[stage]}
            for r in wl["rows"]:
                if r["key"] in rej and r["verdict"] == "채움":
                    r["verdict"], r["reason"] = "보류", "사용자 기각(통합 검토)"
            wl["snapshot_dir"] = str(fresh)
            dump(A / stage / "worklist.json", wl)
            cmd = [sys.executable, SF, "plan-fields", "--worklist", str(A / stage / "worklist.json"), "--out", str(out), "--partial"]
        elif stage == "E":
            wl = load(R / "rel" / "cands.json")
            wl["snapshot_dir"] = str(fresh)
            dump(A / "E" / "cands.json", wl)
            rej = {(x["ref"]["key"], x["ref"]["target"]) for x in rejected["E"]}
            decs = [{"key": r["key"], "target": t, "decision": "기각" if (r["key"], t) in rej else "채택",
                     "note": "사용자 기각(통합 검토)" if (r["key"], t) in rej else ""}
                    for r in wl["rows"] for t, j in (r.get("judged") or {}).items() if j["verdict"] == "제안"]
            dump(A / "E" / "decisions.json", decs)
            cmd = [sys.executable, SF, "relation-plan", "--worklist", str(A / "E" / "cands.json"), "--decisions",
                   str(A / "E" / "decisions.json"), "--out", str(out)] + (["--ledger", ledger] if ledger else [])
        elif stage == "V":
            rej = {(x["ref"]["cid"], x["ref"]["n"]) for x in rejected["V"]}
            j = load(R / "ev" / "judged.json")
            for d in j:
                d["items"] = [ev for n, ev in enumerate(d.get("items") or []) if (d["cid"], n) not in rej]
            dump(A / "V" / "judged.json", j)
            cmd = [sys.executable, SF, "evidence-plan", "--cands", str(R / "ev" / "cands.json"), "--judged", str(A / "V" / "judged.json"),
                   "--snapshot-dir", str(fresh), "--server-name", srv, "--project", proj, "--out", str(out)]
        elif stage == "H":
            rej = {x["ref"]["pid"] for x in rejected["H"]}
            js = []
            for f in sorted((R / "hist" / "judged").glob("*.json")):
                for d in load(f):
                    if d.get("pid") in rej:
                        d = dict(d, kind="현행", move=[])
                    js.append(d)
            dump(A / "H" / "judged.json", js)
            cmd = [sys.executable, SF, "history-plan", "--paras", str(R / "hist" / "paras.json"), "--judged", str(A / "H" / "judged.json"),
                   "--snapshot-dir", str(fresh), "--server-name", srv, "--project", proj, "--out", str(out),
                   "--guide", str(A / "H" / "owner-guide.md")]
        elif stage == "T":
            rej = {(x["ref"]["item"], x["ref"]["path"], x["ref"]["n"]) for x in rejected["T"]}
            props = []
            for d in load(R / "slim" / "proposals.json"):
                keep = [rm for n, rm in enumerate(d.get("remove") or []) if (d["item_id"], d.get("path"), n) not in rej]
                if keep:
                    props.append(dict(d, remove=keep))
            dump(A / "T" / "proposals.json", props)
            cmd = [sys.executable, SF, "slim-plan", "--proposals", str(A / "T" / "proposals.json"), "--snapshot-dir", str(fresh),
                   "--server-name", srv, "--project", proj, "--out", str(out), "--diff", str(A / "T" / "diff.md"), "--skip-bad"]
        p = run(cmd, log)
        if p.returncode != 0 or not out.exists():
            raise SystemExit(f"❌ {stage} 계획 실패 — {log} 끝부분을 보라:\n{(p.stdout + p.stderr)[-1500:]}")
        return out, (p.stdout + p.stderr).strip().splitlines()[-3:]

    for pre, name, _ in STAGES:
        if not adopted[pre] or (a.only and pre not in a.only.split(",")):
            continue
        ids = {d["item"] for d in adopted[pre] if d["item"]}
        (A / pre).mkdir(parents=True, exist_ok=True)
        for attempt in (1, 2):
            fresh = snap(pre, ids, f"snap-before-{attempt}")
            plan_p, plan_tail = build(pre, fresh)
            plan = load(plan_p)
            if not plan.get("items"):
                report += [f"## [{pre}] {name}", "", "적용할 것 없음(계획 0) — " + " / ".join(plan_tail), ""]
                break
            if a.dry:
                report += [f"## [{pre}] {name}", "", f"(예행) 계획 항목 {len(plan['items'])} · " + " / ".join(plan_tail), ""]
                break
            ap = run([sys.executable, PM, "apply", "--server", srv, "--plan", str(plan_p), "--log", str(A / pre / "apply.log.jsonl"),
                      "--probe", "--allow-dependents", "--restore-self"], log)
            out = ap.stdout + ap.stderr
            (A / pre / f"apply-{attempt}.out.txt").write_text(out, encoding="utf-8")
            if ap.returncode != 0 and "E_CONFLICT_VERSION" in out and attempt == 1:
                done = {json.loads(l).get("item") for l in open(A / pre / "apply.log.jsonl", encoding="utf-8") if '"ok": true' in l}
                ids = ids - done  # 이미 적용된 것은 빼고 나머지만 다시 떠서 재계획
                continue
            after = A / pre / "snap-after"
            run([sys.executable, PM, "snapshot", "--server", srv, "--project", proj, "--from-plan", str(plan_p), "--dir", str(after)], log)
            ck = run([sys.executable, SF, "check", "--plan", str(plan_p), "--after-dir", str(after)], log)
            deps = sorted({x.strip() for l in out.splitlines() if "하위 표시 변화" in l for x in l.split("허용):")[-1].split(",") if x.strip()})
            restored = sum(1 for l in out.splitlines() if "자기 표시 자동 복원" in l)
            report += [f"## [{pre}] {name}", "",
                       f"- 계획: 항목 {(plan.get('totals') or {}).get('items_to_update', len(plan['items']))} · 칸 {(plan.get('totals') or {}).get('fields_to_set', sum(len(i.get('changes') or i.get('ops') or []) for i in plan['items']))} · 기각 {len(rejected[pre])}줄",
                       f"- 적용: {'✅' if ap.returncode == 0 else '❌ exit ' + str(ap.returncode)} · 자기 재검토 표시 자동 복원 묶음 {restored} · 하위 새 표시 {len(deps)}항목",
                       f"- 최종값 대조: {(ck.stdout + ck.stderr).strip().splitlines()[0] if (ck.stdout + ck.stderr).strip() else '?'}",
                       *([f"- 계획에서 건너뛴 것: " + " / ".join(plan_tail)] if plan_tail else []), ""]
            if ap.returncode != 0 or ck.returncode != 0:
                report += [f"❌ **여기서 멈춤** — {pre} 단계 실패. 로그: `{A/pre}/apply-{attempt}.out.txt`", "",
                           "```", out[-2500:], "```"]
                Path(R / "REPORT.md").write_text("\n".join(report) + "\n", encoding="utf-8")
                raise SystemExit(f"❌ {pre} 단계에서 멈춤 — {R/'REPORT.md'}")
            break
    # 해당 없음 칸 → 장부(서버에는 쓰지 않는다)
    na = R / "na-cells.json"
    if ledger and na.exists() and not a.dry:
        led = load(ledger) if Path(ledger).exists() else {}
        n = 0
        for c in load(na):
            if c["key"] not in led:
                if c.get("source") != "auto-na":
                    continue  # auto-na 외(출처 없는 옛 파일 포함)는 장부에 «해당 없음» 으로 닫지 않는다 — review-all 을 다시 돌리면 출처가 붙는다
                led[c["key"]] = {"verdict": "해당 없음", "reason": "자동 해당 없음(통합 검토) — " + c["why"][:200]}; n += 1
        dump(ledger, led)
        report += [f"장부에 「해당 없음」 {n}칸 기록(서버 쓰기 없음).", ""]
    if not a.dry:
        # ③ 끝 보고 — 재진단 + 전후 비교(사람이 따로 돌리지 않게)
        dd = R / "diag-after"
        dd.mkdir(exist_ok=True)
        run([sys.executable, PM, "scan", "--server", srv, "--project", proj, "--out", str(dd / "scan.json")], log)
        run([sys.executable, SF, "diagnose", "--server", srv, "--project", proj, "--out-dir", str(dd),
             "--scan", str(dd / "scan.json"), "--refresh"], log)
        pg = run([sys.executable, SF, "progress", "--before", a.diagnose, "--after", str(dd / "diagnose.json")], log)
        report += ["## 재진단 — 이번 라운드 전후", "", "```", (pg.stdout + pg.stderr).strip(), "```", ""]
    Path(R / "REPORT.md").write_text("\n".join(report) + "\n", encoding="utf-8")
    print(f"✅ 일괄 적용 끝 → {R/'REPORT.md'}")


def cmd_scale(a) -> None:
    """모으기 직후·판정 전에 규모를 추정한다 — 시작 게이트에서 범위를 고르게(KLID 상용 2026-10-02:
    경위 문단 13,803개·304만 자, 관계 후보 2,780칸 — 사람이 즉석에서 범위를 정해야 했다)."""
    R = Path(a.dir)
    rows = []
    def n_rows(p, key="rows"):
        return len(load(p)[key]) if p.exists() else 0
    L = n_rows(R / "refs" / "decisions.json", "decisions")
    rows.append(("L 산문 속 ID 이관", L, max(1, -(-L // 600)) if L else 0, "판정 행 약 600개씩"))
    for sub, name in (("c", "C 산문 보충"), ("code", "D 코드 근거"), ("fields", "S 구조·담당자")):
        n = n_rows(R / sub / "worklist.json")
        rows.append((name, n, max(1, -(-n // 200)) if n else 0, "칸 약 200개씩(원문을 전부 정독)"))
    p = R / "rel" / "cands.json"
    nc = sum(len(r.get("candidates") or []) for r in load(p)["rows"]) if p.exists() else 0
    rows.append((f"E 관계 초안(칸 {n_rows(p)})", nc, max(1, -(-nc // 200)) if nc else 0, "후보 약 200개씩"))
    p = R / "hist" / "paras.json"
    chars = sum(len(x.get("text") or "") for x in load(p)) if p.exists() else 0
    npara = len(load(p)) if p.exists() else 0
    rows.append((f"H 경위 분리 + T 슬림화(문단 {npara})", chars, max(1, -(-chars // 80000)) if chars else 0, "글자 약 8만 자씩"))
    print("| 단계 | 규모 | 판정 에이전트(추정) | 나누는 단위 |\n|---|---:|---:|---|")
    for name, n, ag, unit in rows:
        if n:
            print(f"| {name} | {n:,} | {ag} | {unit} |")
    tot = sum(r[2] for r in rows)
    print(f"\n판정 에이전트 합계 약 **{tot}** (동시 실행 상한 20 — 넘으면 대기열). 적용은 분당 약 30항목(KLID 실측).")
    if tot > 20:
        print("⚠️ 규모가 크다 — 시작 게이트에서 단계·타입을 줄여 이번 라운드 범위를 정하라(예: H·T 는 다음 라운드, E 는 핵심 타입만).")


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sp = ap.add_subparsers(dest="cmd", required=True)
    s = sp.add_parser("review-all"); s.set_defaults(fn=cmd_review_all)
    for k in ("--dir", "--diagnose"):
        s.add_argument(k, required=True)
    s.add_argument("--server"); s.add_argument("--project")
    s = sp.add_parser("scale"); s.set_defaults(fn=cmd_scale)
    s.add_argument("--dir", required=True)
    s = sp.add_parser("reject"); s.set_defaults(fn=cmd_reject)
    s.add_argument("--dir", required=True); s.add_argument("--ids"); s.add_argument("--stages")
    s.add_argument("--field"); s.add_argument("--field-stage")
    s = sp.add_parser("apply-all"); s.set_defaults(fn=cmd_apply_all)
    for k in ("--dir", "--server", "--project", "--diagnose"):
        s.add_argument(k, required=True)
    s.add_argument("--ledger"); s.add_argument("--only"); s.add_argument("--dry", action="store_true")
    a = ap.parse_args()
    a.fn(a)


if __name__ == "__main__":
    main()
