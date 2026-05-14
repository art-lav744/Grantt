import { ChangeDetectorRef, Component, OnInit } from '@angular/core';
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
  private originalRound: any = null;

  constructor(
    private fb: FormBuilder,
    private route: ActivatedRoute,
    private router: Router,
    private api: ApiService,
    private cdr: ChangeDetectorRef
  ) {
    this.roundId = Number(this.route.snapshot.paramMap.get('id'));
    this.form = this.fb.group({
      title: ['', Validators.required],
      description: ['', Validators.required],
      start: ['', Validators.required],
      end: ['', Validators.required],
      status: ['pending']
    });
  }

  ngOnInit(): void {
    this.api.getRound(this.roundId).subscribe({
      next: (round: any) => {
        this.originalRound = round;
        this.tournamentId = round?.tournament_id || round?.tournament || null;
        this.form.patchValue({
          title: round?.title || '',
          description: round?.description || '',
          start: this.toDateTimeLocal(round?.start_time),
          end: this.toDateTimeLocal(round?.end_time),
          status: this.toFormStatus(round?.status)
        });
        this.loading = false;
        this.cdr.detectChanges();
      },
      error: () => {
        this.error = 'Не вдалося завантажити раунд.';
        this.loading = false;
        this.cdr.detectChanges();
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

    const value = this.form.value;
    this.api.updateRound(this.roundId, {
      title: value.title,
      description: value.description,
      requirements: this.originalRound?.requirements || value.description || value.title,
      start_time: this.toApiDateTime(value.start),
      end_time: this.toApiDateTime(value.end),
      status: this.toApiStatus(value.status),
      criteria_definition: this.originalRound?.evaluation_criteria || 'Technical | 100\nFunctionality | 100'
    }).subscribe({
      next: () => this.router.navigate(this.tournamentId ? ['/tournaments', this.tournamentId] : ['/']),
      error: (err: any) => {
        console.error('Round update error:', err);
        this.error = this.extractError(err) || 'Не вдалося зберегти раунд.';
        this.saving = false;
        this.cdr.detectChanges();
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

  private toFormStatus(status: any): string {
    if (status === 'closed') return 'completed';
    if (status === 'active') return 'active';
    return 'pending';
  }

  private toApiStatus(status: any): string {
    if (status === 'completed') return 'closed';
    if (status === 'active') return 'active';
    return 'draft';
  }

  private toApiDateTime(value: any): string {
    if (!value) return '';
    const date = new Date(value);
    return Number.isNaN(date.getTime()) ? String(value) : date.toISOString();
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
