#!/usr/bin/env node
/**
 * mc-logi-upload-kit — 로컬 스킬 디렉터리를 LogiCraft 마켓플레이스에 **REST 직송** 발행 (CO-034).
 *
 * ## 왜 이 스크립트인가
 * MCP `publish_skill` 은 호출하는 AI 가 **모든 파일 내용을 한 tool call 에 실어야** 한다.
 * 큰 스킬은 모델 출력 한도에서 잘리고, `Read` 도구로 읽으면 줄번호 prefix(`   123→`)가 섞이며,
 * AI 가 본문을 다시 타이핑하는 과정에서 오타가 들어간다(실측: 마켓본에 `컬럼→컴럼`·`과잉→과익`).
 * 여기서는 **스크립트가 파일을 직접 읽어 보내므로 본문이 대화 컨텍스트를 거치지 않는다** —
 * 잘림·줄번호 오염·재타이핑 오타가 원천적으로 불가능하다.
 *
 * `upload-artifact.mjs`(아티팩트 단일 파일 업로드)의 형제이며, 같은 인증·종료코드 규약을 쓴다.
 * 인자 체계가 완전히 다르므로(디렉터리 발행 + 시맨틱 옵션) 파일을 나눠 둔다.
 *
 * ## 사용법
 * ```
 * LOGICRAFT_API_KEY=lc_… LOGICRAFT_API_BASE=https://호스트:포트/api \
 *   node publish-skill.mjs <스킬디렉터리> --category <카테고리> [옵션]
 * ```
 *
 * ## ★ 플러그인 레벨 파일 규칙 — `_plugin/` 하위
 * 스킬 디렉터리 안의 **`_plugin/` 아래 파일은 `plugin_files[]`** 로 전송되어
 * `plugins/<name>/` **바로 아래**에 놓인다. 동봉 서브에이전트가 대표 사례다:
 * ```
 * ~/.claude/skills/mc-logi-update/
 *   SKILL.md                       →  plugins/mc-logi-update/skills/mc-logi-update/SKILL.md
 *   cascade-patterns.md            →  plugins/mc-logi-update/skills/mc-logi-update/cascade-patterns.md
 *   _plugin/agents/specialist.md   →  plugins/mc-logi-update/agents/specialist.md
 * ```
 * Claude Code 플러그인은 서브에이전트를 `plugins/<name>/agents/` 에서 로드한다
 * (`skills/<name>/agents/` 에 두면 설치해도 에이전트로 잡히지 않는다).
 * `_plugin/` 이 없으면 `plugin_files` 파트를 **아예 보내지 않으며**, 그때 서버는
 * 기존 플러그인 레벨 파일을 **보존**한다.
 *
 * 제외: `.git` · `node_modules` · `.DS_Store` (`_plugin/` 안에서도 동일).
 *
 * ## ★ 발행은 되돌리기 번거로운 공개 행위다
 * 실발행 전 **반드시 `--dry-run`** 으로 무엇이 쓰이고/사라지고/보존되는지 확인하고
 * 사용자에게 보여준 뒤 실행할 것. dry_run 은 검증만 하고 커밋·push 를 하지 않는다.
 *
 * 종료코드: 0 성공 · 1 인자 오류 · 2 HTTP/인증 오류 · 3 파일 오류.
 */
import { readdir, readFile, stat } from "node:fs/promises";
import { existsSync } from "node:fs";
import { basename, join, relative, resolve, sep } from "node:path";

const SKIP_NAMES = new Set([".git", "node_modules", ".DS_Store"]);
const PLUGIN_DIR = "_plugin";
const CATEGORIES = [
  "design",
  "feature_impl",
  "screen_impl",
  "operations",
  "review",
  "other",
];

// ── 인자 파싱 ─────────────────────────────────────────────
/**
 * `--key value` · `--flag` · 반복 지정(`--delete a --delete b`) 지원.
 * 위치 인자(스킬 디렉터리)는 `_rest` 로 모은다.
 */
function parseArgs(argv) {
  const out = { _rest: [] };
  const REPEATABLE = new Set(["delete", "delete-plugin"]);
  for (let i = 0; i < argv.length; i++) {
    const a = argv[i];
    if (!a.startsWith("--")) {
      out._rest.push(a);
      continue;
    }
    const key = a.slice(2);
    const next = argv[i + 1];
    const value = next === undefined || next.startsWith("--") ? true : next;
    if (value !== true) i++;
    if (REPEATABLE.has(key)) {
      (out[key] ??= []).push(value === true ? "" : value);
    } else {
      out[key] = value;
    }
  }
  return out;
}

