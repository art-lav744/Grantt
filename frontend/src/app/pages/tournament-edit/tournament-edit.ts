import { Component, OnInit } from '@angular/core';
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
  form: FormGroup;
  loading = true;
  saving = false;
  error = '';
  message = '';

  constructor(
    private fb: FormBuilder,
    private route: ActivatedRoute,
    private router: Router,
    private api: ApiService
  ) {
    this.form = this.fb.group({
      title: ['', Validators.required],
      description: [''],
      status: ['registration', Validators.required]
    });
  }

  ngOnInit(): void {
    this.tournamentId = Number(this.route.snapshot.paramMap.get('id'));

    this.api.getTournaments().subscribe({
      next: (items: any) => {
        const tournament = Array.isArray(items) ? items.find((item: any) => item.id === this.tournamentId) : null;
        if (tournament) {
          this.form.patchValue({
            title: tournament.title || '',
            description: tournament.description || '',
            status: tournament.status || 'registration'
          });
        }
        this.loading = false;
      },
      error: () => {
        this.error = 'Не вдалося завантажити турнір.';
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
    this.message = '';

    this.api.updateTournament(this.tournamentId, this.form.value).subscribe({
      next: () => this.router.navigate(['/tournaments', this.tournamentId]),
      error: (err: any) => {
        console.error('Tournament update error:', err);
        this.error = err?.error?.detail || 'Не вдалося зберегти зміни турніру.';
        this.saving = false;
      }
    });
  }
}
