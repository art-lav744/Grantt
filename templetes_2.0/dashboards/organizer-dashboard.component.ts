import { Component } from '@angular/core';
import { FormBuilder, FormGroup, Validators } from '@angular/forms';

@Component({
  selector: 'app-organizer-dashboard',
  templateUrl: './organizer-dashboard.component.html',
  styleUrls: ['./organizer-dashboard.component.scss']
})
export class OrganizerDashboardComponent {
  tournaments: any[] = [];
  totalUsers: number = 0;
  staffForm: FormGroup;

  constructor(private fb: FormBuilder) {
    this.staffForm = this.fb.group({
      email: ['', [Validators.required, Validators.email]],
      role: ['jury', Validators.required]
    });
  }

  onCreateStaff() {
    if (this.staffForm.valid) {
      // API call
    }
  }
}