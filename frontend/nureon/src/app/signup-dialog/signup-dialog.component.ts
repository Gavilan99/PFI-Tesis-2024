import { Component, AfterViewInit, ChangeDetectorRef } from '@angular/core';
import { FormBuilder, FormGroup, Validators } from '@angular/forms';

@Component({
  selector: 'app-signup-dialog',
  templateUrl: './signup-dialog.component.html',
  styleUrls: ['./signup-dialog.component.css']  // fixed styleUrls typo
})
export class SignupDialogComponent implements AfterViewInit {
  signUpForm: FormGroup;
  genders: string[] = ['Male', 'Female', 'AMOGUS'];
  userTypes: string[] = ['Normal Human being', 'Human Resourses (Disgrace)', 'Psycologyst'];

  constructor(private fb: FormBuilder, private cdRef: ChangeDetectorRef) {
    this.signUpForm = this.fb.group({
      username: ['', Validators.required],
      email: ['', [Validators.required, Validators.email]],
      confirmEmail: ['', Validators.required],
      password: ['', Validators.required],
      confirmPassword: ['', Validators.required],
      birthDate: ['', Validators.required],
      gender: ['', Validators.required],
      userType: ['', Validators.required],
    });
  }
  
  // Ensure colors are applied correctly by triggering change detection
  ngAfterViewInit(): void {
    this.cdRef.detectChanges();
  }

  onSubmit() {
    if (this.signUpForm.valid) {
      console.log('Form submitted', this.signUpForm.value);
    }
  }

  onCancel() {
    this.signUpForm.reset();
  }
}
