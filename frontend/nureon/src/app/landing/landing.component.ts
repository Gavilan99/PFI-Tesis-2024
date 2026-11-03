import { Component, Inject } from '@angular/core';
import { AsyncPipe } from '@angular/common';
import { Router } from '@angular/router';
import { Observable, catchError, map, of, switchMap } from 'rxjs';
import { User } from '../core/models/user.model';
import { AuthService } from '../core/services/auth.service';
import { API_SERVICE, ApiService } from '../core/services/api.service';
import { PageContainerComponent } from '../shared/layout/page-container/page-container.component';
import { BrandButtonComponent } from '../shared/components/brand-button/brand-button.component';
import { CardComponent } from '../shared/components/card/card.component';
import { StartTestDialogComponent } from '../inicio/start-test-dialog/start-test-dialog.component';

// Public, prerendered entry point — pure marketing content for a logged-out
// visitor, same as every route in this stage. The one exception is the
// notice after deleting an account (Feature 11): /perfil navigates here with
// { accountDeleted: true } in the navigation state. Only a client-side
// navigation carries it, so the prerendered page never shows it. With a
// session the hero greets the person instead of inviting them to /registro;
// the prerendered page has no session, so it's always the logged-out one.
//
// With a session, the hero's main action is the test itself (CU003), not a
// detour through /perfil: "Empezar el test", or "Continuar test" — rendered
// inverted, same rule CU008 already uses for /inicio — once inProgress$
// resolves. A salud/rrhh account starting fresh goes through the same "who's
// this for" dialog /inicio opens from its own "Iniciar test"; resuming an
// attempt already in progress never needs it, whoever it was started for.
@Component({
  selector: 'app-landing',
  standalone: true,
  imports: [
    AsyncPipe,
    PageContainerComponent,
    BrandButtonComponent,
    CardComponent,
    StartTestDialogComponent,
  ],
  templateUrl: './landing.component.html',
  styleUrl: './landing.component.scss',
})
export class LandingComponent {
  readonly accountDeleted: boolean;
  readonly user$: Observable<User | null>;
  readonly inProgress$: Observable<boolean>;
  showStartTestDialog = false;

  constructor(
    router: Router,
    private readonly auth: AuthService,
    @Inject(API_SERVICE) private readonly api: ApiService,
  ) {
    this.user$ = auth.currentUserChanges;
    this.accountDeleted = router.getCurrentNavigation()?.extras.state?.['accountDeleted'] === true;
    this.inProgress$ = this.user$.pipe(
      switchMap((user) => (user ? this.api.getLatestAttempt(user.id) : of(null))),
      map((attempt) => attempt?.status === 'in_progress'),
      // A failed check just falls back to "Empezar el test"; /test resolves the real state anyway.
      catchError(() => of(false)),
    );
  }

  isProfessional(user: User): boolean {
    return user.accountType === 'salud' || user.accountType === 'rrhh';
  }

  openStartTestDialog(): void {
    this.showStartTestDialog = true;
  }

  closeStartTestDialog(): void {
    this.showStartTestDialog = false;
  }
}
