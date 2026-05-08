import { Component, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { ActivatedRoute, RouterLink } from '@angular/router';
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
  loading = true;
  forbiddenMessage = '';

  constructor(
    private api: ApiService,
    private route: ActivatedRoute
  ) {}

  get role(): string {
    return (localStorage.getItem('role') || '').toLowerCase();
  }

  get isAdminOrOrganizer(): boolean {
    return this.role === 'admin' || this.role === 'organizer';
  }

  get isJuryOrOrganizer(): boolean {
    return this.role === 'jury' || this.role === 'organizer';
  }

  ngOnInit(): void {
    const forbidden = this.route.snapshot.queryParamMap.get('forbidden');
    if (forbidden === 'admin') {
      this.forbiddenMessage = 'У вас немає доступу до адмін-панелі.';
    } else if (forbidden === 'jury') {
      this.forbiddenMessage = 'У вас немає доступу до панелі журі.';
    }

    this.api.getMyTeams().subscribe({
      next: (teams: any) => {
        this.teams = teams;
        this.loading = false;
      },
      error: () => {
        this.loading = false;
      }
    });
  }
}
