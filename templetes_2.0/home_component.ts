import { Component, OnInit } from '@angular/core';

@Component({
  selector: 'app-home',
  templateUrl: './home_component.html',
  styleUrls: ['./home_component.scss']
})
export class HomeComponent implements OnInit {
  regOpenTournaments: any[] = []; // Дані завантажуються з сервісу
  runningTournaments: any[] = [];

  constructor() {}

  ngOnInit(): void {
    // Тут буде виклик API через сервіс
  }
}