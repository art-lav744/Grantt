import { Component, OnInit } from '@angular/core';

@Component({
  selector: 'app-tournament-list',
  templateUrl: './tournament-list.component.html',
  styleUrls: ['./tournament-list.component.scss']
})
export class TournamentListComponent implements OnInit {
  // Масив турнірів, який буде заповнюватися з API
  tournaments: any[] = [];
  isLoading: boolean = true;

  constructor() {}

  ngOnInit(): void {
    this.loadTournaments();
  }

  loadTournaments(): void {
    // Тут буде виклик сервісу, наприклад:
    // this.tournamentService.getTournaments().subscribe(data => {
    //   this.tournaments = data;
    //   this.isLoading = false;
    // });
    
    // Для демонстрації логіки завантаження:
    this.isLoading = false;
  }
}