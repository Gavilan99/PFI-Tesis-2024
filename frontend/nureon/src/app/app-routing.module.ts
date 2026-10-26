import { NgModule } from '@angular/core';
import { RouterModule, Routes } from '@angular/router';
import { NotFoundComponent } from './not-found/not-found.component';
import { LandingComponent } from './landing/landing.component';
import { RegistroComponent } from './registro/registro.component';
import { IngresarComponent } from './ingresar/ingresar.component';
import { InicioComponent } from './inicio/inicio.component';
import { TestComponent } from './test/test.component';
import { ResultadosComponent } from './resultados/resultados.component';
import { ProfileComponent } from './profile/profile.component';
import { EneagramaComponent } from './eneagrama/eneagrama.component';
import { NosotrosComponent } from './nosotros/nosotros.component';
import { ContactoComponent } from './contacto/contacto.component';
import { PagoComponent } from './pago/pago.component';
import { sessionGuard } from './core/guards/session.guard';
import { resultAvailableGuard } from './core/guards/result-available.guard';
import { eneatypeGuard, eneatypeTitleResolver } from './eneagrama/eneatype-route';
import { environment } from '../environments/environment';

// Guarded routes use runGuardsAndResolvers: 'always' so that AppComponent can
// re-run their guards on logout by reloading the current URL.
export const routes: Routes = [
  { path: '', component: LandingComponent, data: { title: 'Descubrí tu eneatipo' } },
  { path: 'registro', component: RegistroComponent, data: { title: 'Registro' } },
  { path: 'ingresar', component: IngresarComponent, data: { title: 'Ingresar' } },
  {
    path: 'inicio',
    component: InicioComponent,
    data: { title: 'Inicio' },
    canActivate: [sessionGuard],
    runGuardsAndResolvers: 'always',
  },
  {
    path: 'test',
    component: TestComponent,
    data: { title: 'Test' },
    canActivate: [sessionGuard],
    runGuardsAndResolvers: 'always',
  },
  {
    path: 'resultados',
    component: ResultadosComponent,
    data: { title: 'Resultados' },
    canActivate: [resultAvailableGuard],
    runGuardsAndResolvers: 'always',
  },
  {
    path: 'resultados/:attemptId',
    component: ResultadosComponent,
    data: { title: 'Resultado de intento' },
    canActivate: [resultAvailableGuard],
    runGuardsAndResolvers: 'always',
  },
  // Feature 6: back from Mercado Pago. Behind the session guard: the session
  // survives the round trip (the token is in localStorage).
  {
    path: 'pago',
    component: PagoComponent,
    data: { title: 'Pago' },
    canActivate: [sessionGuard],
    runGuardsAndResolvers: 'always',
  },
  {
    path: 'perfil',
    component: ProfileComponent,
    data: { title: 'Perfil' },
    canActivate: [sessionGuard],
    runGuardsAndResolvers: 'always',
  },
  { path: 'eneagrama', component: EneagramaComponent, data: { title: 'Sobre el eneagrama' } },
  // Lazy and prerendered (see prerender-routes.txt): one short public page
  // per type. The title is resolved per type, not fixed in data.
  {
    path: 'eneagrama/:tipo',
    loadComponent: () =>
      import('./eneagrama/eneatype-page/eneatype-page.component').then((m) => m.EneatypePageComponent),
    canActivate: [eneatypeGuard],
    resolve: { title: eneatypeTitleResolver },
  },
  { path: 'nosotros', component: NosotrosComponent, data: { title: 'Nosotros' } },
  { path: 'contacto', component: ContactoComponent, data: { title: 'Contacto' } },
  // Lazy: long text few visitors open, prerendered anyway. Keeps it out of
  // the initial bundle.
  {
    path: 'privacidad',
    loadComponent: () => import('./privacidad/privacidad.component').then((m) => m.PrivacidadComponent),
    data: { title: 'Política de privacidad' },
  },
  {
    path: 'terminos',
    loadComponent: () => import('./terminos/terminos.component').then((m) => m.TerminosComponent),
    data: { title: 'Términos y condiciones' },
  },
];

// Dev-only: guarded by environment.production (a compile-time constant once
// fileReplacements swaps in environment.development.ts for dev builds), so
// esbuild's dead-code elimination drops both this route and its lazy chunk
// from the production bundle. Keeps it out of the prerendered route list too,
// since the prerenderer crawls the same route config the app builds with.
if (!environment.production) {
  routes.push({
    path: 'styleguide',
    loadComponent: () =>
      import('./styleguide/styleguide.component').then((m) => m.StyleguideComponent),
  });
}

routes.push({ path: '**', component: NotFoundComponent });

@NgModule({
  imports: [RouterModule.forRoot(routes)],
  exports: [RouterModule]
})
export class AppRoutingModule { }
