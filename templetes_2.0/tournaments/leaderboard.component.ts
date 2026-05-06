import { Component, Input } from '@angular/core';
import { CommonModule } from '@angular/common';

@Component({
  selector: 'app-leaderboard',
  standalone: true,
  imports: [CommonModule],
  templateUrl: './leaderboard.component.html',
  styleUrls: ['./leaderboard.component.scss']
})
export class LeaderboardComponent {
  tournament = { title: 'Grantt Tournament 2026' };
  isFinal = false;
  
  leaderboard = [
    {
      rank: 1,
      team_name: 'Cyber Hornets',
      average_score: 95,
      total_raw_score: 285,
      rounds_scored: 2,
      submissions_count: 3,
      evaluations_count: 6,
      criteria_summary: [
        { name: 'Код', average: 92, round_scores: [90, 94] },
        { name: 'UI', average: 98, round_scores: [96, 100] }
      ]
    }
    // ... інші команди
  ];
}