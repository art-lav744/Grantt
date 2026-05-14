import { Component } from '@angular/core';
import { CommonModule } from '@angular/common';
import { AbstractControl, FormBuilder, FormGroup, ReactiveFormsModule, ValidationErrors, Validators } from '@angular/forms';
import { Router } from '@angular/router';
import { ApiService } from '../../services/api';

@Component({
  selector: 'app-register',
  standalone: true,
  imports: [CommonModule, ReactiveFormsModule],
  templateUrl: './register.html',
  styleUrls: ['./register.scss']
})
export class Register {
  private readonly allowedEmailDomains = ['gmail.com', 'outlook.com', 'hotmail.com', 'live.com', 'yahoo.com', 'icloud.com', 'ukr.net'];
  registerForm: FormGroup;
  visiblePasswords: { [key: string]: boolean } = {
    password: false,
    confirmPassword: false
  };
  errorMessage = '';

  constructor(
    private fb: FormBuilder,
    private api: ApiService,
    private router: Router
  ) {
    this.registerForm = this.fb.group({
      username: ['', Validators.required],
      email: ['', [Validators.required, Validators.email, this.emailLikeDjangoValidator.bind(this)]],
      password: ['', [Validators.required, Validators.minLength(8)]],
      confirmPassword: ['', Validators.required],
      termsAccepted: [false, Validators.requiredTrue]
    }, { validators: this.passwordMatchValidator });
  }

  passwordMatchValidator(control: AbstractControl): ValidationErrors | null {
    const password = control.get('password');
    const confirmPassword = control.get('confirmPassword');

    if (password && confirmPassword && password.value !== confirmPassword.value) {
      return { mismatch: true };
    }

    return null;
  }

  emailLikeDjangoValidator(control: AbstractControl): ValidationErrors | null {
    const value = String(control.value || '').trim().toLowerCase();
    if (!value) return null;
    if (/[А-Яа-яЁёІіЇїЄєҐґ]/.test(value)) {
      return { cyrillicEmail: true };
    }

    const domain = value.split('@')[1] || '';
    if (domain && !this.allowedEmailDomains.includes(domain)) {
      return { unsupportedDomain: true };
    }

    return null;
  }

  getLabel(name: string): string {
    const labels: { [key: string]: string } = {
      username: 'Нікнейм',
      email: 'Email',
      password: 'Пароль',
      confirmPassword: 'Підтвердіть пароль'
    };
    return labels[name];
  }

  togglePass(field: string): void {
    this.visiblePasswords[field] = !this.visiblePasswords[field];
  }

  isPasswordVisible(field: string): boolean {
    return this.visiblePasswords[field];
  }

  onRegister(): void {
    if (this.registerForm.invalid) {
      this.registerForm.markAllAsTouched();
      return;
    }

    this.errorMessage = '';

    this.api.register({
      nickname: this.registerForm.value.username,
      email: this.registerForm.value.email,
      password: this.registerForm.value.password
    }).subscribe({
      next: () => this.router.navigate(['/login']),
      error: (err: any) => {
        console.error('Register error:', err);
        this.errorMessage = this.extractError(err) || 'Помилка реєстрації';
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
}
