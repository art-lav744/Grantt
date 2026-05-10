import { Component, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { ActivatedRoute } from '@angular/router';
import { TournamentService } from '../services/tournament.service'; // Припускаємо наявність сервісу
import { trigger, transition, style, animate } from '@angular/animations';

@Component({
  selector: 'app-tournament-detail',
  standalone: true,
  imports: [CommonModule],
  templateUrl: './tournament-detail.component.html',
  styleUrls: ['./tournament-detail.component.scss'],
  animations: [
    trigger('slideUp', [
      transition(':enter', [
        style({ opacity: 0, transform: 'translateY(20px)' }),
        animate('400ms ease-out', style({ opacity: 1, transform: 'translateY(0)' }))
      ])
    ])
  ]
})
export class TournamentDetailComponent implements OnInit {
  tournament: any = null;
  teams: any[] = [];
  rounds: any[] = [];
  canManage: boolean = false;

  constructor(
    private route: ActivatedRoute,
    private tournamentService: TournamentService
  ) {}

  ngOnInit(): void {
    const id = this.route.snapshot.paramMap.get('id');
    if (id) {
      this.loadTournamentData(+id);
    }
  }

  loadTournamentData(id: number): void {
    this.tournamentService.getTournamentById(id).subscribe({
      next: (data) => {
        this.tournament = data;
        this.teams = data.teams || [];
        this.rounds = data.rounds || [];
        this.canManage = data.is_organizer; // Реальна перевірка прав
      },
      error: (err) => console.error('Помилка при завантаженні турніру', err)
    });
  }

  onCoverUpload(event: any): void {
    const file = event.target.files[0];
    if (file && this.tournament) {
      const formData = new FormData();
      formData.append('cover', file);
      
      this.tournamentService.uploadCover(this.tournament.id, formData).subscribe(res => {
        this.tournament.cover_url = res.url;
      });
    }
  }

  addRound(): void {
    // Логіка відкриття модалки або переходу на сторінку створення раунду
  }
}