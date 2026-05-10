import { Component, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { RouterModule, Router } from '@angular/router';

// Описуємо структуру команди для типізації (це допоможе уникати помилок в шаблоні)
export interface TournamentTeam {
  id: number;
  name: string;
  image?: string;
  is_captain: boolean;
  status: 'in-progress' | 'completed';
  tournament: {
    title: string;
  };
}

@Component({
  selector: 'app-dashboard',
  standalone: true,
  imports: [CommonModule, RouterModule],
  templateUrl: './dashboard_component.html',
  styleUrls: ['./dashboard_component.scss']
})
export class DashboardComponent implements OnInit {
  // Використовуємо твій нікнейм
  user = { nickname: 'Zaliska' };

  // Порожній масив чекає на дані з твого сервісу/API
  teams: TournamentTeam[] = [];

  constructor(private router: Router) {}

  ngOnInit(): void {
    /** * ТУТ ПІДКЛЮЧАЙ СЕРВІС:
     * this.teamService.getMyTeams().subscribe(data => {
     * this.teams = data;
     * });
     */
  }

  // Метод для переходу до конкретної команди
  openTeam(id: number): void {
    this.router.navigate(['/dashboard/tournaments', id]);
  }
}