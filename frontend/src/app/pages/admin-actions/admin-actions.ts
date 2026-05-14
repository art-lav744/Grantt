import { ChangeDetectorRef, Component, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { RouterLink } from '@angular/router';
import { ApiService } from '../../services/api';

@Component({
  selector: 'app-admin-actions',
  standalone: true,
  imports: [CommonModule, FormsModule, RouterLink],
  templateUrl: './admin-actions.html',
  styleUrl: './admin-actions.scss'
})
export class AdminActions implements OnInit {
  tournaments: any[] = [];
  pendingJuryRegistrations: any[] = [];
  rounds: any[] = [];
  teams: any[] = [];
  selectedTournamentId: number | null = null;
  selectedStatus = 'registration';
  selectedRoundId: number | null = null;
  selectedTeamIdToDelete: number | null = null;
  message = '';
  error = '';

  constructor(private api: ApiService, private cdr: ChangeDetectorRef) {}

  ngOnInit(): void {
    this.loadTournaments();
    this.loadPendingJuryRegistrations();
  }

  loadTournaments(): void {
    this.api.getTournaments().subscribe({
      next: (items: any) => { this.tournaments = items; this.cdr.detectChanges(); },
      error: () => this.error = 'Не вдалося завантажити турніри.'
    });
  }

  loadPendingJuryRegistrations(): void {
    this.api.getPendingJuryRegistrations().subscribe({
      next: (items: any) => { this.pendingJuryRegistrations = items; this.cdr.detectChanges(); },
      error: () => this.pendingJuryRegistrations = []
    });
  }


  onTournamentChanged(): void {
    this.selectedRoundId = null;
    this.selectedTeamIdToDelete = null;
    this.rounds = [];
    this.teams = [];
    if (!this.selectedTournamentId) {
      this.cdr.detectChanges();
      return;
    }
    this.api.getTournamentRounds(this.selectedTournamentId).subscribe({
      next: (items: any) => {
        this.rounds = Array.isArray(items) ? items : [];
        this.cdr.detectChanges();
      },
      error: () => {
        this.rounds = [];
        this.cdr.detectChanges();
      }
    });

    this.api.getTournamentTeams(this.selectedTournamentId).subscribe({
      next: (items: any) => {
        this.teams = Array.isArray(items) ? items : [];
        this.cdr.detectChanges();
      },
      error: () => {
        this.teams = [];
        this.cdr.detectChanges();
      }
    });
  }

  updateStatus(): void {
    if (!this.selectedTournamentId) {
      this.error = 'Оберіть турнір.';
      return;
    }

    this.api.updateTournamentStatus(this.selectedTournamentId, this.selectedStatus).subscribe({
      next: () => {
        this.message = 'Статус турніру оновлено.';
        this.error = '';
        this.loadTournaments();
      },
      error: () => this.error = 'Не вдалося оновити статус турніру.'
    });
  }

  distributeRound(): void {
    if (!this.selectedRoundId) {
      this.error = 'Введіть ID раунду.';
      return;
    }

    this.api.distributeRound(this.selectedRoundId).subscribe({
      next: (result: any) => {
        this.message = result?.status || 'Роботи розподілено.';
        this.error = '';
      },
      error: (err: any) => this.error = err?.error?.detail || 'Не вдалося розподілити роботи.'
    });
  }

  deleteTeam(): void {
    if (!this.selectedTournamentId) {
      this.error = 'Оберіть турнір.';
      return;
    }

    if (!this.selectedTeamIdToDelete) {
      this.error = 'Оберіть команду з цього турніру.';
      return;
    }

    this.api.deleteTeam(this.selectedTeamIdToDelete).subscribe({
      next: () => {
        this.message = 'Команду видалено.';
        this.error = '';
        this.selectedTeamIdToDelete = null;
        this.onTournamentChanged();
      },
      error: () => this.error = 'Не вдалося видалити команду.'
    });
  }

  reviewJuryRegistration(registrationId: number, status: string): void {
    this.api.reviewJuryRegistration(registrationId, status).subscribe({
      next: () => {
        this.message = status === 'approved' ? 'Заявку журі підтверджено.' : 'Заявку журі відхилено.';
        this.error = '';
        this.loadPendingJuryRegistrations();
      },
      error: () => this.error = 'Не вдалося обробити заявку журі.'
    });
  }
}
