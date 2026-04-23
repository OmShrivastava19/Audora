import { clsx, type ClassValue } from 'clsx';
import { twMerge } from 'tailwind-merge';

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs));
}

export function formatTimestamp(seconds: number): string {
  const total = Math.max(0, Math.round(seconds));
  const mm = Math.floor(total / 60);
  const ss = total % 60;
  return `${String(mm).padStart(2, '0')}:${String(ss).padStart(2, '0')}`;
}

export function formatFileSize(bytes: number): string {
  if (bytes < 1024) return `${bytes} B`;
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
  return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
}

export function formatDate(date: string): string {
  return new Date(date).toLocaleDateString('en-US', {
    year: 'numeric',
    month: 'short',
    day: 'numeric',
    hour: '2-digit',
    minute: '2-digit',
  });
}

export function slugify(text: string): string {
  return text
    .toLowerCase()
    .replace(/[^a-z0-9]+/g, '_')
    .replace(/^_|_$/g, '')
    .slice(0, 28);
}

export function sleep(ms: number): Promise<void> {
  return new Promise((resolve) => setTimeout(resolve, ms));
}

export function getConfidenceColor(label: string): string {
  switch (label.toUpperCase()) {
    case 'HIGH':
      return 'text-accent border-accent bg-accent-muted';
    case 'MEDIUM':
      return 'text-accent3 border-accent3 bg-accent3-muted';
    case 'LOW':
      return 'text-accent2 border-accent2 bg-accent2-muted';
    default:
      return 'text-muted border-border bg-surface';
  }
}

export function getUrgencyColor(urgency: string): string {
  return urgency === 'HIGH'
    ? 'text-accent2 border-accent2 bg-accent2-muted'
    : 'text-accent3 border-accent3 bg-accent3-muted';
}

export function getCoverageColor(percent: number): string {
  if (percent >= 70) return '#4fffb0';
  if (percent >= 25) return '#ffd166';
  return '#ff6b6b';
}

export function getCoverageGradient(percent: number): string {
  const color = getCoverageColor(percent);
  return `linear-gradient(90deg, ${color}ee, ${color}88)`;
}
