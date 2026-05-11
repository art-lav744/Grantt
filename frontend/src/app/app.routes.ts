import { Routes } from '@angular/router';
import { Tournaments } from './pages/tournaments/tournaments';
import { Login } from './pages/login/login';
import { Register } from './pages/register/register';
import { TournamentDetail } from './pages/tournament-detail/tournament-detail';
import { TeamDetail } from './pages/team-detail/team-detail';
import { CreateTeam } from './pages/create-team/create-team';
import { SubmissionForm } from './pages/submission-form/submission-form';
import { Dashboard } from './pages/dashboard/dashboard';
import { JuryEvaluations } from './pages/jury-evaluations/jury-evaluations';
import { EvaluationForm } from './pages/evaluation-form/evaluation-form';
import { AdminActions } from './pages/admin-actions/admin-actions';
import { TournamentEdit } from './pages/tournament-edit/tournament-edit';
import { RoundCreate } from './pages/round-create/round-create';
import { RoundEdit } from './pages/round-edit/round-edit';
import { adminOrganizerGuard, authGuard, juryGuard } from './guards/role.guard';

export const routes: Routes = [
  { path: '', component: Tournaments },
  { path: 'login', component: Login },
  { path: 'register', component: Register },
  { path: 'tournaments/:id', component: TournamentDetail },
  { path: 'tournaments/edit/:id', component: TournamentEdit, canActivate: [adminOrganizerGuard] },
  { path: 'tournaments/:id/create-team', component: CreateTeam, canActivate: [authGuard] },
  { path: 'rounds/create/:id', component: RoundCreate, canActivate: [adminOrganizerGuard] },
  { path: 'rounds/edit/:id', component: RoundEdit, canActivate: [adminOrganizerGuard] },
  { path: 'teams/:id', component: TeamDetail },
  { path: 'teams/:teamId/rounds/:roundId/submit', component: SubmissionForm, canActivate: [authGuard] },
  { path: 'dashboard', component: Dashboard, canActivate: [authGuard] },
  { path: 'dashboard/tournaments', component: Tournaments, canActivate: [authGuard] },
  { path: 'jury/evaluations', component: JuryEvaluations, canActivate: [juryGuard] },
  { path: 'jury/evaluations/:id', component: EvaluationForm, canActivate: [juryGuard] },
  { path: 'admin/actions', component: AdminActions, canActivate: [adminOrganizerGuard] },
  { path: '**', redirectTo: '' }
];
