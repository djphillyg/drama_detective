'use client';

import { useState, useRef } from 'react';
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
import { UploadIcon } from '@/components/UploadIcon';

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
  const [isDragging, setIsDragging] = useState(false);
  const fileInputRef = useRef<HTMLInputElement>(null);

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

  const handleDragOver = (e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(true);
  };

  const handleDragLeave = (e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(false);
  };

  const handleDrop = async (e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(false);

    const files = e.dataTransfer.files;
    if (!files || files.length === 0) return;

    // Limit to 5 images total
    const remainingSlots = 5 - images.length;
    if (remainingSlots <= 0) {
      toast.error('Maximum 5 images allowed');
      return;
    }

    const filesToProcess = Array.from(files)
      .filter(file => file.type.startsWith('image/'))
      .slice(0, remainingSlots);

    if (filesToProcess.length === 0) {
      toast.error('Please drop image files only');
      return;
    }

    try {
      const newImages: string[] = [];
      const newPreviews: string[] = [];

      for (const file of filesToProcess) {
        const previewUrl = URL.createObjectURL(file);
        newPreviews.push(previewUrl);

        const base64 = await new Promise<string>((resolve, reject) => {
          const reader = new FileReader();
          reader.onload = () => {
            const result = reader.result as string;
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
  };

  const handleUploadClick = () => {
    fileInputRef.current?.click();
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
    <main className="min-h-screen p-4 bg-gradient-pink">
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
            <CardTitle className="text-4xl font-serif italic text-card-foreground text-center">
              🔥 DRAMA DETECTOR 🔥
            </CardTitle>
            <p className="text-base italic text-muted-foreground text-center">Spill the tea & get read! ☕</p>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="space-y-2">
              <Label htmlFor="images">Add screenshots</Label>

              {/* Hidden file input */}
              <input
                ref={fileInputRef}
                id="images"
                type="file"
                accept="image/*"
                multiple
                onChange={handleImageUpload}
                disabled={images.length >= 5}
                className="hidden"
              />

              {/* Styled drag-and-drop area matching Figma */}
              <div
                onClick={handleUploadClick}
                onDragOver={handleDragOver}
                onDragLeave={handleDragLeave}
                onDrop={handleDrop}
                className={`
                  relative flex flex-col items-center justify-center
                  border-4 border-solid rounded-2xl
                  bg-white/10 backdrop-blur-sm
                  px-12 py-12 cursor-pointer
                  transition-all duration-200
                  ${isDragging
                    ? 'border-[#c6005c] bg-white/20'
                    : 'border-[#f6339a] hover:border-[#c6005c] hover:bg-white/15'
                  }
                  ${images.length >= 5 ? 'opacity-50 cursor-not-allowed' : ''}
                `}
                style={{ minHeight: '200px' }}
              >
                <UploadIcon className="mb-4" />
                <p
                  className="text-xl text-center mb-2 font-serif italic"
                  style={{ color: '#861043' }}
                >
                  Drop your drama screenshot!
                </p>
                <p
                  className="text-base text-center font-serif italic"
                  style={{ color: '#c6005c' }}
                >
                  or click to browse
                </p>
              </div>

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
              <Label htmlFor="summary">Add more context (optional)</Label>
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
              <div className="bg-card/80 rounded-2xl p-4 border border-pink-200">
                <Label className="text-sm italic text-muted-foreground flex items-center gap-2 mb-3">
                  Tell us about yourself! 💅
                </Label>
                <p className="text-xs italic text-muted-foreground mb-3">What's your role in this drama?</p>
                <div className="space-y-3">
                  <button
                    type="button"
                    onClick={() => setRelationship('participant')}
                    className={`w-full text-left px-6 py-4 text-sm rounded-3xl transition-all duration-200 border-2 border-(--card-border) bg-card/50 shadow-sm hover:bg-card hover:shadow-md ${
                      relationship === 'participant' ? 'bg-card shadow-md ring-2 ring-primary/50' : ''
                    }`}
                  >
                    <span className="italic text-card-foreground">
                      🎭 I'm in it! (Main character energy)
                    </span>
                  </button>
                  <button
                    type="button"
                    onClick={() => setRelationship('witness')}
                    className={`w-full text-left px-6 py-4 text-sm rounded-3xl transition-all duration-200 border-2 border-(--card-border) bg-card/50 shadow-sm hover:bg-card hover:shadow-md ${
                      relationship === 'witness' ? 'bg-card shadow-md ring-2 ring-primary/50' : ''
                    }`}
                  >
                    <span className="italic text-card-foreground">
                      👀 Just watching (Eating popcorn)
                    </span>
                  </button>
                  <button
                    type="button"
                    onClick={() => setRelationship('secondhand')}
                    className={`w-full text-left px-6 py-4 text-sm rounded-3xl transition-all duration-200 border-2 border-(--card-border) bg-card/50 shadow-sm hover:bg-card hover:shadow-md ${
                      relationship === 'secondhand' ? 'bg-card shadow-md ring-2 ring-primary/50' : ''
                    }`}
                  >
                    <span className="italic text-card-foreground">
                      🕊️ The peacemaker (Trying to help)
                    </span>
                  </button>
                  <button
                    type="button"
                    onClick={() => setRelationship('friend')}
                    className={`w-full text-left px-6 py-4 text-sm rounded-3xl transition-all duration-200 border-2 border-(--card-border) bg-card/50 shadow-sm hover:bg-card hover:shadow-md ${
                      relationship === 'friend' ? 'bg-card shadow-md ring-2 ring-primary/50' : ''
                    }`}
                  >
                    <span className="italic text-card-foreground">
                      😈 Started it (No regrets)
                    </span>
                  </button>
                </div>
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
