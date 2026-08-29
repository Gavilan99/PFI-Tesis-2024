import { Component, ElementRef, EventEmitter, HostListener, OnDestroy, OnInit, Output, ViewChild } from '@angular/core';
import { BrandButtonComponent } from '../../shared/components/brand-button/brand-button.component';

// What "Desbloquear mi perfil completo" (RF09/RF10) opens instead of doing
// nothing — an honest preview of the tiers, since Mercado Pago isn't wired
// up yet (see mvp-status.md). Self-contained modal: captures focus on
// init and restores it on destroy, closes on Escape or a backdrop click.
@Component({
  selector: 'app-freemium-info-dialog',
  standalone: true,
  imports: [BrandButtonComponent],
  templateUrl: './freemium-info-dialog.component.html',
  styleUrl: './freemium-info-dialog.component.scss',
})
export class FreemiumInfoDialogComponent implements OnInit, OnDestroy {
  @Output() closed = new EventEmitter<void>();
  @ViewChild('dialog') private dialogRef?: ElementRef<HTMLElement>;
  private focusedElementBeforeOpen: HTMLElement | null = null;

  ngOnInit(): void {
    this.focusedElementBeforeOpen = document.activeElement as HTMLElement | null;
    setTimeout(() => this.dialogRef?.nativeElement.focus());
  }

  ngOnDestroy(): void {
    this.focusedElementBeforeOpen?.focus();
  }

  close(): void {
    this.closed.emit();
  }

  @HostListener('window:keydown.escape')
  onEscape(): void {
    this.close();
  }
}
