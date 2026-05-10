import { Component, OnInit } from '@angular/core';

interface AssignedTournament {
  id: number;
  title: string;
  status: string;
}

interface Evaluation {
  id: number;
  team_name: string;
  is_scored: boolean;
}

@Component({
  selector: 'app-jury-dashboard',
  templateUrl: './jury-dashboard.component.html',
  styleUrls: ['./jury-dashboard.component.scss']
})
export class JuryDashboardComponent implements OnInit {
  assignedTournaments: AssignedTournament[] = [];
  myEvaluations: Evaluation[] = [];
  totalCount: number = 0;
  doneCount: number = 0;
  isLoading: boolean = true;

  constructor() {}

  ngOnInit(): void {
    this.fetchJuryData();
  }

  fetchJuryData(): void {
    this.isLoading = true;
    
    // ТУТ МАЄ БУТИ ВИКЛИК ВАШОГО СЕРВІСУ:
    // this.juryService.getDashboardData().subscribe(data => {
    //    this.assignedTournaments = data.tournaments;
    //    this.myEvaluations = data.evaluations;
    //    this.totalCount = data.total;
    //    this.doneCount = data.done;
    //    this.isLoading = false;
    // });

    // Імітація завантаження (видалити після підключення сервісу)
    setTimeout(() => {
      this.isLoading = false;
    }, 1000);
  }
}