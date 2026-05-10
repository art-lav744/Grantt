import { Component, OnInit } from '@angular/core';
import { FormBuilder, FormGroup, Validators, ReactiveFormsModule } from '@angular/forms';
import { CommonModule } from '@angular/common';

@Component({
  selector: 'app-manage-access',
  standalone: true,
  imports: [CommonModule, ReactiveFormsModule],
  templateUrl: './manage-access.component.html',
  styleUrls: ['./manage-access.component.scss']
})
export class ManageAccessComponent implements OnInit {
  // Масиви тепер порожні, вони мають заповнюватися через API-сервіс
  users: any[] = [];
  juryUsers: any[] = [];
  submissions: any[] = [];
  assignments: any[] = [];

  assignForm: FormGroup;

  constructor(private fb: FormBuilder) {
    this.assignForm = this.fb.group({
      juryId: ['', Validators.required],
      submissionId: ['', Validators.required]
    });
  }

  ngOnInit(): void {
    // Тут має бути виклик сервісу, наприклад:
    // this.userService.getUsers().subscribe(data => { 
    //   this.users = data; 
    //   this.updateJuryList(); 
    // });
    this.updateJuryList();
  }

  updateJuryList() {
    if (this.users) {
      this.juryUsers = this.users.filter(u => u.role === 'jury' && u.isActive);
    }
  }

  toggleStatus(user: any) {
    // В реальному додатку тут буде виклик до API
    user.isActive = !user.isActive;
    this.updateJuryList();
  }

  changeRole(user: any) {
    // В реальному додатку тут буде виклик до API
    user.role = user.role === 'jury' ? 'participant' : 'jury';
    this.updateJuryList();
  }

  onAssign() {
    if (this.assignForm.valid) {
      // Логіка відправки призначення на бекенд
      const payload = this.assignForm.value;
      console.log('Відправка призначення на сервер:', payload);
      
      // Після успішної відповіді сервера можна оновити список assignments
      this.assignForm.reset();
    }
  }

  goToDashboard() {
    // Логіка навігації (Router)
  }
}