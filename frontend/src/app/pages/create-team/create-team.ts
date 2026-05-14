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
      name: ['', [Validators.required, Validators.minLength(3)]],
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

  get role(): string {
    return (localStorage.getItem('role') || '').toLowerCase();
  }

  get canCreateTeam(): boolean {
    return !this.role || this.role === 'participant';
  }

  get isRegistrationOpen(): boolean {
    if (!this.tournament) return true;
    const status = String(this.tournament?.status || this.tournament?.logical_status || '').toLowerCase();
    if (['closed', 'archived', 'finished', 'completed'].includes(status)) return false;

    const regEnd = this.tournament?.reg_end ? new Date(this.tournament.reg_end) : null;
    if (regEnd && !Number.isNaN(regEnd.getTime()) && regEnd.getTime() <= Date.now()) return false;

    return ['registration', 'open', 'active', 'running', ''].includes(status);
  }

  ngOnInit(): void {
    this.tournamentId = Number(this.route.snapshot.paramMap.get('id'));
    if (!this.tournamentId) {
      this.error = 'Турнір не знайдено.';
      this.loading = false;
      return;
    }

    if (!this.canCreateTeam) {
      this.error = 'Адмін, організатор або журі не можуть реєструватися як учасники турніру.';
      this.loading = false;
      this.cdr.detectChanges();
      return;
    }

    this.api.getTournament(this.tournamentId).subscribe({
      next: (tournament: any) => {
        this.tournament = {
          ...tournament,
          imageUrl: tournament?.imageUrl || tournament?.banner_url || tournament?.cover_image_path || tournament?.image || ''
        };
        this.ensureMinimumMembers();
        this.loading = false;
        if (!this.isRegistrationOpen) {
          this.error = 'Реєстрацію на цей турнір завершено. Змінювати склад команди більше не можна.';
          this.form.disable();
        }
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
    if (!this.canAddMember || !this.isRegistrationOpen) return;
    this.members.push(this.fb.group({
      email: ['', [Validators.required, Validators.email]]
    }));
  }

  removeMember(index: number): void {
    if (!this.isRegistrationOpen) return;
    this.members.removeAt(index);
  }

  save(): void {
    if (!this.canCreateTeam) {
      this.error = 'Тільки учасник може створити команду для участі в турнірі.';
      return;
    }

    if (!this.isRegistrationOpen) {
      this.error = 'Реєстрацію на цей турнір завершено. Створити або змінити команду вже не можна.';
      return;
    }

    if (this.form.invalid) {
      this.form.markAllAsTouched();
      return;
    }

    this.error = '';
    this.saving = true;
    const value = this.form.value;

    this.api.createTeam({
      tournament_id: this.tournamentId,
      name: value.name,
      captain_name: localStorage.getItem('nickname') || localStorage.getItem('username') || '',
      captain_email: localStorage.getItem('email') || '',
      members: (value.members || []).map((member: any) => ({
        email: member.email,
        full_name: member.full_name || member.email
      }))
    }).subscribe({
      next: (team: any) => this.router.navigate(['/teams', team.id]),
      error: (err: any) => {
        this.error = this.extractError(err) || 'Не вдалося створити команду.';
        this.saving = false;
        this.cdr.detectChanges();
      }
    });
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
