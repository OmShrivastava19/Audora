import { cn } from '@/lib/utils';
import type { ReactNode } from 'react';

interface MetricCardProps {
  label: string;
  value: string | number;
  icon?: ReactNode;
  trend?: 'up' | 'down' | 'neutral';
  className?: string;
}

export function MetricCard({ label, value, icon, className }: MetricCardProps) {
  return (
    <div
      className={cn(
        'rounded-xl bg-surface border border-border p-4 flex items-center gap-4',
        className
      )}
    >
      {icon && (
        <div className="w-10 h-10 rounded-lg bg-accent-muted flex items-center justify-center flex-shrink-0">
          {icon}
        </div>
      )}
      <div>
        <p className="text-xs font-mono uppercase tracking-widest text-muted">{label}</p>
        <p className="text-xl font-display font-bold text-text mt-0.5">{value}</p>
      </div>
    </div>
  );
}

interface EmptyStateProps {
  icon?: ReactNode;
  title: string;
  description?: string;
  action?: ReactNode;
  className?: string;
}

export function EmptyState({ icon, title, description, action, className }: EmptyStateProps) {
  return (
    <div className={cn('flex flex-col items-center justify-center py-16 text-center', className)}>
      {icon && <div className="text-muted/60 mb-4">{icon}</div>}
      <h3 className="font-display font-bold text-lg text-text-secondary">{title}</h3>
      {description && <p className="text-sm text-muted mt-2 max-w-md">{description}</p>}
      {action && <div className="mt-6">{action}</div>}
    </div>
  );
}

interface SectionLabelProps {
  children: ReactNode;
  className?: string;
}

export function SectionLabel({ children, className }: SectionLabelProps) {
  return (
    <h3
      className={cn(
        'font-mono text-[0.68rem] tracking-[3px] uppercase text-accent mb-3',
        className
      )}
    >
      {children}
    </h3>
  );
}

interface ErrorBannerProps {
  message: string;
  onDismiss?: () => void;
  className?: string;
}

export function ErrorBanner({ message, onDismiss, className }: ErrorBannerProps) {
  return (
    <div
      className={cn(
        'flex items-center gap-3 rounded-lg bg-accent2-muted border border-accent2/30 px-4 py-3 text-sm text-accent2',
        className
      )}
      role="alert"
    >
      <svg className="w-5 h-5 flex-shrink-0" fill="currentColor" viewBox="0 0 20 20">
        <path
          fillRule="evenodd"
          d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-7 4a1 1 0 11-2 0 1 1 0 012 0zm-1-9a1 1 0 00-1 1v4a1 1 0 102 0V6a1 1 0 00-1-1z"
          clipRule="evenodd"
        />
      </svg>
      <p className="flex-1">{message}</p>
      {onDismiss && (
        <button
          onClick={onDismiss}
          className="text-accent2 hover:text-accent2/70 transition-colors"
          aria-label="Dismiss error"
        >
          ✕
        </button>
      )}
    </div>
  );
}
