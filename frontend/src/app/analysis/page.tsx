'use client';

import { useEffect } from 'react';
import { useRouter } from 'next/navigation';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Separator } from '@/components/ui/separator';
import { Button } from '@/components/ui/button';
import { ArrowLeft } from 'lucide-react';
import { useAppDispatch, useAppSelector } from '@/store/hooks';
import {
  selectSessionId,
  selectIncidentName,
  selectAnalysisData,
  selectAnalysisLoading,
  selectLoadingMessage
} from '@/store/selectors';
import { fetchAnalysis } from '@/store/thunks/investigationThunks';
import ShareButton from '@/components/ShareButton';
import LoadingMessages from '@/components/LoadingMessages';
import AnalysisSection from '@/components/AnalysisSection';

interface TimelineEvent {
  time: string;
  event: string;
}

interface Verdict {
  primary_responsibility: string;
  percentage: number;
  reasoning: string;
  contributing_factors: string;
  drama_rating: number;
  drama_rating_explanation: string;
}

interface AnalysisData {
  timeline: TimelineEvent[];
  key_facts: string[];
  gaps: string[];
  verdict: Verdict;
}

export default function AnalysisPage() {
  const router = useRouter();
  const dispatch = useAppDispatch();

  const sessionId = useAppSelector(selectSessionId);
  const incidentName = useAppSelector(selectIncidentName);
  const analysisData = useAppSelector(selectAnalysisData) as AnalysisData | null;
  const isLoading = useAppSelector(selectAnalysisLoading);
  const loadingMessage = useAppSelector(selectLoadingMessage);

  // Redirect if no session
  useEffect(() => {
    if (!sessionId) {
      router.push('/');
      return;
    }

    // Fetch analysis on mount if not already loaded
    if (!analysisData && !isLoading) {
      dispatch(fetchAnalysis(sessionId));
    }
  }, [sessionId, analysisData, isLoading, dispatch, router]);

  if (!sessionId) return null;

  // Loading state
  if (isLoading || !analysisData) {
    return (
      <main className="min-h-screen p-4 bg-gradient-to-b from-background to-muted">
        <div className="max-w-3xl mx-auto">
          <Card className="border-2">
            <CardContent className="pt-6">
              <LoadingMessages />
            </CardContent>
          </Card>
        </div>
      </main>
    );
  }

  const { timeline, key_facts, gaps, verdict } = analysisData;

  // Helper to get drama rating color
  const getDramaRatingColor = (rating: number) => {
    if (rating <= 3) return 'bg-green-500';
    if (rating <= 6) return 'bg-yellow-500';
    if (rating <= 8) return 'bg-orange-500';
    return 'bg-red-500';
  };

  return (
    <main className="min-h-screen p-4 bg-gradient-to-b from-background to-muted">
      <div className="max-w-3xl mx-auto space-y-6">
        {/* Header */}
        <div className="flex items-center justify-between">
          <Button
            variant="ghost"
            onClick={() => router.push('/')}
            size="sm"
          >
            <ArrowLeft className="mr-2 h-4 w-4" />
            New Investigation
          </Button>
        </div>

        {/* Title Card */}
        <Card className="border-2">
          <CardHeader>
            <div className="flex items-start justify-between gap-4">
              <div>
                <CardTitle className="text-2xl mb-2">{incidentName}</CardTitle>
                <div className="flex items-center gap-2">
                  <span className="text-sm text-muted-foreground">Drama Rating:</span>
                  <Badge className={`${getDramaRatingColor(verdict.drama_rating)} text-white`}>
                    {verdict.drama_rating}/10
                  </Badge>
                </div>
              </div>
            </div>
          </CardHeader>
        </Card>

        {/* Verdict Section */}
        <AnalysisSection title="The Verdict" icon="⚖️">
          <div className="space-y-4">
            <div>
              <h4 className="font-semibold text-sm mb-2">Primary Responsibility</h4>
              <p className="text-sm">
                <span className="font-bold text-2xl">{verdict.primary_responsibility}</span>
                {' '}(<span className="text-red-500">{verdict.percentage}%</span> responsible)
              </p>
            </div>
            <div>
              <h4 className="font-semibold text-sm mb-2">Reasoning</h4>
              <p className="text-sm text-muted-foreground">{verdict.reasoning}</p>
            </div>
            {verdict.contributing_factors && (
              <div>
                <h4 className="font-semibold text-sm mb-2">Contributing Factors</h4>
                <p className="text-sm text-muted-foreground">{verdict.contributing_factors}</p>
              </div>
            )}
            <div>
              <h4 className="font-semibold text-sm mb-2">Drama Assessment</h4>
              <p className="text-sm text-muted-foreground">{verdict.drama_rating_explanation}</p>
            </div>
          </div>
        </AnalysisSection>

        {/* Timeline Section */}
        {/* {timeline && timeline.length > 0 && (
          <AnalysisSection title="Timeline" icon="⏱️">
            <div className="space-y-3">
              {timeline.map((event, index) => (
                <div key={index} className="flex gap-3">
                  <div className="text-sm font-semibold text-primary min-w-[80px]">
                    {event.time}
                  </div>
                  <div className="text-sm text-muted-foreground flex-1">
                    {event.event}
                  </div>
                </div>
              ))}
            </div>
          </AnalysisSection>
        )} */}

        {/* Key Facts Section */}
        {key_facts && key_facts.length > 0 && (
          <AnalysisSection title="Key Facts" icon="📋">
            <ul className="list-disc list-inside space-y-2">
              {key_facts.map((fact, index) => (
                <li key={index} className="text-sm text-muted-foreground">
                  {fact}
                </li>
              ))}
            </ul>
          </AnalysisSection>
        )}

        {/* Gaps Section */}
        {/* {gaps && gaps.length > 0 && (
          <AnalysisSection title="What's Still Unclear" icon="❓">
            <ul className="list-disc list-inside space-y-2">
              {gaps.map((gap, index) => (
                <li key={index} className="text-sm text-muted-foreground">
                  {gap}
                </li>
              ))}
            </ul>
          </AnalysisSection>
        )} */}

        {/* Share Button */}
        <div className="pt-4">
          <ShareButton
            analysisText={`Drama Rating: ${verdict.drama_rating}/10\n\n${verdict.reasoning}`}
            incidentName={incidentName}
          />
        </div>
      </div>
    </main>
  );
}