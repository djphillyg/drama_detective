import { RootState } from './index';

// Session selectors
export const selectSessionId = (state: RootState) => state.session.sessionId;
export const selectSessionStatus = (state: RootState) => state.session.status;
export const selectSessionError = (state: RootState) => state.session.error;
export const selectIncidentName = (state: RootState) => state.session.incidentName;

// Question selectors
export const selectCurrentQuestion = (state: RootState) => state.question.currentQuestion;
export const selectAnswerOptions = (state: RootState) => state.question.answerOptions;
export const selectSelectedAnswerIndex = (state: RootState) => state.question.selectedAnswerIndex;
export const selectCustomAnswer = (state: RootState) => state.question.customAnswer;
export const selectIsSubmitting = (state: RootState) => state.question.isSubmitting;

// Derived selector: can submit if either pre-gen selected or custom answer entered
export const selectCanSubmitAnswer = (state: RootState) => {
  const hasSelectedAnswer = state.question.selectedAnswerIndex !== null;
  const hasCustomAnswer = state.question.customAnswer.trim().length > 0;
  return (hasSelectedAnswer || hasCustomAnswer) && !state.question.isSubmitting;
};

// Derived selector: get the answer to submit (pre-gen or custom)
export const selectAnswerToSubmit = (state: RootState) => {
  const customAnswer = state.question.customAnswer.trim();

  if (customAnswer.length > 0) {
    return {
      answer: customAnswer,
      reasoning: 'User provided custom answer',
    };
  }

  const selectedIndex = state.question.selectedAnswerIndex;
  if (selectedIndex !== null && state.question.answerOptions[selectedIndex]) {
    return state.question.answerOptions[selectedIndex];
  }

  return null;
};

// Progress selectors
export const selectTurnCount = (state: RootState) => state.progress.turnCount;
export const selectGoals = (state: RootState) => state.progress.goals;
export const selectFactsCount = (state: RootState) => state.progress.factsCount;

// Derived selector: calculate progress percentage from goals
export const selectProgressPercentage = (state: RootState) => {
  const goals = state.progress.goals;
  if (goals.length === 0) return 0;

  const totalConfidence = goals.reduce((sum, goal) => sum + goal.confidence, 0);
  const avgConfidence = totalConfidence / goals.length;

  return Math.round(avgConfidence);
};

// Analysis selectors
export const selectAnalysisData = (state: RootState) => state.analysis.data;
export const selectAnalysisLoading = (state: RootState) => state.analysis.isLoading;
export const selectLoadingMessage = (state: RootState) => state.analysis.loadingMessage;
