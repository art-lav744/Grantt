import { Component } from '@angular/core';
import { Router, RouterLink, RouterLinkActive, RouterOutlet } from '@angular/router';
import { CommonModule } from '@angular/common';

@Component({
  selector: 'app-root',
  standalone: true,
  imports: [CommonModule, RouterOutlet, RouterLink, RouterLinkActive],
  templateUrl: './app.html',
  styleUrl: './app.scss',
})
export class App {
  constructor(private router: Router) {}

  get isLoggedIn(): boolean {
    return !!(localStorage.getItem('access_token') || localStorage.getItem('token') || localStorage.getItem('access'));
  }

  get role(): string {
    return (localStorage.getItem('role') || '').toLowerCase();
  }

  get isAdminOrOrganizer(): boolean {
    return this.role === 'admin' || this.role === 'organizer';
  }

  get isJuryOrOrganizer(): boolean {
    return this.role === 'jury' || this.role === 'organizer';
  }

  logout(): void {
    localStorage.removeItem('access_token');
    localStorage.removeItem('token');
    localStorage.removeItem('access');
    localStorage.removeItem('refresh_token');
    localStorage.removeItem('refresh');
    localStorage.removeItem('role');
    localStorage.removeItem('nickname');
    localStorage.removeItem('user_id');
    localStorage.removeItem('email');
    this.router.navigate(['/login']);
  }
}
