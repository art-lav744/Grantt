import { Component, OnInit } from '@angular/core';

@Component({
  selector: 'app-tournament-list',
  templateUrl: './tournament-list.component.html',
  styleUrls: ['./tournament-list.component.scss']
})
export class TournamentListComponent implements OnInit {
  tournaments: any[] = [];

  constructor() {}

  ngOnInit(): void {
    // Завантаження списку турнірів
  }
}