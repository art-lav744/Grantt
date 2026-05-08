import { Component } from '@angular/core';
import { FormBuilder, FormGroup, Validators, ReactiveFormsModule } from '@angular/forms';
import { CommonModule } from '@angular/common';
import { Router, RouterLink } from '@angular/router';
import { ApiService } from '../../services/api';

@Component({
  selector: 'app-login',
  standalone: true,
  imports: [CommonModule, ReactiveFormsModule, RouterLink],
  templateUrl: './login.html',
  styleUrls: ['./login.scss']
})
export class Login {
  loginForm: FormGroup;
  isPasswordVisible = false;
  errorMessage = '';
  loading = false;

  constructor(
    private fb: FormBuilder,
    private api: ApiService,
    private router: Router
  ) {
    this.loginForm = this.fb.group({
      email: ['', [Validators.required, Validators.email]],
      password: ['', Validators.required]
    });
  }

  toggleVisibility(): void {
    this.isPasswordVisible = !this.isPasswordVisible;
  }

  onLogin(): void {
    if (this.loginForm.invalid || this.loading) {
      return;
    }

    this.loading = true;
    this.errorMessage = '';

    this.api.login(this.loginForm.value).subscribe({
      next: (response: any) => {
        const token = response?.access_token || response?.token;

        if (!token) {
          this.errorMessage = 'Сервер не повернув токен авторизації.';
          this.loading = false;
          return;
        }

        localStorage.setItem('access_token', token);
        localStorage.setItem('token', token);

        if (response.role) localStorage.setItem('role', response.role);
        if (response.nickname) localStorage.setItem('nickname', response.nickname);
        if (response.user_id) localStorage.setItem('user_id', String(response.user_id));
        if (response.email) localStorage.setItem('email', response.email);

        this.router.navigate(['/dashboard']);
      },
      error: (error: any) => {
        this.errorMessage = error?.error?.non_field_errors?.[0]
          || error?.error?.detail
          || error?.error
          || 'Не вдалося увійти. Перевір email і пароль.';
        this.loading = false;
      }
    });
  }
}
