import { readFileSync } from "node:fs";
import { resolve } from "node:path";
import ts from "typescript";

const filePath = resolve(process.cwd(), "src/lib/api.ts");
const source = readFileSync(filePath, "utf8");

const sf = ts.createSourceFile(
  filePath,
  source,
  ts.ScriptTarget.Latest,
  true,
  ts.ScriptKind.TS,
);

let apiBaseDecl = null;
let apiFetchDecl = null;

function walk(node) {
  if (ts.isVariableDeclaration(node) && ts.isIdentifier(node.name)) {
    if (node.name.text === "API_BASE") {
      apiBaseDecl = node;
    }
    if (node.name.text === "apiFetch") {
      apiFetchDecl = node;
    }
  }
  if (ts.isFunctionDeclaration(node) && node.name) {
    if (node.name.text === "apiFetch") {
      apiFetchDecl = node;
    }
  }
  ts.forEachChild(node, walk);
}

walk(sf);

if (!apiBaseDecl) {
  console.error(`Expected API_BASE declaration in ${filePath}.`);
  process.exit(1);
}

if (!apiFetchDecl) {
  console.error(`Expected apiFetch declaration in ${filePath}.`);
  process.exit(1);
}

const apiBaseText = apiBaseDecl.initializer
  ? apiBaseDecl.initializer.getText(sf).replace(/\s+/g, " ")
  : "";
const apiFetchText = apiFetchDecl.body
  ? apiFetchDecl.body.getText(sf).replace(/\s+/g, " ")
  : apiFetchDecl.initializer
    ? apiFetchDecl.initializer.getText(sf).replace(/\s+/g, " ")
    : "";

if (!apiBaseText.includes("VITE_API_BASE_URL")) {
  console.error("API_BASE must read from VITE_API_BASE_URL.");
  process.exit(1);
}

if (!apiFetchText.includes("fetch(`${API_BASE}${path}`")) {
  console.error("apiFetch must route requests through API_BASE.");
  process.exit(1);
}

console.log("API client sanity check passed.");
