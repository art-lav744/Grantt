import { Component, OnInit } from '@angular/core';
import { FormBuilder, FormGroup, Validators, ReactiveFormsModule } from '@angular/forms';
import { CommonModule } from '@angular/common';
import { ActivatedRoute, Router } from '@angular/router'; // Додано для навігації
import { trigger, transition, style, animate, query, stagger } from '@angular/animations';
import { TournamentService } from '../services/tournament.service'; // Ваш шлях до сервісу

@Component({
  selector: 'app-round-form',
  standalone: true,
  imports: [CommonModule, ReactiveFormsModule],
  templateUrl: './round-form.component.html',
  styleUrls: ['./round-form.component.scss'],
  animations: [
    trigger('listAnimation', [
      transition(':enter', [
        query('.card', [
          style({ opacity: 0, transform: 'translateY(30px)' }),
          stagger(200, [
            animate('500ms ease-out', style({ opacity: 1, transform: 'translateY(0)' }))
          ])
        ], { optional: true })
      ])
    ])
  ]
})
export class RoundFormComponent implements OnInit {
  roundForm: FormGroup;
  tournamentId: string | null = null;
  tournament: any = null; // Тепер дані завантажуються з сервера
  isLoading = true;

  constructor(
    private fb: FormBuilder,
    private route: ActivatedRoute,
    private router: Router,
    private tournamentService: TournamentService
  ) {
    this.roundForm = this.fb.group({
      title: ['', Validators.required],
      description: [''],
      deadline: ['', Validators.required]
    });
  }

  ngOnInit() {
    // Отримуємо ID турніру з параметрів маршруту (наприклад, /tournaments/5/create-round)
    this.tournamentId = this.route.snapshot.paramMap.get('id');
    
    if (this.tournamentId) {
      this.tournamentService.getTournament(this.tournamentId).subscribe({
        next: (data) => {
          this.tournament = data;
          this.isLoading = false;
        },
        error: (err) => console.error('Помилка завантаження турніру', err)
      });
    }
  }

  submit() {
    if (this.roundForm.valid && this.tournamentId) {
      this.tournamentService.createRound(this.tournamentId, this.roundForm.value).subscribe({
        next: () => {
          // Повертаємося на сторінку турніру після успішного створення
          this.router.navigate(['/tournaments', this.tournamentId]);
        },
        error: (err) => console.error('Помилка при створенні раунду', err)
      });
    }
  }

  goBack() {
    if (this.tournamentId) {
      this.router.navigate(['/tournaments', this.tournamentId]);
    }
  }
}