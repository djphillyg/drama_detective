'use client';

import { useRouter } from 'next/navigation';
import { Button } from '@/components/ui/button';
import { Card, CardContent } from '@/components/ui/card';

export default function Home() {
  const router = useRouter();

  return (
    <main className="min-h-screen flex items-center justify-center p-4 bg-gradient-to-b from-background to-muted">
      <Card className="w-full max-w-md">
        <CardContent className="pt-6 space-y-6">
          <div className="text-center space-y-2">
            <h1 className="text-4xl font-bold">Drama Detective</h1>
            <p className="text-lg text-muted-foreground">Spill the tea ☕</p>
          </div>

          <div className="space-y-3 pt-4">
            <Button
              variant="outline"
              size="lg"
              className="w-full min-h-touch text-lg"
              disabled
            >
              📸 Screenshots
              <span className="ml-2 text-xs text-muted-foreground">(Coming Soon)</span>
            </Button>

            <Button
              size="lg"
              className="w-full min-h-touch text-lg"
              onClick={() => router.push('/deets')}
            >
              💬 Deets
            </Button>
          </div>
        </CardContent>
      </Card>
    </main>
  );
}
