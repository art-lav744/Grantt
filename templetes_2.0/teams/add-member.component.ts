import { Component, OnInit } from '@angular/core';
import { FormBuilder, FormGroup, Validators, ReactiveFormsModule } from '@angular/forms';
import { CommonModule, Location } from '@angular/common';
import { Router } from '@angular/router';

@Component({
  selector: 'app-add-member',
  standalone: true,
  imports: [CommonModule, ReactiveFormsModule],
  templateUrl: './add-member.component.html',
  styleUrls: ['./add-member.component.scss']
})
export class AddMemberComponent implements OnInit {
  addMemberForm: FormGroup;
  teamName: string = 'Завантаження...'; // Значення за замовчуванням

  constructor(
    private fb: FormBuilder,
    private router: Router,
    private location: Location
  ) {
    this.addMemberForm = this.fb.group({
      fullName: ['', [Validators.required, Validators.minLength(2)]],
      email: ['', [Validators.required, Validators.email]]
    });
  }

  ngOnInit(): void {
    // Тут зазвичай логіка отримання назви команди з сервісу або параметрів маршруту
    // Наприклад: this.teamName = "Grantt Developers";
  }

  onSubmit(): void {
    if (this.addMemberForm.valid) {
      const newMember = this.addMemberForm.value;
      console.log('Додавання учасника:', newMember);
      // Тут викликаємо сервіс для відправки даних на бекенд
    }
  }

  goBack(): void {
    // Повернення до попередньої сторінки або на дашборд
    this.router.navigate(['/team-dashboard']);
  }
}