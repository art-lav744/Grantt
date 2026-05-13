import { ChangeDetectorRef, Component, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormArray, FormBuilder, FormGroup, ReactiveFormsModule, Validators } from '@angular/forms';
import { ActivatedRoute, Router, RouterLink } from '@angular/router';
import { ApiService } from '../../services/api';

@Component({
  selector: 'app-create-team',
  standalone: true,
  imports: [CommonModule, ReactiveFormsModule, RouterLink],
  templateUrl: './create-team.html',
  styleUrl: './create-team.scss',
})
export class CreateTeam implements OnInit {
  tournamentId = 0;
  tournament: any = null;
  form: FormGroup;
  loading = true;
  saving = false;
  error = '';

  constructor(
    private fb: FormBuilder,
    private route: ActivatedRoute,
    private router: Router,
    private api: ApiService,
    private cdr: ChangeDetectorRef
  ) {
    this.form = this.fb.group({
      name: [''],
      team_name: ['', [Validators.required, Validators.minLength(3)]],
      captain_name: [localStorage.getItem('nickname') || localStorage.getItem('username') || '', Validators.required],
      captain_email: [localStorage.getItem('email') || '', [Validators.required, Validators.email]],
      members: this.fb.array([])
    });
  }

  get members(): FormArray {
    return this.form.get('members') as FormArray;
  }

  get minMembers(): number {
    return Number(this.tournament?.min_team_members || 1);
  }

  get maxMembers(): number {
    return Number(this.tournament?.max_team_members || 5);
  }

  get canAddMember(): boolean {
    return this.members.length + 1 < this.maxMembers;
  }

  ngOnInit(): void {
    this.tournamentId = Number(this.route.snapshot.paramMap.get('id'));
    if (!this.tournamentId) {
      this.error = 'Турнір не знайдено.';
      this.loading = false;
      return;
    }

    this.api.getTournament(this.tournamentId).subscribe({
      next: (tournament: any) => {
        this.tournament = { ...tournament, imageUrl: tournament?.imageUrl || tournament?.banner_url || tournament?.cover_url || tournament?.image || '' };
        this.form.patchValue({ team_name: this.form.value.name || this.form.value.team_name });
        this.ensureMinimumMembers();
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

  addMember(): void {
    if (!this.canAddMember) return;
    this.members.push(this.fb.group({
      full_name: [''],
      team_name: ['', [Validators.required, Validators.minLength(3)]],
      email: ['', [Validators.required, Validators.email]]
    }));
  }

  removeMember(index: number): void {
    this.members.removeAt(index);
  }

  save(): void {
    if (this.form.invalid) {
      this.form.markAllAsTouched();
      return;
    }

    this.error = '';
    this.saving = true;
    const value = this.form.value;

    this.api.createTeam({
      tournament_id: this.tournamentId,
      name: value.name || value.team_name,
      captain_name: value.captain_name,
      captain_email: value.captain_email,
      members: value.members || []
    }).subscribe({
      next: (team: any) => this.router.navigate(['/teams', team.id]),
      error: (err: any) => {
        this.error = this.extractError(err) || 'Не вдалося створити команду.';
        this.saving = false;
        this.cdr.detectChanges();
      }
    });
  }

  get teamForm(): FormGroup {
    return this.form;
  }

  onSubmit(): void {
    this.save();
  }

  private ensureMinimumMembers(): void {
    const requiredAdditionalMembers = Math.max(this.minMembers - 1, 0);
    while (this.members.length < requiredAdditionalMembers) {
      this.addMember();
    }
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
