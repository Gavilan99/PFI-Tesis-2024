import { Component } from '@angular/core';
import { RouterLink } from '@angular/router';
import { PageContainerComponent } from '../shared/layout/page-container/page-container.component';
import { ENEATYPE_CONTENT, ENEATYPE_NUMBERS, TRIADS } from '../resultados/eneatype-content';

// Public, prerendered educational content — no ApiService call, same as
// LandingComponent. The nine cards link to /eneagrama/:tipo; names, triads
// and colors come from ENEATYPE_CONTENT, the one source for everything
// about a type. The legend under the grid names each triad's types in words,
// so the color is never the only way to tell them apart.
//
// Deliberately doesn't say which triad group any item or option belongs
// to — that's the instrument's scoring key, not marketing content.
@Component({
  selector: 'app-eneagrama',
  standalone: true,
  imports: [PageContainerComponent, RouterLink],
  templateUrl: './eneagrama.component.html',
  styleUrl: './eneagrama.component.scss',
})
export class EneagramaComponent {
  readonly eneatypes = ENEATYPE_NUMBERS;
  readonly triads = TRIADS;

  titleOf(eneatype: number): string {
    return ENEATYPE_CONTENT[eneatype].title;
  }

  colorOf(eneatype: number): string {
    return `var(${ENEATYPE_CONTENT[eneatype].color})`;
  }
}
