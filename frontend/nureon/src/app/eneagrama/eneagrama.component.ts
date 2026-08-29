import { Component } from '@angular/core';
import { PageContainerComponent } from '../shared/layout/page-container/page-container.component';
import { CardComponent } from '../shared/components/card/card.component';

interface EneatypeSummary {
  number: number;
  name: string;
}

// Public, prerendered educational content — no ApiService call, same as
// LandingComponent. Names only, not the descriptive copy from
// resultados/eneatype-content.ts: that file is explicitly provisional
// (see its own header comment) and scoped to the results screen, and this
// page shouldn't silently change if that copy gets rewritten for accuracy.
//
// Deliberately doesn't say which triad group any item or option belongs
// to — that's the instrument's scoring key, not marketing content.
const ENEATYPES: EneatypeSummary[] = [
  { number: 1, name: 'El Reformador' },
  { number: 2, name: 'El Ayudador' },
  { number: 3, name: 'El Triunfador' },
  { number: 4, name: 'El Individualista' },
  { number: 5, name: 'El Investigador' },
  { number: 6, name: 'El Leal' },
  { number: 7, name: 'El Entusiasta' },
  { number: 8, name: 'El Desafiador' },
  { number: 9, name: 'El Pacificador' },
];

@Component({
  selector: 'app-eneagrama',
  standalone: true,
  imports: [PageContainerComponent, CardComponent],
  templateUrl: './eneagrama.component.html',
  styleUrl: './eneagrama.component.scss',
})
export class EneagramaComponent {
  readonly eneatypes = ENEATYPES;
}
