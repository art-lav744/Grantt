import { Component } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { ActivatedRoute, RouterLink } from '@angular/router';
import { ApiService } from '../../services/api';

@Component({
  selector: 'app-submission-form',
  standalone: true,
  imports: [CommonModule, FormsModule, RouterLink],
  templateUrl: './submission-form.html',
  styleUrl: './submission-form.scss'
})
export class SubmissionForm {
  roundId = 0;
  teamId = 0;

  form = {
    github_link: '',
    description: ''
  };

  success = '';
  error = '';

  constructor(
    private route: ActivatedRoute,
    private api: ApiService
  ) {
    this.roundId = Number(this.route.snapshot.paramMap.get('roundId'));
    this.teamId = Number(this.route.snapshot.paramMap.get('teamId'));
  }

  submit() {
    this.success = '';
    this.error = '';

    this.api.createSubmission({
      round: this.roundId,
      team: this.teamId,
      github_link: this.form.github_link,
      description: this.form.description
    }).subscribe({
      next: () => {
        this.success = 'Роботу успішно відправлено';
      },
      error: () => {
        this.error = 'Не вдалося відправити роботу';
      }
    });
  }
}
