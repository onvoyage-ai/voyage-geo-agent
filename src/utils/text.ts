export function truncate(text: string, maxLength: number): string {
  if (text.length <= maxLength) return text;
  return text.slice(0, maxLength - 3) + '...';
}

export function countOccurrences(text: string, term: string): number {
  const regex = new RegExp(escapeRegex(term), 'gi');
  const matches = text.match(regex);
  return matches ? matches.length : 0;
}

export function escapeRegex(str: string): string {
  return str.replace(/[.*+?^${}()|[\]\\]/g, '\\$&');
}

export function extractSentences(text: string): string[] {
  return text
    .split(/(?<=[.!?])\s+/)
    .map((s) => s.trim())
    .filter((s) => s.length > 0);
}

export function normalizeBrandName(name: string): string {
  return name.trim().toLowerCase();
}

export function containsBrand(text: string, brand: string): boolean {
  const regex = new RegExp(`\\b${escapeRegex(brand)}\\b`, 'i');
  return regex.test(text);
}

export function extractBrandMentions(text: string, brands: string[]): Map<string, number> {
  const mentions = new Map<string, number>();
  for (const brand of brands) {
    mentions.set(brand, countOccurrences(text, brand));
  }
  return mentions;
}

export function cleanResponseText(text: string): string {
  return text
    .replace(/\n{3,}/g, '\n\n')
    .replace(/[^\S\n]{2,}/g, ' ')
    .trim();
}
