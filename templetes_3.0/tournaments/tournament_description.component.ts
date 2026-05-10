import { Component, OnInit } from '@angular/core';
import { ActivatedRoute } from '@angular/router';
import { HttpClient } from '@angular/common/http';

@Component({
  selector: 'app-tournament-detail',
  templateUrl: './tournament_description.component.html',
  styleUrls: ['./tournament_description.component.scss']
})
export class TournamentDetailComponent implements OnInit {
  tournament: any;
  isLoading: boolean = true;

  constructor(
    private route: ActivatedRoute,
    private http: HttpClient
  ) {}

  ngOnInit(): void {
    const id = this.route.snapshot.paramMap.get('id');
    if (id) {
      this.loadTournamentDetails(id);
    }
  }

  loadTournamentDetails(id: string): void {
    // Використовуємо існуючий API шлях з api_urls.py
    this.http.get(`api/tournaments/`).subscribe((data: any) => {
      // У вашому API зараз TournamentListCreateView повертає список. 
      // В ідеалі створити окремий DetailView, але поки знайдемо в списку:
      this.tournament = data.find((t: any) => t.id === +id);
      this.isLoading = false;
    });
  }
}