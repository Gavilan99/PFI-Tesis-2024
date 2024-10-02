import { ComponentFixture, TestBed } from '@angular/core/testing';

import { AboutEnneatypeComponent } from './about-enneatype.component';

describe('AboutEnneatypeComponent', () => {
  let component: AboutEnneatypeComponent;
  let fixture: ComponentFixture<AboutEnneatypeComponent>;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      declarations: [AboutEnneatypeComponent]
    })
    .compileComponents();
    
    fixture = TestBed.createComponent(AboutEnneatypeComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
