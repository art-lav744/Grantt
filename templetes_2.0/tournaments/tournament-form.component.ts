import { Component } from '@angular/core';
import { FormBuilder, FormGroup, Validators, ReactiveFormsModule } from '@angular/forms';
import { CommonModule } from '@angular/common';

@Component({
  selector: 'app-tournament-form',
  standalone: true,
  imports: [CommonModule, ReactiveFormsModule],
  templateUrl: './tournament-form.component.html',
  styleUrls: ['./tournament-form.component.scss']
})
export class TournamentFormComponent {
  tournamentForm: FormGroup;
  fileForm: FormGroup;
  isEdit = false;

  files = [
    { title: 'Завдання.zip', type: 'Архів', uploadedBy: 'Zaliska', date: '01.05.2026' }
  ];

  constructor(private fb: FormBuilder) {
    this.tournamentForm = this.fb.group({
      title: ['', Validators.required],
      description: [''],
      reg_start: ['', Validators.required],
      reg_end: ['', Validators.required]
    });

    this.fileForm = this.fb.group({
      fileTitle: ['', Validators.required],
      file: [null, Validators.required]
    });
  }

  saveTournament() { console.log(this.tournamentForm.value); }
  uploadFile() { console.log(this.fileForm.value); }
}