function die(code, msg) {
  process.stderr.write(`✖ ${msg}\n`);
  process.exit(code);
}

function usage() {
  process.stdout.write(`사용법:
  node publish-skill.mjs <스킬디렉터리> --category <카테고리> [옵션]

필수
  <스킬디렉터리>           발행할 스킬 폴더 (예: ~/.claude/skills/mc-logi-update)
  --category <값>          ${CATEGORIES.join(" | ")}

선택
  --name <이름>            스킬명. 기본값 = 디렉터리 이름 (SKILL.md frontmatter name 과 같아야 함)
  --mode upsert|replace    기본 upsert(넘긴 파일만 갱신, 나머지 보존).
                           replace 는 skills/<name>/ 전체 교체 — 파일이 사라지면 서버가 거부한다.
  --allow-delete           replace 에서 파일 소멸을 허용(소멸 가드 해제)
  --delete <상대경로>       upsert 에서 지울 스킬 파일 (반복 지정 가능)
  --delete-plugin <경로>    지울 플러그인 레벨 파일 (반복 지정 가능)
  --changelog "<문구>"      커밋 메시지에 붙는 변경 요약
  --summary "<문구>"        카드 한 줄 요약
  --listing <파일>          카드 상세(MARKETPLACE.md) 마크다운 파일 경로. 생략 시 기존 상세 보존
  --dry-run                ★ 예행연습 — 서버가 검증만 하고 원격에 커밋·push 하지 않는다
  --list-only              전송 없이 보낼 목록만 로컬 출력 (네트워크·api key 불필요)
  --api-key <키>           기본값 = 환경변수 LOGICRAFT_API_KEY (lc_… , write 권한 필요)
  --api-base <URL>         기본값 = LOGICRAFT_API_BASE, 없으면 http://localhost:14000/api
                           ★ '/api' 를 **포함**한 값이다 (upload-artifact.mjs 와 동일 규약).
                             레포 안 CLI(apps/api/scripts/publish-skill.ts)의 --api-url 은
                             '/api' 를 포함하지 않는 다른 규약이니 혼동하지 말 것.

예시
  # 1) 무엇이 올라가고 사라지는지 먼저 확인 (원격 무변경)
  LOGICRAFT_API_KEY=lc_… LOGICRAFT_API_BASE=https://logicraft.cudo.co.kr:10000/api \\
    node publish-skill.mjs ~/.claude/skills/mc-logi-update --category operations --dry-run
  # 2) 확인했으면 실제 발행
  LOGICRAFT_API_KEY=lc_… LOGICRAFT_API_BASE=https://logicraft.cudo.co.kr:10000/api \\
    node publish-skill.mjs ~/.claude/skills/mc-logi-update --category operations
  # 3) 잘못된 위치의 파일을 지우면서 발행
  … node publish-skill.mjs <dir> --category operations --delete agents/old.md
`);
}

// ── 디렉터리 수집 ─────────────────────────────────────────
/**
 * 재귀 수집. `_plugin/` 아래는 별도 그룹으로 분리하고 경로에서 접두를 벗긴다.
 * 반환 경로는 항상 `/` 구분자(서버 규약 — 파트의 filename 이 곧 상대경로).
 */
async function collect(root) {
  const files = [];
  const pluginFiles = [];
  async function walk(dir) {
    const entries = await readdir(dir, { withFileTypes: true });
    for (const e of entries) {
      if (SKIP_NAMES.has(e.name)) continue;
      const abs = join(dir, e.name);
      if (e.isDirectory()) {
        await walk(abs);
        continue;
      }
      if (!e.isFile()) continue;
      const rel = relative(root, abs).split(sep).join("/");
      const st = await stat(abs);
      if (rel === PLUGIN_DIR || rel.startsWith(`${PLUGIN_DIR}/`)) {
        pluginFiles.push({
          rel: rel.slice(PLUGIN_DIR.length + 1),
          abs,
          bytes: st.size,
        });
      } else {
        files.push({ rel, abs, bytes: st.size });
      }
    }
  }
  await walk(root);
  const byRel = (a, b) => a.rel.localeCompare(b.rel);
  files.sort(byRel);
  pluginFiles.sort(byRel);
  return { files, pluginFiles };
}

/**
 * 파일 본문 읽기.
 *
 * ⚠️ **크기·개수 상한은 여기서 판정하지 않는다.** 서버는 DB 오버레이(CO-032 시스템 설정)를
 * 우선하므로 로컬에 상한을 박으면 서버와 갈라지고, 그 어긋남은 아무 테스트에도 안 걸린다.
 * 판정은 서버에 맡기고 여기서는 **사람이 읽을 수 있게 크기를 출력**만 한다.
 * 상한으로 거부되면 서버 응답(`limits` 포함)을 그대로 보여준다.
 */
