import { Component, OnInit } from '@angular/core';
import { FormBuilder, FormGroup, Validators, ReactiveFormsModule } from '@angular/forms';
import { CommonModule } from '@angular/common';

// Інтерфейс для відповідності новому дизайну карток
export interface TournamentTeam {
  id: number;
  name: string;
  image?: string;
  captain?: {
    id: number;
  };
  tournament: {
    title: string;
  };
}

@Component({
  selector: 'app-team-dashboard',
  standalone: true, // Якщо ви використовуєте Standalone компоненти
  imports: [CommonModule, ReactiveFormsModule],
  templateUrl: './team-dashboard.component.html',
  styleUrls: ['./team-dashboard.component.scss']
})
export class TeamDashboardComponent implements OnInit {
  // Дані користувача
  nickname: string = 'Zaliska';
  role: string = 'Учасник';

  // Список команд (тепер з типізацією)
  myTeams: TournamentTeam[] = [];
  
  // Вибрана команда та пов'язані дані
  selectedTeam: TournamentTeam | null = null;
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

  ngOnInit(): void {
    // Тут зазвичай завантажуються дані з сервісу
    // Приклад заповнення для тестування дизайну:
    /*
    this.myTeams = [
      {
        id: 1,
        name: 'Cyber Tigers',
        tournament: { title: 'Autumn Code Cup 2024' },
        captain: { id: 1 } // Ви капітан
      }
    ];
    */
  }

  /**
   * Метод вибору команди (спрацьовує при кліку на картку)
   */
  selectTeam(teamId: number) {
    const team = this.myTeams.find(t => t.id === teamId);
    if (team) {
      this.selectedTeam = team;
      this.loadTeamDetails(teamId);
    }
  }

  /**
   * Завантаження учасників та історії рішень для конкретної команди
   */
  private loadTeamDetails(teamId: number) {
    console.log('Завантаження даних для команди:', teamId);
    // Логіка виклику сервісу:
    // this.teamService.getTeamMembers(teamId).subscribe(m => this.members = m);
    // this.teamService.getSubmissions(teamId).subscribe(s => this.submissions = s);
  }

  /**
   * Відправка форми рішення
   */
  submitSolution() {
    if (this.submissionForm.valid && this.selectedTeam) {
      const payload = {
        team_id: this.selectedTeam.id,
        ...this.submissionForm.value
      };
      console.log('Sending submission...', payload);
      
      // Після успішної відправки можна очистити форму
      // this.submissionForm.reset();
    }
  }
}