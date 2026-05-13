import { Component, Input } from '@angular/core';

@Component({
  selector: 'app-team-invite-email',
  templateUrl: './team-invite-email.component.html',
  styleUrls: ['./team-invite-email.component.css']
})
export class TeamInviteEmailComponent {
  @Input() inviterName: string = 'Адміністратор';
  @Input() teamName: string = 'Назва команди';
  @Input() acceptUrl: string = '#';
  
  // Посилання на логотип (повинно бути абсолютним для імейлів)
  logoUrl: string = 'assets/logo_grantt.png'; 
}