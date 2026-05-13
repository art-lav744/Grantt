import { Component, OnInit } from '@angular/core';
import { FormBuilder, FormGroup, Validators } from '@angular/forms';

interface Tournament {
  id: number;
  title: string;
  status: string;
  teams_count: number;
}

@Component({
  selector: 'app-organizer-dashboard',
  templateUrl: './organizer-dashboard.component.html',
  styleUrls: ['./organizer-dashboard.component.scss']
})
export class OrganizerDashboardComponent implements OnInit {
  tournaments: Tournament[] = [];
  totalUsers: number = 0;
  isLoading: boolean = true;
  staffForm: FormGroup;

  constructor(private fb: FormBuilder) {
    this.staffForm = this.fb.group({
      email: ['', [Validators.required, Validators.email]],
      role: ['jury', Validators.required]
    });
  }

  ngOnInit(): void {
    this.fetchData();
  }

  fetchData(): void {
    this.isLoading = true;
    // Імітація завантаження даних
    setTimeout(() => {
      this.tournaments = [
        { id: 1, title: 'Summer Cup 2026', status: 'Active', teams_count: 12 },
        { id: 2, title: 'Winter Invitational', status: 'Upcoming', teams_count: 8 }
      ];
      this.totalUsers = 156;
      this.isLoading = false;
    }, 1000);
  }

  onCreateStaff(): void {
    if (this.staffForm.valid) {
      console.log('Створення персоналу:', this.staffForm.value);
      this.staffForm.reset({ role: 'jury' });
    }
  }
}