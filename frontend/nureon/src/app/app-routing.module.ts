import { NgModule } from '@angular/core';
import { RouterModule, Routes } from '@angular/router';
import { LandingPageComponent } from './landing-page/landing-page.component'; 
import { MainScreenComponent } from './main-screen/main-screen.component'; 
import { TestComponent } from './test/test.component';
import { ResultsComponent } from './results/results.component';
import { AboutEnneatypeComponent } from './about-enneatype/about-enneatype.component';
import { AboutUsComponent } from './about-us/about-us.component';
import { ContactComponent } from './contact/contact.component';

const routes: Routes = [
  { path: '', redirectTo: '/landing-page', pathMatch: 'full' },
  { path: 'landing-page', component: LandingPageComponent },
  { 
    path: 'main-screen', 
    component: MainScreenComponent, 
    children: [
      { path: 'test', component: TestComponent },
      { path: 'results', component: ResultsComponent },
      { path: 'about-enneatype', component: AboutEnneatypeComponent },
      { path: 'about-us', component: AboutUsComponent },
      { path: 'contact', component: ContactComponent }
    ]
  },
  { path: '**', redirectTo: '/landing-page' },
];


@NgModule({
  imports: [RouterModule.forRoot(routes)],
  exports: [RouterModule]
})
export class AppRoutingModule { }
