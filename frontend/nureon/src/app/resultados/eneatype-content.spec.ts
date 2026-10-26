import { ENEATYPE_CONTENT, ENEATYPE_NUMBERS, TRIADS } from './eneatype-content';

// Five words in a row in common is already a copied phrase, not two texts
// that happen to talk about the same type.
const COPIED_RUN = 5;

function words(text: string): string[] {
  return text
    .toLowerCase()
    .replace(/[^\p{L}\p{N}\s]/gu, ' ')
    .split(/\s+/)
    .filter(Boolean);
}

function runs(text: string): Set<string> {
  const all = words(text);
  const result = new Set<string>();
  for (let i = 0; i + COPIED_RUN <= all.length; i++) {
    result.add(all.slice(i, i + COPIED_RUN).join(' '));
  }
  return result;
}

describe('ENEATYPE_CONTENT', () => {
  // The result's text, every type's: the free page of one type shouldn't
  // echo the paid text of any.
  const resultRuns = new Set<string>();
  for (const n of ENEATYPE_NUMBERS) {
    const c = ENEATYPE_CONTENT[n];
    for (const text of [c.summary, c.coreMotivation, ...c.strengths, ...c.tensions, c.growth, c.stress]) {
      runs(text).forEach((run) => resultRuns.add(run));
    }
  }

  for (const n of ENEATYPE_NUMBERS) {
    it(`keeps eneatype ${n}'s public page apart from the result's text`, () => {
      const { strengths, weaknesses, growth, tensions } = ENEATYPE_CONTENT[n].page;
      for (const text of [...strengths, ...weaknesses, ...growth, ...tensions]) {
        const copied = [...runs(text)].filter((run) => resultRuns.has(run));
        expect(copied).withContext(text).toEqual([]);
      }
    });

    it(`gives eneatype ${n} three or four short points per section`, () => {
      for (const section of Object.values(ENEATYPE_CONTENT[n].page)) {
        expect(section.length).toBeGreaterThanOrEqual(3);
        expect(section.length).toBeLessThanOrEqual(4);
      }
    });
  }

  it('puts each type in the triad that lists it, with its own color token', () => {
    for (const triad of TRIADS) {
      for (const n of triad.eneatypes) {
        expect(ENEATYPE_CONTENT[n].triad).toBe(triad.id);
        expect(ENEATYPE_CONTENT[n].color).toBe(`--nureon-type-${n}`);
      }
    }
    expect(TRIADS.flatMap((triad) => triad.eneatypes).sort()).toEqual(ENEATYPE_NUMBERS);
  });
});
