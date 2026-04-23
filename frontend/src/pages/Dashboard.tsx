import { useState, useCallback } from 'react';
import { useNavigate } from 'react-router-dom';
import { motion } from 'framer-motion';
import { Sparkles, GraduationCap, KeyRound } from 'lucide-react';
import { Button } from '@/components/ui/Button';
import { Input } from '@/components/ui/Input';
import { SyllabusDropZone, LectureDropZone } from '@/components/ui/DropZone';
import { PipelineProgress } from '@/components/ui/Progress';
import { ErrorBanner, SectionLabel } from '@/components/ui/Misc';
import { useAppStore } from '@/store/app';
import { apiClient } from '@/api/client';
import type { PipelineStage } from '@/types';

const INITIAL_STAGES: PipelineStage[] = [
  { id: 'syllabus', label: 'Processing syllabus', status: 'pending' },
  { id: 'transcribe', label: 'Transcribing lecture', status: 'pending' },
  { id: 'context', label: 'Retrieving syllabus context', status: 'pending' },
  { id: 'notes', label: 'Generating structured notes', status: 'pending' },
  { id: 'coverage', label: 'Computing syllabus coverage', status: 'pending' },
  { id: 'practice', label: 'Generating study practice', status: 'pending' },
  { id: 'audio', label: 'Generating audio notes', status: 'pending' },
  { id: 'done', label: 'Complete', status: 'pending' },
];

export function DashboardPage() {
  const { provider, language, setCurrentResult } = useAppStore();
  const navigate = useNavigate();

  const [syllabusFile, setSyllabusFile] = useState<File | null>(null);
  const [lectureFile, setLectureFile] = useState<File | null>(null);
  const [apiKey, setApiKey] = useState('');
  const [generating, setGenerating] = useState(false);
  const [stages, setStages] = useState<PipelineStage[]>(INITIAL_STAGES);
  const [error, setError] = useState('');


  const updateStage = useCallback((stageLabel: string, progress: number) => {
    setStages((prev) => {
      const stageMap: Record<string, string> = {
        'Processing syllabus...': 'syllabus',
        'Transcribing lecture...': 'transcribe',
        'Retrieving syllabus context...': 'context',
        'Generating structured notes...': 'notes',
        'Computing coverage...': 'coverage',
        'Generating study practice...': 'practice',
        'Generating audio notes...': 'audio',
        'Done!': 'done',
      };
      const activeId = stageMap[stageLabel] || '';
      return prev.map((s) => {
        if (s.id === activeId) return { ...s, status: 'active' as const };
        const sIndex = prev.findIndex((x) => x.id === s.id);
        const activeIndex = prev.findIndex((x) => x.id === activeId);
        if (sIndex < activeIndex) return { ...s, status: 'done' as const };
        return s;
      });
    });
  }, []);

  const handleGenerate = async () => {
    if (!lectureFile) return;
    setError('');
    setGenerating(true);
    setStages(INITIAL_STAGES);
    try {
      const result = await apiClient.generateNotes(
        lectureFile,
        syllabusFile,
        provider,
        language,
        apiKey.trim(),
        updateStage
      );
      setCurrentResult(result);
      setStages((prev) => prev.map((s) => ({ ...s, status: 'done' as const })));
      setTimeout(() => navigate(`/results?id=${encodeURIComponent(result.id)}`), 400);
    } catch (err: any) {
      setError(err.message || 'Generation failed. Please try again.');
      setStages((prev) =>
        prev.map((s) => (s.status === 'active' ? { ...s, status: 'error' as const } : s))
      );
    } finally {
      setGenerating(false);
    }
  };

  const canGenerate = !!lectureFile && !generating;

  return (
    <motion.div
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      transition={{ duration: 0.4 }}
      className="space-y-8"
    >
      {/* Header */}
      <div className="flex items-center gap-3">
        <div className="w-10 h-10 rounded-xl bg-accent-muted flex items-center justify-center">
          <GraduationCap className="w-5 h-5 text-accent" />
        </div>
        <div>
          <h1 className="font-display font-extrabold text-2xl text-text">Generate Notes</h1>
          <p className="text-sm text-muted">Upload your lecture and get AI-powered study materials</p>
        </div>
      </div>

      {error && <ErrorBanner message={error} onDismiss={() => setError('')} />}

      {/* API Key */}
      <motion.div
        initial={{ opacity: 0, y: 10 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.1 }}
      >
        <Input
          label={`${provider === 'groq' ? 'Groq' : 'OpenAI'} API Key`}
          type="password"
          placeholder={provider === 'groq' ? 'gsk_...' : 'sk-...'}
          value={apiKey}
          onChange={(e) => setApiKey(e.target.value)}
          icon={<KeyRound className="w-4 h-4" />}
        />
        <p className="text-xs text-muted mt-1.5">
          {provider === 'groq'
            ? 'Get a free key from console.groq.com'
            : 'Get a paid key from platform.openai.com'}
        </p>
      </motion.div>

      {/* Upload area */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        <motion.div
          initial={{ opacity: 0, y: 10 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.2 }}
        >
          <SectionLabel>Course Syllabus (Optional)</SectionLabel>
          <SyllabusDropZone
            onFileSelect={setSyllabusFile}
            selectedFile={syllabusFile}
            onClear={() => setSyllabusFile(null)}
          />
        </motion.div>

        <motion.div
          initial={{ opacity: 0, y: 10 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.3 }}
        >
          <SectionLabel>Lecture Recording</SectionLabel>
          <LectureDropZone
            onFileSelect={setLectureFile}
            selectedFile={lectureFile}
            onClear={() => setLectureFile(null)}
          />
        </motion.div>
      </div>

      {/* Generate button */}
      <motion.div
        initial={{ opacity: 0, y: 10 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.4 }}
        className="flex justify-center"
      >
        <Button
          size="lg"
          onClick={handleGenerate}
          disabled={!canGenerate}
          loading={generating}
          className="px-12 text-base"
        >
          <Sparkles className="w-5 h-5" />
          Generate Notes
        </Button>
      </motion.div>

      {/* Pipeline tracker */}
      {generating && (
        <motion.div
          initial={{ opacity: 0, height: 0 }}
          animate={{ opacity: 1, height: 'auto' }}
          className="rounded-2xl border border-border bg-surface p-6"
        >
          <SectionLabel>Pipeline Progress</SectionLabel>
          <PipelineProgress stages={stages} />
        </motion.div>
      )}

      {/* Empty state placeholder */}
      {!generating && !error && (
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          transition={{ delay: 0.5 }}
          className="rounded-2xl border border-border bg-surface p-12 text-center"
        >
          <p className="text-4xl mb-3">🎓</p>
          <h3 className="font-display font-bold text-xl text-text mb-2">
            Automated Lecture Synthesis
          </h3>
          <p className="text-sm text-muted max-w-lg mx-auto leading-relaxed">
            Choose your provider in the sidebar, add your API key, upload a lecture recording,
            and generate syllabus-aware notes with exam hints, coverage analysis, and study practice.
          </p>
        </motion.div>
      )}
    </motion.div>
  );
}
