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

  getMe() {
    return this.http.get<any>(`${this.apiUrl}/users/me/`, this.authHeaders());
  }

  updateMe(payload: any) {
    return this.http.patch<any>(`${this.apiUrl}/users/me/`, payload, this.authHeaders());
  }

  createTournament(data: any) {
    return this.http.post<any>(`${this.apiUrl}/tournaments/`, data, this.authHeaders());
  }

  getTournament(id: number) {
    return this.http.get<any>(`${this.apiUrl}/tournaments/${id}/`, this.authHeaders());
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
    return this.http.get<any[]>(`${this.apiUrl}/tournaments/${id}/teams/`, this.authHeaders());
  }

  getTournamentRounds(tournamentId: number) {
    return this.http.get<any[]>(`${this.apiUrl}/rounds/?tournament_id=${tournamentId}`, this.authHeaders());
  }

  getTournamentFiles(tournamentId: number) {
    return this.http.get<any[]>(`${this.apiUrl}/tournaments/${tournamentId}/files/`, this.authHeaders());
  }

  uploadTournamentFile(tournamentId: number, data: { title: string; file_type: string; file: File }) {
    const body = new FormData();
    body.append('title', data.title);
    body.append('file_type', data.file_type);
    body.append('file', data.file);
    return this.http.post<any>(`${this.apiUrl}/tournaments/${tournamentId}/files/`, body, this.authHeaders());
  }

  uploadTournamentImage(tournamentId: number, file: File) {
    const body = new FormData();
    body.append('file', file);
    return this.http.post<any>(`${this.apiUrl}/tournaments/${tournamentId}/image/`, body, this.authHeaders());
  }

  getTournamentLeaderboard(tournamentId: number) {
    return this.http.get<any>(`${this.apiUrl}/tournaments/${tournamentId}/leaderboard/`);
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
    return this.http.get<any>(`${this.apiUrl}/teams/${teamId}/`, this.authHeaders());
  }

  createTeam(data: any) {
    return this.http.post<any>(`${this.apiUrl}/teams/`, data, this.authHeaders());
  }

  addTeamMember(teamId: number, data: { email: string; full_name?: string }) {
    return this.http.post<any>(`${this.apiUrl}/teams/${teamId}/members/`, data, this.authHeaders());
  }

  deleteTeamMember(teamId: number, memberId: number) {
    return this.http.delete<any>(`${this.apiUrl}/teams/${teamId}/members/${memberId}/`, this.authHeaders());
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

  applyAsJury(tournamentId: number) {
    return this.http.post<any>(`${this.apiUrl}/jury/registrations/`, { tournament_id: tournamentId }, this.authHeaders());
  }

}

@Injectable({
  providedIn: 'root'
})
export class Api {}
