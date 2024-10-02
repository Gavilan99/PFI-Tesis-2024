import { Component } from '@angular/core';
import { trigger, transition, style, animate } from '@angular/animations';
import { HttpClient } from '@angular/common/http'; // Import HttpClient to send requests

@Component({
  selector: 'app-test',
  templateUrl: './test.component.html',
  styleUrls: ['./test.component.css'],
  animations: [
    trigger('slideInOut', [
      transition(':enter', [
        style({ transform: 'translateY(100%)', opacity: 0 }),
        animate('600ms ease-in-out', style({ transform: 'translateY(0)', opacity: 1 }))
      ]),
      transition(':leave', [
        animate('600ms ease-in-out', style({ transform: 'translateY(-100%)', opacity: 0 }))
      ])
    ])
  ]
})
export class TestComponent {
  currentQuestionIndex = 0;
  showSlide = true;

  // Store user's selected answers
  userAnswers: any = {
    hornevian: '',
    harmonic: '',
    harmony: '',
    triad: ''
  };

  questions = [
    {
      question: 'En una situación en la que tus ideas son cuestionadas, ¿cómo respondes habitualmente?',
      key: 'hornevian',
      answers: [
        { text: 'Afirmo mi punto de vista y mantengo mi postura', value: '1' },
        { text: 'Intento conciliar las diferencias y mantener la armonía', value: '2' },
        { text: 'Tomo distancia para reflexionar y reconsiderar mi posición', value: '3' }
      ]
    },
    {
      question: 'Imagina que te enfrentas con un obstáculo en tu camino hacia un objetivo, ¿cómo reaccionarías?',
      key: 'harmonic',
      answers: [
        { text: 'Me concentro en encontrar una solución y seguir adelante', value: '1' },
        { text: 'Mantengo una actitud positiva y busco el lado bueno', value: '2' },
        { text: 'Reacciono emocionalmente y expreso mi frustración', value: '3' }
      ]
    },
    {
      question: 'Cuando trabajas en un proyecto grupal, ¿qué es lo que más motiva tu comportamiento?',
      key: 'harmony',
      answers: [
        { text: 'Asegurarme de que todos se sientan involucrados', value: '1' },
        { text: 'Asegurarme de que el proyecto cumpla con un alto estándar', value: '2' },
        { text: 'Tomar decisiones difíciles para mantener el proyecto en marcha', value: '3' }
      ]
    },
    {
      question: 'Cuando alguien te critica, ¿cuál es tu reacción inicial?',
      key: 'triad',
      answers: [
        { text: 'Me siento herido o rechazado', value: '1' },
        { text: 'Me defiendo instintivamente', value: '2' },
        { text: 'Analizo la validez de la crítica', value: '3' }
      ]
    }
  ];

  constructor(private http: HttpClient) {}

  get currentQuestion() {
    return this.questions[this.currentQuestionIndex];
  }

  // Capture user's answer and jump to next question
  selectAnswer(answerValue: string) {
    const currentKey = this.questions[this.currentQuestionIndex].key;
    this.userAnswers[currentKey] = answerValue; // Store answer based on question key
    this.nextQuestion(); // Move to the next question after selection
  }

  // Move to the next question or submit answers if the last question is reached
  nextQuestion() {
    if (this.currentQuestionIndex < this.questions.length - 1) {
      this.triggerSlideChange(() => {
        this.currentQuestionIndex++;
      });
    } else {
      this.submitAnswers(); // Submit answers when all questions are answered
    }
  }

  previousQuestion() {
    if (this.currentQuestionIndex > 0) {
      this.triggerSlideChange(() => {
        this.currentQuestionIndex--;
      });
    }
  }

  private triggerSlideChange(callback: () => void) {
    this.showSlide = false;
    setTimeout(() => {
      callback();
      this.showSlide = true;
    }, 600);
  }

  // Submit answers to the backend
  submitAnswers() {
    this.http.post<any>('http://localhost:5000/predict', this.userAnswers) // Replace with your actual backend URL
      .subscribe(
        (response) => {
          console.log('Prediction result:', response.predicted_enneatype);
          alert(`Tu Eneatipo predicho es: ${response.predicted_enneatype}`);
        },
        (error) => {
          console.error('Error during prediction:', error);
        }
      );
  }

  // Check if the answer is selected to keep it marked
  isSelected(answerValue: string): boolean {
    const currentKey = this.questions[this.currentQuestionIndex].key;
    return this.userAnswers[currentKey] === answerValue;
  }
}
