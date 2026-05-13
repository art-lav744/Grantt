import { ComponentFixture, TestBed } from '@angular/core/testing';
import { provideHttpClient } from '@angular/common/http';
import { provideRouter } from '@angular/router';

import { TournamentDetail } from './tournament-detail';

describe('TournamentDetail', () => {
  let component: TournamentDetail;
  let fixture: ComponentFixture<TournamentDetail>;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [TournamentDetail],
      providers: [provideHttpClient(), provideRouter([])],
    }).compileComponents();

    fixture = TestBed.createComponent(TournamentDetail);
    component = fixture.componentInstance;
    await fixture.whenStable();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
