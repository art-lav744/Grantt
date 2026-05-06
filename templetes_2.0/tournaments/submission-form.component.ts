import { Component, OnInit } from '@angular/core';
import { FormBuilder, FormGroup, Validators, ReactiveFormsModule } from '@angular/forms';
import { CommonModule } from '@angular/common';

@Component({
  selector: 'app-submission-form',
  standalone: true,
  imports: [CommonModule, ReactiveFormsModule],
  templateUrl: './submission-form.component.html',
  styleUrls: ['./submission-form.component.scss']
})
export class SubmissionFormComponent implements OnInit {
  submissionForm: FormGroup;
  teamName: string = 'Завантаження...';

  constructor(private fb: FormBuilder) {
    this.submissionForm = this.fb.group({
      githubLink: ['', [Validators.required, Validators.pattern('https?://github.com/.*')]],
      videoLink: ['', [Validators.pattern('https?://.*')]],
      description: ['', [Validators.required, Validators.minLength(20)]]
    });
  }

  ngOnInit(): void {
    // Отримання назви команди з сервісу
    this.teamName = "Grantt Developers";
  }

  onSubmit() {
    if (this.submissionForm.valid) {
      console.log('Дані подачі:', this.submissionForm.value);
    }
  }
}