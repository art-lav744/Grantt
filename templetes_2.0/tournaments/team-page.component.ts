import { Component, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';

@Component({
  selector: 'app-team-page',
  standalone: true,
  imports: [CommonModule],
  templateUrl: './team-page.component.html',
  styleUrls: ['./team-page.component.scss']
})
export class TeamPageComponent implements OnInit {
  isCaptain = true;
  team = {
    name: 'Cyber Hornets',
    tournament: { title: 'Junior IT Cup 2026' },
    organization: 'Lyceum #1',
    captain_name: 'Zaliska',
    captain_email: 'cap@gmail.com',
    max_members: 5,
    members: [
      { full_name: 'Zaliska', email: 'cap@gmail.com', isCaptain: true },
      { full_name: 'Іван Іванов', email: 'ivan@gmail.com', isCaptain: false }
    ]
  };

  submissions = [
    {
      roundTitle: 'Кваліфікація',
      createdAt: new Date(),
      evalCount: 1,
      totalAvg: 85,
      criteriaPreview: 'UI: 90, Logic: 80',
      githubLink: 'https://github.com/example',
      videoLink: 'https://youtube.com/example'
    }
  ];

  constructor() {}

  ngOnInit(): void {}

  goToSubmit() { /* Router logic */ }
  goToAddMember() { /* Router logic */ }
}