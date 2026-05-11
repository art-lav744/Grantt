import { inject } from '@angular/core';
import { CanActivateFn, Router } from '@angular/router';

function currentRole(): string {
  return (localStorage.getItem('role') || '').toLowerCase();
}

function hasAnyRole(allowedRoles: string[]): boolean {
  const role = currentRole();
  return allowedRoles.map(item => item.toLowerCase()).includes(role);
}

export const authGuard: CanActivateFn = () => {
  const router = inject(Router);
  const token = localStorage.getItem('access_token') || localStorage.getItem('token') || localStorage.getItem('access');

  if (token) {
    return true;
  }

  return router.createUrlTree(['/login']);
};

export const adminOrganizerGuard: CanActivateFn = () => {
  const router = inject(Router);
  const token = localStorage.getItem('access_token') || localStorage.getItem('token') || localStorage.getItem('access');

  if (!token) {
    return router.createUrlTree(['/login']);
  }

  if (hasAnyRole(['admin', 'organizer'])) {
    return true;
  }

  return router.createUrlTree(['/dashboard'], {
    queryParams: { forbidden: 'admin' }
  });
};

export const juryGuard: CanActivateFn = () => {
  const router = inject(Router);
  const token = localStorage.getItem('access_token') || localStorage.getItem('token') || localStorage.getItem('access');

  if (!token) {
    return router.createUrlTree(['/login']);
  }

  if (hasAnyRole(['jury', 'organizer'])) {
    return true;
  }

  return router.createUrlTree(['/dashboard'], {
    queryParams: { forbidden: 'jury' }
  });
};
