#!/usr/bin/env node

const { spawnSync } = require("node:child_process");
const { existsSync } = require("node:fs");
const path = require("node:path");

const root = path.resolve(__dirname, "..");

const targets = {
  codex: path.join(root, "scripts", "install_codex_plugin.py"),
  gemini: path.join(root, "scripts", "install_gemini_extension.py"),
  qwen: path.join(root, "scripts", "install_qwen_extension.py"),
  all: path.join(root, "scripts", "install_real_env.py"),
};

function printUsage() {
  console.log(`Usage:
  npx @xinsd/cli-notice all
  npx @xinsd/cli-notice codex
  npx @xinsd/cli-notice gemini
  npx @xinsd/cli-notice qwen

Notes:
  - "all" installs Codex, Gemini, and Qwen integrations
  - each installer creates a backup and rollback script under backups/<timestamp>/`);
}

function detectPython() {
  for (const candidate of ["python3", "python"]) {
    const probe = spawnSync(candidate, ["--version"], { stdio: "ignore" });
    if (probe.status === 0) {
      return candidate;
    }
  }
  return null;
}

const arg = process.argv[2];
if (!arg || arg === "-h" || arg === "--help" || arg === "help") {
  printUsage();
  process.exit(0);
}

if (!Object.hasOwn(targets, arg)) {
  console.error(`Unknown target: ${arg}`);
  printUsage();
  process.exit(1);
}

const scriptPath = targets[arg];
if (!existsSync(scriptPath)) {
  console.error(`Installer script not found: ${scriptPath}`);
  process.exit(1);
}

const python = detectPython();
if (!python) {
  console.error("Python 3 is required but was not found as python3 or python.");
  process.exit(1);
}

const result = spawnSync(python, [scriptPath], {
  cwd: root,
  stdio: "inherit",
});

if (typeof result.status === "number") {
  process.exit(result.status);
}

console.error("Installer process did not return a normal exit status.");
process.exit(1);
