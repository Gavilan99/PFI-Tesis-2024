import { Component, Inject, Input, OnInit } from '@angular/core';
import { Router } from '@angular/router';
import { API_SERVICE, ApiService } from '../../../core/services/api.service';
import { ApiError } from '../../../core/services/api-error';
import { CHECKOUT_COPY } from '../../../core/payments/checkout-copy';
import { saveCheckoutReturn } from '../../../core/payments/checkout-return';
import { Subscription } from '../../../core/models/subscription.model';
import { BrandButtonComponent } from '../brand-button/brand-button.component';

// Feature 6 — "Pasar a premium": shows the plan's price (from the backend's
// configuration) and sends the buyer to Mercado Pago. The checkout is created
// by the backend with its own price; this only follows the URL it answers.
// Used wherever the plans text is (between cuts, the result, the tiers
// dialog), each with the path to come back to.
@Component({
  selector: 'app-premium-button',
  standalone: true,
  imports: [BrandButtonComponent],
  templateUrl: './premium-button.component.html',
  styleUrl: './premium-button.component.scss',
})
export class PremiumButtonComponent implements OnInit {
  @Input({ required: true }) returnTo!: string;
  @Input() variant: 'primary' | 'secondary' = 'secondary';

  readonly copy = CHECKOUT_COPY;
  plan: Subscription | null = null;
  busy = false;
  error: string | null = null;

  constructor(
    @Inject(API_SERVICE) private readonly api: ApiService,
    private readonly router: Router,
  ) {}

  ngOnInit(): void {
    // Without the price the button still works: Mercado Pago shows it too.
    this.api.getSubscription().subscribe({ next: (plan) => (this.plan = plan), error: () => undefined });
  }

  get priceText(): string | null {
    return this.plan ? this.copy.planPrice(this.plan.planPrice, this.plan.planCurrency, this.plan.planDays) : null;
  }

  start(): void {
    if (this.busy) {
      return;
    }
    this.busy = true;
    this.error = null;
    saveCheckoutReturn(this.returnTo);
    this.api.startCheckout().subscribe({
      next: ({ checkoutUrl }) => {
        // The mock answers a path of this app; the backend, Mercado Pago's page.
        if (checkoutUrl.startsWith('/')) {
          this.busy = false;
          this.router.navigateByUrl(checkoutUrl);
        } else {
          window.location.assign(checkoutUrl);
        }
      },
      error: (error: unknown) => {
        this.busy = false;
        this.error = error instanceof ApiError && error.status !== 0 ? error.message : this.copy.startError;
      },
    });
  }
}
