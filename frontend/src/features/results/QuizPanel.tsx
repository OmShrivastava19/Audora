import { useState, useMemo } from 'react';
import { motion } from 'framer-motion';
import { RotateCcw, Send, Timer } from 'lucide-react';
import { Button } from '@/components/ui/Button';
import { Card } from '@/components/ui/Card';
import { Badge } from '@/components/ui/Badge';
import { MetricCard } from '@/components/ui/Misc';
import type { PracticeQuizItem } from '@/types';

interface QuizPanelProps {
  quizItems: PracticeQuizItem[];
}

interface QuizResult {
  score: number;
  total: number;
  accuracy: number;
  wrong: Array<{
    question: PracticeQuizItem;
    userAnswer: string;
    correctAnswer: string;
  }>;
}

export function QuizPanel({ quizItems }: QuizPanelProps) {
  const [quizLength, setQuizLength] = useState(() =>
    Math.min(10, quizItems.length)
  );
  const [activeIds, setActiveIds] = useState<number[]>(() =>
    shuffleAndPick(quizItems.length, quizLength)
  );
  const [answers, setAnswers] = useState<Record<number, any>>({});
  const [submitted, setSubmitted] = useState(false);
  const [result, setResult] = useState<QuizResult | null>(null);

  const availableLengths = useMemo(() => {
    return [5, 10, 20].filter((n) => n <= quizItems.length);
  }, [quizItems.length]);

  function shuffleAndPick(total: number, count: number): number[] {
    const indices = Array.from({ length: total }, (_, i) => i);
    for (let i = indices.length - 1; i > 0; i--) {
      const j = Math.floor(Math.random() * (i + 1));
      [indices[i], indices[j]] = [indices[j], indices[i]];
    }
    return indices.slice(0, count);
  }

  const handleNewQuiz = () => {
    const newIds = shuffleAndPick(quizItems.length, quizLength);
    setActiveIds(newIds);
    setAnswers({});
    setSubmitted(false);
    setResult(null);
  };

  const handleSubmit = () => {
    let score = 0;
    const wrong: QuizResult['wrong'] = [];

    for (const qid of activeIds) {
      const q = quizItems[qid];
      const userAnswer = answers[qid];
      let isCorrect = false;

      if (q.type === 'mcq') {
        isCorrect = userAnswer === q.correct_index;
      } else if (q.type === 'true_false') {
        isCorrect = userAnswer === q.answer;
      } else {
        const expected = String(q.answer || '').toLowerCase().trim();
        const given = String(userAnswer || '').toLowerCase().trim();
        isCorrect = given.length > 0 && (expected.includes(given) || given.includes(expected));
      }

      if (isCorrect) {
        score++;
      } else {
        wrong.push({
          question: q,
          userAnswer: formatAnswer(q, userAnswer),
          correctAnswer: formatCorrectAnswer(q),
        });
      }
    }

    setResult({
      score,
      total: activeIds.length,
      accuracy: (score / activeIds.length) * 100,
      wrong,
    });
    setSubmitted(true);
  };

  const handleRetryWrong = () => {
    if (!result) return;
    const wrongIds = result.wrong.map((w) => quizItems.indexOf(w.question));
    setActiveIds(wrongIds);
    setAnswers({});
    setSubmitted(false);
    setResult(null);
  };

  if (!quizItems.length) {
    return (
      <div className="text-center py-12 text-muted">
        <p className="text-lg mb-2">📝</p>
        <p>No quiz questions available.</p>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Controls */}
      <div className="flex flex-wrap items-center gap-3">
        <div className="flex items-center gap-2">
          <span className="text-xs text-muted">Length:</span>
          {availableLengths.map((n) => (
            <button
              key={n}
              onClick={() => { setQuizLength(n); }}
              className={`px-3 py-1 rounded-lg text-xs font-bold transition-all ${
                quizLength === n
                  ? 'bg-accent text-bg'
                  : 'bg-surface border border-border text-muted hover:text-text'
              }`}
            >
              {n}
            </button>
          ))}
        </div>
        <Button variant="secondary" size="sm" onClick={handleNewQuiz}>
          <RotateCcw className="w-3.5 h-3.5" /> New Quiz
        </Button>
      </div>

      {/* Results summary */}
      {submitted && result && (
        <motion.div
          initial={{ opacity: 0, y: -10 }}
          animate={{ opacity: 1, y: 0 }}
          className="space-y-4"
        >
          <div className="grid grid-cols-3 gap-3">
            <MetricCard label="Score" value={`${result.score}/${result.total}`} />
            <MetricCard label="Accuracy" value={`${result.accuracy.toFixed(1)}%`} />
            <MetricCard label="Wrong" value={result.wrong.length} />
          </div>
          {result.wrong.length > 0 && (
            <Button variant="secondary" size="sm" onClick={handleRetryWrong}>
              <RotateCcw className="w-3.5 h-3.5" /> Retry Wrong ({result.wrong.length})
            </Button>
          )}
          {result.wrong.length === 0 && (
            <div className="text-center py-4 text-accent font-display font-bold">
              🎉 Perfect score! No wrong answers.
            </div>
          )}
        </motion.div>
      )}

      {/* Questions */}
      <div className="space-y-4">
        {activeIds.map((qid, qNo) => {
          const q = quizItems[qid];
          const wrongItem = submitted && result
            ? result.wrong.find((w) => w.question === q)
            : null;
          const isCorrect = submitted && !wrongItem;

          return (
            <motion.div
              key={`${qid}-${qNo}`}
              initial={{ opacity: 0, y: 12 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: qNo * 0.03 }}
            >
              <Card
                className={
                  submitted
                    ? isCorrect
                      ? 'border-l-4 border-l-accent'
                      : 'border-l-4 border-l-accent2'
                    : ''
                }
              >
                <div className="flex items-center gap-2 mb-3">
                  <span className="font-mono text-[0.65rem] tracking-widest uppercase text-accent">
                    Question {qNo + 1}
                  </span>
                  <Badge variant="muted">{q.module}</Badge>
                  <Badge
                    variant={
                      q.difficulty === 'easy'
                        ? 'accent'
                        : q.difficulty === 'hard'
                        ? 'danger'
                        : 'warning'
                    }
                  >
                    {q.difficulty}
                  </Badge>
                </div>

                <p className="text-sm font-semibold text-text mb-4">{q.question}</p>

                {/* MCQ */}
                {q.type === 'mcq' && q.options && (
                  <div className="space-y-2">
                    {q.options.map((opt, oi) => (
                      <label
                        key={oi}
                        className={`flex items-center gap-3 px-3 py-2.5 rounded-lg border cursor-pointer transition-all text-sm ${
                          answers[qid] === oi
                            ? 'border-accent bg-accent/[0.06] text-text'
                            : 'border-border hover:border-border-focus text-text-secondary'
                        } ${submitted && q.correct_index === oi ? '!border-accent !bg-accent/[0.08]' : ''}
                          ${submitted && answers[qid] === oi && q.correct_index !== oi ? '!border-accent2 !bg-accent2/[0.06]' : ''}`}
                      >
                        <input
                          type="radio"
                          name={`q-${qid}`}
                          checked={answers[qid] === oi}
                          onChange={() => !submitted && setAnswers((p) => ({ ...p, [qid]: oi }))}
                          disabled={submitted}
                          className="accent-accent"
                        />
                        {opt}
                      </label>
                    ))}
                  </div>
                )}

                {/* True/False */}
                {q.type === 'true_false' && (
                  <div className="flex gap-3">
                    {[true, false].map((val) => (
                      <button
                        key={String(val)}
                        onClick={() => !submitted && setAnswers((p) => ({ ...p, [qid]: val }))}
                        disabled={submitted}
                        className={`flex-1 py-2.5 rounded-lg border text-sm font-medium transition-all ${
                          answers[qid] === val
                            ? 'border-accent bg-accent/[0.06] text-accent'
                            : 'border-border text-text-secondary hover:border-border-focus'
                        }`}
                      >
                        {val ? 'True' : 'False'}
                      </button>
                    ))}
                  </div>
                )}

                {/* Short answer */}
                {q.type === 'short_answer' && (
                  <input
                    type="text"
                    placeholder="Type your answer..."
                    value={answers[qid] || ''}
                    onChange={(e) => !submitted && setAnswers((p) => ({ ...p, [qid]: e.target.value }))}
                    disabled={submitted}
                    className="w-full rounded-lg border border-border bg-bg-elevated px-4 py-2.5 text-sm text-text placeholder:text-muted/50 focus:border-accent focus:outline-none"
                  />
                )}

                {/* Wrong answer feedback */}
                {submitted && wrongItem && (
                  <div className="mt-3 pt-3 border-t border-border space-y-1">
                    <p className="text-xs">
                      <span className="text-accent2 font-medium">Your answer:</span>{' '}
                      <span className="text-text-secondary">{wrongItem.userAnswer}</span>
                    </p>
                    <p className="text-xs">
                      <span className="text-accent font-medium">Correct:</span>{' '}
                      <span className="text-text-secondary">{wrongItem.correctAnswer}</span>
                    </p>
                    <p className="text-xs text-muted">{q.explanation}</p>
                  </div>
                )}
              </Card>
            </motion.div>
          );
        })}
      </div>

      {/* Submit */}
      {!submitted && (
        <Button fullWidth onClick={handleSubmit}>
          <Send className="w-4 h-4" /> Submit Quiz
        </Button>
      )}
    </div>
  );
}

function formatAnswer(q: PracticeQuizItem, answer: any): string {
  if (q.type === 'mcq' && q.options && typeof answer === 'number') {
    return q.options[answer] || 'No answer';
  }
  if (q.type === 'true_false') {
    return answer === true ? 'True' : answer === false ? 'False' : 'No answer';
  }
  return String(answer || 'No answer');
}

function formatCorrectAnswer(q: PracticeQuizItem): string {
  if (q.type === 'mcq' && q.options && q.correct_index !== undefined) {
    return q.options[q.correct_index] || 'Unknown';
  }
  if (q.type === 'true_false') {
    return q.answer === true ? 'True' : 'False';
  }
  return String(q.answer || 'Unknown');
}
