export interface ParsedAnalysis {
  verdict: string;
  primaryResponsibility: string;
  contributingFactors: string;
  dramaRating: number;
  dramaDescription: string;
  unansweredQuestions: string[];
  rawText: string;
}

export function parseAnalysis(analysisText: string): ParsedAnalysis {
  const lines = analysisText.split('\n');

  let verdict = '';
  let primaryResponsibility = '';
  let contributingFactors = '';
  let dramaRating = 0;
  let dramaDescription = '';
  const unansweredQuestions: string[] = [];

  let currentSection = '';

  for (const line of lines) {
    const trimmedLine = line.trim();

    // Detect sections
    if (trimmedLine.includes('The Verdict') || trimmedLine.includes('Verdict')) {
      currentSection = 'verdict';
      continue;
    } else if (trimmedLine.includes('Primary Responsibility')) {
      currentSection = 'primaryResponsibility';
      continue;
    } else if (trimmedLine.includes('Contributing Factors')) {
      currentSection = 'contributingFactors';
      continue;
    } else if (trimmedLine.includes('Drama Rating')) {
      currentSection = 'dramaRating';
      continue;
    } else if (trimmedLine.includes('Unanswered Questions')) {
      currentSection = 'unansweredQuestions';
      continue;
    }

    // Skip empty lines and separators
    if (!trimmedLine || trimmedLine.match(/^[-=]+$/)) {
      continue;
    }

    // Parse content based on section
    switch (currentSection) {
      case 'verdict':
        verdict += trimmedLine + '\n';
        break;
      case 'primaryResponsibility':
        primaryResponsibility += trimmedLine + ' ';
        break;
      case 'contributingFactors':
        contributingFactors += trimmedLine + ' ';
        break;
      case 'dramaRating':
        // Extract rating number (e.g., "7/10")
        const ratingMatch = trimmedLine.match(/(\d+)\/10/);
        if (ratingMatch) {
          dramaRating = parseInt(ratingMatch[1], 10);
        } else if (!trimmedLine.includes('🔥')) {
          dramaDescription += trimmedLine + ' ';
        }
        break;
      case 'unansweredQuestions':
        if (trimmedLine.startsWith('•') || trimmedLine.startsWith('-')) {
          unansweredQuestions.push(trimmedLine.substring(1).trim());
        } else if (trimmedLine.match(/^\d+\./)) {
          unansweredQuestions.push(trimmedLine.substring(trimmedLine.indexOf('.') + 1).trim());
        }
        break;
    }
  }

  return {
    verdict: verdict.trim(),
    primaryResponsibility: primaryResponsibility.trim(),
    contributingFactors: contributingFactors.trim(),
    dramaRating,
    dramaDescription: dramaDescription.trim(),
    unansweredQuestions,
    rawText: analysisText,
  };
}
