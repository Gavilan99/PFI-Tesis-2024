import { NgModule } from '@angular/core';
import { AsyncPipe } from '@angular/common';
import { BrowserModule, provideClientHydration } from '@angular/platform-browser';
import { BrowserAnimationsModule } from '@angular/platform-browser/animations';
import { provideAnimationsAsync } from '@angular/platform-browser/animations/async';
import { HttpClientModule } from '@angular/common/http';

import { AppRoutingModule } from './app-routing.module';
import { AppComponent } from './app.component';
import { environment } from '../environments/environment';
import { API_SERVICE } from './core/services/api.service';
import { MockApiService } from './core/services/mock-api.service';
import { HttpApiService } from './core/services/http-api.service';
import { HeaderComponent } from './shared/layout/header/header.component';
import { FooterComponent } from './shared/layout/footer/footer.component';

@NgModule({
  declarations: [
    AppComponent,
  ],
  imports: [
    BrowserModule,
    BrowserAnimationsModule,
    AppRoutingModule,
    HttpClientModule,
    AsyncPipe,
    HeaderComponent,
    FooterComponent,
  ],
  providers: [
    provideClientHydration(),
    provideAnimationsAsync(),
    {
      provide: API_SERVICE,
      useClass: environment.useMockApi ? MockApiService : HttpApiService,
    },
  ],
  bootstrap: [AppComponent],
})
export class AppModule { }
