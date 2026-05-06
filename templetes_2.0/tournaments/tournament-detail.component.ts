import { Component } from '@angular/core';
import { CommonModule } from '@angular/common';

@Component({
  selector: 'app-tournament-detail',
  standalone: true,
  imports: [CommonModule],
  templateUrl: './tournament-detail.component.html',
  styleUrls: ['./tournament-detail.component.scss']
})
export class TournamentDetailComponent {
  canManage = true; // Роль адміністратора/організатора
  tournament = {
    id: 1,
    title: 'Spring Code Challenge',
    description: 'Змагання з алгоритмічного програмування для студентів.',
    regStart: '01.03.2026',
    regEnd: '15.04.2026',
    status: 'Реєстрація відкрита'
  };

  teams = [{ name: 'Hornets', captain: 'cap@gmail.com', count: 3 }];
  rounds = [{ title: 'Перший етап', status: 'Активний', start: '01.05', end: '05.05' }];
  files = [{ title: 'Правила.pdf', type: 'Регламент' }];
}