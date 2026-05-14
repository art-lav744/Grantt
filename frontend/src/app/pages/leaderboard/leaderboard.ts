import { ChangeDetectorRef, Component, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { ActivatedRoute, RouterLink } from '@angular/router';
import { ApiService } from '../../services/api';

type SortDirection = 'asc' | 'desc';
type SortKey =
  | 'rank'
  | 'team'
  | 'average'
  | 'total'
  | 'rounds'
  | 'submissions'
  | 'evaluations';

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
  sortedLeaderboard: any[] = [];
  loading = true;
  error = '';

  sortKey: SortKey = 'rank';
  sortDirection: SortDirection = 'asc';

  readonly sortOptions: { key: SortKey; label: string }[] = [
    { key: 'rank', label: 'Місце' },
    { key: 'team', label: 'Команда' },
    { key: 'average', label: 'Середній бал' },
    { key: 'total', label: 'Загальний результат' },
    { key: 'rounds', label: 'Раунди' },
    { key: 'submissions', label: 'Подані роботи' },
    { key: 'evaluations', label: 'Оцінки' }
  ];

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
        this.applySort();
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

  setSort(key: SortKey): void {
    if (this.sortKey === key) {
      this.sortDirection = this.sortDirection === 'asc' ? 'desc' : 'asc';
    } else {
      this.sortKey = key;
      this.sortDirection = key === 'rank' || key === 'team' ? 'asc' : 'desc';
    }

    this.applySort();
  }

  sortIndicator(key: SortKey): string {
    if (this.sortKey !== key) return '';
    return this.sortDirection === 'asc' ? '↑' : '↓';
  }

  scoreClass(value: any): string {
    const score = Number(value || 0);
    if (score >= 80) return 'score-high';
    if (score >= 60) return 'score-medium';
    return 'score-low';
  }

  private applySort(): void {
    const direction = this.sortDirection === 'asc' ? 1 : -1;
    this.sortedLeaderboard = [...this.leaderboard].sort((left, right) => {
      const a = this.valueForSort(left, this.sortKey);
      const b = this.valueForSort(right, this.sortKey);

      if (typeof a === 'string' || typeof b === 'string') {
        return String(a).localeCompare(String(b), 'uk') * direction;
      }

      return ((Number(a) || 0) - (Number(b) || 0)) * direction;
    });
  }

  private valueForSort(entry: any, key: SortKey): number | string {
    switch (key) {
      case 'team':
        return entry?.team_name || '';
      case 'average':
        return Number(entry?.average_score || 0);
      case 'total':
        return Number(entry?.total_raw_score || 0);
      case 'rounds':
        return Number(entry?.rounds_scored || 0);
      case 'submissions':
        return Number(entry?.submissions_count || 0);
      case 'evaluations':
        return Number(entry?.evaluations_count || 0);
      case 'rank':
      default:
        return Number(entry?.rank || 0);
    }
  }
}
