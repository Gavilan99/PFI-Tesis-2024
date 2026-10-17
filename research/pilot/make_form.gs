/**
 * NureonAI — generates the training-data collection Form from the consolidated bank.
 *
 * WHY A SCRIPT: 145 questions × 3–5 options is ~533 fields. Hand-entering them would
 * introduce transcription errors into the one dataset there is time to collect, and
 * would break the question_id ↔ response mapping the training pipeline depends on.
 *
 * ── SETUP ──────────────────────────────────────────────────────────────────────
 * 1. Upload "NureonAI Prototype v4.1.2.csv" to Google Drive. Upload it AS-IS. Do not open it in Sheets or Excel first — a Spanish-locale
 *    re-save rewrites it with semicolon delimiters and cp1252 encoding, which
 *    silently corrupts every accented character you just spent an evening fixing.
 * 2. script.google.com → New project → paste this file → Save.
 * 3. Run buildForm(). Authorise when prompted (it needs Drive + Forms access).
 * 4. The execution log prints the form's edit and share URLs.
 *
 * Runtime is ~2–4 min. Apps Script caps at 6 min; if it times out, see RESUME below.
 *
 * ── QUÉ CAMBIÓ RESPECTO DE LA VERSIÓN DE AGOSTO ────────────────────────────────
 * Aquella versión servía el banco v1 (200 ítems, subset de 120 administrado, todo
 * escenario). Ésta sirve el prototipo consolidado: 145 ítems, de los cuales **49 son
 * Likert**. Tres consecuencias, las tres deliberadas:
 *
 *   1. LOS LIKERT VAN COMO MULTIPLE CHOICE, no como ScaleItem. Parece peor UX y es la
 *      decisión correcta: parse_form_export.py mapea las respuestas por COINCIDENCIA
 *      EXACTA DEL TEXTO de la opción, y el CSV ya trae las cinco anclas como filas con
 *      su display_order 1..5. Con ScaleItem el export devolvería enteros y el parser
 *      dejaría de matchear. Un solo camino de código, un solo formato de export, el
 *      parser sin tocar.
 *
 *   2. EL INTERCALADO AHORA MIRA TAMBIÉN EL FORMATO. El de agosto intercalaba sólo por
 *      conjunto, porque el banco era todo escenario. Corrido sobre este banco producía
 *      **rachas de hasta 17 ítems del mismo formato** y 9 Likert entre los primeros 20.
 *      Eso es exactamente el "block-level response set" que el intercalado existe para
 *      evitar — acomodarse a un patrón y quedarse ahí — sólo que en la dimensión que
 *      más se nota: la acción de responder cambia por completo entre los dos formatos.
 *      Medido con el reparto nuevo, semilla 20260921, sobre el CSV real:
 *        racha máxima de formato 4 · de conjunto 1
 *        Likert por tercio 17/17/15 · 7 Likert entre los primeros 20 (ideal 6.8)
 *        conjunto por tercio 12-13 para los cuatro
 *
 *   3. EL TEXTO DE AYUDA ES POR ÍTEM, no por página. "Elegí la opción que más se
 *      parezca a vos" no aplica a una escala de acuerdo.
 *
 * ── v4.1.1 (2026-10-07) ────────────────────────────────────────────────────────
 * Ver "PDR — NureonAI Mid-Collection Rewording of Observed Items". 8 ítems se
 * reescribieron EN EL FORMULARIO VIVO, a mano, sólo en la forma y con el mismo id
 * (16 opciones, 4 enunciados). El 2026-10-08 se sumó una segunda ronda, v4.1.2:
 * revisión general del banco, 14 ítems más, sólo cambios A/B. Este script construye la
 * última versión: lee "NureonAI Prototype v4.1.2.csv", que es v4.1 con todos los textos
 * de qbank/bank_aliases.json aplicados ("…v4.1.1.csv" queda con la primera ronda sola).
 * Mismos ids, mismo orden, misma forma (145 / 533), así que el intercalado da
 * exactamente el mismo orden de preguntas que el formulario vivo.
 *
 * NUNCA CORRER buildForm() SOBRE LA RECOLECCIÓN EN CURSO. Crea un formulario NUEVO, con
 * otro link: se pierden los borradores guardados y deja de servir el link enviado a los
 * reclutados. Esto existe para reconstruir el instrumento si hiciera falta (otra tanda,
 * otra cuenta), no para editarlo. Los cambios al formulario vivo se hacen a mano.
 */

