import { Component, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { RouterLink } from '@angular/router';
import { ApiService } from '../../services/api';

@Component({
  selector: 'app-tournaments',
  standalone: true,
  imports: [CommonModule, RouterLink],
  templateUrl: './tournaments.html',
  styleUrls: ['./tournaments.scss']
})
export class Tournaments implements OnInit {
  tournaments: any[] = [];
  isLoading = true;
  errorMessage = '';

  constructor(private api: ApiService) {}

  ngOnInit(): void {
    this.loadTournaments();
  }

  loadTournaments(): void {
    this.isLoading = true;
    this.errorMessage = '';

    this.api.getTournaments().subscribe({
      next: (items: any[]) => {
        this.tournaments = Array.isArray(items) ? items : [];
        this.isLoading = false;
      },
      error: () => {
        this.tournaments = [];
        this.errorMessage = 'Не вдалося завантажити турніри';
        this.isLoading = false;
      }
    });
  }
}
