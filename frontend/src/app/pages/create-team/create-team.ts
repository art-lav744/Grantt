import { Component, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { ActivatedRoute, RouterLink } from '@angular/router';
import { ApiService } from '../../services/api';

@Component({
  selector: 'app-create-team',
  standalone: true,
  imports: [CommonModule, RouterLink],
  templateUrl: './create-team.html',
  styleUrl: './create-team.scss',
})
export class CreateTeam implements OnInit {
  tournament: any = { banner_url: '', title: '', description: '', reg_start: null, reg_end: null, status: '' };
  teams: any[] = [];
  rounds: any[] = [];
  files: any[] = [];
  error = '';

  constructor(
    private route: ActivatedRoute,
    private api: ApiService
  ) {}

  get role(): string {
    return (localStorage.getItem('role') || '').toLowerCase();
  }

  get canManageRounds(): boolean {
    return this.role === 'admin' || this.role === 'organizer';
  }

  get canAccessFiles(): boolean {
    return true;
  }

  ngOnInit(): void {
    const id = Number(this.route.snapshot.paramMap.get('id'));

    this.api.getTournaments().subscribe({
      next: (items: any) => {
        this.tournament = Array.isArray(items) ? (items.find((t: any) => t.id === id) || this.tournament) : this.tournament;
        if (!this.tournament) {
          this.error = 'Турнір не знайдено';
        }
      },
      error: () => this.error = 'Не вдалося завантажити турнір'
    });

    this.api.getTournamentTeams(id).subscribe({
      next: (teams: any) => this.teams = Array.isArray(teams) ? teams : [],
      error: () => this.teams = []
    });

    this.api.getTournamentRounds(id).subscribe({
      next: (rounds: any) => this.rounds = Array.isArray(rounds) ? rounds : [],
      error: () => this.rounds = []
    });
  }

  onBannerSelected(event: Event): void {
    const input = event.target as HTMLInputElement;
    const file = input.files?.[0];
    if (!file || !this.tournament) return;

    const reader = new FileReader();
    reader.onload = () => {
      this.tournament = { ...this.tournament, banner_url: reader.result as string };
    };
    reader.readAsDataURL(file);
  }
}
