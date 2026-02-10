import type { QueryResult } from '../../../types/result.js';
import type { BrandProfile } from '../../../types/brand.js';

export interface Analyzer {
  name: string;
  analyze(results: QueryResult[], profile: BrandProfile): unknown;
}
