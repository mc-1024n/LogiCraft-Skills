#!/usr/bin/env node
/**
 * file-transfer — LogiCraft **프로젝트 자료실** 파일 업로더/다운로더 (CO-086).
 *
 *   node file-transfer.mjs upload   --project <uuid> --file <경로> --name "표시 이름" --category <분류> [옵션]
 *   node file-transfer.mjs download --project <uuid> --id FILE-001 [--out <경로>] [--force]
 *
 * ## ★ 왜 `mc-logi-upload-kit` 이 아니라 별도인가
 * 저쪽은 **정적 텍스트 산출물 전용**이다 — 5종 전부 `{html}`·`{markdown}` JSON 이거나
 * text/html+text/css multipart 이고 `readFile(file, "utf8")` 로 읽는다. 자료실은 hwp·pdf·zip
 * 같은 **바이너리**를 최대 3GB 까지 다루고, 프로토콜도 세션→청크→finalize 로 완전히 다르다.
 * CO-035 가 발행 기능을 분리하며 남긴 근거가 그대로 적용된다:
 * **대상·시맨틱·리스크가 다르면 한 스킬 description 에 묶지 않는다**(둘 다 트리거가 약해진다).
 *
 * ## ★ 왜 한 방 POST 가 아닌가
 * ① 재개가 없다 — 90%에서 끊기면 처음부터. ② 단일 요청이 수십 분 살아 프록시·LB·Node
 * 타임아웃을 다 통과해야 한다. ③ 무결성 확인 지점이 없다.
 * 그래서 서버가 tus 를 흉내낸 3단 프로토콜을 쓴다(CO-080 §2-6).
 *
 * ## 해시
 * Node 는 `crypto.createHash` 에 **증분 API 가 있다**. 브라우저(`crypto.subtle`)와 달리
 * 직접 구현할 필요가 없다 — `apps/web/lib/sha256.ts` 를 포팅하지 말 것. 그건 브라우저에
 * 증분 API 가 없어서 생긴 물건이다.
 *
 * 종료코드: 0 성공 · 1 인자 오류 · 2 HTTP/인증 오류 · 3 파일 오류 · 4 무결성 불일치
 *
 * @design CO-086 (자료실 본체는 CO-080)
 */

import { stat, mkdir, readFile } from "node:fs/promises";
import { readFileSync, createReadStream, createWriteStream, existsSync } from "node:fs";
import { createHash } from "node:crypto";
import { pipeline } from "node:stream/promises";
import { Readable } from "node:stream";
import { homedir } from "node:os";
import { join, basename, dirname, resolve } from "node:path";


// ─────────────────────────────────────────────────────────────────────────────
// ⚠️ 아래 인자 파싱 · MCP 설정 폴백 블록은 `mc-logi-upload-kit/bin/upload-artifact.mjs`
//    와 **같은 내용의 복사본**이다(CO-049 의 키·base 자동 조달).
//    스킬 간 경로 의존을 만들면 배포가 까다로워져 복사를 택했다.
//    ★ 한쪽을 고치면 다른 쪽도 같이 고칠 것 — 안 그러면 조용히 갈라진다.
// ─────────────────────────────────────────────────────────────────────────────

function parseArgs(argv) {
  const out = {};
  for (let i = 0; i < argv.length; i++) {
    const a = argv[i];
    if (a.startsWith("--")) {
      const key = a.slice(2);
      const next = argv[i + 1];
      if (next === undefined || next.startsWith("--")) {
        out[key] = true;
      } else {
        out[key] = next;
        i++;
      }
    }
  }
  return out;
}

function die(code, msg) {
  process.stderr.write(`✖ ${msg}\n`);
  process.exit(code);
}


// ── 모드·인자 ─────────────────────────────────────────────
const args = parseArgs(process.argv.slice(2));
const mode = process.argv[2] && !process.argv[2].startsWith("--") ? process.argv[2] : args.mode;

if (!mode || !["upload", "download"].includes(mode)) {
  die(1, `첫 인자는 upload | download. (받음: ${mode ?? "없음"})\n` +
         `  업로드: file-transfer.mjs upload   --project <uuid> --file <경로> --name "..." --category <분류>\n` +
         `  다운로드: file-transfer.mjs download --project <uuid> --id FILE-001 [--out <경로>] [--force]`);
}

const project = args.project;
if (!project) die(1, "--project <uuid> 필수.");

