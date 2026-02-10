export interface AnalysisResult {
  runId: string;
  brand: string;
  analyzedAt: string;
  mindshare: MindshareScore;
  mentionRate: MentionRateScore;
  sentiment: SentimentScore;
  positioning: PositioningScore;
  citations: CitationScore;
  competitorAnalysis: CompetitorAnalysis;
  summary: ExecutiveSummary;
}

export interface MindshareScore {
  overall: number;
  byProvider: Record<string, number>;
  byCategory: Record<string, number>;
  rank: number;
  totalBrandsDetected: number;
}

export interface MentionRateScore {
  overall: number;
  byProvider: Record<string, number>;
  byCategory: Record<string, number>;
  totalMentions: number;
  totalResponses: number;
}

export interface SentimentScore {
  overall: number;
  label: 'positive' | 'neutral' | 'negative';
  confidence: number;
  byProvider: Record<string, number>;
  byProviderLabel: Record<string, 'positive' | 'neutral' | 'negative'>;
  byCategory: Record<string, number>;
  positiveCount: number;
  neutralCount: number;
  negativeCount: number;
  totalSentences: number;
  topPositive: SentimentExcerpt[];
  topNegative: SentimentExcerpt[];
}

export interface SentimentExcerpt {
  text: string;
  score: number;
  provider: string;
}

export interface PositioningScore {
  primaryPosition: string;
  attributes: PositionAttribute[];
  byProvider: Record<string, string>;
}

export interface PositionAttribute {
  attribute: string;
  frequency: number;
  sentiment: number;
}

export interface CitationScore {
  totalCitations: number;
  uniqueSourcesCited: number;
  citationRate: number;
  byProvider: Record<string, number>;
  topSources: CitationSource[];
}

export interface CitationSource {
  source: string;
  count: number;
  providers: string[];
}

export interface CompetitorAnalysis {
  competitors: CompetitorScore[];
  brandRank: number;
}

export interface CompetitorScore {
  name: string;
  mentionRate: number;
  sentiment: number;
  mindshare: number;
}

export interface ExecutiveSummary {
  headline: string;
  keyFindings: string[];
  strengths: string[];
  weaknesses: string[];
  recommendations: string[];
  overallScore: number;
}
