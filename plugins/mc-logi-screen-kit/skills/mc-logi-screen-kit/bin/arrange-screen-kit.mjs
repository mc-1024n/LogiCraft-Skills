#!/usr/bin/env node
/**
 * arrange-screen-kit.mjs — 화면 키트 결정적 정리(arrange) 단계 (screen-kit)
 *
 * LLM 0 · 네트워크 0(순수 로컬 파일 변환).
 *
 * download-kit.mjs 가 만든 "평평한(type별)" 스테이징을, mc-logi-screen-implement 의
 * kit-contract.md 가 기대하는 화면 중심(screen-centric) 레이아웃으로 재배치하고
 * 합성 인덱스(SCREENS.md · _shared/ui-catalog.md · _shared/shell-nav.md ·
 * _shared/design-system.md · version-master.md)를 결정적으로 만든다.
 *
 * 내용(설계 본문)은 서버 스켈레톤(verbatim)을 그대로 옮길 뿐 요약/변형하지 않는다 →
 * 열화 원천 차단. 이 스크립트는 이미 받아둔 파일을 "옮겨 담고 목록을 만드는" 기계 작업이다.
 *
 * 입력:
 *   --staging <dir>   download-kit.mjs 산출(평평) 루트 (.kit-manifest.json 포함)
 *   --out <dir>       화면 키트 최종 루트 (docs/screen-design/{slug}-{DOMAIN}/)
 *   --report <path>   download-kit.mjs 의 --report (이번 run status·삭제·모드)
 *   --project <uuid>  project_id (frontmatter·헤더)
 *   [--domain DOMAIN-002] [--domain-name "영상 관제"] [--slug klid-2nd]
 *   [--sync-session 3] [--screens SCREEN-001,SCREEN-002]  (피벗 화면 명시; 없으면 staging 의 screen_spec 전량)
 *
 * 종료코드: 0=성공, 1=인자 오류, 3=무결성 검증 실패
 */
import { promises as fs } from "node:fs";
import { join, dirname } from "node:path";

// ── 인자 ──────────────────────────────────────────────────────────────
function parseArgs(argv) {
  const out = { _: [] };
  for (let i = 0; i < argv.length; i++) {
    const a = argv[i];
    if (a.startsWith("--")) {
      const key = a.slice(2);
      const next = argv[i + 1];
      if (next === undefined || next.startsWith("--")) out[key] = true;
      else { out[key] = next; i++; }
    } else out._.push(a);
  }
  return out;
}
function die(code, msg) { process.stderr.write(`✖ ${msg}\n`); process.exit(code); }

const args = parseArgs(process.argv.slice(2));
const stagingDir = args.staging;
const outDir = args.out;
const reportPath = args.report;
const projectId = args.project || "";
const domain = args.domain || null;
const domainName = args["domain-name"] || domain || "";
const slug = args.slug || "";
const syncSession = args["sync-session"] || "1";
const screensArg = typeof args.screens === "string" ? args.screens.split(",").map((s) => s.trim()).filter(Boolean) : null;

if (!stagingDir) die(1, "--staging <dir> 필수.");
if (!outDir) die(1, "--out <dir> 필수.");

// ── 파일 유틸 ──────────────────────────────────────────────────────────
async function readIf(path) { try { return await fs.readFile(path, "utf-8"); } catch { return null; } }
async function readJsonIf(path) { const t = await readIf(path); if (t == null) return null; try { return JSON.parse(t); } catch { return null; } }

/** 쓰기 + read-back 무결성 검증. */
async function writeVerified(path, content) {
  await fs.mkdir(dirname(path), { recursive: true });
  await fs.writeFile(path, content, "utf-8");
  const back = await fs.readFile(path, "utf-8");
  if (back !== content) die(3, `무결성 검증 실패(수신≠기록): ${path}`);
}
async function copyVerified(from, to) {
  const c = await readIf(from);
  if (c == null) return false;
  await writeVerified(to, c);
  return true;
}

