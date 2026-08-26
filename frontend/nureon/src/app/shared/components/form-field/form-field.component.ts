import { Component, Input } from '@angular/core';
import { MatFormFieldModule } from '@angular/material/form-field';

// Wraps mat-form-field/mat-error so consumers pass an errorMessage instead
// of repeating the *ngIf/@if boilerplate. Validity decisions (when there IS
// an error) stay in the consuming form — this only renders what it's given.
@Component({
  selector: 'app-form-field',
  standalone: true,
  imports: [MatFormFieldModule],
  templateUrl: './form-field.component.html',
})
export class FormFieldComponent {
  @Input() label = '';
  @Input() hint: string | null = null;
  @Input() errorMessage: string | null = null;
}
