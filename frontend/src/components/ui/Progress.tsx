import { cn } from '@/lib/utils';
import { motion } from 'framer-motion';

interface ProgressBarProps {
  value: number;
  max?: number;
  label?: string;
  sublabel?: string;
  color?: string;
  className?: string;
  showPercent?: boolean;
}

export function ProgressBar({
  value,
  max = 100,
  label,
  sublabel,
  className,
  showPercent = true,
}: ProgressBarProps) {
  const percent = Math.min(100, Math.max(0, (value / max) * 100));

  return (
    <div className={cn('space-y-2', className)}>
      {(label || showPercent) && (
        <div className="flex items-center justify-between text-xs">
          <span className="text-text-secondary font-medium">{label}</span>
          {showPercent && <span className="font-mono text-muted">{Math.round(percent)}%</span>}
        </div>
      )}
      <div className="h-2 rounded-full bg-surface-hover overflow-hidden border border-border/50">
        <motion.div
          className="h-full rounded-full"
          style={{
            background: 'linear-gradient(90deg, #4fffb0, #00c4ff)',
          }}
          initial={{ width: 0 }}
          animate={{ width: `${percent}%` }}
          transition={{ duration: 0.5, ease: 'easeOut' }}
        />
      </div>
      {sublabel && <p className="text-xs text-muted">{sublabel}</p>}
    </div>
  );
}

interface PipelineProgressProps {
  stages: Array<{ id: string; label: string; status: 'pending' | 'active' | 'done' | 'error' }>;
  className?: string;
}

export function PipelineProgress({ stages, className }: PipelineProgressProps) {
  return (
    <div className={cn('space-y-1', className)}>
      {stages.map((stage, i) => (
        <motion.div
          key={stage.id}
          initial={{ opacity: 0, x: -10 }}
          animate={{ opacity: 1, x: 0 }}
          transition={{ delay: i * 0.05 }}
          className={cn(
            'flex items-center gap-3 py-2 px-3 rounded-lg text-sm transition-colors',
            stage.status === 'active' && 'bg-accent/[0.06] text-accent',
            stage.status === 'done' && 'text-muted',
            stage.status === 'pending' && 'text-muted/50',
            stage.status === 'error' && 'text-accent2'
          )}
        >
          <div
            className={cn(
              'w-5 h-5 rounded-full border-2 flex items-center justify-center flex-shrink-0 transition-all',
              stage.status === 'active' && 'border-accent animate-pulse-glow',
              stage.status === 'done' && 'border-accent bg-accent',
              stage.status === 'pending' && 'border-border',
              stage.status === 'error' && 'border-accent2 bg-accent2'
            )}
          >
            {stage.status === 'done' && (
              <svg className="w-3 h-3 text-bg" fill="currentColor" viewBox="0 0 20 20">
                <path
                  fillRule="evenodd"
                  d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z"
                  clipRule="evenodd"
                />
              </svg>
            )}
            {stage.status === 'active' && (
              <div className="w-2 h-2 rounded-full bg-accent" />
            )}
            {stage.status === 'error' && (
              <svg className="w-3 h-3 text-bg" fill="currentColor" viewBox="0 0 20 20">
                <path
                  fillRule="evenodd"
                  d="M4.293 4.293a1 1 0 011.414 0L10 8.586l4.293-4.293a1 1 0 111.414 1.414L11.414 10l4.293 4.293a1 1 0 01-1.414 1.414L10 11.414l-4.293 4.293a1 1 0 01-1.414-1.414L8.586 10 4.293 5.707a1 1 0 010-1.414z"
                  clipRule="evenodd"
                />
              </svg>
            )}
          </div>
          <span className="font-medium">{stage.label}</span>
        </motion.div>
      ))}
    </div>
  );
}
