import { Component, EventEmitter, Input, Output } from '@angular/core';
import { Question } from '../../core/models/question.model';

// One of the two item renderers TestComponent dispatches to by
// questionType. Adding 'ordering'/'text' later means adding a sibling
// renderer here, not touching this one or TestComponent's dispatch logic.
@Component({
  selector: 'app-scenario-item',
  standalone: true,
  templateUrl: './scenario-item.component.html',
  styleUrl: './scenario-item.component.scss',
})
export class ScenarioItemComponent {
  @Input({ required: true }) question!: Question;
  @Input() selectedOptionId: string | null = null;
  @Output() select = new EventEmitter<string>();
}
