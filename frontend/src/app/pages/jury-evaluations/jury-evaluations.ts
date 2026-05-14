import { ChangeDetectorRef, Component, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { RouterLink } from '@angular/router';
import { ApiService } from '../../services/api';

@Component({
  selector: 'app-jury-evaluations',
  standalone: true,
  imports: [CommonModule, RouterLink],
  templateUrl: './jury-evaluations.html',
  styleUrl: './jury-evaluations.scss'
})
export class JuryEvaluations implements OnInit {
  evaluations: any[] = [];
  filteredEvaluations: any[] = [];
  activeFilter: 'all' | 'pending' | 'evaluated' = 'all';
  activeSort: 'status' | 'team' | 'round' = 'status';
  readonly statusFilters: Array<{ value: 'all' | 'pending' | 'evaluated'; label: string }> = [
    { value: 'all', label: 'Усі' },
    { value: 'pending', label: 'Очікують' },
    { value: 'evaluated', label: 'Оцінені' }
  ];
  readonly sortOptions: Array<{ value: 'status' | 'team' | 'round'; label: string }> = [
    { value: 'status', label: 'За статусом' },
    { value: 'team', label: 'За командою' },
    { value: 'round', label: 'За раундом' }
  ];
  loading = true;
  error = '';

  get doneCount(): number {
    return this.evaluations.filter(item => this.isEvaluationDone(item)).length;
  }

  get pendingCount(): number {
    return Math.max(this.evaluations.length - this.doneCount, 0);
  }

  constructor(private api: ApiService, private cdr: ChangeDetectorRef) {}

  ngOnInit(): void {
    this.api.getMyEvaluations().subscribe({
      next: (items: any) => {
        this.evaluations = Array.isArray(items) ? items : [];
        this.applyView();
        this.loading = false;
        this.cdr.detectChanges();
      },
      error: () => {
        this.error = 'Не вдалося завантажити роботи для оцінювання.';
        this.loading = false;
        this.cdr.detectChanges();
      }
    });
  }

  setFilter(filter: 'all' | 'pending' | 'evaluated'): void {
    this.activeFilter = filter;
    this.applyView();
  }

  setSort(sort: 'status' | 'team' | 'round'): void {
    this.activeSort = sort;
    this.applyView();
  }

  filterCount(filter: 'all' | 'pending' | 'evaluated'): number {
    if (filter === 'all') {
      return this.evaluations.length;
    }

    return this.evaluations.filter(item => this.evaluationViewStatus(item) === filter).length;
  }

  evaluationStatusLabel(evaluation: any): string {
    return this.isEvaluationDone(evaluation) ? 'Оцінено' : 'Очікує';
  }

  evaluationViewStatus(evaluation: any): 'pending' | 'evaluated' {
    return this.isEvaluationDone(evaluation) ? 'evaluated' : 'pending';
  }

  private applyView(): void {
    const filtered = this.activeFilter === 'all'
      ? [...this.evaluations]
      : this.evaluations.filter(item => this.evaluationViewStatus(item) === this.activeFilter);

    this.filteredEvaluations = filtered.sort((a, b) => this.compareEvaluations(a, b));
  }

  private compareEvaluations(a: any, b: any): number {
    if (this.activeSort === 'team') {
      return this.compareText(a?.team_name, b?.team_name);
    }

    if (this.activeSort === 'round') {
      return this.compareText(a?.round_title, b?.round_title) || this.compareText(a?.team_name, b?.team_name);
    }

    const statusDiff = Number(this.isEvaluationDone(a)) - Number(this.isEvaluationDone(b));
    return statusDiff || this.compareText(a?.team_name, b?.team_name);
  }

  private compareText(a: any, b: any): number {
    return String(a || '').localeCompare(String(b || ''), 'uk', { numeric: true, sensitivity: 'base' });
  }

  private isEvaluationDone(item: any): boolean {
    const status = String(item?.status || '').toLowerCase();
    return item?.is_scored || ['done', 'scored', 'completed', 'evaluated'].includes(status);
  }
}
