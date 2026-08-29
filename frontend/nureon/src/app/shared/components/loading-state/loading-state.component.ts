import { Component, Input } from '@angular/core';
import { MatProgressSpinnerModule } from '@angular/material/progress-spinner';

// Sibling to EmptyStateComponent/ErrorStateComponent (Stage 3) — formalizes
// the spinner+text pattern the styleguide already demoed ad-hoc, so every
// screen's loading state is the same component instead of scattered
// <p>Cargando…</p> text.
@Component({
  selector: 'app-loading-state',
  standalone: true,
  imports: [MatProgressSpinnerModule],
  templateUrl: './loading-state.component.html',
  styleUrl: './loading-state.component.scss',
})
export class LoadingStateComponent {
  @Input() message = 'Cargando…';
}
