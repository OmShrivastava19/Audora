import { useAppStore } from '@/store/app';
import { formatTimestamp, cn } from '@/lib/utils';
import type { TranscriptSegment } from '@/types';

interface TranscriptPanelProps {
  segments: TranscriptSegment[];
  transcriptText: string;
}

export function TranscriptPanel({ segments, transcriptText }: TranscriptPanelProps) {
  const { selectedSegmentId, setSelectedSegment } = useAppStore();

  if (!segments.length && !transcriptText) {
    return (
      <div className="text-center py-12 text-muted">
        <p className="text-lg mb-2">🎙️</p>
        <p>No transcript available.</p>
      </div>
    );
  }

  if (!segments.length) {
    return (
      <div className="rounded-xl border border-border bg-surface p-5">
        <pre className="font-mono text-xs text-muted leading-[1.8] whitespace-pre-wrap">
          {transcriptText.slice(0, 4000)}
          {transcriptText.length > 4000 && '...'}
        </pre>
      </div>
    );
  }

  return (
    <div className="space-y-1.5 max-h-[600px] overflow-y-auto pr-1">
      {segments.map((seg) => {
        const isActive = selectedSegmentId === seg.segment_id;
        return (
          <button
            key={seg.segment_id}
            onClick={() => setSelectedSegment(seg.segment_id, seg.start_sec)}
            className={cn(
              'w-full text-left rounded-lg border p-3 transition-all duration-200',
              isActive
                ? 'border-accent bg-accent/[0.06] shadow-sm shadow-accent/10'
                : 'border-border hover:border-border-focus hover:bg-surface-hover'
            )}
          >
            <div className="flex items-center gap-2 mb-1">
              <span
                className={cn(
                  'font-mono text-[0.65rem] font-semibold',
                  isActive ? 'text-accent' : 'text-muted'
                )}
              >
                {seg.segment_id}
              </span>
              <span className="text-[0.6rem] text-muted font-mono">
                {formatTimestamp(seg.start_sec)} – {formatTimestamp(seg.end_sec)}
              </span>
            </div>
            <p className={cn('text-sm leading-relaxed', isActive ? 'text-text' : 'text-text-secondary')}>
              {seg.text}
            </p>
          </button>
        );
      })}
    </div>
  );
}
