# Adding a New Analyzer

Analyzers process query results to extract specific metrics about brand visibility.

## 1. Create the Analyzer

Create `src/stages/analysis/analyzers/<name>.ts`:

```typescript
import type { Analyzer } from './types.js';
import type { QueryResult } from '../../../types/result.js';
import type { BrandProfile } from '../../../types/brand.js';

export interface MyAnalysisScore {
  // Define your output shape
  overall: number;
  byProvider: Record<string, number>;
}

export class MyAnalyzer implements Analyzer {
  name = 'my-analyzer';

  analyze(results: QueryResult[], profile: BrandProfile): MyAnalysisScore {
    const validResults = results.filter((r) => !r.error && r.response);

    // Your analysis logic here
    // Use helpers from utils/text.ts and statistics.ts

    return {
      overall: 0,
      byProvider: {},
    };
  }
}
```

## 2. Register the Analyzer

In `src/stages/analysis/stage.ts`, add to `ANALYZER_MAP`:

```typescript
import { MyAnalyzer } from './analyzers/my-analyzer.js';

const ANALYZER_MAP: Record<string, () => Analyzer> = {
  // ... existing analyzers
  'my-analyzer': () => new MyAnalyzer(),
};
```

## 3. Add to Config Schema

In `src/config/schema.ts`, add to the analyzers enum:

```typescript
export const analysisConfigSchema = z.object({
  analyzers: z.array(z.enum([
    // ... existing analyzers
    'my-analyzer',
  ])),
});
```

## 4. Add Result Type

If your analyzer produces a new data shape, add it to `src/types/analysis.ts` and update `AnalysisResult`.

## Built-in Analyzers

| Analyzer | What it measures |
|----------|-----------------|
| `mindshare` | Brand's share of AI "attention" vs competitors |
| `mention-rate` | How often the brand is mentioned in responses |
| `sentiment` | Positive/negative/neutral sentiment of brand mentions |
| `positioning` | How AI models describe and position the brand |
| `citation` | What URLs/sources AI models cite |
| `competitor` | Comparison of brand metrics against competitors |

## Useful Utilities

- `containsBrand(text, brand)` — check if text mentions brand
- `extractSentences(text)` — split text into sentences
- `countOccurrences(text, term)` — count term occurrences
- `groupBy(items, keyFn)` — group items
- `mean(values)` / `percentage(part, total)` — statistics
