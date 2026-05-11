import { Component, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormBuilder, FormGroup, ReactiveFormsModule, Validators } from '@angular/forms';
import { ActivatedRoute, Router, RouterLink } from '@angular/router';
import { ApiService } from '../../services/api';

@Component({
  selector: 'app-round-edit',
  standalone: true,
  imports: [CommonModule, ReactiveFormsModule, RouterLink],
  templateUrl: './round-edit.html',
  styleUrl: './round-edit.scss'
})
export class RoundEdit implements OnInit {
  roundId = 0;
  tournamentId: number | null = null;
  form: FormGroup;
  loading = true;
  saving = false;
  error = '';

  constructor(
    private fb: FormBuilder,
    private route: ActivatedRoute,
    private router: Router,
    private api: ApiService
  ) {
    this.roundId = Number(this.route.snapshot.paramMap.get('id'));
    this.form = this.fb.group({
      title: ['', Validators.required],
      description: [''],
      start: ['', Validators.required],
      end: ['', Validators.required],
      status: ['pending']
    });
  }

  ngOnInit(): void {
    this.api.getRound(this.roundId).subscribe({
      next: (round: any) => {
        this.tournamentId = round?.tournament_id || round?.tournament || null;
        this.form.patchValue({
          title: round?.title || '',
          description: round?.description || '',
          start: this.toDateTimeLocal(round?.start),
          end: this.toDateTimeLocal(round?.end),
          status: round?.status || 'pending'
        });
        this.loading = false;
      },
      error: () => {
        this.error = 'Не вдалося завантажити раунд.';
        this.loading = false;
      }
    });
  }

  save(): void {
    if (this.form.invalid) {
      this.form.markAllAsTouched();
      return;
    }

    this.saving = true;
    this.error = '';

    this.api.updateRound(this.roundId, this.form.value).subscribe({
      next: () => this.router.navigate(this.tournamentId ? ['/tournaments', this.tournamentId] : ['/']),
      error: (err: any) => {
        console.error('Round update error:', err);
        this.error = err?.error?.detail || 'Не вдалося зберегти раунд.';
        this.saving = false;
      }
    });
  }

  private toDateTimeLocal(value: any): string {
    if (!value) return '';
    const date = new Date(value);
    if (Number.isNaN(date.getTime())) return String(value).slice(0, 16);
    const offsetMs = date.getTimezoneOffset() * 60000;
    return new Date(date.getTime() - offsetMs).toISOString().slice(0, 16);
  }
}
