import { Injectable } from '@angular/core';

export type Role = 'guest' | 'participant' | 'jury' | 'organizer' | 'admin';

@Injectable({ providedIn: 'root' })
export class AuthRoleService {
  get token(): string | null {
    return localStorage.getItem('access_token') || localStorage.getItem('token');
  }

  get isLoggedIn(): boolean {
    return !!this.token;
  }

  get nickname(): string {
    return this.firstString([
      localStorage.getItem('nickname'),
      localStorage.getItem('username'),
      this.localUserValue('nickname'),
      this.localUserValue('username'),
      this.jwtValue('nickname'),
      this.jwtValue('username'),
      this.jwtValue('email')
    ]) || 'Grantt';
  }

  get role(): Role {
    const rawRole = this.firstString([
      localStorage.getItem('role'),
      localStorage.getItem('user_role'),
      this.localUserValue('role'),
      this.localUserValue('user_role'),
      this.jwtValue('role'),
      this.jwtValue('user_role'),
      this.jwtValue('type')
    ]);

    const normalized = this.normalizeRole(rawRole);
    if (normalized) return normalized;

    if (this.anyBool(['is_admin_like', 'is_superuser', 'is_staff'])) {
      return 'admin';
    }

    if (this.anyBool(['is_jury_like'])) {
      return 'jury';
    }

    return this.isLoggedIn ? 'participant' : 'guest';
  }

  get isAdmin(): boolean { return this.role === 'admin'; }
  get isOrganizer(): boolean { return this.role === 'organizer'; }
  get isJury(): boolean { return this.role === 'jury'; }
  get isParticipant(): boolean { return this.role === 'participant'; }

  // These getters intentionally mirror backend User.is_admin_like / User.is_jury_like:
  // is_admin_like => admin OR organizer; is_jury_like => jury OR organizer.
  get isAdminLike(): boolean { return this.isAdmin || this.isOrganizer; }
  get isJuryLike(): boolean { return this.isJury || this.isOrganizer; }

  get canUseAdminPanel(): boolean { return this.isAdminLike; }
  get canManageTournaments(): boolean { return this.isAdminLike; }
  get canManageTeams(): boolean { return this.isAdminLike; }
  get canReviewJuryRequests(): boolean { return this.isAdminLike; }
  get canEvaluateSubmissions(): boolean { return this.isJuryLike; }
  get canCreateTeam(): boolean { return this.isParticipant; }
  get canSubmitWork(): boolean { return this.isParticipant; }

  hasAnyRole(allowedRoles: string[]): boolean {
    const normalized = allowedRoles
      .map(role => this.normalizeRole(role))
      .filter((role): role is Role => !!role);
    return normalized.includes(this.role);
  }

  clearSession(): void {
    [
      'access_token', 'refresh_token', 'token',
      'role', 'user_role', 'nickname', 'username', 'user_id', 'email',
      'is_staff', 'is_superuser', 'is_admin_like', 'is_jury_like', 'user', 'current_user'
    ].forEach(key => localStorage.removeItem(key));
  }

  private normalizeRole(value: unknown): Role | null {
    const role = String(value || '').toLowerCase().trim();

    if (['admin', 'administrator', 'superuser', 'staff'].includes(role)) return 'admin';
    if (['organizer', 'organiser'].includes(role)) return 'organizer';
    if (['jury', 'judge'].includes(role)) return 'jury';
    if (['participant', 'user', 'member'].includes(role)) return 'participant';
    if (['guest', 'anonymous', 'anon'].includes(role)) return 'guest';

    return null;
  }

  private firstString(values: unknown[]): string {
    for (const value of values) {
      if (typeof value === 'string' && value.trim()) return value.trim();
      if (typeof value === 'number' || typeof value === 'boolean') return String(value);
    }
    return '';
  }

  private boolValue(value: unknown): boolean {
    if (typeof value === 'boolean') return value;
    return ['true', '1', 'yes'].includes(String(value || '').toLowerCase().trim());
  }

  private anyBool(keys: string[]): boolean {
    return keys.some(key =>
      this.boolValue(localStorage.getItem(key)) ||
      this.boolValue(this.localUserValue(key)) ||
      this.boolValue(this.jwtValue(key))
    );
  }

  private localUserValue(key: string): unknown {
    const raw = localStorage.getItem('user') || localStorage.getItem('current_user');
    if (!raw) return null;

    try {
      return JSON.parse(raw)?.[key] ?? null;
    } catch {
      return null;
    }
  }

  private jwtValue(key: string): unknown {
    const payload = this.jwtPayload();
    return payload?.[key] ?? payload?.user?.[key] ?? null;
  }

  private jwtPayload(): any | null {
    const token = this.token;
    if (!token || !token.includes('.')) return null;

    try {
      const payload = token.split('.')[1].replace(/-/g, '+').replace(/_/g, '/');
      const decoded = atob(payload.padEnd(payload.length + (4 - payload.length % 4) % 4, '='));
      return JSON.parse(decoded);
    } catch {
      return null;
    }
  }
}
