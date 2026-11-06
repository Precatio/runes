import { readFileSync } from "node:fs";
import { join } from "node:path";

// The released version, read when the site is built from CITATION.cff in the project root – the file each release
// updates (RELEASING.md), so the start page always shows the latest version. Only for server components.
function cff(): string {
  try {
    return readFileSync(join(process.cwd(), "..", "CITATION.cff"), "utf8");
  } catch {
    return "";
  }
}
const CFF = cff();

export const VERSION = /^version:\s*"?([0-9][^"\s]*)"?\s*$/m.exec(CFF)?.[1] ?? "3.0.0";
// Zenodo: doi is the DOI for all versions (it always resolves to the latest); the identifier described "Version X" is
// this release's own DOI, which a citation of the version should use
export const CONCEPT_DOI = /^doi:\s*"?([^"\s]+)"?\s*$/m.exec(CFF)?.[1] ?? null;
export const VERSION_DOI = new RegExp(`value:\\s*"?([^"\\s]+)"?\\s*\\n\\s*description:\\s*"Version ${VERSION.replace(/\./g, "\\.")}"`).exec(CFF)?.[1] ?? CONCEPT_DOI;
