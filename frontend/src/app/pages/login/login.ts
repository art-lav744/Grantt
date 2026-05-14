import { Component } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormBuilder, FormGroup, ReactiveFormsModule, Validators } from '@angular/forms';
import { Router } from '@angular/router';
import { ApiService } from '../../services/api';

@Component({
  selector: 'app-login',
  standalone: true,
  imports: [CommonModule, ReactiveFormsModule],
  templateUrl: './login.html',
  styleUrls: ['./login.scss']
})
export class Login {
  loginForm: FormGroup;
  isPasswordVisible = false;
  errorMessage = '';

  constructor(
    private fb: FormBuilder,
    private api: ApiService,
    private router: Router
  ) {
    this.loginForm = this.fb.group({
      username: ['', [Validators.required]],
      password: ['', [Validators.required]]
    });
  }

  toggleVisibility(): void {
    this.isPasswordVisible = !this.isPasswordVisible;
  }

  onLogin(): void {
    this.onSubmit();
  }

  onSubmit(): void {
    if (this.loginForm.invalid) {
      this.loginForm.markAllAsTouched();
      return;
    }

    this.errorMessage = '';

    this.api.login({
      email: this.loginForm.value.username,
      password: this.loginForm.value.password
    }).subscribe({
      next: (res: any) => {
        const token = res?.access || res?.token || res?.access_token;

        if (token) {
          localStorage.setItem('access_token', token);
          localStorage.setItem('token', token);
        }

        if (res?.refresh) {
          localStorage.setItem('refresh_token', res.refresh);
        }

        if (res?.role) {
          localStorage.setItem('role', String(res.role));
        }

        if (res?.nickname) {
          localStorage.setItem('nickname', String(res.nickname));
          localStorage.setItem('username', String(res.nickname));
        }

        if (res?.email) {
          localStorage.setItem('email', String(res.email));
        }

        if (res?.user_id) {
          localStorage.setItem('user_id', String(res.user_id));
        }

        this.router.navigate(['/dashboard']);
      },
      error: (err: any) => {
        console.error('Login error:', err);
        this.errorMessage = this.extractError(err) || 'Невірний email або пароль';
      }
    });
  }

  goToRegister(): void {
    this.router.navigate(['/register']);
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
