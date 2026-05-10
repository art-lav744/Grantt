import { Component, OnInit, Input } from '@angular/core';
import { CommonModule } from '@angular/common';

interface TeamMember {
  full_name: string;
  email: string;
  isCaptain: boolean;
}

interface Submission {
  roundTitle: string;
  createdAt: Date;
  totalAvg: number;
  githubLink: string;
  videoLink?: string;
}

@Component({
  selector: 'app-team-page',
  standalone: true,
  imports: [CommonModule],
  templateUrl: './team-page.component.html',
  styleUrls: ['./team-page.component.scss']
})
export class TeamPageComponent implements OnInit {
  // Видалено заглушки. Ці дані мають приходити з сервісу або через @Input
  @Input() team: any = null; 
  @Input() submissions: Submission[] = [];
  @Input() isCaptain: boolean = false;

  constructor() {}

  ngOnInit(): void {
    // Тут має бути виклик сервісу, наприклад:
    // this.teamService.getTeamData().subscribe(data => this.team = data);
  }

  goToSubmit(): void {
    // Реальна логіка навігації
  }

  goToAddMember(): void {
    // Реальна логіка відкриття модалки
  }

  get isTeamFull(): boolean {
    return this.team?.members?.length >= (this.team?.max_members || 5);
  }
}