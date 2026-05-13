import { Component, Input, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';

@Component({
  selector: 'app-leaderboard',
  standalone: true,
  imports: [CommonModule],
  templateUrl: './leaderboard.component.html',
  styleUrls: ['./leaderboard.component.scss']
})
export class LeaderboardComponent {
  // Дані тепер надходять ззовні (наприклад, через API-сервіс у батьківському компоненті)
  @Input() tournament: any = { title: '' };
  @Input() leaderboard: any[] = [];
  @Input() isFinal: boolean = false;
}