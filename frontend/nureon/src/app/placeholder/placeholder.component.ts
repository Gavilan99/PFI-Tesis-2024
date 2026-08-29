import { AsyncPipe } from '@angular/common';
import { Component } from '@angular/core';
import { ActivatedRoute } from '@angular/router';
import { map } from 'rxjs';
import { PageContainerComponent } from '../shared/layout/page-container/page-container.component';

// Generic stub screen reused across every not-yet-built route in the Stage 2
// skeleton (landing, registro, ingresar, inicio, test, resultados, perfil,
// eneagrama, nosotros, contacto). Each route supplies its own label via
// route data; real screens replace this route-by-route in later stages.
@Component({
  selector: 'app-placeholder',
  standalone: true,
  imports: [AsyncPipe, PageContainerComponent],
  templateUrl: './placeholder.component.html',
})
export class PlaceholderComponent {
  readonly title$ = this.route.data.pipe(map((data) => (data['title'] as string) ?? 'NureonAI'));

  constructor(private readonly route: ActivatedRoute) {}
}
