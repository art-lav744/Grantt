import { ChangeDetectorRef, Component, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { ActivatedRoute, Router } from '@angular/router';
import { ApiService } from '../../services/api';

@Component({
  selector: 'app-team-detail',
  standalone: true,
  imports: [CommonModule],
  templateUrl: './team-detail.html',
  styleUrl: './team-detail.scss',
})
export class TeamDetail implements OnInit {
  team: any = null;
  submissions: any[] = [];
  error = '';
  loading = true;
  isCaptain = false;

  constructor(
    private route: ActivatedRoute,
    private router: Router,
    private api: ApiService,
    private cdr: ChangeDetectorRef
  ) {}

  ngOnInit(): void {
    const id = Number(this.route.snapshot.paramMap.get('id'));

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

  goToSubmit(): void {
    const firstRoundId = this.team?.current_round_id || this.team?.rounds?.[0]?.id;
    if (this.team?.id && firstRoundId) {
      this.router.navigate(['/teams', this.team.id, 'rounds', firstRoundId, 'submit']);
    }
  }

  goToAddMember(): void {
    if (this.team?.tournament_id) {
      this.router.navigate(['/tournaments', this.team.tournament_id, 'create-team']);
    }
  }
}
