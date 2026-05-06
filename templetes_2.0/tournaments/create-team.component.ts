import { Component, OnInit } from '@angular/core';
import { FormBuilder, FormGroup, Validators, ReactiveFormsModule } from '@angular/forms';
import { ActivatedRoute, Router } from '@angular/router';
import { CommonModule } from '@angular/common';

@Component({
  selector: 'app-create-team',
  standalone: true,
  imports: [CommonModule, ReactiveFormsModule],
  templateUrl: './create-team.component.html',
  styleUrls: ['./create-team.component.scss']
})
export class CreateTeamComponent implements OnInit {
  teamForm: FormGroup;
  tournamentId: string | null = null;
  tournamentTitle: string = 'Завантаження...'; // Назва турніру з контексту

  constructor(
    private fb: FormBuilder,
    private route: ActivatedRoute,
    private router: Router
  ) {
    this.teamForm = this.fb.group({
      teamName: ['', [Validators.required, Validators.minLength(3), Validators.maxLength(50)]]
    });
  }

  ngOnInit(): void {
    // Отримуємо ID турніру, на який реєструється команда
    this.tournamentId = this.route.snapshot.paramMap.get('tournamentId');
    
    // Тут має бути виклик сервісу для отримання назви турніру по ID
    this.tournamentTitle = "Spring Code Challenge 2026"; 
  }

  onCreateTeam(): void {
    if (this.teamForm.valid) {
      const payload = {
        name: this.teamForm.value.teamName,
        tournamentId: this.tournamentId
      };

      console.log('Створення команди:', payload);

      // Після створення редіректимо на дашборд або сторінку команди
      this.router.navigate(['/dashboard']);
    } else {
      // Маркуємо всі поля як "торкнуті", щоб показати помилки валідації
      this.teamForm.markAllAsTouched();
    }
  }
}