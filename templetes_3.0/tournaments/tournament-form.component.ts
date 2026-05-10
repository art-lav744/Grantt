import { Component, OnInit, Input } from '@angular/forms';
import { FormBuilder, FormGroup, Validators, ReactiveFormsModule } from '@angular/forms';
import { CommonModule } from '@angular/common';
import { trigger, transition, style, animate, query, stagger } from '@angular/animations';

@Component({
  selector: 'app-tournament-form',
  standalone: true,
  imports: [CommonModule, ReactiveFormsModule],
  templateUrl: './tournament-form.component.html',
  styleUrls: ['./tournament-form.component.scss'],
  animations: [
    trigger('listAnimation', [
      transition('* <=> *', [
        query(':enter', [
          style({ opacity: 0, transform: 'translateY(-10px)' }),
          stagger('50ms', animate('300ms ease-out', style({ opacity: 1, transform: 'translateY(0)' })))
        ], { optional: true })
      ])
    ]),
    trigger('fadeSlide', [
      transition(':enter', [
        style({ opacity: 0, transform: 'translateY(20px)' }),
        animate('400ms ease-out', style({ opacity: 1, transform: 'translateY(0)' }))
      ])
    ])
  ]
})
export class TournamentFormComponent implements OnInit {
  @Input() tournamentData: any; // Сюди передаємо реальні дані з батьківського компонента
  
  tournamentForm!: FormGroup;
  fileForm!: FormGroup;
  isEdit = false;
  files: any[] = []; // Порожній масив, який заповниться реальними даними

  constructor(private fb: FormBuilder) {}

  ngOnInit(): void {
    this.isEdit = !!this.tournamentData;
    this.initForms();
    
    if (this.isEdit) {
      this.tournamentForm.patchValue(this.tournamentData);
      this.files = this.tournamentData.files || [];
    }
  }

  private initForms(): void {
    this.tournamentForm = this.fb.group({
      title: [this.tournamentData?.title || '', [Validators.required]],
      reg_start: [this.tournamentData?.reg_start || '', Validators.required],
      reg_end: [this.tournamentData?.reg_end || '', Validators.required]
    });

    this.fileForm = this.fb.group({
      fileTitle: ['', Validators.required],
      fileSource: [null, Validators.required]
    });
  }

  onFileChange(event: any): void {
    const file = event.target.files[0];
    if (file) {
      this.fileForm.patchValue({ fileSource: file });
    }
  }

  saveTournament(): void {
    if (this.tournamentForm.valid) {
      // Відправка реального об'єкта на сервер
      const payload = {
        ...this.tournamentForm.value,
        id: this.tournamentData?.id
      };
      console.log('Sending to API:', payload);
    }
  }

  uploadFile(): void {
    if (this.fileForm.valid) {
      const formData = new FormData();
      formData.append('title', this.fileForm.value.fileTitle);
      formData.append('file', this.fileForm.value.fileSource);

      // Імітація успішного завантаження для UI
      this.files.push({
        title: this.fileForm.value.fileTitle,
        type: this.fileForm.value.fileSource.name.split('.').pop().toUpperCase(),
        date: new Date().toLocaleDateString('uk-UA')
      });
      this.fileForm.reset();
    }
  }
}import { Component, OnInit, Input } from '@angular/forms';
import { FormBuilder, FormGroup, Validators, ReactiveFormsModule } from '@angular/forms';
import { CommonModule } from '@angular/common';
import { trigger, transition, style, animate, query, stagger } from '@angular/animations';

@Component({
  selector: 'app-tournament-form',
  standalone: true,
  imports: [CommonModule, ReactiveFormsModule],
  templateUrl: './tournament-form.component.html',
  styleUrls: ['./tournament-form.component.scss'],
  animations: [
    trigger('listAnimation', [
      transition('* <=> *', [
        query(':enter', [
          style({ opacity: 0, transform: 'translateY(-10px)' }),
          stagger('50ms', animate('300ms ease-out', style({ opacity: 1, transform: 'translateY(0)' })))
        ], { optional: true })
      ])
    ]),
    trigger('fadeSlide', [
      transition(':enter', [
        style({ opacity: 0, transform: 'translateY(20px)' }),
        animate('400ms ease-out', style({ opacity: 1, transform: 'translateY(0)' }))
      ])
    ])
  ]
})
export class TournamentFormComponent implements OnInit {
  @Input() tournamentData: any; // Сюди передаємо реальні дані з батьківського компонента
  
  tournamentForm!: FormGroup;
  fileForm!: FormGroup;
  isEdit = false;
  files: any[] = []; // Порожній масив, який заповниться реальними даними

  constructor(private fb: FormBuilder) {}

  ngOnInit(): void {
    this.isEdit = !!this.tournamentData;
    this.initForms();
    
    if (this.isEdit) {
      this.tournamentForm.patchValue(this.tournamentData);
      this.files = this.tournamentData.files || [];
    }
  }

  private initForms(): void {
    this.tournamentForm = this.fb.group({
      title: [this.tournamentData?.title || '', [Validators.required]],
      reg_start: [this.tournamentData?.reg_start || '', Validators.required],
      reg_end: [this.tournamentData?.reg_end || '', Validators.required]
    });

    this.fileForm = this.fb.group({
      fileTitle: ['', Validators.required],
      fileSource: [null, Validators.required]
    });
  }

  onFileChange(event: any): void {
    const file = event.target.files[0];
    if (file) {
      this.fileForm.patchValue({ fileSource: file });
    }
  }

  saveTournament(): void {
    if (this.tournamentForm.valid) {
      // Відправка реального об'єкта на сервер
      const payload = {
        ...this.tournamentForm.value,
        id: this.tournamentData?.id
      };
      console.log('Sending to API:', payload);
    }
  }

  uploadFile(): void {
    if (this.fileForm.valid) {
      const formData = new FormData();
      formData.append('title', this.fileForm.value.fileTitle);
      formData.append('file', this.fileForm.value.fileSource);

      // Імітація успішного завантаження для UI
      this.files.push({
        title: this.fileForm.value.fileTitle,
        type: this.fileForm.value.fileSource.name.split('.').pop().toUpperCase(),
        date: new Date().toLocaleDateString('uk-UA')
      });
      this.fileForm.reset();
    }
  }
}