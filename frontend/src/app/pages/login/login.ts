import { Component } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormBuilder, FormGroup, ReactiveFormsModule, Validators } from '@angular/forms';
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

    const payload = {
      username: this.loginForm.value.username,
      password: this.loginForm.value.password
    };

    this.errorMessage = '';

    this.api.login(payload).subscribe({
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

        if (res?.username) {
          localStorage.setItem('username', String(res.username));
        }

        this.router.navigate(['/dashboard']);
      },
      error: (err: any) => {
        console.error('Login error:', err);
        this.errorMessage = err?.error?.detail || err?.error?.message || 'Невірний логін або пароль';
      }
    });
  }

  goToRegister(): void {
    this.router.navigate(['/register']);
  }
}
