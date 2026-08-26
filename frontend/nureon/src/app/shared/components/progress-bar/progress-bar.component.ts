import { Component, Input } from '@angular/core';
import { MatProgressBarModule } from '@angular/material/progress-bar';

@Component({
  selector: 'app-progress-bar',
  standalone: true,
  imports: [MatProgressBarModule],
  templateUrl: './progress-bar.component.html',
  styleUrl: './progress-bar.component.scss',
})
export class ProgressBarComponent {
  @Input({ required: true }) current!: number;
  @Input({ required: true }) total!: number;

  get percentage(): number {
    return this.total > 0 ? Math.round((this.current / this.total) * 100) : 0;
  }
}