// ── CONFIG ────────────────────────────────────────────────────────────────────
var CSV_NAME       = 'NureonAI Prototype v4.1.2.csv';   // v4.1 + bank_aliases.json, rondas v4.1.1 y v4.1.2
var FORM_TITLE     = 'NureonAI — Cuestionario de personalidad';
var ITEMS_PER_PAGE = 20;            // 145 preguntas → 8 secciones
var INTERLEAVE     = true;
var SHUFFLE_SEED   = 20260921;

// Forma esperada del banco — el script se niega a construir si no coincide, así un
// CSV equivocado o corrupto falla ruidosamente en vez de producir un form sutilmente roto.
var EXPECT_QUESTIONS = 145;
var EXPECT_ROWS      = 533;

// ── CONSENT (Ley 25.326) ──────────────────────────────────────────────────────
var CONSENT_TEXT =
  'Este cuestionario forma parte del Proyecto Final de Ingeniería en Informática ' +
  '(UADE) de Tobías Vodopivec y Juan Manuel Gavilán.\n\n' +
  'FINALIDAD. Tus respuestas se usan únicamente para entrenar y evaluar un modelo ' +
  'de identificación de tipos de personalidad según la Teoría del Eneagrama, en el ' +
  'marco académico de este proyecto.\n\n' +
  'DATOS. No se solicitan nombre, correo ni datos de contacto en este formulario. ' +
  'Tus respuestas se identifican con un código que te entregamos por separado.\n\n' +
  'CONSERVACIÓN Y DERECHOS. Los datos se conservan mientras dure el proyecto y su ' +
  'evaluación académica. Conforme a la Ley 25.326 podés solicitar en cualquier ' +
  'momento el acceso, la rectificación o la supresión de tus datos escribiéndonos; ' +
  'en ese caso se eliminará tu identificación y las respuestas quedarán anonimizadas.\n\n' +
  'PARTICIPACIÓN. Es voluntaria y podés abandonar el cuestionario en cualquier momento.';

var FORM_DESCRIPTION =
  // "alrededor de una hora": medido, no estimado. El piloto del 21-09 dio 60 min
  // exactos sobre 145 ítems (24.8 s/ítem), por encima de los 23 s/ítem de los dos
  // pilotos anteriores. La estimación de 20 s/ítem (~48 min) era optimista, y la
  // hipótesis de que los 49 Likert acelerarían la lectura se murió con el dato.
  'Son 145 preguntas y lleva alrededor de una hora. No hay respuestas correctas ni ' +
  'incorrectas.\n\n' +
  'Vas a encontrar dos tipos de pregunta, mezclados:\n' +
  '• situaciones con tres opciones — elegí la que más se parezca a vos, aunque ' +
  'ninguna encaje del todo;\n' +
  '• afirmaciones con una escala — marcá cuánto acordás con lo que dice.\n\n' +
  'Podés cortar cuando quieras y retomar más tarde desde el mismo dispositivo; ' +
  'no hace falta hacerlo de una sentada.\n\n' +
  'Respondé rápido y con la primera reacción. Pensarlo demasiado suele dar un ' +
  'resultado menos preciso.';

var HELP_SCENARIO = 'Elegí la que más se parezca a vos, aunque ninguna encaje del todo.';
var HELP_LIKERT   = 'Marcá cuánto acordás con la afirmación.';

// ── META (covariables de familiaridad) ────────────────────────────────────────
// Van AL FINAL, nunca al principio: preguntar por el Eneagrama antes de las 145 es
// sugerirlo. Existen para poder reportar la precisión PARTIDA POR FAMILIARIDAD — si
// el clasificador rinde mucho mejor con los que conocen el sistema, aprendió
// autopercepción y no motivación, que es el modo de falla contra el que está
// posicionado el proyecto. Los ids META# no matchean el patrón Q\d{3} del banco;
// parse_form_export.py los levanta por separado.
var META_SECTION_TITLE = 'Últimas tres preguntas';
var META_SECTION_HELP =
  'Listo, ya terminaste las 145. Estas tres son sobre vos, no sobre situaciones.\n\n' +
  'Nos sirven para chequear si conocer el Eneagrama cambia la forma de responder. ' +
  'No hay respuesta mejor ni peor, y ninguna cambia nada de lo que ya contestaste: ' +
  'contestá con lo que realmente pasó.';

