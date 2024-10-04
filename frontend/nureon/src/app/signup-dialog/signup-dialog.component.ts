import { Component, AfterViewInit, ChangeDetectorRef } from '@angular/core';
import { FormBuilder, FormGroup, Validators } from '@angular/forms';
import { HttpClient } from '@angular/common/http';
import { MatSnackBar } from '@angular/material/snack-bar';
import { MatDialogRef } from '@angular/material/dialog';  // Import MatDialogRef
import { Usuario } from '../dataTypes/Usuario';

@Component({
  selector: 'app-signup-dialog',
  templateUrl: './signup-dialog.component.html',
  styleUrls: ['./signup-dialog.component.css']
})
export class SignupDialogComponent implements AfterViewInit {
  signUpForm: FormGroup;
  usuarios: Usuario[] = [];
  genders: string[] = ['Male', 'Female'];
  userTypes: string[] = ['Personal use', 'Human Resourses Professional', 'Psycologyst/Psychiatrist'];

  constructor(
    private fb: FormBuilder,
    private cdRef: ChangeDetectorRef,
    private http: HttpClient,
    private snackBar: MatSnackBar,
    private dialogRef: MatDialogRef<SignupDialogComponent>  // Inject MatDialogRef
  ) {
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

  ngAfterViewInit(): void {
    this.cdRef.detectChanges();
  }

  onSubmit() {
    if (this.signUpForm.valid) {
      const formData = this.signUpForm.value;

      const mappedData = {
        ...formData,
        gender: formData.gender === 'Male' ? 'M' : 'F',
        userType: formData.userType === 'Personal use' ? 'P' :
                  formData.userType === 'Human Resourses Professional' ? 'H' : 'D'
      };

      this.http.post('http://localhost:5000/createUser', mappedData).subscribe(
        (response) => {
          this.snackBar.open('User created successfully!', 'Close', {
            duration: 3000,
            panelClass: ['success-snackbar']
          });

          this.dialogRef.close();  // Close the dialog after success
        },
        (error) => {
          this.snackBar.open('Failed to create user. Please try again.', 'Close', {
            duration: 3000,
            panelClass: ['error-snackbar']
          });
        }
      );
    }
  }

  onCancel() {
    this.signUpForm.reset();
    this.dialogRef.close();  // Close the dialog on cancel
  }
}
