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
  assignableUsers: any[] = [];
  rounds: any[] = [];
  teams: any[] = [];
  selectedTournamentId: number | null = null;
  selectedStatus = 'registration';
  selectedRoundId: number | null = null;
  selectedTeamIdToDelete: number | null = null;
  selectedStaffUserId: number | null = null;
  staffEmail = '';
  staffRole: 'admin' | 'jury' = 'jury';
  message = '';
  error = '';

  constructor(private api: ApiService, private cdr: ChangeDetectorRef) {}

  ngOnInit(): void {
    this.loadTournaments();
    this.loadPendingJuryRegistrations();
    this.loadAssignableUsers();
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

  loadAssignableUsers(): void {
    this.api.getAssignableUsers().subscribe({
      next: (items: any) => {
        this.assignableUsers = Array.isArray(items) ? items : [];
        this.cdr.detectChanges();
      },
      error: () => {
        this.assignableUsers = [];
        this.cdr.detectChanges();
      }
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

  assignStaffRole(): void {
    const email = this.staffEmail.trim().toLowerCase();
    if (!email) {
      this.error = 'Введіть email користувача.';
      return;
    }

    this.api.assignStaffRole({ email, role: this.staffRole }).subscribe({
      next: () => {
        this.message = `Роль для ${email} оновлено.`;
        this.error = '';
        this.selectedStaffUserId = null;
        this.staffEmail = '';
        this.loadAssignableUsers();
        this.cdr.detectChanges();
      },
      error: (err: any) => {
        this.error = this.extractError(err) || 'Не вдалося змінити роль користувача.';
        this.cdr.detectChanges();
      }
    });
  }

  private extractError(err: any): string {
    const payload = err?.error;
    if (!payload) return '';
    if (typeof payload === 'string') return payload;
    if (payload.detail || payload.message) return String(payload.detail || payload.message);
    const firstValue = Object.values(payload)[0];
    return Array.isArray(firstValue) ? String(firstValue[0]) : String(firstValue || '');
  }
}