/** 스테이징 .md 의 다운로더 frontmatter 를 떼고 본문(스켈레톤 verbatim)만 반환. */
function stripFrontmatter(md) {
  if (md.startsWith("---\n")) {
    const end = md.indexOf("\n---\n", 4);
    if (end !== -1) return md.slice(end + 5).replace(/^\n+/, "");
  }
  return md.replace(/^\n+/, "");
}

/** 다운로더 frontmatter 의 links: 블록에서 연결된 모든 ITEM id 를 평면 수집(방향/rel 무관). */
function parseFrontmatterLinks(md) {
  if (!md || !md.startsWith("---\n")) return [];
  const end = md.indexOf("\n---\n", 4);
  if (end === -1) return [];
  const front = md.slice(4, end);
  const ids = [];
  let inLinks = false;
  for (const line of front.split("\n")) {
    if (/^links:\s*$/.test(line)) { inLinks = true; continue; }
    if (inLinks) {
      if (/^\s+/.test(line)) {
        const m = line.match(/\[([^\]]*)\]/);
        if (m) for (const id of m[1].split(",").map((s) => s.trim()).filter(Boolean)) ids.push(id);
      } else break; // 들여쓰기 끝 = links 블록 종료
    }
  }
  return ids;
}

// ── 스테이징 경로 ──────────────────────────────────────────────────────
const stg = {
  md: (type, id) => join(stagingDir, type, `${id}.md`),
  raw: (type, id) => join(stagingDir, type, "_raw", `${id}.json`),
  renderDir: (type, id) => join(stagingDir, type, id),
};

// ── 최종(화면 키트) 경로 ──────────────────────────────────────────────
const kit = {
  screenDir: (id) => join(outDir, "screens", id),
  sharedSub: (sub, id) => join(outDir, "_shared", sub, `${id}.md`),
  sharedRaw: (sub, id) => join(outDir, "_shared", sub, "_raw", `${id}.json`),
};

// 타입 → _shared 하위 폴더
const SHARED_SUB = {
  api_endpoint: "api",
  constant: "constant",
  permission_role: "role",
  implementation_guideline: "guideline",
};

// ── frontmatter 빌더 (screen-kit 형식) ─────────────────────────────────
function fm(fields) {
  const lines = ["---"];
  for (const [k, v] of Object.entries(fields)) {
    if (v === undefined) continue;
    lines.push(`${k}: ${v}`);
  }
  lines.push("---");
  return lines.join("\n");
}
function statusBanner(rawItem, status, prevVersion) {
  if (status !== "CHANGED") return "";
  const cs = rawItem.change_summary ? String(rawItem.change_summary) : "(change_summary 없음)";
  const v = rawItem.current_version;
  return (
    `\n> ⚠️ **버전 변경 감지 — logicraft v${prevVersion} → v${v}**\n` +
    `> change_summary: ${cs}\n` +
    `> ↳ 요약/구현 노트 재검토 후 작성된 코드에 반영. 직전 요약은 git diff 확인.\n`
  );
}

