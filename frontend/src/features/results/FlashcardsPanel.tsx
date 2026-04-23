import { useState, useCallback } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { Shuffle, RotateCcw, ChevronLeft, ChevronRight, Check, X, Eye, EyeOff } from 'lucide-react';
import { Button } from '@/components/ui/Button';
import { Card } from '@/components/ui/Card';
import { Badge } from '@/components/ui/Badge';
import { MetricCard } from '@/components/ui/Misc';
import type { PracticeFlashcard } from '@/types';

interface FlashcardsPanelProps {
  flashcards: PracticeFlashcard[];
}

export function FlashcardsPanel({ flashcards }: FlashcardsPanelProps) {
  const [order, setOrder] = useState<number[]>(() => flashcards.map((_, i) => i));
  const [currentIndex, setCurrentIndex] = useState(0);
  const [revealed, setRevealed] = useState<Record<number, boolean>>({});
  const [marks, setMarks] = useState<Record<number, 'known' | 'review'>>({});

  const knownCount = Object.values(marks).filter((v) => v === 'known').length;
  const reviewCount = Object.values(marks).filter((v) => v === 'review').length;

  const currentId = order[currentIndex];
  const card = flashcards[currentId];
  const isRevealed = revealed[currentId] || false;

  const handleShuffle = useCallback(() => {
    const shuffled = [...order].sort(() => Math.random() - 0.5);
    setOrder(shuffled);
    setCurrentIndex(0);
    setRevealed({});
  }, [order]);

  const handleReset = useCallback(() => {
    setMarks({});
    setRevealed({});
  }, []);

  if (!flashcards.length) {
    return (
      <div className="text-center py-12 text-muted">
        <p className="text-lg mb-2">🃏</p>
        <p>No flashcards available.</p>
      </div>
    );
  }

  return (
    <div className="space-y-5">
      {/* Stats */}
      <div className="grid grid-cols-3 gap-3">
        <MetricCard label="Total" value={flashcards.length} />
        <MetricCard label="Known" value={knownCount} />
        <MetricCard label="Review" value={reviewCount} />
      </div>

      {/* Controls */}
      <div className="flex items-center gap-2">
        <Button variant="secondary" size="sm" onClick={handleShuffle}>
          <Shuffle className="w-3.5 h-3.5" /> Shuffle
        </Button>
        <Button variant="secondary" size="sm" onClick={handleReset}>
          <RotateCcw className="w-3.5 h-3.5" /> Reset
        </Button>
        <span className="ml-auto text-xs text-muted font-mono">
          Card {currentIndex + 1} of {flashcards.length}
        </span>
      </div>

      {/* Card */}
      <AnimatePresence mode="wait">
        <motion.div
          key={currentId}
          initial={{ opacity: 0, x: 30 }}
          animate={{ opacity: 1, x: 0 }}
          exit={{ opacity: 0, x: -30 }}
          transition={{ duration: 0.25 }}
        >
          <Card className="min-h-[200px]">
            <div className="flex items-center gap-2 mb-4">
              <Badge variant="muted">{card.module}</Badge>
              <Badge
                variant={
                  card.difficulty === 'easy'
                    ? 'accent'
                    : card.difficulty === 'hard'
                    ? 'danger'
                    : 'warning'
                }
              >
                {card.difficulty}
              </Badge>
              {marks[currentId] && (
                <Badge variant={marks[currentId] === 'known' ? 'accent' : 'warning'}>
                  {marks[currentId]}
                </Badge>
              )}
            </div>

            <p className="text-base font-semibold text-text leading-relaxed">{card.question}</p>

            {/* Reveal toggle */}
            <div className="mt-4">
              <Button
                variant="outline"
                size="sm"
                fullWidth
                onClick={() =>
                  setRevealed((prev) => ({ ...prev, [currentId]: !prev[currentId] }))
                }
              >
                {isRevealed ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
                {isRevealed ? 'Hide Answer' : 'Reveal Answer'}
              </Button>
            </div>

            <AnimatePresence>
              {isRevealed && (
                <motion.div
                  initial={{ opacity: 0, height: 0 }}
                  animate={{ opacity: 1, height: 'auto' }}
                  exit={{ opacity: 0, height: 0 }}
                  className="mt-4 pt-4 border-t border-border"
                >
                  <p className="text-[0.65rem] font-mono uppercase tracking-widest text-accent mb-1">
                    Answer
                  </p>
                  <p className="text-sm text-text-secondary leading-relaxed">{card.answer}</p>
                </motion.div>
              )}
            </AnimatePresence>
          </Card>
        </motion.div>
      </AnimatePresence>

      {/* Mark buttons */}
      <div className="grid grid-cols-2 gap-3">
        <Button
          variant="secondary"
          onClick={() => setMarks((prev) => ({ ...prev, [currentId]: 'known' }))}
        >
          <Check className="w-4 h-4 text-accent" /> Mark as Known
        </Button>
        <Button
          variant="secondary"
          onClick={() => setMarks((prev) => ({ ...prev, [currentId]: 'review' }))}
        >
          <X className="w-4 h-4 text-accent3" /> Mark for Review
        </Button>
      </div>

      {/* Navigation */}
      <div className="grid grid-cols-2 gap-3">
        <Button
          variant="ghost"
          disabled={currentIndex <= 0}
          onClick={() => setCurrentIndex((i) => Math.max(0, i - 1))}
        >
          <ChevronLeft className="w-4 h-4" /> Previous
        </Button>
        <Button
          variant="ghost"
          disabled={currentIndex >= order.length - 1}
          onClick={() => setCurrentIndex((i) => Math.min(order.length - 1, i + 1))}
        >
          Next <ChevronRight className="w-4 h-4" />
        </Button>
      </div>
    </div>
  );
}
