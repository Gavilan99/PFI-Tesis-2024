import { Component } from '@angular/core';
import { MatDialog } from '@angular/material/dialog'; // Import MatDialog
import { ProfileComponent } from '../profile/profile.component'; 

@Component({
  selector: 'app-main-screen',
  templateUrl: './main-screen.component.html',
  styleUrls: ['./main-screen.component.css']
})
export class MainScreenComponent {
  sidenavOpened: boolean = true; // Start with sidenav open
  activeSection: string = 'Take the test'; // Default active section

  constructor(private dialog: MatDialog) {} // Inject MatDialog

  toggleSidenav() {
    this.sidenavOpened = !this.sidenavOpened; // Toggle sidenav state
  }

  setActiveSection(section: string) {
    this.activeSection = section; // Set the active section
  }

  navigateToProfile() {
    console.log('Navigating to Profile');
    this.openProfileDialog(); // Call the method to open the profile dialog
  }

  openProfileDialog(): void {
    const dialogRef = this.dialog.open(ProfileComponent, {
      width: '400px', // Adjust the width as needed
      data: {
        // You can pass data to the profile component here if necessary
      }
    });

    dialogRef.afterClosed().subscribe(result => {
      console.log('The dialog was closed', result);
      // Handle any logic after dialog is closed if needed
    });
  }

  changeLanguage() {
    console.log('Changing Language');
    // Implement language change logic here
  }

  logout() {
    console.log('Logging Out');
    // Implement logout logic here
  }

  navigateTo(page: string): void {
    switch (page) {
      case 'privacy':
        // Navigate to Privacy Policy page
        console.log('Navigating to Privacy Policy');
        break;
      case 'terms':
        // Navigate to Terms and Conditions page
        console.log('Navigating to Terms and Conditions');
        break;
      default:
        console.log('Unknown page');
    }
  }
}
