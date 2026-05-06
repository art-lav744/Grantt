import { Component } from '@angular/core';
import { CommonModule } from '@angular/common';

@Component({
  selector: 'app-dashboard',
  standalone: true,
  imports: [CommonModule],
  templateUrl: './dashboard.component.html',
  styleUrls: ['./dashboard.component.scss']
})
export class DashboardComponent {
  userNickname = 'Zaliska'; // Буде завантажуватись з сервісу
  managedTeam = { name: 'Grantt Team', members: [{ nickname: 'User1' }, { nickname: 'User2' }] };
  joinedTeam = null;
  availableTournaments = [
    { id: 1, title: 'Summer IT Cup', reg_end: new Date('2026-06-01') }
  ];
}