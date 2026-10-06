import { Component, EventEmitter, Input, Output } from '@angular/core';
import { MatButtonModule } from '@angular/material/button';

// Generic retry-on-error UI — literally CU004's alternate flows 3.2/3.3, but
// built without any knowledge of what failed or how to retry it: the parent
// owns that, this just emits retry and shows a message.
@Component({
  selector: 'app-error-state',
  standalone: true,
  imports: [MatButtonModule],
  templateUrl: './error-state.component.html',
  styleUrl: './error-state.component.scss',
})
export class ErrorStateComponent {
  @Input() message = 'Ocurrió un error. Intentá de nuevo.';
  @Output() retry = new EventEmitter<void>();
}
