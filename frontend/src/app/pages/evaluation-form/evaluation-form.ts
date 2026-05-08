import { Component, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { ActivatedRoute, Router, RouterLink } from '@angular/router';
import { ApiService } from '../../services/api';

@Component({
  selector: 'app-evaluation-form',
  standalone: true,
  imports: [CommonModule, FormsModule, RouterLink],
  templateUrl: './evaluation-form.html',
  styleUrl: './evaluation-form.scss'
})
export class EvaluationForm implements OnInit {
  evaluation: any = null;
  criteriaScores: any[] = [];
  comment = '';
  loading = true;
  saving = false;
  error = '';

  constructor(
    private route: ActivatedRoute,
    private router: Router,
    private api: ApiService
  ) {}

  ngOnInit(): void {
    const id = Number(this.route.snapshot.paramMap.get('id'));

    this.api.getEvaluation(id).subscribe({
      next: (evaluation: any) => {
        this.evaluation = evaluation;
        this.criteriaScores = (evaluation.criteria_scores || []).map((item: any) => ({ ...item }));
        this.comment = evaluation.comment || '';
        this.loading = false;
      },
      error: () => {
        this.error = 'Не вдалося завантажити оцінювання.';
        this.loading = false;
      }
    });
  }

  save(): void {
    if (!this.evaluation) {
      return;
    }

    this.saving = true;
    this.error = '';

    const payload = {
      comment: this.comment,
      criteria_scores: this.criteriaScores.map((item: any) => ({
        criterion_id: item.criterion_id,
        score: Number(item.score || 0)
      }))
    };

    this.api.saveEvaluation(this.evaluation.id, payload).subscribe({
      next: () => this.router.navigate(['/jury/evaluations']),
      error: (err: any) => {
        this.error = err?.error?.detail || 'Не вдалося зберегти оцінку.';
        this.saving = false;
      }
    });
  }
}
