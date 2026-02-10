export interface GeneratedQuery {
  id: string;
  text: string;
  category: QueryCategory;
  strategy: QueryStrategy;
  intent: string;
  metadata?: Record<string, unknown>;
}

export type QueryCategory =
  | 'recommendation'
  | 'comparison'
  | 'best-of'
  | 'how-to'
  | 'review'
  | 'alternative'
  | 'general';

export type QueryStrategy =
  | 'keyword'
  | 'persona'
  | 'competitor'
  | 'intent';

export interface QuerySet {
  brand: string;
  queries: GeneratedQuery[];
  generatedAt: string;
  totalCount: number;
}
