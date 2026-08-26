import { Component } from '@angular/core';

// Max-width wrapper with consistent vertical rhythm between direct children.
// Used inside routed page components, not around the whole app shell — the
// shell (header/footer) stays full-bleed; a hero section later might too.
@Component({
  selector: 'app-page-container',
  standalone: true,
  templateUrl: './page-container.component.html',
  styleUrl: './page-container.component.scss',
})
export class PageContainerComponent {}
