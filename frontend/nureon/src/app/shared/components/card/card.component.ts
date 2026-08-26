import { Component, Input } from '@angular/core';
import { MatCardModule } from '@angular/material/card';

@Component({
  selector: 'app-card',
  standalone: true,
  imports: [MatCardModule],
  templateUrl: './card.component.html',
})
export class CardComponent {
  @Input() title: string | null = null;
  @Input() subtitle: string | null = null;
}
