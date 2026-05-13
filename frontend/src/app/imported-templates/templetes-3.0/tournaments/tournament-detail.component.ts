import { Component, OnInit } from '@angular/core';
import { ActivatedRoute } from '@angular/router';

@Component({
  selector: 'app-tournament-detail',
  templateUrl: './tournament-detail.component.html',
  styleUrls: ['./tournament-detail.component.scss']
})
export class TournamentDetailComponent implements OnInit {
  tournament: any = {
    title: 'Весняний Кубок',
    description: 'Масштабне змагання для молодіжних команд регіону.',
    reg_start: new Date('2026-05-10T09:00:00'),
    reg_end: new Date('2026-05-20T18:00:00'),
    status: 'АКТИВНИЙ',
    banner_url: null // Поле для збереження прев'ю банера
  };

  teams: any[] = [
    { id: 1, name: 'Cyber Dragons', captain_email: 'draco@mail.com', members_count: 5 },
    { id: 2, name: 'Alpha Squad', captain_email: 'alpha@corp.ua', members_count: 4 }
  ];

  rounds: any[] = [
    { id: 1, title: 'Кваліфікація #1', status: 'Завершено', start: '01.05', end: '05.05' }
  ];

  files: any[] = [
    { id: 101, title: 'Rules_Final.pdf', file_type: 'PDF' }
  ];

  canManageRounds: boolean = true;
  canAccessFiles: boolean = true;

  constructor(private route: ActivatedRoute) {}

  ngOnInit(): void {
    const id = this.route.snapshot.paramMap.get('id');
    // Тут буде виклик сервісу: this.tournamentService.getById(id)...
  }

  onBannerSelected(event: any): void {
    const file = event.target.files[0];
    if (file) {
      const reader = new FileReader();
      reader.onload = (e: any) => {
        this.tournament.banner_url = e.target.result;
      };
      reader.readAsDataURL(file);
      
      // Тут також можна викликати сервіс для завантаження файлу на сервер
      // this.tournamentService.uploadBanner(this.tournament.id, file).subscribe();
    }
  }
}