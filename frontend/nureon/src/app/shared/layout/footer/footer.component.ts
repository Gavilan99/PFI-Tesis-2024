import { Component } from '@angular/core';

// Privacidad/Términos are plain text, not links, on purpose: those pages
// aren't part of the Stage 2 route tree yet, and this stage doesn't add
// routes on its own initiative. Wire them up once that content exists.
@Component({
  selector: 'app-footer',
  standalone: true,
  templateUrl: './footer.component.html',
  styleUrl: './footer.component.scss',
})
export class FooterComponent {
  readonly currentYear = new Date().getFullYear();
}