/**
 * 자료실 분류 — `packages/schemas/src/item-types/file.ts` 의 `fileCategorySchema` 미러.
 * ⚠️ 저쪽이 늘면 여기도 늘려야 한다. 안 늘리면 서버는 받는데 스크립트가 먼저 거절한다.
 */
const FILE_CATEGORIES = ["form", "package", "evidence", "reference", "other"];

if (mode === "upload") {
  if (!args.file) die(1, "upload 은 --file <경로> 필수.");
  if (!args.name) die(1, 'upload 은 --name "표시 이름" 필수.');
  if (!args.category) die(1, `upload 은 --category <${FILE_CATEGORIES.join("|")}> 필수.`);
  if (!FILE_CATEGORIES.includes(args.category)) {
    die(1, `--category 는 ${FILE_CATEGORIES.join(" | ")} 중 하나. (받음: ${args.category})`);
  }
} else {
  if (!args.id) die(1, "download 은 --id <FILE-NNN> 필수.");
  if (!/^FILE-\d+$/.test(String(args.id))) {
    die(1, `--id 는 FILE-NNN 형식. (받음: ${args.id})`);
  }
}

/**
 * MCP 설정 폴백 — env 가 없을 때 ~/.claude.json 의 mcpServers 에서 api-key·base 를 읽는다.
 * 예전 기본값 `localhost:14000` 은 개발 머신 포트라, 다른 환경에서는 자기 빈 로컬을 찔러
 * "서버 접속 불가"로 죽었다. 기본값을 없애고 MCP 설정에서 실제 서버를 읽는다(CO-049).
 * 키 값은 로그에 출력하지 않는다(출처 이름만).
 */
