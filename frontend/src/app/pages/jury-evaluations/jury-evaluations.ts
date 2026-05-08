import { Component, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { RouterLink } from '@angular/router';
import { ApiService } from '../../services/api';

@Component({
  selector: 'app-jury-evaluations',
  standalone: true,
  imports: [CommonModule, RouterLink],
  templateUrl: './jury-evaluations.html',
  styleUrl: './jury-evaluations.scss'
})
export class JuryEvaluations implements OnInit {
  evaluations: any[] = [];
  loading = true;
  error = '';

  constructor(private api: ApiService) {}

  ngOnInit(): void {
    this.api.getMyEvaluations().subscribe({
      next: (items: any) => {
        this.evaluations = items;
        this.loading = false;
      },
      error: () => {
        this.error = 'Не вдалося завантажити роботи для оцінювання.';
        this.loading = false;
      }
    });
  }
}
