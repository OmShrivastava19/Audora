import { cn } from '@/lib/utils';
import type { ReactNode } from 'react';

interface BadgeProps {
  children: ReactNode;
  variant?: 'default' | 'accent' | 'danger' | 'warning' | 'info' | 'muted';
  size?: 'sm' | 'md';
  className?: string;
}

export function Badge({ children, variant = 'default', size = 'sm', className }: BadgeProps) {
  const variants: Record<string, string> = {
    default: 'border-border text-muted bg-surface',
    accent: 'border-accent/40 text-accent bg-accent-muted',
    danger: 'border-accent2/40 text-accent2 bg-accent2-muted',
    warning: 'border-accent3/40 text-accent3 bg-accent3-muted',
    info: 'border-info/40 text-info bg-info-muted',
    muted: 'border-border text-muted bg-transparent',
  };

  const sizes: Record<string, string> = {
    sm: 'px-2.5 py-0.5 text-[0.65rem]',
    md: 'px-3 py-1 text-xs',
  };

  return (
    <span
      className={cn(
        'inline-flex items-center rounded-md border font-mono font-medium uppercase tracking-widest',
        variants[variant],
        sizes[size],
        className
      )}
    >
      {children}
    </span>
  );
}
