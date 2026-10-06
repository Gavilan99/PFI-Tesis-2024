import { Component, Input } from '@angular/core';

@Component({
  selector: 'app-enneatype-badge',
  standalone: true,
  templateUrl: './enneatype-badge.component.html',
  styleUrl: './enneatype-badge.component.scss',
})
export class EnneatypeBadgeComponent {
  @Input({ required: true }) eneatype!: number; // 1-9, per Result.eneatype
}
