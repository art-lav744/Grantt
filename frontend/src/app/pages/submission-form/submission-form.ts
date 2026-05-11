import { Component } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormBuilder, ReactiveFormsModule, ValidationErrors, Validators } from '@angular/forms';
import { ActivatedRoute } from '@angular/router';
import { ApiService } from '../../services/api';

@Component({
  selector: 'app-submission-form',
  standalone: true,
  imports: [CommonModule, ReactiveFormsModule],
  templateUrl: './submission-form.html',
  styleUrl: './submission-form.scss'
})
export class SubmissionForm {
  roundId = 0;
  teamId = 0;
  activeTab: 'info' | 'submit' = 'info';
  isExpired = false;
  countdownText = 'Термін активний';
  success = '';
  error = '';

  tournament: any = {
    title: 'Відправка роботи',
    description: 'Завантажте посилання на виконане завдання.',
    requirements: []
  };

  submissionForm;

  constructor(
    private fb: FormBuilder,
    private route: ActivatedRoute,
    private api: ApiService
  ) {
    this.submissionForm = this.fb.group({
      github_link: ['', [Validators.required, this.githubValidator]],
      video_link: ['', this.youtubeValidator],
      description: ['']
    });
    this.roundId = Number(this.route.snapshot.paramMap.get('roundId'));
    this.teamId = Number(this.route.snapshot.paramMap.get('teamId'));
  }

  private githubValidator(control: any): ValidationErrors | null {
    const value = String(control.value || '').trim();
    return value && !/^https?:\/\/(www\.)?github\.com\/.+/.test(value) ? { notGithub: true } : null;
  }

  private youtubeValidator(control: any): ValidationErrors | null {
    const value = String(control.value || '').trim();
    return value && !/^https?:\/\/(www\.)?(youtube\.com|youtu\.be)\/.+/.test(value) ? { notYoutube: true } : null;
  }

  onSubmit(): void {
    if (this.submissionForm.invalid) {
      this.submissionForm.markAllAsTouched();
      return;
    }

    this.success = '';
    this.error = '';

    const value = this.submissionForm.value;
    this.api.createSubmission({
      round: this.roundId,
      team: this.teamId,
      github_link: value.github_link,
      video_link: value.video_link,
      description: value.description
    }).subscribe({
      next: () => this.success = 'Роботу успішно відправлено',
      error: () => this.error = 'Не вдалося відправити роботу'
    });
  }
}
