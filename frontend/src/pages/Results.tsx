import { useEffect, useState } from 'react';
import { useSearchParams } from 'react-router-dom';
import { motion } from 'framer-motion';
import {
  Cpu,
  Globe,
  VolumeX,
  AlertTriangle,
  BookOpen,
  Target,
  Mic,
  BarChart3,
  Lightbulb,
  Download,
} from 'lucide-react';
import { useAppStore } from '@/store/app';
import { apiClient } from '@/api/client';
import { mockGenerationResult } from '@/api/mock-data';
import { Button } from '@/components/ui/Button';
import { EmptyState, ErrorBanner, MetricCard, SectionLabel } from '@/components/ui/Misc';
import { Tabs } from '@/components/ui/Tabs';
import { NotesPanel } from '@/features/results/NotesPanel';
import { ExamRadarPanel } from '@/features/results/ExamRadar';
import { TranscriptPanel } from '@/features/results/TranscriptPanel';
import { CoverageHeatmap } from '@/features/results/CoverageHeatmap';
import { FlashcardsPanel } from '@/features/results/FlashcardsPanel';
import { QuizPanel } from '@/features/results/QuizPanel';
import { DownloadsSection } from '@/features/results/DownloadsSection';
import type { GenerationResult } from '@/types';

const DEMO_MODE = import.meta.env.MODE === 'demo' || false;

export function ResultsPage() {
  const { currentResult, setCurrentResult } = useAppStore();
  const [searchParams] = useSearchParams();
  const resultId = searchParams.get('id');
  const [result, setResult] = useState<GenerationResult | null>(
    resultId && currentResult?.id !== resultId ? null : currentResult
  );
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  useEffect(() => {
    if (!resultId) {
      if (currentResult) {
        setResult(currentResult);
        setError('');
        return;
      }

      if (DEMO_MODE) {
        setResult(mockGenerationResult);
        setError('');
        return;
      }

      setResult(null);
      setError('No result selected. Open a lecture from History or generate a new one.');
      return;
    }

    let cancelled = false;
    setLoading(true);
    setError('');

    if (currentResult?.id !== resultId) {
      setResult(null);
    }

    apiClient
      .getGenerationResult(resultId)
      .then((fetched) => {
        if (cancelled) return;
        setResult(fetched);
        setCurrentResult(fetched);
      })
      .catch((err: any) => {
        if (cancelled) return;
        if (DEMO_MODE) {
          setResult({ ...mockGenerationResult, id: resultId });
          setError('');
          return;
        }

        setResult(null);
        setError(err?.message || 'Could not load the requested result.');
      })
      .finally(() => {
        if (!cancelled) setLoading(false);
      });

    return () => {
      cancelled = true;
    };
  }, [resultId, currentResult, setCurrentResult]);

  const displayResult = result;

  const stagger = {
    hidden: {},
    visible: { transition: { staggerChildren: 0.06 } },
  };
  const fadeUp = {
    hidden: { opacity: 0, y: 16 },
    visible: { opacity: 1, y: 0, transition: { duration: 0.4 } },
  };

  if (loading && !displayResult) {
    return (
      <div className="space-y-6">
        <div className="rounded-2xl border border-border bg-surface p-8">
          <p className="text-sm text-muted">Loading result...</p>
        </div>
      </div>
    );
  }

  if (error && !displayResult) {
    return (
      <div className="space-y-6">
        <ErrorBanner message={error} />
        <EmptyState
          icon={<BookOpen className="w-12 h-12" />}
          title="Result unavailable"
          description="The selected lecture result could not be loaded. Try opening it again from History or generate a new lecture."
          action={
            <Button variant="secondary" onClick={() => window.history.back()}>
              Go back
            </Button>
          }
        />
      </div>
    );
  }

  if (!displayResult) {
    return (
      <EmptyState
        icon={<BookOpen className="w-12 h-12" />}
        title="No result selected"
        description="Open a lecture from History or generate a new lecture to view its study workspace."
      />
    );
  }

  return (
    <motion.div variants={stagger} initial="hidden" animate="visible" className="space-y-8">
      {error && <ErrorBanner message={error} />}

      {/* Title */}
      <motion.div variants={fadeUp}>
        <h1 className="font-display font-extrabold text-2xl lg:text-3xl text-text">
          {displayResult.title}
        </h1>
        <p className="text-sm text-muted mt-1 font-mono">{displayResult.lecture_filename}</p>
      </motion.div>

      {/* Metrics */}
      <motion.div variants={fadeUp} className="grid grid-cols-2 lg:grid-cols-4 gap-3">
        <MetricCard
          label="Provider"
          value={displayResult.provider === 'groq' ? 'Groq' : 'OpenAI'}
          icon={<Cpu className="w-5 h-5 text-accent" />}
        />
        <MetricCard
          label="Language"
          value={displayResult.language === 'en' ? 'English' : displayResult.language}
          icon={<Globe className="w-5 h-5 text-accent" />}
        />
        <MetricCard
          label="Noise Removed"
          value={displayResult.filtered_count}
          icon={<VolumeX className="w-5 h-5 text-accent" />}
        />
        <MetricCard
          label="Exam Hints"
          value={displayResult.exam_radar.length}
          icon={<AlertTriangle className="w-5 h-5 text-accent" />}
        />
      </motion.div>

      {/* Summary */}
      {displayResult.summary && (
        <motion.div
          variants={fadeUp}
          className="rounded-xl bg-surface border-l-4 border-l-accent border border-border p-5"
        >
          <SectionLabel>Executive Summary</SectionLabel>
          <p className="text-sm text-text-secondary leading-relaxed">{displayResult.summary}</p>
        </motion.div>
      )}

      {/* Main workspace tabs */}
      <motion.div variants={fadeUp}>
        <Tabs
          items={[
            {
              id: 'notes',
              label: 'Study Notes',
              icon: <BookOpen className="w-4 h-4" />,
              content: <NotesPanel notes={displayResult.notes} segments={displayResult.transcript_segments} />,
            },
            {
              id: 'exam',
              label: 'Exam Radar',
              icon: <Target className="w-4 h-4" />,
              content: <ExamRadarPanel hints={displayResult.exam_radar} />,
            },
            {
              id: 'transcript',
              label: 'Transcript',
              icon: <Mic className="w-4 h-4" />,
              content: (
                <TranscriptPanel
                  segments={displayResult.transcript_segments}
                  transcriptText={displayResult.transcript_text}
                />
              ),
            },
            {
              id: 'coverage',
              label: 'Coverage',
              icon: <BarChart3 className="w-4 h-4" />,
              content: <CoverageHeatmap coverage={displayResult.syllabus_coverage} />,
            },
            {
              id: 'practice',
              label: 'Study Practice',
              icon: <Lightbulb className="w-4 h-4" />,
              content: (
                <Tabs
                  items={[
                    {
                      id: 'flashcards',
                      label: 'Flashcards',
                      content: <FlashcardsPanel flashcards={displayResult.practice.flashcards} />,
                    },
                    {
                      id: 'quiz',
                      label: 'Quiz',
                      content: <QuizPanel quizItems={displayResult.practice.quiz} />,
                    },
                  ]}
                />
              ),
            },
            {
              id: 'downloads',
              label: 'Downloads',
              icon: <Download className="w-4 h-4" />,
              content: <DownloadsSection result={displayResult} />,
            },
          ]}
        />
      </motion.div>
    </motion.div>
  );
}
