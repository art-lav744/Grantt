import { Component } from '@angular/core';
import { FormGroup, FormControl, Validators } from '@angular/forms';

@Component({
  selector: 'app-submission-form',
  templateUrl: './submission-form_component.html',
  styleUrls: ['./submission-form_component.scss']
})
export class SubmissionFormComponent {
  teamName: string = "Назва команди"; // Отримуємо через Input або сервіс
  submissionForm = new FormGroup({
    github_link: new FormControl('', [Validators.required]),
    video_link: new FormControl(''),
    description: new FormControl('')
  });

  onSubmit() {
    if (this.submissionForm.valid) {
      console.log(this.submissionForm.value);
    }
  }
}