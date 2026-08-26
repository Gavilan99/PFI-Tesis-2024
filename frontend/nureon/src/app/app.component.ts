import { Component, Inject, Injector, PLATFORM_ID } from '@angular/core';
import { isPlatformBrowser } from '@angular/common';
import { environment } from '../environments/environment';
import { installDevTools } from './core/dev-tools';

@Component({
  selector: 'app-root',
  templateUrl: './app.component.html',
  styleUrl: './app.component.css'
})
export class AppComponent {
  title = 'nureon';

  constructor(injector: Injector, @Inject(PLATFORM_ID) platformId: object) {
    if (!environment.production && isPlatformBrowser(platformId)) {
      installDevTools(injector);
    }
  }
}
