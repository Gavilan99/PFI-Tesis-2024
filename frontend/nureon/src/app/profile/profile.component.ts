import { Component, OnInit } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { MatDialogRef } from '@angular/material/dialog';
import { MatDialog } from '@angular/material/dialog';

@Component({
  selector: 'app-profile',
  templateUrl: './profile.component.html',
  styleUrls: ['./profile.component.css']
})
export class ProfileComponent implements OnInit {
  username: string = ''; // Initially empty, will be set from the API
  email: string = ''; // Initially empty, will be set from the API
  password: string = ''; // Password will be fetched from the API
  showPassword: boolean = false;

  // To hold the original values before editing
  originalUsername: string = this.username;
  originalEmail: string = this.email;
  originalPassword: string = this.password;

  editMode: boolean = false; // To toggle between edit and view modes
  userId: number | undefined; // Store user ID

  constructor(
    public dialogRef: MatDialogRef<ProfileComponent>, 
    private dialog: MatDialog,
    private http: HttpClient
  ) {}

  ngOnInit(): void {
    // Get the logged-in username from localStorage
    const storedUsername = localStorage.getItem('username');
    if (storedUsername) {
      this.fetchUserProfile(storedUsername);
    }
  }

  fetchUserProfile(username: string): void {
    this.http.get<any>(`http://localhost:5000/getUserByUsername/${username}`).subscribe(
      (response) => {
        const user = response.usuarios[0]; // Assuming response contains an array of users
        this.userId = user[0]; // Assuming user[0] is the user ID
        this.username = user[1];  // Assuming user[1] is the username
        this.email = user[2];     // Assuming user[2] is the email
        this.password = user[3];  // Assuming user[3] is the password

        // Set original values to the fetched data
        this.originalUsername = this.username;
        this.originalEmail = this.email;
        this.originalPassword = this.password;
      },
      (error) => {
        console.error('Error fetching user profile:', error);
      }
    );
  }

  // New method to update user information
  updateUserProfile(): void {
    const updatedUserData = {
      id: this.userId, // Include the user ID in the update request
      username: this.username,
      email: this.email,
      password: this.password
    };

    this.http.put('http://localhost:5000/updateUser', updatedUserData).subscribe(
      (response) => {
        console.log('User updated successfully:', response);
        // Update original values after a successful update
        this.originalUsername = this.username;
        this.originalEmail = this.email;
        this.originalPassword = this.password;
        this.editMode = false; // Exit edit mode
      },
      (error) => {
        console.error('Error updating user profile:', error);
        alert('An error occurred while updating the profile. Please try again.');
      }
    );
  }

  // Method to enable editing for specific fields
  editField(field: string) {
    this.editMode = true;
    if (field === 'password') {
      this.showPassword = true;
    }
  }

  // Method to confirm changes
  confirmEdit() {
    this.updateUserProfile();
    this.showPassword = false;
  }

  // Method to cancel editing and revert to original values
  cancelEdit() {
    this.editMode = false;
    this.username = this.originalUsername;
    this.email = this.originalEmail;
    this.password = this.originalPassword;
    this.showPassword = false; // Ideally, you'd reset to masked state
  }

  // Method to close the dialog
  onClose(): void {
    this.dialogRef.close();
  }

  editProfilePicture(): void {
    // Add code to open a dialog for editing profile picture
  }

  changeFrameColor(): void {
    // Add code to change the frame color of the profile picture
  }
}
