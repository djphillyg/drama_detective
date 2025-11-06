'use client';

import { useState } from 'react';
import { useRouter } from 'next/navigation';
import { Button } from '@/components/ui/button';
import { Textarea } from '@/components/ui/textarea';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { ArrowLeft, X } from 'lucide-react';
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
  const [images, setImages] = useState<string[]>([]);
  const [imagePreviews, setImagePreviews] = useState<string[]>([]);

  const handleImageUpload = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const files = e.target.files;
    if (!files || files.length === 0) return;

    // Limit to 5 images total
    const remainingSlots = 5 - images.length;
    if (remainingSlots <= 0) {
      toast.error('Maximum 5 images allowed');
      return;
    }

    const filesToProcess = Array.from(files).slice(0, remainingSlots);

    try {
      const newImages: string[] = [];
      const newPreviews: string[] = [];

      for (const file of filesToProcess) {
        // Create preview URL
        const previewUrl = URL.createObjectURL(file);
        newPreviews.push(previewUrl);

        // Convert to base64 for API
        const base64 = await new Promise<string>((resolve, reject) => {
          const reader = new FileReader();
          reader.onload = () => {
            const result = reader.result as string;
            // Remove data URL prefix to get just base64
            const base64Data = result.split(',')[1];
            resolve(base64Data);
          };
          reader.onerror = reject;
          reader.readAsDataURL(file);
        });

        newImages.push(base64);
      }

      setImages([...images, ...newImages]);
      setImagePreviews([...imagePreviews, ...newPreviews]);
    } catch (error) {
      toast.error('Failed to process images');
    }

    // Reset input
    e.target.value = '';
  };

  const handleRemoveImage = (index: number) => {
    // Revoke object URL to prevent memory leak
    URL.revokeObjectURL(imagePreviews[index]);

    setImages(images.filter((_, i) => i !== index));
    setImagePreviews(imagePreviews.filter((_, i) => i !== index));
  };

  const handleSubmit = async () => {
    // Validate at least text (10+ chars) OR images provided
    const hasValidText = summary.trim().length >= 10;
    const hasImages = images.length > 0;

    if (!hasValidText && !hasImages) {
      toast.error('Please provide at least 10 characters or upload images');
      return;
    }

    setIsLoading(true);

    try {
      const incidentName = generateIncidentName(summary || 'Image Upload');

      await dispatch(startInvestigation({
        incidentName,
        summary: summary.trim(),
        intervieweeName: intervieweeName.trim() || 'Anonymous',
        relationship,
        images
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
              <Label htmlFor="images">Add screenshots (optional)</Label>
              <Input
                id="images"
                type="file"
                accept="image/*"
                multiple
                onChange={handleImageUpload}
                disabled={images.length >= 5}
              />
              <p className="text-xs text-muted-foreground">
                Upload up to 5 screenshots of text messages, social media posts, etc.
              </p>

              {imagePreviews.length > 0 && (
                <div className="grid grid-cols-2 gap-2 mt-2">
                  {imagePreviews.map((preview, index) => (
                    <div key={index} className="relative group">
                      <img
                        src={preview}
                        alt={`Preview ${index + 1}`}
                        className="w-full h-32 object-cover rounded border"
                      />
                      <Button
                        type="button"
                        variant="destructive"
                        size="icon"
                        className="absolute top-1 right-1 h-6 w-6 opacity-0 group-hover:opacity-100 transition-opacity"
                        onClick={() => handleRemoveImage(index)}
                      >
                        <X className="h-4 w-4" />
                      </Button>
                    </div>
                  ))}
                </div>
              )}
            </div>

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
              disabled={isLoading || (summary.trim().length < 10 && images.length === 0)}
            >
              {isLoading ? 'Starting Detective...' : 'Start Detective'}
            </Button>
          </CardContent>
        </Card>
      </div>
    </main>
  );
}
