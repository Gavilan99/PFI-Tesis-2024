import { Component, Inject, OnInit } from '@angular/core';
import { API_SERVICE, ApiService } from '../core/services/api.service';
import { AttemptTier } from '../core/models/test-attempt.model';
import { PageContainerComponent } from '../shared/layout/page-container/page-container.component';
import { ErrorStateComponent } from '../shared/components/error-state/error-state.component';
import { BrandButtonComponent } from '../shared/components/brand-button/brand-button.component';
import { EnneagramDiagramComponent, ENEATYPE_STRUCTURE } from './enneagram-diagram/enneagram-diagram.component';
import { ENEATYPE_CONTENT, EneatypeContent, Encuadre, FRAMING_TEXT } from './eneatype-content';

// CU004 — layered reading, top to bottom: eneatype + name, one-line summary,
// core motivation, strengths/tensions, wings, then (only then) the blurred
// premium content. No classifier confidence signal shown — that's an open
// point of the plan, not a call this component makes on its own.
@Component({
  selector: 'app-resultados',
  standalone: true,
  imports: [PageContainerComponent, ErrorStateComponent, BrandButtonComponent, EnneagramDiagramComponent],
  templateUrl: './resultados.component.html',
  styleUrl: './resultados.component.scss',
})
export class ResultadosComponent implements OnInit {
  loading = true;
  error: string | null = null;
  eneatype: number | null = null;
  private tier: AttemptTier | null = null;

  // RF09/RF10 encuadre slot: hardcoded to 'individual' for now because
  // account_type isn't collected anywhere yet (that's profile/RF07, Stage 7).
  // Once it exists, whoever reads the user's profile sets this instead of
  // leaving it at the default — no other change needed here.
  readonly encuadre: Encuadre = 'individual';

  constructor(@Inject(API_SERVICE) private readonly api: ApiService) {}

  ngOnInit(): void {
    this.load();
  }

  get content(): EneatypeContent | null {
    return this.eneatype ? ENEATYPE_CONTENT[this.eneatype] : null;
  }

  get framingIntro(): string | null {
    return FRAMING_TEXT[this.encuadre].intro ?? FRAMING_TEXT.individual.intro;
  }

  get wings(): EneatypeContent[] {
    if (!this.eneatype) {
      return [];
    }
    return ENEATYPE_STRUCTURE[this.eneatype].wings.map((n) => ENEATYPE_CONTENT[n]);
  }

  get isPaid(): boolean {
    return this.tier === 'paid_full';
  }

  retry(): void {
    this.load();
  }

  private load(): void {
    this.loading = true;
    this.error = null;
    this.api.getLatestAttempt().subscribe({
      next: (attempt) => {
        if (!attempt || attempt.status !== 'completed') {
          this.fail();
          return;
        }
        this.tier = attempt.tier;
        this.api.getResult(attempt.id).subscribe({
          next: (result) => {
            this.eneatype = result.eneatype;
            this.loading = false;
          },
          error: () => this.fail(),
        });
      },
      error: () => this.fail(),
    });
  }

  private fail(): void {
    this.loading = false;
    this.error = 'No pudimos cargar tu resultado.';
  }
}
