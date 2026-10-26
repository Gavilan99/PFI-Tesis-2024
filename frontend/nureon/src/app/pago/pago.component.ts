import { Component, Inject, OnInit } from '@angular/core';
import { ActivatedRoute, Router } from '@angular/router';
import { API_SERVICE, ApiService } from '../core/services/api.service';
import { ApiError } from '../core/services/api-error';
import { CHECKOUT_COPY, formatDate } from '../core/payments/checkout-copy';
import { readCheckoutReturn } from '../core/payments/checkout-return';
import { PaymentStatus } from '../core/models/subscription.model';
import { BrandButtonComponent } from '../shared/components/brand-button/brand-button.component';
import { LoadingStateComponent } from '../shared/components/loading-state/loading-state.component';
import { PageContainerComponent } from '../shared/layout/page-container/page-container.component';

type PagoState = 'checking' | PaymentStatus | 'abandoned' | 'error';

// Feature 6 — where the buyer lands back from Mercado Pago (through the
// backend's /api/payments/return, which forwards only ?payment_id=). The
// outcome is never read from the URL: the backend asks Mercado Pago and
// answers it. Approved, "Seguir con el test" goes to /test, which resumes the
// attempt in progress — the same one, now able to continue (RF17); from a
// result, back to /resultados/:id, where "Seguir" continues in a new, linked
// attempt (RF16).
@Component({
  selector: 'app-pago',
  standalone: true,
  imports: [BrandButtonComponent, LoadingStateComponent, PageContainerComponent],
  templateUrl: './pago.component.html',
  styleUrl: './pago.component.scss',
})
export class PagoComponent implements OnInit {
  readonly copy = CHECKOUT_COPY;
  state: PagoState = 'checking';
  until: string | null = null;
  errorMessage: string = CHECKOUT_COPY.checkError;
  private paymentId: string | null = null;
  readonly returnTo = readCheckoutReturn() ?? '/test';

  constructor(
    @Inject(API_SERVICE) private readonly api: ApiService,
    private readonly route: ActivatedRoute,
    private readonly router: Router,
  ) {}

  ngOnInit(): void {
    this.paymentId = this.route.snapshot.queryParamMap.get('payment_id');
    this.check();
  }

  get backLabel(): string {
    return this.returnTo.startsWith('/resultados') ? this.copy.backToResult : this.copy.continueTest;
  }

  check(): void {
    if (!this.paymentId) {
      this.state = 'abandoned';
      return;
    }
    this.state = 'checking';
    this.api.confirmPayment(this.paymentId).subscribe({
      next: (confirmation) => {
        this.until = confirmation.currentPeriodEnd ? formatDate(confirmation.currentPeriodEnd) : null;
        this.state = confirmation.paymentStatus;
      },
      error: (error: unknown) => {
        this.errorMessage =
          error instanceof ApiError && error.status !== 0 && error.status < 500 ? error.message : this.copy.checkError;
        this.state = 'error';
      },
    });
  }

  goBack(): void {
    this.router.navigateByUrl(this.returnTo);
  }

  goHome(): void {
    this.router.navigateByUrl('/inicio');
  }
}
