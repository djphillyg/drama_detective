export const LOADING_MESSAGES = [
  "Analyzing the tea ☕",
  "Calculating drama levels 🔥",
  "Detecting red flags 🚩",
  "Reading between the lines 👀",
  "Consulting the drama archives 📚",
  "Measuring the vibe check ✨",
  "Processing the receipts 🧾",
];

export function getRandomLoadingMessage(): string {
  return LOADING_MESSAGES[Math.floor(Math.random() * LOADING_MESSAGES.length)];
}
