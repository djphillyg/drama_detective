'use client';

import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Separator } from '@/components/ui/separator';

interface AnalysisSectionProps {
  title: string;
  icon: string;
  children: React.ReactNode;
}

export default function AnalysisSection({
  title,
  icon,
  children
}: AnalysisSectionProps) {
  return (
    <Card>
      <CardHeader className="pb-3">
        <CardTitle className="flex items-center gap-2 text-xl">
          <span>{icon}</span>
          <span>{title}</span>
        </CardTitle>
      </CardHeader>
      <Separator />
      <CardContent className="pt-4">
        <div className="prose prose-sm max-w-none">
          {children}
        </div>
      </CardContent>
    </Card>
  );
}
