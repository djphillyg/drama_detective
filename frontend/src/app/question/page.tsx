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
  selectProgressPercentage,
  selectSessionStatus,
} from '@/store/selectors';
import {
  selectAnswer,
  setCustomAnswer
} from '@/store/slices/questionSlice';
import { submitAnswer } from '@/store/thunks/investigationThunks';
import AnswerButton from '@/components/AnswerButton';
import ProgressIndicator from '@/components/ProgressIndicator';
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
  const progressPercentage = useAppSelector(selectProgressPercentage);
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
    } catch (error) {
      toast.error('Failed to submit answer');
    }
  };

  if (!sessionId) return null;

  return (
    <main className="min-h-screen p-4 bg-gradient-to-b from-background to-muted">
      <div className="max-w-2xl mx-auto space-y-4">
        <ProgressIndicator
          turnCount={turnCount}
          progressPercentage={progressPercentage}
        />

        <Card>
          <CardContent className="pt-6 space-y-6">
            <h2 className="text-xl font-semibold leading-relaxed">
              {currentQuestion}
            </h2>

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

            <div className="space-y-2 pt-4">
              <Label htmlFor="custom-answer">Or write your own:</Label>
              <Textarea
                id="custom-answer"
                placeholder="Type your custom answer here..."
                value={customAnswer}
                onChange={(e) => handleCustomAnswerChange(e.target.value)}
                rows={3}
                className="resize-none"
              />
            </div>

            <Button
              size="lg"
              className="w-full min-h-touch text-lg"
              onClick={handleSubmit}
              disabled={!canSubmit}
            >
              Submit
            </Button>
          </CardContent>
        </Card>
      </div>
    </main>
  );
}