var META_QUESTIONS = [
  { id: 'META1',
    title: '¿Cuánto conocés el Eneagrama?',
    help: '',
    required: true,
    choices: ['Nada', 'Algo, de oído', 'Bastante', 'Mucho, lo estudié'] },
  { id: 'META2',
    title: '¿Te considerás de algún tipo en particular?',
    help: 'Si no conocés el sistema o nunca te lo planteaste, marcá la última opción.',
    required: false,
    // Sólo números: nombrar los tipos importaría una taxonomía concreta (y la de quién)
    // a un dato que solo necesita ser comparable con la tipificación del equipo.
    choices: ['Tipo 1', 'Tipo 2', 'Tipo 3', 'Tipo 4', 'Tipo 5', 'Tipo 6',
              'Tipo 7', 'Tipo 8', 'Tipo 9',
              'Dudo entre dos', 'No sé / no me considero de ninguno'] },
  { id: 'META3',
    title: 'Mientras respondías, ¿intentaste identificar a qué tipo apuntaba alguna pregunta?',
    help: 'Contestá con franqueza: es información útil, no un error tuyo.',
    required: true,
    choices: ['No, en ningún momento', 'Alguna vez', 'Bastante seguido'] }
];

// ── MAIN ──────────────────────────────────────────────────────────────────────
function buildForm() {
  var bank = loadBank_();
  Logger.log('Bank loaded: %s questions, %s option rows',
             bank.order.length, bank.rowCount);

  if (bank.order.length !== EXPECT_QUESTIONS || bank.rowCount !== EXPECT_ROWS) {
    throw new Error(
      'Bank shape mismatch. Expected ' + EXPECT_QUESTIONS + ' questions / ' +
      EXPECT_ROWS + ' rows, got ' + bank.order.length + ' / ' + bank.rowCount +
      '. Estás usando una versión superseded (v1, v1.1, v1.2, el subset de 120) ' +
      'o un CSV corrupto. Usá el archivo que escribe build.py, sin abrirlo.');
  }

  var counts = formatCounts_(bank);
  Logger.log('Formats: %s scenario / %s likert', counts.scenario, counts.likert);

  var order = INTERLEAVE ? interleave_(bank) : bank.order;
  logSpread_(bank, order);

  var form = FormApp.create(FORM_TITLE);
  form.setDescription(FORM_DESCRIPTION)
      .setProgressBar(true)
      .setCollectEmail(false)      // identity travels via the código, not the account
      .setLimitOneResponsePerUser(false)
      .setAllowResponseEdits(false)
      .setShowLinkToRespondAgain(false);

  // --- consent gate ---
  form.addSectionHeaderItem()
      .setTitle('Consentimiento informado')
      .setHelpText(CONSENT_TEXT);

  form.addMultipleChoiceItem()
      .setTitle('CONSENT — ¿Aceptás participar en estas condiciones?')
      .setChoiceValues(['Sí, acepto participar'])
      .setRequired(true);

  // Validación por regex. Sin esto, un campo de texto libre acepta cualquier cosa: en el
  // piloto alguien escribió un alias en vez de su código y hubo que corregirlo después,
  // a mano, en code_fixes.json. El patrón tolera espacios al borde y minúscula —el
  // parser normaliza— y rechaza todo lo que no tenga forma de código.
  var codigoOk = FormApp.createTextValidation()
      .setHelpText('Tiene que ser la letra R seguida de tres números, como R017. ' +
                   'No es un apodo ni tu nombre: es el código que te enviamos.')
      .requireTextMatchesPattern('\\s*[Rr]\\d{3}\\s*')
      .build();

  form.addTextItem()
      .setTitle('CODIGO — Código de participante')
      .setHelpText('El código que te enviamos al invitarte, con forma R + tres números ' +
                   '(por ejemplo R017). No es un apodo ni tu nombre. Sirve para vincular ' +
                   'este cuestionario con la entrevista sin tener que usar tus datos.')
      .setValidation(codigoOk)
      .setRequired(true);

  // --- questions ---
  var n = 0;
  for (var i = 0; i < order.length; i++) {
    if (n % ITEMS_PER_PAGE === 0) {
      var page = Math.floor(n / ITEMS_PER_PAGE) + 1;
      var total = Math.ceil(order.length / ITEMS_PER_PAGE);
      form.addPageBreakItem()
          .setTitle('Parte ' + page + ' de ' + total)
          .setHelpText('Hay dos tipos de pregunta mezclados. Cada una dice abajo qué hacer.');
    }
    addQuestion_(form, bank.byId[order[i]]);
    n++;
  }

  addMetaQuestions_(form);

  Logger.log('DONE — %s questions written + %s meta', n, META_QUESTIONS.length);
  Logger.log('EDIT  : %s', form.getEditUrl());
  Logger.log('SHARE : %s', form.getPublishedUrl());
  Logger.log('Next: pilot on 2-3 people, TIME IT, and run parse_form_export.py on the ' +
             'export BEFORE recruiting at volume. Ojo: parse_form_export.py todavía ' +
             'apunta al banco v1 — hay que repuntarlo al prototipo antes de parsear.');
}

