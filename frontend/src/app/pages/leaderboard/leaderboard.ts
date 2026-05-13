import { ChangeDetectorRef, Component, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { ActivatedRoute, RouterLink } from '@angular/router';
import { ApiService } from '../../services/api';

@Component({
  selector: 'app-leaderboard',
  standalone: true,
  imports: [CommonModule, RouterLink],
  templateUrl: './leaderboard.html',
  styleUrl: './leaderboard.scss'
})
export class Leaderboard implements OnInit {
  tournamentId = 0;
  tournamentTitle = '';
  tournament: any = null;
  isFinal = false;
  leaderboard: any[] = [];
  loading = true;
  error = '';

  constructor(
    private route: ActivatedRoute,
    private api: ApiService,
    private cdr: ChangeDetectorRef
  ) {}

  ngOnInit(): void {
    this.tournamentId = Number(this.route.snapshot.paramMap.get('id'));
    if (!this.tournamentId) {
      this.error = 'Турнір не знайдено.';
      this.loading = false;
      return;
    }

    this.api.getTournamentLeaderboard(this.tournamentId).subscribe({
      next: (payload: any) => {
        this.tournamentTitle = payload?.tournament_title || 'Таблиця лідерів';
        this.tournament = payload?.tournament || { title: this.tournamentTitle };
        this.isFinal = Boolean(payload?.is_final);
        this.leaderboard = Array.isArray(payload?.leaderboard) ? payload.leaderboard : [];
        this.loading = false;
        this.cdr.detectChanges();
      },
      error: () => {
        this.error = 'Не вдалося завантажити таблицю лідерів.';
        this.loading = false;
        this.cdr.detectChanges();
      }
    });
  }

  scoreClass(value: any): string {
    const score = Number(value || 0);
    if (score >= 80) return 'score-high';
    if (score >= 60) return 'score-medium';
    return 'score-low';
  }
}
