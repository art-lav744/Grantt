import { Component, OnInit } from '@angular/core';
import { FormBuilder, FormGroup, Validators, ReactiveFormsModule } from '@angular/forms';
import { CommonModule } from '@angular/common';

@Component({
  selector: 'app-evaluation-detail',
  standalone: true,
  imports: [CommonModule, ReactiveFormsModule],
  templateUrl: './evaluation-detail.component.html',
  styleUrls: ['./evaluation-detail.component.scss']
})
export class EvaluationDetailComponent implements OnInit {
  evalForm!: FormGroup;
  
  // Імітація даних з сервісу (можна замінити на реальний API call)
  evaluation: any = {
    submission: {
      team: { name: 'Grantt Developers' },
      round: { title: 'Фінал' },
      description: 'Проєкт з розробки інноваційної платформи для збору фідбеку в реальному часі.',
      github_link: 'https://github.com/example/project',
      video_link: 'https://youtube.com/watch?v=example'
    },
    comment: ''
  };

  // Критерії оцінювання
  criteriaScores = [
    { criterion_id: 1, criterion: { name: 'Дизайн та UX', max_score: 20 }, score: 15 },
    { criterion_id: 2, criterion: { name: 'Технічна складність', max_score: 50 }, score: 40 },
    { criterion_id: 3, criterion: { name: 'Якість презентації', max_score: 30 }, score: 25 }
  ];

  criteriaDefinition = "Оцінюйте візуальну привабливість, стабільність роботи коду та вміння команди презентувати свій продукт.";

  constructor(private fb: FormBuilder) {}

  ngOnInit(): void {
    this.initForm();
  }

  /**
   * Ініціалізація форми з динамічними контролами для кожного критерію
   */
  private initForm(): void {
    const group: any = {
      comment: [this.evaluation.comment || '']
    };

    this.criteriaScores.forEach(item => {
      // Створюємо окремий контрол для кожного критерію
      // Angular автоматично синхронізує range та number через один formControlName
      group['criterion_' + item.criterion_id] = [
        item.score, 
        [
          Validators.required, 
          Validators.min(0), 
          Validators.max(item.criterion.max_score)
        ]
      ];
    });

    this.evalForm = this.fb.group(group);
  }

  /**
   * Геттер для підрахунку поточної суми балів
   */
  get totalScore(): number {
    if (!this.evalForm) return 0;
    
    return this.criteriaScores.reduce((acc, item) => {
      const value = this.evalForm.get('criterion_' + item.criterion_id)?.value;
      return acc + (Number(value) || 0);
    }, 0);
  }

  /**
   * Геттер для отримання максимально можливої суми
   */
  get maxTotal(): number {
    return this.criteriaScores.reduce((acc, curr) => acc + curr.criterion.max_score, 0);
  }

  /**
   * Обробка відправки форми
   */
  onSubmit(): void {
    if (this.evalForm.valid) {
      const results = {
        ...this.evalForm.value,
        total: this.totalScore,
        submittedAt: new Date().toISOString()
      };
      
      console.log('Дані оцінювання успішно сформовано:', results);
      // Тут зазвичай іде виклик сервісу: this.evalService.save(results)...
      alert('Оцінку збережено!');
    } else {
      this.markFormGroupTouched(this.evalForm);
    }
  }

  /**
   * Допоміжний метод для підсвітки помилок, якщо форма невалідна
   */
  private markFormGroupTouched(formGroup: FormGroup) {
    Object.values(formGroup.controls).forEach(control => {
      control.markAsTouched();
    });
  }

  // Логіка залишається без змін, як ви просили.
  // Тільки переконайтеся, що в ngOnInit контрол створюється коректно:
  this.criteriaScores.forEach(item => {
    group['criterion_' + item.criterion_id] = [
      item.score, 
      [Validators.required, Validators.min(0), Validators.max(item.criterion.max_score)]
    ];
  })
}
