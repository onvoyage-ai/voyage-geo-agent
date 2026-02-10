# Adding a New Query Strategy

Query strategies generate different types of search queries to test brand visibility.

## 1. Create the Strategy

Create `src/stages/query-generation/strategies/<name>.ts`:

```typescript
import { randomBytes } from 'node:crypto';
import type { BrandProfile } from '../../../types/brand.js';
import type { GeneratedQuery } from '../../../types/query.js';
import type { QueryStrategyInterface } from './types.js';

export class MyStrategy implements QueryStrategyInterface {
  name = 'my-strategy';

  generate(profile: BrandProfile, count: number): GeneratedQuery[] {
    const queries: GeneratedQuery[] = [];

    for (let i = 0; i < count; i++) {
      queries.push({
        id: `ms-${randomBytes(4).toString('hex')}`,
        text: `Your query text using ${profile.name}`,
        category: 'recommendation',
        strategy: 'my-strategy' as any,
        intent: 'discovery',
        metadata: { /* optional extra data */ },
      });
    }

    return queries;
  }
}
```

## 2. Register the Strategy

In `src/stages/query-generation/stage.ts`, add to `STRATEGY_MAP`:

```typescript
import { MyStrategy } from './strategies/my-strategy.js';

const STRATEGY_MAP: Record<string, () => QueryStrategyInterface> = {
  // ... existing strategies
  'my-strategy': () => new MyStrategy(),
};
```

## 3. Update Config Schema

In `src/config/schema.ts`, add to the strategies enum:

```typescript
strategies: z.array(z.enum([
  'keyword', 'persona', 'competitor', 'intent',
  'my-strategy',
])),
```

Also update `src/types/query.ts`:

```typescript
export type QueryStrategy = 'keyword' | 'persona' | 'competitor' | 'intent' | 'my-strategy';
```

## Built-in Strategies

| Strategy | Description |
|----------|-------------|
| `keyword` | Template-based queries using brand keywords and category |
| `persona` | Queries from different user personas (developer, business owner, etc.) |
| `competitor` | Head-to-head comparison queries (brand vs competitor) |
| `intent` | Queries based on search intent (informational, navigational, commercial, transactional) |

## Tips

- Use `randomBytes(4).toString('hex')` for unique IDs with a strategy prefix
- Access `profile.name`, `profile.category`, `profile.competitors`, `profile.keywords` for template data
- Set meaningful `category` and `intent` values — these are used in analysis grouping
- The `metadata` field can store strategy-specific context (e.g., which persona, which competitor)
