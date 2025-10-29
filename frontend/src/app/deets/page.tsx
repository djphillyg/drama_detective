'use client';

import { useState } from 'react';
import { useRouter } from 'next/navigation';
import { Button } from '@/components/ui/button';
import { Textarea } from '@/components/ui/textarea';
import { Label } from '@/components/ui/label';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { ArrowLeft } from 'lucide-react';
import { useAppDispatch } from '@/store/hooks';
import { startInvestigation } from '@/store/thunks/investigationThunks';
import { generateIncidentName } from '@/lib/utils/incidentName';
import { toast } from 'sonner';

export default function DeetsPage() {
  const router = useRouter();
  const dispatch = useAppDispatch();
  const [summary, setSummary] = useState('');
  const [isLoading, setIsLoading] = useState(false);

  const handleSubmit = async () => {
    if (summary.trim().length < 10) {
      toast.error('Please provide at least 10 characters');
      return;
    }

    setIsLoading(true);

    try {
      const incidentName = generateIncidentName(summary);

      await dispatch(startInvestigation({
        incidentName,
        summary: summary.trim()
      })).unwrap();

      // Navigate to question page on success
      router.push('/question');
    } catch (error) {
      toast.error('Failed to start investigation');
      setIsLoading(false);
    }
  };

  return (
    <main className="min-h-screen p-4 bg-gradient-to-b from-background to-muted">
      <div className="max-w-2xl mx-auto space-y-4">
        <Button
          variant="ghost"
          onClick={() => router.push('/')}
          className="mb-4"
        >
          <ArrowLeft className="mr-2 h-4 w-4" />
          Back
        </Button>

        <Card>
          <CardHeader>
            <CardTitle className="text-2xl">What's the drama?</CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="space-y-2">
              <Label htmlFor="summary">Tell us what happened</Label>
              <Textarea
                id="summary"
                placeholder="My friend Sarah texted me saying that Rob told her that Alex was talking about me behind my back, but when I asked Alex about it..."
                value={summary}
                onChange={(e) => setSummary(e.target.value)}
                rows={8}
                className="resize-none"
              />
              <p className="text-xs text-muted-foreground text-right">
                {summary.length} characters
              </p>
            </div>

            <Button
              size="lg"
              className="w-full min-h-touch text-lg"
              onClick={handleSubmit}
              disabled={isLoading || summary.trim().length < 10}
            >
              {isLoading ? 'Starting Detective...' : 'Start Detective'}
            </Button>
          </CardContent>
        </Card>
      </div>
    </main>
  );
}
