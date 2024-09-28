import { Component, OnInit, Renderer2, ElementRef } from '@angular/core';
import { MatDialog } from '@angular/material/dialog';
import { LoginDialogComponent } from '../login-dialog/login-dialog.component';
import { SignupDialogComponent } from '../signup-dialog/signup-dialog.component';

@Component({
  selector: 'app-landing-page',
  standalone: false,
  
  templateUrl: './landing-page.component.html',
  styleUrls: ['./landing-page.component.css']
})
export class LandingPageComponent implements OnInit {
  private intervalId: any;

  constructor(private renderer: Renderer2, private el: ElementRef, public dialog: MatDialog) {}

  openLoginDialog(): void {
    const dialogRef = this.dialog.open(LoginDialogComponent, {
      width: '300px', // you can customize the width of the modal
    });

    dialogRef.afterClosed().subscribe(result => {
      console.log('The dialog was closed');
    });
  }

  openSignupDialog(): void {
    const dialogRef = this.dialog.open(SignupDialogComponent, {
      width: '300px', // you can customize the width of the modal
    });

    dialogRef.afterClosed().subscribe(result => {
      console.log('The dialog was closed');
    });
  }

  ngOnInit(): void {
    this.initCarousel();
  }

  initCarousel(): void {
    let currentSlide = 0;
    const slides = this.el.nativeElement.querySelectorAll('.carousel-slide');
    const indicators = this.el.nativeElement.querySelectorAll('.indicator');
    const totalSlides = slides.length;

    const showSlide = (index: number): void => {
      slides.forEach((slide: HTMLElement, i: number) => {
        if (i === index) {
          this.renderer.setStyle(slide, 'display', 'flex');
          setTimeout(() => {
            this.renderer.setStyle(slide, 'opacity', '1');
          }, 10); // Small delay to trigger transition
        } else {
          this.renderer.setStyle(slide, 'opacity', '0');
          setTimeout(() => {
            this.renderer.setStyle(slide, 'display', 'none');
          }, 1000); // Match the transition duration
        }
      });
      indicators.forEach((indicator: HTMLElement, i: number) => {
        this.renderer.removeClass(indicator, 'active');
        if (i === index) {
          this.renderer.addClass(indicator, 'active');
        }
      });
    };

    const nextSlide = (): void => {
      const previousSlide = currentSlide;
      currentSlide = (currentSlide + 1) % totalSlides;
      this.renderer.setStyle(slides[previousSlide], 'opacity', '0');
      setTimeout(() => {
        this.renderer.setStyle(slides[previousSlide], 'display', 'none');
        showSlide(currentSlide);
      }, 1000); // Match the transition duration
    };

    const resetInterval = (): void => {
      clearInterval(this.intervalId);
      this.intervalId = setInterval(nextSlide, 5000);
    };

    // Show the first slide initially
    showSlide(currentSlide);

    // Change slide every 5 seconds
    this.intervalId = setInterval(nextSlide, 5000);

    // Add click event to indicators
    indicators.forEach((indicator: HTMLElement, i: number) => {
      this.renderer.listen(indicator, 'click', () => {
        const previousSlide = currentSlide;
        currentSlide = i;
        this.renderer.setStyle(slides[previousSlide], 'opacity', '0');
        setTimeout(() => {
          this.renderer.setStyle(slides[previousSlide], 'display', 'none');
          showSlide(currentSlide);
        }, 1000); // Match the transition duration
        resetInterval();
      });
    });
  }
}