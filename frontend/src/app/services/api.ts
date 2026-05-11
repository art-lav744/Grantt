import { Injectable } from '@angular/core';
import { HttpClient, HttpHeaders } from '@angular/common/http';

@Injectable({
  providedIn: 'root'
})
export class ApiService {
  private apiUrl = 'http://127.0.0.1:8000/api';

  constructor(private http: HttpClient) {}

  private authHeaders() {
    const token = localStorage.getItem('access_token') || localStorage.getItem('token') || localStorage.getItem('access');
    if (!token) {
      return {};
    }
    return {
      headers: new HttpHeaders({
        Authorization: `Bearer ${token}`
      })
    };
  }

  getTournaments() {
    return this.http.get<any[]>(`${this.apiUrl}/tournaments/`);
  }

  getTournament(id: number) {
    return this.http.get<any>(`${this.apiUrl}/tournaments/${id}/`);
  }

  updateTournament(id: number, data: any) {
    return this.http.patch<any>(`${this.apiUrl}/tournaments/${id}/`, data, this.authHeaders());
  }

  login(data: any) {
    return this.http.post(`${this.apiUrl}/auth/login/`, data);
  }

  register(data: any) {
    return this.http.post(`${this.apiUrl}/auth/register/`, data);
  }

  getTournamentTeams(id: number) {
    return this.http.get<any[]>(`${this.apiUrl}/tournaments/${id}/teams/`);
  }

  getTournamentRounds(tournamentId: number) {
    return this.http.get<any[]>(`${this.apiUrl}/rounds/?tournament_id=${tournamentId}`);
  }

  getRound(roundId: number) {
    return this.http.get<any>(`${this.apiUrl}/rounds/${roundId}/`, this.authHeaders());
  }

  createRound(data: any) {
    return this.http.post<any>(`${this.apiUrl}/rounds/`, data, this.authHeaders());
  }

  updateRound(roundId: number, data: any) {
    return this.http.patch<any>(`${this.apiUrl}/rounds/${roundId}/`, data, this.authHeaders());
  }

  getTeam(teamId: number) {
    return this.http.get<any>(`${this.apiUrl}/teams/${teamId}/`);
  }

  createTeam(data: any) {
    return this.http.post<any>(`${this.apiUrl}/teams/`, data, this.authHeaders());
  }

  getMyTeams() {
    return this.http.get<any[]>(`${this.apiUrl}/users/me/teams/`, this.authHeaders());
  }

  createSubmission(data: any) {
    return this.http.post<any>(`${this.apiUrl}/submissions/`, data, this.authHeaders());
  }

  getMyEvaluations() {
    return this.http.get<any[]>(`${this.apiUrl}/users/me/evaluations/`, this.authHeaders());
  }

  getEvaluation(evaluationId: number) {
    return this.http.get<any>(`${this.apiUrl}/evaluations/${evaluationId}/`, this.authHeaders());
  }

  saveEvaluation(evaluationId: number, data: any) {
    return this.http.patch<any>(`${this.apiUrl}/evaluations/${evaluationId}/`, data, this.authHeaders());
  }

  updateTournamentStatus(tournamentId: number, status: string) {
    return this.http.patch<any>(`${this.apiUrl}/tournaments/${tournamentId}/status/`, { status }, this.authHeaders());
  }

  distributeRound(roundId: number) {
    return this.http.post<any>(`${this.apiUrl}/rounds/${roundId}/distribute/`, {}, this.authHeaders());
  }

  deleteTeam(teamId: number) {
    return this.http.delete<any>(`${this.apiUrl}/admin/teams/${teamId}/`, this.authHeaders());
  }

  getPendingJuryRegistrations() {
    return this.http.get<any[]>(`${this.apiUrl}/jury/registrations/pending/`, this.authHeaders());
  }

  reviewJuryRegistration(registrationId: number, status: string) {
    return this.http.patch<any>(`${this.apiUrl}/jury/registrations/${registrationId}/review/`, { status }, this.authHeaders());
  }

}
export class Api {}
