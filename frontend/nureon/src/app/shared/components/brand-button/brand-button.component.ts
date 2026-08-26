import { Component, Input } from '@angular/core';
import { MatButtonModule } from '@angular/material/button';

export type BrandButtonVariant = 'primary' | 'secondary' | 'text';

@Component({
  selector: 'app-brand-button',
  standalone: true,
  imports: [MatButtonModule],
  templateUrl: './brand-button.component.html',
})
export class BrandButtonComponent {
  @Input() variant: BrandButtonVariant = 'primary';
  @Input() disabled = false;
  @Input() type: 'button' | 'submit' = 'button';
}
