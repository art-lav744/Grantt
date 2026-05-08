import { Component, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { RouterLink } from '@angular/router';

@Component({
  selector: 'app-tournaments',
  standalone: true,
  imports: [CommonModule,RouterLink],
  templateUrl: './tournaments.html',
  styleUrls: ['./tournaments.scss']
})
export class Tournaments implements OnInit {
  activeStatus: string = 'all';

  tournaments = [
    {
      id: 1,
      title: 'Spring Code Challenge',
      regStart: new Date('2026-03-01'),
      regEnd: new Date('2026-04-15'),
      status: 'registration'
    },
    {
      id: 2,
      title: 'AI Hackathon',
      regStart: new Date('2026-01-10'),
      regEnd: new Date('2026-02-01'),
      status: 'running'
    }
  ];

  filteredTournaments = [...this.tournaments];

  ngOnInit(): void {
    this.filter('all');
  }

  filter(status: string): void {
    this.activeStatus = status;

    if (status === 'all') {
      this.filteredTournaments = this.tournaments;
    } else {
      this.filteredTournaments = this.tournaments.filter(t => t.status === status);
    }
  }
}