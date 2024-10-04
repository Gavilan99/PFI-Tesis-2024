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

  numberToEnneatype(num: number): string {
    const enneatypeMap: { [key: number]: string } = {
      1: 'ONE',
      2: 'TWO',
      3: 'THREE',
      4: 'FOUR',
      5: 'FIVE',
      6: 'SIX',
      7: 'SEVEN',
      8: 'EIGHT',
      9: 'NINE',
      0: 'UNKNOWN' // Default case if needed
    };
    return enneatypeMap[num] || 'UNKNOWN'; // Return 'UNKNOWN' for invalid numbers
  }

  // Method to get the enneatype (replace with actual logic)
  getEnneatype(): string {
    const enneatypeNum = parseInt(localStorage.getItem('enneatype') || '0', 10); // Convert to number
    return this.numberToEnneatype(enneatypeNum); // Convert number to enneatype string
  }

  getImageSrc(): string {
    // Map enneatypes to their respective image sources
    const enneatypeImages: { [key: string]: string } = {
      ONE: '/assets/testAssets/E1_big.png',
      TWO: '/assets/testAssets/E2_big.png',
      THREE: '/assets/testAssets/E3_big.png',
      FOUR: '/assets/testAssets/E4_big.png',
      FIVE: '/assets/testAssets/E5_big.png',
      SIX: '/assets/testAssets/E6_big.png',
      SEVEN: '/assets/testAssets/E7_big.png',
      EIGHT: '/assets/testAssets/E8_big.png',
      NINE: '/assets/testAssets/E9_big.png'
    };
    return enneatypeImages[this.enneatype] || '/assets/testAssets/default.png'; // Fallback image
  }
}