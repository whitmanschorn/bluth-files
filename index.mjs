// bluth-files — programmatic access to the committed datasets, plus paths to
// the locally generated layers (run `npx bluth-files fetch && npx bluth-files
// build` once per install to materialize those; see README).

import { readFileSync, readdirSync, existsSync } from "node:fs";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";

export const root = dirname(fileURLToPath(import.meta.url));

const json = (p) => JSON.parse(readFileSync(join(root, p), "utf8"));
const jsonl = (p) =>
  readFileSync(join(root, p), "utf8").trim().split("\n").map(JSON.parse);

// committed data — always available
export const people = () => json("data/family/people.json");
export const relationships = () => json("data/family/relationships.json");
export const locations = () => json("data/family/locations.json");
export const lifeEvents = () => json("data/family/life-events.json");
export const episodes = () => json("data/family/episodes.json");
export const photoManifest = () => json("data/photos/manifest.json");
export const evalQuestions = () => jsonl("rag/eval/questions.jsonl");
export const transcriptLock = () => json("data/transcripts.lock.json");

// generated locally by `npx bluth-files fetch && npx bluth-files build`
export const paths = {
  transcripts: join(root, "data", "transcripts"),
  corpus: join(root, "corpus"),
  seed: join(root, "out", "seed"),
  pdfs: join(root, "out", "pdf"),
};

export const isBuilt = () => existsSync(paths.corpus);

export const corpus = (name) => jsonl(join("corpus", `${name}.jsonl`));

export const seedTables = () => {
  if (!existsSync(paths.seed)) {
    throw new Error("seed not built — run: npx bluth-files fetch && npx bluth-files build");
  }
  return Object.fromEntries(
    readdirSync(paths.seed)
      .filter((f) => f.endsWith(".json"))
      .map((f) => [f.replace(/\.json$/, ""), json(join("out", "seed", f))])
  );
};
