import { motion } from 'framer-motion';
import { Card } from '@/components/ui/Card';
import { Badge } from '@/components/ui/Badge';
import type { ExamHint } from '@/types';

interface ExamRadarPanelProps {
  hints: ExamHint[];
}

export function ExamRadarPanel({ hints }: ExamRadarPanelProps) {
  if (!hints.length) {
    return (
      <div className="rounded-xl border border-border bg-surface p-12 text-center">
        <p className="text-4xl mb-3">✅</p>
        <p className="text-muted">No exam hints detected in this lecture.</p>
      </div>
    );
  }

  return (
    <div className="space-y-3">
      {hints.map((hint, idx) => (
        <motion.div
          key={idx}
          initial={{ opacity: 0, x: -10 }}
          animate={{ opacity: 1, x: 0 }}
          transition={{ delay: idx * 0.06 }}
        >
          <Card variant="danger">
            <div className="flex items-center gap-2 mb-2">
              <Badge variant={hint.urgency === 'HIGH' ? 'danger' : 'warning'}>
                {hint.urgency}
              </Badge>
              <Badge variant="muted">{hint.module}</Badge>
            </div>
            <p className="text-sm font-semibold text-text mb-1">{hint.hint}</p>
            <p className="text-xs text-muted leading-relaxed">{hint.reason}</p>
          </Card>
        </motion.div>
      ))}
    </div>
  );
}
