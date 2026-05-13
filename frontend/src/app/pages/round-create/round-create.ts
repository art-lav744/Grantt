import { Component } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormBuilder, FormGroup, ReactiveFormsModule, Validators } from '@angular/forms';
import { ActivatedRoute, Router, RouterLink } from '@angular/router';
import { ApiService } from '../../services/api';

@Component({
  selector: 'app-round-create',
  standalone: true,
  imports: [CommonModule, ReactiveFormsModule, RouterLink],
  templateUrl: './round-create.html',
  styleUrl: './round-create.scss'
})
export class RoundCreate {
  tournamentId = 0;
  form: FormGroup;
  saving = false;
  error = '';

  constructor(
    private fb: FormBuilder,
    private route: ActivatedRoute,
    private router: Router,
    private api: ApiService
  ) {
    this.tournamentId = Number(this.route.snapshot.paramMap.get('id'));
    this.form = this.fb.group({
      title: ['', Validators.required],
      description: ['', Validators.required],
      start: ['', Validators.required],
      end: ['', Validators.required]
    });
  }

  save(): void {
    if (this.form.invalid) {
      this.form.markAllAsTouched();
      return;
    }

    this.saving = true;
    this.error = '';

    const value = this.form.value;
    this.api.createRound({
      title: value.title,
      description: value.description,
      requirements: value.description || value.title,
      start_time: value.start,
      end_time: value.end,
      status: 'draft',
      tournament: this.tournamentId,
      criteria_definition: 'Technical | 100\nFunctionality | 100'
    }).subscribe({
      next: () => this.router.navigate(['/tournaments', this.tournamentId]),
      error: (err: any) => {
        console.error('Round create error:', err);
        this.error = this.extractError(err) || 'Не вдалося створити раунд.';
        this.saving = false;
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
