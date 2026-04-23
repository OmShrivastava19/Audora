import { FileDown, FileText, FileJson, FileAudio, ScrollText } from 'lucide-react';
import { Button } from '@/components/ui/Button';
import { SectionLabel } from '@/components/ui/Misc';
import { slugify, formatTimestamp } from '@/lib/utils';
import type { GenerationResult } from '@/types';

interface DownloadsSectionProps {
  result: GenerationResult;
}

export function DownloadsSection({ result }: DownloadsSectionProps) {
  const safeTitle = slugify(result.title);

  // Build markdown notes
  const buildMarkdown = (): string => {
    let md = `# ${result.title}\n\n**Summary:** ${result.summary}\n\n`;
    for (const n of result.notes) {
      md += `## ${n.module}\n\n`;
      md += `**Confidence:** ${n.confidence_label} (${n.confidence_score.toFixed(2)})\n\n`;
      md += `**Reason:** ${n.confidence_reason}\n\n`;
      md += `${n.content}\n\n`;
      if (n.references.length) {
        md += '**Sources:**\n';
        for (const ref of n.references) {
          md += `- ${formatTimestamp(ref.start_sec)} to ${formatTimestamp(ref.end_sec)} (${ref.segment_id})`;
          if (ref.quote) md += `: ${ref.quote}`;
          md += '\n';
        }
        md += '\n';
      }
    }
    if (result.exam_radar.length) {
      md += '## Exam Radar\n\n';
      for (const h of result.exam_radar) {
        md += `- **[${h.urgency}]** ${h.hint} *(Module: ${h.module})*\n`;
      }
    }
    return md;
  };

  const download = (content: string, filename: string, mime: string) => {
    const blob = new Blob([content], { type: mime });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = filename;
    a.click();
    URL.revokeObjectURL(url);
  };

  const downloads = [
    {
      label: 'Notes (Markdown)',
      icon: <FileText className="w-4 h-4" />,
      action: () => download(buildMarkdown(), `audora_${safeTitle}.md`, 'text/markdown'),
    },
    {
      label: 'Notes (JSON)',
      icon: <FileJson className="w-4 h-4" />,
      action: () =>
        download(
          JSON.stringify(result, null, 2),
          `audora_${safeTitle}.json`,
          'application/json'
        ),
    },
    {
      label: 'Transcript (TXT)',
      icon: <ScrollText className="w-4 h-4" />,
      action: () =>
        download(result.transcript_text, `transcript_${safeTitle}.txt`, 'text/plain'),
    },
    {
      label: 'Flashcards (JSON)',
      icon: <FileJson className="w-4 h-4" />,
      action: () =>
        download(
          JSON.stringify(result.practice.flashcards, null, 2),
          `flashcards_${safeTitle}.json`,
          'application/json'
        ),
    },
    {
      label: 'Quiz (JSON)',
      icon: <FileJson className="w-4 h-4" />,
      action: () =>
        download(
          JSON.stringify(result.practice.quiz, null, 2),
          `quiz_${safeTitle}.json`,
          'application/json'
        ),
    },
    {
      label: 'Revision Set (TXT)',
      icon: <FileText className="w-4 h-4" />,
      action: () => {
        const lines = result.practice.flashcards.map(
          (c, i) => `${i + 1}. Q: ${c.question}\nA: ${c.answer}`
        );
        download(lines.join('\n\n'), `revision_${safeTitle}.txt`, 'text/plain');
      },
    },
  ];

  return (
    <div className="space-y-4">
      <SectionLabel>Export Files</SectionLabel>
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-3">
        {downloads.map((dl) => (
          <Button key={dl.label} variant="secondary" onClick={dl.action} className="justify-start">
            {dl.icon}
            {dl.label}
            <FileDown className="w-3 h-3 ml-auto text-muted" />
          </Button>
        ))}
      </div>
    </div>
  );
}
