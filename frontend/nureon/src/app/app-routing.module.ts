import { NgModule } from '@angular/core';
import { RouterModule, Routes } from '@angular/router';
import { PlaceholderComponent } from './placeholder/placeholder.component';
import { environment } from '../environments/environment';

const routes: Routes = [
  { path: '', component: PlaceholderComponent },
];

// Dev-only: guarded by environment.production (a compile-time constant once
// fileReplacements swaps in environment.ts for the production build), so
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

routes.push({ path: '**', redirectTo: '' });

@NgModule({
  imports: [RouterModule.forRoot(routes)],
  exports: [RouterModule]
})
export class AppRoutingModule { }