async function readText(f) {
  let buf;
  try {
    buf = await readFile(f.abs);
  } catch (e) {
    die(3, `파일 읽기 실패: ${f.rel} — ${e.message}`);
  }
  // 스킬은 텍스트 번들이다. NUL 이 있으면 UTF-8 로 실어 보내는 순간 손상된다.
  if (buf.includes(0)) {
    die(3, `${f.rel} 은 바이너리로 보입니다 — 스킬은 텍스트 파일만 발행됩니다.`);
  }
  return buf.toString("utf8");
}

function fmtBytes(n) {
  if (n < 1024) return `${n}B`;
  if (n < 1024 * 1024) return `${(n / 1024).toFixed(1)}KB`;
  return `${(n / 1024 / 1024).toFixed(2)}MB`;
}

function asList(v) {
  return Array.isArray(v) ? v : [];
}

// ── 본체 ──────────────────────────────────────────────────
const args = parseArgs(process.argv.slice(2));

if (args.help || args.h) {
  usage();
  process.exit(0);
}
if (args._rest.length !== 1) {
  usage();
  die(1, `스킬 디렉터리를 정확히 1개 지정하세요. (받음: ${args._rest.length}개)`);
}

const dir = resolve(String(args._rest[0]).replace(/^~(?=$|\/)/, process.env.HOME ?? "~"));
if (!existsSync(dir)) die(3, `디렉터리가 없습니다: ${dir}`);

const category = typeof args.category === "string" ? args.category : undefined;
if (!category) die(1, `--category 는 필수입니다. (${CATEGORIES.join(" | ")})`);
if (!CATEGORIES.includes(category)) {
  die(1, `--category 는 ${CATEGORIES.join(" | ")} 중 하나. (받음: ${category})`);
}

const mode = typeof args.mode === "string" ? args.mode : undefined;
if (mode && mode !== "upsert" && mode !== "replace") {
  die(1, `--mode 는 upsert | replace. (받음: ${mode})`);
}
const deletePaths = (args.delete ?? []).filter(Boolean);
const deletePluginPaths = (args["delete-plugin"] ?? []).filter(Boolean);
if (mode === "replace" && deletePaths.length) {
  die(1, "--mode replace 와 --delete 는 함께 쓸 수 없습니다 (서버가 거부).");
}

const name = (typeof args.name === "string" ? args.name : basename(dir)).trim();
const dryRun = args["dry-run"] === true;
const listOnly = args["list-only"] === true;
const allowDelete = args["allow-delete"] === true;

const { files, pluginFiles } = await collect(dir);
if (files.length === 0) die(3, `발행할 파일이 없습니다: ${dir}`);
if (!files.some((f) => f.rel === "SKILL.md")) {
  die(3, "최상위 SKILL.md 가 필요합니다.");
}

let listing;
if (typeof args.listing === "string") {
  const p = resolve(args.listing);
  if (!existsSync(p)) die(3, `--listing 파일이 없습니다: ${p}`);
  try {
    listing = await readFile(p, "utf8");
  } catch (e) {
    die(3, `--listing 읽기 실패: ${p} — ${e.message}`);
  }
}

// ── 보낼 목록 출력 (전송 전 항상) ─────────────────────────
const totalBytes = [...files, ...pluginFiles].reduce((s, f) => s + f.bytes, 0);
process.stdout.write(
  `▶ ${name}  (mode=${mode ?? "upsert"} · category=${category}${dryRun ? " · DRY RUN" : ""})\n` +
    `  from: ${dir}\n` +
    `  files(${files.length}) ${fmtBytes(totalBytes)} 합계\n` +
    files.map((f) => `      ${f.rel}  ${fmtBytes(f.bytes)}\n`).join("") +
    (pluginFiles.length
      ? `  plugin_files(${pluginFiles.length}) → plugins/${name}/\n` +
        pluginFiles.map((f) => `      ${f.rel}  ${fmtBytes(f.bytes)}\n`).join("")
      : `  plugin_files: 없음 (기존 플러그인 레벨 파일은 서버가 보존)\n`) +
    (deletePaths.length ? `  delete: ${deletePaths.join(", ")}\n` : "") +
    (deletePluginPaths.length
      ? `  delete-plugin: ${deletePluginPaths.join(", ")}\n`
      : ""),
);

