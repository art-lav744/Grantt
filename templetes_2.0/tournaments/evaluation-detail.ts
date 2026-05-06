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
  // Дані завантажуються через сервіс
  evaluation: any = {
    submission: {
      team: { name: 'Grantt Developers' },
      round: { title: 'Фінал' },
      description: 'Опис розробленого проекту...',
      github_link: 'https://github.com/example',
      video_link: 'https://youtube.com/example'
    }
  };
  criteriaScores = [
    { criterion_id: 1, criterion: { name: 'Дизайн', max_score: 20 }, score: 15 },
    { criterion_id: 2, criterion: { name: 'Технології', max_score: 50 }, score: 40 }
  ];
  criteriaDefinition = "Оцінюйте зручність інтерфейсу та чистоту коду.";

  constructor(private fb: FormBuilder) {}

  ngOnInit(): void {
    const group: any = {
      comment: [this.evaluation.comment || '']
    };
    this.criteriaScores.forEach(item => {
      group['criterion_' + item.criterion_id] = [
        item.score, 
        [Validators.required, Validators.min(0), Validators.max(item.criterion.max_score)]
      ];
    });
    this.evalForm = this.fb.group(group);
  }

  get totalScore(): number {
    let total = 0;
    this.criteriaScores.forEach(item => {
      total += Number(this.evalForm.get('criterion_' + item.criterion_id)?.value || 0);
    });
    return total;
  }

  get maxTotal(): number {
    return this.criteriaScores.reduce((acc, curr) => acc + curr.criterion.max_score, 0);
  }

  onSubmit() {
    if (this.evalForm.valid) {
      console.log('Оцінка збережена:', this.evalForm.value);
    }
  }
}