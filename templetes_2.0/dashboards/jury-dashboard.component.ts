import { Component, OnInit } from '@angular/core';

@Component({
  selector: 'app-jury-dashboard',
  templateUrl: './jury-dashboard.component.html',
  styleUrls: ['./jury-dashboard.component.scss']
})
export class JuryDashboardComponent implements OnInit {
  userNickname: string = '';
  totalCount: number = 0;
  doneCount: number = 0;
  assignedTournaments: any[] = [];
  myEvaluations: any[] = [];

  constructor() {}

  ngOnInit(): void {
    // Завантаження через JuryService
  }
}