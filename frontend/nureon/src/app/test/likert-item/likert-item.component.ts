import { Component, EventEmitter, Input, Output } from '@angular/core';
import { Question } from '../../core/models/question.model';

// The other item renderer TestComponent dispatches to. A 5-option ordinal
// scale reads and operates differently from three scenario cards — same
// question shape, deliberately different component.
@Component({
  selector: 'app-likert-item',
  standalone: true,
  templateUrl: './likert-item.component.html',
  styleUrl: './likert-item.component.scss',
})
export class LikertItemComponent {
  @Input({ required: true }) question!: Question;
  @Input() selectedOptionId: string | null = null;
  @Output() select = new EventEmitter<string>();
}
