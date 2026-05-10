import { Component, OnInit } from '@angular/core';
import { FormBuilder, FormGroup, Validators, ReactiveFormsModule } from '@angular/forms';
import { CommonModule } from '@angular/common';
import { ActivatedRoute, Router } from '@angular/router';
import { HttpClientModule } from '@angular/common/http';
// Імпортуйте ваші сервіси та інтерфейси тут
// import { TournamentService } from '../../services/tournament.service'; 
// import { TeamService } from '../../services/team.service';

@Component({
  selector: 'app-create-team',
  standalone: true,
  imports: [CommonModule, ReactiveFormsModule, HttpClientModule],
  templateUrl: './create-team.component.html',
  styleUrls: ['./create-team.component.scss']
})
export class CreateTeamComponent implements OnInit {
  teamForm: FormGroup;
  tournamentId: string | null = null;
  tournament: any = null; // Буде заповнено з API
  isLoading = true;
  errorMessage = '';

  constructor(
    private fb: FormBuilder,
    private route: ActivatedRoute,
    private router: Router,
    // private tournamentService: TournamentService,
    // private teamService: TeamService
  ) {
    this.teamForm = this.fb.group({
      team_name: ['', [Validators.required, Validators.minLength(3), Validators.maxLength(30)]]
    });
  }

  ngOnInit(): void {
    // 1. Отримуємо ID турніру з URL (наприклад, /tournaments/:id/register)
    this.tournamentId = this.route.snapshot.paramMap.get('id');

    if (this.tournamentId) {
      this.loadTournamentData(this.tournamentId);
    } else {
      this.errorMessage = 'Турнір не знайдено';
      this.isLoading = false;
    }
  }

  loadTournamentData(id: string) {
    // Реальний виклик API через ваш сервіс
    /* this.tournamentService.getTournamentById(id).subscribe({
      next: (data) => {
        this.tournament = data;
        this.isLoading = false;
      },
      error: (err) => {
        this.errorMessage = 'Помилка завантаження даних турніру';
        this.isLoading = false;
      }
    });
    */

    // Тимчасова імітація успішної відповіді, поки сервіс не підключено:
    this.isLoading = false;
    this.tournament = { imageUrl: 'assets/images/default-tournament.jpg', title: 'Завантажений турнір' };
  }

  onSubmit() {
    if (this.teamForm.valid && this.tournamentId) {
      const payload = {
        name: this.teamForm.value.team_name,
        tournament_id: this.tournamentId
      };

      console.log('Відправка на сервер:', payload);

      // Виклик сервісу для створення команди
      /*
      this.teamService.createTeam(payload).subscribe({
        next: (res) => {
          // Перенаправлення в кабінет капітана після успіху
          this.router.navigate(['/dashboard/teams', res.id]);
        },
        error: (err) => {
          this.errorMessage = 'Не вдалося створити команду. Можливо, назва вже зайнята.';
        }
      });
      */
    }
  }
}