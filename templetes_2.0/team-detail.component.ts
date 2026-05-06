import { Component } from '@angular/core';

@Component({
  selector: 'app-team-detail',
  templateUrl: './team-detail.component.html',
  styleUrls: ['./team-detail.component.scss']
})
export class TeamDetailComponent {
  team: any; 
  currentUser: any;
  members: any[] = [];
  submissions: any[] = [];
  newMemberEmail: string = '';

  addMember() {
    // Логіка виклику сервісу для додавання учасника
    console.log('Adding:', this.newMemberEmail);
  }
}