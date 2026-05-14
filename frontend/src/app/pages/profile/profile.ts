import { ChangeDetectorRef, Component, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormBuilder, FormGroup, ReactiveFormsModule, Validators } from '@angular/forms';
import { ApiService } from '../../services/api';

@Component({
  selector: 'app-profile',
  standalone: true,
  imports: [CommonModule, ReactiveFormsModule],
  templateUrl: './profile.html',
  styleUrl: './profile.scss'
})
export class Profile implements OnInit {
  form: FormGroup;
  loading = true;
  saving = false;
  message = '';
  error = '';

  constructor(private fb: FormBuilder, private api: ApiService, private cdr: ChangeDetectorRef) {
    this.form = this.fb.group({
      nickname: ['', Validators.required],
      full_name: [''],
      discord_tag: ['']
    });
  }

  ngOnInit(): void {
    this.api.getMe().subscribe({
      next: (user: any) => {
        this.form.patchValue({
          nickname: user?.nickname || '',
          full_name: user?.full_name || '',
          discord_tag: user?.discord_tag || ''
        });
        this.deferStoredUserUpdate(user);
        this.loading = false;
        this.cdr.detectChanges();
      },
      error: () => {
        this.error = 'Не вдалося завантажити профіль.';
        this.loading = false;
        this.cdr.detectChanges();
      }
    });
  }

  save(): void {
    if (this.form.invalid) {
      this.form.markAllAsTouched();
      return;
    }
    this.saving = true;
    this.error = '';
    this.message = '';
    this.api.updateMe(this.form.value).subscribe({
      next: (user: any) => {
        this.deferStoredUserUpdate(user);
        this.message = 'Профіль збережено.';
        this.saving = false;
        this.cdr.detectChanges();
      },
      error: (err: any) => {
        this.error = this.extractError(err) || 'Не вдалося зберегти профіль.';
        this.saving = false;
        this.cdr.detectChanges();
      }
    });
  }

  private extractError(err: any): string {
    const payload = err?.error;
    if (!payload) return '';
    if (typeof payload === 'string') return payload;
    if (payload.detail || payload.message) return String(payload.detail || payload.message);
    const firstValue = Object.values(payload)[0];
    return Array.isArray(firstValue) ? String(firstValue[0]) : String(firstValue || '');
  }

  private deferStoredUserUpdate(user: any): void {
    setTimeout(() => {
      localStorage.setItem('nickname', user?.nickname || '');
      localStorage.setItem('email', user?.email || '');
      localStorage.setItem('role', user?.role || '');
      localStorage.setItem('profile_image', user?.profile_image_path || '');
    });
  }
}
