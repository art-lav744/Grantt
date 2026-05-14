import { ChangeDetectorRef, Component, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { ActivatedRoute, Router } from '@angular/router';
import { ApiService } from '../../services/api';

@Component({
  selector: 'app-team-detail',
  standalone: true,
  imports: [CommonModule, FormsModule],
  templateUrl: './team-detail.html',
  styleUrl: './team-detail.scss',
})
export class TeamDetail implements OnInit {
  team: any = null;
  submissions: any[] = [];
  error = '';
  loading = true;
  isCaptain = false;
  memberEmail = '';
  memberSaving = false;
  memberMessage = '';
  memberError = '';

  constructor(
    private route: ActivatedRoute,
    private router: Router,
    private api: ApiService,
    private cdr: ChangeDetectorRef
  ) {}

  ngOnInit(): void {
    const id = Number(this.route.snapshot.paramMap.get('id'));
    this.loadTeam(id);
  }

  private loadTeam(id: number): void {
    this.api.getTeam(id).subscribe({
      next: (team: any) => {
        this.team = team;
        this.submissions = team?.submissions || [];
        this.isCaptain = !!team?.is_captain;
        this.loading = false;
        this.cdr.detectChanges();
      },
      error: () => {
        this.error = 'Не вдалося завантажити команду';
        this.loading = false;
        this.cdr.detectChanges();
      }
    });
  }

  get canManageMembers(): boolean {
    if (!this.isCaptain || !this.team?.tournament) return false;

    const tournament = this.team.tournament;
    const status = String(tournament?.status || tournament?.logical_status || '').toLowerCase();
    if (['closed', 'archived', 'finished', 'completed'].includes(status)) return false;

    const regEnd = tournament?.reg_end ? new Date(tournament.reg_end) : null;
    if (regEnd && !Number.isNaN(regEnd.getTime()) && regEnd.getTime() <= Date.now()) return false;

    return ['registration', 'open', ''].includes(status);
  }

  get canSubmitWork(): boolean {
    return this.isCaptain && Boolean(this.team?.current_round_id);
  }

  goToSubmit(): void {
    const firstRoundId = this.team?.current_round_id || this.team?.rounds?.[0]?.id;
    if (this.team?.id && firstRoundId) {
      this.router.navigate(['/teams', this.team.id, 'rounds', firstRoundId, 'submit']);
    }
  }

  addMember(): void {
    if (!this.canManageMembers || !this.team?.id || !this.memberEmail.trim()) return;

    this.memberSaving = true;
    this.memberError = '';
    this.memberMessage = '';

    this.api.addTeamMember(this.team.id, { email: this.memberEmail.trim() }).subscribe({
      next: () => {
        this.memberEmail = '';
        this.memberSaving = false;
        this.memberMessage = 'Учасника додано.';
        this.loadTeam(this.team.id);
        this.cdr.detectChanges();
      },
      error: (err: any) => {
        this.memberError = this.extractError(err) || 'Не вдалося додати учасника.';
        this.memberSaving = false;
        this.cdr.detectChanges();
      }
    });
  }

  removeMember(member: any): void {
    if (!this.canManageMembers || !this.team?.id || !member?.id) return;

    this.api.deleteTeamMember(this.team.id, member.id).subscribe({
      next: () => {
        this.memberMessage = 'Учасника прибрано.';
        this.memberError = '';
        this.loadTeam(this.team.id);
        this.cdr.detectChanges();
      },
      error: (err: any) => {
        this.memberError = this.extractError(err) || 'Не вдалося прибрати учасника.';
        this.cdr.detectChanges();
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
