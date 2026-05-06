import { Component, Input } from '@angular/core';
import { CommonModule } from '@angular/common';

@Component({
  selector: 'app-jury-card',
  standalone: true,
  imports: [CommonModule],
  templateUrl: './jury-card.component.html',
  styleUrls: ['./jury-card.component.scss']
})
export class JuryCardComponent {
  @Input() eval: any;
  @Input() border: string = '#2563eb';
  @Input() label: string = 'Нова';
  @Input() btn_label: string = 'Оцінити';

  truncate(text: string): string {
    return text.split(' ').slice(0, 25).join(' ') + '...';
  }
}