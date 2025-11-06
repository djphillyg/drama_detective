'use client';

import { cn } from '@/lib/utils';

interface AnswerButtonProps {
  letter?: string;
  answer: string;
  isSelected: boolean;
  onClick: () => void;
  disabled?: boolean;
}

export default function AnswerButton({
  answer,
  isSelected,
  onClick,
  disabled = false,
}: AnswerButtonProps) {
  return (
    <button
      className={cn(
        'w-full h-auto min-h-touch text-left justify-start items-start px-6 py-4 text-base rounded-3xl',
        'transition-all duration-200 whitespace-normal',
        'border-2 border-(--card-border) bg-card/50 shadow-sm hover:bg-card hover:shadow-md',
        'disabled:pointer-events-none disabled:opacity-50',
        isSelected && 'bg-card shadow-md ring-2 ring-primary/50'
      )}
      onClick={onClick}
      disabled={disabled}
    >
      <span className="italic text-card-foreground flex items-center gap-2">
        {answer}
      </span>
    </button>
  );
}
