import { Component } from '@angular/core';
import { PageContainerComponent } from '../shared/layout/page-container/page-container.component';

// Public, prerendered content. One line per person with their role in the
// project: no photos and no personal contact details.
@Component({
  selector: 'app-nosotros',
  standalone: true,
  imports: [PageContainerComponent],
  templateUrl: './nosotros.component.html',
  styleUrl: './nosotros.component.scss',
})
export class NosotrosComponent {}
