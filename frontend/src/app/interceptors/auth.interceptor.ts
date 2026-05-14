import { HttpErrorResponse, HttpInterceptorFn } from '@angular/common/http';
import { inject } from '@angular/core';
import { Router } from '@angular/router';
import { catchError, throwError } from 'rxjs';

function getStoredToken(): string | null {
  return localStorage.getItem('access_token') || localStorage.getItem('token') || localStorage.getItem('access');
}

function isAuthEndpoint(url: string): boolean {
  return url.includes('/auth/login/') || url.includes('/auth/register/');
}

export const authInterceptor: HttpInterceptorFn = (req, next) => {
  const router = inject(Router);
  const token = getStoredToken();

  const authReq = token && !isAuthEndpoint(req.url)
    ? req.clone({
        setHeaders: {
          Authorization: `Bearer ${token}`,
        },
      })
    : req;

  return next(authReq).pipe(
    catchError((error: HttpErrorResponse) => {
      if (error.status === 401 && !isAuthEndpoint(req.url)) {
        localStorage.removeItem('access_token');
        localStorage.removeItem('token');
        localStorage.removeItem('role');
        localStorage.removeItem('nickname');
        localStorage.removeItem('user_id');
        localStorage.removeItem('email');
        router.navigate(['/login']);
      }

      return throwError(() => error);
    })
  );
};
