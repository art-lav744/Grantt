import { ComponentFixture, TestBed } from '@angular/core/testing';

import { Tournaments } from './tournaments';

describe('Tournaments', () => {
  let component: Tournaments;
  let fixture: ComponentFixture<Tournaments>;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [Tournaments],
    }).compileComponents();

    fixture = TestBed.createComponent(Tournaments);
    component = fixture.componentInstance;
    await fixture.whenStable();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
