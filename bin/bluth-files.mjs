#!/usr/bin/env node
// CLI for the bluth-files data pipeline. Wraps the stdlib-only Python
// scripts (python3 required):
//
//   bluth-files fetch    rebuild transcripts from lock-pinned wiki revisions
//   bluth-files build    corpus chunks + manuscript PDFs + Hope Chest seed
//   bluth-files verify   checksum data/transcripts/ against the lockfile
//   bluth-files all      fetch + build + verify

import { spawnSync } from "node:child_process";
import { createHash } from "node:crypto";
import { readFileSync, readdirSync, existsSync } from "node:fs";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";

const root = join(dirname(fileURLToPath(import.meta.url)), "..");

function py(script, ...args) {
  const r = spawnSync("python3", [join(root, "scripts", script), ...args], {
    stdio: "inherit",
  });
  if (r.error?.code === "ENOENT") {
    console.error("python3 not found — the pipeline needs Python 3.10+ (stdlib only)");
    process.exit(1);
  }
  if (r.status !== 0) process.exit(r.status ?? 1);
}

function verify() {
  const lock = JSON.parse(
    readFileSync(join(root, "data", "transcripts.lock.json"), "utf8"));
  const dir = join(root, "data", "transcripts");
  if (!existsSync(dir)) {
    console.error("data/transcripts/ missing — run: bluth-files fetch");
    process.exit(1);
  }
  const byCode = Object.fromEntries(
    readdirSync(dir).filter((f) => f.endsWith(".md"))
      .map((f) => [f.slice(0, 6), f]));
  let bad = 0;
  for (const [code, pin] of Object.entries(lock)) {
    const file = byCode[code];
    const sha = file &&
      createHash("sha256").update(readFileSync(join(dir, file))).digest("hex");
    if (sha !== pin.sha256) {
      console.error(`MISMATCH ${code} (${file ?? "missing"})`);
      bad++;
    }
  }
  const n = Object.keys(lock).length;
  console.log(bad ? `${bad}/${n} transcripts FAILED verification`
                  : `${n}/${n} transcripts verified against lock`);
  process.exit(bad ? 1 : 0);
}

const cmd = process.argv[2];
switch (cmd) {
  case "fetch":
    py("fetch_transcripts.py", ...process.argv.slice(3));
    break;
  case "build":
    py("build_corpus.py");
    py("make_pdfs.py");
    py("export_seed.py");
    break;
  case "verify":
    verify();
    break;
  case "all":
    py("fetch_transcripts.py");
    py("build_corpus.py");
    py("make_pdfs.py");
    py("export_seed.py");
    verify();
    break;
  default:
    console.log("usage: bluth-files <fetch|build|verify|all>");
    process.exit(cmd ? 1 : 0);
}
