import { Component } from '@angular/core';
import { FormBuilder, FormGroup, Validators, ReactiveFormsModule } from '@angular/forms';
import { CommonModule } from '@angular/common';

@Component({
  selector: 'app-login',
  standalone: true,
  imports: [CommonModule, ReactiveFormsModule],
  templateUrl: './login.component.html',
  styleUrls: ['./login.component.scss']
})
export class LoginComponent {
  loginForm: FormGroup;
  isPasswordVisible = false;
  errorMessage = '';

  constructor(private fb: FormBuilder) {
    this.loginForm = this.fb.group({
      // Змінено на 'username', але зазвичай у таких формах це email або login
      username: ['', [Validators.required]], 
      password: ['', [Validators.required]]
    });
  }

  // Метод для перемикання видимості пароля (тепер керує зміною SVG в HTML)
  toggleVisibility(): void {
    this.isPasswordVisible = !this.isPasswordVisible;
  }

  onLogin(): void {
    if (this.loginForm.valid) {
      console.log('Спроба входу з даними:', this.loginForm.value);
      // Тут буде виклик сервісу для авторизації
    } else {
      // Позначаємо всі поля як touched, щоб показати помилки валідації, якщо вони є
      this.loginForm.markAllAsTouched();
    }
  }

  // Додатковий метод для переходу на реєстрацію (якщо не використовуєш routerLink)
  goToRegister(): void {
    console.log('Перехід на сторінку реєстрації');
  }
}