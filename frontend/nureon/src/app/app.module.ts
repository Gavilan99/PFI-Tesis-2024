import { NgModule } from '@angular/core';
import { AsyncPipe } from '@angular/common';
import { BrowserModule, provideClientHydration } from '@angular/platform-browser';
import { BrowserAnimationsModule } from '@angular/platform-browser/animations';
import { provideAnimationsAsync } from '@angular/platform-browser/animations/async';
import { HTTP_INTERCEPTORS, HttpClientModule } from '@angular/common/http';

import { AppRoutingModule } from './app-routing.module';
import { AppComponent } from './app.component';
import { environment } from '../environments/environment';
import { API_SERVICE } from './core/services/api.service';
import { MockApiService } from './core/services/mock-api.service';
import { HttpApiService } from './core/services/http-api.service';
import { AuthTokenInterceptor } from './core/auth/auth-token.interceptor';
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
    // Only against the real backend: the mock has no token to send.
    ...(environment.useMockApi
      ? []
      : [{ provide: HTTP_INTERCEPTORS, useClass: AuthTokenInterceptor, multi: true }]),
  ],
  bootstrap: [AppComponent],
})
export class AppModule { }
