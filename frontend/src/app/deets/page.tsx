'use client';

import { useState } from 'react';
import { useRouter } from 'next/navigation';
import { Button } from '@/components/ui/button';
import { Textarea } from '@/components/ui/textarea';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { ArrowLeft } from 'lucide-react';
import { useAppDispatch } from '@/store/hooks';
import { startInvestigation } from '@/store/thunks/investigationThunks';
import { generateIncidentName } from '@/lib/utils/incidentName';
import { toast } from 'sonner';

type RelationshipType = 'participant' | 'witness' | 'secondhand' | 'friend';

export default function DeetsPage() {
  const router = useRouter();
  const dispatch = useAppDispatch();
  const [summary, setSummary] = useState('');
  const [intervieweeName, setIntervieweeName] = useState('');
  const [relationship, setRelationship] = useState<RelationshipType>('participant');
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
        summary: summary.trim(),
        intervieweeName: intervieweeName.trim() || 'Anonymous',
        relationship
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

            <div className="space-y-2">
              <Label htmlFor="name">What's your name?</Label>
              <Input
                id="name"
                placeholder="Anonymous"
                value={intervieweeName}
                onChange={(e) => setIntervieweeName(e.target.value)}
              />
            </div>

            <div className="space-y-2">
              <Label>What's your relationship to this incident?</Label>
              <div className="space-y-2">
                <label className="flex items-center space-x-3 cursor-pointer">
                  <input
                    type="radio"
                    name="relationship"
                    value="participant"
                    checked={relationship === 'participant'}
                    onChange={(e) => setRelationship(e.target.value as RelationshipType)}
                    className="h-4 w-4 border-gray-300 text-primary focus:ring-primary"
                  />
                  <span className="text-sm">I was directly involved</span>
                </label>
                <label className="flex items-center space-x-3 cursor-pointer">
                  <input
                    type="radio"
                    name="relationship"
                    value="witness"
                    checked={relationship === 'witness'}
                    onChange={(e) => setRelationship(e.target.value as RelationshipType)}
                    className="h-4 w-4 border-gray-300 text-primary focus:ring-primary"
                  />
                  <span className="text-sm">I witnessed it happen</span>
                </label>
                <label className="flex items-center space-x-3 cursor-pointer">
                  <input
                    type="radio"
                    name="relationship"
                    value="secondhand"
                    checked={relationship === 'secondhand'}
                    onChange={(e) => setRelationship(e.target.value as RelationshipType)}
                    className="h-4 w-4 border-gray-300 text-primary focus:ring-primary"
                  />
                  <span className="text-sm">Someone told me about it</span>
                </label>
                <label className="flex items-center space-x-3 cursor-pointer">
                  <input
                    type="radio"
                    name="relationship"
                    value="friend"
                    checked={relationship === 'friend'}
                    onChange={(e) => setRelationship(e.target.value as RelationshipType)}
                    className="h-4 w-4 border-gray-300 text-primary focus:ring-primary"
                  />
                  <span className="text-sm">I'm friends with someone involved</span>
                </label>
              </div>
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
