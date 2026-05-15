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
  readonly passwordCriteria = [
    { key: 'minLength', label: 'Мінімум 8 символів' },
    { key: 'lowercase', label: 'Мала літера' },
    { key: 'uppercase', label: 'Велика літера' },
    { key: 'number', label: 'Цифра' },
    { key: 'special', label: 'Спецсимвол (!@#$%^&*)' }
  ];
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
      password: ['', [Validators.required, this.passwordCriteriaValidator.bind(this)]],
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

  passwordCriteriaValidator(control: AbstractControl): ValidationErrors | null {
    const password = String(control.value || '');
    const isValid = this.passwordCriteria.every((criterion) => this.testPasswordCriterion(criterion.key, password));

    return isValid ? null : { passwordCriteria: true };
  }

  isPasswordCriterionMet(key: string): boolean {
    const password = String(this.registerForm?.get('password')?.value || '');
    return this.testPasswordCriterion(key, password);
  }

  private testPasswordCriterion(key: string, password: string): boolean {
    switch (key) {
      case 'minLength':
        return password.length >= 8;
      case 'lowercase':
        return /[a-z]/.test(password);
      case 'uppercase':
        return /[A-Z]/.test(password);
      case 'number':
        return /\d/.test(password);
      case 'special':
        return /[!@#$%^&*(),.?":{}|<>]/.test(password);
      default:
        return false;
    }
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

  isPasswordField(field: string): boolean {
    return field.toLowerCase().includes('password');
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
