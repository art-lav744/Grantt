import { Component, OnInit, OnDestroy } from '@angular/core';
import { FormBuilder, FormGroup, Validators, AbstractControl, ValidationErrors } from '@angular/forms';
import { interval, Subscription } from 'rxjs';

// Інтерфейс для даних від адміна
interface TournamentData {
  title: string;
  description: string;
  requirements: string[];
  deadline: string; // ISO формат: "2024-12-31T23:59:59"
}

@Component({
  selector: 'app-submission-form',
  templateUrl: './submission-form.component.html',
  styleUrls: ['./submission-form.component.scss']
})
export class SubmissionFormComponent implements OnInit, OnDestroy {
  submissionForm: FormGroup;
  activeTab: 'info' | 'submit' = 'info';
  countdownText: string = '--:--:--';
  isExpired: boolean = false;
  
  // Дані, які прийдуть від адміна (зараз порожні)
  tournament?: TournamentData;
  private timerSubscription?: Subscription;

  constructor(private fb: FormBuilder) {
    this.submissionForm = this.fb.group({
      github_link: ['', [Validators.required, this.urlValidator, this.githubValidator]],
      video_link: ['', [Validators.required, this.urlValidator, this.youtubeValidator]],
      description: ['']
    });
  }

  ngOnInit() {
    // Тут ви будете викликати сервіс: this.service.getTournament().subscribe(data => { ... })
    // Для прикладу імітуємо отримання даних:
    this.loadAdminData({
      title: "Назва турніру від адміна",
      description: "Повний опис завдання, який ввів адміністратор...",
      requirements: ["Вимога 1", "Вимога 2"],
      deadline: new Date(Date.now() + 172800000).toISOString() // +2 дні
    });
  }

  loadAdminData(data: TournamentData) {
    this.tournament = data;
    this.startTimer(new Date(data.deadline));
  }

  private startTimer(deadlineDate: Date) {
    this.timerSubscription?.unsubscribe();
    this.timerSubscription = interval(1000).subscribe(() => {
      const now = new Date().getTime();
      const diff = deadlineDate.getTime() - now;

      if (diff <= 0) {
        this.countdownText = 'ЧАС ВИЙШОВ';
        this.isExpired = true;
        this.submissionForm.disable();
        return;
      }

      const h = Math.floor(diff / 3600000);
      const m = Math.floor((diff % 3600000) / 60000);
      const s = Math.floor((diff % 60000) / 1000);
      this.countdownText = `${h}h ${m}m ${s}s`;
    });
  }

  // Валідатори залишаються суворими для безпеки даних
  private urlValidator(control: AbstractControl): ValidationErrors | null {
    const urlPattern = /^(https?:\/\/)?([\w\d\-_]+\.+[A-Za-z]{2,}).*$/;
    return control.value && !urlPattern.test(control.value) ? { invalidUrl: true } : null;
  }

  private githubValidator(control: AbstractControl): ValidationErrors | null {
    return control.value && !control.value.includes('github.com') ? { notGithub: true } : null;
  }

  private youtubeValidator(control: AbstractControl): ValidationErrors | null {
    return control.value && !(/youtube\.com|youtu\.be/.test(control.value)) ? { notYoutube: true } : null;
  }

  onSubmit() {
    if (this.submissionForm.valid && !this.isExpired) {
      console.log('Відправка на сервер:', this.submissionForm.value);
    }
  }

  ngOnDestroy() { this.timerSubscription?.unsubscribe(); }
}