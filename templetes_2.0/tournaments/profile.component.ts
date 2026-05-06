import { Component } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormBuilder, FormGroup, ReactiveFormsModule } from '@angular/forms';

@Component({
  selector: 'app-profile',
  standalone: true,
  imports: [CommonModule, ReactiveFormsModule],
  templateUrl: './profile.component.html',
  styleUrls: ['./profile.component.scss']
})
export class ProfileComponent {
  activeTab: 'teams' | 'submissions' | 'edit' = 'teams';
  user = { nickname: 'Zaliska', email: 'zaliska@edu.ua', role: 'jury', discord: 'zaliska#1234' };
  
  profileForm: FormGroup;

  constructor(private fb: FormBuilder) {
    this.profileForm = this.fb.group({
      nickname: [this.user.nickname],
      full_name: [''],
      discord_tag: [this.user.discord],
      profile_image: [null]
    });
  }

  switchTab(tab: 'teams' | 'submissions' | 'edit') {
    this.activeTab = tab;
  }

  onFileChange(event: any) {
    const file = event.target.files[0];
    this.profileForm.patchValue({ profile_image: file });
  }

  saveProfile() {
    console.log('Дані профілю:', this.profileForm.value);
  }
}