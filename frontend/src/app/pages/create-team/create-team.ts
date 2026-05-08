import { Component, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormArray, FormBuilder, FormGroup, ReactiveFormsModule, Validators } from '@angular/forms';
import { ActivatedRoute, Router, RouterLink } from '@angular/router';
import { ApiService } from '../../services/api';

@Component({
  selector: 'app-create-team',
  standalone: true,
  imports: [CommonModule, ReactiveFormsModule, RouterLink],
  templateUrl: './create-team.html',
  styleUrl: './create-team.scss',
})
export class CreateTeam implements OnInit {
  tournamentId = 0;
  teamForm: FormGroup;
  error = '';
  success = '';
  loading = false;

  constructor(
    private fb: FormBuilder,
    private route: ActivatedRoute,
    private router: Router,
    private api: ApiService
  ) {
    this.teamForm = this.fb.group({
      name: ['', Validators.required],
      captain_name: ['', Validators.required],
      captain_email: ['', [Validators.required, Validators.email]],
      members: this.fb.array([])
    });
  }

  ngOnInit(): void {
    this.tournamentId = Number(this.route.snapshot.paramMap.get('id'));
  }

  get members(): FormArray {
    return this.teamForm.get('members') as FormArray;
  }

  addMember(): void {
    this.members.push(this.fb.group({
      full_name: ['', Validators.required],
      email: ['', [Validators.required, Validators.email]]
    }));
  }

  removeMember(index: number): void {
    this.members.removeAt(index);
  }

  private extractError(error: any): string {
    const data = error?.error;
    if (!data) {
      return 'Не вдалося створити команду';
    }
    if (typeof data === 'string') {
      return data;
    }
    if (data.detail) {
      return data.detail;
    }
    if (data.non_field_errors?.length) {
      return data.non_field_errors.join(' ');
    }
    return JSON.stringify(data);
  }

  onSubmit(): void {
    if (this.teamForm.invalid) {
      this.teamForm.markAllAsTouched();
      return;
    }

    this.error = '';
    this.success = '';
    this.loading = true;

    const payload = {
      ...this.teamForm.value,
      tournament_id: this.tournamentId
    };

    this.api.createTeam(payload).subscribe({
      next: (team: any) => {
        this.success = 'Команду створено';
        this.loading = false;
        this.router.navigate(['/teams', team.id]);
      },
      error: (error: any) => {
        this.error = this.extractError(error);
        this.loading = false;
      }
    });
  }
}
