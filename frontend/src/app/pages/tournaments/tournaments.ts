import { ChangeDetectorRef, Component, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { RouterLink } from '@angular/router';
import { ApiService } from '../../services/api';

@Component({
  selector: 'app-tournaments',
  standalone: true,
  imports: [CommonModule, RouterLink],
  templateUrl: './tournaments.html',
  styleUrls: ['./tournaments.scss']
})
export class Tournaments implements OnInit {
  tournaments: any[] = [];
  filteredTournaments: any[] = [];
  activeStatus: 'all' | 'registration' | 'running' | 'finished' = 'all';
  isLoading = true;
  errorMessage = '';

  constructor(
    private api: ApiService,
    private cdr: ChangeDetectorRef
  ) {}

  ngOnInit(): void {
    this.loadTournaments();
  }

  loadTournaments(): void {
    this.isLoading = true;
    this.errorMessage = '';

    this.api.getTournaments().subscribe({
      next: (items: any[]) => {
        this.tournaments = Array.isArray(items) ? items.map(item => this.normalizeTournament(item)) : [];
        this.applyFilter(this.activeStatus);
        this.isLoading = false;
        this.cdr.detectChanges();
      },
      error: () => {
        this.tournaments = [];
        this.errorMessage = 'Не вдалося завантажити турніри';
        this.isLoading = false;
        this.cdr.detectChanges();
      }
    });
  }

  applyFilter(status: 'all' | 'registration' | 'running' | 'finished'): void {
    this.activeStatus = status;
    if (status === 'all') {
      this.filteredTournaments = [...this.tournaments];
      return;
    }

    this.filteredTournaments = this.tournaments.filter(tournament => tournament.viewStatus === status);
  }

  statusLabel(tournament: any): string {
    if (tournament.viewStatus === 'registration') return 'Реєстрація';
    if (tournament.viewStatus === 'running') return 'Активний';
    if (tournament.viewStatus === 'finished') return 'Завершений';
    return tournament.status || 'Невідомо';
  }

  private normalizeTournament(tournament: any): any {
    const status = String(tournament?.logical_status || tournament?.status || '').toLowerCase();
    const viewStatus = ['registration'].includes(status)
      ? 'registration'
      : ['open', 'active', 'running'].includes(status)
        ? 'running'
        : ['closed', 'archived', 'finished', 'completed'].includes(status)
          ? 'finished'
          : status || 'registration';

    return {
      ...tournament,
      viewStatus
    };
  }
}
