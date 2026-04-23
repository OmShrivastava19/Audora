import { motion } from 'framer-motion';
import { Badge } from '@/components/ui/Badge';
import { Card } from '@/components/ui/Card';
import { Button } from '@/components/ui/Button';
import { useAppStore } from '@/store/app';
import { formatTimestamp, getConfidenceColor } from '@/lib/utils';
import type { StructuredNote, TranscriptSegment } from '@/types';

interface NotesPanelProps {
  notes: StructuredNote[];
  segments: TranscriptSegment[];
}

export function NotesPanel({ notes, segments }: NotesPanelProps) {
  const { setSelectedSegment } = useAppStore();

  if (!notes.length) {
    return (
      <div className="text-center py-12 text-muted">
        <p className="text-lg mb-2">📝</p>
        <p>No structured notes were returned.</p>
      </div>
    );
  }

  return (
    <div className="space-y-4">
      {notes.map((note, idx) => (
        <motion.div
          key={idx}
          initial={{ opacity: 0, y: 12 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: idx * 0.05 }}
        >
          <Card>
            {/* Module header */}
            <div className="flex items-center flex-wrap gap-2 mb-3">
              <span className="font-mono text-[0.65rem] tracking-[3px] uppercase text-accent">
                {note.module}
              </span>
              <Badge
                variant={
                  note.confidence_label === 'HIGH'
                    ? 'accent'
                    : note.confidence_label === 'MEDIUM'
                    ? 'warning'
                    : 'danger'
                }
              >
                Confidence {note.confidence_label}
              </Badge>
              <Badge variant="muted">{note.confidence_score.toFixed(2)}</Badge>
            </div>

            {/* Note content */}
            <div
              className="text-sm text-text-secondary leading-[1.85] prose-sm"
              dangerouslySetInnerHTML={{
                __html: note.content
                  .replace(/\*\*([^*]+)\*\*/g, '<strong class="text-text font-semibold">$1</strong>')
                  .replace(/\n/g, '<br/>'),
              }}
            />

            {/* Confidence reason */}
            {note.confidence_reason && (
              <p className="text-xs text-muted mt-3 leading-relaxed">
                {note.confidence_reason}
              </p>
            )}

            {/* Source references */}
            {note.references.length > 0 && (
              <div className="mt-4 pt-3 border-t border-border">
                <p className="text-[0.65rem] font-mono uppercase tracking-widest text-muted mb-2">
                  Sources
                </p>
                <div className="flex flex-wrap gap-2">
                  {note.references.map((ref, refIdx) => (
                    <button
                      key={refIdx}
                      onClick={() => setSelectedSegment(ref.segment_id, ref.start_sec)}
                      className="group flex items-center gap-1.5 px-2.5 py-1.5 rounded-lg bg-bg-elevated border border-border text-xs text-text-secondary hover:border-accent hover:text-accent transition-all"
                      title={ref.quote}
                    >
                      <span className="font-mono text-[0.65rem]">
                        {formatTimestamp(ref.start_sec)}–{formatTimestamp(ref.end_sec)}
                      </span>
                      <span className="text-muted">·</span>
                      <span className="font-mono text-[0.6rem] text-muted">{ref.segment_id}</span>
                      {ref.confidence !== undefined && (
                        <>
                          <span className="text-muted">·</span>
                          <span className="text-[0.6rem] text-muted">{ref.confidence.toFixed(2)}</span>
                        </>
                      )}
                    </button>
                  ))}
                </div>
              </div>
            )}
          </Card>
        </motion.div>
      ))}
    </div>
  );
}
