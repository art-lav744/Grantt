import { ChangeDetectorRef, Component, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { Router, RouterLink, ActivatedRoute } from '@angular/router';
import { ApiService } from '../../services/api';

@Component({
  selector: 'app-dashboard',
  standalone: true,
  imports: [CommonModule, RouterLink],
  templateUrl: './dashboard.html',
  styleUrl: './dashboard.scss'
})
export class Dashboard implements OnInit {
  teams: any[] = [];
  isLoading = true;
  errorMessage = '';
  forbiddenMessage = '';
  currentUser: any = {
    nickname: localStorage.getItem('nickname') || localStorage.getItem('username') || 'користувачу'
  };

  get role(): string {
    return (localStorage.getItem('role') || '').toLowerCase();
  }

  get isAdminOrOrganizer(): boolean {
    return this.role === 'admin' || this.role === 'organizer';
  }

  get isJury(): boolean {
    return this.role === 'jury' || this.role === 'organizer';
  }

  constructor(
    private api: ApiService,
    private router: Router,
    private route: ActivatedRoute,
    private cdr: ChangeDetectorRef
  ) {}

  ngOnInit(): void {
    const forbidden = this.route.snapshot.queryParamMap.get('forbidden');
    if (forbidden === 'admin') {
      this.forbiddenMessage = 'У вас немає доступу до адмін-панелі.';
    } else if (forbidden === 'jury') {
      this.forbiddenMessage = 'У вас немає доступу до панелі журі.';
    }
    this.loadMyTeams();
  }

  loadMyTeams(): void {
    this.isLoading = true;
    this.errorMessage = this.forbiddenMessage;

    this.api.getMyTeams().subscribe({
      next: (teams: any[]) => {
        this.teams = Array.isArray(teams) ? teams.map(team => this.normalizeTeam(team)) : [];
        this.isLoading = false;
        this.cdr.detectChanges();
      },
      error: () => {
        this.teams = [];
        this.errorMessage = 'Не вдалося завантажити ваші команди';
        this.isLoading = false;
        this.cdr.detectChanges();
      }
    });
  }

  openTeam(teamId: number): void {
    this.router.navigate(['/teams', teamId]);
  }

  private normalizeTeam(team: any): any {
    const email = (localStorage.getItem('email') || '').toLowerCase();
    const isCaptain = Boolean(team?.is_captain) || String(team?.captain_email || '').toLowerCase() === email;
    const tournamentStatus = String(team?.tournament?.status || '').toLowerCase();

    return {
      ...team,
      image: team?.image || team?.image_path || '/assets/team-placeholder.png',
      tournament: team?.tournament || { title: `Турнір #${team?.tournament_id || ''}`.trim() },
      is_captain: isCaptain,
      status: ['closed', 'archived', 'finished', 'completed'].includes(tournamentStatus) ? 'completed' : 'in-progress'
    };
  }
}