function readMcpConfig(preferred) {
  const home = homedir() || process.env.HOME || "";
  if (!home) return null;
  let cfg;
  try {
    cfg = JSON.parse(readFileSync(join(home, ".claude.json"), "utf8"));
  } catch {
    return null;
  }
  const pools = [];
  if (cfg && cfg.mcpServers) pools.push(cfg.mcpServers);
  for (const proj of Object.values((cfg && cfg.projects) || {})) {
    if (proj && proj.mcpServers) pools.push(proj.mcpServers);
  }
  const preferredNames = preferred ? [preferred] : ["logicraft", "logicraft-dev"];
  for (const pool of pools) {
    const ordered = [
      ...preferredNames.filter((n) => pool[n]),
      ...Object.keys(pool).filter((k) => /^logicraft/i.test(k) && !preferredNames.includes(k)),
    ];
    for (const name of ordered) {
      const srv = pool[name];
      if (!srv) continue;
      const env = srv.env || {};
      const argv = Array.isArray(srv.args) ? srv.args : [];
      let key = env.LOGICRAFT_API_KEY || env.AUTH_TOKEN || env.API_KEY || "";
      if (!key) {
        const h = argv.find((a) => typeof a === "string" && /^authorization\s*:/i.test(a));
        if (h) key = h.slice(h.indexOf(":") + 1);
      }
      key = String(key).replace(/^\s*Bearer\s+/i, "").trim();
      if (/^\$\{.*\}$/.test(key)) key = "";
      const urlArg = argv.find((a) => typeof a === "string" && /^https?:\/\//.test(a));
      const base = urlArg ? urlArg.replace(/\/mcp\/?$/, "").replace(/\/$/, "") : "";
      if (key || base) return { name, key, base };
    }
  }
  return null;
}

const _mcp =
  !process.env.LOGICRAFT_API_KEY || !process.env.LOGICRAFT_API_BASE
    ? readMcpConfig(typeof args.server === "string" ? args.server : null)
    : null;
const API_KEY = String(process.env.LOGICRAFT_API_KEY || (_mcp && _mcp.key) || "")
  .replace(/^\s*Bearer\s+/i, "")
  .trim();
const BASE = String(process.env.LOGICRAFT_API_BASE || (_mcp && _mcp.base) || "").replace(/\/$/, "");
const KEY_SOURCE = process.env.LOGICRAFT_API_KEY ? "env" : _mcp && _mcp.key ? `MCP(${_mcp.name})` : "없음";
const BASE_SOURCE = process.env.LOGICRAFT_API_BASE ? "env" : _mcp && _mcp.base ? `MCP(${_mcp.name})` : "없음";
if (!BASE)
  die(
    1,
    "API base 를 결정할 수 없습니다.\n" +
      "  · LOGICRAFT_API_BASE env 로 지정하거나\n" +
      "  · ~/.claude.json 의 mcpServers 에 logicraft 서버를 등록하세요(자동 인식).\n" +
      "  ※ 로컬 기본값(localhost:14000)은 제거됐습니다 — 남의 머신을 조용히 찌르지 않기 위함(CO-049).",
  );
if (!API_KEY)
  die(
    2,
    "API key 를 결정할 수 없습니다.\n" +
      "  · LOGICRAFT_API_KEY env 로 지정하거나\n" +
      "  · ~/.claude.json 의 mcpServers.<logicraft>.env.AUTH_TOKEN 을 사용하세요(자동 인식).\n" +
      "  ※ 업로드는 write 권한이 필요합니다 — read 전용 키면 403 이 납니다.",
  );
// 키 값은 절대 출력하지 않는다 — 출처 이름만.
process.stdout.write(`🔑 base=${BASE} (${BASE_SOURCE}) · key=${KEY_SOURCE}\n`);


// ── 공통 HTTP ─────────────────────────────────────────────
const enc = encodeURIComponent;
const auth = { Authorization: `Bearer ${API_KEY}` };
const FILES = `${BASE}/projects/${enc(project)}/files`;

/** 응답 본문을 JSON 으로(아니면 문자열 그대로). */
async function body(res) {
  const t = await res.text();
  try {
    return JSON.parse(t);
  } catch {
    return t;
  }
}

/** 실패 응답을 사람이 읽을 수 있게. 서버 code 를 앞세운다. */
function httpMsg(res, j) {
  const code = j && typeof j === "object" && j.code ? j.code : res.status;
  const msg = j && typeof j === "object" && j.message ? j.message : String(j).slice(0, 300);
  return `[${res.status} ${code}] ${msg}`;
}

function fmtBytes(n) {
  if (n < 1024) return `${n} B`;
  const u = ["KB", "MB", "GB", "TB"];
  let v = n / 1024, i = 0;
  while (v >= 1024 && i < u.length - 1) { v /= 1024; i++; }
  return `${v.toFixed(v < 10 ? 1 : 0)} ${u[i]}`;
}

/**
 * 확장자 → MIME. 서버는 이 값을 **그대로 저장**하고 다운로드 때 돌려준다.
 * ⚠️ 목록에 없으면 `application/octet-stream` — 지어내지 않는다.
 *    틀린 MIME 을 박으면 브라우저가 엉뚱하게 렌더하려 든다.
 */
const MIME = {
  hwp: "application/x-hwp", hwpx: "application/hwp+zip",
  pdf: "application/pdf", zip: "application/zip", "7z": "application/x-7z-compressed",
  gz: "application/gzip", tar: "application/x-tar",
  doc: "application/msword",
  docx: "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
  xls: "application/vnd.ms-excel",
  xlsx: "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
  ppt: "application/vnd.ms-powerpoint",
  pptx: "application/vnd.openxmlformats-officedocument.presentationml.presentation",
  png: "image/png", jpg: "image/jpeg", jpeg: "image/jpeg", gif: "image/gif",
  svg: "image/svg+xml", webp: "image/webp",
  csv: "text/csv", txt: "text/plain", json: "application/json", xml: "application/xml",
  md: "text/markdown", html: "text/html",
};
function guessMime(name) {
  const m = /\.([A-Za-z0-9]{1,10})$/.exec(name);
  return (m && MIME[m[1].toLowerCase()]) || "application/octet-stream";
}

/** 스트리밍 sha256 — 파일 크기와 무관하게 상주 메모리가 일정하다. */
async function hashFile(path) {
  const h = createHash("sha256");
  await pipeline(createReadStream(path), async function* (src) {
    for await (const c of src) { h.update(c); yield c; }
  }, async function (src) { for await (const _ of src) { /* drain */ } });
  return h.digest("hex");
}

/** 진행률 한 줄 갱신 (TTY 가 아니면 줄바꿈으로 남긴다 — 로그가 깨지지 않게). */
function progress(done, total, startedAt) {
  const pct = total ? ((done / total) * 100).toFixed(1) : "?";
  const sec = (Date.now() - startedAt) / 1000;
  const rate = sec > 0 ? done / sec : 0;
  const eta = rate > 0 && total > done ? `· 남은 ${Math.ceil((total - done) / rate)}s` : "";
  const line = `  ↑ ${fmtBytes(done)} / ${fmtBytes(total)} (${pct}%) · ${fmtBytes(rate)}/s ${eta}`;
  if (process.stdout.isTTY) process.stdout.write(`\r${line}\x1b[K`);
  else process.stdout.write(`${line}\n`);
}

// ─────────────────────────────────────────────────────────────────────────────
// 업로드 — 세션 생성 → 청크 append → finalize
// ─────────────────────────────────────────────────────────────────────────────
async function doUpload() {
  const path = args.file;
  let st;
  try {
    st = await stat(path);
  } catch (e) {
    die(3, `파일을 열 수 없습니다: ${path} — ${e.message}`);
  }
  if (!st.isFile()) die(3, `파일이 아닙니다: ${path}`);
  if (st.size === 0) die(3, `빈 파일입니다: ${path} (0 바이트는 올릴 이유가 없습니다)`);

  const originalName = basename(path);
  const mimeType = args["mime-type"] || guessMime(originalName);

  process.stdout.write(`📦 ${originalName} · ${fmtBytes(st.size)} · ${mimeType}\n`);
  process.stdout.write(`   해시 계산 중…\n`);
  const sha256 = await hashFile(path);
  process.stdout.write(`   sha256=${sha256}\n`);

  // ① 세션 — --resume 이 있으면 만들지 않고 기존 것을 잇는다.
  let sessionId = typeof args.resume === "string" ? args.resume : null;
  let chunkMax = null;

  if (!sessionId) {
    const res = await fetch(`${FILES}/upload-sessions`, {
      method: "POST",
      headers: { ...auth, "Content-Type": "application/json" },
      body: JSON.stringify({
        original_name: originalName,
        mime_type: mimeType,
        declared_size: st.size,
        expected_sha256: sha256,
        name: args.name,
        category: args.category,
        ...(args.description ? { description: args.description } : {}),
        ...(args.source ? { source: args.source } : {}),
        ...(args.retention ? { retention: args.retention } : {}),
        ...(args["version-label"] ? { version_label: args["version-label"] } : {}),
        ...(args.notes ? { notes: args.notes } : {}),
      }),
    }).catch((e) => die(2, `세션 생성 실패(네트워크): ${e.message} — BASE=${BASE} 확인.`));
    const j = await body(res);
    if (!res.ok) die(2, `세션 생성 실패 ${httpMsg(res, j)}`);
    const s = j.session || j;
    sessionId = s.session_id;
    chunkMax = s.chunk_max_bytes;
    process.stdout.write(`   세션=${sessionId} · 청크상한=${fmtBytes(chunkMax)}\n`);
  }

  // ② 재개 지점 — HEAD 가 진실원. --resume 이든 아니든 항상 확인한다(서버가 이미 받은 게 있을 수 있다).
  let offset = 0;
  {
    const res = await fetch(`${FILES}/upload-sessions/${enc(sessionId)}`, { method: "HEAD", headers: auth })
      .catch((e) => die(2, `offset 조회 실패: ${e.message}`));
    if (!res.ok) die(2, `offset 조회 실패 [${res.status}] — 세션이 만료됐거나 없습니다: ${sessionId}`);
    offset = Number(res.headers.get("upload-offset") || 0);
    if (!chunkMax) {
      // --resume 경로에서는 세션 응답을 못 봤으므로 본문 판으로 상한을 받는다.
      const g = await fetch(`${FILES}/upload-sessions/${enc(sessionId)}`, { headers: auth });
      const gj = await body(g);
      chunkMax = (gj.session || gj).chunk_max_bytes;
    }
    if (offset > 0) process.stdout.write(`   ↻ 재개 — 서버가 이미 ${fmtBytes(offset)} 받았습니다\n`);
  }
  if (!chunkMax || chunkMax <= 0) die(2, "청크 상한을 결정할 수 없습니다(서버 응답에 chunk_max_bytes 없음).");
  if (args["chunk-bytes"]) chunkMax = Math.min(chunkMax, Number(args["chunk-bytes"]));

  // ③ 청크 루프
  const startedAt = Date.now();
  const fail = (msg, code = 2) => {
    process.stdout.write("\n");
    die(code, `${msg}\n  ↻ 이어서 올리려면: --resume ${sessionId}`);
  };

  while (offset < st.size) {
    const end = Math.min(offset + chunkMax, st.size);
    const chunk = await readFileRange(path, offset, end);
    const res = await fetch(`${FILES}/upload-sessions/${enc(sessionId)}`, {
      method: "PATCH",
      headers: {
        ...auth,
        // ⚠️ 전역 body parser 가 먹는 타입(json·urlencoded·text/*)으로 보내면 415 다.
        //    본문이 이미 소비돼 0바이트가 append 되는 사고를 서버가 막고 있다(CO-080).
        "Content-Type": "application/offset+octet-stream",
        "Upload-Offset": String(offset),
      },
      body: chunk,
    }).catch((e) => fail(`청크 전송 실패(네트워크, offset=${offset}): ${e.message}`));

    const j = await body(res);

    if (res.status === 409) {
      // 서버가 본문에 자기 offset 을 실어 준다 — HEAD 왕복 없이 맞춘다.
      const srv = j && typeof j === "object" ? j.offset : null;
      if (typeof srv !== "number") fail(`offset 불일치인데 서버가 위치를 안 알려줬습니다: ${httpMsg(res, j)}`);
      process.stdout.write(`\n   ↻ offset 재정렬: ${offset} → ${srv}\n`);
      offset = srv;
      continue;
    }
    if (res.status === 413) fail(`청크가 너무 큽니다 — --chunk-bytes 로 줄이세요. ${httpMsg(res, j)}`);
    if (res.status === 415) fail(`서버가 Content-Type 을 거절했습니다(스크립트 버그). ${httpMsg(res, j)}`);
    if (!res.ok) fail(`청크 전송 실패 ${httpMsg(res, j)}`);

    offset = typeof j.offset === "number" ? j.offset : end;
    progress(offset, st.size, startedAt);
  }
  if (process.stdout.isTTY) process.stdout.write("\n");

  // ④ finalize — 서버가 실물 해시를 다시 계산해 대조하고, 통과해야 FILE ITEM 이 생긴다.
  const res = await fetch(`${FILES}/upload-sessions/${enc(sessionId)}/finalize`, {
    method: "POST",
    headers: { ...auth, "Content-Type": "application/json" },
    body: JSON.stringify({
      name: args.name,
      category: args.category,
      ...(args.description ? { description: args.description } : {}),
      ...(args.source ? { source: args.source } : {}),
      ...(args.retention ? { retention: args.retention } : {}),
      ...(args["version-label"] ? { version_label: args["version-label"] } : {}),
      ...(args.notes ? { notes: args.notes } : {}),
    }),
  }).catch((e) => fail(`finalize 실패(네트워크): ${e.message}`));

  const j = await body(res);
  if (res.status === 422) {
    process.stdout.write("\n");
    die(4,
      `무결성 대조 실패 — 서버가 받은 내용이 선언한 해시와 다릅니다.\n` +
      `  세션은 폐기됐습니다(부분 수용 없음). 올리는 도중 파일이 바뀌었을 가능성이 큽니다.\n` +
      `  → 처음부터 다시 올리세요(--resume 은 소용없습니다).\n  ${httpMsg(res, j)}`);
  }
  if (!res.ok) fail(`finalize 실패 ${httpMsg(res, j)}`);

  const item = j.item || {};
  const f = j.file || {};
  process.stdout.write(`✅ 자료실 업로드 완료 — ${item.id}\n`);
  process.stdout.write(JSON.stringify(j, null, 2) + "\n");
  process.stdout.write(
    `\n다른 산출물에서 참조하려면 그 ITEM 의 attached_files 에 "${item.id}" 를 넣으세요` +
    ` (update_item · attaches 링크가 자동 생성됩니다).\n`);
  if (f.storage_backend) process.stdout.write(`저장 백엔드: ${f.storage_backend}\n`);
  process.exit(0);
}

/** 파일의 [start, end) 구간만 Buffer 로 읽는다 — 전체를 메모리에 올리지 않는다. */
async function readFileRange(path, start, end) {
  const chunks = [];
  await pipeline(createReadStream(path, { start, end: end - 1 }), async function (src) {
    for await (const c of src) chunks.push(c);
  });
  return Buffer.concat(chunks);
}

// ─────────────────────────────────────────────────────────────────────────────
// 다운로드 — 스트림으로 파일에 쓰고, 받은 뒤 sha256 을 재계산해 대조한다
// ─────────────────────────────────────────────────────────────────────────────
async function doDownload() {
  const id = String(args.id);

  const res = await fetch(`${FILES}/${enc(id)}/download`, { headers: auth })
    .catch((e) => die(2, `다운로드 실패(네트워크): ${e.message} — BASE=${BASE} 확인.`));
  if (!res.ok) {
    const j = await body(res);
    if (res.status === 404) {
      die(2, `찾을 수 없습니다 — ${id} (프로젝트가 맞는지, 삭제되지 않았는지 확인).\n  ${httpMsg(res, j)}`);
    }
    die(2, `다운로드 실패 ${httpMsg(res, j)}`);
  }

  // 파일명은 서버가 준 Content-Disposition 이 진실원(RFC5987). --out 이 있으면 그게 이긴다.
  const cd = res.headers.get("content-disposition") || "";
  const serverName = parseFilename(cd) || `${id}.bin`;
  const outPath = resolve(typeof args.out === "string" ? args.out : serverName);

  if (existsSync(outPath) && args.force !== true && args.force !== "") {
    die(3, `이미 있습니다: ${outPath}\n  덮어쓰려면 --force 를 주세요.`);
  }
  await mkdir(dirname(outPath), { recursive: true });

  const total = Number(res.headers.get("content-length") || 0);
  const startedAt = Date.now();
  const h = createHash("sha256");
  let got = 0;

  await pipeline(
    Readable.fromWeb(res.body),
    async function* (src) {
      for await (const c of src) {
        h.update(c);
        got += c.length;
        if (total) progress(got, total, startedAt);
        yield c;
      }
    },
    createWriteStream(outPath),
  ).catch((e) => die(3, `파일 쓰기 실패: ${outPath} — ${e.message}`));
  if (process.stdout.isTTY && total) process.stdout.write("\n");

  const localSha = h.digest("hex");
  process.stdout.write(`✅ 내려받음 — ${outPath} (${fmtBytes(got)})\n`);

  // ★ 받은 뒤 대조 — 전송 중 잘림을 조용히 넘기지 않는다.
  //   ITEM 메타의 sha256 이 서버가 실물을 받아 실측한 값이라 이 대조가 곧 왕복 무결성 증명이다.
  const meta = await fetchMeta(id);
  if (meta && meta.sha256) {
    if (meta.sha256 === localSha) {
      process.stdout.write(`   sha256 일치 ✓ (${localSha})\n`);
    } else {
      die(4,
        `무결성 불일치 — 받은 파일이 서버 기록과 다릅니다.\n` +
        `  기록: ${meta.sha256}\n  받음: ${localSha}\n` +
        `  파일은 ${outPath} 에 남겨뒀습니다. 다시 받아 보고, 반복되면 서버 저장소를 확인하세요.`);
    }
    if (meta.byte_size && Number(meta.byte_size) !== got) {
      die(4, `크기 불일치 — 기록 ${meta.byte_size} · 받음 ${got}`);
    }
  } else {
    process.stdout.write(`   ⚠️ 메타를 못 읽어 sha256 대조를 건너뜀 — 로컬 해시: ${localSha}\n`);
  }
  process.exit(0);
}

/** `Content-Disposition` 에서 파일명 — RFC5987(`filename*`) 우선. */
function parseFilename(cd) {
  const star = /filename\*\s*=\s*UTF-8''([^;]+)/i.exec(cd);
  if (star) {
    try {
      return basename(decodeURIComponent(star[1].trim()));
    } catch {
      /* 잘못 인코딩된 값 — plain 으로 폴백 */
    }
  }
  const plain = /filename\s*=\s*"([^"]+)"/i.exec(cd) || /filename\s*=\s*([^;]+)/i.exec(cd);
  return plain ? basename(plain[1].trim()) : null;
}

/**
 * FILE ITEM 의 `data` 를 읽어 sha256·byte_size 를 얻는다.
 * ⚠️ 실패해도 다운로드를 실패로 만들지 않는다 — 파일은 이미 받았고, 대조만 못 한 것이다.
 *    그 사실을 **명시적으로 알린다**(조용히 통과시키지 않는다).
 */
async function fetchMeta(id) {
  try {
    const res = await fetch(`${FILES}`, { headers: auth });
    if (!res.ok) return null;
    const j = await body(res);
    const list = Array.isArray(j) ? j : Array.isArray(j.files) ? j.files : Array.isArray(j.items) ? j.items : [];
    const hit = list.find((x) => x && (x.id === id || x.file_item_id === id));
    if (!hit) return null;
    return hit.data ? hit.data : hit;
  } catch {
    return null;
  }
}

// ── 실행 ─────────────────────────────────────────────────
if (mode === "upload") await doUpload();
else await doDownload();
