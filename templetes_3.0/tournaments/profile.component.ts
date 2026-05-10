import { Component, OnInit, OnDestroy } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormBuilder, FormGroup, ReactiveFormsModule, Validators } from '@angular/forms';
import { HttpClient, HttpClientModule } from '@angular/common/http';
import { Subject, takeUntil } from 'rxjs';

// Інтерфейс для чіткої типізації даних користувача
interface UserProfile {
  nickname: string;
  email: string;
  joinDate: string;
  country: string;
  discord: string;
  teamsCount: number;
  submissionsCount: number;
  avatarUrl?: string;
}

@Component({
  selector: 'app-profile',
  standalone: true,
  imports: [CommonModule, ReactiveFormsModule, HttpClientModule],
  templateUrl: './profile.component.html',
  styleUrls: ['./profile.component.scss']
})
export class ProfileComponent implements OnInit, OnDestroy {
  // Дані за замовчуванням (пусті), які заміняться даними з сервера
  user!: UserProfile;
  profileForm!: FormGroup;
  isLoading = true;
  
  private destroy$ = new Subject<void>();
  private readonly API_URL = 'https://api.your-platform.com/user/profile'; // Замініть на ваш реальний URL

  constructor(
    private fb: FormBuilder,
    private http: HttpClient
  ) {
    this.initForm();
  }

  ngOnInit(): void {
    this.loadUserData();
  }

  ngOnDestroy(): void {
    this.destroy$.next();
    this.destroy$.complete();
  }

  /**
   * Завантаження реальних даних з бекенду
   */
  private loadUserData(): void {
    this.isLoading = true;
    this.http.get<UserProfile>(this.API_URL)
      .pipe(takeUntil(this.destroy$))
      .subscribe({
        next: (data) => {
          this.user = data;
          this.patchFormValues(data);
          this.isLoading = false;
        },
        error: (err) => {
          console.error('Помилка завантаження профілю:', err);
          this.isLoading = false;
        }
      });
  }

  private initForm(): void {
    this.profileForm = this.fb.group({
      nickname: ['', [Validators.required]],
      country: ['', [Validators.required]],
      discord_tag: [''],
      profile_image: [null]
    });
  }

  private patchFormValues(data: UserProfile): void {
    this.profileForm.patchValue({
      nickname: data.nickname,
      country: data.country,
      discord_tag: data.discord
    });
  }

  /**
   * Обробка вибору файлу (SVG-іконка або олівець)
   */
  onFileChange(event: any): void {
    const file = event.target.files[0];
    if (file) {
      this.profileForm.patchValue({ profile_image: file });
      // Можна відразу відправляти файл на сервер, якщо це передбачено дизайном
      this.uploadAvatar(file);
    }
  }

  /**
   * Окремий метод для завантаження тільки аватара
   */
  private uploadAvatar(file: File): void {
    const formData = new FormData();
    formData.append('avatar', file);

    this.http.post(`${this.API_URL}/upload-avatar`, formData)
      .subscribe(res => console.log('Аватар оновлено'));
  }

  /**
   * Збереження основних даних профілю
   */
  saveProfile(): void {
    if (this.profileForm.valid) {
      const payload = {
        nickname: this.profileForm.value.nickname,
        country: this.profileForm.value.country,
        discord: this.profileForm.value.discord_tag
      };

      this.http.put(this.API_URL, payload)
        .pipe(takeUntil(this.destroy$))
        .subscribe({
          next: (updatedUser) => {
            this.user = { ...this.user, ...payload };
            alert('Дані успішно оновлено!');
          },
          error: (err) => alert('Помилка при збереженні')
        });
    }
  }

  logout(): void {
    // Виклик вашого AuthService для видалення токенів та редиректу
    this.http.post('/api/auth/logout', {}).subscribe(() => {
      window.location.href = '/login';
    });
  }

  // В інтерфейс UserProfile додаємо поле
  interface UserProfile {
    // ... інші поля
    submissionHistory: { [date: string]: number };
  }

  // У методі loadUserData дані автоматично потраплять у компонент
  private loadUserData(): void {
    this.http.get<UserProfile>(this.API_URL).subscribe(data => {
      this.user = data;
      this.generateHeatmap(data.submissionHistory);
    });
  }
}