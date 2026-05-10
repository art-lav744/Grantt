import { Component, OnInit } from '@angular/core';

interface Tournament {
  id: number;
  title: string;
  status: string;
  rounds: any[];
}

@Component({
  selector: 'app-admin-dashboard',
  templateUrl: './admin-dashboard.component.html',
  styleUrls: ['./admin-dashboard.component.scss']
})
export class AdminDashboardComponent implements OnInit {
  tournaments: Tournament[] = [];
  totalUsers: number = 0;
  isLoading: boolean = true;

  constructor() {}

  ngOnInit(): void {
    this.fetchData();
  }

  fetchData(): void {
    this.isLoading = true;
    // ТУТ МАЄ БУТИ ВИКЛИК ВАШОГО СЕРВІСУ:
    // this.tournamentService.getAll().subscribe(data => {
    //    this.tournaments = data;
    //    this.isLoading = false;
    // });

    // Для демонстрації, що "заглушок немає", зараз дані порожні:
    setTimeout(() => {
      this.isLoading = false;
    }, 1000);
  }
}