'use client';

import { Button } from '@/components/ui/button';
import { cn } from '@/lib/utils';

interface AnswerButtonProps {
  letter: string;
  answer: string;
  isSelected: boolean;
  onClick: () => void;
  disabled?: boolean;
}

export default function AnswerButton({
  letter,
  answer,
  isSelected,
  onClick,
  disabled = false,
}: AnswerButtonProps) {
  return (
    <Button
      variant={isSelected ? 'default' : 'outline'}
      className={cn(
        'w-full min-h-touch text-left justify-start p-4 text-base',
        'transition-all duration-200',
        isSelected && 'ring-2 ring-primary ring-offset-2'
      )}
      onClick={onClick}
      disabled={disabled}
    >
      <span className="font-bold mr-2">{letter}:</span>
      <span className="flex-1">{answer}</span>
    </Button>
  );
}
