import { Component, OnInit } from '@angular/core';
import { ActivatedRoute } from '@angular/router';
import { HttpClient } from '@angular/common/http';
import { trigger, transition, style, animate, query, stagger } from '@angular/animations';

@Component({
  selector: 'app-tournament-teams',
  templateUrl: './tournament-teams.component.html',
  styleUrls: ['./tournament-teams.component.scss'],
  animations: [
    trigger('fadeIn', [
      transition(':enter', [
        style({ opacity: 0 }),
        animate('400ms ease-in', style({ opacity: 1 }))
      ])
    ]),
    trigger('listItem', [
      transition(':enter', [
        style({ opacity: 0, transform: 'translateY(20px)' }),
        animate('300ms {{delay}}ms ease-out', style({ opacity: 1, transform: 'translateY(0)' }))
      ], { params: { delay: 0 } })
    ])
  ]
})
export class TournamentTeamsComponent implements OnInit {
  teams: any[] = [];
  isLoading = true;

  constructor(
    private route: ActivatedRoute,
    private http: HttpClient
  ) {}

  ngOnInit(): void {
    const id = this.route.snapshot.paramMap.get('id');
    if (id) {
      this.loadTeams(id);
    }
  }

  loadTeams(id: string): void {
    // Використовуємо ваш API ендпоінт для отримання команд
    this.http.get<any[]>(`api/tournaments/${id}/teams/`).subscribe({
      next: (data) => {
        this.teams = data;
        this.isLoading = false;
      },
      error: () => this.isLoading = false
    });
  }
}