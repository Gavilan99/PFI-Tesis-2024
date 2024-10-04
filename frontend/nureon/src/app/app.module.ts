import { NgModule } from '@angular/core';
import { BrowserModule, provideClientHydration } from '@angular/platform-browser';
import { BrowserAnimationsModule } from '@angular/platform-browser/animations';
import { ReactiveFormsModule, FormsModule } from '@angular/forms';
import { provideAnimationsAsync } from '@angular/platform-browser/animations/async';
import { HttpClientModule } from '@angular/common/http';

import { MatFormFieldModule } from '@angular/material/form-field';
import { MatInputModule } from '@angular/material/input';
import { MatDatepickerModule } from '@angular/material/datepicker';
import { MatNativeDateModule } from '@angular/material/core'; 
import { MatSelectModule } from '@angular/material/select';
import { MatButtonModule } from '@angular/material/button';
import { MatCardModule } from '@angular/material/card';
import { MatSidenavModule } from '@angular/material/sidenav';  
import { MatIconModule } from '@angular/material/icon';      
import { MatToolbarModule } from '@angular/material/toolbar';  
import { MatListModule } from '@angular/material/list';       
import { MatDialogModule } from '@angular/material/dialog'; 
import { MatMenuModule } from '@angular/material/menu'; // Added Menu module
import { MatIconRegistry } from '@angular/material/icon';

import { AppRoutingModule } from './app-routing.module';  // Import the new AppRoutingModule
import { AppComponent } from './app.component';
import { LandingPageComponent } from './landing-page/landing-page.component';
import { LoginDialogComponent } from './login-dialog/login-dialog.component';
import { SignupDialogComponent } from './signup-dialog/signup-dialog.component';
import { MainScreenComponent } from './main-screen/main-screen.component';
import { TestComponent } from './test/test.component';
import { ResultsComponent } from './results/results.component';
import { AboutEnneatypeComponent } from './about-enneatype/about-enneatype.component';
import { AboutUsComponent } from './about-us/about-us.component';
import { ContactComponent } from './contact/contact.component';
import { ProfileComponent } from './profile/profile.component';

@NgModule({
  declarations: [
    AppComponent,
    LoginDialogComponent,
    SignupDialogComponent,
    MainScreenComponent,
    LandingPageComponent,
    TestComponent,
    ResultsComponent,
    AboutEnneatypeComponent,
    AboutUsComponent,
    ContactComponent,
    ProfileComponent,
  ],
  imports: [
    BrowserModule,
    BrowserAnimationsModule,
    ReactiveFormsModule,
    FormsModule,
    AppRoutingModule,  // Use the AppRoutingModule here
    MatFormFieldModule,
    MatInputModule,
    MatDatepickerModule,
    MatNativeDateModule,
    MatSelectModule,
    MatButtonModule,
    MatCardModule,
    MatSidenavModule,    // Sidenav module
    MatIconModule,       // Icon module
    MatToolbarModule,    // Toolbar module
    MatListModule,       // List module
    MatDialogModule,
    MatMenuModule,
    HttpClientModule
  ],
  providers: [
    provideClientHydration(),
    provideAnimationsAsync()
  ],
  bootstrap: [AppComponent]
})
export class AppModule { }