/**
 * RESUME — if buildForm() times out partway through.
 * Open the partly-built form, note how many questions it already has, and run
 * resumeForm('<form edit url>', <count already written>).
 */
function resumeForm(editUrl, alreadyWritten) {
  var bank = loadBank_();
  var order = INTERLEAVE ? interleave_(bank) : bank.order;
  var form = FormApp.openByUrl(editUrl);
  var n = alreadyWritten;
  for (var i = alreadyWritten; i < order.length; i++) {
    if (n % ITEMS_PER_PAGE === 0) {
      var page = Math.floor(n / ITEMS_PER_PAGE) + 1;
      var total = Math.ceil(order.length / ITEMS_PER_PAGE);
      form.addPageBreakItem().setTitle('Parte ' + page + ' de ' + total);
    }
    addQuestion_(form, bank.byId[order[i]]);
    n++;
  }
  addMetaQuestions_(form);
  Logger.log('Resumed. Total questions now: %s (+ %s meta)', n, META_QUESTIONS.length);
}

// ── HELPERS ───────────────────────────────────────────────────────────────────

function addQuestion_(form, q) {
  // The question_id MUST lead the title: Forms exports use the title as the column
  // header, and it is the only thing linking a response back to the bank.
  var item = form.addMultipleChoiceItem()
      .setTitle(q.id + ' — ' + q.prompt)
      .setHelpText(q.format === 'likert' ? HELP_LIKERT : HELP_SCENARIO)
      .setRequired(true);

  var choices = q.options.map(function (o) { return o.text; });
  item.setChoiceValues(choices);
  // Deliberately NOT shuffling: option order was already de-confounded from
  // group_label when the bank was built, with a fixed seed (χ² = 0 en los cuatro
  // conjuntos). Y en los Likert el orden ES la escala: barajarlo la destruiría.
  return item;
}

/** Las tres covariables de familiaridad, en su propia sección final. */
function addMetaQuestions_(form) {
  form.addPageBreakItem()
      .setTitle(META_SECTION_TITLE)
      .setHelpText(META_SECTION_HELP);

  for (var i = 0; i < META_QUESTIONS.length; i++) {
    var m = META_QUESTIONS[i];
    var item = form.addMultipleChoiceItem()
        .setTitle(m.id + ' — ' + m.title)   // el id va primero, igual que en el banco
        .setChoiceValues(m.choices)
        .setRequired(m.required);
    if (m.help) item.setHelpText(m.help);
  }
}

function formatCounts_(bank) {
  var c = { scenario: 0, likert: 0 };
  bank.order.forEach(function (id) {
    var f = bank.byId[id].format;
    c[f] = (c[f] || 0) + 1;
  });
  return c;
}

function loadBank_() {
  var files = DriveApp.getFilesByName(CSV_NAME);
  if (!files.hasNext()) {
    throw new Error('Not found in Drive: ' + CSV_NAME);
  }
  var file = files.next();
  if (files.hasNext()) {
    throw new Error('Multiple files named ' + CSV_NAME +
                    ' in Drive. Remove the duplicates so the right bank is unambiguous.');
  }

  // UTF-8 is explicit and load-bearing: without it the accents come through as mojibake.
  var text = file.getBlob().getDataAsString('UTF-8');
  var rows = Utilities.parseCsv(text);
  var head = rows[0];

  var col = {};
  for (var c = 0; c < head.length; c++) col[head[c].trim()] = c;
  ['question_id', 'prompt', 'option_text', 'display_order', 'grouping_system', 'format']
    .forEach(function (k) {
      if (col[k] === undefined) throw new Error('CSV missing column: ' + k);
    });

  var byId = {}, order = [], rowCount = 0;
  for (var r = 1; r < rows.length; r++) {
    var row = rows[r];
    if (!row[col.question_id]) continue;
    rowCount++;
    var id = row[col.question_id];
    if (!byId[id]) {
      byId[id] = { id: id, prompt: row[col.prompt],
                   system: row[col.grouping_system],
                   format: row[col.format],
                   options: [] };
      order.push(id);
    }
    byId[id].options.push({ text: row[col.option_text],
                            ord: parseInt(row[col.display_order], 10) });
  }
  order.forEach(function (id) {
    byId[id].options.sort(function (a, b) { return a.ord - b.ord; });
  });

  return { byId: byId, order: order, rowCount: rowCount };
}

