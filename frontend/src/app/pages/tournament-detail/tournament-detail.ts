import { ChangeDetectorRef, Component, OnInit, ElementRef, ViewChild } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { ActivatedRoute, RouterLink } from '@angular/router';

import { ApiService } from '../../services/api';

@Component({
  selector: 'app-tournament-detail',
  standalone: true,
  imports: [CommonModule, FormsModule, RouterLink],
  templateUrl: './tournament-detail.html',
  styleUrl: './tournament-detail.scss',
})
export class TournamentDetail implements OnInit {
  @ViewChild('cropperCanvas') cropperCanvas!: ElementRef<HTMLCanvasElement>;
  @ViewChild('cropperImage') cropperImage!: ElementRef<HTMLImageElement>;

  tournament: any = { banner_url: '', title: '', description: '', reg_start: null, reg_end: null, status: '' };
  teams: any[] = [];
  rounds: any[] = [];
  files: any[] = [];
  error = '';
  message = '';
  canAccessFiles = false;

  selectedFile: File | null = null;
  fileTitle = '';
  fileType = 'document';
  uploadingFile = false;

  // Кропер банера
  showCropper = false;
  selectedBannerFile: File | null = null;
  cropImageSrc: string = '';
  isCropping = false;

  // Параметри масштабування та позиції
  scale = 1;
  minScale = 0.5;
  maxScale = 5;
  offsetX = 0;
  offsetY = 0;
  isDragging = false;
  lastX = 0;
  lastY = 0;

  private readonly targetWidth = 1200;
  private readonly targetHeight = 450;

  constructor(
    private route: ActivatedRoute,
    private api: ApiService,
    private cdr: ChangeDetectorRef
  ) {}

  get role(): string {
    return (localStorage.getItem('role') || '').toLowerCase();
  }

  get canManageRounds(): boolean {
    return this.role === 'admin' || this.role === 'organizer';
  }

  get isJury(): boolean {
    return this.role === 'jury';
  }

  get canUploadFiles(): boolean {
    return this.canManageRounds;
  }

  get canRegisterTeam(): boolean {
    return this.isLoggedIn() && this.role === 'participant' && 
           String(this.tournament?.status || '').toLowerCase() === 'registration';
  }

  ngOnInit(): void {
    const id = Number(this.route.snapshot.paramMap.get('id'));
    if (!id) {
      this.error = 'Турнір не знайдено';
      return;
    }

    this.api.getTournament(id).subscribe({
      next: (item: any) => {
        this.tournament = this.normalizeTournament(item);
        this.cdr.detectChanges();
      },
      error: () => {
        this.error = 'Не вдалося завантажити турнір';
        this.cdr.detectChanges();
      }
    });

    this.api.getTournamentTeams(id).subscribe({
      next: (teams: any) => {
        this.teams = Array.isArray(teams) ? teams : [];
        this.cdr.detectChanges();
      },
      error: () => { this.teams = []; this.cdr.detectChanges(); }
    });

    this.api.getTournamentRounds(id).subscribe({
      next: (rounds: any) => {
        this.rounds = Array.isArray(rounds) ? rounds.map((round: any) => this.normalizeRound(round)) : [];
        this.cdr.detectChanges();
      },
      error: () => { this.rounds = []; this.cdr.detectChanges(); }
    });

    this.loadFiles(id);
  }

  // ==================== КРОПЕР БАНЕРА ====================
  onBannerSelected(event: Event): void {
    const input = event.target as HTMLInputElement;
    const file = input.files?.[0];
    if (!file || !this.canManageRounds) return;

    this.selectedBannerFile = file;
    this.scale = 1;
    this.offsetX = 0;
    this.offsetY = 0;

    const reader = new FileReader();
    reader.onload = (e) => {
      this.cropImageSrc = e.target?.result as string;
      this.showCropper = true;
      this.cdr.detectChanges();
    };
    reader.readAsDataURL(file);
  }

