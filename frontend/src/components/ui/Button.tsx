import { forwardRef, type ButtonHTMLAttributes } from 'react';
import { cn } from '@/lib/utils';

interface ButtonProps extends ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: 'primary' | 'secondary' | 'ghost' | 'danger' | 'outline';
  size?: 'sm' | 'md' | 'lg';
  loading?: boolean;
  fullWidth?: boolean;
}

const Button = forwardRef<HTMLButtonElement, ButtonProps>(
  ({ className, variant = 'primary', size = 'md', loading, fullWidth, children, disabled, ...props }, ref) => {
    const base =
      'inline-flex items-center justify-center gap-2 font-display font-bold tracking-tight rounded-lg transition-all duration-200 focus-visible:outline-2 focus-visible:outline-accent disabled:opacity-40 disabled:cursor-not-allowed select-none';

    const variants: Record<string, string> = {
      primary:
        'bg-accent text-bg hover:shadow-glow hover:brightness-110 active:scale-[0.97]',
      secondary:
        'bg-surface text-text border border-border hover:bg-surface-hover hover:border-border-focus active:scale-[0.97]',
      ghost:
        'text-text-secondary hover:bg-surface hover:text-text active:scale-[0.97]',
      danger:
        'bg-accent2-muted text-accent2 border border-accent2/30 hover:bg-accent2/20 active:scale-[0.97]',
      outline:
        'border border-border text-text-secondary hover:border-accent hover:text-accent active:scale-[0.97]',
    };

    const sizes: Record<string, string> = {
      sm: 'h-8 px-3 text-xs',
      md: 'h-10 px-5 text-sm',
      lg: 'h-12 px-7 text-base',
    };

    return (
      <button
        ref={ref}
        className={cn(base, variants[variant], sizes[size], fullWidth && 'w-full', className)}
        disabled={disabled || loading}
        {...props}
      >
        {loading && (
          <svg className="animate-spin h-4 w-4" viewBox="0 0 24 24" fill="none">
            <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="3" />
            <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
          </svg>
        )}
        {children}
      </button>
    );
  }
);

Button.displayName = 'Button';
export { Button };
export type { ButtonProps };
