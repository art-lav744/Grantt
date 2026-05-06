import { Component } from '@angular/core';
import { FormBuilder, FormGroup, Validators, ReactiveFormsModule } from '@angular/forms';
import { CommonModule } from '@angular/common';

@Component({
  selector: 'app-manage-access',
  standalone: true,
  imports: [CommonModule, ReactiveFormsModule],
  templateUrl: './manage-access.component.html',
  styleUrls: ['./manage-access.component.scss']
})
export class ManageAccessComponent {
  users = [
    { id: 1, nickname: 'Zaliska', email: 'test@mail.com', role: 'jury', isActive: true },
    { id: 2, nickname: 'Oleg', email: 'oleg@mail.com', role: 'participant', isActive: false }
  ];
  
  juryUsers = this.users.filter(u => u.role === 'jury');
  submissions = [{ id: 101, teamName: 'Alpha' }, { id: 102, teamName: 'Beta' }];
  assignments = [
    { submissionId: 101, juryName: 'Zaliska', teamName: 'Alpha', roundTitle: 'Кваліфікація' }
  ];

  assignForm: FormGroup;

  constructor(private fb: FormBuilder) {
    this.assignForm = this.fb.group({
      juryId: ['', Validators.required],
      submissionId: ['', Validators.required]
    });
  }

  toggleStatus(user: any) { user.isActive = !user.isActive; }
  changeRole(user: any) { user.role = user.role === 'jury' ? 'participant' : 'jury'; }
  onAssign() { if(this.assignForm.valid) console.log(this.assignForm.value); }
  goToDashboard() { /* Router logic */ }
}