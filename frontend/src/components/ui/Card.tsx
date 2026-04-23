import { type ReactNode } from 'react';
import { cn } from '@/lib/utils';

interface CardProps {
  children: ReactNode;
  className?: string;
  variant?: 'default' | 'accent' | 'danger' | 'glass';
  hover?: boolean;
  onClick?: () => void;
}

export function Card({ children, className, variant = 'default', hover, onClick }: CardProps) {
  const variants: Record<string, string> = {
    default: 'bg-surface border-border',
    accent: 'bg-surface border-l-4 border-l-accent border-t border-r border-b border-t-border border-r-border border-b-border',
    danger: 'bg-surface border-l-4 border-l-accent2 border-t border-r border-b border-t-border border-r-border border-b-border',
    glass: 'glass',
  };

  return (
    <div
      className={cn(
        'rounded-xl border p-5 transition-all duration-200',
        variants[variant],
        hover && 'cursor-pointer hover:border-border-focus hover:bg-surface-hover hover:shadow-md',
        onClick && 'cursor-pointer',
        className
      )}
      onClick={onClick}
      role={onClick ? 'button' : undefined}
      tabIndex={onClick ? 0 : undefined}
    >
      {children}
    </div>
  );
}

interface CardHeaderProps {
  children: ReactNode;
  className?: string;
}

export function CardHeader({ children, className }: CardHeaderProps) {
  return <div className={cn('mb-3', className)}>{children}</div>;
}

interface CardContentProps {
  children: ReactNode;
  className?: string;
}

export function CardContent({ children, className }: CardContentProps) {
  return <div className={cn('', className)}>{children}</div>;
}
