export function generateIncidentName(summary: string): string {
  // Take first 3 words, sanitize, and add timestamp
  const words = summary
    .trim()
    .split(/\s+/)
    .slice(0, 3)
    .map(word => word.replace(/[^a-zA-Z0-9]/g, ''))
    .filter(word => word.length > 0);

  const timestamp = Date.now();

  if (words.length === 0) {
    return `Drama_${timestamp}`;
  }

  return `${words.join('_')}_${timestamp}`;
}
