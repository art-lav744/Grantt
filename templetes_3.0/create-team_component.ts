import { Component } from '@angular/core';
import { FormBuilder, FormGroup, Validators, ReactiveFormsModule } from '@angular/forms';
import { CommonModule } from '@angular/common';

@Component({
  selector: 'app-create-team',
  standalone: true,
  imports: [CommonModule, ReactiveFormsModule],
  templateUrl: './create-team.component.html',
  styleUrls: ['./create-team.component.scss']
})
export class CreateTeamComponent {
  teamForm: FormGroup;
  
  // Дані турніру (можна отримувати через @Input або сервіс)
  tournament = {
    title: 'Spring Tournament 2026',
    imageUrl: '' // Сюди прийде лінк на фото від організатора
  };

  constructor(private fb: FormBuilder) {
    this.teamForm = this.fb.group({
      team_name: ['', [Validators.required, Validators.minLength(3)]]
    });
  }

  onSubmit() {
    if (this.teamForm.valid) {
      console.log('Дані форми:', this.teamForm.value);
      // Тут логіка відправки на сервер
    }
  }
}