import { Component, Inject, ViewEncapsulation } from '@angular/core';
import { MatDialogRef, MAT_DIALOG_DATA } from '@angular/material/dialog';
import { FormBuilder, FormGroup, Validators } from '@angular/forms';
import { HttpClient } from '@angular/common/http';
import { Router } from '@angular/router';

// Step 1: Define the LoginResponse interface
interface LoginResponse {
  message: string; // Define the expected structure of the response
}

@Component({
  selector: 'app-login-dialog',
  templateUrl: './login-dialog.component.html',
  styleUrls: ['./login-dialog.component.css'],
  encapsulation: ViewEncapsulation.None,
})
export class LoginDialogComponent {
  loginForm: FormGroup;

  constructor(
    public dialogRef: MatDialogRef<LoginDialogComponent>,
    @Inject(MAT_DIALOG_DATA) public data: any,
    private fb: FormBuilder,
    private http: HttpClient,
    private router: Router
  ) {
    this.loginForm = this.fb.group({
      username: ['', Validators.required],
      password: ['', Validators.required]
    });
    this.dialogRef.updateSize('600px', 'auto');
  }

  onNoClick(): void {
    this.dialogRef.close();
  }

  onLogin() {
    if (this.loginForm.valid) {
      this.http.post('http://localhost:5000/loginUser', this.loginForm.value)
        .subscribe({
          next: (response: any) => {
            // Check the response message for login status
            if (response.message === "Login successful") {
              localStorage.setItem('username', this.loginForm.value.username);
              this.router.navigate(['/main-screen/test']);
              this.dialogRef.close();  // Close the dialog on successful login
            } else if (response.message === "Invalid password") {
              // Stay on the landing page and inform the user
              console.error('Login failed: Invalid password');
              alert('Invalid password. Please try again.'); // Display an alert or use a more sophisticated method to show the message
            } else {
              // Handle other cases (like user not found) if needed
              alert(response.message); // Inform the user of the error
            }
          },
          error: (error) => {
            // Handle network or other errors
            console.error('Login error:', error);
            alert('An error occurred while logging in. Please try again.'); // Display an error message
          }
        });
    } else {
      // If the form is not valid, log an error or notify the user
      console.error('Login form is invalid');
      alert('Please fill in all required fields.'); // Notify the user about form validity
    }
  }
  
  
}
