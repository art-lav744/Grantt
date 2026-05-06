import { Component, OnInit } from '@angular/core';
import { ActivatedRoute } from '@angular/router';

@Component({
  selector: 'app-tournament-detail',
  templateUrl: './tournament-detail.component.html',
  styleUrls: ['./tournament-detail.component.scss']
})
export class TournamentDetailComponent implements OnInit {
  tournament: any;
  teams: any[] = [];
  rounds: any[] = [];
  files: any[] = [];
  
  // Флаги доступу (зазвичай приходять з Auth-сервісу)
  canManageRounds: boolean = false;
  canAccessFiles: boolean = false;

  constructor(private route: ActivatedRoute) {}

  ngOnInit(): void {
    const id = this.route.snapshot.paramMap.get('id');
    // Тут завантаження даних через TournamentService
  }
}