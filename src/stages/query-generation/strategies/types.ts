import type { BrandProfile } from '../../../types/brand.js';
import type { GeneratedQuery } from '../../../types/query.js';
import type { AIProvider } from '../../../providers/types.js';

export interface QueryStrategyInterface {
  name: string;
  generate(profile: BrandProfile, count: number, provider: AIProvider): Promise<GeneratedQuery[]>;
}
