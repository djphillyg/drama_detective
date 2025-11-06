'use client';

import { useEffect } from 'react';
import { useRouter } from 'next/navigation';
import { Button } from '@/components/ui/button';
import { Textarea } from '@/components/ui/textarea';
import { Label } from '@/components/ui/label';
import { Card, CardContent } from '@/components/ui/card';
import { useAppDispatch, useAppSelector } from '@/store/hooks';
import {
  selectSessionId,
  selectCurrentQuestion,
  selectAnswerOptions,
  selectSelectedAnswerIndex,
  selectCustomAnswer,
  selectCanSubmitAnswer,
  selectAnswerToSubmit,
  selectTurnCount,
  selectSessionStatus,
} from '@/store/selectors';
import {
  selectAnswer,
  setCustomAnswer
} from '@/store/slices/questionSlice';
import { submitAnswer } from '@/store/thunks/investigationThunks';
import AnswerButton from '@/components/AnswerButton';
import { toast } from 'sonner';

const ANSWER_LETTERS = ['A', 'B', 'C', 'D'];

export default function QuestionPage() {
  const router = useRouter();
  const dispatch = useAppDispatch();

  const sessionId = useAppSelector(selectSessionId);
  const currentQuestion = useAppSelector(selectCurrentQuestion);
  const answerOptions = useAppSelector(selectAnswerOptions);
  const selectedAnswerIndex = useAppSelector(selectSelectedAnswerIndex);
  const customAnswer = useAppSelector(selectCustomAnswer);
  const canSubmit = useAppSelector(selectCanSubmitAnswer);
  const answerToSubmit = useAppSelector(selectAnswerToSubmit);
  const turnCount = useAppSelector(selectTurnCount);
  const sessionStatus = useAppSelector(selectSessionStatus);

  // Redirect if no session
  useEffect(() => {
    if (!sessionId) {
      router.push('/');
    }
  }, [sessionId, router]);

  // Redirect to analysis when complete
  useEffect(() => {
    if (sessionStatus === 'complete') {
      router.push('/analysis');
    }
  }, [sessionStatus, router]);

  const handleSelectAnswer = (index: number) => {
    dispatch(selectAnswer(index));
  };

  const handleCustomAnswerChange = (value: string) => {
    dispatch(setCustomAnswer(value));
  };

  const handleSubmit = async () => {
    if (!sessionId || !answerToSubmit) return;

    try {
      const result = await dispatch(
        submitAnswer({ sessionId, answer: answerToSubmit })
      ).unwrap();

      if (result.isComplete) {
        // Will be redirected by useEffect
        return;
      }
    } catch {
      toast.error('Failed to submit answer');
    }
  };

  if (!sessionId) return null;

  return (
    <main className="min-h-screen p-4 bg-gradient-pink">
      <div className="max-w-2xl mx-auto space-y-4">
        <Card>
          <CardContent className="pt-6 space-y-6">
            {/* Header with title and progress */}
            <div className="flex items-center justify-between">
              <h1 className="text-2xl font-serif italic font-semibold text-card-foreground">
                lets research mama! 📚✨
              </h1>
              <div className="bg-primary/90 text-white px-4 py-1.5 rounded-full text-sm font-medium">
                Question {turnCount}
              </div>
            </div>

            {/* Question */}
            <div className="bg-card/80 rounded-2xl p-4 border border-pink-200">
              <h2 className="text-lg font-serif italic leading-relaxed text-card-foreground">
                {currentQuestion}
              </h2>
            </div>

            {/* Answer Options */}
            <div className="space-y-3">
              {answerOptions.map((option, index) => (
                <AnswerButton
                  key={index}
                  letter={ANSWER_LETTERS[index]}
                  answer={option.answer}
                  isSelected={selectedAnswerIndex === index}
                  onClick={() => handleSelectAnswer(index)}
                  disabled={false}
                />
              ))}
            </div>

            {/* Custom Answer */}
            <div className="space-y-2 pt-4">
              <div className="bg-card/80 rounded-2xl p-4 border border-pink-200">
                <Label htmlFor="custom-answer" className="text-sm italic text-muted-foreground flex items-center gap-2">
                  ✨ Other (write your own answer):
                </Label>
                <Textarea
                  id="custom-answer"
                  placeholder="Type your answer here..."
                  value={customAnswer}
                  onChange={(e) => handleCustomAnswerChange(e.target.value)}
                  rows={3}
                  className="resize-none mt-2"
                />
              </div>
            </div>

            {/* Submit Button */}
            <Button
              size="lg"
              className="w-full min-h-touch text-lg font-medium"
              onClick={handleSubmit}
              disabled={!canSubmit}
            >
              Next Question! →
            </Button>
          </CardContent>
        </Card>
      </div>
    </main>
  );
}
