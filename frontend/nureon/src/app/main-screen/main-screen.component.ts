// main-screen.component.ts
import { Component } from '@angular/core';

@Component({
  selector: 'app-main-screen',
  templateUrl: './main-screen.component.html',
  styleUrls: ['./main-screen.component.css']
})
export class MainScreenComponent {
  sidenavOpened: boolean = true; // Start with sidenav open
  activeSection: string = 'Take the test'; // Default active section

  toggleSidenav() {
    this.sidenavOpened = !this.sidenavOpened; // Toggle sidenav state
  }

  setActiveSection(section: string) {
    this.activeSection = section; // Set the active section
  }

  navigateToProfile() {
    console.log('Navigating to Profile');
    // Implement navigation logic here
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
