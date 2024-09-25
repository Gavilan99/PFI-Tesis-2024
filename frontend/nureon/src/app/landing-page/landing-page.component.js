document.addEventListener('DOMContentLoaded', function() {
  let currentSlide = 0;
  const slides = document.querySelectorAll('.carousel-slide');
  const indicators = document.querySelectorAll('.indicator');
  const totalSlides = slides.length;
  let intervalId;

  function showSlide(index) {
    slides.forEach((slide, i) => {
      if (i === index) {
        slide.style.display = 'flex';
        setTimeout(() => {
          slide.style.opacity = '1';
        }, 10); // Small delay to trigger transition
      } else {
        slide.style.opacity = '0';
        setTimeout(() => {
          slide.style.display = 'none';
        }, 1000); // Match the transition duration
      }
    });
    indicators.forEach((indicator, i) => {
      indicator.classList.remove('active');
      if (i === index) {
        indicator.classList.add('active');
      }
    });
  }

  function nextSlide() {
    const previousSlide = currentSlide;
    currentSlide = (currentSlide + 1) % totalSlides;
    slides[previousSlide].style.opacity = '0';
    setTimeout(() => {
      slides[previousSlide].style.display = 'none';
      showSlide(currentSlide);
    }, 1000); // Match the transition duration
  }

  function resetInterval() {
    clearInterval(intervalId);
    intervalId = setInterval(nextSlide, 5000);
  }

  // Show the first slide initially
  showSlide(currentSlide);

  // Change slide every 5 seconds
  intervalId = setInterval(nextSlide, 5000);

  // Add click event to indicators
  indicators.forEach((indicator, i) => {
    indicator.addEventListener('click', () => {
      const previousSlide = currentSlide;
      currentSlide = i;
      slides[previousSlide].style.opacity = '0';
      setTimeout(() => {
        slides[previousSlide].style.display = 'none';
        showSlide(currentSlide);
      }, 1000); // Match the transition duration
      resetInterval();
    });
  });
});