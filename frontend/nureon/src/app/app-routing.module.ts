import { NgModule } from '@angular/core';
import { RouterModule, Routes } from '@angular/router';
import { PlaceholderComponent } from './placeholder/placeholder.component';
import { NotFoundComponent } from './not-found/not-found.component';
import { LandingComponent } from './landing/landing.component';
import { RegistroComponent } from './registro/registro.component';
import { IngresarComponent } from './ingresar/ingresar.component';
import { sessionGuard } from './core/guards/session.guard';
import { resultAvailableGuard } from './core/guards/result-available.guard';
import { environment } from '../environments/environment';

const routes: Routes = [
  { path: '', component: LandingComponent, data: { title: 'Descubrí tu eneatipo' } },
  { path: 'registro', component: RegistroComponent, data: { title: 'Registro' } },
  { path: 'ingresar', component: IngresarComponent, data: { title: 'Ingresar' } },
  {
    path: 'inicio',
    component: PlaceholderComponent,
    data: { title: 'Inicio' },
    canActivate: [sessionGuard],
  },
  {
    path: 'test',
    component: PlaceholderComponent,
    data: { title: 'Test' },
    canActivate: [sessionGuard],
  },
  {
    path: 'resultados',
    component: PlaceholderComponent,
    data: { title: 'Resultados' },
    canActivate: [resultAvailableGuard],
  },
  {
    path: 'resultados/:attemptId',
    component: PlaceholderComponent,
    data: { title: 'Resultado de intento' },
    canActivate: [resultAvailableGuard],
  },
  {
    path: 'perfil',
    component: PlaceholderComponent,
    data: { title: 'Perfil' },
    canActivate: [sessionGuard],
  },
  { path: 'eneagrama', component: PlaceholderComponent, data: { title: 'Sobre el eneagrama' } },
  { path: 'nosotros', component: PlaceholderComponent, data: { title: 'Nosotros' } },
  { path: 'contacto', component: PlaceholderComponent, data: { title: 'Contacto' } },
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
