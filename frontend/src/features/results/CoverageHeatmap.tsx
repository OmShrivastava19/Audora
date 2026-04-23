import { useState } from 'react';
import { motion } from 'framer-motion';
import { Badge } from '@/components/ui/Badge';
import { MetricCard } from '@/components/ui/Misc';
import { formatTimestamp, getCoverageColor, cn } from '@/lib/utils';
import type { SyllabusCoverage, CoverageModule } from '@/types';
import { CheckCircle2, AlertCircle, XCircle, ChevronDown } from 'lucide-react';

interface CoverageHeatmapProps {
  coverage: SyllabusCoverage;
}

export function CoverageHeatmap({ coverage }: CoverageHeatmapProps) {
  if (coverage.error) {
    return (
      <div className="text-center py-12 text-muted">
        <p className="text-lg mb-2">📊</p>
        <p>{coverage.error}</p>
      </div>
    );
  }

  if (!coverage.modules.length) {
    return (
      <div className="text-center py-12 text-muted">
        <p className="text-lg mb-2">📊</p>
        <p>No syllabus modules were detected to score coverage.</p>
      </div>
    );
  }

  const { summary } = coverage;

  return (
    <div className="space-y-6">
      {/* Summary metrics */}
      <div className="grid grid-cols-3 gap-3">
        <MetricCard
          label="Covered"
          value={summary.covered}
          icon={<CheckCircle2 className="w-5 h-5 text-accent" />}
        />
        <MetricCard
          label="Partial"
          value={summary.partial}
          icon={<AlertCircle className="w-5 h-5 text-accent3" />}
        />
        <MetricCard
          label="Missing"
          value={summary.missing}
          icon={<XCircle className="w-5 h-5 text-accent2" />}
        />
      </div>

      {/* Module rows */}
      <div className="rounded-xl border border-border bg-surface overflow-hidden">
        {/* Header */}
        <div className="grid grid-cols-[2fr_1fr_0.8fr_0.6fr] gap-3 px-5 py-3 border-b border-border text-[0.65rem] font-mono uppercase tracking-widest text-muted">
          <span>Module</span>
          <span>Coverage</span>
          <span>Status</span>
          <span>Evidence</span>
        </div>

        {/* Rows */}
        {coverage.modules.map((mod, i) => (
          <CoverageRow key={i} module={mod} index={i} />
        ))}
      </div>
    </div>
  );
}

function CoverageRow({ module: mod, index }: { module: CoverageModule; index: number }) {
  const [expanded, setExpanded] = useState(false);
  const color = getCoverageColor(mod.coverage_percent);

  return (
    <motion.div
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      transition={{ delay: index * 0.04 }}
    >
      <button
        onClick={() => setExpanded(!expanded)}
        className="w-full grid grid-cols-[2fr_1fr_0.8fr_0.6fr] gap-3 px-5 py-3 border-b border-border hover:bg-surface-hover transition-colors text-left items-center"
      >
        <span className="text-sm text-text truncate">{mod.module_name}</span>
        <div className="space-y-1">
          <div className="h-2 rounded-full bg-bg-elevated border border-border/50 overflow-hidden">
            <motion.div
              className="h-full rounded-full"
              style={{ background: color }}
              initial={{ width: 0 }}
              animate={{ width: `${mod.coverage_percent}%` }}
              transition={{ duration: 0.8, delay: index * 0.05 }}
            />
          </div>
          <span className="text-[0.65rem] text-muted font-mono">{mod.coverage_percent.toFixed(1)}%</span>
        </div>
        <Badge
          variant={
            mod.status === 'Covered' ? 'accent' : mod.status === 'Partial' ? 'warning' : 'danger'
          }
        >
          {mod.status}
        </Badge>
        <div className="flex items-center gap-1">
          <span className="text-sm text-text-secondary">{mod.evidence_count}</span>
          <ChevronDown
            className={cn('w-3.5 h-3.5 text-muted transition-transform', expanded && 'rotate-180')}
          />
        </div>
      </button>

      {expanded && (
        <motion.div
          initial={{ height: 0, opacity: 0 }}
          animate={{ height: 'auto', opacity: 1 }}
          exit={{ height: 0, opacity: 0 }}
          className="px-5 py-3 bg-bg-elevated border-b border-border"
        >
          {mod.top_evidence_snippets.length === 0 ? (
            <p className="text-xs text-muted">No strong transcript evidence found for this module.</p>
          ) : (
            <div className="space-y-2">
              {mod.top_evidence_snippets.map((snip, si) => (
                <div key={si} className="text-xs">
                  <p className="font-mono text-muted mb-0.5">
                    <span className="font-semibold">{formatTimestamp(snip.start_sec)}</span>
                    {' – '}
                    {formatTimestamp(snip.end_sec)}
                    {' · '}
                    <span className="text-accent">{snip.score.toFixed(2)}</span>
                  </p>
                  <p className="text-text-secondary leading-relaxed">{snip.text}</p>
                </div>
              ))}
            </div>
          )}
        </motion.div>
      )}
    </motion.div>
  );
}
