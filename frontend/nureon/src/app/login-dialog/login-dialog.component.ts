import { Component, Inject, ViewEncapsulation } from '@angular/core';
import { MatDialogRef, MAT_DIALOG_DATA } from '@angular/material/dialog';

@Component({
  selector: 'app-login-dialog',
  templateUrl: './login-dialog.component.html',
  styleUrls: ['./login-dialog.component.css'],
  encapsulation: ViewEncapsulation.None,
})
export class LoginDialogComponent {

  constructor(
    public dialogRef: MatDialogRef<LoginDialogComponent>,  // Inject MatDialogRef to control the dialog
    @Inject(MAT_DIALOG_DATA) public data: any) {
    
    // Set the size of the dialog here
    this.dialogRef.updateSize('600px', 'auto');  // Adjust width and height here
  }

  onNoClick(): void {
    this.dialogRef.close();  // Close the dialog when needed
  }
}