// ── main ──────────────────────────────────────────────────────────────
async function main() {
  const manifest = await readJsonIf(join(stagingDir, ".kit-manifest.json"));
  if (!manifest || !manifest.items) die(1, `스테이징 manifest 없음: ${stagingDir}/.kit-manifest.json (download-kit 먼저 실행)`);
  const report = (reportPath && (await readJsonIf(reportPath))) || { mode: "SYNC", items: {}, deleted: [] };
  const statusOf = (id) => report.items?.[id]?.status || "UNCHANGED";
  const prevOf = (id) => report.items?.[id]?.prev_version ?? null;

  // 1) 스테이징 전 ITEM 로드 (manifest 기준) — type/id + raw + body
  const items = {}; // id → {id, type, version, raw, body}
  for (const [id, m] of Object.entries(manifest.items)) {
    const rawWrap = await readJsonIf(stg.raw(m.type, id));
    const raw = rawWrap?.item ?? null;
    const md = await readIf(stg.md(m.type, id));
    items[id] = { id, type: m.type, version: m.version, raw, body: md != null ? stripFrontmatter(md) : "", fmLinks: md != null ? parseFrontmatterLinks(md) : [] };
  }
  const byType = (t) => Object.values(items).filter((it) => it.type === t);

  // 2) 화면 집합 + UC/AC 소속 매핑 (screen.data 기준)
  const screens = byType("screen_spec").filter((s) => !screensArg || screensArg.includes(s.id));
  // UC → 그 UC 를 검증하는 AC 목록 (data.covered_by_acceptances ∪ 그래프 links 의 AC-*)
  const ucToAcs = {};
  for (const uc of byType("use_case")) {
    const d = uc.raw?.data ?? {};
    ucToAcs[uc.id] = [...new Set([...(d.covered_by_acceptances || []), ...uc.fmLinks.filter((x) => x.startsWith("AC-"))])];
  }

  const ucOwner = {}; // UC-id → [screenId]
  const acOwner = {}; // AC-id → [screenId]
  for (const s of screens) {
    const d = s.raw?.data ?? {};
    // 화면↔UC 는 data 필드(realizes_use_cases) 또는 그래프 links(references 등)로 표현됨.
    // AC 는 화면에 직접 안 붙고 SCREEN→UC→(covered_by)→AC 로 간접(depth-2) 연결 → UC 경유로 귀속.
    const related = new Set([...(d.realizes_use_cases || []), ...(d.covered_by_acceptances || []), ...s.fmLinks]);
    for (const id of related) {
      if (id.startsWith("UC-")) {
        (ucOwner[id] ||= []).push(s.id);
        for (const ac of ucToAcs[id] || []) (acOwner[ac] ||= []).push(s.id); // depth-2 AC 귀속
      } else if (id.startsWith("AC-")) {
        (acOwner[id] ||= []).push(s.id); // (드묾) 화면 직접 AC 링크
      }
    }
  }

  const counts = { screen: 0, uc: 0, ac: 0, api: 0, constant: 0, role: 0, guideline: 0, ui: 0, wireframe: 0, design: 0 };

  // 3) 화면(screen_spec) 파일 + 와이어프레임 + 디자인
  const screenRows = []; // SCREENS.md 화면 목록용
  for (const s of screens) {
    const d = s.raw?.data ?? {};
    const dir = kit.screenDir(s.id);
    const renders = Array.isArray(d.static_renders) ? d.static_renders : [];
    const single = renders.length === 1;
    let wfFlag = "⚠️없음";

    // 와이어프레임 렌더 복사 (self-contained: html + wireframe.css 는 downloader 가 이미 상대화)
    if (renders.length === 0) {
      await writeVerified(join(dir, "_no-wireframe.md"), `# ${s.id} 와이어프레임 없음\n\nlogicraft 에 static_render 미등록. mc-logi-screen-design 으로 생성 후 재SYNC.\n`);
    } else {
      let wroteCss = false;
      for (const r of renders) {
        const rid = String(r.id ?? r.surface ?? "render");
        const srcHtml = join(stg.renderDir("screen_spec", s.id), `${rid}.html`);
        const dstHtml = join(dir, single ? "wireframe.html" : `wireframe-${rid}.html`);
        if (await copyVerified(srcHtml, dstHtml)) { counts.wireframe++; wfFlag = "✅"; }
        // 공통 wireframe.css (downloader 가 self-contain 해둔 것) 1회 복사
        if (!wroteCss) {
          if (await copyVerified(join(stg.renderDir("screen_spec", s.id), "wireframe.css"), join(dir, "wireframe.css"))) wroteCss = true;
        }
      }
    }

    // SCREEN frontmatter (links = data 의 의존 필드) + 본문(verbatim)
    const links = {
      consumes_apis: d.consumes_apis || [],
      required_roles: d.required_roles || [],
      realizes_use_cases: d.realizes_use_cases || [],
      acceptance: d.covered_by_acceptances || [],
    };
    const linkLines = Object.entries(links).filter(([, v]) => v.length).map(([k, v]) => `  ${k}: [${v.join(", ")}]`);
    const headLines = [
      "---",
      `logicraft_item: ${s.id}`,
      `type: screen_spec`,
      `version: ${s.raw?.current_version ?? s.version}`,
      `last_updated_at: ${s.raw?.last_updated_at ?? "null"}`,
      `domain: ${domain ?? "null"}`,
      `project_id: ${projectId}`,
      `synced_at: ${new Date().toISOString()}`,
      `sync_session: ${syncSession}`,
      `stale: ${s.raw?.stale ?? false}`,
      `status: ${statusOf(s.id)}`,
      `prev_version: ${prevOf(s.id) ?? "null"}`,
      `raw: ./_raw/${s.id}.json`,
      `wireframe: ${renders.length ? (single ? "./wireframe.html" : `./wireframe-${renders[0].id}.html`) : "null"}`,
      ...(linkLines.length ? ["links:", ...linkLines] : []),
      "---",
    ];
    const front = headLines.join("\n");
    await writeVerified(join(dir, `${s.id}.md`), `${front}\n${statusBanner(s.raw || {}, statusOf(s.id), prevOf(s.id))}\n${s.body}`);
    await writeVerified(join(dir, "_raw", `${s.id}.json`), JSON.stringify({ item: s.raw }, null, 2));
    counts.screen++;
    screenRows.push({ id: s.id, title: s.raw?.title || d.title || s.id, status: statusOf(s.id), wf: wfFlag, apis: (d.consumes_apis || []).join(", "), roles: (d.required_roles || []).join(", ") });
  }

  // 4) 디자인(screen_design → screens/{screen}/design/)
  for (const sd of byType("screen_design")) {
    const d = sd.raw?.data ?? {};
    const screenId = d.designs_screen;
    if (!screenId || !screens.find((s) => s.id === screenId)) continue; // 소속 화면이 이 키트에 없으면 skip
    const designDir = join(kit.screenDir(screenId), "design");
    const renders = Array.isArray(d.renders) ? d.renders : [];
    for (const r of renders) {
      const rid = String(r.id ?? r.surface ?? "render");
      let html = await readIf(join(stg.renderDir("screen_design", sd.id), `${rid}.html`));
      const css = await readIf(join(stg.renderDir("screen_design", sd.id), `${rid}.css`));
      if (html != null) {
        // 내부 상대 css 링크(rid.css)를 design-rid.css 로 치환
        html = html.split(`"${rid}.css"`).join(`"design-${rid}.css"`);
        await writeVerified(join(designDir, `design-${rid}.html`), html);
        counts.design++;
      }
      if (css != null) await writeVerified(join(designDir, `design-${rid}.css`), css);
    }
    // _sd-meta.md
    const meta =
      `# ${sd.id} — 화면 디자인 메타 (${screenId})\n\n` +
      `| 항목 | 값 |\n|---|---|\n` +
      `| SD | ${sd.id} v${sd.raw?.current_version ?? sd.version} |\n` +
      `| status | ${sd.raw?.status ?? ""} |\n` +
      `| designer | ${d.renders?.[0]?.uploaded_by ?? "-"} |\n` +
      `| designs_screen | ${screenId} |\n\n` +
      `## renders\n\n` +
      (renders.map((r) => `- ${r.id} (${r.surface || "-"}) — ${r.label || ""}`).join("\n") || "- (없음)") + "\n";
    await writeVerified(join(designDir, "_sd-meta.md"), meta);
  }

  // 5) UC / AC (소속 화면 아래로 중첩)
  for (const uc of byType("use_case")) {
    const owners = ucOwner[uc.id] || [];
    const targets = owners.length ? owners.map((sid) => join(kit.screenDir(sid), "uc", `${uc.id}.md`)) : [join(outDir, "_shared", "uc-orphan", `${uc.id}.md`)];
    const front = fm({ logicraft_item: uc.id, type: "use_case", version: uc.raw?.current_version ?? uc.version, status: statusOf(uc.id), prev_version: prevOf(uc.id) ?? "null", raw: `${uc.id}.json` });
    for (const t of targets) { await writeVerified(t, `${front}\n${statusBanner(uc.raw || {}, statusOf(uc.id), prevOf(uc.id))}\n${uc.body}`); counts.uc++; }
  }
  for (const ac of byType("acceptance")) {
    const owners = acOwner[ac.id] || [];
    const targets = owners.length ? owners.map((sid) => join(kit.screenDir(sid), "ac", `${ac.id}.md`)) : [join(outDir, "_shared", "ac-orphan", `${ac.id}.md`)];
    const front = fm({ logicraft_item: ac.id, type: "acceptance", version: ac.raw?.current_version ?? ac.version, status: statusOf(ac.id), prev_version: prevOf(ac.id) ?? "null", raw: `${ac.id}.json` });
    for (const t of targets) { await writeVerified(t, `${front}\n${statusBanner(ac.raw || {}, statusOf(ac.id), prevOf(ac.id))}\n${ac.body}`); counts.ac++; }
  }

  // 6) _shared 개별 파일 타입 (api/constant/role/guideline)
  for (const [type, sub] of Object.entries(SHARED_SUB)) {
    for (const it of byType(type)) {
      const front = fm({ logicraft_item: it.id, type, version: it.raw?.current_version ?? it.version, status: statusOf(it.id), prev_version: prevOf(it.id) ?? "null", raw: `./_raw/${it.id}.json` });
      await writeVerified(kit.sharedSub(sub, it.id), `${front}\n${statusBanner(it.raw || {}, statusOf(it.id), prevOf(it.id))}\n${it.body}`);
      await writeVerified(kit.sharedRaw(sub, it.id), JSON.stringify({ item: it.raw }, null, 2));
      counts[sub === "api" ? "api" : sub === "role" ? "role" : sub]++;
    }
  }

  // 7) 합성 인덱스 — design-system.md / ui-catalog.md / shell-nav.md (verbatim 본문 concat)
  const dsItems = byType("design_system");
  if (dsItems.length) {
    const dsBody = dsItems.map((it) => `<!-- ${it.id} v${it.raw?.current_version ?? it.version} -->\n\n${it.body}`).join("\n\n---\n\n");
    await writeVerified(join(outDir, "_shared", "design-system.md"), `# 디자인 시스템 (verbatim)\n\n${dsBody}\n`);
    for (const it of dsItems) await writeVerified(join(outDir, "_shared", "_raw", `${it.id}.json`), JSON.stringify({ item: it.raw }, null, 2));
  }
  const uiItems = byType("ui_component");
  {
    const header = `# UI 컴포넌트 카탈로그${uiItems.length ? ` (${uiItems.length}건)` : " — ⚠️ 비어있음"}\n\n`;
    const idx = uiItems.length
      ? "| ID | 이름 | category |\n|---|---|---|\n" +
        uiItems.map((it) => `| ${it.id} | ${it.raw?.title || ""} | ${it.raw?.data?.category || ""} |`).join("\n") + "\n\n---\n\n"
      : "> ui_component 0건 — mc-logi-screen-implement Phase 0.5 에서 시드 필요.\n\n";
    const body = uiItems.map((it) => `<!-- ${it.id} -->\n\n${it.body}`).join("\n\n---\n\n");
    await writeVerified(join(outDir, "_shared", "ui-catalog.md"), header + idx + body + "\n");
    for (const it of uiItems) await writeVerified(join(outDir, "_shared", "_raw", `${it.id}.json`), JSON.stringify({ item: it.raw }, null, 2));
    counts.ui = uiItems.length;
  }
  const shellItems = [...byType("app_shell"), ...byType("navigation_tree")];
  if (shellItems.length) {
    const body = shellItems.map((it) => `<!-- ${it.id} (${it.type}) -->\n\n${it.body}`).join("\n\n---\n\n");
    await writeVerified(join(outDir, "_shared", "shell-nav.md"), `# 앱 셸 + 내비게이션\n\n${body}\n`);
    for (const it of shellItems) await writeVerified(join(outDir, "_shared", "_raw", `${it.id}.json`), JSON.stringify({ item: it.raw }, null, 2));
  }

  // 8) RETIRED (report.deleted) → _retired/ 이동 (스테이징엔 없음 → 최종 키트에서 이동)
  const retired = Array.isArray(report.deleted) ? report.deleted : [];
  for (const id of retired) {
    // 화면/공유 어디에 있었는지 모르므로 알려진 위치 후보를 훑어 이동
    // (간단화: _retired/{id}.md 로 마킹만 — 실제 파일 위치는 다음 재배치 때 사라짐)
    await writeVerified(join(outDir, "_retired", `${id}.md`), `# RETIRED ${id}\n\nlogicraft 활성 목록에서 제외됨. 코드 제거 검토.\n`);
  }

  // 9) SCREENS.md
  const uiFlag = uiItems.length ? `populated ${uiItems.length}건` : "⚠️ 비어있음 — implement Phase 0.5 에서 시드 필요";
  const changedRows = Object.entries(report.items || {})
    .filter(([, v]) => v.status === "CHANGED" || v.status === "NEW")
    .map(([id, v]) => `| ${id} | ${v.type} | ${v.status}${v.prev_version ? ` (v${v.prev_version}→v${v.version})` : ""} |`);
  const screensMd =
    `# ${domainName} 화면 키트 — SCREENS.md\n\n` +
    `> 이 파일이 화면 구현의 진입점이다. mc-logi-screen-implement 는 이 파일부터 읽는다.\n` +
    `> 키트는 read-only 산출물 — **직접 수정 금지**. 갱신은 mc-logi-screen-kit 재실행.\n\n` +
    `## 키트 현황\n\n| 항목 | 값 |\n|---|---|\n` +
    `| Domain | ${domain ?? "-"} ${domainName} |\n` +
    `| last sync | ${new Date().toISOString()} (session ${syncSession}) |\n` +
    `| 화면 수 | ${screens.length}개 |\n` +
    `| ui_component 카탈로그 | ${uiFlag} |\n` +
    `| 출력 루트 | ${outDir} |\n` +
    `| 생성 | download-kit.mjs + arrange-screen-kit.mjs (결정적, LLM 0) |\n\n` +
    (uiItems.length ? "" : `> ⚠️ **ui_component 카탈로그 비어있음** — mc-logi-screen-implement Phase 0.5 에서 시드 필요\n> DS archetype: ${dsItems[0]?.raw?.title || "미확인"}\n\n`) +
    `## 화면 목록\n\n| SCREEN-ID | 화면명 | 상태 | 와이어프레임 | consumes_apis | required_roles |\n|---|---|---|---|---|---|\n` +
    (screenRows.map((r) => `| ${r.id} | ${r.title} | ${r.status} | ${r.wf} | ${r.apis} | ${r.roles} |`).join("\n") || "| (없음) | | | | | |") + "\n\n" +
    `## 공유 자산 인덱스\n\n| type | 파일 | 건수 |\n|---|---|---|\n` +
    `| design_system | _shared/design-system.md | ${dsItems.length} |\n` +
    `| ui_component | _shared/ui-catalog.md | ${uiItems.length} |\n` +
    `| app_shell + nav | _shared/shell-nav.md | ${shellItems.length} |\n` +
    `| api_endpoint | _shared/api/ | ${counts.api} |\n` +
    `| constant | _shared/constant/ | ${counts.constant} |\n` +
    `| permission_role | _shared/role/ | ${counts.role} |\n` +
    `| implementation_guideline | _shared/guideline/ | ${counts.guideline} |\n\n` +
    `## 빌드 순서 (mc-logi-screen-implement 참조)\n\n` +
    `> "공유 자산 먼저, 화면 단위 점진" 원칙.\n\n` +
    `### Phase 1 — 공유 자산\n1. guideline/ → constant/ → design-system.md\n2. ui-catalog.md (0건이면 Phase 0.5 선행)\n3. shell-nav.md\n4. api/ + role/\n\n` +
    `### Phase 4 — 화면별 점진\n\n| 순서 | 화면 | screen_spec | 와이어프레임 | UC | AC |\n|---|---|---|---|---|---|\n` +
    screens.map((s, i) => `| ${i + 1} | ${s.id} — ${s.raw?.title || ""} | screens/${s.id}/${s.id}.md | wireframe.html | uc/ | ac/ |`).join("\n") + "\n\n" +
    (changedRows.length ? `## 변경 알림 (코드 재반영 필요)\n\n| ITEM | type | 상태 |\n|---|---|---|\n${changedRows.join("\n")}\n\n` : "") +
    (retired.length ? `## RETIRED (_retired/ 이동)\n\n${retired.map((id) => `- ${id} — 코드 제거 검토`).join("\n")}\n\n` : "") +
    `## git 권장\n\n\`docs/screen-design/\` 를 git 으로 함께 버전관리 권장.\n`;
  await writeVerified(join(outDir, "SCREENS.md"), screensMd);

  // 10) version-master.md
  const all = Object.values(items);
  const nNew = all.filter((it) => statusOf(it.id) === "NEW").length;
  const nChanged = all.filter((it) => statusOf(it.id) === "CHANGED").length;
  const nUnchanged = all.filter((it) => statusOf(it.id) === "UNCHANGED").length;
  const vmRows = all
    .slice()
    .sort((a, b) => a.id.localeCompare(b.id))
    .map((it) => `| ${it.id} | ${it.type} | ${it.raw?.title || ""} | ${it.raw?.current_version ?? it.version} | ${it.raw?.stale ?? false} | ${statusOf(it.id)} |`)
    .join("\n");
  const vm =
    `# Version Master — ${domainName} (${domain ?? "-"}) — 화면 키트\n\n` +
    `| 항목 | 값 |\n|---|---|\n` +
    `| project_id | ${projectId} |\n| Domain | ${domain ?? "-"} ${domainName} |\n` +
    `| 다운로드 화면 | ${screens.map((s) => s.id).join(", ") || "-"} |\n` +
    `| Last sync | ${new Date().toISOString()} (session ${syncSession}) |\n` +
    `| Mode | ${report.mode} — NEW ${nNew} / CHANGED ${nChanged} / UNCHANGED ${nUnchanged}${retired.length ? ` / RETIRED ${retired.length}` : ""} |\n` +
    `| 출력 루트 | ${outDir} |\n\n` +
    `## ITEM 버전 표\n\n| ITEM ID | type | title | version | stale | status |\n|---|---|---|---|---|---|\n${vmRows}\n`;
  await writeVerified(join(outDir, "version-master.md"), vm);

  console.log(
    `✅ arrange 완료 — 화면 ${counts.screen} · UC ${counts.uc} · AC ${counts.ac} · ` +
      `API ${counts.api} · CONST ${counts.constant} · ROLE ${counts.role} · GUIDE ${counts.guideline} · UI ${counts.ui} · ` +
      `와이어프레임 ${counts.wireframe} · 디자인 ${counts.design}${retired.length ? ` · RETIRED ${retired.length}` : ""}`,
  );
}

main().catch((e) => die(3, e && e.stack ? e.stack : String(e)));
