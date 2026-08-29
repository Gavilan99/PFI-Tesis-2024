import { Component, Input } from '@angular/core';

// Riso-Hudson convention: integratesTo is the growth direction, disintegratesTo
// is the stress direction. wings are always the two numerically adjacent
// points on the circle. This is standard Enneagram structure, not content —
// same for every user who gets a given eneatype, unlike the description text.
export interface EneatypeStructure {
  wings: [number, number];
  integratesTo: number;
  disintegratesTo: number;
}

// Exported so ResultadosComponent can read wings/integration/disintegration
// for the text layers without duplicating this table.
export const ENEATYPE_STRUCTURE: Record<number, EneatypeStructure> = {
  1: { wings: [9, 2], integratesTo: 7, disintegratesTo: 4 },
  2: { wings: [1, 3], integratesTo: 4, disintegratesTo: 8 },
  3: { wings: [2, 4], integratesTo: 6, disintegratesTo: 9 },
  4: { wings: [3, 5], integratesTo: 1, disintegratesTo: 2 },
  5: { wings: [4, 6], integratesTo: 8, disintegratesTo: 7 },
  6: { wings: [5, 7], integratesTo: 9, disintegratesTo: 3 },
  7: { wings: [6, 8], integratesTo: 5, disintegratesTo: 1 },
  8: { wings: [7, 9], integratesTo: 2, disintegratesTo: 5 },
  9: { wings: [8, 1], integratesTo: 3, disintegratesTo: 6 },
};

// The nine fixed connecting lines of the enneagram symbol (hexad + triad) —
// drawn faint for every type as context; the two touching the result get
// highlighted. This geometry never changes, regardless of who's looking at it.
const CONNECTIONS: Array<[number, number]> = [
  [1, 4],
  [4, 2],
  [2, 8],
  [8, 5],
  [5, 7],
  [7, 1],
  [3, 9],
  [9, 6],
  [6, 3],
];

const SIZE = 320;
const CENTER = SIZE / 2;
const RADIUS = SIZE * 0.4;

interface Point {
  n: number;
  x: number;
  y: number;
}

interface Edge {
  x1: number;
  y1: number;
  x2: number;
  y2: number;
  kind: 'context' | 'integration' | 'disintegration';
}

function pointFor(n: number): Point {
  // n=9 -> 0 -> -90deg (top); clockwise from there, 40deg apart (9 points).
  const angleDeg = -90 + (n % 9) * 40;
  const angleRad = (angleDeg * Math.PI) / 180;
  return {
    n,
    x: CENTER + RADIUS * Math.cos(angleRad),
    y: CENTER + RADIUS * Math.sin(angleRad),
  };
}

const POINTS: Point[] = Array.from({ length: 9 }, (_, i) => pointFor(i + 1));
const POINTS_BY_NUMBER = new Map(POINTS.map((p) => [p.n, p]));

// Code-generated SVG, not a static image: scales without blurring, and the
// nine PNGs the old design mapped (of which only one ever existed) are gone.
@Component({
  selector: 'app-enneagram-diagram',
  standalone: true,
  templateUrl: './enneagram-diagram.component.html',
  styleUrl: './enneagram-diagram.component.scss',
})
export class EnneagramDiagramComponent {
  @Input({ required: true }) eneatype!: number;

  readonly size = SIZE;
  readonly points = POINTS;

  get structure(): EneatypeStructure {
    return ENEATYPE_STRUCTURE[this.eneatype];
  }

  get edges(): Edge[] {
    const struct = this.structure;
    return CONNECTIONS.map(([a, b]) => {
      const from = POINTS_BY_NUMBER.get(a)!;
      const to = POINTS_BY_NUMBER.get(b)!;
      const touchesResult = a === this.eneatype || b === this.eneatype;
      const other = a === this.eneatype ? b : a;
      let kind: Edge['kind'] = 'context';
      if (touchesResult && other === struct.integratesTo) {
        kind = 'integration';
      } else if (touchesResult && other === struct.disintegratesTo) {
        kind = 'disintegration';
      }
      return { x1: from.x, y1: from.y, x2: to.x, y2: to.y, kind };
    });
  }

  isResult(n: number): boolean {
    return n === this.eneatype;
  }

  isWing(n: number): boolean {
    return this.structure.wings.includes(n);
  }

  pointRadius(n: number): number {
    if (this.isResult(n)) return SIZE * 0.055;
    if (this.isWing(n)) return SIZE * 0.045;
    return SIZE * 0.035;
  }
}
