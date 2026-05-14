import { ChangeDetectorRef, Component, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormBuilder, FormGroup, ReactiveFormsModule, Validators } from '@angular/forms';
import { ActivatedRoute, Router, RouterLink } from '@angular/router';
import { ApiService } from '../../services/api';

@Component({
  selector: 'app-tournament-edit',
  standalone: true,
  imports: [CommonModule, ReactiveFormsModule, RouterLink],
  templateUrl: './tournament-edit.html',
  styleUrl: './tournament-edit.scss'
})
export class TournamentEdit implements OnInit {
  tournamentId = 0;
  isCreate = false;
  form: FormGroup;
  loading = true;
  saving = false;
  error = '';
  message = '';

  constructor(
    private fb: FormBuilder,
    private route: ActivatedRoute,
    private router: Router,
    private api: ApiService,
    private cdr: ChangeDetectorRef
  ) {
    this.form = this.fb.group({
      title: ['', Validators.required],
      description: ['', Validators.required],
      status: ['registration', Validators.required],
      reg_start: ['', Validators.required],
      reg_end: ['', Validators.required],
      start_time: ['', Validators.required],
      end_time: ['', Validators.required],
      max_teams: [10, [Validators.required, Validators.min(1)]],
      max_rounds: [1, [Validators.required, Validators.min(1)]],
      min_team_members: [2, [Validators.required, Validators.min(1)]],
      max_team_members: [5, [Validators.required, Validators.min(1)]],
      hide_teams_until_registration_end: [false]
    });
  }

  ngOnInit(): void {
    this.tournamentId = Number(this.route.snapshot.paramMap.get('id'));
    this.isCreate = !this.tournamentId;

    if (this.isCreate) {
      this.loading = false;
      this.cdr.detectChanges();
      return;
    }

    this.api.getTournament(this.tournamentId).subscribe({
      next: (tournament: any) => {
        this.form.patchValue({
          title: tournament?.title || '',
          description: tournament?.description || '',
          status: this.toFormStatus(tournament?.status),
          reg_start: this.toDateTimeLocal(tournament?.reg_start),
          reg_end: this.toDateTimeLocal(tournament?.reg_end),
          start_time: this.toDateTimeLocal(tournament?.start_time),
          end_time: this.toDateTimeLocal(tournament?.end_time),
          max_teams: tournament?.max_teams || 10,
          max_rounds: tournament?.max_rounds || 1,
          min_team_members: tournament?.min_team_members || 2,
          max_team_members: tournament?.max_team_members || 5,
          hide_teams_until_registration_end: Boolean(tournament?.hide_teams_until_registration_end)
        });
        this.loading = false;
        this.cdr.detectChanges();
      },
      error: () => {
        this.error = 'Не вдалося завантажити турнір.';
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
    this.message = '';

    const value = this.form.value;
    const payload = {
      title: value.title,
      description: value.description,
      status: this.toApiStatus(value.status),
      reg_start: this.toApiDateTime(value.reg_start),
      reg_end: this.toApiDateTime(value.reg_end),
      start_time: this.toApiDateTime(value.start_time),
      end_time: this.toApiDateTime(value.end_time),
      max_teams: value.max_teams,
      max_rounds: value.max_rounds,
      min_team_members: value.min_team_members,
      max_team_members: value.max_team_members,
      hide_teams_until_registration_end: value.hide_teams_until_registration_end
    };

    const request$ = this.isCreate
      ? this.api.createTournament(payload)
      : this.api.updateTournament(this.tournamentId, payload);

    request$.subscribe({
      next: (tournament: any) => this.router.navigate(['/tournaments', tournament?.id || this.tournamentId]),
      error: (err: any) => {
        console.error('Tournament update error:', err);
        this.error = this.extractError(err) || 'Не вдалося зберегти турнір.';
        this.saving = false;
        this.cdr.detectChanges();
      }
    });
  }


  private toApiDateTime(value: any): string {
    if (!value) return '';
    const date = new Date(value);
    return Number.isNaN(date.getTime()) ? String(value) : date.toISOString();
  }

  private toDateTimeLocal(value: any): string {
    if (!value) return '';
    const date = new Date(value);
    if (Number.isNaN(date.getTime())) return String(value).slice(0, 16);
    const offsetMs = date.getTimezoneOffset() * 60000;
    return new Date(date.getTime() - offsetMs).toISOString().slice(0, 16);
  }

  private toFormStatus(status: any): string {
    if (status === 'open') return 'active';
    if (status === 'closed' || status === 'archived') return 'completed';
    return status || 'registration';
  }

  private toApiStatus(status: any): string {
    if (status === 'active') return 'open';
    if (status === 'completed') return 'closed';
    return status || 'registration';
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
