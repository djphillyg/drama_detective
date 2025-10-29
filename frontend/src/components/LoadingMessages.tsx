'use client';

import { useEffect } from 'react';
import { useAppDispatch, useAppSelector } from '@/store/hooks';
import { updateLoadingMessage } from '@/store/slices/analysisSlice';
import { selectLoadingMessage } from '@/store/selectors';
import { Spinner } from '@/components/ui/spinner';

export default function LoadingMessages() {
  const dispatch = useAppDispatch();
  const message = useAppSelector(selectLoadingMessage);

  useEffect(() => {
    // Rotate loading message every 2 seconds
    const interval = setInterval(() => {
      dispatch(updateLoadingMessage());
    }, 2000);

    return () => clearInterval(interval);
  }, [dispatch]);

  return (
    <div className="flex flex-col items-center justify-center gap-4 p-8">
      <Spinner className="w-12 h-12" />
      <p className="text-lg font-medium text-center animate-pulse">
        {message}
      </p>
    </div>
  );
}