  onCropImageLoad(): void {
    this.drawCanvas();
  }

  private drawCanvas(): void {
    const canvas = this.cropperCanvas.nativeElement;
    const ctx = canvas.getContext('2d')!;
    const img = this.cropperImage.nativeElement;

    canvas.width = this.targetWidth;
    canvas.height = this.targetHeight;

    ctx.clearRect(0, 0, canvas.width, canvas.height);

    const scaledWidth = img.width * this.scale;
    const scaledHeight = img.height * this.scale;

    const x = (canvas.width - scaledWidth) / 2 + this.offsetX;
    const y = (canvas.height - scaledHeight) / 2 + this.offsetY;

    ctx.drawImage(img, x, y, scaledWidth, scaledHeight);
  }

  onScaleChange(): void {
    this.drawCanvas();
  }

  onMouseDown(e: MouseEvent): void {
    this.isDragging = true;
    this.lastX = e.clientX;
    this.lastY = e.clientY;
    this.cropperCanvas.nativeElement.style.cursor = 'grabbing';
  }

  onMouseMove(e: MouseEvent): void {
    if (!this.isDragging) return;

    this.offsetX += (e.clientX - this.lastX);
    this.offsetY += (e.clientY - this.lastY);

    this.lastX = e.clientX;
    this.lastY = e.clientY;

    this.drawCanvas();
  }

  onMouseUp(): void {
    this.isDragging = false;
    if (this.cropperCanvas?.nativeElement) {
      this.cropperCanvas.nativeElement.style.cursor = 'grab';
    }
  }

  async confirmBannerCrop(): Promise<void> {
    if (!this.cropperCanvas || !this.selectedBannerFile || !this.tournament?.id) return;

    this.isCropping = true;
    this.cdr.detectChanges();

    const canvas = this.cropperCanvas.nativeElement;
    const croppedDataUrl = canvas.toDataURL('image/jpeg', 0.92);

    this.tournament = { ...this.tournament, banner_url: croppedDataUrl };

    try {
      const response = await fetch(croppedDataUrl);
      const blob = await response.blob();
      const croppedFile = new File([blob], this.selectedBannerFile.name, { type: 'image/jpeg' });

      this.api.uploadTournamentImage(this.tournament.id, croppedFile).subscribe({
        next: (updated: any) => {
          this.tournament = this.normalizeTournament(updated);
          this.resetCropper();
        },
        error: () => {
          this.error = 'Не вдалося зберегти банер турніру';
          this.resetCropper();
        }
      });
    } catch {
      this.error = 'Помилка обробки зображення';
      this.resetCropper();
    }
  }

  cancelBannerCrop(): void {
    this.resetCropper();
  }

  private resetCropper(): void {
    this.showCropper = false;
    this.cropImageSrc = '';
    this.selectedBannerFile = null;
    this.isCropping = false;
    this.scale = 1;
    this.offsetX = 0;
    this.offsetY = 0;
    this.cdr.detectChanges();
  }
  // =====================================================

  // ==================== ЗАВАНТАЖЕННЯ ФАЙЛУ ====================
  downloadFile(file: any): void {
    const url = this.fileUrl(file);
    if (!url) return;

    const fileName = file.title || file.original_name || file.name || `file_${Date.now()}`;

    fetch(url)
      .then(response => {
        if (!response.ok) throw new Error('Помилка мережі');
        return response.blob();
      })
      .then(blob => {
        const downloadUrl = window.URL.createObjectURL(blob);
        const link = document.createElement('a');
        link.href = downloadUrl;
        link.download = fileName;
        document.body.appendChild(link);
        link.click();
        document.body.removeChild(link);
        window.URL.revokeObjectURL(downloadUrl);
      })
      .catch(() => {
        this.error = 'Не вдалося завантажити файл. Спробуйте відкрити його в новій вкладці.';
        this.cdr.detectChanges();
      });
  }
  // =====================================================

