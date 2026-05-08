import { Component, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { ActivatedRoute, RouterLink } from '@angular/router';
import { ApiService } from '../../services/api';

@Component({
  selector: 'app-tournament-detail',
  standalone: true,
  imports: [CommonModule, RouterLink],
  templateUrl: './tournament-detail.html',
  styleUrl: './tournament-detail.scss',
})
export class TournamentDetail implements OnInit {
  tournament: any = null;
  teams: any[] = [];
  rounds: any[] = [];
  error = '';

  constructor(
    private route: ActivatedRoute,
    private api: ApiService
  ) {}

  ngOnInit(): void {
    const id = Number(this.route.snapshot.paramMap.get('id'));

    this.api.getTournaments().subscribe({
      next: (items: any) => {
        this.tournament = items.find((t: any) => t.id === id);
      },
      error: () => this.error = 'Не вдалося завантажити турнір'
    });

    this.api.getTournamentTeams(id).subscribe({
      next: (teams: any) => this.teams = teams,
      error: () => this.teams = []
    });

    this.api.getTournamentRounds(id).subscribe({
      next: (rounds: any) => this.rounds = rounds,
      error: () => this.rounds = []
    });
  }
}