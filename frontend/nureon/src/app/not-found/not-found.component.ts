import { Component } from '@angular/core';
import { RouterLink } from '@angular/router';

// Real 404: the wildcard route used to silently redirect to '/', which
// hides that the path didn't match anything. This renders a distinct,
// dedicated not-found screen instead.
@Component({
  selector: 'app-not-found',
  standalone: true,
  imports: [RouterLink],
  templateUrl: './not-found.component.html',
})
export class NotFoundComponent {}
