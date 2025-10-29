'use client';

import { Button } from '@/components/ui/button';
import { toast } from 'sonner';

interface ShareButtonProps {
  analysisText: string;
  incidentName: string;
}

export default function ShareButton({
  analysisText,
  incidentName
}: ShareButtonProps) {
  const handleShare = async () => {
    const shareText = `🔍 Drama Detective Results\n\n${analysisText}\n\nAnalyze your drama at: ${window.location.origin}`;

    try {
      // Try Web Share API first (works on mobile)
      if (navigator.share) {
        await navigator.share({
          title: `Drama Detective: ${incidentName}`,
          text: shareText,
          url: window.location.href,
        });
        toast.success('Shared successfully!');
      } else {
        // Fallback to clipboard
        await navigator.clipboard.writeText(shareText);
        toast.success('Copied to clipboard!');
      }
    } catch (error) {
      // User cancelled or error occurred
      if (error instanceof Error && error.name !== 'AbortError') {
        toast.error('Failed to share');
      }
    }
  };

  return (
    <Button
      onClick={handleShare}
      className="w-full min-h-touch text-lg"
      size="lg"
    >
      📤 Share Results
    </Button>
  );
}
