import { Component } from '@angular/core';

@Component({
  selector: 'app-base',
  templateUrl: './base_component.html',
  styleUrls: ['./base_component.scss']
})
export class BaseComponent {
  title = 'Tournament 2026';
  isLoggedIn = true; // Зазвичай керується через AuthService
  user = {
    nickname: 'Zaliska',
    profile_image: null
  };
  messages: {text: string, type: string}[] = [];

  logout() {
    console.log('User logged out');
    this.isLoggedIn = false;
  }
}