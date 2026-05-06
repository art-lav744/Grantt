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
  user = { nickname: 'Zaliska' };
  teams = [
    { id: 1, name: 'CyberDragons', tournament: { title: 'Spring Cup' } }
  ];
  submissions = [
    { 
      team: { name: 'CyberDragons' }, 
      round: { title: 'Фінал' }, 
      github_link: 'https://github.com/test',
      created_at: new Date()
    }
  ];

  openTeam(id: number) {
    console.log('Перехід до команди:', id);
  }
}