if (listOnly) {
  process.stdout.write("(--list-only — 전송하지 않았습니다)\n");
  process.exit(0);
}

// ── 인증·주소 ─────────────────────────────────────────────
const API_KEY =
  (typeof args["api-key"] === "string" ? args["api-key"] : undefined) ??
  process.env.LOGICRAFT_API_KEY;
if (!API_KEY) {
  die(
    2,
    "LOGICRAFT_API_KEY 환경변수 필요(MCP 와 동일한 lc_ 키, write 권한). " +
      "키를 명령 이력에 남기지 않으려면 환경변수를 쓰세요.",
  );
}
const BASE = (
  (typeof args["api-base"] === "string" ? args["api-base"] : undefined) ??
  process.env.LOGICRAFT_API_BASE ??
  "http://localhost:14000/api"
).replace(/\/+$/, "");

// ── 전송 ──────────────────────────────────────────────────
const form = new FormData();
form.append("category", category);
if (mode) form.append("mode", mode);
if (typeof args.changelog === "string") form.append("changelog", args.changelog);
if (typeof args.summary === "string") form.append("summary", args.summary);
if (listing !== undefined) form.append("listing", listing);
if (allowDelete) form.append("allow_delete", "true");
// 서버 stringList() 는 '[' 로 시작하면 JSON 배열로 파싱한다.
if (deletePaths.length) form.append("delete_paths", JSON.stringify(deletePaths));
if (deletePluginPaths.length) {
  form.append("delete_plugin_paths", JSON.stringify(deletePluginPaths));
}
// ★ 파트의 filename 이 곧 상대경로다 (서버 규약). 필드명은 files / plugin_files 두 가지뿐.
for (const f of files) {
  form.append("files", new Blob([await readText(f)]), f.rel);
}
for (const f of pluginFiles) {
  form.append("plugin_files", new Blob([await readText(f)]), f.rel);
}

// dry_run 은 쿼리로도 받는다(서버가 쿼리 우선). 명령·로그에서 가장 눈에 띄는 자리다.
const url =
  `${BASE}/skills/${encodeURIComponent(name)}/publish` +
  (dryRun ? "?dry_run=true" : "");

let res;
try {
  res = await fetch(url, {
    method: "POST",
    headers: { Authorization: `Bearer ${API_KEY}` },
    body: form,
  });
} catch (e) {
  die(2, `요청 실패: ${url} — ${e.message}`);
}

const text = await res.text();
let json;
try {
  json = JSON.parse(text);
} catch {
  json = text;
}

if (!res.ok) {
  const code = typeof json === "object" && json?.code ? json.code : res.status;
  const msg =
    typeof json === "object" && json?.message
      ? typeof json.message === "string"
        ? json.message
        : JSON.stringify(json.message, null, 2)
      : String(text).slice(0, 500);
  const lim =
    typeof json === "object" && json?.limits
      ? `\n서버 상한: ${JSON.stringify(json.limits)}`
      : "";
  die(2, `발행 실패 [${res.status} ${code}]: ${msg}${lim}`);
}

const r = typeof json === "object" && json ? json : {};
// ⚠️ 예행연습 결과를 "발행 완료"처럼 출력하면 안 된다 — 사람이 그걸 보고 끝났다고 믿는다.
const isDry = r.dry_run === true;
process.stdout.write(
  (isDry
    ? `\n🔎 [DRY RUN] ${r.name}@${r.version} — 아무것도 발행하지 않았습니다 (아래는 예측)\n`
    : `\n✅ ${r.name}@${r.version} — commit ${r.commit}\n`) +
    `   written : ${asList(r.files_written).length}건  ${asList(r.files_written).join(", ")}\n` +
    `   kept    : ${r.files_kept ?? "-"}건 (손대지 않고 보존된 기존 파일)\n` +
    `   deleted : ${asList(r.files_deleted).length}건  ${asList(r.files_deleted).join(", ")}\n` +
    (asList(r.files_delete_missing).length
      ? `   (없어서 건너뛴 삭제: ${asList(r.files_delete_missing).join(", ")})\n`
      : "") +
    (asList(r.plugin_files_written).length
      ? `   plugin written : ${asList(r.plugin_files_written).join(", ")}\n`
      : "") +
    (asList(r.plugin_files_deleted).length
      ? `   plugin deleted : ${asList(r.plugin_files_deleted).join(", ")}\n`
      : "") +
    (isDry
      ? `   → 이대로 발행하려면 --dry-run 을 빼고 다시 실행하세요.\n`
      : `   ${r.install_command ?? ""}\n`),
);
process.exit(0);
