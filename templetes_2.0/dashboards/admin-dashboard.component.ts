import { Component, OnInit } from '@angular/core';

@Component({
  selector: 'app-admin-dashboard',
  templateUrl: './admin-dashboard.component.html',
  styleUrls: ['./admin-dashboard.component.scss']
})
export class AdminDashboardComponent implements OnInit {
  tournaments: any[] = [];
  totalUsers: number = 0;
  myEvaluations: any[] = [];

  ngOnInit(): void {
    // Завантаження даних
  }

  registerStaff(email: string, role: string) {
    // Логіка реєстрації персоналу
  }
}