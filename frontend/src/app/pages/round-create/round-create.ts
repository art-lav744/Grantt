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
      description: [''],
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

    this.api.createRound({
      ...this.form.value,
      tournament: this.tournamentId,
      tournament_id: this.tournamentId
    }).subscribe({
      next: () => this.router.navigate(['/tournaments', this.tournamentId]),
      error: (err: any) => {
        console.error('Round create error:', err);
        this.error = err?.error?.detail || 'Не вдалося створити раунд.';
        this.saving = false;
      }
    });
  }
}
