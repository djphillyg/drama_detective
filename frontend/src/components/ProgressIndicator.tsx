'use client';

import { Progress } from '@/components/ui/progress';
import { Badge } from '@/components/ui/badge';

interface ProgressIndicatorProps {
  turnCount: number;
  progressPercentage: number;
}

export default function ProgressIndicator({
  turnCount,
  progressPercentage,
}: ProgressIndicatorProps) {
  return (
    <div className="flex items-center gap-3 p-4 bg-muted/50 rounded-lg">
      <Badge variant="secondary" className="text-xs">
        Question {turnCount}
      </Badge>
      <div className="flex-1 flex items-center gap-2">
        <Progress value={progressPercentage} className="flex-1" />
        <span className="text-xs text-muted-foreground font-medium">
          {progressPercentage}%
        </span>
      </div>
    </div>
  );
}
