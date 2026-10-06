import { Component, Input } from '@angular/core';
import { NgTemplateOutlet } from '@angular/common';
import { RouterLink } from '@angular/router';
import { MatButtonModule } from '@angular/material/button';

export type BrandButtonVariant = 'primary' | 'secondary' | 'text';

@Component({
  selector: 'app-brand-button',
  standalone: true,
  imports: [MatButtonModule, RouterLink, NgTemplateOutlet],
  templateUrl: './brand-button.component.html',
})
export class BrandButtonComponent {
  @Input() variant: BrandButtonVariant = 'primary';
  @Input() disabled = false;
  @Input() type: 'button' | 'submit' = 'button';
  // When set, renders as a routable <a> instead of a <button> — for CTAs
  // that navigate (e.g. the landing page's "Empezar gratis").
  @Input() routerLink?: string | unknown[];
}
