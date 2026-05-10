import { Component, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { RouterModule, Router } from '@angular/router';
import { HttpClientModule } from '@angular/common/http';
import { finalize } from 'rxjs/operators';
// Імпортуйте ваші реальні сервіси
// import { TeamService } from '../../services/team.service';
// import { AuthService } from '../../services/auth.service';

export interface TournamentTeam {
  id: number;
  name: string;
  image?: string;
  is_captain: boolean;
  status: 'in-progress' | 'completed';
  tournament: {
    id: number;
    title: string;
  };
}

@Component({
  selector: 'app-dashboard',
  standalone: true,
  imports: [CommonModule, RouterModule, HttpClientModule],
  templateUrl: './dashboard_component.html',
  styleUrls: ['./dashboard_component.scss']
})
export class DashboardComponent implements OnInit {
  teams: TournamentTeam[] = [];
  isLoading = true;
  errorMessage = '';
  currentUser: any = null;

  constructor(
    private router: Router,
    // private teamService: TeamService,
    // private authService: AuthService
  ) {}

  ngOnInit(): void {
    this.loadUserData();
    this.loadMyTeams();
  }

  private loadUserData(): void {
    // Отримуємо дані поточного юзера з сервісу авторизації
    // this.currentUser = this.authService.currentUserValue;
  }

  loadMyTeams(): void {
    this.isLoading = true;
    this.errorMessage = '';

    // Реальний виклик до вашого API
    /*
    this.teamService.getMyTeams()
      .pipe(finalize(() => this.isLoading = false))
      .subscribe({
        next: (data) => {
          this.teams = data;
        },
        error: (err) => {
          console.error('Помилка завантаження команд:', err);
          this.errorMessage = 'Не вдалося завантажити список команд. Спробуйте пізніше.';
        }
      });
    */
    
    // Тимчасова заглушка для демонстрації логіки, поки сервіс не підключено:
    setTimeout(() => { this.isLoading = false; }, 1000);
  }

  openTeam(teamId: number): void {
    // Перехід до детальної сторінки команди або турніру
    this.router.navigate(['/dashboard/teams', teamId]);
  }
}