import { Component } from '@angular/core';
import { FormBuilder, FormGroup, Validators, ReactiveFormsModule } from '@angular/forms';
import { CommonModule } from '@angular/common';

@Component({
  selector: 'app-add-member',
  standalone: true,
  imports: [CommonModule, ReactiveFormsModule],
  templateUrl: './add-member.component.html',
  styleUrls: ['./add-member.component.scss']
})
export class AddMemberComponent {
  addMemberForm: FormGroup;

  constructor(private fb: FormBuilder) {
    this.addMemberForm = this.fb.group({
      fullName: ['', [Validators.required, Validators.minLength(2)]],
      email: ['', [Validators.required, Validators.email]]
    });
  }

  onSubmit(): void {
    if (this.addMemberForm.valid) {
      console.log('Дані для запрошення:', this.addMemberForm.value);
    }
  }

  goBack(): void {
    console.log('Закриття модалки');
  }
}