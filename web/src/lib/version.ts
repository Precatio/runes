import { readFileSync } from "node:fs";
import { join } from "node:path";

// The released version, read when the site is built from CITATION.cff in the project root – the file each release
// updates (RELEASING.md), so the start page always shows the latest version. Only for server components.
function read(): string {
  try {
    const cff = readFileSync(join(process.cwd(), "..", "CITATION.cff"), "utf8");
    return /^version:\s*"?([0-9][^"\s]*)"?\s*$/m.exec(cff)?.[1] ?? "2.0.0";
  } catch {
    return "2.0.0";
  }
}

export const VERSION = read();
