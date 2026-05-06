import { Component } from '@angular/core';
import { FormBuilder, FormGroup, Validators, ReactiveFormsModule } from '@angular/forms';
import { CommonModule } from '@angular/common';

@Component({
  selector: 'app-register',
  standalone: true,
  imports: [CommonModule, ReactiveFormsModule],
  templateUrl: './register.component.html',
  styleUrls: ['./register.component.scss']
})
export class RegisterComponent {
  registerForm: FormGroup;
  visiblePasswords: { [key: string]: boolean } = {
    password: false,
    confirmPassword: false
  };
  errorMessage = '';

  constructor(private fb: FormBuilder) {
    this.registerForm = this.fb.group({
      username: ['', Validators.required],
      email: ['', [Validators.required, Validators.email]],
      password: ['', [Validators.required, Validators.minLength(8)]],
      confirmPassword: ['', Validators.required]
    });
  }

  getLabel(name: string): string {
    const labels: { [key: string]: string } = {
      username: "Ім'я користувача",
      email: "Електронна пошта",
      password: "Пароль",
      confirmPassword: "Підтвердження пароля"
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
    if (this.registerForm.valid) {
      console.log('Дані реєстрації:', this.registerForm.value);
    }
  }
}