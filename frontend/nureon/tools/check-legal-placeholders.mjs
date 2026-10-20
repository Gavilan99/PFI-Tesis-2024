// Fails if the production build still carries a legal placeholder.
//
//     npm run test:legal      (builds production, then runs this)
//     node tools/check-legal-placeholders.mjs [dist folder]
//
// The privacy policy and the terms name the database's responsible party and
// a contact address that are not decided yet. Until they are, they live in
// src/app/legal/legal-content.ts as visible markers. Releasing with a marker
// in place would publish "[RESPONSABLE]" as the legal answer to "who is
// responsible for my data": this check reads every file the build produced
// (browser bundles, server bundles, prerendered HTML) and fails on any of
// them. backend/infra/11-frontend-deploy.ps1 runs it after its build.

import { readdirSync, readFileSync, statSync, existsSync } from 'node:fs';
import { join, relative, resolve } from 'node:path';
import { fileURLToPath } from 'node:url';

const MARKERS = ['[RESPONSABLE]', '[CONTACTO]'];

const appDir = resolve(fileURLToPath(new URL('..', import.meta.url)));
const dist = resolve(process.argv[2] ?? join(appDir, 'dist', 'nureon'));

function filesUnder(folder) {
  return readdirSync(folder).flatMap((name) => {
    const path = join(folder, name);
    return statSync(path).isDirectory() ? filesUnder(path) : [path];
  });
}

// A check that finds nothing because it looked in the wrong place must not pass.
const privacyPage = join(dist, 'browser', 'privacidad', 'index.html');
if (!existsSync(privacyPage)) {
  console.error(`No está la página prerenderizada de privacidad: ${privacyPage}`);
  console.error('Construí producción antes (npm run test:legal lo hace).');
  process.exit(2);
}

const files = filesUnder(dist).filter((path) => /\.(html|js|mjs|json|txt)$/.test(path));
const found = [];
for (const path of files) {
  const content = readFileSync(path, 'utf8');
  for (const marker of MARKERS) {
    if (content.includes(marker)) {
      found.push(`  ${marker} en ${relative(dist, path)}`);
    }
  }
}

if (found.length > 0) {
  console.error(`El build de producción tiene ${found.length} marcador(es) legal(es) sin completar:`);
  console.error(found.join('\n'));
  console.error('Completalos en src/app/legal/legal-content.ts antes del release.');
  process.exit(1);
}
console.log(`Sin marcadores legales en ${files.length} archivos de ${relative(appDir, dist)}.`);
