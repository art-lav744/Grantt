import { Component, OnInit } from '@angular/core';
import { FormBuilder, FormGroup, Validators, ReactiveFormsModule } from '@angular/forms';
import { CommonModule } from '@angular/common';

@Component({
  selector: 'app-round-form',
  standalone: true,
  imports: [CommonModule, ReactiveFormsModule],
  templateUrl: './round-form.component.html',
  styleUrls: ['./round-form.component.scss']
})
export class RoundFormComponent implements OnInit {
  roundForm: FormGroup;
  isEdit = false;
  tournament = { title: 'Tournament 2026' };

  constructor(private fb: FormBuilder) {
    this.roundForm = this.fb.group({
      title: ['', Validators.required],
      description: [''],
      deadline: ['', Validators.required]
    });
  }

  ngOnInit(): void {
    // Якщо edit, завантажуємо дані: this.roundForm.patchValue(...)
  }

  submit() {
    if (this.roundForm.valid) console.log(this.roundForm.value);
  }
}