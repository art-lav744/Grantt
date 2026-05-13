import { Component } from '@angular/core';
import { CommonModule } from '@angular/common';
import { RouterOutlet, RouterLink, RouterLinkActive, Router } from '@angular/router';

@Component({
  selector: 'app-auth-layout',
  standalone: true,
  imports: [CommonModule, RouterOutlet, RouterLink, RouterLinkActive],
  templateUrl: './auth-layout.component.html',
  styleUrls: ['./auth-layout.component.scss']
})
export class AuthLayoutComponent {
  isExpanded = false;
  
  // Static user data based on profile
  user = { 
    nickname: 'Zaliska', 
    profile_image: null 
  };
  
  messages: { text: string; type: string }[] = [];

  constructor(private router: Router) {}

  toggleSidebar(): void {
    this.isExpanded = !this.isExpanded;
  }

  logout(): void {
    // Clear auth state
    localStorage.removeItem('token');
    // Redirect to landing page
    this.router.navigate(['/']);
  }
}