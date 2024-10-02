import { Component } from '@angular/core';

@Component({
  selector: 'app-results',
  templateUrl: './results.component.html',
  styleUrls: ['./results.component.css']
})
export class ResultsComponent {
  imageSrc: string;
  // Property to store the enneatype
  enneatype: string;

  constructor() {
    // Set the enneatype based on external logic
    // This could be passed from a service, API call, or other component
    this.enneatype = this.getEnneatype(); // Example: Replace with actual logic
    this.imageSrc = '/assets/testAssets/E1_big.png';
  }

  // Method to get the enneatype (replace with actual logic)
  getEnneatype(): string {
    // Example: Return an enneatype; replace this with actual logic
    return 'ONE';
  }
}
