'use client';

import { useState, useEffect } from 'react';
import { useRouter } from 'next/navigation';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Card, CardContent } from '@/components/ui/card';
import { toast } from 'sonner';
import { api, tokenManager } from '@/lib/api';

export default function Home() {
  const router = useRouter();
  const [password, setPassword] = useState('');
  const [isAuthenticated, setIsAuthenticated] = useState(false);
  const [isLoading, setIsLoading] = useState(false);

  // Check if already authenticated (has valid token) and redirect
  useEffect(() => {
    if (tokenManager.isAuthenticated()) {
      router.push('/deets');
    }
  }, [router]);

  const handlePasswordSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setIsLoading(true);

    try {
      await api.verifyPassword(password);
      setIsAuthenticated(true);
      setPassword('');
      toast.success('Access granted!');
      // Redirect to deets page immediately
      router.push('/deets');
    } catch (error) {
      toast.error('Invalid password');
      setPassword('');
      tokenManager.clearToken();
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <main className="min-h-screen flex items-center justify-center p-4 bg-gradient-pink">
      <Card className="w-full max-w-md">
        <CardContent className="pt-6 space-y-6">
          <div className="text-center space-y-2">
            <h1 className="text-6xl font-script text-card-foreground">Drama Detective</h1>
            <p className="text-lg text-muted-foreground">Enter password to access</p>
          </div>

          <form onSubmit={handlePasswordSubmit} className="space-y-4 pt-4">
            <Input
              type="password"
              placeholder="Password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              disabled={isLoading}
              className="text-center"
            />
            <Button
              type="submit"
              size="lg"
              className="w-full min-h-touch text-lg"
              disabled={isLoading || !password}
            >
              {isLoading ? 'Verifying...' : 'Enter 🔑'}
            </Button>
          </form>
        </CardContent>
      </Card>
    </main>
  );
}
