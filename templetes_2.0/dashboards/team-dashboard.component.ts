import { Component, OnInit } from '@angular/core';
import { FormBuilder, FormGroup, Validators } from '@angular/forms';

@Component({
  selector: 'app-team-dashboard',
  templateUrl: './team-dashboard.component.html',
  styleUrls: ['./team-dashboard.component.scss']
})
export class TeamDashboardComponent implements OnInit {
  nickname: string = '';
  role: string = '';
  myTeams: any[] = [];
  selectedTeam: any = null;
  members: any[] = [];
  submissions: any[] = [];
  submissionForm: FormGroup;

  constructor(private fb: FormBuilder) {
    this.submissionForm = this.fb.group({
      github_link: ['', [Validators.required, Validators.pattern('https?://.*')]],
      video_link: [''],
      description: ['']
    });
  }

  ngOnInit(): void {}

  selectTeam(teamId: number) {
    // Логіка перемикання команди
  }

  submitSolution() {
    if (this.submissionForm.valid) {
      console.log('Sending data...', this.submissionForm.value);
    }
  }
}