/**
 * Intercala por CONJUNTO **y por FORMATO**.
 *
 * Ocho baldes (4 conjuntos × 2 formatos), barajados con semilla fija, y repartidos
 * por mayor déficit respecto de su cuota — el reparto proporcional clásico, con una
 * penalización al balde que repetiría el conjunto o el formato de la pregunta
 * anterior. Determinista: misma semilla → mismo orden, form reproducible.
 *
 * La versión anterior sólo miraba el conjunto, que alcanzaba cuando el banco era todo
 * escenario. Sobre este banco dejaba rachas de 17 ítems del mismo formato.
 */
function interleave_(bank) {
  var buckets = {}, keys = [];
  bank.order.forEach(function (id) {
    var q = bank.byId[id];
    var k = q.system + '||' + q.format;
    if (!buckets[k]) { buckets[k] = []; keys.push(k); }
    buckets[k].push(id);
  });
  keys.forEach(function (k) { buckets[k] = shuffle_(buckets[k], SHUFFLE_SEED); });

  var total = bank.order.length;
  var taken = {}, size = {};
  keys.forEach(function (k) { taken[k] = 0; size[k] = buckets[k].length; });

  var out = [], prevSystem = null, prevFormat = null;
  for (var pos = 0; pos < total; pos++) {
    var best = null, bestScore = -Infinity;
    for (var i = 0; i < keys.length; i++) {
      var k = keys[i];
      if (taken[k] >= size[k]) continue;
      var parts = k.split('||');
      // cuánto le falta a este balde para estar al día con su cuota
      var score = (pos + 1) * size[k] / total - taken[k];
      if (parts[1] === prevFormat) score -= 0.35;   // no repetir formato
      if (parts[0] === prevSystem) score -= 0.60;   // no repetir conjunto
      if (score > bestScore) { bestScore = score; best = k; }
    }
    var id = buckets[best][taken[best]++];
    out.push(id);
    prevSystem = bank.byId[id].system;
    prevFormat = bank.byId[id].format;
  }
  return out;
}

/** Imprime el reparto real para poder verificarlo antes de mandar el form. */
function logSpread_(bank, order) {
  var maxFmt = 1, maxSys = 1, runF = 1, runS = 1;
  for (var i = 1; i < order.length; i++) {
    var a = bank.byId[order[i - 1]], b = bank.byId[order[i]];
    runF = (a.format === b.format) ? runF + 1 : 1;
    runS = (a.system === b.system) ? runS + 1 : 1;
    if (runF > maxFmt) maxFmt = runF;
    if (runS > maxSys) maxSys = runS;
  }
  Logger.log('Spread — racha máxima mismo formato: %s · mismo conjunto: %s', maxFmt, maxSys);

  var third = Math.ceil(order.length / 3), lk = [0, 0, 0];
  for (var j = 0; j < order.length; j++) {
    if (bank.byId[order[j]].format === 'likert') lk[Math.floor(j / third)]++;
  }
  Logger.log('Likert por tercio: %s', lk.join(' / '));
}

/** Deterministic shuffle (mulberry32) — Apps Script has no seedable RNG. */
function shuffle_(arr, seed) {
  var a = arr.slice(), t = seed >>> 0;
  function rnd() {
    t += 0x6D2B79F5;
    var x = t;
    x = Math.imul(x ^ (x >>> 15), x | 1);
    x ^= x + Math.imul(x ^ (x >>> 7), x | 61);
    return ((x ^ (x >>> 14)) >>> 0) / 4294967296;
  }
  for (var i = a.length - 1; i > 0; i--) {
    var j = Math.floor(rnd() * (i + 1));
    var tmp = a[i]; a[i] = a[j]; a[j] = tmp;
  }
  return a;
}
