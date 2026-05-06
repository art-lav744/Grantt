import { Component } from '@angular/core';

@Component({
  selector: 'app-member-dashboard',
  templateUrl: './member-dashboard.component.html',
  styleUrls: ['./member-dashboard.component.scss']
})
export class MemberDashboardComponent {
  user: any; // Дані користувача з AuthState
  teamParticipations: any[] = [];
}