  onFileSelected(event: Event): void {
    const input = event.target as HTMLInputElement;
    this.selectedFile = input.files?.[0] || null;
    if (this.selectedFile && !this.fileTitle) {
      this.fileTitle = this.selectedFile.name;
    }
  }

  uploadFile(): void {
    if (!this.tournament?.id || !this.selectedFile || !this.fileTitle.trim()) {
      this.error = 'Оберіть файл і вкажіть назву.';
      return;
    }

    this.error = '';
    this.message = '';
    this.uploadingFile = true;

    this.api.uploadTournamentFile(this.tournament.id, {
      title: this.fileTitle.trim(),
      file_type: this.fileType || 'document',
      file: this.selectedFile
    }).subscribe({
      next: () => {
        this.message = 'Файл додано до турніру.';
        this.fileTitle = '';
        this.fileType = 'document';
        this.selectedFile = null;
        this.uploadingFile = false;
        this.loadFiles(this.tournament.id);
      },
      error: (err: any) => {
        this.error = this.extractError(err) || 'Не вдалося завантажити файл.';
        this.uploadingFile = false;
        this.cdr.detectChanges();
      }
    });
  }

  applyAsJury(): void {
    if (!this.tournament?.id) return;
    this.error = '';
    this.message = '';
    this.api.applyAsJury(this.tournament.id).subscribe({
      next: (registration: any) => {
        const status = registration?.status === 'approved' ? 'підтверджена' : 'очікує підтвердження';
        this.message = `Заявка журі ${status}.`;
        this.cdr.detectChanges();
      },
      error: (err: any) => {
        this.error = this.extractError(err) || 'Не вдалося подати заявку журі.';
        this.cdr.detectChanges();
      }
    });
  }

  private normalizeTournament(item: any): any {
    return {
      ...item,
      banner_url: this.toMediaUrl(item?.banner_url || item?.cover_image_path || '')
    };
  }

  fileUrl(file: any): string {
    return this.toMediaUrl(file?.file_url || file?.download_url || file?.url || file?.file || '');
  }

  private toMediaUrl(value: any): string {
    if (!value) return '';
    const url = String(value);
    if (url.startsWith('http://') || url.startsWith('https://') || url.startsWith('data:')) return url;
    if (url.startsWith('/')) return `http://127.0.0.1:8000${url}`;
    return `http://127.0.0.1:8000/${url}`;
  }

  private normalizeRound(round: any): any {
    return {
      ...round,
      start: round?.start || this.formatDateTime(round?.start_time),
      end: round?.end || this.formatDateTime(round?.end_time)
    };
  }

  private loadFiles(tournamentId: number): void {
    if (!this.isLoggedIn()) return;

    this.api.getTournamentFiles(tournamentId).subscribe({
      next: (files: any) => {
        this.files = Array.isArray(files) ? files : [];
        this.canAccessFiles = true;
        this.cdr.detectChanges();
      },
      error: () => {
        this.files = [];
        this.canAccessFiles = false;
        this.cdr.detectChanges();
      }
    });
  }

  private formatDateTime(value: any): string {
    if (!value) return '—';
    const date = new Date(value);
    if (Number.isNaN(date.getTime())) return String(value);
    return date.toLocaleString('uk-UA', {
      day: '2-digit',
      month: '2-digit',
      year: 'numeric',
      hour: '2-digit',
      minute: '2-digit'
    });
  }

  private isLoggedIn(): boolean {
    return !!(localStorage.getItem('access_token') || localStorage.getItem('token') || localStorage.getItem('access'));
  }

  private extractError(err: any): string {
    const payload = err?.error;
    if (!payload) return '';
    if (typeof payload === 'string') return payload;
    if (payload.detail || payload.message) return String(payload.detail || payload.message);
    const firstValue = Object.values(payload)[0];
    return Array.isArray(firstValue) ? String(firstValue[0]) : String(firstValue || '');
  }
}