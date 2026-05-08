import { Component, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { ActivatedRoute, RouterLink } from '@angular/router';
import { ApiService } from '../../services/api';

@Component({
  selector: 'app-team-detail',
  standalone: true,
  imports: [CommonModule, RouterLink],
  templateUrl: './team-detail.html',
  styleUrl: './team-detail.scss',
})
export class TeamDetail implements OnInit {
  team: any = null;
  error = '';
  loading = true;

  constructor(
    private route: ActivatedRoute,
    private api: ApiService
  ) {}

  ngOnInit(): void {
    const id = Number(this.route.snapshot.paramMap.get('id'));

    this.api.getTeam(id).subscribe({
      next: (team: any) => {
        this.team = team;
        this.loading = false;
      },
      error: () => {
        this.error = 'Не вдалося завантажити команду';
        this.loading = false;
      }
    });
  }
}
