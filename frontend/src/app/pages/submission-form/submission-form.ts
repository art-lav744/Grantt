import { Component, OnDestroy, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormBuilder, ReactiveFormsModule, ValidationErrors, Validators } from '@angular/forms';
import { ActivatedRoute, Router } from '@angular/router';
import { ApiService } from '../../services/api';

@Component({
  selector: 'app-submission-form',
  standalone: true,
  imports: [CommonModule, ReactiveFormsModule],
  templateUrl: './submission-form.html',
  styleUrl: './submission-form.scss'
})
export class SubmissionForm implements OnInit, OnDestroy {
  roundId = 0;
  teamId = 0;
  activeTab: 'info' | 'submit' = 'info';
  isExpired = false;
  countdownText = 'Термін активний';
  success = '';
  error = '';
  private roundEnd: Date | null = null;
  private timerId: ReturnType<typeof setInterval> | null = null;

  tournament: any = null;

  submissionForm;

  constructor(
    private fb: FormBuilder,
    private route: ActivatedRoute,
    private router: Router,
    private api: ApiService
  ) {
    this.submissionForm = this.fb.group({
      github_link: ['', [Validators.required, this.githubValidator]],
      video_link: ['', [Validators.required, this.youtubeValidator]],
      description: ['']
    });
  }

  ngOnInit(): void {
    this.roundId = Number(this.route.snapshot.paramMap.get('roundId'));
    this.teamId = Number(this.route.snapshot.paramMap.get('teamId'));

    if (!this.roundId || !this.teamId) {
      this.error = 'Не вдалося визначити команду або раунд';
      return;
    }

    this.api.getTeam(this.teamId).subscribe({
      next: (team: any) => {
        const round = (team?.rounds || []).find((item: any) => Number(item.id) === this.roundId);
        this.tournament = this.normalizeRound(round, team);
        this.roundEnd = this.tournament?.end_time ? new Date(this.tournament.end_time) : null;
        this.updateCountdown();
        this.timerId = setInterval(() => this.updateCountdown(), 30000);
      },
      error: () => {
        this.error = 'Не вдалося завантажити завдання';
        this.tournament = {
          title: 'Відправка роботи',
          description: '',
          requirements: []
        };
      }
    });
  }

  ngOnDestroy(): void {
    if (this.timerId) {
      clearInterval(this.timerId);
    }
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
      description: value.description || 'Опис не надано'
    }).subscribe({
      next: () => {
        this.success = 'Роботу успішно відправлено';
        this.router.navigate(['/teams', this.teamId]);
      },
      error: (err: any) => this.error = this.extractError(err) || 'Не вдалося відправити роботу'
    });
  }

  private normalizeRound(round: any, team: any): any {
    const requirements = String(round?.requirements || '')
      .split(/\r?\n/)
      .map(item => item.trim())
      .filter(Boolean);

    return {
      ...round,
      title: round?.title || team?.tournament?.title || 'Завдання',
      description: round?.description || team?.tournament?.title || '',
      requirements,
      end_time: round?.end_time
    };
  }

  private updateCountdown(): void {
    if (!this.roundEnd || Number.isNaN(this.roundEnd.getTime())) {
      this.isExpired = false;
      this.countdownText = 'Термін активний';
      return;
    }

    const diffMs = this.roundEnd.getTime() - Date.now();
    if (diffMs <= 0) {
      this.isExpired = true;
      this.countdownText = 'Термін завершено';
      return;
    }

    const hours = Math.floor(diffMs / 3600000);
    const minutes = Math.floor((diffMs % 3600000) / 60000);
    this.isExpired = false;
    this.countdownText = `Залишилось ${hours} год ${minutes} хв`;
  }

  private extractError(err: any): string {
    const payload = err?.error;
    if (!payload) return '';
    if (typeof payload === 'string') return payload;
    if (payload.detail || payload.message) return String(payload.detail || payload.message);
    const firstValue = Object.values(payload)[0];
    return Array.isArray(firstValue) ? String(firstValue[0]) : String(firstValue || '');
  }
}
