import { Component, OnInit } from '@angular/core';
import { FormBuilder, FormGroup, Validators, ReactiveFormsModule } from '@angular/forms';
import { CommonModule, Location } from '@angular/common';
import { ActivatedRoute, Router } from '@angular/router';

@Component({
  selector: 'app-add-member',
  standalone: true,
  imports: [CommonModule, ReactiveFormsModule],
  templateUrl: './add-member.component.html',
  styleUrls: ['./add-member.component.scss']
})
export class AddMemberComponent implements OnInit {
  addMemberForm: FormGroup;
  teamId: string | null = null;
  isLoading = false;
  errorMessage = '';

  constructor(
    private fb: FormBuilder,
    private route: ActivatedRoute,
    private router: Router,
    private location: Location
  ) {
    // Ініціалізація форми з валідацією email
    this.addMemberForm = this.fb.group({
      email: ['', [Validators.required, Validators.email]]
    });
  }

  ngOnInit(): void {
    // Отримуємо ID команди з URL, щоб знати куди додавати юзера
    this.teamId = this.route.snapshot.paramMap.get('id');
  }

  onSubmit(): void {
    if (this.addMemberForm.valid) {
      this.isLoading = true;
      const email = this.addMemberForm.value.email;

      console.log(`Відправка запиту на додавання ${email} до команди ${this.teamId}`);
      
      // Імітація запиту до API
      setTimeout(() => {
        this.isLoading = false;
        // Після успішного додавання повертаємось до деталей команди
        this.router.navigate(['/teams', this.teamId]);
      }, 1000);
    }
  }

  goBack(): void {
    this.location.back();
  }
}