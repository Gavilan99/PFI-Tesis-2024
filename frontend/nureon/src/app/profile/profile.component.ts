import { Component } from '@angular/core';
import { MatDialogRef } from '@angular/material/dialog';
import { MatDialog } from '@angular/material/dialog'; // Import MatDialog

@Component({
  selector: 'app-profile',
  templateUrl: './profile.component.html',
  styleUrls: ['./profile.component.css']
})
export class ProfileComponent {
  username: string = 'User Name';
  email: string = 'user@example.com';
  password: string = 'secret'; // Ideally, you wouldn't show this

  // To hold the original values before editing
  originalUsername: string = this.username;
  originalEmail: string = this.email;
  originalPassword: string = this.password;

  editMode: boolean = false; // To toggle between edit and view modes

  constructor(public dialogRef: MatDialogRef<ProfileComponent>, private dialog: MatDialog) {}

  // Method to enable editing for specific fields
  editField(field: string) {
    this.editMode = true;
  }

  // Method to confirm changes
  confirmEdit() {
    this.editMode = false;
    // Here you can also add logic to save the changes, e.g., send to a server
    this.originalUsername = this.username;
    this.originalEmail = this.email;
    this.originalPassword = this.password;
  }

  // Method to cancel editing and revert to original values
  cancelEdit() {
    this.editMode = false;
    this.username = this.originalUsername;
    this.email = this.originalEmail;
    this.password = this.originalPassword; // Ideally, you'd reset to masked state
  }

  // Optional: Method to change the profile picture
  editProfilePicture() {
    // Implement logic to edit the profile picture
    console.log("Edit profile picture clicked.");
  }

  // Optional: Method to change the frame color
  changeFrameColor() {
    // Implement logic to change the frame color
    console.log("Change frame color clicked.");
  }

  // Method to close the dialog
  onClose(): void {
    this.dialogRef.close();
  }
}
