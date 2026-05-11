import { Component, OnInit } from '@angular/core';
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
    nickname: localStorage.getItem('username') || localStorage.getItem('role') || 'користувачу'
  };

  constructor(
    private api: ApiService,
    private router: Router,
    private route: ActivatedRoute
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
    this.errorMessage = '';

    this.api.getMyTeams().subscribe({
      next: (teams: any[]) => {
        this.teams = Array.isArray(teams) ? teams : [];
        this.isLoading = false;
      },
      error: () => {
        this.teams = [];
        this.errorMessage = 'Не вдалося завантажити ваші команди';
        this.isLoading = false;
      }
    });
  }

  openTeam(teamId: number): void {
    this.router.navigate(['/teams', teamId]);
  }
}
