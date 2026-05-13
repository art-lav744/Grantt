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

  truncate(text: string): string {
    if (!text) return '';
    const words = text.split(' ');
    if (words.length <= 20) return text;
    return words.slice(0, 20).join(' ') + '...';
  }
}