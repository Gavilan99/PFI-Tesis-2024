import { Component } from '@angular/core';
import { PageContainerComponent } from '../shared/layout/page-container/page-container.component';

// Public, prerendered content. The author bios are a placeholder draft on
// purpose — see the DRAFT notice in the template — no biographical data was
// invented for this component; it's marked for confirmation instead.
@Component({
  selector: 'app-nosotros',
  standalone: true,
  imports: [PageContainerComponent],
  templateUrl: './nosotros.component.html',
  styleUrl: './nosotros.component.scss',
})
export class NosotrosComponent {}
