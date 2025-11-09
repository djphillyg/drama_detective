'use client';

import { Slider } from '@/components/ui/slider';

interface ConfidenceSliderProps {
  value: number;
  onChange: (value: number) => void;
}

export function ConfidenceSlider({ value, onChange }: ConfidenceSliderProps) {
  return (
    <div className="space-y-4 p-6 rounded-3xl bg-card/30 backdrop-blur-sm border-2 border-pink-200/50 shadow-[0_0_15px_rgba(255,105,180,0.2)]">
      <p className="text-base text-card-foreground/90">
        How confident should the detective be?
      </p>

      <div className="space-y-3">
        <div className="flex justify-between items-center text-sm italic text-muted-foreground px-1">
          <span>get loose with it</span>
          <span>stick to the facts</span>
        </div>

        <Slider
          value={[value]}
          onValueChange={(values) => onChange(values[0])}
          min={30}
          max={90}
          step={1}
          className="w-full"
        />
      </div>
    </div>
  );
}
