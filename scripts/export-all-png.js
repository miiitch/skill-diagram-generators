#!/usr/bin/env node
/**
 * export-all-png.js
 * Convertit tous les SVGs Azure en PNGs en conservant la même arborescence.
 *
 * Usage:
 *   node export-all-png.js
 *   node export-all-png.js --svg-dir ../svg/Icons --png-dir ../png --size 48
 */

const sharp = require("sharp");
const fs    = require("fs");
const path  = require("path");

// ── Arguments ──────────────────────────────────────────────────────────────
const args = process.argv.slice(2);
function arg(flag, def) {
  const i = args.indexOf(flag);
  return i !== -1 ? args[i + 1] : def;
}

const svgRoot = path.resolve(__dirname, arg("--svg-dir", "../svg/Icons"));
const pngRoot = path.resolve(__dirname, arg("--png-dir", "../png/Icons"));
const size    = parseInt(arg("--size", "48"), 10);

// ── Helpers ────────────────────────────────────────────────────────────────
function walkSvgs(dir, results = []) {
  for (const entry of fs.readdirSync(dir, { withFileTypes: true })) {
    const full = path.join(dir, entry.name);
    if (entry.isDirectory()) walkSvgs(full, results);
    else if (entry.name.toLowerCase().endsWith(".svg")) results.push(full);
  }
  return results;
}

async function convertOne(svgPath) {
  const rel     = path.relative(svgRoot, svgPath);
  const pngPath = path.join(pngRoot, rel.replace(/\.svg$/i, ".png"));
  fs.mkdirSync(path.dirname(pngPath), { recursive: true });
  await sharp(fs.readFileSync(svgPath))
    .resize(size, size)
    .png()
    .toFile(pngPath);
  return pngPath;
}

// ── Main ───────────────────────────────────────────────────────────────────
(async () => {
  if (!fs.existsSync(svgRoot)) {
    console.error(`ERROR: svg-dir introuvable : ${svgRoot}`);
    process.exit(1);
  }

  const svgs  = walkSvgs(svgRoot);
  const total = svgs.length;
  console.log(`SVGs trouvés : ${total}  →  PNG dans : ${pngRoot}  (${size}×${size}px)`);

  let ok = 0;
  const errors = [];

  for (let i = 0; i < svgs.length; i++) {
    const svgPath = svgs[i];
    const rel = path.relative(svgRoot, svgPath);
    try {
      await convertOne(svgPath);
      ok++;
      process.stdout.write(`  [${String(i + 1).padStart(3)}/${total}] ${rel}\r`);
    } catch (err) {
      errors.push({ rel, err: err.message });
      console.error(`\n  [ERR] ${rel}: ${err.message}`);
    }
  }

  console.log(`\nTerminé : ${ok} OK, ${errors.length} erreurs`);
  if (errors.length) {
    errors.forEach(({ rel, err }) => console.error(`  ${rel}: ${err}`));
    process.exit(1);
  }
})();
